# -*- coding: utf-8 -*-
# Generated by Django 1.11.26 on 2020-04-08 08:44
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('homepage', '0011_auto_20200402_1637'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reference',
            name='refid',
            field=models.CharField(help_text='Format: AuthorYear[Index]', max_length=200, unique=True),
        ),
    ]
