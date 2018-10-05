# -*- coding: utf-8; Mode: python; tab-width: 4; indent-tabs-mode:nil; -*-
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
#
#    Limonada is accessible at https://www.limonadamd.eu/
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
import os
import unicodedata

# Django
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver

# local Django
from .choices import FFTYPE_CHOICES, SFTYPE_CHOICES


def validate_file_extension(value):
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.zip']
    if ext not in valid_extensions:
        raise ValidationError(u'File not supported!')


def ff_path(instance, filename):
    name = unicodedata.normalize('NFKD', instance.name).encode('ascii', 'ignore').replace(' ', '_')
    filepath = 'forcefields/Gromacs/{0}.ff.zip'.format(name)
    if os.path.isfile(os.path.join(settings.MEDIA_ROOT, filepath)):
        os.remove(os.path.join(settings.MEDIA_ROOT, filepath))
    return filepath


def mdp_path(instance, filename):
    name = unicodedata.normalize('NFKD', instance.name).encode('ascii', 'ignore').replace(' ', '_')
    filepath = 'forcefields/Gromacs/{0}.mdp.zip'.format(name)
    if os.path.isfile(os.path.join(settings.MEDIA_ROOT, filepath)):
        os.remove(os.path.join(settings.MEDIA_ROOT, filepath))
    return filepath


class Forcefield(models.Model):

    name = models.CharField(max_length=30,
                            unique=True)
    forcefield_type = models.CharField(max_length=2,
                                       choices=FFTYPE_CHOICES,
                                       default='AA')
    ff_file = models.FileField(upload_to=ff_path,
                               validators=[validate_file_extension],
                               help_text='Use a zip file containing the forcefield directory')
    mdp_file = models.FileField(upload_to=mdp_path,
                                validators=[validate_file_extension],
                                help_text='Use a zip file containing the mdps for the version X of Gromacs')
    software = models.CharField(max_length=4,
                                choices=SFTYPE_CHOICES,
                                default='GR50')
    description = models.TextField(blank=True)
    reference = models.ManyToManyField('homepage.Reference')
    curator = models.ForeignKey(User,
                                on_delete=models.CASCADE)
    date = models.DateField(auto_now=True)

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('fflist')


def _delete_file(path):
    if os.path.isfile(path):
        os.remove(path)


@receiver(pre_delete, sender=Forcefield)
def delete_file_pre_delete_ff(sender, instance, *args, **kwargs):
    if instance.ff_file:
        _delete_file(instance.ff_file.path)
    if instance.mdp_file:
        _delete_file(instance.mdp_file.path)
