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
import codecs
import operator
import os
import random
import shutil
import unicodedata
import zipfile
from contextlib import contextmanager
from string import ascii_lowercase as abc

# third-party
import simplejson
from dal import autocomplete

# Django
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.core.urlresolvers import reverse
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache
from django.views.generic import DeleteView, DetailView

# Django apps
from forcefields.models import Forcefield, Software
from homepage.functions import FileData
from lipids.models import Lipid, Topology

# local Django
from .forms import MemCommentForm, MembraneForm, MembraneTopolForm, MemFormSet, SelectMembraneForm
from .functions import membraneanalysis
from .models import MemComment, Composition, Membrane, MembraneTag, MembraneTopol, TopolComposition


def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file))


@contextmanager
def cd(newdir):
    prevdir = os.getcwd()
    os.chdir(os.path.expanduser(newdir))
    try:
        yield
    finally:
        os.chdir(prevdir)


@never_cache
def MemList(request):

    mem_list = MembraneTopol.objects.all()

    params = request.GET.copy()

    form_select = SelectMembraneForm()
    selectparams = {}
    for param in ['equilibration', 'lipids', 'tags', 'nbliptypes', 'nblipids']:
        if param in request.GET.keys():
            if request.GET[param] != '':
                if param == 'lipids':
                    liplist = request.GET[param].split(',')
                    selectparams['lipids'] = liplist
                elif param == 'tags':
                    taglist = request.GET[param].split(',')
                    selectparams['tags'] = taglist
                else:
                    selectparams[param] = request.GET[param]
    form_select = SelectMembraneForm(selectparams)
    if form_select.is_valid():
        if 'equilibration' in selectparams.keys():
            mem_list = mem_list.filter(equilibration__gte=selectparams['equilibration'])
        if 'lipids' in selectparams.keys():
            querylist = []
            for i in liplist:
                querylist.append(Q(lipids=Lipid.objects.filter(id=i)))
            mem_list = mem_list.filter(reduce(operator.or_, querylist)).distinct()
        if 'tags' in selectparams.keys():
            querylist = []
            for i in taglist:
                querylist.append(Q(membrane=Membrane.objects.filter(tag=i)))
            mem_list = mem_list.filter(reduce(operator.or_, querylist)).distinct()
        if 'nbliptypes' in selectparams.keys():
            mem_list = mem_list.filter(membrane=Membrane.objects.filter(nb_liptypes__gt=selectparams['nbliptypes']))
        if 'nblipids' in selectparams.keys():
            mem_list = mem_list.filter(nb_lipids__gt=selectparams['nblipids'])

    if 'memid' in request.GET.keys():
        try:
            memid = int(request.GET['memid'])
        except ValidationError:
            memid = 0
        if memid > 0:
            mem_list = mem_list.filter(id=memid)

    if 'topid' in request.GET.keys():
        try:
            topid = int(request.GET['topid'])
        except ValidationError:
            topid = 0
        if topid > 0:
            mem_list = mem_list.filter(topolcomposition__topology=topid).distinct()

    if 'curator' in request.GET.keys():
        try:
            curator = int(request.GET['curator'])
        except ValidationError:
            curator = 0
        if curator > 0:
            mem_list = mem_list.filter(curator=User.objects.filter(id=curator))

    sort = request.GET.get('sort')
    sortdir = request.GET.get('dir')
    headers = ['name', 'nbliptypes', 'nb_lipids']
    if sort is not None and sort in headers:
        if sort == 'nbliptypes':
            mem_list = mem_list.order_by('membrane__nb_liptypes')
        else:
            mem_list = mem_list.order_by(sort)
        if sortdir == 'des':
            mem_list = mem_list.reverse()

    per_page = 25
    if 'per_page' in request.GET.keys():
        try:
            per_page = int(request.GET['per_page'])
        except ValidationError:
            per_page = 25
    if per_page not in [10, 25, 100]:
        per_page = 25
    paginator = Paginator(mem_list, per_page)

    page = request.GET.get('page')
    try:
        membranes = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        membranes = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        membranes = paginator.page(paginator.num_pages)

    data = {}
    data['form_select'] = form_select
    data['page_objects'] = membranes
    data['per_page'] = per_page
    data['sort'] = sort
    if sort is not None and sort in headers:
        data['dir'] = sortdir
    data['membranes'] = True
    data['params'] = params
    data['comps'] = Composition.objects.all()

    return render(request, 'membranes/membranes.html', data)


