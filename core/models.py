from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


class AreaChoices(models.TextChoices):
	COCINA = 'COCINA', 'Cocina'
	BAR = 'BAR', 'Bar'
	CAJA = 'CAJA', 'Caja'
	ALMACEN = 'ALMACEN', 'Almacen'


class ProductCategoryChoices(models.TextChoices):
	COMIDA = 'COMIDA', 'Comida'
	BEBIDA = 'BEBIDA', 'Bebida'


class RequestScopeChoices(models.TextChoices):
	MESA = 'MESA', 'Mesa completa'
	COMENSAL = 'COMENSAL', 'Por comensal'


class OrderStatusChoices(models.TextChoices):
	ABIERTA = 'ABIERTA', 'Abierta'
	PAGADA = 'PAGADA', 'Pagada'
	CANCELADA = 'CANCELADA', 'Cancelada'


class ItemStatusChoices(models.TextChoices):
	COMANDADO = 'COMANDADO', 'Comandado'
	EN_PREPARACION = 'EN_PREPARACION', 'En preparación'
	POR_ENTREGAR = 'POR_ENTREGAR', 'Por entregar'
	ENTREGADO = 'ENTREGADO', 'Entregado'
	CANCELADO = 'CANCELADO', 'Cancelado'


class ItemPaidStatusChoices(models.TextChoices):
	NO_PAGADO = 'NO_PAGADO', 'Pendiente'
	PAGADO = 'PAGADO', 'Pagado'


class WorkDayStatusChoices(models.TextChoices):
	ABIERTO = 'ABIERTO', 'Abierto'
	CERRADO = 'CERRADO', 'Cerrado'


class Product(models.Model):
	name = models.CharField(max_length=120, unique=True)
	category = models.CharField(max_length=20, choices=ProductCategoryChoices.choices)
	price = models.DecimalField(max_digits=10, decimal_places=2)
	description = models.CharField(max_length=255, blank=True)
	is_active = models.BooleanField(default=True)
	stock = models.PositiveIntegerField(default=0)
	supplies = models.ManyToManyField('Supply', through='ProductSupply', related_name='products', blank=True)

	class Meta:
		ordering = ['name']

	def __str__(self):
		return self.name

	@property
	def preparation_area(self):
		if self.category == ProductCategoryChoices.COMIDA:
			return AreaChoices.COCINA
		return AreaChoices.BAR

	@property
	def preparation_area_display(self):
		return AreaChoices(self.preparation_area).label

	def recalculate_stock_from_variants(self):
		from django.db.models import Sum
		total = self.variants.filter(is_active=True).aggregate(total=Sum('stock'))['total'] or 0
		Product.objects.filter(pk=self.pk).update(stock=total)


class Supply(models.Model):
	name = models.CharField(max_length=120, unique=True)
	is_available = models.BooleanField(default=True)

	class Meta:
		ordering = ['name']

	def __str__(self):
		return self.name


class ProductSupply(models.Model):
	product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_supplies')
	supply = models.ForeignKey(Supply, on_delete=models.PROTECT, related_name='supply_products')
	quantity_required = models.DecimalField(max_digits=10, decimal_places=2, default=1)

	class Meta:
		ordering = ['product__name', 'supply__name']
		constraints = [
			models.UniqueConstraint(fields=['product', 'supply'], name='unique_product_supply'),
		]

	def __str__(self):
		return f'{self.product.name} -> {self.supply.name} ({self.quantity_required})'


class ProductVariant(models.Model):
	product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
	name = models.CharField(max_length=120)
	price_delta = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
	stock = models.PositiveIntegerField(default=0)
	is_active = models.BooleanField(default=True)

	class Meta:
		ordering = ['product__name', 'name']
		constraints = [
			models.UniqueConstraint(fields=['product', 'name'], name='unique_product_variant'),
		]

	def __str__(self):
		return f'{self.product.name} - {self.name}'

	@property
	def final_price(self):
		return self.product.price + self.price_delta

	def save(self, *args, **kwargs):
		super().save(*args, **kwargs)
		self.product.recalculate_stock_from_variants()

	def delete(self, *args, **kwargs):
		product = self.product
		super().delete(*args, **kwargs)
		product.recalculate_stock_from_variants()


class WorkDay(models.Model):
	opened_at = models.DateTimeField(default=timezone.now)
	closed_at = models.DateTimeField(null=True, blank=True)
	status = models.CharField(max_length=20, choices=WorkDayStatusChoices.choices, default=WorkDayStatusChoices.ABIERTO)
	opened_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='opened_workdays')
	closed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name='closed_workdays')
	pending_orders_on_close = models.PositiveIntegerField(default=0)

	class Meta:
		ordering = ['-opened_at']

	def __str__(self):
		return f'Dia {self.pk} ({self.get_status_display()})'


