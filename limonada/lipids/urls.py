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
from .views import (LipAutocomplete, LipCreate, LipDelete, LipDetail, LipList,
                    LipUpdate, TopAutocomplete, TopCreate, TopDelete, TopDetail,
                    TopList, TopUpdate)

urlpatterns = [
    url(r'^lipids/$', LipList, name='liplist'),
    url(r'^lipids/create/$', LipCreate, name='lipcreate'),
    url(r'^lipids/(?P<slug>\w+)/$', LipDetail.as_view(), name='lipdetail'),
    url(r'^lipids/(?P<slug>\w+)/update/$', LipUpdate, name='lipupdate'),
    url(r'^lipids/(?P<slug>\w+)/delete/$', login_required(LipDelete.as_view()), name='lipdelete'),
    url(r'^lipid-autocomplete/$', LipAutocomplete.as_view(), name='lipid-autocomplete'),
    url(r'^topologies/$', TopList, name='toplist'),
    url(r'^topologies/create/$', login_required(TopCreate.as_view()), name='topcreate'),
    url(r'^topologies/(?P<pk>\d+)/$', TopDetail.as_view(), name='topdetail'),
    url(r'^topologies/(?P<pk>\d+)/update/$', login_required(TopUpdate.as_view()), name='topupdate'),
    url(r'^topologies/(?P<pk>\d+)/delete/$', login_required(TopDelete.as_view()), name='topdelete'),
    url(r'^topology-autocomplete/$', TopAutocomplete.as_view(), name='topology-autocomplete'),
]
