# -*- coding: utf-8 -*-
# Generated by Django 1.11.26 on 2020-04-02 16:37
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('forcefields', '0016_auto_20181122_1533'),
    ]

    operations = [
        migrations.CreateModel(
            name='FfComment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comment', models.TextField(blank=True)),
                ('date', models.DateTimeField(auto_now=True)),
                ('forcefield', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='forcefields.Forcefield')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AlterField(
            model_name='software',
            name='abbreviation',
            field=models.CharField(max_length=5),
        ),
        migrations.AlterField(
            model_name='software',
            name='order',
            field=models.CharField(max_length=3),
        ),
    ]
