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

# Django
from django.conf.urls import url
from django.views.decorators.cache import never_cache

# local Django
from .views import (GetSoftVersionList, GetFfList, GetLiIndex, GetLmClass, LipAutocomplete, LipCreate,
                    LipDelete, LipDetail, LipList, LipUpdate, TopAutocomplete, TopCreate, TopDelete,
                    TopDetail, TopList, TopUpdate)

urlpatterns = [
    url(r'^lipids/$', LipList, name='liplist'),
    url(r'^lipids/create/$', LipCreate, name='lipcreate'),
    url(r'^lipids/(?P<slug>\w+)/$', never_cache(LipDetail.as_view()), name='lipdetail'),
    url(r'^lipids/(?P<slug>\w+)/update/$', LipUpdate, name='lipupdate'),
    url(r'^lipids/(?P<slug>\w+)/delete/$', LipDelete, name='lipdelete'),
    url(r'^load_lmclass/$', GetLmClass, name='load_lmclass'),
    url(r'^load_liindex/$', GetLiIndex, name='load_liindex'),
    url(r'^load_svlist/$', GetSoftVersionList, name='load_svlist'),
    url(r'^load_fflist/$', GetFfList, name='load_fflist'),
    url(r'^lipid-autocomplete/$', LipAutocomplete.as_view(), name='lipid-autocomplete'),
    url(r'^topologies/$', TopList, name='toplist'),
    url(r'^topologies/create/$', TopCreate, name='topcreate'),
    url(r'^topologies/(?P<pk>\d+)/$', TopDetail, name='topdetail'),
    url(r'^topologies/(?P<pk>\d+)/update/$', TopUpdate, name='topupdate'),
    url(r'^topologies/(?P<pk>\d+)/delete/$', TopDelete, name='topdelete'),
    url(r'^topology-autocomplete/$', TopAutocomplete.as_view(), name='topology-autocomplete'),
]
