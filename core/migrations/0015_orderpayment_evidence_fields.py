from django.db import migrations, models


class Migration(migrations.Migration):

	dependencies = [
		('core', '0014_orderpayment_orderitempayment_and_item_paid_status'),
	]

	operations = [
		migrations.AddField(
			model_name='orderpayment',
			name='card_evidence',
			field=models.FileField(blank=True, upload_to='pago-tarjeta/'),
		),
		migrations.AddField(
			model_name='orderpayment',
			name='transfer_evidence',
			field=models.FileField(blank=True, upload_to='pago-tranferencia/'),
		),
	]