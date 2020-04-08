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
from functools import reduce
import operator
import os
import shutil

# third-party
from dal import autocomplete

# Django
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.urls import reverse
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache

# local Django
from .forms import ForcefieldForm, SelectForcefieldForm, FfCommentForm
from .models import Forcefield, Software, FfComment

# Django apps
from limonada.functions import FileData
from lipids.models import Topology
from membranes.models import MembraneTopol


@never_cache
def FfList(request):

    ff_list = Forcefield.objects.all().order_by('name')

    params = request.GET.copy()

    selectparams = {}
    for param in ['software', 'softversion', 'forcefield_type']:
        if param in request.GET.keys():
            if request.GET[param] != '':
                selectparams[param] = request.GET[param]
    form_select = SelectForcefieldForm(selectparams)
    if form_select.is_valid():
        if 'software' in selectparams.keys():
            softlist = Software.objects.filter(
                abbreviation__istartswith=selectparams['software']).values_list('id', flat=True)
            querylist = []
            for i in softlist:
                querylist.append(Q(software=Software.objects.filter(id=i)))
            ff_list = ff_list.filter(reduce(operator.or_, querylist)).distinct()
        if 'softversion' in selectparams.keys():
            ff_list = ff_list.filter(software=Software.objects.filter(id=selectparams['softversion']))
        if 'forcefield_type' in selectparams.keys():
            ff_list = ff_list.filter(forcefield_type=selectparams['forcefield_type'])
    else:
        form_select = SelectForcefieldForm()

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
    sortdir = request.GET.get('dir')
    headers = ['forcefield_type', 'name']
    if sort is not None and sort in headers:
        ff_list = ff_list.order_by(sort)
        if sortdir == 'des':
            ff_list = ff_list.reverse()

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
    if sort is not None and sort in headers:
        data['dir'] = sortdir
    data['forcefields'] = True
    data['params'] = params

    return render(request, 'forcefields/forcefields.html', data)


@never_cache
def FfDetail(request, pk=None):
    if Forcefield.objects.filter(pk=pk).exists():
        forcefield = Forcefield.objects.get(pk=pk)
        if request.method == 'POST':
            form = FfCommentForm(request.POST)
            if form.is_valid():
                comment = form.save(commit=False)
                comment.forcefield = forcefield
                comment.user = request.user
                comment.save()
                if request.user != forcefield.curator:
                    email = request.user.email
                    subject = 'New comment on your Limonada entry %s_%s' % (forcefield.software.name, forcefield.name)
                    message = ''.join(
                        ('Dear Mr/Ms %s %s,' % (forcefield.curator.first_name, forcefield.curator.last_name),
                         '\n\n%s %s has published ' % (comment.user.first_name, comment.user.last_name),
                         'the following comment on %s.\n\n' % (comment.date.strftime("%b. %d, %Y at %H:%M")),
                         '%s\n\nSincerely,\nThe Limonada Team' % (comment.comment)))
                    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email, ])
                form = FfCommentForm()
        else:
            form = FfCommentForm()
        comments = FfComment.objects.filter(forcefield=forcefield)
        return render(request, 'forcefields/ff_detail.html',
                      {'forcefield': forcefield, 'comments': comments, 'form': form, 'forcefields': True})


@login_required
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
            softwares = form.cleaned_data['software']
            for soft in softwares:
                ff.software.add(soft)
            refs = form.cleaned_data['reference']
            for ref in refs:
                ff.reference.add(ref)
            ff.save()
            return HttpResponseRedirect(reverse('fflist'))
    else:
        form = ForcefieldForm()
    return render(request, 'forcefields/ff_form.html',
                  {'form': form, 'forcefields': True, 'ffcreate': True, 'ffpath': ffpath, 'mdppath': mdppath})


@login_required
@never_cache
def FfUpdate(request, pk=None):
    if Forcefield.objects.filter(pk=pk).exists():
        ff = Forcefield.objects.get(pk=pk)
        software_init = ff.software.all()[0].name
        dir_init = 'media/forcefields/%s' % (ff.software.all()[0].name)
        if ff.curator != request.user:
            return redirect('homepage')
        if request.method == 'POST':
            file_data = {}
            file_data, ffpath = FileData(request, 'ff_file', 'ffpath', file_data)
            mdppath = ''
            if ff.mdp_file:
                file_data, mdppath = FileData(request, 'mdp_file', 'mdppath', file_data)
            form = ForcefieldForm(request.POST, file_data, instance=ff)
            if form.is_valid():
                ff = form.save(commit=False)
                ff.software.clear()
                softwares = form.cleaned_data['software']
                for soft in softwares:
                    ff.software.add(soft)
                ff.reference.clear()
                refs = form.cleaned_data['reference']
                for ref in refs:
                    ff.reference.add(ref)
                ff.save()
                if os.path.isfile('media/' + ffpath):
                    os.remove('media/' + ffpath)
                if mdppath != '' and os.path.isfile('media/' + mdppath):
                    os.remove('media/' + mdppath)
                if software_init != ff.software.all()[0].name:
                    if os.path.isdir(dir_init):
                        shutil.rmtree(dir_init, ignore_errors=True)
                return HttpResponseRedirect(reverse('fflist'))
        else:
            ffpath = 'tmp/%s' % os.path.basename(ff.ff_file.name)
            shutil.copy(ff.ff_file.url[1:], 'media/tmp/')
            mdppath = ''
            if ff.mdp_file:
                mdppath = 'tmp/%s' % os.path.basename(ff.mdp_file.name)
                shutil.copy(ff.mdp_file.url[1:], 'media/tmp/')
            form = ForcefieldForm(instance=ff)
        return render(request, 'forcefields/ff_form.html',
                      {'form': form, 'forcefields': True, 'ffpath': ffpath, 'mdppath': mdppath})


@login_required
def FfDelete(request, pk=None):
    if Forcefield.objects.filter(pk=pk).exists():
        ff = Forcefield.objects.get(pk=pk)
        if ff.curator != request.user:
            return redirect('homepage')
        mt = MembraneTopol.objects.filter(forcefield=ff).distinct()
        top = Topology.objects.filter(forcefield=ff).distinct()
        comments = FfComment.objects.filter(forcefield=ff)
        curator = True
        for obj in mt:
            if obj.curator != request.user:
                curator = False
        for obj in top:
            if obj.curator != request.user:
                curator = False
        if curator:
            if request.method == 'POST':
                ff.delete()
                for obj in mt:
                    m = obj.membrane
                    obj.delete()
                    if not MembraneTopol.objects.filter(membrane=m).count():
                        m.delete()
                for obj in top:
                    obj.delete()
                for obj in comments:
                    obj.delete()
                return HttpResponseRedirect(reverse('fflist'))
            return render(request, 'forcefields/ff_delete.html',
                          {'forcefields': True, 'ff': ff, 'nbtop': len(top), 'nbmem': len(mt)})
        return render(request, 'forcefields/ff_notdelete.html',
                      {'forcefields': True, 'ff': ff, 'nbtop': len(top), 'nbmem': len(mt)})


class SoftwareAutocomplete(autocomplete.Select2QuerySetView):

    def get_queryset(self):
        qs = Software.objects.all().order_by('order')
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        return qs
