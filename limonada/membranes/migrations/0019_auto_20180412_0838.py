# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2018-04-12 08:38
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('membranes', '0018_auto_20180412_0834'),
    ]

    operations = [
        migrations.AlterField(
            model_name='membranetopol',
            name='nb_lipids',
            field=models.PositiveIntegerField(null=True),
        ),
    ]
