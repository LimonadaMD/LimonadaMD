# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2018-10-12 10:51
from __future__ import unicode_literals

from django.db import migrations, models
import homepage.models


class Migration(migrations.Migration):

    dependencies = [
        ('homepage', '0009_auto_20181010_1957'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reference',
            name='doi',
            field=models.CharField(max_length=100, null=True, unique=True, validators=[homepage.models.validate_doi]),
        ),
    ]