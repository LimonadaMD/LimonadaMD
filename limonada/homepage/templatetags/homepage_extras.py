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
import urllib

# Django
from django import template

# local Django
from .. import __version__

register = template.Library()


@register.simple_tag
def version():
    return __version__


@register.simple_tag(takes_context=True)
def url_replace(context, **kwargs):
    query = context['request'].GET.dict()
    query.update(kwargs)
    return urllib.urlencode(query)


@register.simple_tag
def inrange(value, end, dx):
    if dx < 0:
        if value + dx >= 1:
            return value + dx
        else:
            return 1
    else:
        if value + dx <= end:
            return value + dx
        else:
            return end


@register.filter(name='basename')
def split(value):
    return str(value).split("/")[-1]


@register.filter(name='dirname')
def dirname(value):
    return os.path.dirname(value)


@register.filter(name='slashbreak')
def slashbreak(value):
    return re.sub(r'/', '/&#8203;', value) 
