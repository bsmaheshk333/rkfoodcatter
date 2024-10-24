# Generated by Django 4.2 on 2024-10-24 06:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('rkfood_app', '0033_restaurant_set_default'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='restaurant',
            name='set_default',
        ),
        migrations.AddField(
            model_name='customer',
            name='default_restaurant',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='rkfood_app.restaurant'),
        ),
    ]
