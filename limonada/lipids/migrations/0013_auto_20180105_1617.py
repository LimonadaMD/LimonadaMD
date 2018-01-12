# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2018-01-05 16:17
from __future__ import unicode_literals

from django.db import migrations, models
import lipids.models


class Migration(migrations.Migration):

    dependencies = [
        ('lipids', '0012_auto_20180105_1502'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lipid',
            name='img',
            field=models.ImageField(null=True, upload_to=lipids.models.img_path, validators=[lipids.models.validate_file_extension]),
        ),
    ]