class Order(models.Model):
	table_number = models.PositiveIntegerField()
	workday = models.ForeignKey('WorkDay', null=True, blank=True, on_delete=models.PROTECT, related_name='orders')
	status = models.CharField(max_length=20, choices=OrderStatusChoices.choices, default=OrderStatusChoices.ABIERTA)
	notes = models.TextField(blank=True)
	created_at = models.DateTimeField(default=timezone.now)
	closed_at = models.DateTimeField(null=True, blank=True)
	created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return f'Mesa {self.table_number}'

	@property
	def total_amount(self):
		total = self.items.exclude(status=ItemStatusChoices.CANCELADO).aggregate(
			total=models.Sum(models.F('quantity') * models.F('unit_price'), output_field=models.DecimalField(max_digits=10, decimal_places=2))
		)['total']
		return total or Decimal('0.00')

	@property
	def active_items(self):
		return self.items.exclude(status=ItemStatusChoices.CANCELADO)


class OrderItem(models.Model):
	order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
	product = models.ForeignKey(Product, on_delete=models.PROTECT)
	variant = models.ForeignKey(ProductVariant, null=True, blank=True, on_delete=models.SET_NULL)
	diner_name = models.CharField(max_length=120, blank=True)
	waiter_name = models.CharField(max_length=120, blank=True)
	quantity = models.PositiveIntegerField(default=1)
	unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
	notes = models.CharField(max_length=255, blank=True)
	status = models.CharField(max_length=20, choices=ItemStatusChoices.choices, default=ItemStatusChoices.COMANDADO)
	paid_status = models.CharField(max_length=20, choices=ItemPaidStatusChoices.choices, default=ItemPaidStatusChoices.NO_PAGADO)
	paid_at = models.DateTimeField(null=True, blank=True)
	created_at = models.DateTimeField(default=timezone.now)

	class Meta:
		ordering = ['created_at', 'id']

	def __str__(self):
		return f'{self.product.name} x{self.quantity}'

	def save(self, *args, **kwargs):
		if self.product_id and not self.unit_price:
			if self.variant_id and self.variant and self.variant.product_id == self.product_id:
				self.unit_price = self.product.price + self.variant.price_delta
			else:
				self.unit_price = self.product.price
		super().save(*args, **kwargs)

	@property
	def total(self):
		return self.quantity * self.unit_price

	@property
	def area(self):
		return self.product.preparation_area

	@property
	def is_paid(self):
		return self.paid_status == ItemPaidStatusChoices.PAGADO

	@property
	def payment_status_label(self):
		if self.status == ItemStatusChoices.CANCELADO and not self.is_paid:
			return 'No aplica'
		return self.get_paid_status_display()


class OrderPayment(models.Model):
	order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name='payments')
	workday = models.ForeignKey('WorkDay', null=True, blank=True, on_delete=models.PROTECT, related_name='payments')
	created_at = models.DateTimeField(default=timezone.now)
	created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
	cash_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
	card_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
	transfer_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
	total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
	card_evidence = models.FileField(upload_to='pago-tarjeta/', blank=True)
	transfer_evidence = models.FileField(upload_to='pago-tranferencia/', blank=True)

	class Meta:
		ordering = ['-created_at', '-id']

	def __str__(self):
		return f'Pago #{self.pk} comanda #{self.order_id}'


class OrderItemPayment(models.Model):
	payment = models.ForeignKey(OrderPayment, on_delete=models.CASCADE, related_name='payment_items')
	order_item = models.ForeignKey(OrderItem, on_delete=models.PROTECT, related_name='item_payments')
	amount = models.DecimalField(max_digits=10, decimal_places=2)

	class Meta:
		ordering = ['id']
		constraints = [
			models.UniqueConstraint(fields=['payment', 'order_item'], name='unique_payment_order_item'),
			models.UniqueConstraint(fields=['order_item'], name='unique_paid_order_item'),
		]

	def __str__(self):
		return f'Item {self.order_item_id} pagado en pago {self.payment_id}'


class UserAccess(models.Model):
	class RoleChoices(models.TextChoices):
		ADMINISTRADOR = 'ADMINISTRADOR', 'Administrador'
		EMPLEADO = 'EMPLEADO', 'Empleado'

	user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='access_profile')
	role = models.CharField(max_length=20, choices=RoleChoices.choices, default=RoleChoices.EMPLEADO)
	can_menu = models.BooleanField(default=True)
	can_administrador = models.BooleanField(default=False)
	can_comanda = models.BooleanField(default=False)
	can_cocina = models.BooleanField(default=False)
	can_bar = models.BooleanField(default=False)
	can_entregas = models.BooleanField(default=False)
	can_caja = models.BooleanField(default=False)

	class Meta:
		verbose_name = 'Acceso de usuario'
		verbose_name_plural = 'Accesos de usuarios'

	def __str__(self):
		return f'{self.user.username} ({self.get_role_display()})'

	@property
	def is_admin_role(self):
		return self.role == self.RoleChoices.ADMINISTRADOR


@receiver(post_save, sender=get_user_model())
def ensure_user_access_profile(sender, instance, created, **kwargs):
	if created:
		UserAccess.objects.get_or_create(user=instance)
