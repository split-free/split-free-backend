# Generated by Django 4.2 on 2024-01-23 12:17

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0008_member_group_alter_group_members"),
    ]

    operations = [
        migrations.AlterField(
            model_name="member",
            name="group",
            field=models.ForeignKey(
                blank=True,
                default=None,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="core.group",
            ),
        ),
    ]
