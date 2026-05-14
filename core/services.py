from collections import defaultdict
from decimal import Decimal, InvalidOperation
from datetime import timedelta

from django.contrib.sessions.models import Session
from django.db import transaction
from django.db.models import Count, DecimalField, ExpressionWrapper, F, OuterRef, Q, Subquery, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from .models import AreaChoices, DraftOrderReservation, ItemPaidStatusChoices, ItemStatusChoices, Order, OrderItem, OrderItemPayment, OrderItemPriceChange, OrderPayment, OrderStatusChoices, Product, ProductCategoryChoices, ProductVariant, Supply, WorkDay, WorkDayStatusChoices


HOME_MODULES = [
	{'title': 'Administrador', 'url': 'admin-panel', 'description': 'Inventario, recetas, variantes y ventas del turno.'},
	{'title': 'Comandas', 'url': 'comanda-list', 'description': 'Mesas activas, consumo por comensal y detalle de pedido.'},
	{'title': 'Cocina', 'url': 'kitchen-board', 'description': 'Salida de preparaciones en cola para cocina.'},
	{'title': 'Bar', 'url': 'bar-board', 'description': 'Bebidas y pedidos pendientes en barra.'},
	{'title': 'Entregas', 'url': 'deliveries-board', 'description': 'Productos listos para entregar a mesa.'},
	{'title': 'Caja', 'url': 'cash-list', 'description': 'Importes, pagos parciales y cierre por mesa.'},
]

BAR_AREAS = ['Cocina', 'Bar', 'Caja', 'Almacén']
DRAFT_RESERVATION_MINUTES = 10


def _restore_item_stock(product, variant, quantity):
	if variant:
		variant.stock += quantity
		variant.save(update_fields=['stock'])
		return
	product.stock += quantity
	product.save(update_fields=['stock'])


@transaction.atomic
def cleanup_stale_draft_reservations():
	now = timezone.now()
	stale_reservations = list(
		DraftOrderReservation.objects.select_related('product', 'variant').select_for_update().filter(expires_at__lte=now)
	)
	for reservation in stale_reservations:
		_restore_item_stock(reservation.product, reservation.variant, reservation.quantity)
	DraftOrderReservation.objects.filter(id__in=[reservation.id for reservation in stale_reservations]).delete()

def get_home_metrics():
	return {
		'mesas abiertas': Order.objects.filter(status=OrderStatusChoices.ABIERTA).count(),
		'productos con existencia': Product.objects.filter(is_active=True, stock__gt=0).count(),
		'insumos con existencia': Supply.objects.filter(is_available=True).count(),
		'productos en proceso': OrderItem.objects.filter(
			status__in=[
				ItemStatusChoices.COMANDADO,
				ItemStatusChoices.EN_PREPARACION,
				ItemStatusChoices.POR_ENTREGAR,
			]
		).count(),
	}


def get_admin_metrics():
	return {
		'mesas abiertas': Order.objects.filter(status=OrderStatusChoices.ABIERTA).count(),
		'productos con existencia': Product.objects.filter(is_active=True, stock__gt=0).count(),
		'insumos con existencia': Supply.objects.filter(is_available=True).count(),
		'productos en proceso': OrderItem.objects.filter(
			status__in=[
				ItemStatusChoices.COMANDADO,
				ItemStatusChoices.EN_PREPARACION,
				ItemStatusChoices.POR_ENTREGAR,
			]
		).count(),
	}


def get_recent_orders(limit=8, workday_id=None):
	total_paid_subquery = OrderPayment.objects.filter(order_id=OuterRef('pk')).values('order_id').annotate(
		total=Sum('total_amount')
	).values('total')[:1]
	queryset = Order.objects.annotate(
		total_products=Count('items', filter=~Q(items__status=ItemStatusChoices.CANCELADO), distinct=True),
		total_paid=Coalesce(
			Subquery(total_paid_subquery, output_field=DecimalField(max_digits=10, decimal_places=2)),
			Value(Decimal('0.00')),
			output_field=DecimalField(max_digits=10, decimal_places=2),
		),
	).prefetch_related('items', 'payments')
	if workday_id:
		queryset = queryset.filter(workday_id=workday_id)
	if limit is None:
		return queryset
	return queryset[:limit]


