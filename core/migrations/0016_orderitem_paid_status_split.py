from django.db import migrations, models


def migrate_paid_items(apps, schema_editor):
	OrderItem = apps.get_model('core', 'OrderItem')
	OrderItem.objects.filter(status='PAGADO').update(
		status='ENTREGADO',
		paid_status='PAGADO',
	)


def reverse_paid_items(apps, schema_editor):
	OrderItem = apps.get_model('core', 'OrderItem')
	OrderItem.objects.filter(paid_status='PAGADO', status='ENTREGADO').update(status='PAGADO')


class Migration(migrations.Migration):

	dependencies = [
		('core', '0015_orderpayment_evidence_fields'),
	]

	operations = [
		migrations.AddField(
			model_name='orderitem',
			name='paid_at',
			field=models.DateTimeField(blank=True, null=True),
		),
		migrations.AddField(
			model_name='orderitem',
			name='paid_status',
			field=models.CharField(choices=[('NO_PAGADO', 'Pendiente'), ('PAGADO', 'Pagado')], default='NO_PAGADO', max_length=20),
		),
		migrations.RunPython(migrate_paid_items, reverse_paid_items),
		migrations.AlterField(
			model_name='orderitem',
			name='status',
			field=models.CharField(choices=[('COMANDADO', 'Comandado'), ('EN_PREPARACION', 'En preparación'), ('POR_ENTREGAR', 'Por entregar'), ('ENTREGADO', 'Entregado'), ('CANCELADO', 'Cancelado')], default='COMANDADO', max_length=20),
		),
	]