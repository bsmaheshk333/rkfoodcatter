# Generated by Django 4.2 on 2024-10-18 14:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rkfood_app', '0025_alter_feedback_email'),
    ]

    operations = [
        migrations.AddField(
            model_name='feedback',
            name='posted_on',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