def get_active_workday():
	return WorkDay.objects.filter(status=WorkDayStatusChoices.ABIERTO).first()


@transaction.atomic
def open_workday(user):
	active = get_active_workday()
	if active:
		return active, False
	workday = WorkDay.objects.create(opened_by=user)
	return workday, True


@transaction.atomic
def close_workday(user):
	workday = WorkDay.objects.select_for_update().filter(status=WorkDayStatusChoices.ABIERTO).first()
	if not workday:
		return None, 0, False
	pending_orders = workday.orders.filter(status=OrderStatusChoices.ABIERTA).count()
	workday.status = WorkDayStatusChoices.CERRADO
	workday.closed_at = timezone.now()
	workday.closed_by = user
	workday.pending_orders_on_close = pending_orders
	workday.save(update_fields=['status', 'closed_at', 'closed_by', 'pending_orders_on_close'])
	Session.objects.all().delete()
	return workday, pending_orders, True


def get_orders_with_items():
	active_workday = get_active_workday()
	if not active_workday:
		return Order.objects.none()
	total_paid_subquery = OrderPayment.objects.filter(order_id=OuterRef('pk')).values('order_id').annotate(
		total=Sum('total_amount')
	).values('total')[:1]
	return Order.objects.filter(workday=active_workday).annotate(
		total_products=Count('items', filter=~Q(items__status=ItemStatusChoices.CANCELADO), distinct=True),
		total_amount_value=Sum(
			ExpressionWrapper(F('items__quantity') * F('items__unit_price'), output_field=DecimalField(max_digits=10, decimal_places=2)),
			filter=~Q(items__status=ItemStatusChoices.CANCELADO),
		),
		total_diners=Count('items__diner_name', filter=Q(items__diner_name__gt=''), distinct=True),
		total_paid=Coalesce(
			Subquery(total_paid_subquery, output_field=DecimalField(max_digits=10, decimal_places=2)),
			Value(Decimal('0.00')),
			output_field=DecimalField(max_digits=10, decimal_places=2),
		),
	).order_by('-created_at')


def build_available_product_catalog():
	"""Retorna solo productos/variantes con inventario disponible."""
	cleanup_stale_draft_reservations()
	products = Product.objects.filter(is_active=True).prefetch_related('variants', 'product_supplies__supply')
	catalog = []
	for product in products:
		active_variants = list(product.variants.filter(is_active=True))
		available_variants = [v for v in active_variants if v.stock > 0]
		uses_variants = bool(active_variants)

		# Si el producto maneja variantes, solo se muestra si tiene al menos una variante con stock.
		# Si no maneja variantes, se muestra por su propio stock.
		if uses_variants and not available_variants:
			continue
		if not uses_variants and product.stock <= 0:
			continue

		catalog.append(
			{
				'id': product.pk,
				'name': product.name,
				'price': str(product.price),
				'stock': product.stock,
				'variants': [
					{'id': variant.pk, 'name': variant.name, 'price_delta': str(variant.price_delta), 'stock': variant.stock}
					for variant in available_variants
				],
				'supplies': [
					{'id': rel.supply.pk, 'name': rel.supply.name}
					for rel in product.product_supplies.select_related('supply').all()
				],
			}
		)
	return catalog


@transaction.atomic
def reserve_draft_item(session_key, product_id, variant_id, quantity):
	cleanup_stale_draft_reservations()
	product, variant, unit_price, reserved_quantity = _reserve_item_stock(product_id, variant_id, quantity)
	return DraftOrderReservation.objects.create(
		session_key=session_key,
		product=product,
		variant=variant,
		quantity=reserved_quantity,
		unit_price=Decimal(unit_price),
		expires_at=timezone.now() + timedelta(minutes=DRAFT_RESERVATION_MINUTES),
	)


@transaction.atomic
def release_draft_item(session_key, reservation_token):
	cleanup_stale_draft_reservations()
	reservation = DraftOrderReservation.objects.select_related('product', 'variant').select_for_update().filter(
		session_key=session_key,
		reservation_token=reservation_token,
	).first()
	if not reservation:
		return False
	_restore_item_stock(reservation.product, reservation.variant, reservation.quantity)
	reservation.delete()
	return True


