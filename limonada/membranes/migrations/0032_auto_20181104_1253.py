# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2018-11-04 12:53
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forcefields', '0011_auto_20181030_1333'),
        ('membranes', '0031_auto_20181030_1454'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='membranetopol',
            name='software',
        ),
        migrations.AddField(
            model_name='membranetopol',
            name='software',
            field=models.ManyToManyField(to='forcefields.Software'),
        ),
    ]