def formsetdata(mem_file, ff, mempath):
    fname = os.path.splitext(mem_file.name)[0]
    rand = str(random.randrange(1000))
    while os.path.isdir(os.path.join(settings.MEDIA_ROOT, 'tmp', rand)):
        rand = random.randrange(1000)
    dirname = os.path.join(settings.MEDIA_ROOT, 'tmp', rand)
    os.makedirs(dirname)
    fs = FileSystemStorage(location=dirname)
    f = fs.save(mem_file.name, mem_file)

    merrors = []
    minfos = []
    compo, membrane = membraneanalysis(mem_file.name, rand)
    if len(compo.keys()) == 1 and membrane.title != 'error':
        merrors.append('There is a problem with fatslim.')
    if membrane.prot:
        minfos.append('This membrane contains proteins.')
    if len(membrane.unkres.keys()) > 0:
        minfos.append('The following residues are not yet part of Limonada: %s.' % ', '.join(membrane.unkres.keys()))
    if membrane.nblf > 2:
        merrors.append('Several membranes are present in the structure file.')
    if len(compo['unk'].keys()) > 0 and len(membrane.unkres.keys()) == 0:
        merrors.append('Several lipids are not part of the membrane.')

    file_data = ''
    if len(merrors) > 0 or membrane.title == 'error':
        data = {'form-TOTAL_FORMS': 1,
                'form-INITIAL_FORMS': '0',
                'form-MAX_NUM_FORMS': ''}
    else:
        nb = len(compo['up'].keys()) + len(compo['lo'].keys())
        data = {'form-TOTAL_FORMS': nb+1,
                'form-INITIAL_FORMS': '0',
                'form-MAX_NUM_FORMS': ''}
        i = 0
        for lip in sorted(compo['up'], key=compo['up'].__getitem__, reverse=True):
            lid = Lipid.objects.filter(name=lip).values_list('id', flat=True)[0]
            data['form-%d-lipid' % (i)] = lid
            data['form-%d-topology' % (i)] = ''
            if ff != '':
                if Topology.objects.filter(lipid=lid, forcefield=ff).exists():
                    topid = Topology.objects.filter(lipid=lid, forcefield=ff).values_list('id', flat=True)[0]
                    data['form-%d-topology' % (i)] = topid
            data['form-%d-number' % (i)] = compo['up'][lip]
            data['form-%d-side' % (i)] = 'UP'
            i += 1
        for lip in sorted(compo['lo'], key=compo['lo'].__getitem__, reverse=True):
            lid = Lipid.objects.filter(name=lip).values_list('id', flat=True)[0]
            data['form-%d-lipid' % (i)] = lid
            data['form-%d-topology' % (i)] = ''
            if ff != '':
                if Topology.objects.filter(lipid=lid, forcefield=ff).exists():
                    topid = Topology.objects.filter(lipid=lid, forcefield=ff).values_list('id', flat=True)[0]
                    data['form-%d-topology' % (i)] = topid
            data['form-%d-number' % (i)] = compo['lo'][lip]
            data['form-%d-side' % (i)] = 'LO'
            i += 1
        sortedgrofilepath = os.path.join(dirname, '%s_sorted.gro' % fname)
        if os.path.isfile(sortedgrofilepath):
            f = file('media/tmp/%s/%s_sorted.gro' % (rand, fname))
            file_data = {'mem_file': SimpleUploadedFile(f.name, f.read())}
            mempath = os.path.join('tmp/', rand, '%s_sorted.gro' % fname)

    return merrors, minfos, data, file_data, rand, fname, mempath


