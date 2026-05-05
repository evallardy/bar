from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView
from django.db.models import DecimalField, F, Sum, Value
from django.db.models.functions import Coalesce
from django.core.files.storage import default_storage
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils import timezone
from django.views import View
from django.views.generic import DetailView, FormView, ListView, RedirectView, TemplateView
from decimal import Decimal
import json

from .forms import (
	OrderForm,
	OrderItemFormSet,
	ProductForm,
	ProductSupplyForm,
	ProductVariantEditForm,
	ProductVariantForm,
	SupplyForm,
	UserCreateForm,
	UserUpdateForm,
)
from .models import (
	AreaChoices,
	ItemStatusChoices,
	OrderItem,
	OrderPayment,
	Product,
	ProductSupply,
	ProductVariant,
	Supply,
	UserAccess,
	WorkDay,
)
from .services import (
	BAR_AREAS,
	HOME_MODULES,
	add_items_to_order,
	build_available_product_catalog,
	cancel_order_item,
	close_workday,
	close_order,
	create_order_from_forms,
	create_order_from_payload,
	get_admin_metrics,
	get_active_workday,
	get_cash_orders_queryset,
	get_delivery_items,
	get_home_metrics,
	get_order_payment_summary,
	get_order_detail_queryset,
	get_orders_with_items,
	get_production_items,
	get_recent_orders,
	group_order_items,
	open_workday,
	process_order_payment,
	transition_order_item_status,
)

User = get_user_model()

ACCESS_FIELD_MAP = {
	'menu': 'can_menu',
	'administrador': 'can_administrador',
	'comanda': 'can_comanda',
	'cocina': 'can_cocina',
	'bar': 'can_bar',
	'entregas': 'can_entregas',
	'caja': 'can_caja',
}

MODULE_ACCESS_BY_URL = {
	'home': 'menu',
	'admin-panel': 'administrador',
	'comanda-list': 'comanda',
	'kitchen-board': 'cocina',
	'bar-board': 'bar',
	'deliveries-board': 'entregas',
	'cash-list': 'caja',
}


def get_user_access_profile(user):
	if not user.is_authenticated:
		return None
	profile, _ = UserAccess.objects.get_or_create(user=user)
	return profile


def is_admin_role(user):
	if not user.is_authenticated:
		return False
	if user.is_superuser:
		return True
	profile = get_user_access_profile(user)
	if profile and profile.is_admin_role:
		return True
	return user.groups.filter(name='administrador').exists()


def user_has_access(user, access_key):
	if not user.is_authenticated:
		return False
	if is_admin_role(user):
		return True
	profile = get_user_access_profile(user)
	field_name = ACCESS_FIELD_MAP.get(access_key)
	if not field_name or not profile:
		return False
	return bool(getattr(profile, field_name, False))


def is_admin_user(user):
	return is_admin_role(user)


def is_ajax_request(request):
	return request.headers.get('x-requested-with') == 'XMLHttpRequest'


class AdminAccessMixin(UserPassesTestMixin):
	def test_func(self):
		return user_has_access(self.request.user, 'administrador')


class RoleAdminOnlyMixin(UserPassesTestMixin):
	def test_func(self):
		return is_admin_role(self.request.user)


class ModuleAccessMixin(UserPassesTestMixin):
	required_access = None

	def test_func(self):
		if not self.required_access:
			return True
		return user_has_access(self.request.user, self.required_access)


class IndexRedirectView(RedirectView):
	permanent = False

	def get_redirect_url(self, *args, **kwargs):
		if self.request.user.is_authenticated:
			return reverse_lazy('home')
		return reverse_lazy('login')


class AjaxLoginView(LoginView):
	template_name = 'login.html'

	def form_valid(self, form):
		response = super().form_valid(form)
		if is_ajax_request(self.request):
			return JsonResponse(
				{
					'ok': True,
					'message': 'Bienvenido al turno.',
					'redirect_url': self.get_success_url(),
				}
			)
		return response

	def form_invalid(self, form):
		if is_ajax_request(self.request):
			return JsonResponse({'ok': False, 'message': 'Usuario o contraseña incorrectos.'}, status=400)
		return super().form_invalid(form)


