from django.db import migrations, models


class Migration(migrations.Migration):

	dependencies = [
		('core', '0017_draftorderreservation'),
	]

	operations = [
		migrations.AddField(
			model_name='useraccess',
			name='can_edit_caja_prices',
			field=models.BooleanField(default=False),
		),
	]