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
from functools import reduce
import operator
import os
import shutil

# third-party
import requests
from dal import autocomplete
from bokeh.plotting import figure, output_file, show
from bokeh.embed import components

# Django
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.urls import reverse
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache
from django.views.generic import DeleteView, DetailView

# Django apps
from limonada.functions import FileData, review_notification
from membranes.models import MembraneTopol

# local Django
from .models import LI_Property, AnalysisSoftware
from .forms import LI_PropertyForm, SelectForm
from .functions import bokeh_data, properties_types


def PropList(request):

    prop_list = LI_Property.objects.all().order_by('-membranetopol__membrane__nb_liptypes', 'prop','index')

    params = request.GET.copy()

    selectparams = {}
    for param in ['propid', 'memid']:
        if param in request.GET.keys():
            if request.GET[param] != '':
                if param == 'propid':
                    proplist = request.GET[param].split(',')
                    selectparams['propid'] = proplist
                elif param == 'memid':
                    memlist = request.GET[param].split(',')
                    selectparams['memid'] = memlist
                else:
                    selectparams[param] = request.GET[param]
    form_select = SelectForm(selectparams)
    if form_select.is_valid():
        if 'propid' in selectparams.keys():
            querylist = []
            for i in proplist:
                querylist.append(Q(id=i))
            prop_list = prop_list.filter(reduce(operator.or_, querylist))
        elif 'memid' in selectparams.keys():
            querylist = []
            for i in memlist:
                querylist.append(Q(membranetopol=MembraneTopol.objects.filter(id=i)[0]))
            prop_list = prop_list.filter(reduce(operator.or_, querylist))
    else:
        form_select = SelectForm()

    sort = request.GET.get('sort')
    sortdir = request.GET.get('dir')
    headers = ['mem_search_name', 'prop']
    if sort is not None and sort in headers:
        if sort == 'mem_search_name':
            prop_list = prop_list.order_by('-membranetopol__membrane__nb_liptypes')
        else:
            prop_list = prop_list.order_by(sort)
        if sortdir == 'des':
            prop_list = prop_list.reverse()

    per_page = 25
    if 'per_page' in request.GET.keys():
        try:
            per_page = int(request.GET['per_page'])
        except ValidationError:
            per_page = 25
    if per_page not in [10, 25, 100]:
        per_page = 25
    paginator = Paginator(prop_list, per_page)

    page = request.GET.get('page')
    try:
        props = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        props = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        props = paginator.page(paginator.num_pages)

    bokeh_divs = {}
    bokeh_scripts = []
    for prop in props:
        test, script, div = bokeh_data(prop.data_file.name)
        if test:
            bokeh_divs[prop.id] = div
            bokeh_scripts.append(script)

    data = {}
    data['form_select'] = form_select
    data['page_objects'] = props
    data['per_page'] = per_page
    data['sort'] = sort
    if sort is not None and sort in headers:
        data['dir'] = sortdir
    data['membranes'] = True
    data['params'] = params
    data['bokeh_divs'] = bokeh_divs
    data['bokeh_scripts'] = bokeh_scripts

    return render(request, 'properties/properties.html', data)


class PropDetail(DetailView):
    model = LI_Property
    template_name = 'properties/prop_detail.html'

    def get_context_data(self, **kwargs):
        context_data = super(PropDetail, self).get_context_data(**kwargs)
        test, script, div = bokeh_data(context_data['li_property'].data_file.name)
        context_data['membranes'] = True
        if test:
            context_data['script'] = script
            context_data['div'] = div
        return context_data


@login_required
@never_cache
def PropCreate(request):
    xvgpath = ''
    if request.method == 'POST':
        file_data = {}
        file_data, xvgpath = FileData(request, 'data_file', 'xvgpath', file_data)
        form = LI_PropertyForm(request.POST, file_data)
        if form.is_valid():
            prop = form.save(commit=False)
            prop.curator = request.user
            indexlist = LI_Property.objects.filter(
                membranetopol=prop.membranetopol.id,prop=prop.prop).values_list('index', flat=True)
            index = 1
            while index in indexlist:
                index += 1
            prop.index = index
            proptype = properties_types() 
            prop.search_name = 'LIM{0}_{1}-{2}'.format(prop.membranetopol.id, proptype[prop.prop], index)
            prop.save()
            if os.path.isfile('media/' + xvgpath):
                os.remove('media/' + xvgpath)
            review_notification('creation', 'properties', prop.pk)
            return HttpResponseRedirect(reverse('memlist'))
    else:
        form = LI_PropertyForm()
    return render(request, 'properties/prop_form.html',
                  {'form': form, 'membranes': True, 'propcreate': True, 'xvgpath': xvgpath})


@login_required
@never_cache
def PropUpdate(request, pk=None):
    if LI_Property.objects.filter(pk=pk).exists():
        prop = LI_Property.objects.get(pk=pk)
        mt_init = prop.membranetopol.id
        prop_init = prop.prop
        name_init = prop.search_name
        if prop.curator != request.user:
            return redirect('homepage')
        if request.method == 'POST':
            file_data = {}
            file_data, xvgpath = FileData(request, 'data_file', 'xvgpath', file_data)
            form = LI_PropertyForm(request.POST, file_data, instance=prop)
            if form.is_valid():
                prop = form.save(commit=False)
                if prop.membranetopol.id != mt_init or prop.prop != prop_init:
                    indexlist = LI_Property.objects.filter(
                        membranetopol=prop.membranetopol.id,prop=prop.prop).values_list('index', flat=True)
                    index = 1
                    while index in indexlist:
                        index += 1
                    prop.index = index
                    proptype = properties_types() 
                    prop.search_name = 'LIM{0}_{1}-{2}'.format(prop.membranetopol.id, proptype[prop.prop], index)
                    if os.path.isfile('media/properties/%s.xvg' % name_init):
                        os.remove('media/properties/%s.xvg' % name_init)
                prop.save()
                if os.path.isfile('media/' + xvgpath):
                    os.remove('media/' + xvgpath)
                review_notification('update', 'properties', prop.pk)
                return HttpResponseRedirect(reverse('memlist'))
        else:
            xvgpath = 'tmp/%s' % os.path.basename(prop.data_file.name)
            shutil.copy(prop.data_file.url[1:], 'media/tmp/')
            form = LI_PropertyForm(instance=prop)
        return render(request, 'properties/prop_form.html',
                      {'form': form, 'membranes': True, 'xvgpath': xvgpath})
    else:
        return HttpResponseRedirect(reverse('memlist'))


class PropDelete(DeleteView):
    model = LI_Property
    template_name = 'properties/prop_delete.html'

    def get_success_url(self):
        return reverse('memlist')

    def get_context_data(self, **kwargs):
        context_data = super(PropDelete, self).get_context_data(**kwargs)
        context_data['membranes'] = True
        return context_data


class PropAutocomplete(autocomplete.Select2QuerySetView):

    def get_queryset(self):
        qs = LI_Property.objects.all()
        if self.q:
            qs = qs.filter(search_name__icontains=self.q)
        return qs


class AnalysisSoftwareAutocomplete(autocomplete.Select2QuerySetView):

    def get_queryset(self):
        qs = AnalysisSoftware.objects.all()
        if self.q:
            qs = qs.filter(software__icontains=self.q)
        return qs
