# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2018-04-12 10:13
from __future__ import unicode_literals

from django.db import migrations, models

import membranes.models


class Migration(migrations.Migration):

    dependencies = [
        ('membranes', '0020_auto_20180412_0841'),
    ]

    operations = [
        migrations.AlterField(
            model_name='membranetopol',
            name='mem_file',
            field=models.FileField(blank=True, help_text=b'.pdb and .gro files are supported', null=True, upload_to=membranes.models.directory_path, validators=[membranes.models.validate_file_extension]),
        ),
    ]
