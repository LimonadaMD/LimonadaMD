# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2018-11-09 13:23
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forcefields', '0012_auto_20181105_1551'),
    ]

    operations = [
        migrations.AddField(
            model_name='software',
            name='version',
            field=models.CharField(default=1, max_length=50),
            preserve_default=False,
        ),
    ]
