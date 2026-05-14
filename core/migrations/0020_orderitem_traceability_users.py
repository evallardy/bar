from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

	dependencies = [
		('core', '0019_orderitempricechange'),
		migrations.swappable_dependency(settings.AUTH_USER_MODEL),
	]

	operations = [
		migrations.AddField(
			model_name='orderitem',
			name='commanded_by',
			field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='commanded_order_items', to=settings.AUTH_USER_MODEL),
		),
		migrations.AddField(
			model_name='orderitem',
			name='delivered_by',
			field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='delivered_order_items', to=settings.AUTH_USER_MODEL),
		),
		migrations.AddField(
			model_name='orderitem',
			name='paid_by',
			field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='paid_order_items', to=settings.AUTH_USER_MODEL),
		),
		migrations.AddField(
			model_name='orderitem',
			name='prepared_by',
			field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='prepared_order_items', to=settings.AUTH_USER_MODEL),
		),
	]