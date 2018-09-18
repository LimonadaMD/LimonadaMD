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
from .views import FfCreate, FfDelete, FfList, FfUpdate

urlpatterns = [
    url(r'^forcefields/$', FfList, name='fflist'),
    url(r'^forcefields/create/$', login_required(FfCreate.as_view()), name='ffcreate'),
    url(r'^forcefields/(?P<pk>\d+)/update/$', login_required(FfUpdate.as_view()), name='ffupdate'),
    url(r'^forcefields/(?P<pk>\d+)/delete/$', login_required(FfDelete.as_view()), name='ffdelete'),
]
