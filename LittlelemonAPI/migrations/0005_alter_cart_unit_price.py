# Generated by Django 4.2.4 on 2023-08-15 03:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('LittlelemonAPI', '0004_alter_category_slug'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cart',
            name='unit_price',
            field=models.DecimalField(decimal_places=2, editable=False, max_digits=6),
        ),
    ]
