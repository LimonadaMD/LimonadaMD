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
from __future__ import unicode_literals
from unidecode import unidecode
import os

# Django
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.encoding import python_2_unicode_compatible
from django.utils.formats import localize
from django.db import models
from django.db.models.signals import m2m_changed, pre_delete, pre_save
from django.dispatch.dispatcher import receiver

# Django apps
from limonada.functions import delete_file

# local Django
from .choices import FFTYPE_CHOICES


_UNSAVED_FFFILE = 'unsaved_fffile'
_UNSAVED_MDPFILE = 'unsaved_mdpfile'


def validate_file_extension(value):
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.zip']
    if ext not in valid_extensions:
        raise ValidationError(u'File not supported!')


def validate_ff_size(value):
    filesize = value.size
    if filesize > 5242880:
        raise ValidationError("The maximum file size that can be uploaded is 5MB")
    else:
        return value


def ff_path(instance, filename):
    name = unidecode(instance.name).replace(' ', '_')
    filepath = 'forcefields/{0}/{1}.ff.zip'.format(instance.software.all()[0].name, name)
    if os.path.isfile(os.path.join(settings.MEDIA_ROOT, filepath)):
        os.remove(os.path.join(settings.MEDIA_ROOT, filepath))
    return filepath


def validate_mdp_size(value):
    filesize = value.size
    if filesize > 209715:
        raise ValidationError("The maximum file size that can be uploaded is 200KB")
    else:
        return value


def mdp_path(instance, filename):
    name = unidecode(instance.name).replace(' ', '_')
    filepath = 'forcefields/{0}/{1}.par.zip'.format(instance.software.all()[0].name, name)
    if os.path.isfile(os.path.join(settings.MEDIA_ROOT, filepath)):
        os.remove(os.path.join(settings.MEDIA_ROOT, filepath))
    return filepath


@python_2_unicode_compatible
class Forcefield(models.Model):

    name = models.CharField(max_length=50)
    forcefield_type = models.CharField(max_length=2,
                                       choices=FFTYPE_CHOICES,
                                       default='AA')
    ff_file = models.FileField(upload_to=ff_path,
                               validators=[validate_file_extension,
                                           validate_ff_size],
                               help_text='Use a zip file containing the forcefield directory')
    mdp_file = models.FileField(upload_to=mdp_path,
                                validators=[validate_file_extension,
                                            validate_mdp_size],
                                help_text='Use a zip file containing the mdps for the version X of Gromacs',
                                null=True)
    software = models.ManyToManyField('forcefields.Software')
    description = models.TextField(blank=True)
    reference = models.ManyToManyField('homepage.Reference')
    curator = models.ForeignKey(User,
                                on_delete=models.CASCADE)
    date = models.DateField(auto_now=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('fflist')


@python_2_unicode_compatible
class Software(models.Model):

    name = models.CharField(max_length=50)
    version = models.CharField(max_length=50)
    abbreviation = models.CharField(max_length=5)
    order = models.CharField(max_length=3)

    def __str__(self):
        return "%s %s" % (self.name, self.version)


@python_2_unicode_compatible
class FfComment(models.Model):

    forcefield = models.ForeignKey('forcefields.Forcefield',
                                   on_delete=models.CASCADE)
    comment = models.TextField(blank=True)
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '%s %s %s %s' % (self.user.username, self.forcefield.software.name, self.forcefield.name,
                                localize(self.date))


@receiver(pre_delete, sender=Forcefield)
def delete_file_pre_delete_ff(sender, instance, *args, **kwargs):
    if instance.ff_file:
        delete_file(instance.ff_file.path)
    if instance.mdp_file:
        delete_file(instance.mdp_file.path)


@receiver(pre_save, sender=Forcefield)
def skip_saving_file(sender, instance, **kwargs):
    if not instance.pk and not hasattr(instance, _UNSAVED_FFFILE):
        setattr(instance, _UNSAVED_FFFILE, instance.ff_file)
        instance.ff_file = None
        setattr(instance, _UNSAVED_MDPFILE, instance.mdp_file)
        instance.mdp_file = None


@receiver(m2m_changed, sender=Forcefield.software.through)
def save_file_on_m2m(sender, instance, action, **kwargs):
    """ The directory where the forcefield files will be saved involve in its path the name of the software
        familly with which it can be used. For the Forcefield table, software is a ManyToMany field that
        can only be saved once the Forcefield instance has an id.
    """
    if action == 'post_add' and hasattr(instance, _UNSAVED_FFFILE) and hasattr(instance, _UNSAVED_MDPFILE):
        instance.ff_file = getattr(instance, _UNSAVED_FFFILE)
        instance.mdp_file = getattr(instance, _UNSAVED_MDPFILE)
        instance.save()
        instance.__dict__.pop(_UNSAVED_FFFILE)
        instance.__dict__.pop(_UNSAVED_MDPFILE)
