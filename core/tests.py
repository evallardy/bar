from django.contrib.sessions.models import Session
from django.test import Client, TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal

from .forms import OrderForm, OrderItemFormSet
from .models import DraftOrderReservation, ItemStatusChoices, Order, OrderItem, OrderItemPriceChange, OrderStatusChoices, Product, ProductCategoryChoices, ProductVariant, Supply, UserAccess, WorkDay
from .services import cancel_order_item, close_order, create_order_from_forms, create_order_from_payload, get_cash_orders_queryset, get_home_metrics, release_all_draft_items, release_draft_item, reserve_draft_item, transition_order_item_status


class ServiceLayerTests(TestCase):
	def setUp(self):
		self.user = get_user_model().objects.create_user(username='tester', password='Test12345!')
		self.workday = WorkDay.objects.create(opened_by=self.user)
		self.product_food = Product.objects.create(
			name='Hamburguesa',
			category=ProductCategoryChoices.COMIDA,
			price='120.00',
		)
		self.product_drink = Product.objects.create(
			name='Mojito',
			category=ProductCategoryChoices.BEBIDA,
			price='90.00',
		)
		Supply.objects.create(
			name='Limones',
			is_available=False,
		)

	def _create_order_with_item(self, item_status=ItemStatusChoices.COMANDADO):
		order = Order.objects.create(
			table_number=7,
			workday=self.workday,
			created_by=self.user,
		)
		item = OrderItem.objects.create(
			order=order,
			product=self.product_food,
			waiter_name='Luis',
			quantity=1,
			unit_price=self.product_food.price,
			status=item_status,
		)
		return order, item

	def test_create_order_from_forms_sets_unit_price(self):
		form = OrderForm(
			data={
				'table_number': 3,
				'notes': 'Mesa cerca de ventana',
			}
		)
		formset = OrderItemFormSet(
			data={
				'items-TOTAL_FORMS': '1',
				'items-INITIAL_FORMS': '0',
				'items-MIN_NUM_FORMS': '0',
				'items-MAX_NUM_FORMS': '1000',
				'items-0-product': str(self.product_drink.id),
				'items-0-diner_name': 'Pedro',
				'items-0-quantity': '2',
				'items-0-notes': 'Sin azucar',
			}
		)

		self.assertTrue(form.is_valid())
		self.assertTrue(formset.is_valid())

		order = create_order_from_forms(form, formset, self.user)
		item = order.items.get()

		self.assertEqual(order.created_by, self.user)
		self.assertEqual(item.unit_price, Decimal('90.00'))
		self.assertEqual(item.status, ItemStatusChoices.COMANDADO)

	def test_transition_order_item_status_changes_when_allowed(self):
		_, item = self._create_order_with_item(item_status=ItemStatusChoices.COMANDADO)

		updated_item = transition_order_item_status(
			item.id,
			[ItemStatusChoices.COMANDADO],
			ItemStatusChoices.EN_PREPARACION,
		)

		self.assertEqual(updated_item.status, ItemStatusChoices.EN_PREPARACION)

	def test_transition_order_item_status_keeps_status_when_not_allowed(self):
		_, item = self._create_order_with_item(item_status=ItemStatusChoices.POR_ENTREGAR)

		updated_item = transition_order_item_status(
			item.id,
			[ItemStatusChoices.COMANDADO],
			ItemStatusChoices.EN_PREPARACION,
		)

		self.assertEqual(updated_item.status, ItemStatusChoices.POR_ENTREGAR)

	def test_cancel_order_item_rejects_delivered_items(self):
		_, item = self._create_order_with_item(item_status=ItemStatusChoices.ENTREGADO)

		updated_item, cancelled = cancel_order_item(item.id)

		self.assertFalse(cancelled)
		self.assertEqual(updated_item.status, ItemStatusChoices.ENTREGADO)

	def test_close_order_is_idempotent(self):
		order, _ = self._create_order_with_item()
		order.items.update(paid_status='PAGADO')

		first_order, first_closed = close_order(order.id)
		second_order, second_closed = close_order(order.id)

		self.assertTrue(first_closed)
		self.assertFalse(second_closed)
		self.assertEqual(first_order.status, OrderStatusChoices.PAGADA)
		self.assertEqual(second_order.status, OrderStatusChoices.PAGADA)
		self.assertIsNotNone(first_order.closed_at)

	def test_home_metrics_and_cash_queryset_reflect_statuses(self):
		order, item = self._create_order_with_item(item_status=ItemStatusChoices.POR_ENTREGAR)
		metrics = get_home_metrics()

		self.assertEqual(metrics['mesas abiertas'], 1)
		self.assertEqual(metrics['productos en proceso'], 1)
		self.assertEqual(metrics['productos con existencia'], 0)
		self.assertEqual(metrics['insumos con existencia'], 0)

		item.status = ItemStatusChoices.CANCELADO
		item.save(update_fields=['status'])
		row = get_cash_orders_queryset().get(id=order.id)
		self.assertEqual(row.total_amount_value, None)

	def test_draft_reservation_reserves_and_releases_stock(self):
		self.product_drink.stock = 1
		self.product_drink.save(update_fields=['stock'])

		reservation = reserve_draft_item('draft-session', self.product_drink.id, None, 1)
		self.product_drink.refresh_from_db()
		self.assertEqual(self.product_drink.stock, 0)
		self.assertTrue(DraftOrderReservation.objects.filter(pk=reservation.pk).exists())

		released = release_draft_item('draft-session', reservation.reservation_token)
		self.assertTrue(released)
		self.product_drink.refresh_from_db()
		self.assertEqual(self.product_drink.stock, 1)

	def test_create_order_from_payload_consumes_existing_draft_reservation(self):
		self.product_drink.stock = 1
		self.product_drink.save(update_fields=['stock'])
		reservation = reserve_draft_item('draft-session', self.product_drink.id, None, 1)

		form = OrderForm(data={'table_number': 9, 'notes': 'Mesa apartada'})
		self.assertTrue(form.is_valid())

		order = create_order_from_payload(
			form,
			[
				{
					'product_id': self.product_drink.id,
					'variant_id': None,
					'reservation_token': reservation.reservation_token,
					'quantity': 1,
					'notes': '',
					'diner_name': 'Pedro',
				}
			],
			self.user,
			session_key='draft-session',
		)

		self.assertEqual(order.items.count(), 1)
		self.assertFalse(DraftOrderReservation.objects.filter(reservation_token=reservation.reservation_token).exists())
		self.product_drink.refresh_from_db()
		self.assertEqual(self.product_drink.stock, 0)

	def test_release_all_draft_items_restores_all_reserved_stock(self):
		self.product_food.stock = 2
		self.product_drink.stock = 3
		self.product_food.save(update_fields=['stock'])
		self.product_drink.save(update_fields=['stock'])

		reserve_draft_item('draft-session', self.product_food.id, None, 1)
		reserve_draft_item('draft-session', self.product_drink.id, None, 2)

		released_count = release_all_draft_items('draft-session')

		self.assertEqual(released_count, 2)
		self.product_food.refresh_from_db()
		self.product_drink.refresh_from_db()
		self.assertEqual(self.product_food.stock, 2)
		self.assertEqual(self.product_drink.stock, 3)


