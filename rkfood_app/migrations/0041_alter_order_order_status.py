# Generated by Django 4.2 on 2024-10-27 11:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rkfood_app', '0040_alter_order_order_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='order_status',
            field=models.CharField(choices=[('Recent', 'Recent'), ('Past Orders', 'Past Orders'), ('Failed', 'failed')], max_length=20),
        ),
    ]