class UserLogoutView(View):
	http_method_names = ['get', 'post']

	def get(self, request, *args, **kwargs):
		auth_logout(request)
		return redirect('login')

	def post(self, request, *args, **kwargs):
		auth_logout(request)
		return redirect('login')


class HomeView(LoginRequiredMixin, ModuleAccessMixin, TemplateView):
	template_name = 'home.html'
	required_access = 'menu'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['modules'] = [
			module for module in HOME_MODULES if user_has_access(self.request.user, MODULE_ACCESS_BY_URL.get(module['url'], 'menu'))
		]
		context['areas'] = BAR_AREAS
		context['metrics'] = get_home_metrics()
		context['is_admin_user'] = is_admin_user(self.request.user)
		return context


class AdminPanelView(LoginRequiredMixin, ModuleAccessMixin, TemplateView):
	template_name = 'core/admin_panel.html'
	required_access = 'administrador'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		active_workday = get_active_workday()
		workdays = WorkDay.objects.order_by('-opened_at')[:30]
		workday_param = self.request.GET.get('workday', '').strip()
		selected_workday_value = ''
		selected_workday_id = None
		if workday_param == 'all':
			selected_workday_value = 'all'
			selected_workday_id = None
		elif workday_param.isdigit():
			selected_workday_value = workday_param
			selected_workday_id = int(workday_param)
		elif active_workday:
			selected_workday_value = str(active_workday.id)
			selected_workday_id = active_workday.id
		else:
			today_workday = WorkDay.objects.filter(opened_at__date=timezone.localdate()).order_by('-opened_at').first()
			if today_workday:
				selected_workday_value = str(today_workday.id)
				selected_workday_id = today_workday.id
		context['metrics'] = get_admin_metrics()
		context['product_form'] = kwargs.get('product_form', ProductForm(prefix='product'))
		context['supply_form'] = kwargs.get('supply_form', SupplyForm(prefix='supply'))
		context['variant_form'] = kwargs.get('variant_form', ProductVariantForm(prefix='variant'))
		context['recipe_form'] = kwargs.get('recipe_form', ProductSupplyForm(prefix='recipe'))
		context['products'] = Product.objects.prefetch_related('variants').all()
		context['supplies'] = Supply.objects.all()
		context['variants'] = ProductVariant.objects.select_related('product').filter(is_active=True)
		context['recipes'] = ProductSupply.objects.select_related('product', 'supply').all()
		orders_limit = None if selected_workday_value == 'all' else 8
		sales_orders = get_recent_orders(limit=None, workday_id=selected_workday_id)
		sales_total_amount = OrderItem.objects.filter(order__in=sales_orders).exclude(status=ItemStatusChoices.CANCELADO).aggregate(
			total=Coalesce(
				Sum(
					F('quantity') * F('unit_price'),
					output_field=DecimalField(max_digits=10, decimal_places=2),
				),
				Value(Decimal('0.00')),
				output_field=DecimalField(max_digits=10, decimal_places=2),
			),
		)['total']
		sales_total_paid = OrderPayment.objects.filter(order__in=sales_orders).aggregate(
			total=Coalesce(
				Sum('total_amount'),
				Value(Decimal('0.00')),
				output_field=DecimalField(max_digits=10, decimal_places=2),
			),
		)['total']
		context['recent_orders'] = sales_orders if orders_limit is None else sales_orders[:orders_limit]
		context['sales_total_amount'] = sales_total_amount
		context['sales_total_paid'] = sales_total_paid
		context['workdays'] = workdays
		context['selected_workday_id'] = selected_workday_id
		context['selected_workday_value'] = selected_workday_value
		context['active_workday'] = active_workday
		return context

	def post(self, request, *args, **kwargs):
		product_form = ProductForm(prefix='product')
		supply_form = SupplyForm(prefix='supply')
		variant_form = ProductVariantForm(prefix='variant')
		recipe_form = ProductSupplyForm(prefix='recipe')
		form_kind = request.POST.get('form_kind')
		if form_kind == 'product':
			product_form = ProductForm(request.POST, prefix='product')
			if product_form.is_valid():
				product = product_form.save()
				messages.success(request, 'Producto guardado correctamente.')
				if is_ajax_request(request):
					return JsonResponse(
						{
							'ok': True,
							'message': 'Producto guardado correctamente.',
							'product': {
							'id': product.pk,
							'name': product.name,
							'category': product.get_category_display(),
							'category_value': product.category,
							'price': str(product.price),
							'stock': product.stock,
							'description': product.description,
							'is_active': product.is_active,
						},
						}
					)
				return redirect('admin-panel')
		elif form_kind == 'supply':
			supply_form = SupplyForm(request.POST, prefix='supply')
			if supply_form.is_valid():
				supply = supply_form.save()
				messages.success(request, 'Insumo guardado correctamente.')
				if is_ajax_request(request):
					return JsonResponse(
						{
							'ok': True,
							'message': 'Insumo guardado correctamente.',
							'supply': {
								'id': supply.pk,
								'name': supply.name,
								'is_available': supply.is_available,
							},
						}
					)
				return redirect('admin-panel')
		elif form_kind == 'variant':
			variant_form = ProductVariantForm(request.POST, prefix='variant')
			if variant_form.is_valid():
				variant = variant_form.save()
				variant.product.refresh_from_db(fields=['stock'])
				messages.success(request, 'Variante guardada correctamente.')
				if is_ajax_request(request):
					return JsonResponse(
						{
							'ok': True,
							'message': 'Variante guardada correctamente.',
							'variant': {
								'id': variant.pk,
								'product': variant.product.name,
								'product_id': variant.product.pk,
								'name': variant.name,
								'price_delta': str(variant.price_delta),
								'stock': variant.stock,
								'is_active': variant.is_active,
								'product_stock': variant.product.stock,
							},
						}
					)
				return redirect('admin-panel')
		elif form_kind == 'recipe':
			recipe_form = ProductSupplyForm(request.POST, prefix='recipe')
			if recipe_form.is_valid():
				recipe = recipe_form.save()
				messages.success(request, 'Insumo de producto guardado correctamente.')
				if is_ajax_request(request):
					return JsonResponse(
						{
							'ok': True,
							'message': 'Insumo de producto guardado correctamente.',
							'recipe': {
								'id': recipe.pk,
								'product': recipe.product.name,
								'product_id': recipe.product.pk,
								'supply': recipe.supply.name,
								'supply_id': recipe.supply.pk,
							},
						}
					)
				return redirect('admin-panel')
		elif form_kind == 'workday_open':
			workday, created = open_workday(request.user)
			if created:
				messages.success(request, f'Día de trabajo #{workday.pk} abierto correctamente.')
			else:
				messages.info(request, f'Ya hay un día de trabajo abierto: #{workday.pk}.')
			return redirect('admin-panel')
		elif form_kind == 'workday_close':
			workday, pending_orders, closed = close_workday(request.user)
			if not closed:
				messages.info(request, 'No hay un día de trabajo abierto para cerrar.')
			elif pending_orders:
				messages.warning(request, f'Día #{workday.pk} cerrado con {pending_orders} comandas pendientes.')
			else:
				messages.success(request, f'Día #{workday.pk} cerrado correctamente sin comandas pendientes.')
			return redirect('admin-panel')
		if is_ajax_request(request):
			return JsonResponse({'ok': False, 'message': 'No se pudo guardar el formulario.'}, status=400)
		return self.render_to_response(self.get_context_data(product_form=product_form, supply_form=supply_form, variant_form=variant_form, recipe_form=recipe_form))


