# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2018-04-12 08:41
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('membranes', '0019_auto_20180412_0838'),
    ]

    operations = [
        migrations.AlterField(
            model_name='membrane',
            name='nb_liptypes',
            field=models.PositiveIntegerField(null=True),
        ),
    ]