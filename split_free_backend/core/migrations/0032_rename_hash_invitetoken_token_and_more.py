# Generated by Django 5.0.3 on 2024-03-23 21:35

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0031_alter_user_activation_token_alter_user_name_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="invitetoken",
            old_name="hash",
            new_name="token",
        ),
        migrations.AlterUniqueTogether(
            name="invitetoken",
            unique_together={("token", "group")},
        ),
    ]