class ComandaListView(LoginRequiredMixin, ModuleAccessMixin, ListView):
	template_name = 'core/comanda_list.html'
	context_object_name = 'orders'
	required_access = 'comanda'

	def get_queryset(self):
		return get_orders_with_items()

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		for order in context['orders']:
			summary = get_order_payment_summary(order)
			order.can_close = order.status == 'ABIERTA' and (order.total_paid or 0) == (order.total_amount_value or 0)
			order.pending_amount = summary['pending_amount']
		return context


class ComandaCreateView(LoginRequiredMixin, ModuleAccessMixin, FormView):
	template_name = 'core/comanda_form.html'
	form_class = OrderForm
	required_access = 'comanda'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['product_catalog'] = build_available_product_catalog()
		return context

	def form_valid(self, form):
		items_raw = self.request.POST.get('items_json', '[]')
		try:
			items_payload = json.loads(items_raw)
		except json.JSONDecodeError:
			items_payload = []
		if not items_payload:
			if is_ajax_request(self.request):
				return JsonResponse({'ok': False, 'message': 'Agrega al menos un producto a la comanda.'}, status=400)
			messages.error(self.request, 'Agrega al menos un producto a la comanda.')
			return self.render_to_response(self.get_context_data(form=form))
		try:
			order = create_order_from_payload(form, items_payload, self.request.user)
		except ValueError as exc:
			if is_ajax_request(self.request):
				return JsonResponse({'ok': False, 'message': str(exc)}, status=400)
			messages.error(self.request, str(exc))
			return self.render_to_response(self.get_context_data(form=form))
		messages.success(self.request, f'Comanda #{order.id} creada para la mesa {order.table_number}.')
		if is_ajax_request(self.request):
			return JsonResponse(
				{
					'ok': True,
					'message': f'Comanda #{order.id} creada para la mesa {order.table_number}.',
					'order_id': order.id,
					'redirect_url': reverse_lazy('comanda-detail', kwargs={'order_id': order.id}),
				}
			)
		return redirect('comanda-detail', order_id=order.id)

	def form_invalid(self, form):
		if is_ajax_request(self.request):
			return JsonResponse({'ok': False, 'message': 'Revisa los datos generales de la comanda.'}, status=400)
		return super().form_invalid(form)


