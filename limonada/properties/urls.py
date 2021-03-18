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
from .views import PropList, PropCreate, PropDetail, PropUpdate, PropDelete
from .views import PropAutocomplete, AnalysisSoftwareAutocomplete

urlpatterns = [
    url(r'^properties/$', PropList, name='proplist'),
    url(r'^properties/create/$', PropCreate, name='propcreate'),
    url(r'^properties/(?P<pk>\d+)/$', PropDetail.as_view(), name='propdetail'),
    url(r'^properties/(?P<pk>\d+)/update/$', PropUpdate, name='propupdate'),
    url(r'^properties/(?P<pk>\d+)/delete/$', login_required(PropDelete.as_view()), name='propdelete'),
    url(r'^prop-autocomplete/$', PropAutocomplete.as_view(), name='prop-autocomplete'),
    url(r'^analysissoftware-autocomplete/$', AnalysisSoftwareAutocomplete.as_view(create_field='software'),
        name='analysissoftware-autocomplete'),
]