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
from django.conf.urls import url
from django.contrib.auth.decorators import login_required

# local Django
from .views import (homepage, links, mail, RefCreate, RefDelete, AuthorAutocomplete,
                    ReferenceAutocomplete, RefList, RefUpdate)

urlpatterns = [
    url(r'^$', homepage, name='homepage'),
    url(r'^references/$', RefList, name='reflist'),
    url(r'^references/create/$', RefCreate, name='refcreate'),
    url(r'^references/(?P<pk>\d+)/update/$', RefUpdate, name='refupdate'),
    url(r'^references/(?P<pk>\d+)/delete/$', login_required(RefDelete.as_view()), name='refdelete'),
    url(r'^reference-autocomplete/$', ReferenceAutocomplete.as_view(), name='reference-autocomplete'),
    url(r'^author-autocomplete/$', AuthorAutocomplete.as_view(), name='author-autocomplete'),
    url(r'^links/$', links, name='links'),
    url(r'^mail/$', mail, name='mail'),
]
