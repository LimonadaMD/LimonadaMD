# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2018-11-05 15:51
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forcefields', '0011_auto_20181030_1333'),
    ]

    operations = [
        migrations.AlterField(
            model_name='forcefield',
            name='name',
            field=models.CharField(max_length=50),
        ),
    ]