class ComandaDetailView(LoginRequiredMixin, ModuleAccessMixin, DetailView):
	template_name = 'core/cash_detail.html'
	context_object_name = 'order'
	pk_url_kwarg = 'order_id'
	required_access = 'comanda'

	def get_queryset(self):
		return get_order_detail_queryset()

	def _build_catalog(self):
		return build_available_product_catalog()

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		grouped = group_order_items(self.object)
		context['grouped_items'] = grouped
		context['show_close_action'] = False
		context['is_admin_user'] = is_admin_user(self.request.user)
		if self.object.status == 'ABIERTA':
			context['product_catalog'] = self._build_catalog()
			# Comensales únicos ya en la comanda: items con nombre + 'Mesa' si hay sin nombre
			raw = list(
				self.object.items.values_list('diner_name', flat=True).distinct().order_by('diner_name')
			)
			diners = []
			has_unnamed = any(d == '' or d is None for d in raw)
			if has_unnamed:
				diners.append({'value': '', 'label': 'Mesa'})
			diners += [{'value': d, 'label': d} for d in raw if d]
			context['existing_diners'] = diners
		else:
			context['product_catalog'] = []
			context['existing_diners'] = []
		return context


class OrderItemAddView(LoginRequiredMixin, ModuleAccessMixin, View):
	http_method_names = ['post']
	required_access = 'comanda'

	def post(self, request, order_id, *args, **kwargs):
		order = get_object_or_404(get_order_detail_queryset(), pk=order_id)
		if order.status != 'ABIERTA':
			if is_ajax_request(request):
				return JsonResponse({'ok': False, 'message': 'La comanda ya no está abierta.'}, status=400)
			messages.error(request, 'La comanda ya no está abierta.')
			return redirect('comanda-detail', order_id=order_id)

		items_raw = request.POST.get('items_json', '[]')
		try:
			items_payload = json.loads(items_raw)
		except json.JSONDecodeError:
			items_payload = []

		try:
			new_items = add_items_to_order(order, items_payload)
		except ValueError as exc:
			if is_ajax_request(request):
				return JsonResponse({'ok': False, 'message': str(exc)}, status=400)
			messages.error(request, str(exc))
			return redirect('comanda-detail', order_id=order_id)

		if is_ajax_request(request):
			items_data = [
				{
					'id': item.pk,
					'product_name': item.product.name,
					'variant_name': item.variant.name if item.variant else '',
					'diner_name': item.diner_name or 'Mesa',
					'waiter_name': item.waiter_name or '-',
					'quantity': item.quantity,
					'unit_price': str(item.unit_price),
					'total': str(item.total),
					'notes': item.notes,
					'status': item.status,
					'status_display': item.get_status_display(),
					'paid_status': item.paid_status,
					'payment_status_display': item.payment_status_label,
				}
				for item in new_items
			]
			return JsonResponse({'ok': True, 'message': f'{len(new_items)} producto(s) agregado(s).', 'items': items_data})

		messages.success(request, f'{len(new_items)} producto(s) agregado(s) a la comanda.')
		return redirect('comanda-detail', order_id=order_id)


