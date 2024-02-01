# Generated by Django 4.2 on 2024-01-30 20:12

import django.contrib.auth.models
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("split_free_all", "0015_alter_balance_owner"),
    ]

    operations = [
        migrations.AlterModelManagers(
            name="user",
            managers=[
                ("objects", django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.RemoveField(
            model_name="user",
            name="name",
        ),
        migrations.AddField(
            model_name="user",
            name="email",
            field=models.CharField(
                default="example@hotmail.com", max_length=128, unique=True
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="is_active",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="user",
            name="last_login",
            field=models.DateTimeField(
                blank=True, null=True, verbose_name="last login"
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="password",
            field=models.CharField(max_length=32, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="username",
            field=models.CharField(max_length=32, null=True),
        ),
    ]