@login_required
@never_cache
def MemCreate(request, formset_class, template):
    rand = ''
    fname = ''
    mempath = ''
    merrors = []
    minfos = []
    if request.method == 'POST' and 'add' in request.POST:
        file_data = {}
        file_data, mempath = FileData(request, 'mem_file', 'mempath', file_data)
        topform = MembraneTopolForm(request.POST, file_data)
        memform = MembraneForm(request.POST)
        formset = formset_class(request.POST)
        if topform.is_valid() and memform.is_valid() and formset.is_valid():
            mt = topform.save(commit=False)
            mt.curator = request.user
            mt.save()
            nb_lipids = 0
            nb_lipup = 0
            nb_liplo = 0
            topcomp = []
            for lip in formset:
                lipid = lip.cleaned_data.get('lipid')
                topology = lip.cleaned_data.get('topology')
                number = lip.cleaned_data.get('number')
                side = lip.cleaned_data.get('side')
                if lipid:
                    nb_lipids += number
                    if side == 'UP':
                        nb_lipup += number
                    else:
                        nb_liplo += number
                    topcomp.append(TopolComposition(membrane=mt, lipid=lipid, topology=topology, number=number,
                                                    side=side))
            refs = topform.cleaned_data['reference']
            for ref in refs:
                mt.reference.add(ref)
            mt.nb_lipids = nb_lipids

            # Build a unique name based on the lipid composition
            lipupnames = {}
            lipupnumbers = {}
            liplonames = {}
            liplonumbers = {}
            liptypes = []
            for lip in formset:
                lipid = lip.cleaned_data.get('lipid')
                if lipid:
                    number = lip.cleaned_data.get('number')
                    side = lip.cleaned_data.get('side')
                    if side == 'UP':
                        nb = ('%7.4f' % (100*float(number)/nb_lipup)).rstrip('0').rstrip('.')
                        if lipid.name in lipupnames.keys():
                            nbtemp = '%7.4f' % (100*(float(number)+float(lipupnumbers[lipid.name]))/nb_lipup)
                            nb = nbtemp.rstrip('0').rstrip('.')
                        lipupnames[lipid.name] = 'u' + lipid.name + nb
                        lipupnumbers[lipid.name] = nb
                    else:
                        nb = ('%7.4f' % (100*float(number)/nb_liplo)).rstrip('0').rstrip('.')
                        if lipid.name in liplonames.keys():
                            nb = '%7.4f' % (100*(float(number)+float(liplonumbers[lipid.name]))/nb_liplo)
                            nb = nbtemp.rstrip('0').rstrip('.')
                        liplonames[lipid.name] = 'l' + lipid.name + nb
                        liplonumbers[lipid.name] = nb
                    if lipid not in liptypes:
                        liptypes.append(lipid)
            name = ''
            compodata = '[ leaflet_1 ]\n'
            for key in sorted(lipupnumbers, key=lipupnumbers.__getitem__, reverse=True):
                name += '-' + lipupnames[key]
                compodata += '%10s%10s\n' % (lipupnames[key][1:5], lipupnames[key][5:])
            compodata += '\n[ leaflet_2 ]\n'
            for key in sorted(liplonumbers, key=liplonumbers.__getitem__, reverse=True):
                name += '-' + liplonames[key]
                compodata += '%10s%10s\n' % (liplonames[key][1:5], liplonames[key][5:])
            # Create a new Membrane object if it doesn't exists
            if Membrane.objects.filter(name=name[1:]).exists():
                m = Membrane.objects.get(name=name[1:])
                tags = memform.cleaned_data['tag']
                for tag in tags:
                    if tag not in m.tag.all():
                        m.tag.add(tag)
                m.save()
            else:
                m = memform.save(commit=False)
                m.name = name[1:]
                m.nb_liptypes = len(liptypes)
                m.save()
                tags = memform.cleaned_data['tag']
                for tag in tags:
                    m.tag.add(tag)
                m.save()
                comp = []
                for lip in formset:
                    lipid = lip.cleaned_data.get('lipid')
                    number = lip.cleaned_data.get('number')
                    side = lip.cleaned_data.get('side')
                    if lipid:
                        if side == 'UP':
                            comp.append(Composition(membrane=m, lipid=lipid, number=100*float(number)/nb_lipup,
                                                    side=side))
                        else:
                            comp.append(Composition(membrane=m, lipid=lipid, number=100*float(number)/nb_liplo,
                                                    side=side))
                try:
                    with transaction.atomic():
                        Composition.objects.filter(membrane=m).delete()
                        Composition.objects.bulk_create(comp)
                        messages.success(request, 'You have updated your composition.')
                except IntegrityError:
                    messages.error(request, 'There was an error saving your composition.')

            rand = request.POST['rand']
            fname = request.POST['fname']
            mempath = 'media/tmp/%s/%s_sorted.gro' % (rand, fname)
            memname = unicodedata.normalize('NFKD', mt.name).encode('ascii', 'ignore').replace(' ', '_')
            if not request.FILES and os.path.isfile(mempath):
                newmempath = 'media/membranes/LIM{0}_{1}.gro'.format(mt.id, memname)
                shutil.copy(mempath, newmempath)
                mt.mem_file = 'membranes/LIM{0}_{1}.gro'.format(mt.id, memname)
            compofile = open('media/membranes/LIM{0}_{1}.txt'.format(mt.id, memname), 'w')
            compofile.write(compodata)
            compofile.close()
            mt.compo_file = 'membranes/LIM{0}_{1}.txt'.format(mt.id, memname)

            mt.membrane = m
            mt.save()

            if rand:
                shutil.rmtree(os.path.join(settings.MEDIA_ROOT, 'tmp', rand), ignore_errors=True)

