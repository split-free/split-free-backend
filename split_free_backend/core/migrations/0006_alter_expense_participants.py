# Generated by Django 5.0 on 2023-12-29 21:45

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "core",
            "0005_balance_debt_group_remove_idealtransfer_event_and_more",
        ),
    ]

    operations = [
        migrations.AlterField(
            model_name="expense",
            name="participants",
            field=models.ManyToManyField(related_name="participants", to="core.user"),
        ),
    ]
