# Generated by Django 4.2 on 2024-01-23 12:10

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "split_free_all",
            "0007_remove_balance_user_expense_currency_expense_date_and_more",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="member",
            name="group",
            field=models.ForeignKey(
                default=None,
                on_delete=django.db.models.deletion.CASCADE,
                to="split_free_all.group",
            ),
        ),
        migrations.AlterField(
            model_name="group",
            name="members",
            field=models.ManyToManyField(
                blank=True,
                null=True,
                related_name="group_members",
                to="split_free_all.member",
            ),
        ),
    ]
