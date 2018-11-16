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
import re
import unicodedata

# third-party
import requests

# Django
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models.signals import m2m_changed, pre_delete, pre_save
from django.dispatch.dispatcher import receiver
from django.utils.formats import localize
from django.utils.translation import ugettext_lazy as _

# Django apps
from limonada.functions import delete_file


_UNSAVED_ITPFILE = 'unsaved_itpfile'
_UNSAVED_GROFILE = 'unsaved_grofile'

def validate_name(value):
    if len(value) != 4 or not re.match(r'[0-9A-Z]{4}', value):
        raise ValidationError(_('Invalid name'),
                              code='invalid',
                              params={'value': value})


def validate_lmid(value):
    if value[:2] == 'LM':
        try:
            lm_response = requests.get('http://www.lipidmaps.org/rest/compound/lm_id/%s/all/json' % value)
            lm_data_raw = lm_response.json()
            if lm_data_raw == []:
                raise ValidationError(_('Invalid LMID'),
                                      code='invalid',
                                      params={'value': value})
        except ValidationError:
            raise ValidationError(_('Invalid LMID'),
                                  code='invalid',
                                  params={'value': value})
    elif value[:2] != 'LI':
        raise ValidationError(_('Invalid LMID'),
                              code='invalid',
                              params={'value': value})


def validate_file_extension(value):
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.png', '.jpg']
    if ext not in valid_extensions:
        raise ValidationError(u'File not supported!')


def img_path(instance, filename):
    ext = os.path.splitext(filename)[1]
    filepath = 'lipids/{0}{1}'.format(instance.lmid, ext)
    valid_extensions = ['.png', '.jpg']
    for ext in valid_extensions:
        imgpath = 'lipids/{0}{1}'.format(instance.lmid, ext)
        if os.path.isfile(os.path.join(settings.MEDIA_ROOT, imgpath)):
            os.remove(os.path.join(settings.MEDIA_ROOT, imgpath))
    return filepath


def file_path(instance, filename):
    ext = os.path.splitext(filename)[1]
    version = unicodedata.normalize('NFKD', instance.version).encode('ascii', 'ignore').replace(' ', '_')
    forcefield = unicodedata.normalize('NFKD', instance.forcefield.name).encode('ascii', 'ignore').replace(' ', '_')
#   ex.: topologies/Gromacs/Martini/POPC/version/POPC.{itp,gro} (we assume gromacs for now)
    filepath = 'topologies/{0}/{1}/{2}/{3}/{2}{4}'.format(instance.software.all()[0].name, forcefield,
                                                          instance.lipid.name, version, ext)
    if os.path.isfile(os.path.join(settings.MEDIA_ROOT, filepath)):
        os.remove(os.path.join(settings.MEDIA_ROOT, filepath))
    return filepath


class Lipid(models.Model):

    name = models.CharField(max_length=4,
                            unique=True)
    lmid = models.CharField(max_length=20,
                            unique=True)
    com_name = models.CharField(max_length=200,
                                unique=True)
    search_name = models.CharField(max_length=300,
                                   null=True)
    sys_name = models.CharField(max_length=200,
                                null=True)
    iupac_name = models.CharField(max_length=500,
                                  null=True)
    formula = models.CharField(max_length=30,
                               null=True)
    core = models.CharField(max_length=200,
                            null=True)
    main_class = models.CharField(max_length=200,
                                  null=True)
    sub_class = models.CharField(max_length=200,
                                 null=True)
    l4_class = models.CharField(max_length=200,
                                null=True,
                                blank=True)
    pubchem_cid = models.CharField(max_length=50,
                                   null=True)
    img = models.ImageField(upload_to=img_path,
                            validators=[validate_file_extension],
                            null=True)
    curator = models.ForeignKey(User,
                                on_delete=models.CASCADE)
    date = models.DateField(auto_now=True)
    slug = models.SlugField()

    def __unicode__(self):
        return self.search_name

    def get_absolute_url(self):
        return reverse('liplist')


class Topology(models.Model):

    software = models.ManyToManyField('forcefields.Software')
    forcefield = models.ForeignKey('forcefields.Forcefield',
                                   on_delete=models.CASCADE)
    lipid = models.ForeignKey(Lipid,
                              on_delete=models.CASCADE)
    itp_file = models.FileField(upload_to=file_path)
    gro_file = models.FileField(upload_to=file_path)
    version = models.CharField(max_length=30,
                               help_text='YearAuthor')
    description = models.TextField(blank=True)
    reference = models.ManyToManyField('homepage.Reference')
    date = models.DateField(auto_now=True)
    curator = models.ForeignKey(User,
                                on_delete=models.CASCADE)

    def __unicode__(self):
        return '%s_%s' % (self.lipid.name, self.version)

    def get_absolute_url(self):
        return reverse('toplist')


class TopComment(models.Model):

    topology = models.ForeignKey('lipids.Topology',
                                 on_delete=models.CASCADE)
    comment = models.TextField(blank=True)
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return '%s %s %s %s' % (self.user.username, self.topology.lipid.name, self.topology.version,
            localize(self.date))


@receiver(pre_delete, sender=Lipid)
def delete_file_pre_delete_lip(sender, instance, *args, **kwargs):
    if instance.img:
         delete_file(instance.img.path)


@receiver(pre_delete, sender=Topology)
def delete_file_pre_delete_top(sender, instance, *args, **kwargs):
    if instance.itp_file:
         delete_file(instance.itp_file.path)
    if instance.gro_file:
         delete_file(instance.gro_file.path)


@receiver(pre_save, sender=Topology)
def skip_saving_file(sender, instance, **kwargs):
    if not instance.pk and not hasattr(instance, _UNSAVED_GROFILE):
        setattr(instance, _UNSAVED_ITPFILE, instance.itp_file)
        instance.itp_file = None
        setattr(instance, _UNSAVED_GROFILE, instance.gro_file)
        instance.gro_file = None


@receiver(m2m_changed, sender=Topology.software.through)
def save_file_on_m2m(sender, instance, action, **kwargs):
    """ The directory where the topology files will be saved involve in its path the name of the software
        familly with which it can be used. For the Topology table, software is a ManyToMany field that
        can only be saved once the Topology instance has an id.
    """
    if action == 'post_add' and hasattr(instance, _UNSAVED_ITPFILE) and hasattr(instance, _UNSAVED_GROFILE):
        instance.itp_file = getattr(instance, _UNSAVED_ITPFILE)
        instance.gro_file = getattr(instance, _UNSAVED_GROFILE)
        instance.save()        
        instance.__dict__.pop(_UNSAVED_ITPFILE)
        instance.__dict__.pop(_UNSAVED_GROFILE)
