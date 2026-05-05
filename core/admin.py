from django.contrib import admin

from .models import Order, OrderItem, Product, ProductSupply, ProductVariant, Supply, UserAccess, WorkDay


class OrderItemInline(admin.TabularInline):
	model = OrderItem
	extra = 0


class ProductSupplyInline(admin.TabularInline):
	model = ProductSupply
	extra = 1


class ProductVariantInline(admin.TabularInline):
	model = ProductVariant
	extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
	list_display = ('name', 'category', 'preparation_area_display', 'price', 'stock', 'is_active')
	list_filter = ('category', 'is_active')
	search_fields = ('name',)
	inlines = [ProductSupplyInline, ProductVariantInline]

	@admin.display(description='Área')
	def preparation_area_display(self, obj):
		return obj.preparation_area_display


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
	list_display = ('product', 'name', 'price_delta', 'stock', 'is_active')
	list_filter = ('is_active', 'product')
	search_fields = ('name', 'product__name')



@admin.register(Supply)
class SupplyAdmin(admin.ModelAdmin):
	list_display = ('name', 'is_available')
	list_filter = ('is_available',)
	search_fields = ('name',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
	list_display = ('id', 'table_number', 'status', 'created_at')
	list_filter = ('status', 'created_at')
	search_fields = ('table_number',)
	inlines = [OrderItemInline]


@admin.register(UserAccess)
class UserAccessAdmin(admin.ModelAdmin):
	list_display = (
		'user',
		'role',
		'can_menu',
		'can_administrador',
		'can_comanda',
		'can_cocina',
		'can_bar',
		'can_entregas',
		'can_caja',
	)
	list_filter = ('role', 'can_administrador', 'can_comanda', 'can_cocina', 'can_bar', 'can_entregas', 'can_caja')
	search_fields = ('user__username', 'user__first_name', 'user__last_name')


@admin.register(WorkDay)
class WorkDayAdmin(admin.ModelAdmin):
	list_display = ('id', 'status', 'opened_at', 'opened_by', 'closed_at', 'closed_by', 'pending_orders_on_close')
	list_filter = ('status', 'opened_at')
	search_fields = ('opened_by__username', 'closed_by__username')
