# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-12-19 22:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('homepage', '0003_auto_20171219_2009'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reference',
            name='doi',
            field=models.CharField(max_length=30, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='reference',
            name='refid',
            field=models.CharField(max_length=200, unique=True),
        ),
        migrations.AlterField(
            model_name='reference',
            name='title',
            field=models.CharField(max_length=200),
        ),
    ]
