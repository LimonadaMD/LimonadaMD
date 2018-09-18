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
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, DeleteView, UpdateView

# local Django
from .forms import ForcefieldForm, SelectForcefieldForm
from .models import Forcefield

headers = {'software': 'asc',
           'forcefield_type': 'asc',
           'name': 'asc'}


def FfList(request):

    ff_list = Forcefield.objects.all()

    params = request.GET.copy()

    selectparams = {}
    for param in ['software', 'forcefield_type']:
        if param in request.GET.keys():
            if request.GET[param] != '':
                selectparams[param] = request.GET[param]
    form_select = SelectForcefieldForm(selectparams)
    if form_select.is_valid():
        if 'software' in selectparams.keys():
            ff_list = ff_list.filter(software=selectparams['software'])
        if 'forcefield_type' in selectparams.keys():
            ff_list = ff_list.filter(forcefield_type=selectparams['forcefield_type'])

    if 'ffid' in request.GET.keys():
        try:
            ffid = int(request.GET['ffid'])
        except ValidationError:
            ffid = 0
        if ffid > 0:
            ff_list = ff_list.filter(id=ffid)

    if 'curator' in request.GET.keys():
        try:
            curator = int(request.GET['curator'])
        except ValidationError:
            curator = 0
        if curator > 0:
            ff_list = ff_list.filter(curator=User.objects.filter(id=curator))

    sort = request.GET.get('sort')
    if sort is not None:
        ff_list = ff_list.order_by(sort)
        if headers[sort] == 'des':
            ff_list = ff_list.reverse()
            headers[sort] = 'asc'
        else:
            headers[sort] = 'des'

    per_page = 25
    if 'per_page' in request.GET.keys():
        try:
            per_page = int(request.GET['per_page'])
        except ValidationError:
            per_page = 25
    if per_page not in [10, 25, 100]:
        per_page = 25
    paginator = Paginator(ff_list, per_page)

    page = request.GET.get('page')
    try:
        forcefields = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        forcefields = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        forcefields = paginator.page(paginator.num_pages)

    data = {}
    data['form_select'] = form_select
    data['page_objects'] = forcefields
    data['per_page'] = per_page
    data['sort'] = sort
    if sort is not None:
        data['dir'] = headers[sort]
    data['forcefields'] = True
    data['params'] = params

    return render(request, 'forcefields/forcefields.html', data)


@method_decorator(staff_member_required, name='dispatch')
class FfCreate(CreateView):
    model = Forcefield
    form_class = ForcefieldForm
    template_name = 'forcefields/ff_form.html'

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.curator = self.request.user
        self.object.save()
        refs = form.cleaned_data['reference']
        for ref in refs:
            self.object.reference.add(ref)
        return HttpResponseRedirect(self.object.get_absolute_url())

    def get_context_data(self, **kwargs):
        context_data = super(FfCreate, self).get_context_data(**kwargs)
        context_data['forcefields'] = True
        context_data['ffcreate'] = True
        return context_data


@method_decorator(staff_member_required, name='dispatch')
class FfUpdate(UpdateView):
    model = Forcefield
    form_class = ForcefieldForm
    template_name = 'forcefields/ff_form.html'

    def form_valid(self, form):
        self.object = form.save()
        self.object.save()
        return HttpResponseRedirect(self.object.get_absolute_url())

    def get_context_data(self, **kwargs):
        context_data = super(FfUpdate, self).get_context_data(**kwargs)
        context_data['forcefields'] = True
        return context_data


@method_decorator(staff_member_required, name='dispatch')
class FfDelete(DeleteView):
    model = Forcefield
    template_name = 'forcefields/ff_delete.html'

    def get_success_url(self):
        return reverse('fflist')

    def get_context_data(self, **kwargs):
        context_data = super(FfDelete, self).get_context_data(**kwargs)
        context_data['forcefields'] = True
        return context_data
