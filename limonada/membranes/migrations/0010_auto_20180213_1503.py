# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('membranes', '0009_auto_20180212_1330'),
    ]

    operations = [
        migrations.AlterField(
            model_name='membrane',
            name='organel',
            field=models.CharField(max_length=30, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='membrane',
            name='organism',
            field=models.CharField(max_length=30, blank=True),
            preserve_default=True,
        ),
    ]
