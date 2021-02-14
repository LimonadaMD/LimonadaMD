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
from django.http import HttpResponseServerError
from django.shortcuts import render
from django.template import RequestContext
from django.views.generic.base import TemplateView


class page_not_found_view(TemplateView):
    template_name = '404.html'
    status_code = 404


def error_view(request):
    values_for_template = {}
    return render(request,'500.html',values_for_template,status=500)


class get_error(TemplateView):
    template_name = '502.html'
    status_code = 502


class permission_denied_view(TemplateView):
    template_name = '403.html'
    status_code = 403


class bad_request_view(TemplateView):
    template_name = '400.html'
    status_code = 400
