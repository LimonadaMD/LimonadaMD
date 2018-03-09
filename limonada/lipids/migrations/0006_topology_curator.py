# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-11-22 12:31
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('lipids', '0005_auto_20171024_1415'),
    ]

    operations = [
        migrations.AddField(
            model_name='topology',
            name='curator',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL),
        ),
    ]