#           Create the composition objects
            try:
                with transaction.atomic():
                    TopolComposition.objects.filter(membrane=mt).delete()
                    TopolComposition.objects.bulk_create(topcomp)
                    messages.success(request, 'You have updated your composition.')
            except IntegrityError:
                messages.error(request, 'There was an error saving your composition.')

            return HttpResponseRedirect(reverse('memlist'))
    elif request.method == 'POST' and 'analyze' in request.POST:
        file_data = {}
        file_data, mempath = FileData(request, 'mem_file', 'mempath', file_data)
        topform = MembraneTopolForm(request.POST, file_data)
        memform = MembraneForm(request.POST)
        mem_file = file_data['mem_file']
        data = {'form-TOTAL_FORMS': 1,
                'form-INITIAL_FORMS': '0',
                'form-MAX_NUM_FORMS': ''}
        if 'forcefield' in topform.data:
            ff = topform.data['forcefield']
            merrors, minfos, data, file_data, rand, fname, mempath = formsetdata(mem_file, ff, mempath)
            if file_data != '':
                topform = MembraneTopolForm(request.POST, file_data)
        formset = MemFormSet(data)
    else:
        topform = MembraneTopolForm()
        memform = MembraneForm()
        formset = formset_class()
    return render(request, template, {
        'topform': topform, 'memform': memform, 'formset': formset, 'tops': Topology.objects.all(), 'membranes': True,
        'memcreate': True, 'merrors': merrors, 'minfos': minfos, 'rand': rand, 'fname': fname, 'mempath': mempath})