class ViewFlowTests(TestCase):
	def setUp(self):
		user_model = get_user_model()
		self.employee = user_model.objects.create_user(username='mesero', password='Test12345!')
		self.admin_user = user_model.objects.create_superuser(username='admin_test', password='Admin12345!', email='admin@test.local')
		self.workday = WorkDay.objects.create(opened_by=self.admin_user)
		profile = self.employee.access_profile
		profile.can_menu = True
		profile.can_comanda = True
		profile.can_cocina = True
		profile.can_bar = True
		profile.can_entregas = True
		profile.can_caja = True
		profile.save(update_fields=['can_menu', 'can_comanda', 'can_cocina', 'can_bar', 'can_entregas', 'can_caja'])

		self.product_food = Product.objects.create(
			name='Taco',
			category=ProductCategoryChoices.COMIDA,
			price='80.00',
		)
		self.product_drink = Product.objects.create(
			name='Cerveza',
			category=ProductCategoryChoices.BEBIDA,
			price='55.00',
		)

	def _create_order_with_items(self):
		order = Order.objects.create(
			table_number=12,
			workday=self.workday,
			created_by=self.employee,
		)
		food_item = OrderItem.objects.create(
			order=order,
			product=self.product_food,
			commanded_by=self.employee,
			waiter_name='Mario',
			quantity=1,
			unit_price=self.product_food.price,
			status=ItemStatusChoices.COMANDADO,
		)
		drink_item = OrderItem.objects.create(
			order=order,
			product=self.product_drink,
			commanded_by=self.employee,
			waiter_name='Mario',
			quantity=2,
			unit_price=self.product_drink.price,
			status=ItemStatusChoices.COMANDADO,
		)
		return order, food_item, drink_item

	def test_admin_panel_requires_proper_role(self):
		response = self.client.get(reverse('admin-panel'))
		self.assertEqual(response.status_code, 302)
		self.assertIn(reverse('login'), response.url)

		self.client.login(username='mesero', password='Test12345!')
		response = self.client.get(reverse('admin-panel'))
		self.assertEqual(response.status_code, 403)

		self.client.logout()
		self.client.login(username='admin_test', password='Admin12345!')
		response = self.client.get(reverse('admin-panel'))
		self.assertEqual(response.status_code, 200)

	def test_admin_can_browse_workdays_and_order_details(self):
		order, _, _ = self._create_order_with_items()
		closed_workday = WorkDay.objects.create(
			opened_by=self.admin_user,
			closed_by=self.admin_user,
			status='CERRADO',
			closed_at=timezone.now(),
		)
		closed_order = Order.objects.create(
			table_number=7,
			workday=closed_workday,
			created_by=self.employee,
			status=OrderStatusChoices.PAGADA,
		)
		OrderItem.objects.create(
			order=closed_order,
			product=self.product_food,
			waiter_name='Mario',
			quantity=1,
			unit_price=self.product_food.price,
			status=ItemStatusChoices.ENTREGADO,
			paid_status='PAGADO',
		)

		self.client.login(username='admin_test', password='Admin12345!')

		response = self.client.get(reverse('admin-workday-list'))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Días laborales')
		self.assertContains(response, f'#{self.workday.id}')
		self.assertContains(response, f'#{closed_workday.id}')

		response = self.client.get(reverse('admin-workday-detail', args=[closed_workday.id]))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Ver detalle')
		self.assertContains(response, '7')

		response = self.client.get(reverse('admin-workday-order-detail', args=[closed_order.id]))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Consulta de mesa 7')
		self.assertContains(response, 'Taco')
		self.assertContains(response, 'Ver usuarios')
		self.assertNotContains(response, 'Agregar producto')
		self.assertNotContains(response, 'Cancelar')

		response = self.client.get(reverse('admin-workday-order-detail', args=[order.id]))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Consulta de mesa 12')
		self.assertContains(response, 'Ver usuarios')
		self.assertNotContains(response, 'Agregar producto')
		self.assertNotContains(response, 'modalAddOrderItem')

	def test_kitchen_delivery_and_cash_flow(self):
		order, food_item, drink_item = self._create_order_with_items()
		self.client.login(username='mesero', password='Test12345!')

		response = self.client.post(reverse('item-start', args=[food_item.id]))
		self.assertEqual(response.status_code, 302)
		food_item.refresh_from_db()
		self.assertEqual(food_item.status, ItemStatusChoices.EN_PREPARACION)
		self.assertEqual(food_item.prepared_by, self.employee)

		response = self.client.post(reverse('item-ready', args=[food_item.id]))
		self.assertEqual(response.status_code, 302)
		food_item.refresh_from_db()
		self.assertEqual(food_item.status, ItemStatusChoices.POR_ENTREGAR)

		response = self.client.get(reverse('deliveries-board'))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Taco')

		response = self.client.post(reverse('item-deliver', args=[food_item.id]))
		self.assertEqual(response.status_code, 302)
		food_item.refresh_from_db()
		self.assertEqual(food_item.status, ItemStatusChoices.ENTREGADO)
		self.assertEqual(food_item.delivered_by, self.employee)

		response = self.client.post(
			reverse('order-pay-items', args=[order.id]),
			data={
				'item_ids': [str(food_item.id), str(drink_item.id)],
				'cash_amount': '190.00',
				'card_amount': '0',
				'transfer_amount': '0',
			},
		)
		self.assertEqual(response.status_code, 302)
		food_item.refresh_from_db()
		drink_item.refresh_from_db()
		self.assertEqual(food_item.paid_status, 'PAGADO')
		self.assertEqual(drink_item.paid_status, 'PAGADO')
		self.assertEqual(food_item.paid_by, self.employee)
		self.assertEqual(drink_item.paid_by, self.employee)

		response = self.client.post(reverse('close-order', args=[order.id]))
		self.assertEqual(response.status_code, 302)
		order.refresh_from_db()
		self.assertEqual(order.status, OrderStatusChoices.PAGADA)

	def test_create_order_records_who_commanded_each_item(self):
		self.client.login(username='mesero', password='Test12345!')
		self.product_food.stock = 3
		self.product_food.save(update_fields=['stock'])

		response = self.client.post(
			reverse('comanda-create'),
			data={
				'table_number': '4',
				'notes': '',
				'items_json': '[{"product_id": %d, "variant_id": null, "quantity": 1, "notes": "", "diner_name": "Ana"}]' % self.product_food.id,
			},
			HTTP_X_REQUESTED_WITH='XMLHttpRequest',
		)

		self.assertEqual(response.status_code, 200)
		order_id = response.json()['order_id']
		item = OrderItem.objects.get(order_id=order_id)
		self.assertEqual(item.commanded_by, self.employee)

	def test_cancel_item_requires_admin(self):
		_, _, drink_item = self._create_order_with_items()

		self.client.login(username='mesero', password='Test12345!')
		response = self.client.post(reverse('item-cancel', args=[drink_item.id]))
		self.assertEqual(response.status_code, 403)

		self.client.logout()
		self.client.login(username='admin_test', password='Admin12345!')
		response = self.client.post(reverse('item-cancel', args=[drink_item.id]))
		self.assertEqual(response.status_code, 302)
		drink_item.refresh_from_db()
		self.assertEqual(drink_item.status, ItemStatusChoices.CANCELADO)

	def test_cash_can_update_unpaid_item_price(self):
		order, food_item, _ = self._create_order_with_items()
		self.client.login(username='mesero', password='Test12345!')
		profile = self.employee.access_profile
		profile.can_edit_caja_prices = True
		profile.save(update_fields=['can_edit_caja_prices'])

		response = self.client.post(
			reverse('order-item-price-update', args=[food_item.id]),
			data={'unit_price': '95.50'},
			HTTP_X_REQUESTED_WITH='XMLHttpRequest',
		)

		self.assertEqual(response.status_code, 200)
		payload = response.json()
		self.assertTrue(payload['ok'])
		self.assertEqual(payload['unit_price'], '95.50')
		self.assertEqual(payload['item_total'], '95.50')
		food_item.refresh_from_db()
		self.assertEqual(food_item.unit_price, Decimal('95.50'))
		self.assertEqual(payload['pending_amount'], '205.50')
		self.assertEqual(payload['total_amount'], '205.50')
		price_change = OrderItemPriceChange.objects.get(order_item=food_item)
		self.assertEqual(price_change.previous_unit_price, Decimal('80.00'))
		self.assertEqual(price_change.new_unit_price, Decimal('95.50'))
		self.assertEqual(price_change.note, '')
		self.assertEqual(price_change.changed_by, self.employee)

	def test_cash_price_history_endpoint_returns_recorded_changes(self):
		order, food_item, _ = self._create_order_with_items()
		self.client.login(username='mesero', password='Test12345!')
		profile = self.employee.access_profile
		profile.can_edit_caja_prices = True
		profile.save(update_fields=['can_edit_caja_prices'])

		response = self.client.post(
			reverse('order-item-price-update', args=[food_item.id]),
			data={'unit_price': '95.50'},
			HTTP_X_REQUESTED_WITH='XMLHttpRequest',
		)
		self.assertEqual(response.status_code, 200)

		response = self.client.get(
			reverse('order-item-price-history', args=[food_item.id]),
			HTTP_X_REQUESTED_WITH='XMLHttpRequest',
		)
		self.assertEqual(response.status_code, 200)
		payload = response.json()
		self.assertTrue(payload['ok'])
		self.assertEqual(payload['product_name'], 'Taco')
		self.assertEqual(len(payload['changes']), 1)
		self.assertEqual(payload['changes'][0]['previous_unit_price'], '80.00')
		self.assertEqual(payload['changes'][0]['new_unit_price'], '95.50')
		self.assertEqual(payload['changes'][0]['changed_by'], 'mesero')

	def test_cash_cannot_update_price_without_specific_access(self):
		order, food_item, _ = self._create_order_with_items()
		self.client.login(username='mesero', password='Test12345!')

		response = self.client.post(
			reverse('order-item-price-update', args=[food_item.id]),
			data={'unit_price': '95.50'},
		)

		self.assertEqual(response.status_code, 403)
		food_item.refresh_from_db()
		self.assertEqual(food_item.unit_price, Decimal('80.00'))

	def test_closing_workday_logs_out_all_active_sessions(self):
		admin_client = Client()
		employee_client = Client()

		self.assertTrue(admin_client.login(username='admin_test', password='Admin12345!'))
		self.assertTrue(employee_client.login(username='mesero', password='Test12345!'))
		self.assertEqual(Session.objects.count(), 2)

		response = admin_client.post(reverse('admin-panel'), data={'form_kind': 'workday_close'})
		self.assertRedirects(response, f"{reverse('login')}?reason=workday_closed")

		self.workday.refresh_from_db()
		self.assertIsNotNone(self.workday.closed_at)
		self.assertEqual(self.workday.status, 'CERRADO')
		self.assertEqual(Session.objects.count(), 0)

		response = admin_client.get(f"{reverse('login')}?reason=workday_closed")
		self.assertContains(response, 'El día laboral fue cerrado.')

		response = employee_client.get(reverse('home'))
		self.assertEqual(response.status_code, 302)
		self.assertIn(reverse('login'), response.url)

	def test_product_update_keeps_stock_when_variants_exist_and_stock_is_omitted(self):
		self.client.login(username='admin_test', password='Admin12345!')
		product = Product.objects.create(
			name='Michelada',
			category=ProductCategoryChoices.BEBIDA,
			price='95.00',
			stock=0,
		)
		ProductVariant.objects.create(
			product=product,
			name='Grande',
			price_delta='10.00',
			stock=6,
		)

		response = self.client.post(
			reverse('product-update', args=[product.id]),
			data={
				'name': 'Michelada especial',
				'category': ProductCategoryChoices.BEBIDA,
				'price': '105.00',
				'description': 'Con clamato',
				'is_active': 'true',
			},
			HTTP_X_REQUESTED_WITH='XMLHttpRequest',
		)

		self.assertEqual(response.status_code, 200)
		payload = response.json()
		self.assertTrue(payload['ok'])
		self.assertEqual(payload['product']['name'], 'Michelada especial')
		self.assertEqual(payload['product']['stock'], 6)
		self.assertEqual(payload['product']['category_value'], ProductCategoryChoices.BEBIDA)

		product.refresh_from_db()
		self.assertEqual(product.name, 'Michelada especial')
		self.assertEqual(product.stock, 6)

	def test_draft_reserve_endpoint_validates_stock_before_adding_to_borrador(self):
		self.client.login(username='mesero', password='Test12345!')
		self.product_drink.stock = 1
		self.product_drink.save(update_fields=['stock'])

		response = self.client.post(
			reverse('draft-order-reserve'),
			data='{"product_id": %d, "quantity": 1}' % self.product_drink.id,
			content_type='application/json',
			HTTP_X_REQUESTED_WITH='XMLHttpRequest',
		)
		self.assertEqual(response.status_code, 200)
		payload = response.json()
		self.assertTrue(payload['ok'])

		response = self.client.post(
			reverse('draft-order-reserve'),
			data='{"product_id": %d, "quantity": 1}' % self.product_drink.id,
			content_type='application/json',
			HTTP_X_REQUESTED_WITH='XMLHttpRequest',
		)
		self.assertEqual(response.status_code, 400)
		self.assertIn('No hay inventario suficiente', response.json()['message'])

	def test_draft_catalog_endpoint_returns_current_available_catalog(self):
		self.client.login(username='mesero', password='Test12345!')
		self.product_food.stock = 2
		self.product_drink.stock = 0
		self.product_food.save(update_fields=['stock'])
		self.product_drink.save(update_fields=['stock'])

		response = self.client.get(reverse('draft-order-catalog'), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
		self.assertEqual(response.status_code, 200)
		payload = response.json()
		self.assertTrue(payload['ok'])
		product_names = [entry['name'] for entry in payload['catalog']]
		self.assertIn('Taco', product_names)
		self.assertNotIn('Cerveza', product_names)
