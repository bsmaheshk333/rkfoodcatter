# Generated by Django 4.2 on 2024-10-19 07:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rkfood_app', '0028_alter_menu_restaurant'),
    ]

    operations = [
        migrations.AlterField(
            model_name='menu',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
    ]
