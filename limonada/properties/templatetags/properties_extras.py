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

# Django
from django import template

# local Django
from properties.choices import PROPTYPE_CHOICES


register = template.Library()


@register.simple_tag
def property_type(prop):
   proptypes = dict((key, val) for key, val in PROPTYPE_CHOICES)

   return proptypes[prop]


@register.simple_tag
def property_name(search_name):
   name = '_'.join(search_name.split('_')[1:])

   return name


@register.simple_tag
def get_bokeh_div(bokeh, propid):
   div = bokeh[propid]

   return div