@login_required
@never_cache
@transaction.atomic
def MemUpdate(request, pk=None):
    rand = ''
    fname = ''
    merrors = []
    minfos = []
    if MembraneTopol.objects.filter(pk=pk).exists():
        mt = MembraneTopol.objects.get(pk=pk)
        mempath_init = mt.mem_file.name
        compopath_init = mt.compo_file.name
        if mt.curator != request.user:
            return redirect('homepage')
        if request.method == 'POST' and 'add' in request.POST:
            file_data = {}
            file_data, mempath = FileData(request, 'mem_file', 'mempath', file_data)
            topform = MembraneTopolForm(request.POST, file_data, instance=mt)
            memform = MembraneForm(request.POST, instance=mt.membrane)
            formset = MemFormSet(request.POST)
            if topform.is_valid() and memform.is_valid() and formset.is_valid():
                mt = topform.save()
                nb_lipids = 0
                nb_lipup = 0
                nb_liplo = 0
                topcomp = []
                for lip in formset:
                    lipid = lip.cleaned_data.get('lipid')
                    if lipid:
                        topology = lip.cleaned_data.get('topology')
                        number = lip.cleaned_data.get('number')
                        side = lip.cleaned_data.get('side')
                        if lipid:
                            nb_lipids += number
                            if side == 'UP':
                                nb_lipup += number
                            else:
                                nb_liplo += number
                            topcomp.append(TopolComposition(membrane=mt, lipid=lipid, topology=topology, number=number,
                                                            side=side))
                mt.nb_lipids = nb_lipids
                mt.reference.clear()
                refs = topform.cleaned_data['reference']
                for ref in refs:
                    mt.reference.add(ref)
                mt.nb_lipids = nb_lipids