class ProductionBoardBaseView(LoginRequiredMixin, ModuleAccessMixin, ListView):
	template_name = 'core/production_board.html'
	context_object_name = 'items'
	area = None
	title = ''

	def get_queryset(self):
		return get_production_items(self.area)

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['title'] = self.title
		context['area'] = self.area
		return context


class KitchenBoardView(ProductionBoardBaseView):
	area = AreaChoices.COCINA
	title = 'Cocina'
	required_access = 'cocina'


class BarBoardView(ProductionBoardBaseView):
	area = AreaChoices.BAR
	title = 'Bar'
	required_access = 'bar'


class ItemActionBaseView(LoginRequiredMixin, ModuleAccessMixin, View):
	allowed_statuses = []
	target_status = None
	required_access = None

	def test_func(self):
		return user_has_access(self.request.user, 'cocina') or user_has_access(self.request.user, 'bar')

	def get(self, request, *args, **kwargs):
		return HttpResponseForbidden('Método no permitido.')

	def get_success_url(self, item):
		return 'kitchen-board' if item.area == AreaChoices.COCINA else 'bar-board'

	def post(self, request, item_id, *args, **kwargs):
		item = transition_order_item_status(item_id, self.allowed_statuses, self.target_status)
		if is_ajax_request(request):
			return JsonResponse(
				{
					'ok': True,
					'item_id': item.id,
					'status': item.status,
					'status_display': item.get_status_display(),
					'paid_status': item.paid_status,
					'payment_status_display': item.payment_status_label,
					'redirect_url': reverse_lazy(self.get_success_url(item)),
				}
			)
		return redirect(self.get_success_url(item))


class ItemStartView(ItemActionBaseView):
	allowed_statuses = [ItemStatusChoices.COMANDADO]
	target_status = ItemStatusChoices.EN_PREPARACION


class ItemReadyView(ItemActionBaseView):
	allowed_statuses = [ItemStatusChoices.COMANDADO, ItemStatusChoices.EN_PREPARACION]
	target_status = ItemStatusChoices.POR_ENTREGAR


class DeliveriesBoardView(LoginRequiredMixin, ModuleAccessMixin, ListView):
	template_name = 'core/deliveries.html'
	context_object_name = 'items'
	required_access = 'entregas'

	def get_queryset(self):
		return get_delivery_items()

class ItemDeliverView(ItemActionBaseView):
	allowed_statuses = [ItemStatusChoices.POR_ENTREGAR]
	target_status = ItemStatusChoices.ENTREGADO
	required_access = 'entregas'

	def test_func(self):
		return user_has_access(self.request.user, 'entregas')

	def get_success_url(self, item):
		return 'deliveries-board'


class ItemCancelView(LoginRequiredMixin, AdminAccessMixin, View):
	def get(self, request, *args, **kwargs):
		return HttpResponseForbidden('Método no permitido.')

	def post(self, request, item_id, *args, **kwargs):
		item, cancelled = cancel_order_item(item_id)
		if cancelled:
			messages.warning(request, 'Producto cancelado en la comanda.')
		if is_ajax_request(request):
			return JsonResponse(
				{
					'ok': True,
					'item_id': item.id,
					'cancelled': cancelled,
					'status': item.status,
					'status_display': item.get_status_display(),
					'paid_status': item.paid_status,
					'payment_status_display': item.payment_status_label,
					'message': 'Producto cancelado en la comanda.' if cancelled else 'No se puede cancelar un producto entregado.',
				}
			)
		return redirect('cash-detail', order_id=item.order_id)


class CashListView(LoginRequiredMixin, ModuleAccessMixin, ListView):
	template_name = 'core/cash_list.html'
	context_object_name = 'orders'
	required_access = 'caja'

	def get_queryset(self):
		return get_cash_orders_queryset()