@transaction.atomic
def release_all_draft_items(session_key):
	cleanup_stale_draft_reservations()
	reservations = list(
		DraftOrderReservation.objects.select_related('product', 'variant').select_for_update().filter(session_key=session_key)
	)
	for reservation in reservations:
		_restore_item_stock(reservation.product, reservation.variant, reservation.quantity)
	DraftOrderReservation.objects.filter(id__in=[reservation.id for reservation in reservations]).delete()
	return len(reservations)


def _consume_draft_reservation(session_key, reservation_token, product_id, variant_id, quantity):
	requested_quantity = max(int(quantity or 1), 1)
	reservation = DraftOrderReservation.objects.select_related('product', 'variant').select_for_update().filter(
		session_key=session_key,
		reservation_token=reservation_token,
	).first()
	if not reservation:
		raise ValueError('La reserva del producto ya expiró o no está disponible. Vuelve a agregarlo a la comanda.')
	if reservation.product_id != product_id:
		raise ValueError('El producto reservado ya no coincide con el borrador actual.')
	if (reservation.variant_id or None) != (variant_id or None):
		raise ValueError('La variante reservada ya no coincide con el borrador actual.')
	if reservation.quantity != requested_quantity:
		raise ValueError('La cantidad reservada cambió. Vuelve a agregar el producto para confirmar el inventario.')
	product = reservation.product
	variant = reservation.variant
	unit_price = reservation.unit_price
	reserved_quantity = reservation.quantity
	reservation.delete()
	return product, variant, unit_price, reserved_quantity


def _reserve_item_stock(product_id, variant_id, quantity):
	quantity = max(int(quantity or 1), 1)
	product = Product.objects.select_for_update().filter(pk=product_id, is_active=True).first()
	if not product:
		raise ValueError('Uno de los productos seleccionados ya no está disponible.')

	variant = None
	unit_price = product.price

	if variant_id:
		variant = ProductVariant.objects.select_for_update().filter(pk=variant_id, product=product, is_active=True).first()
		if not variant:
			raise ValueError('Una variante seleccionada no corresponde al producto.')
		if variant.stock < quantity:
			raise ValueError(f'No hay inventario suficiente para la variante {variant.name}.')
		variant.stock -= quantity
		variant.save(update_fields=['stock'])
		unit_price = product.price + variant.price_delta
	else:
		# Si el producto tiene variantes activas, debe elegirse una variante.
		if product.variants.filter(is_active=True).exists():
			raise ValueError('Este producto requiere seleccionar una variante disponible.')
		if product.stock < quantity:
			raise ValueError(f'No hay inventario suficiente para el producto {product.name}.')
		product.stock -= quantity
		product.save(update_fields=['stock'])

	return product, variant, unit_price, quantity


def get_order_detail_queryset():
	active_workday = get_active_workday()
	if not active_workday:
		return Order.objects.none()
	return Order.objects.filter(workday=active_workday).prefetch_related('items__product', 'items__price_changes__changed_by')


def group_order_items(order):
	grouped_items = defaultdict(list)
	for item in order.items.all():
		grouped_items[item.diner_name or 'Mesa'].append(item)
	return dict(grouped_items)


def get_production_items(area):
	active_workday = get_active_workday()
	if not active_workday:
		return OrderItem.objects.none()
	category = ProductCategoryChoices.COMIDA if area == AreaChoices.COCINA else ProductCategoryChoices.BEBIDA
	return OrderItem.objects.select_related('order', 'product').filter(
		product__category=category,
		status__in=[ItemStatusChoices.COMANDADO, ItemStatusChoices.EN_PREPARACION],
		order__status=OrderStatusChoices.ABIERTA,
		order__workday=active_workday,
	)


def get_delivery_items():
	active_workday = get_active_workday()
	if not active_workday:
		return OrderItem.objects.none()
	return OrderItem.objects.select_related('order', 'product').filter(
		status=ItemStatusChoices.POR_ENTREGAR,
		order__status=OrderStatusChoices.ABIERTA,
		order__workday=active_workday,
	)