#               Build a unique name based on the lipid composition
                lipupnames = {}
                lipupnumbers = {}
                liplonames = {}
                liplonumbers = {}
                liptypes = []
                for lip in formset:
                    lipid = lip.cleaned_data.get('lipid')
                    if lipid:
                        number = lip.cleaned_data.get('number')
                        side = lip.cleaned_data.get('side')
                        if side == 'UP':
                            nb = ('%7.4f' % (100*float(number)/nb_lipup)).rstrip('0').rstrip('.')
                            if lipid.name in lipupnames.keys():
                                nbtemp = '%7.4f' % (100*(float(number)+float(lipupnumbers[lipid.name]))/nb_lipup)
                                nb = nbtemp.rstrip('0').rstrip('.')
                            lipupnames[lipid.name] = 'u' + lipid.name + nb
                            lipupnumbers[lipid.name] = nb
                        else:
                            nb = ('%7.4f' % (100*float(number)/nb_liplo)).rstrip('0').rstrip('.')
                            if lipid.name in liplonames.keys():
                                nbtemp = '%7.4f' % (100*(float(number)+float(liplonumbers[lipid.name]))/nb_liplo)
                                nb = nbtemp.rstrip('0').rstrip('.')
                            liplonames[lipid.name] = 'l' + lipid.name + nb
                            liplonumbers[lipid.name] = nb
                        if lipid not in liptypes:
                            liptypes.append(lipid)
                name = ''
                compodata = '[ leaflet_1 ]\n'
                for key in sorted(lipupnumbers, key=lipupnumbers.__getitem__, reverse=True):
                    name += '-' + lipupnames[key]
                    compodata += '%10s%10s\n' % (lipupnames[key][1:5], lipupnames[key][5:])
                compodata += '\n[ leaflet_2 ]\n'
                for key in sorted(liplonumbers, key=liplonumbers.__getitem__, reverse=True):
                    name += '-' + liplonames[key]
                    compodata += '%10s%10s\n' % (liplonames[key][1:5], liplonames[key][5:])

                # Create a new Membrane object if it changed and doesn't exists
                if Membrane.objects.filter(name=name[1:]).exists():
                    m = Membrane.objects.get(name=name[1:])
                    tags = memform.cleaned_data['tag']
                    for tag in tags:
                        if tag not in m.tag.all():
                            m.tag.add(tag)
                    m.save()
                else:
                    m = memform.save(commit=False)
                    m.name = name[1:]
                    m.nb_liptypes = len(liptypes)
                    m.save()
                    tags = memform.cleaned_data['tag']
                    for tag in tags:
                        m.tag.add(tag)
                    m.save()
                    comp = []
                    for lip in formset:
                        lipid = lip.cleaned_data.get('lipid')
                        if lipid:
                            number = lip.cleaned_data.get('number')
                            side = lip.cleaned_data.get('side')
                            if lipid:
                                if side == 'UP':
                                    comp.append(Composition(membrane=m, lipid=lipid, number=100*float(number)/nb_lipup,
                                                            side=side))
                                else:
                                    comp.append(Composition(membrane=m, lipid=lipid, number=100*float(number)/nb_liplo,
                                                            side=side))
                    try:
                        with transaction.atomic():
                            Composition.objects.filter(membrane=m).delete()
                            Composition.objects.bulk_create(comp)
                            messages.success(request, 'You have updated your composition.')
                    except IntegrityError:
                        messages.error(request, 'There was an error saving your composition.')

                rand = request.POST['rand']
                fname = request.POST['fname']
                mempath = 'media/tmp/%s/%s_sorted.gro' % (rand, fname)
                memname = unicodedata.normalize('NFKD', mt.name).encode('ascii', 'ignore').replace(' ', '_')
                if not request.FILES and os.path.isfile(mempath):
                    newmempath = 'media/membranes/LIM{0}_{1}.gro'.format(mt.id, memname)
                    shutil.copy(mempath, newmempath)
                    mt.mem_file = 'membranes/LIM{0}_{1}.gro'.format(mt.id, memname)
                compofile = open('media/membranes/LIM{0}_{1}.txt'.format(mt.id, memname), 'w')
                compofile.write(compodata)
                compofile.close()
                mt.compo_file = 'membranes/LIM{0}_{1}.txt'.format(mt.id, memname)

                mt.membrane = m
                mt.save()

                if rand:
                    shutil.rmtree(os.path.join(settings.MEDIA_ROOT, 'tmp', rand), ignore_errors=True)
                if mempath_init != mt.mem_file:
                    os.remove('media/' + mempath_init)
                if compopath_init != mt.compo_file:
                    os.remove('media/' + compopath_init)

                # Create the composition objects
                try:
                    with transaction.atomic():
                        TopolComposition.objects.filter(membrane=mt).delete()
                        TopolComposition.objects.bulk_create(topcomp)
                        messages.success(request, 'You have updated your composition.')
                except IntegrityError:
                    messages.error(request, 'There was an error saving your composition.')

                return HttpResponseRedirect(reverse('memlist'))
        elif request.method == 'POST' and 'mem_file' in request.FILES.keys():
            file_data = {}
            file_data, mempath = FileData(request, 'mem_file', 'mempath', file_data)
            topform = MembraneTopolForm(request.POST, file_data, instance=mt)
            memform = MembraneForm(request.POST, instance=mt.membrane)
            mem_file = file_data['mem_file']
            data = {'form-TOTAL_FORMS': 1,
                    'form-INITIAL_FORMS': '0',
                    'form-MAX_NUM_FORMS': ''}
            if 'forcefield' in topform.data:
                ff = topform.data['forcefield']
                merrors, minfos, data, file_data, rand, fname, mempath = formsetdata(mem_file, ff, mempath)
                if file_data != '':
                    topform = MembraneTopolForm(request.POST, file_data)
            formset = MemFormSet(data)
        else:
            mempath = ''
            if mt.mem_file: 
                mempath = 'tmp/%s' % os.path.basename(mt.mem_file.name)
                shutil.copy(mt.mem_file.url[1:], 'media/tmp/')
            topform = MembraneTopolForm(instance=mt)
            memform = MembraneForm(instance=mt.membrane)
            c = TopolComposition.objects.filter(membrane=mt)
            data = {'form-TOTAL_FORMS': len(c)+1,
                    'form-INITIAL_FORMS': '0',
                    'form-MAX_NUM_FORMS': ''}
            i = 0
            for lip in c:
                data['form-%d-lipid' % (i)] = lip.lipid
                data['form-%d-topology' % (i)] = lip.topology
                data['form-%d-number' % (i)] = lip.number
                data['form-%d-side' % (i)] = lip.side
                i += 1
            formset = MemFormSet(data)
        return render(request, 'membranes/mem_form.html', {
            'topform': topform, 'memform': memform, 'formset': formset, 'tops': Topology.objects.all(), 
            'membranes': True, 'merrors': merrors, 'minfos': minfos, 'rand': rand, 'fname': fname, 'mempath': mempath})
    else:
        return HttpResponseRedirect(reverse('memlist'))