class CashDetailView(LoginRequiredMixin, ModuleAccessMixin, DetailView):
	template_name = 'core/cash_detail.html'
	context_object_name = 'order'
	pk_url_kwarg = 'order_id'
	required_access = 'caja'

	def get_queryset(self):
		return get_order_detail_queryset()

	def get_back_url(self):
		next_url = self.request.GET.get('next', '').strip()
		if next_url and url_has_allowed_host_and_scheme(
			next_url,
			allowed_hosts={self.request.get_host()},
			require_https=self.request.is_secure(),
		):
			return next_url

		referer = self.request.META.get('HTTP_REFERER', '').strip()
		if referer and url_has_allowed_host_and_scheme(
			referer,
			allowed_hosts={self.request.get_host()},
			require_https=self.request.is_secure(),
		):
			return referer

		return str(reverse_lazy('cash-list'))

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['grouped_items'] = group_order_items(self.object)
		context['show_close_action'] = True
		context['is_admin_user'] = is_admin_user(self.request.user)
		context['payment_summary'] = get_order_payment_summary(self.object)
		context['back_url'] = self.get_back_url()
		return context


class CashPaymentListView(LoginRequiredMixin, ModuleAccessMixin, DetailView):
	template_name = 'core/cash_payment_list.html'
	context_object_name = 'order'
	pk_url_kwarg = 'order_id'
	required_access = 'caja'

	def get_queryset(self):
		return get_order_detail_queryset().prefetch_related('payments__payment_items__order_item', 'payments__created_by', 'payments__workday')

	def get_back_url(self):
		next_url = self.request.GET.get('next', '').strip()
		if next_url and url_has_allowed_host_and_scheme(
			next_url,
			allowed_hosts={self.request.get_host()},
			require_https=self.request.is_secure(),
		):
			return next_url

		referer = self.request.META.get('HTTP_REFERER', '').strip()
		if referer and url_has_allowed_host_and_scheme(
			referer,
			allowed_hosts={self.request.get_host()},
			require_https=self.request.is_secure(),
		):
			return referer

		return str(reverse_lazy('cash-list'))

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['payments'] = self.object.payments.all()
		context['back_url'] = self.get_back_url()
		context['payment_summary'] = get_order_payment_summary(self.object)
		return context


class OrderPaymentView(LoginRequiredMixin, ModuleAccessMixin, View):
	http_method_names = ['post']
	required_access = 'caja'

	def post(self, request, order_id, *args, **kwargs):
		item_ids = request.POST.getlist('item_ids')
		cash_amount = request.POST.get('cash_amount', '0').strip()
		card_amount = request.POST.get('card_amount', '0').strip()
		transfer_amount = request.POST.get('transfer_amount', '0').strip()
		try:
			result = process_order_payment(
				order_id=order_id,
				item_ids=item_ids,
				cash_amount=cash_amount,
				card_amount=card_amount,
				transfer_amount=transfer_amount,
				user=request.user,
			)
		except ValueError as exc:
			if is_ajax_request(request):
				return JsonResponse({'ok': False, 'message': str(exc)}, status=400)
			messages.error(request, str(exc))
			return redirect('cash-detail', order_id=order_id)

		summary = result['summary']
		message = f"Pago registrado por ${result['selected_total']}."
		if is_ajax_request(request):
			return JsonResponse(
				{
					'ok': True,
					'message': message,
					'payment_id': result['payment'].id,
					'paid_item_ids': result['paid_item_ids'],
					'selected_total': str(result['selected_total']),
					'card_amount': str(result['payment'].card_amount),
					'transfer_amount': str(result['payment'].transfer_amount),
					'pending_amount': str(summary['pending_amount']),
					'paid_amount': str(summary['paid_amount']),
					'total_amount': str(summary['total_amount']),
					'can_close_order': summary['can_close'],
				}
			)
		messages.success(request, message)
		return redirect('cash-detail', order_id=order_id)


