from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from decimal import Decimal

from .forms import OrderForm, OrderItemFormSet
from .models import ItemStatusChoices, Order, OrderItem, OrderStatusChoices, Product, ProductCategoryChoices, ProductVariant, Supply, UserAccess, WorkDay
from .services import cancel_order_item, close_order, create_order_from_forms, get_cash_orders_queryset, get_home_metrics, transition_order_item_status


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
			waiter_name='Mario',
			quantity=1,
			unit_price=self.product_food.price,
			status=ItemStatusChoices.COMANDADO,
		)
		drink_item = OrderItem.objects.create(
			order=order,
			product=self.product_drink,
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

	def test_kitchen_delivery_and_cash_flow(self):
		order, food_item, drink_item = self._create_order_with_items()
		self.client.login(username='mesero', password='Test12345!')

		response = self.client.post(reverse('item-start', args=[food_item.id]))
		self.assertEqual(response.status_code, 302)
		food_item.refresh_from_db()
		self.assertEqual(food_item.status, ItemStatusChoices.EN_PREPARACION)

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

		response = self.client.post(reverse('close-order', args=[order.id]))
		self.assertEqual(response.status_code, 302)
		order.refresh_from_db()
		self.assertEqual(order.status, OrderStatusChoices.PAGADA)

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
