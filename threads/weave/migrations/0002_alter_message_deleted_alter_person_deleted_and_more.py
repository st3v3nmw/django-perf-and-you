# Generated by Django 4.2.3 on 2023-08-01 02:45

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("weave", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="message",
            name="deleted",
            field=models.BooleanField(db_index=True),
        ),
        migrations.AlterField(
            model_name="person",
            name="deleted",
            field=models.BooleanField(db_index=True),
        ),
        migrations.AlterField(
            model_name="thread",
            name="deleted",
            field=models.BooleanField(db_index=True),
        ),
    ]
