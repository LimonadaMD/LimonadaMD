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
from django.contrib.auth import views as auth_views

# local Django
from .forms import LoginForm
from .views import activation, UserAutocomplete, UserDetail, signup, update, userinfo

urlpatterns = [
    url(r'^login/$', auth_views.LoginView.as_view(), {'template_name': 'homepage/index.html', 'authentication_form': LoginForm,
        'extra_context': {'homepage': True}}, name='login'),
    url(r'^logout/$', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    url(r'^signup/$', signup, name='signup'),
    url(r'^activation/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        activation, name='activation'),
    url(r'^update/$', update, name='update'),
    url(r'^userinfo/$', userinfo, name='userinfo'),
    url(r'^users/(?P<pk>\d+)/$', UserDetail.as_view(), name='userdetail'),
    url(r'^user-autocomplete/$', UserAutocomplete.as_view(), name='user-autocomplete'),
    url(r'^password_reset/$', auth_views.PasswordResetView.as_view(), {'extra_context': {'homepage': True}}, name='password_reset'),
    url(r'^password_reset/done/$', auth_views.PasswordResetDoneView.as_view(), {'extra_context': {'homepage': True}},
        name='password_reset_done'),
    url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        auth_views.PasswordResetConfirmView.as_view(), {'extra_context': {'homepage': True}}, name='password_reset_confirm'),
    url(r'^reset/done/$', auth_views.PasswordResetCompleteView.as_view(), {'extra_context': {'homepage': True}},
        name='password_reset_complete'),
]