@never_cache
def MemDetail(request, pk=None):
    if MembraneTopol.objects.filter(pk=pk).exists():
        membrane = MembraneTopol.objects.get(pk=pk)
        if membrane.forcefield.forcefield_type == 'CG':
            representation = 'spacefill' #'ball+stick'
        else:
            representation = 'licorice'
        mem_file = ''
        if membrane.mem_file:
            mem_file = membrane.mem_file.url
        if request.method == 'POST':
            form = MemCommentForm(request.POST)
            if form.is_valid():
                comment = form.save(commit=False)
                comment.membrane = membrane
                comment.user = request.user
                comment.save()
                if request.user != membrane.curator:
                    email = request.user.email
                    subject = 'New comment on your Limonada entry %s' % (membrane.name)
                    text = ''.join(('Dear Mr/Ms %s %s,' % (membrane.curator.first_name, membrane.curator.last_name),
                                   '\n\n%s %s has published ' % (comment.user.first_name, comment.user.last_name),
                                   'the following comment on %s.\n\n' % (comment.date.strftime("%b. %d, %Y at %H:%M")),
                                   '%s\n\nSincerely,\nThe Limonada Team' % (comment.comment)))
                    send_mail(subject, text, settings.VERIFIED_EMAIL_MAIL_FROM, [email, ])
                form = MemCommentForm()
        else:
            form = MemCommentForm()
        comments = MemComment.objects.filter(membrane=membrane)
        return render(request, 'membranes/mem_detail.html', {'membranetopol': membrane, 'comments': comments, 'form': form,
            'mem_file': mem_file, 'rep': representation, 'membranes': True})


@login_required
def MemDelete(request, pk=None):
    if MembraneTopol.objects.filter(pk=pk).exists():
        mt = MembraneTopol.objects.get(pk=pk)
        if mt.curator != request.user:
            return redirect('homepage')
        comments = MemComment.objects.filter(membrane=mt)
        if request.method == 'POST':
            m = mt.membrane
            mt.delete()
            if not MembraneTopol.objects.filter(membrane=m).count():
                m.delete()
            for obj in comments:
                obj.delete()
            return HttpResponseRedirect(reverse('memlist'))
        return render(request, 'membranes/mem_delete.html', {'membranes': True, 'mt': mt})


class MembraneAutocomplete(autocomplete.Select2QuerySetView):

    def get_queryset(self):
        qs = Membrane.objects.all()
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        return qs


def GetLipTops(request):
    lipid_id = request.GET['lip']
    ff_id = request.GET['ff']
    topologies = []
    if lipid_id and ff_id:
        if Lipid.objects.filter(id=lipid_id).exists() and Forcefield.objects.filter(id=ff_id).exists():
            topologies = Topology.objects.filter(lipid=Lipid.objects.get(id=lipid_id),
                                                 forcefield=Forcefield.objects.get(id=ff_id))
    result_set = []
    for top in topologies:
        result_set.append({'value': top.id, 'name': top.version})
    return HttpResponse(simplejson.dumps(result_set), content_type='application/json')


