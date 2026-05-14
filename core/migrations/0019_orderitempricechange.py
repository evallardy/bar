from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

	dependencies = [
		('core', '0018_useraccess_can_edit_caja_prices'),
		migrations.swappable_dependency(settings.AUTH_USER_MODEL),
	]

	operations = [
		migrations.CreateModel(
			name='OrderItemPriceChange',
			fields=[
				('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
				('previous_unit_price', models.DecimalField(decimal_places=2, max_digits=10)),
				('new_unit_price', models.DecimalField(decimal_places=2, max_digits=10)),
				('note', models.CharField(blank=True, max_length=255)),
				('changed_at', models.DateTimeField(default=django.utils.timezone.now)),
				('changed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
				('order_item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='price_changes', to='core.orderitem')),
			],
			options={
				'ordering': ['-changed_at', '-id'],
			},
		),
	]