def get_cash_orders_queryset():
	active_workday = get_active_workday()
	if not active_workday:
		return Order.objects.none()
	return Order.objects.filter(workday=active_workday).prefetch_related('items').annotate(
		total_items=Count('items'),
		delivered_items=Count('items', filter=Q(items__status=ItemStatusChoices.ENTREGADO)),
		paid_items=Count('items', filter=Q(items__paid_status=ItemPaidStatusChoices.PAGADO) & ~Q(items__status=ItemStatusChoices.CANCELADO)),
		unpaid_items=Count('items', filter=Q(items__paid_status=ItemPaidStatusChoices.NO_PAGADO) & ~Q(items__status=ItemStatusChoices.CANCELADO)),
		total_amount_value=Sum(
			ExpressionWrapper(F('items__quantity') * F('items__unit_price'), output_field=DecimalField(max_digits=10, decimal_places=2)),
			filter=~Q(items__status=ItemStatusChoices.CANCELADO),
		),
		pending_amount_value=Sum(
			ExpressionWrapper(F('items__quantity') * F('items__unit_price'), output_field=DecimalField(max_digits=10, decimal_places=2)),
			filter=Q(items__paid_status=ItemPaidStatusChoices.NO_PAGADO) & ~Q(items__status=ItemStatusChoices.CANCELADO),
		),
	)


def get_order_payment_summary(order):
	amount_expr = ExpressionWrapper(F('quantity') * F('unit_price'), output_field=DecimalField(max_digits=10, decimal_places=2))
	aggregated = order.items.aggregate(
		total_amount=Sum(amount_expr, filter=~Q(status=ItemStatusChoices.CANCELADO)),
		pending_amount=Sum(amount_expr, filter=Q(paid_status=ItemPaidStatusChoices.NO_PAGADO) & ~Q(status=ItemStatusChoices.CANCELADO)),
		paid_amount=Sum(amount_expr, filter=Q(paid_status=ItemPaidStatusChoices.PAGADO) & ~Q(status=ItemStatusChoices.CANCELADO)),
	)
	pending_amount = aggregated['pending_amount'] or Decimal('0.00')
	return {
		'total_amount': aggregated['total_amount'] or Decimal('0.00'),
		'pending_amount': pending_amount,
		'paid_amount': aggregated['paid_amount'] or Decimal('0.00'),
		'can_close': order.status == OrderStatusChoices.ABIERTA and pending_amount == Decimal('0.00'),
	}


@transaction.atomic
def update_order_item_unit_price(item_id, unit_price, changed_by=None, note=''):
	try:
		new_unit_price = Decimal(unit_price or '0').quantize(Decimal('0.01'))
	except (InvalidOperation, TypeError):
		raise ValueError('Captura un precio válido.')
	note = (note or '').strip()

	if new_unit_price < 0:
		raise ValueError('El precio no puede ser negativo.')

	item = OrderItem.objects.select_related('order', 'product').select_for_update().get(pk=item_id)
	if item.order.status != OrderStatusChoices.ABIERTA:
		raise ValueError('Solo se puede cambiar el precio en comandas abiertas.')
	if item.status == ItemStatusChoices.CANCELADO:
		raise ValueError('No se puede cambiar el precio de un producto cancelado.')
	if item.paid_status == ItemPaidStatusChoices.PAGADO:
		raise ValueError('No se puede cambiar el precio de un producto ya pagado.')

	previous_unit_price = item.unit_price
	item.unit_price = new_unit_price
	item.save(update_fields=['unit_price'])
	price_change = OrderItemPriceChange.objects.create(
		order_item=item,
		previous_unit_price=previous_unit_price,
		new_unit_price=new_unit_price,
		note=note,
		changed_by=changed_by,
	)
	order = item.order
	summary = get_order_payment_summary(order)
	return item, summary, price_change