def GetFiles(request):
    image_data = ''
    if 'memid' in request.GET.keys():
        memid = request.GET['memid']
        if memid != '':
            if MembraneTopol.objects.filter(id=memid).exists():
                mem = MembraneTopol.objects.get(id=memid)
                memname = unicodedata.normalize('NFKD', mem.name).encode('ascii', 'ignore').replace(' ', '_')

                mediadir = settings.MEDIA_ROOT
                rand = str(random.randrange(1000))
                while os.path.isdir(os.path.join(mediadir, 'tmp', rand)):
                    rand = random.randrange(1000)
                dirname = os.path.join(mediadir, 'tmp', rand, memname)
                os.makedirs(dirname)
                topdir = os.path.join(dirname, 'toppar')
                os.makedirs(topdir)

                ffzip = zipfile.ZipFile(mem.forcefield.ff_file.url[1:])
                ffdir = ffzip.namelist()[0]
                ffzip.extractall(dirname)

                mdpzip = zipfile.ZipFile(mem.forcefield.mdp_file.url[1:])
                mdpzip.extractall(dirname)

                topfile = open(os.path.join(dirname, 'topol.top'), 'w')
                topfile.write('')
                topfile.write('#include "%sforcefield.itp"\n\n' % ffdir)

                if mem.mem_file:
                    shutil.copy(mem.mem_file.url[1:], dirname)
                else:
                    grodir = os.path.join(dirname, 'lipids')
                    os.makedirs(grodir)
                tops = {}
                for lip in mem.topolcomposition_set.all():
                    if lip.topology.id not in tops.keys():
                        lipname = lip.lipid.name
                        i = 0
                        while lipname in tops.values():
                            lipname = '%s%s' % (lip.lipid.name, abc[i:i+1])
                            i += 1
                        tops[lip.topology.id] = lipname
                        topfile.write('#include "toppar/%s.itp"\n' % lipname)
                    lipname = tops[lip.topology.id]
                    if lipname == lip.lipid.name:
                        shutil.copy(lip.topology.itp_file.url[1:], topdir)
                        if not mem.mem_file:
                            shutil.copy(lip.topology.gro_file.url[1:], grodir)
                    else:
                        infile = codecs.open(lip.topology.itp_file.url[1:], 'r', encoding='utf-8')
                        filedata = infile.read()
                        infile.close()
                        newdata = filedata.replace(' %s' % lip.lipid.name, lipname)
                        newdata2 = newdata.replace('%s ' % lip.lipid.name, lipname)
                        outfile = codecs.open('%s.itp' % os.path.join(topdir, lipname), 'w', encoding='utf-8')
                        outfile.write(newdata2)
                        outfile.close()
                        if not mem.mem_file:
                            infile = codecs.open(lip.topology.gro_file.url[1:], 'r', encoding='utf-8')
                            filedata = infile.read()
                            infile.close()
                            newdata = filedata.replace('%s ' % lip.lipid.name, lipname)
                            outfile = codecs.open('%s.gro' % os.path.join(grodir, lipname), 'w', encoding='utf-8')
                            outfile.write(newdata)
                            outfile.close()
                topfile.write('\n[ system ]\n')
                topfile.write('%s\n\n' % mem.name)
                topfile.write('[ molecules ]\n')
                for lip in mem.topolcomposition_set.all():
                    topfile.write('%-6s%10s\n' % (tops[lip.topology.id], lip.number))
                topfile.close()

                zipf = zipfile.ZipFile('%s.zip' % os.path.join(mediadir, 'tmp', rand, memname), 'w',
                                       zipfile.ZIP_DEFLATED)
                with cd(os.path.join(mediadir, 'tmp', rand)):
                    zipdir(memname, zipf)
                    image_data = open('%s.zip' % memname, 'rb')
                zipf.close()

                shutil.rmtree(os.path.join(mediadir, 'tmp', rand), ignore_errors=True)

    response = HttpResponse(image_data, content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename=%s.zip' % memname
    return response


class MembraneTagAutocomplete(autocomplete.Select2QuerySetView):

    def get_queryset(self):
        qs = MembraneTag.objects.all()
        if self.q:
            qs = qs.filter(tag__icontains=self.q)
        return qs
