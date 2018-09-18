# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-11-22 13:13
from __future__ import unicode_literals

from django.db import migrations, models

import lipids.models


class Migration(migrations.Migration):

    dependencies = [
        ('lipids', '0006_topology_curator'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lipid',
            name='img',
            field=models.FileField(null=True, upload_to=lipids.models.img_path, validators=[lipids.models.validate_file_extension]),
        ),
    ]
