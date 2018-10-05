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
import datetime

# third-party
import requests

# Django
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.translation import ugettext_lazy as _


def validate_year(value):
    if value < 1950 or value > datetime.datetime.now().year:
        raise ValidationError(_('Year must be > 1950 and < %(value)s'),
                              params={'value': datetime.datetime.now().year})


def validate_doi(value):
    url = 'http://dx.doi.org/%s' % value
    headers = {'Accept': 'application/citeproc+json'}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException:
        raise ValidationError(_('%(value)s is not valid'),
                              code='invalid',
                              params={'value': value})


class Reference(models.Model):

    refid = models.CharField(max_length=200,
                             help_text='Format: AuthorYear[Index]',
                             unique=True)
    authors = models.CharField(max_length=500)
    title = models.CharField(max_length=500)
    journal = models.CharField(max_length=200)
    volume = models.CharField(max_length=30,
                              null=True)
    year = models.PositiveSmallIntegerField(validators=[validate_year])
    doi = models.CharField(max_length=30,
                           validators=[validate_doi],
                           unique=True,
                           null=True)
    curator = models.ForeignKey(User,
                                on_delete=models.CASCADE)
    date = models.DateField(auto_now=True)

    def __unicode__(self):
        return self.refid

    def get_absolute_url(self):
        return reverse('reflist')
