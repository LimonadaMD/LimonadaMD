# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2018-09-19 07:48
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_auto_20180309_1025'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='miscellaneous',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='address',
            field=models.TextField(blank=True, default=datetime.datetime(2018, 9, 19, 7, 48, 36, 536810, tzinfo=utc)),
            preserve_default=False,
        ),
    ]