@transaction.atomic
def process_order_payment(order_id, item_ids, cash_amount, card_amount, transfer_amount, user):
	order = Order.objects.select_for_update().select_related('workday').get(pk=order_id)
	if order.status != OrderStatusChoices.ABIERTA:
		raise ValueError('La comanda ya esta cerrada.')

	if not item_ids:
		raise ValueError('Selecciona al menos un producto para cobrar.')

	selected_ids = []
	for raw_id in item_ids:
		try:
			parsed_id = int(raw_id)
		except (TypeError, ValueError):
			continue
		if parsed_id > 0 and parsed_id not in selected_ids:
			selected_ids.append(parsed_id)

	if not selected_ids:
		raise ValueError('Selecciona al menos un producto válido para cobrar.')

	items = list(
		OrderItem.objects.select_for_update()
		.filter(order=order, id__in=selected_ids)
		.exclude(status=ItemStatusChoices.CANCELADO)
		.exclude(paid_status=ItemPaidStatusChoices.PAGADO)
	)
	if len(items) != len(selected_ids):
		raise ValueError('Algunos productos seleccionados ya no estan disponibles para cobro.')

	selected_total = sum((item.total for item in items), Decimal('0.00')).quantize(Decimal('0.01'))

	try:
		cash_value = Decimal(cash_amount or '0').quantize(Decimal('0.01'))
		card_value = Decimal(card_amount or '0').quantize(Decimal('0.01'))
		transfer_value = Decimal(transfer_amount or '0').quantize(Decimal('0.01'))
	except (InvalidOperation, TypeError):
		raise ValueError('Captura montos válidos para el pago.')

	if cash_value < 0 or card_value < 0 or transfer_value < 0:
		raise ValueError('Los montos de pago no pueden ser negativos.')

	payment_total = (cash_value + card_value + transfer_value).quantize(Decimal('0.01'))
	if payment_total != selected_total:
		raise ValueError('La suma de efectivo, tarjeta y transferencia debe coincidir con el total seleccionado.')

	payment = OrderPayment.objects.create(
		order=order,
		workday=order.workday,
		created_by=user,
		cash_amount=cash_value,
		card_amount=card_value,
		transfer_amount=transfer_value,
		total_amount=payment_total,
	)

	for item in items:
		OrderItemPayment.objects.create(payment=payment, order_item=item, amount=item.total)
		item.paid_status = ItemPaidStatusChoices.PAGADO
		item.paid_at = payment.created_at
		item.paid_by = user
	OrderItem.objects.bulk_update(items, ['paid_status', 'paid_at', 'paid_by'])

	summary = get_order_payment_summary(order)
	return {
		'payment': payment,
		'paid_item_ids': [item.id for item in items],
		'selected_total': selected_total,
		'summary': summary,
	}


@transaction.atomic
def create_order_from_forms(form, formset, user):
	workday = get_active_workday()
	if not workday:
		raise ValueError('No hay un día de trabajo abierto. Abre el día de trabajo para crear comandas.')
	order = form.save(commit=False)
	order.created_by = user
	order.workday = workday
	order.save()
	formset.instance = order
	items = formset.save(commit=False)
	for item in items:
		item.order = order
		item.unit_price = item.product.price
		item.commanded_by = user
		item.save()
	return order


@transaction.atomic
def create_order_from_payload(form, items_payload, user, session_key=None):
	cleanup_stale_draft_reservations()
	workday = get_active_workday()
	if not workday:
		raise ValueError('No hay un día de trabajo abierto. Abre el día de trabajo para crear comandas.')
	if not items_payload:
		raise ValueError('Agrega al menos un producto a la comanda.')

	order = form.save(commit=False)
	order.created_by = user
	order.workday = workday
	order.save()

	for raw_item in items_payload:
		product_id = raw_item.get('product_id')
		variant_id = raw_item.get('variant_id')
		reservation_token = raw_item.get('reservation_token')
		requested_quantity = raw_item.get('quantity') or 1
		notes = (raw_item.get('notes') or '').strip()
		supply_names = raw_item.get('supply_names') or []

		if product_id is None:
			raise ValueError('Uno de los productos del borrador ya no es válido.')
		product_id = int(product_id)
		variant_id = int(variant_id) if variant_id else None

		if reservation_token:
			if not session_key:
				raise ValueError('La sesión del borrador no está disponible. Vuelve a capturar la comanda.')
			product, variant, unit_price, quantity = _consume_draft_reservation(
				session_key,
				reservation_token,
				product_id,
				variant_id,
				requested_quantity,
			)
		else:
			product, variant, unit_price, quantity = _reserve_item_stock(product_id, variant_id, requested_quantity)

		extra_notes = []
		if variant:
			extra_notes.append(variant.name)
		if supply_names:
			extra_notes.append(', '.join(supply_names))
		if extra_notes:
			notes = (notes + ' | ' if notes else '') + ' | '.join(extra_notes)

		diner_name = (raw_item.get('diner_name') or '').strip()

		OrderItem.objects.create(
			order=order,
			product=product,
			variant=variant,
			commanded_by=user,
			quantity=quantity,
			unit_price=Decimal(unit_price),
			notes=notes,
			diner_name=diner_name,
		)

	return order


