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
from future.moves.urllib.parse import urlencode
import os
import re

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
    """ This function keeps the web URL with all the GET parameters
        and only updates the ones specified.
    """
    query = context['request'].GET.dict()
    query.update(kwargs)
    return urlencode(query)


@register.simple_tag
def inrange(value, end, dx):
    """ This function is used for pagination to slide the
        pages window when there is to many pages.
    """
    if value + dx >= 1 and value + dx <= end:
        return value + dx
    elif dx < 0:
        return 1
    else:
        return end


@register.filter(name='basename')
def basename(value):
    return str(value).split("/")[-1]


@register.filter(name='dirname')
def dirname(value):
    return os.path.dirname(value)


@register.filter(name='slashbreak')
def slashbreak(value):
    """ This function is used to add an invisible space in a string
        after a "/" and enable a carriage return when necessary.
    """
    return re.sub(r'/', '/&#8203;', value)
