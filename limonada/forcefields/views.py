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

# standard library
import os
import shutil

# Django
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.generic import CreateView, DeleteView, UpdateView

# local Django
from .forms import ForcefieldForm, SelectForcefieldForm
from .models import Forcefield

# Django apps
from homepage.functions import FileData
from lipids.models import Topology
from membranes.models import MembraneTopol

headers = {'software': 'asc',
           'forcefield_type': 'asc',
           'name': 'asc'}


@never_cache
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


@staff_member_required
@never_cache
def FfCreate(request):
    ffpath = ''
    mdppath = ''
    if request.method == 'POST':
        file_data = {}
        file_data, ffpath = FileData(request, 'ff_file', 'ffpath', file_data)
        file_data, mdppath = FileData(request, 'mdp_file', 'mdppath', file_data)
        form = ForcefieldForm(request.POST, file_data)
        if form.is_valid():
            ff = form.save(commit=False)
            ff.curator = request.user
            ff.save()
            if os.path.isfile('media/' + ffpath):
                os.remove('media/' + ffpath)
            if os.path.isfile('media/' + mdppath):
                os.remove('media/' + mdppath)
            refs = form.cleaned_data['reference']
            for ref in refs:
                ff.reference.add(ref)
            ff.save()
            return HttpResponseRedirect(reverse('fflist'))
    else:
        form = ForcefieldForm()
    return render(request, 'forcefields/ff_form.html', {'form': form, 'forcefields': True, 'ffcreate': True,
        'ffpath': ffpath, 'mdppath': mdppath})


@staff_member_required
@never_cache
def FfUpdate(request, pk=None):
    if Forcefield.objects.filter(pk=pk).exists():
        ff = Forcefield.objects.get(pk=pk)
        if ff.curator != request.user:
            return redirect('homepage')
        if request.method == 'POST':
            file_data = {}
            file_data, ffpath = FileData(request, 'ff_file', 'ffpath', file_data)
            file_data, mdppath = FileData(request, 'mdp_file', 'mdppath', file_data)
            form = ForcefieldForm(request.POST, file_data, instance=ff)
            if form.is_valid():
                form.save()
                if os.path.isfile('media/' + ffpath):
                    os.remove('media/' + ffpath)
                if os.path.isfile('media/' + mdppath):
                    os.remove('media/' + mdppath)
                return HttpResponseRedirect(reverse('fflist'))
        else:
            ffpath = 'tmp/%s' % os.path.basename(ff.ff_file.name)
            shutil.copy(ff.ff_file.url[1:], 'media/tmp/')
            mdppath = 'tmp/%s' % os.path.basename(ff.mdp_file.name)
            shutil.copy(ff.mdp_file.url[1:], 'media/tmp/')
            form = ForcefieldForm(instance=ff)
        return render(request, 'forcefields/ff_form.html', {'form': form, 'forcefields': True,
            'ffpath': ffpath, 'mdppath': mdppath})


@staff_member_required
def FfDelete(request, pk=None):
    if Forcefield.objects.filter(pk=pk).exists():
        ff = Forcefield.objects.get(pk=pk)
        if ff.curator != request.user:
            return redirect('homepage')
        mt = MembraneTopol.objects.filter(forcefield=ff).distinct()
        top = Topology.objects.filter(forcefield=ff).distinct()
        curator = True
        for obj in mt:
           if obj.curator != request.user:
               curator = False
        for obj in top:
           if obj.curator != request.user:
               curator = False
        if curator == True:
            if request.method == 'POST':
                ff.delete()
                for obj in mt:
                    m = obj.membrane
                    obj.delete()
                    if not MembraneTopol.objects.filter(membrane=m).count():
                        m.delete()
                for obj in top:
                    obj.delete()
                return HttpResponseRedirect(reverse('fflist'))
            return render(request, 'forcefields/ff_delete.html',
                {'forcefields': True, 'ff': ff, 'nbtop': len(top), 'nbmem': len(mt)})
        return render(request, 'forcefields/ff_notdelete.html',
            {'forcefields': True, 'ff': ff, 'nbtop': len(top), 'nbmem': len(mt)})