class OrderPaymentEvidenceView(LoginRequiredMixin, ModuleAccessMixin, View):
	http_method_names = ['post']
	required_access = 'caja'

	def post(self, request, payment_id, *args, **kwargs):
		payment = get_object_or_404(OrderPayment, pk=payment_id)
		card_evidence = request.FILES.get('card_evidence')
		transfer_evidence = request.FILES.get('transfer_evidence')

		if not card_evidence and not transfer_evidence:
			return JsonResponse({'ok': False, 'message': 'Selecciona al menos una evidencia para guardar.'}, status=400)

		for uploaded_file, label in ((card_evidence, 'tarjeta'), (transfer_evidence, 'transferencia')):
			if uploaded_file and not str(uploaded_file.content_type or '').startswith('image/'):
				return JsonResponse({'ok': False, 'message': f'La evidencia de {label} debe ser una imagen.'}, status=400)

		previous_card_name = payment.card_evidence.name if payment.card_evidence else ''
		previous_transfer_name = payment.transfer_evidence.name if payment.transfer_evidence else ''

		if card_evidence:
			payment.card_evidence = card_evidence
		if transfer_evidence:
			payment.transfer_evidence = transfer_evidence
		payment.save(update_fields=['card_evidence', 'transfer_evidence'])

		for old_name, current_file in ((previous_card_name, payment.card_evidence), (previous_transfer_name, payment.transfer_evidence)):
			current_name = current_file.name if current_file else ''
			if old_name and old_name != current_name:
				try:
					default_storage.delete(old_name)
				except OSError:
					pass

		return JsonResponse(
			{
				'ok': True,
				'message': 'Evidencia guardada correctamente.',
				'has_card_evidence': bool(payment.card_evidence),
				'has_transfer_evidence': bool(payment.transfer_evidence),
				'card_evidence_url': payment.card_evidence.url if payment.card_evidence else '',
				'transfer_evidence_url': payment.transfer_evidence.url if payment.transfer_evidence else '',
			}
		)


class CloseOrderView(LoginRequiredMixin, ModuleAccessMixin, View):
	http_method_names = ['post']
	success_url = reverse_lazy('cash-list')
	required_access = 'caja'

	def post(self, request, order_id, *args, **kwargs):
		try:
			order, closed = close_order(order_id)
		except ValueError as exc:
			if is_ajax_request(request):
				return JsonResponse({'ok': False, 'message': str(exc)}, status=400)
			messages.error(request, str(exc))
			return redirect('cash-detail', order_id=order_id)
		if closed:
			messages.success(request, f'Comanda #{order.id} cobrada correctamente.')
			message = f'Comanda #{order.id} cobrada correctamente.'
		else:
			messages.info(request, f'La comanda #{order.id} ya estaba cobrada.')
			message = f'La comanda #{order.id} ya estaba cobrada.'
		if is_ajax_request(request):
			return JsonResponse(
				{
					'ok': True,
					'closed': closed,
					'order_id': order.id,
					'order_status': order.status,
					'message': message,
					'redirect_url': str(self.success_url),
				}
			)
		return redirect(self.success_url)


class ProductUpdateView(LoginRequiredMixin, AdminAccessMixin, View):
	http_method_names = ['post']

	def post(self, request, pk):
		product = get_object_or_404(Product, pk=pk)
		has_variants = product.variants.filter(is_active=True).exists()
		form_data = request.POST.copy()
		if has_variants and 'stock' not in form_data:
			form_data['stock'] = str(product.stock)
		form = ProductForm(form_data, instance=product)
		if form.is_valid():
			product = form.save()
			if has_variants:
				product.recalculate_stock_from_variants()
				product.refresh_from_db(fields=['stock'])
			return JsonResponse({
				'ok': True,
				'product': {
					'id': product.pk,
					'name': product.name,
					'category': product.get_category_display(),
					'category_value': product.category,
					'price': str(product.price),
					'stock': product.stock,
					'description': product.description,
					'is_active': product.is_active,
				},
			})
		return JsonResponse({'ok': False, 'errors': form.errors.get_json_data()}, status=400)


class ProductVariantUpdateView(LoginRequiredMixin, AdminAccessMixin, View):
	http_method_names = ['post']

	def post(self, request, pk):
		variant = get_object_or_404(ProductVariant, pk=pk)
		form = ProductVariantEditForm(request.POST, instance=variant)
		if form.is_valid():
			variant = form.save()
			variant.product.refresh_from_db(fields=['stock'])
			return JsonResponse({
				'ok': True,
				'variant': {
					'id': variant.pk,
					'product': variant.product.name,
					'product_id': variant.product.pk,
					'name': variant.name,
					'price_delta': str(variant.price_delta),
					'stock': variant.stock,
					'is_active': variant.is_active,
					'product_stock': variant.product.stock,
				},
			})
		return JsonResponse({'ok': False, 'errors': form.errors.get_json_data()}, status=400)


