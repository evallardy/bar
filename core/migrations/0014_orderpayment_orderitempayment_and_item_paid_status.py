from decimal import Decimal

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_remove_order_waiter_request_scope'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='orderitem',
            name='status',
            field=models.CharField(
                choices=[
                    ('COMANDADO', 'Comandado'),
                    ('EN_PREPARACION', 'En preparación'),
                    ('POR_ENTREGAR', 'Por entregar'),
                    ('ENTREGADO', 'Entregado'),
                    ('PAGADO', 'Pagado'),
                    ('CANCELADO', 'Cancelado'),
                ],
                default='COMANDADO',
                max_length=20,
            ),
        ),
        migrations.CreateModel(
            name='OrderPayment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('cash_amount', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10)),
                ('card_amount', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10)),
                ('transfer_amount', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10)),
                ('total_amount', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='payments', to='core.order')),
                ('workday', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='payments', to='core.workday')),
            ],
            options={
                'ordering': ['-created_at', '-id'],
            },
        ),
        migrations.CreateModel(
            name='OrderItemPayment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('order_item', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='item_payments', to='core.orderitem')),
                ('payment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payment_items', to='core.orderpayment')),
            ],
            options={
                'ordering': ['id'],
            },
        ),
        migrations.AddConstraint(
            model_name='orderitempayment',
            constraint=models.UniqueConstraint(fields=('payment', 'order_item'), name='unique_payment_order_item'),
        ),
        migrations.AddConstraint(
            model_name='orderitempayment',
            constraint=models.UniqueConstraint(fields=('order_item',), name='unique_paid_order_item'),
        ),
    ]