@transaction.atomic
def add_items_to_order(order, items_payload, user=None):
	"""Agrega items a una comanda ya existente (debe estar ABIERTA)."""
	if order.status != OrderStatusChoices.ABIERTA:
		raise ValueError('Solo se pueden agregar productos a comandas abiertas.')
	if not items_payload:
		raise ValueError('Agrega al menos un producto.')

	created_items = []
	for raw_item in items_payload:
		product_id = raw_item.get('product_id')
		variant_id = raw_item.get('variant_id')
		requested_quantity = raw_item.get('quantity') or 1
		notes = (raw_item.get('notes') or '').strip()
		supply_names = raw_item.get('supply_names') or []

		product, variant, unit_price, quantity = _reserve_item_stock(product_id, variant_id, requested_quantity)

		extra_notes = []
		if variant:
			extra_notes.append(variant.name)
		if supply_names:
			extra_notes.append(', '.join(supply_names))
		if extra_notes:
			notes = (notes + ' | ' if notes else '') + ' | '.join(extra_notes)

		diner_name = (raw_item.get('diner_name') or '').strip()
		waiter_name = (raw_item.get('waiter_name') or '').strip()

		item = OrderItem.objects.create(
			order=order,
			product=product,
			variant=variant,
			commanded_by=user,
			quantity=quantity,
			unit_price=Decimal(unit_price),
			notes=notes,
			diner_name=diner_name,
			waiter_name=waiter_name,
		)
		created_items.append(item)

	return created_items


@transaction.atomic
def transition_order_item_status(item_id, allowed_statuses, target_status, user=None):
	item = OrderItem.objects.select_related('order', 'product').select_for_update().get(pk=item_id)
	if item.status in allowed_statuses:
		item.status = target_status
		update_fields = ['status']
		if target_status in [ItemStatusChoices.EN_PREPARACION, ItemStatusChoices.POR_ENTREGAR] and user and not item.prepared_by_id:
			item.prepared_by = user
			update_fields.append('prepared_by')
		if target_status == ItemStatusChoices.ENTREGADO and user:
			item.delivered_by = user
			update_fields.append('delivered_by')
		item.save(update_fields=update_fields)
	return item


@transaction.atomic
def cancel_order_item(item_id):
	item = OrderItem.objects.select_related('order').select_for_update().get(pk=item_id)
	cancelled = False
	if item.status != ItemStatusChoices.ENTREGADO and item.paid_status != ItemPaidStatusChoices.PAGADO:
		item.status = ItemStatusChoices.CANCELADO
		item.save(update_fields=['status'])
		cancelled = True
	return item, cancelled


@transaction.atomic
def close_order(order_id):
	order = Order.objects.select_for_update().get(pk=order_id)
	was_closed = order.status == OrderStatusChoices.PAGADA
	has_unpaid_items = order.items.filter(paid_status=ItemPaidStatusChoices.NO_PAGADO).exclude(status=ItemStatusChoices.CANCELADO).exists()
	if order.status == OrderStatusChoices.ABIERTA and has_unpaid_items:
		raise ValueError('No se puede cerrar la comanda mientras existan productos sin pagar.')
	if not was_closed:
		order.status = OrderStatusChoices.PAGADA
		order.closed_at = timezone.now()
		order.save(update_fields=['status', 'closed_at'])
	return order, not was_closed