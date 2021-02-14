# -*- coding: utf-8; Mode: python; tab-width: 4; indent-tabs-mode:nil; -*-
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
#
#    Limonada is accessible at https://limonada.univ-reims.fr/
#    Copyright (C) 2016-2020 - The Limonada Team (see the AUTHORS file)
#
#    This file is part of Limonada.
#
#    Limonada is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Limonada is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Limonada.  If not, see <http://www.gnu.org/licenses/>.

# standard library
from unidecode import unidecode
import os

# Django
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver
from django.utils.encoding import python_2_unicode_compatible

# Django apps
from limonada.functions import delete_file

# local Django
from .choices import PROPTYPE_CHOICES


def validate_file_extension(value):
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.xvg']
    if ext not in valid_extensions:
        raise ValidationError(u'File not supported!')


def validate_file_size(value):
    filesize = value.size
    if filesize > 209715:
        raise ValidationError("The maximum file size that can be uploaded is 200KB")


def directory_path(instance, filename):
    ext = os.path.splitext(filename)[1]
    filepath = 'properties/{0}{1}'.format(instance.search_name, ext)
    if os.path.isfile(os.path.join(settings.MEDIA_ROOT, filepath)):
        os.remove(os.path.join(settings.MEDIA_ROOT, filepath))
    return filepath


@python_2_unicode_compatible
class LI_Property(models.Model):

    search_name = models.CharField(max_length=100,
                                   blank=True)
    prop = models.CharField(max_length=3,
                            choices=PROPTYPE_CHOICES,
                            default='APL')
    membranetopol = models.ForeignKey('membranes.MembraneTopol', 
                                      on_delete=models.CASCADE)
    data_file = models.FileField(upload_to=directory_path,
                                 help_text='Only .xvg files are supported',
                                 validators=[validate_file_extension,
                                             validate_file_size],
                                 blank=True,
                                 null=True)
    software = models.ForeignKey('properties.AnalysisSoftware',
                                 on_delete=models.CASCADE)
    index = models.PositiveIntegerField(null=True)
    description = models.TextField(blank=True)
    date = models.DateField(auto_now=True)
    curator = models.ForeignKey(User,
                                on_delete=models.CASCADE)

    def __str__(self):
        return self.search_name


@python_2_unicode_compatible
class AnalysisSoftware(models.Model):

    software = models.CharField(max_length=50)

    def __str__(self):
        return self.software


@receiver(pre_delete, sender=LI_Property)
def delete_file_pre_delete_prop(sender, instance, *args, **kwargs):
    if instance.data_file:
        delete_file(instance.data_file.path)
