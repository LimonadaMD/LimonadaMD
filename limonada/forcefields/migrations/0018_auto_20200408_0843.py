# -*- coding: utf-8 -*-
# Generated by Django 1.11.26 on 2020-04-08 08:43
from __future__ import unicode_literals

from django.db import migrations, models
import forcefields.models


class Migration(migrations.Migration):

    dependencies = [
        ('forcefields', '0017_auto_20200402_1637'),
    ]

    operations = [
        migrations.AlterField(
            model_name='forcefield',
            name='ff_file',
            field=models.FileField(help_text='Use a zip file containing the forcefield directory', upload_to=forcefields.models.ff_path, validators=[forcefields.models.validate_file_extension, forcefields.models.validate_ff_size]),
        ),
        migrations.AlterField(
            model_name='forcefield',
            name='forcefield_type',
            field=models.CharField(choices=[('AA', 'All atom'), ('UA', 'United atom'), ('CG', 'Coarse grained')], default='AA', max_length=2),
        ),
        migrations.AlterField(
            model_name='forcefield',
            name='mdp_file',
            field=models.FileField(help_text='Use a zip file containing the mdps for the version X of Gromacs', null=True, upload_to=forcefields.models.mdp_path, validators=[forcefields.models.validate_file_extension, forcefields.models.validate_mdp_size]),
        ),
    ]