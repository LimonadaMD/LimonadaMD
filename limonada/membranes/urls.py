# -*- coding: utf-8; Mode: python; tab-width: 4; indent-tabs-mode:nil; -*-
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
#
#  Copyright (C) 2016-2020  Jean-Marc Crowet <jeanmarccrowet@gmail.com>
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
from .forms import MemFormSet
from .views import (GetFiles, GetLipTops, MembraneAutocomplete, MembraneTagAutocomplete, MemCreate,
                    MemDelete, MemDetail, MemList, MemUpdate)

urlpatterns = [
    url(r'^membranes/$', MemList, name='memlist'),
    url(r'^membranes/create/$', MemCreate, {'formset_class': MemFormSet, 'template': 'membranes/mem_form.html'},
        name='memcreate'),
    url(r'^membranes/(?P<pk>\d+)/$', MemDetail.as_view(), name='memdetail'),
    url(r'^membranes/(?P<pk>\d+)/update/$', MemUpdate, name='memupdate'),
    url(r'^membranes/(?P<pk>\d+)/delete/$', login_required(MemDelete.as_view()), name='memdelete'),
    url(r'^membrane-autocomplete/$', MembraneAutocomplete.as_view(), name='membrane-autocomplete'),
    url(r'^getliptops/$', GetLipTops, name='getliptops'),
    url(r'^getfiles/$', GetFiles, name='getfiles'),
    url(r'^membranetag-autocomplete/$', MembraneTagAutocomplete.as_view(create_field='tag'),
        name='membranetagautocomplete'),
    url(r'^tag-autocomplete/$', MembraneTagAutocomplete.as_view(), name='tag-autocomplete'),
]
