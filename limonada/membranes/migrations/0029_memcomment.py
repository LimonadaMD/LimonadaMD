# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2018-10-17 08:17
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('membranes', '0028_auto_20181012_1051'),
    ]

    operations = [
        migrations.CreateModel(
            name='MemComment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comment', models.TextField(blank=True)),
                ('date', models.DateTimeField(auto_now=True)),
                ('membrane', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='membranes.MembraneTopol')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
