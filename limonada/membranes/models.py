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
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver
from django.utils.formats import localize

# Django apps
from limonada.functions import delete_file


def validate_file_extension(value):
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.gro', '.pdb']
    if ext not in valid_extensions:
        raise ValidationError(u'File not supported!')


def directory_path(instance, filename):
    ext = os.path.splitext(filename)[1]
    name = unicodedata.normalize('NFKD', instance.name).encode('ascii', 'ignore').replace(' ', '_')
    filepath = 'membranes/LIM{0}_{1}{2}'.format(instance.id, name, ext)
    if os.path.isfile(os.path.join(settings.MEDIA_ROOT, filepath)):
        os.remove(os.path.join(settings.MEDIA_ROOT, filepath))
    return filepath


class MembraneTopol(models.Model):

    name = models.CharField(max_length=100)
    membrane = models.ForeignKey('Membrane',
                                 null=True,
                                 on_delete=models.CASCADE)
    lipids = models.ManyToManyField('lipids.Lipid',
                                    through='TopolComposition')
    temperature = models.PositiveIntegerField()
    equilibration = models.PositiveIntegerField()
    mem_file = models.FileField(upload_to=directory_path,
                                help_text='.pdb and .gro files are supported',
                                validators=[validate_file_extension],
                                blank=True,
                                null=True)
    compo_file = models.FileField(upload_to=directory_path,
                                  blank=True,
                                  null=True)
    software = models.ForeignKey('forcefields.Software')
    forcefield = models.ForeignKey('forcefields.Forcefield',
                                   on_delete=models.CASCADE)
    nb_lipids = models.PositiveIntegerField(null=True)
    description = models.TextField(blank=True)
    reference = models.ManyToManyField('homepage.Reference')
    date = models.DateField(auto_now=True)
    curator = models.ForeignKey(User,
                                on_delete=models.CASCADE)
    # salt []

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.id is None:
            saved_mem_file = self.mem_file
            self.mem_file = None
            super(MembraneTopol, self).save(*args, **kwargs)
            self.mem_file = saved_mem_file
        super(MembraneTopol, self).save(*args, **kwargs)


class TopolComposition(models.Model):

    UPPER = 'UP'
    LOWER = 'LO'
    LEAFLET_CHOICES = ((UPPER, 'Upper leaflet'),
                       (LOWER, 'Lower leaflet'))

    membrane = models.ForeignKey(MembraneTopol,
                                 on_delete=models.CASCADE)
    lipid = models.ForeignKey('lipids.Lipid',
                              on_delete=models.CASCADE)
    topology = models.ForeignKey('lipids.Topology',
                                 on_delete=models.CASCADE)
    number = models.PositiveIntegerField()
    side = models.CharField(max_length=2,
                            choices=LEAFLET_CHOICES,
                            default=UPPER)


class Membrane(models.Model):

    name = models.TextField(unique=True, null=True, blank=True)
    lipids = models.ManyToManyField('lipids.Lipid',
                                    through='Composition')
    tag = models.ManyToManyField('membranes.MembraneTag',
                                 blank=True)
    nb_liptypes = models.PositiveIntegerField(null=True)

    def __unicode__(self):
        return self.name


class MembraneTag(models.Model):

    tag = models.CharField(max_length=30,
                           unique=True)

    def __unicode__(self):
        return self.tag


class Composition(models.Model):

    UPPER = 'UP'
    LOWER = 'LO'
    LEAFLET_CHOICES = ((UPPER, 'Upper leaflet'),
                       (LOWER, 'Lower leaflet'))

    membrane = models.ForeignKey(Membrane,
                                 on_delete=models.CASCADE)
    lipid = models.ForeignKey('lipids.Lipid',
                              on_delete=models.CASCADE)
    number = models.DecimalField(max_digits=7, decimal_places=4)
    side = models.CharField(max_length=2,
                            choices=LEAFLET_CHOICES,
                            default=UPPER)


class MemComment(models.Model):

    membrane = models.ForeignKey(MembraneTopol,
                                 on_delete=models.CASCADE)
    comment = models.TextField(blank=True)
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return '%s %s %s' % (self.user.username, self.membrane.name, localize(self.date))


@receiver(pre_delete, sender=MembraneTopol)
def delete_file_pre_delete_mem(sender, instance, *args, **kwargs):
    if instance.mem_file:
        delete_file(instance.mem_file.path)
    if instance.compo_file:
        delete_file(instance.compo_file.path)
