# Generated by Django 3.1.7 on 2021-04-30 07:05

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('home', '0009_auto_20210430_0005'),
    ]

    operations = [
        migrations.AlterField(
            model_name='answer',
            name='upVotes',
            field=models.ManyToManyField(blank=True, related_name='upVotes', to=settings.AUTH_USER_MODEL),
        ),
    ]
