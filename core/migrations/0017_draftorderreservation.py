from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone

import core.models


class Migration(migrations.Migration):

	dependencies = [
		('core', '0016_orderitem_paid_status_split'),
	]

	operations = [
		migrations.CreateModel(
			name='DraftOrderReservation',
			fields=[
				('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
				('session_key', models.CharField(db_index=True, max_length=40)),
				('reservation_token', models.CharField(default=core.models.generate_draft_reservation_token, editable=False, max_length=32, unique=True)),
				('quantity', models.PositiveIntegerField(default=1)),
				('unit_price', models.DecimalField(decimal_places=2, max_digits=10)),
				('created_at', models.DateTimeField(default=django.utils.timezone.now)),
				('expires_at', models.DateTimeField(db_index=True)),
				('product', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='draft_reservations', to='core.product')),
				('variant', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='draft_reservations', to='core.productvariant')),
			],
			options={
				'ordering': ['created_at', 'id'],
			},
		),
	]