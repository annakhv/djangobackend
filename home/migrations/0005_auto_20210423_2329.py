# Generated by Django 3.1.7 on 2021-04-24 06:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0004_auto_20210423_0144'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='whichAnswer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='home.answer'),
        ),
    ]