class SupplyUpdateView(LoginRequiredMixin, AdminAccessMixin, View):
	http_method_names = ['post']

	def post(self, request, pk):
		supply = get_object_or_404(Supply, pk=pk)
		form = SupplyForm(request.POST, instance=supply)
		if form.is_valid():
			supply = form.save()
			return JsonResponse(
				{
					'ok': True,
					'supply': {
						'id': supply.pk,
						'name': supply.name,
						'is_available': supply.is_available,
					},
				}
			)
		return JsonResponse({'ok': False, 'errors': form.errors.get_json_data()}, status=400)


class ProductSupplyUpdateView(LoginRequiredMixin, AdminAccessMixin, View):
	http_method_names = ['post']

	def post(self, request, pk):
		recipe = get_object_or_404(ProductSupply, pk=pk)
		form = ProductSupplyForm(request.POST, instance=recipe)
		if form.is_valid():
			recipe = form.save()
			return JsonResponse(
				{
					'ok': True,
					'recipe': {
						'id': recipe.pk,
						'product': recipe.product.name,
						'product_id': recipe.product.pk,
						'supply': recipe.supply.name,
						'supply_id': recipe.supply.pk,
					},
				}
			)
		return JsonResponse({'ok': False, 'errors': form.errors.get_json_data()}, status=400)


class ProductVariantDeleteView(LoginRequiredMixin, AdminAccessMixin, View):
	http_method_names = ['post']

	def post(self, request, pk):
		variant = get_object_or_404(ProductVariant, pk=pk)
		product = variant.product
		variant_id = variant.pk
		variant.delete()
		product.refresh_from_db(fields=['stock'])
		return JsonResponse(
			{
				'ok': True,
				'variant_id': variant_id,
				'product_id': product.pk,
				'product_stock': product.stock,
			}
		)


class ProductSupplyDeleteView(LoginRequiredMixin, AdminAccessMixin, View):
	http_method_names = ['post']

	def post(self, request, pk):
		recipe = get_object_or_404(ProductSupply, pk=pk)
		recipe_id = recipe.pk
		recipe.delete()
		return JsonResponse({'ok': True, 'recipe_id': recipe_id})


class UserListView(LoginRequiredMixin, RoleAdminOnlyMixin, ListView):
	template_name = 'core/user_list.html'
	context_object_name = 'users'

	def get_queryset(self):
		users = User.objects.order_by('username')
		for user in users:
			UserAccess.objects.get_or_create(user=user)
		return User.objects.select_related('access_profile').order_by('username')


class UserCreateView(LoginRequiredMixin, RoleAdminOnlyMixin, FormView):
	template_name = 'core/user_form.html'
	form_class = UserCreateForm
	success_url = reverse_lazy('user-list')

	def form_valid(self, form):
		form.save()
		messages.success(self.request, 'Usuario creado correctamente.')
		return redirect(self.success_url)


class UserUpdateView(LoginRequiredMixin, RoleAdminOnlyMixin, FormView):
	template_name = 'core/user_form.html'
	form_class = UserUpdateForm
	success_url = reverse_lazy('user-list')

	def dispatch(self, request, *args, **kwargs):
		self.user_obj = get_object_or_404(User, pk=kwargs['pk'])
		return super().dispatch(request, *args, **kwargs)

	def get_form_kwargs(self):
		kwargs = super().get_form_kwargs()
		kwargs['instance'] = self.user_obj
		return kwargs

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['editing_user'] = self.user_obj
		return context

	def form_valid(self, form):
		updated_user = form.save()
		if self.request.user == updated_user:
			messages.info(self.request, 'Tu perfil fue actualizado. Si cambiaste contraseña, vuelve a iniciar sesión.')
		else:
			messages.success(self.request, 'Usuario actualizado correctamente.')
		return redirect(self.success_url)


class UserDeleteView(LoginRequiredMixin, RoleAdminOnlyMixin, View):
	http_method_names = ['post']
	success_url = reverse_lazy('user-list')

	def post(self, request, pk, *args, **kwargs):
		user_obj = get_object_or_404(User, pk=pk)
		if request.user == user_obj:
			messages.error(request, 'No puedes eliminar tu propio usuario en esta pantalla.')
			return redirect(self.success_url)
		username = user_obj.username
		user_obj.delete()
		messages.success(request, f'Usuario {username} eliminado correctamente.')
		return redirect(self.success_url)
