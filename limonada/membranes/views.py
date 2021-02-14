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
import codecs
import copy
from functools import reduce
import operator
import os
import re
import random
import shutil
import zipfile
from contextlib import contextmanager
from string import ascii_uppercase as abc
from unidecode import unidecode
import zipfile

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
from django.core.mail import send_mail
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.urls import reverse
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache

# Django apps
from forcefields.models import Forcefield, Software
from limonada.functions import FileData, review_notification
from lipids.models import Lipid, Topology
from properties.models import LI_Property

# local Django
from .forms import MemCommentForm, MembraneForm, MembraneTopolForm, MemFormSet, SelectMembraneForm
from .functions import compo_isvalid, membrane_residues, membraneanalysis, nb_lip_per_leaflet
from .models import MemComment, Composition, Membrane, MembraneTopol, TopolComposition
from .models import MembraneProt, MembraneDoi, MembraneTag


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

    mem_list = MembraneTopol.objects.all().order_by('-membrane__nb_liptypes')

    params = request.GET.copy()

    form_select = SelectMembraneForm()
    selectparams = {}
    for param in ['software', 'softversion', 'forcefield', 'lipids', 'tags', 'prots']:
        if param in request.GET.keys():
            if request.GET[param] != '':
                if param == 'lipids':
                    liplist = request.GET[param].split(',')
                    selectparams['lipids'] = liplist
                elif param == 'prots':
                    protlist = request.GET[param].split(',')
                    selectparams['prots'] = protlist
                elif param == 'tags':
                    taglist = request.GET[param].split(',')
                    selectparams['tags'] = taglist
                elif param == 'software':
                    selectparams[param] = request.GET[param]
                elif param == 'softversion':
                    selectparams[param] = request.GET[param]
                else:
                    selectparams[param] = request.GET[param]
    form_select = SelectMembraneForm(selectparams)
    if form_select.is_valid():
        if 'software' in selectparams.keys():
            softlist = Software.objects.filter(
                abbreviation__istartswith=selectparams['software']).values_list('id', flat=True)
            if softlist:
                querylist = []
                for i in softlist:
                    querylist.append(Q(software=Software.objects.filter(id=i)[0]))
                mem_list = mem_list.filter(reduce(operator.or_, querylist)).distinct()
            else:
                mem_list = MembraneTopol.objects.none()
        if 'softversion' in selectparams.keys():
            mem_list = mem_list.filter(software=Software.objects.filter(id=selectparams['softversion'])[0])
        if 'forcefield' in selectparams.keys():
            mem_list = mem_list.filter(forcefield=Forcefield.objects.filter(id=selectparams['forcefield'])[0])
        if 'lipids' in selectparams.keys():
            querylist = []
            for i in liplist:
                querylist.append(Q(lipids=Lipid.objects.filter(id=i)[0]))
            mem_list = mem_list.filter(reduce(operator.or_, querylist)).distinct()
        if 'prots' in selectparams.keys():
            querylist = []
            for i in protlist:
                querylist.append(Q(prot=MembraneProt.objects.filter(id=i)[0]))
            mem_list = mem_list.filter(reduce(operator.or_, querylist)).distinct()
        if 'tags' in selectparams.keys():
            querylist = []
            for i in taglist:
                querylist.append(Q(membrane=Membrane.objects.filter(tag=i)[0]))
            mem_list = mem_list.filter(reduce(operator.or_, querylist)).distinct()

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
            mem_list = mem_list.filter(curator=User.objects.filter(id=curator)[0])

    sort = request.GET.get('sort')
    sortdir = request.GET.get('dir')
    headers = ['name', 'nbliptypes', 'nb_lipids', 'forcefield']
    if sort is not None and sort in headers:
        if sort == 'nbliptypes':
            mem_list = mem_list.order_by('membrane__nb_liptypes')
        elif sort == 'forcefield':
            mem_list = mem_list.order_by('forcefield__name')
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
    extension = os.path.splitext(mem_file.name)[1]
    rand = str(random.randrange(1000))
    while os.path.isdir(os.path.join(settings.MEDIA_ROOT, 'tmp', rand)):
        rand = str(random.randrange(1000))
    dirname = os.path.join(settings.MEDIA_ROOT, 'tmp', rand)
    os.makedirs(dirname)
    fs = FileSystemStorage(location=dirname)
    f = fs.save(mem_file.name, mem_file)

    merrors = []
    minfos = []
    compo, membrane, ndxdiff = membraneanalysis(mem_file.name, ff, rand)
    if membrane.prot:
        minfos.append('This membrane contains proteins.')
    if membrane.unkres:
        minfos.append('If the following residues are lipids, their topologies are not yet part of Limonada: %s.' % ', '.join(membrane.unkres))
    if membrane.title == 'error':
        merrors.append('The membrane file is not valid or one of the lipid is not available with the selected forcefield.')
    elif len(compo.keys()) == 1:
        merrors.append('fatslim returned en error.')

    nbmemb = 1
    file_data = ''
    if len(merrors) > 0 or membrane.title == 'error':
        data = {'form-TOTAL_FORMS': 1,
                'form-INITIAL_FORMS': '0',
                'form-MAX_NUM_FORMS': ''}
    else:
        nb = 0
        for leaflet in list(compo.keys()):
            nb += len(compo[leaflet].keys())
        data = {'form-TOTAL_FORMS': nb+1,
                'form-INITIAL_FORMS': '0',
                'form-MAX_NUM_FORMS': ''}
        i = 0
        for leaflet in list(compo.keys()):
            for lip in sorted(compo[leaflet], key=compo[leaflet].__getitem__, reverse=True):
                lid = Lipid.objects.filter(name=lip).values_list('id', flat=True)[0]
                data['form-%d-lipid' % (i)] = lid
                data['form-%d-topology' % (i)] = ''
                if ff != '':
                    if Topology.objects.filter(lipid=lid, forcefield=ff).exists():
                        topid = Topology.objects.filter(lipid=lid, forcefield=ff).values_list('id', flat=True)[0]
                        data['form-%d-topology' % (i)] = topid
                data['form-%d-number' % (i)] = compo[leaflet][lip]
                n = 0
                if leaflet == "unk":
                    data['form-%d-side' % (i)] = 'UNK'
                elif leaflet[-2:] == "_1":
                    n = int(leaflet.split("_")[1])
                    if n == 1:
                        data['form-%d-side' % (i)] = 'UP'
                    else:
                        data['form-%d-side' % (i)] = 'UP%d' % n
                else:
                    n = int(leaflet.split("_")[1])
                    if n == 1:
                        data['form-%d-side' % (i)] = 'LO'
                    else:
                        data['form-%d-side' % (i)] = 'LO%d' % n
                i += 1
                if n > nbmemb:
                    nbmemb = n
        sortedgrofilepath = os.path.join(dirname, '%s_sorted%s' % (fname, extension))
        if os.path.isfile(sortedgrofilepath):
            f = open('media/tmp/%s/%s_sorted%s' % (rand, fname, extension), 'rb')
            file_data = {'mem_file': SimpleUploadedFile(f.name, f.read())}
            mempath = os.path.join('tmp/', rand, '%s_sorted%s' % (fname, extension))

    return merrors, minfos, data, file_data, rand, fname, extension, mempath, nbmemb


@login_required
@never_cache
def MemCreate(request, formset_class, template):
    rand = ''
    fname = ''
    extension = ''
    mempath = ''
    otherpath = ''
    nbmemb = 1
    merrors = []
    minfos = []
    if request.method == 'POST' and 'add' in request.POST:
        file_data = {}
        file_data, mempath = FileData(request, 'mem_file', 'mempath', file_data)
        file_data, otherpath = FileData(request, 'other_file', 'otherpath', file_data)
        ffid = simplejson.loads(request.POST.get('forcefield', None))
        forcefield = Forcefield.objects.filter(id=ffid)
        softabb = forcefield[0].software.all()[0].abbreviation
        if os.path.isfile(os.path.join(settings.MEDIA_ROOT, mempath)):
            extension = os.path.splitext(mempath)[1]
            if softabb[:2] != "AM":
                merrors = compo_isvalid(mempath, forcefield[0], request.POST)
        topform = MembraneTopolForm(request.POST, file_data)
        memform = MembraneForm(request.POST)
        formset = formset_class(request.POST)
        if topform.is_valid() and memform.is_valid() and formset.is_valid() and not merrors:
            mt = topform.save(commit=False)
            mt.curator = request.user
            mt.save()
            nb_lipids = 0
            topcomp = []
            nbsides = {}
            for lip in formset:
                lipid = lip.cleaned_data.get('lipid')
                topology = lip.cleaned_data.get('topology')
                number = lip.cleaned_data.get('number')
                side = lip.cleaned_data.get('side')
                if side and side != 'UNK':
                    if len(side) == 2:
                        nbs = 1
                    else:
                        nbs = int(side[2:])
                    if nbs > nbmemb:
                        nbmemb = nbs
                if lipid:
                    nb_lipids += number
                    if side not in nbsides.keys():
                        nbsides[side] = number
                    else:
                        nbsides[side] += number
                    topcomp.append(TopolComposition(membrane=mt, lipid=lipid, topology=topology, number=number,
                                                    side=side))
            refs = topform.cleaned_data['reference']
            for ref in refs:
                mt.reference.add(ref)
            prots = topform.cleaned_data['prot']
            for prot in prots:
                mt.prot.add(prot)
            dois = topform.cleaned_data['doi']
            for doi in dois:
                mt.doi.add(doi)
            mt.nb_lipids = nb_lipids

            # Build a unique name based on the lipid composition
            lipsidenames = {}
            lipsidenumbers = {}
            liptypes = []
            for lip in formset:
                lipid = lip.cleaned_data.get('lipid')
                if lipid:
                    number = lip.cleaned_data.get('number')
                    side = lip.cleaned_data.get('side')
                    if side in lipsidenames.keys(): 
                        if lipid.name in lipsidenames[side].keys():
                            number += lipsidenumbers[side][lipid.name] 
                    else:
                        lipsidenames[side] = {}
                        lipsidenumbers[side] = {}
                    s = "o"
                    if side[:2] == "UP":
                        s = "u"
                    elif side[:2] == "LO":
                        s = "l"
                    lipsidenames[side][lipid.name] = s + side[2:] + lipid.name
                    lipsidenumbers[side][lipid.name] =  number
                    if lipid not in liptypes:
                        liptypes.append(lipid)
            for side in lipsidenames.keys():
                for lipid in lipsidenames[side].keys():
                    nb = ('%7.4f' % (100*float(lipsidenumbers[side][lipid])/nbsides[side])).rstrip('0').rstrip('.') 
                    lipsidenames[side][lipid] = lipsidenames[side][lipid] + nb 
                    lipsidenumbers[side][lipid] = nb
            name = ''
            compodata = ''
            for leaflet in lipsidenames.keys():
                if len(leaflet) == 2:
                    mi = "1"
                elif leaflet == "UNK":
                    mi = "0"
                else:
                    mi = leaflet[2:]
                if leaflet[:2] == "UP":
                    li = 1
                else:
                    li = 2
                if mi == "0":
                    compodata += '[ not_in_leaflet ]\n'
                else:
                    compodata += '[ membrane_%s_leaflet_%d ]\n' % (mi, li)
                if mi == "1":
                    for key in sorted(lipsidenumbers[leaflet], key=lipsidenumbers[leaflet].__getitem__, reverse=True):
                        name += '-' + lipsidenames[leaflet][key]
                        compodata += '%10s%10s\n' % (lipsidenames[leaflet][key][1:5], lipsidenames[leaflet][key][5:])
                elif mi == "0":
                    for key in sorted(lipsidenumbers[leaflet], key=lipsidenumbers[leaflet].__getitem__, reverse=True):
                        name += '-' + lipsidenames[leaflet][key]
                        compodata += '%10s%10s\n' % (lipsidenames[leaflet][key][2:6], lipsidenames[leaflet][key][6:])
                else:
                    ki = len(mi) + 1
                    for key in sorted(lipsidenumbers[leaflet], key=lipsidenumbers[leaflet].__getitem__, reverse=True):
                        name += '-' + lipsidenames[leaflet][key]
                        compodata += '%10s%10s\n' % (lipsidenames[leaflet][key][ki:ki+4], lipsidenames[leaflet][key][ki+4:])
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
                        comp.append(Composition(membrane=m, lipid=lipid, number=100*float(number)/nbsides[side],
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
            mempath = 'media/%s' % mempath
            if rand:
                if os.path.isfile(mempath):
                    os.remove(mempath)
                extension = request.POST['extension']
                mempath = 'media/tmp/%s/%s_sorted%s' % (rand, fname, extension)
            memname = unidecode(mt.name).replace(' ', '_')
            if os.path.isfile(mempath):
                newmempath = 'media/membranes/LIM{0}_{1}{2}'.format(mt.id, memname, extension)
                shutil.copy(mempath, newmempath)
                mt.mem_file = 'membranes/LIM{0}_{1}{2}'.format(mt.id, memname, extension)
                os.remove(mempath)
            compofile = open('media/membranes/LIM{0}_{1}.txt'.format(mt.id, memname), 'w')
            compofile.write(compodata)
            compofile.close()
            mt.compo_file = 'membranes/LIM{0}_{1}.txt'.format(mt.id, memname)

            mt.search_name = "LIM%d_%s" % (mt.id, memname)

            mt.membrane = m
            mt.save()

            if rand:
                shutil.rmtree(os.path.join(settings.MEDIA_ROOT, 'tmp', rand), ignore_errors=True)
            review_notification("creation", "membranes", mt.pk)

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
        file_data, otherpath = FileData(request, 'other_file', 'otherpath', file_data)
        topform = MembraneTopolForm(request.POST, file_data)
        memform = MembraneForm(request.POST)
        data = {'form-TOTAL_FORMS': 1,
                'form-INITIAL_FORMS': '0',
                'form-MAX_NUM_FORMS': ''}
        if 'mem_file' in file_data.keys() and 'forcefield' in topform.data:
            mem_file = file_data['mem_file']
            ff = topform.data['forcefield']
            forcefield = Forcefield.objects.filter(id=ff)
            softabb = forcefield[0].software.all()[0].abbreviation
            if softabb[:2] != "AM":
                merrors, minfos, data, file_data, rand, fname, extension, mempath, nbmemb = formsetdata(mem_file, ff,
                                                                                                        mempath)
            else:
                merrors = ['Structure files associated with Amber cannot be analyzed.']
            if file_data != '':
                topform = MembraneTopolForm(request.POST, file_data)
        formset = MemFormSet(data)
    else:
        topform = MembraneTopolForm()
        memform = MembraneForm()
        formset = formset_class()
    return render(request, template, {
        'topform': topform, 'memform': memform, 'formset': formset, 'tops': Topology.objects.all(), 'membranes': True,
        'memcreate': True, 'merrors': merrors, 'minfos': minfos, 'rand': rand, 'fname': fname, 'extension': extension,
        'mempath': mempath, 'otherpath': otherpath, 'nbmemb': nbmemb})


@login_required
@never_cache
@transaction.atomic
def MemUpdate(request, pk=None):
    rand = ''
    fname = ''
    extension = ''
    nbmemb = 1
    merrors = []
    minfos = []
    if MembraneTopol.objects.filter(pk=pk).exists():
        mt = MembraneTopol.objects.get(pk=pk)
        mempath_init = mt.mem_file.name
        otherpath_init = mt.other_file.name
        compopath_init = mt.compo_file.name
        if mt.curator != request.user:
            return redirect('homepage')
        if request.method == 'POST' and 'add' in request.POST:
            file_data = {}
            mempath = ''
            file_data, mempath = FileData(request, 'mem_file', 'mempath', file_data)
            softabb = mt.forcefield.software.all()[0].abbreviation
            ffid = simplejson.loads(request.POST.get('forcefield', None))
            forcefield = Forcefield.objects.filter(id=ffid)
            if os.path.isfile(os.path.join(settings.MEDIA_ROOT, mempath)):
                extension = os.path.splitext(mempath)[1]
                if softabb[:2] != "AM":
                    merrors = compo_isvalid(mempath, forcefield[0], request.POST)
            otherpath = ''
            file_data, otherpath = FileData(request, 'other_file', 'otherpath', file_data)
            topform = MembraneTopolForm(request.POST, file_data, instance=mt)
            memform = MembraneForm(request.POST, instance=mt.membrane)
            formset = MemFormSet(request.POST)
            if topform.is_valid() and memform.is_valid() and formset.is_valid() and not merrors:
                mt = topform.save()
                nb_lipids = 0
                topcomp = []
                nbsides = {}
                for lip in formset:
                    lipid = lip.cleaned_data.get('lipid')
                    if lipid:
                        topology = lip.cleaned_data.get('topology')
                        number = lip.cleaned_data.get('number')
                        side = lip.cleaned_data.get('side')
                        if side and side != 'UNK':
                            if len(side) == 2:
                                nbs = 1
                            else:
                                nbs = int(side[2:])
                            if nbs > nbmemb:
                                nbmemb = nbs
                        if lipid:
                            nb_lipids += number
                            if side not in nbsides.keys():
                                nbsides[side] = number
                            else:
                                nbsides[side] += number
                            topcomp.append(TopolComposition(membrane=mt, lipid=lipid, topology=topology, number=number,
                                                            side=side))
                mt.nb_lipids = nb_lipids
                mt.reference.clear()
                refs = topform.cleaned_data['reference']
                for ref in refs:
                    mt.reference.add(ref)
                prots = topform.cleaned_data['prot']
                for prot in prots:
                    mt.prot.add(prot)
                dois = topform.cleaned_data['doi']
                for doi in dois:
                    mt.doi.add(doi)
                mt.nb_lipids = nb_lipids

#               Build a unique name based on the lipid composition
                lipsidenames = {}
                lipsidenumbers = {}
                liptypes = []
                for lip in formset:
                    lipid = lip.cleaned_data.get('lipid')
                    if lipid:
                        number = lip.cleaned_data.get('number')
                        side = lip.cleaned_data.get('side')
                        if side in lipsidenames.keys(): 
                            if lipid.name in lipsidenames[side].keys():
                                number += lipsidenumbers[side][lipid.name] 
                        else:
                            lipsidenames[side] = {}
                            lipsidenumbers[side] = {}
                        s = "o"
                        if side[:2] == "UP":
                            s = "u"
                        elif side[:2] == "LO":
                            s = "l"
                        lipsidenames[side][lipid.name] = s + side[2:] + lipid.name
                        lipsidenumbers[side][lipid.name] =  number
                        if lipid not in liptypes:
                            liptypes.append(lipid)
                for side in lipsidenames.keys():
                    for lipid in lipsidenames[side].keys():
                        nb = ('%7.4f' % (100*float(lipsidenumbers[side][lipid])/nbsides[side])).rstrip('0').rstrip('.') 
                        lipsidenames[side][lipid] = lipsidenames[side][lipid] + nb 
                        lipsidenumbers[side][lipid] = nb
                name = ''
                compodata = ''
                for leaflet in lipsidenames.keys():
                    if len(leaflet) == 2:
                        mi = "1"
                    elif leaflet == "UNK":
                        mi = "0"
                    else:
                        mi = leaflet[2:]
                    if leaflet[:2] == "UP":
                        li = 1
                    else:
                        li = 2
                    if mi == "0":
                        compodata += '[ not_in_leaflet ]\n'
                    else:
                        compodata += '[ membrane_%s_leaflet_%d ]\n' % (mi, li)
                    if mi == "1":
                        for key in sorted(lipsidenumbers[leaflet], key=lipsidenumbers[leaflet].__getitem__, reverse=True):
                            name += '-' + lipsidenames[leaflet][key]
                            compodata += '%10s%10s\n' % (lipsidenames[leaflet][key][1:5], lipsidenames[leaflet][key][5:])
                    elif mi == "0":
                        for key in sorted(lipsidenumbers[leaflet], key=lipsidenumbers[leaflet].__getitem__, reverse=True):
                            name += '-' + lipsidenames[leaflet][key]
                            compodata += '%10s%10s\n' % (lipsidenames[leaflet][key][2:6], lipsidenames[leaflet][key][6:])
                    else:
                        ki = len(mi) + 1
                        for key in sorted(lipsidenumbers[leaflet], key=lipsidenumbers[leaflet].__getitem__, reverse=True):
                            name += '-' + lipsidenames[leaflet][key]
                            compodata += '%10s%10s\n' % (lipsidenames[leaflet][key][ki:ki+4], lipsidenames[leaflet][key][ki+4:])

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
                                comp.append(Composition(membrane=m, lipid=lipid,
                                                        number=100*float(number)/nbsides[side], side=side))
                    try:
                        with transaction.atomic():
                            Composition.objects.filter(membrane=m).delete()
                            Composition.objects.bulk_create(comp)
                            messages.success(request, 'You have updated your composition.')
                    except IntegrityError:
                        messages.error(request, 'There was an error saving your composition.')

                rand = request.POST['rand']
                fname = request.POST['fname']
                mempath = 'media/%s' % mempath
                if rand:
                    if os.path.isfile(mempath):
                        os.remove(mempath)
                    extension = request.POST['extension']
                    mempath = 'media/tmp/%s/%s_sorted%s' % (rand, fname, extension)
                memname = unidecode(mt.name).replace(' ', '_')
                if os.path.isfile(mempath):
                    newmempath = 'media/membranes/LIM{0}_{1}{2}'.format(mt.id, memname, extension)
                    shutil.copy(mempath, newmempath)
                    mt.mem_file = 'membranes/LIM{0}_{1}{2}'.format(mt.id, memname, extension)
                compofile = open('media/membranes/LIM{0}_{1}.txt'.format(mt.id, memname), 'w')
                compofile.write(compodata)
                compofile.close()
                mt.compo_file = 'membranes/LIM{0}_{1}.txt'.format(mt.id, memname)

                mt.search_name = "LIM%d_%s" % (mt.id, memname)

                mt.membrane = m
                mt.save()

                if rand:
                    shutil.rmtree(os.path.join(settings.MEDIA_ROOT, 'tmp', rand), ignore_errors=True)
                if mempath_init != mt.mem_file and os.path.isfile('media/' + mempath_init):
                    os.remove('media/' + mempath_init)
                if otherpath_init != mt.other_file and otherpath_init:
                    os.remove('media/' + otherpath_init)
                if compopath_init != mt.compo_file:
                    os.remove('media/' + compopath_init)
                review_notification("update", "membranes", mt.pk)

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
            file_data, otherpath = FileData(request, 'other_file', 'otherpath', file_data)
            topform = MembraneTopolForm(request.POST, file_data, instance=mt)
            memform = MembraneForm(request.POST, instance=mt.membrane)
            mem_file = file_data['mem_file']
            data = {'form-TOTAL_FORMS': 1,
                    'form-INITIAL_FORMS': '0',
                    'form-MAX_NUM_FORMS': ''}
            if 'forcefield' in topform.data:
                ff = topform.data['forcefield']
                merrors, minfos, data, file_data, rand, fname, extension, mempath, nbmemb = formsetdata(mem_file, ff,
                                                                                                         mempath)
                if file_data != '':
                    topform = MembraneTopolForm(request.POST, file_data)
            formset = MemFormSet(data)
        else:
            mempath = ''
            if mt.mem_file:
                mempath = 'tmp/%s' % os.path.basename(mt.mem_file.name)
                shutil.copy(mt.mem_file.url[1:], 'media/tmp/')
            otherpath = ''
            if mt.other_file:
                otherpath = 'tmp/%s' % os.path.basename(mt.other_file.name)
                shutil.copy(mt.other_file.url[1:], 'media/tmp/')
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
                if lip.side and lip.side != 'UNK':
                    if len(lip.side) == 2:
                        nbs = 1
                    else:
                        nbs = int(lip.side[2:])
                    if nbs > nbmemb:
                        nbmemb = nbs
            formset = MemFormSet(data)
        return render(request, 'membranes/mem_form.html',
                      {'topform': topform, 'memform': memform, 'formset': formset, 'tops': Topology.objects.all(),
                       'membranes': True, 'merrors': merrors, 'minfos': minfos, 'rand': rand, 'fname': fname,
                       'extension': extension, 'mempath': mempath, 'otherpath': otherpath, 'nbmemb': nbmemb})
    else:
        return HttpResponseRedirect(reverse('memlist'))


@never_cache
def MemDetail(request, pk=None):
    if MembraneTopol.objects.filter(pk=pk).exists():
        membrane = MembraneTopol.objects.get(pk=pk)
        if membrane.forcefield.forcefield_type == 'CG':
            representation = 'spacefill'
        else:
            representation = 'licorice'
        mem_file = ''
        if membrane.mem_file:
            mem_file = membrane.mem_file.url
        other_file = ''
        other_filelist = []
        if membrane.other_file:
            other_file = membrane.other_file.url
            with zipfile.ZipFile(other_file[1:], 'r') as zipObj:
                # Get list of files names in zip
                other_filelist = zipObj.namelist()
        nblip = nb_lip_per_leaflet(membrane)
        prop = ''
        nb = LI_Property.objects.filter(membranetopol=pk).count()
        if nb >= 1:
            prop = list(LI_Property.objects.filter(membranetopol=pk).values_list('id', flat=True))
            prop = [str(i) for i in prop]
            prop = ','.join(prop)
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
                                    '\n\n%s %s has published the ' % (comment.user.first_name, comment.user.last_name),
                                    'following comment on %s.\n\n' % (comment.date.strftime("%b. %d, %Y at %H:%M")),
                                    '%s\n\nSincerely,\nThe Limonada Team' % (comment.comment)))
                    send_mail(subject, text, settings.DEFAULT_FROM_EMAIL, [email, ])
                form = MemCommentForm()
        else:
            form = MemCommentForm()
        comments = MemComment.objects.filter(membrane=membrane)
        return render(request, 'membranes/mem_detail.html',
                      {'membranetopol': membrane, 'comments': comments, 'form': form, 'mem_file': mem_file,
                       'other_file': other_file, 'other_filelist': other_filelist, 'rep': representation,
                       'nblip': nblip, 'prop': prop, 'membranes': True})


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


class MembraneTopolAutocomplete(autocomplete.Select2QuerySetView):

    def get_queryset(self):
        qs = MembraneTopol.objects.all()
        if self.q:
            qs = qs.filter(search_name__icontains=self.q)
        return qs


class MembraneAutocomplete(autocomplete.Select2QuerySetView):

    def get_queryset(self):
        qs = Membrane.objects.all()
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        return qs


def GetLipTops(request):
    lipid_id = request.GET['lip']
    ff_id = request.GET['ff']
    soft_id = request.GET['soft']
    ff_list = []
    if soft_id:
        softabb = Software.objects.filter(id=soft_id).values_list('abbreviation', flat=True)[0]
        if softabb[:2] == "NA":
            ff_list = Forcefield.objects.all().values_list('id', flat=True)
        else:
            ff_list = Forcefield.objects.filter(software=Software.objects.filter(id=soft_id)[0]).values_list('id',
                                                                                                          flat=True)
        if not ff_id:
            ff_id = ff_list[0]
        elif int(ff_id) not in list(ff_list):
            ff_id = ff_list[0]

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
                memname = unidecode(mem.name).replace(' ', '_')

                mediadir = settings.MEDIA_ROOT
                rand = str(random.randrange(1000))
                while os.path.isdir(os.path.join(mediadir, 'tmp', rand)):
                    rand = str(random.randrange(1000))
                dirname = os.path.join(mediadir, 'tmp', rand, memname)
                os.makedirs(dirname)
                topdir = os.path.join(dirname, 'toppar')
                os.makedirs(topdir)

                ffzip = zipfile.ZipFile(mem.forcefield.ff_file.url[1:])
                ffdir = ffzip.namelist()[0]
                ffzip.extractall(dirname)

                if mem.forcefield.mdp_file:
                    mdpzip = zipfile.ZipFile(mem.forcefield.mdp_file.url[1:])
                    mdpzip.extractall(dirname)

                if mem.other_file:
                    otherzip = zipfile.ZipFile(mem.other_file.url[1:])
                    otherzip.extractall(dirname)

                soft = mem.forcefield.software.all()[0].name
                if soft == "Gromacs":
                    topfile = open(os.path.join(dirname, 'topol.top'), 'w')
                    topfile.write('\n; Include forcefield parameters\n')
                    topfile.write('#include "%sforcefield.itp"\n\n' % ffdir)
                else:
                    topfile = open(os.path.join(dirname, 'topol.txt'), 'w')

                memresidues = []
                othermol = {}
                residues = []
                if mem.mem_file:
                    shutil.copy(mem.mem_file.url[1:], dirname)
                    memresidues, lipresidues, othermol, residues, headers = membrane_residues(mem.mem_file.name, mem.forcefield)
                    extension = os.path.splitext(mem.mem_file.name)[1]
                else:
                    grodir = os.path.join(dirname, 'lipids')
                    os.makedirs(grodir)

                if soft == "Gromacs":
                    for moltype in ['Protein', 'DNA', 'RNA']:
                        if moltype in othermol.keys():
                            topfile.write('; Include topology for %s\n' % moltype)
                            topfile.write('#include "%s.itp"\n\n' % moltype)

                    topfile.write('; Include topology for lipids\n')

                tops = {}
                topolcompo = []
                fifthdigit = False
                for lip in mem.topolcomposition_set.all():
                    if lip.topology.id not in tops.keys():
                        lipname = lip.lipid.name
                        i = 0
                        while lipname in tops.values():
                            lipname = '%s%s' % (lip.lipid.name, abc[i:i+1])
                            i += 1
                            fifthdigit = True
                        tops[lip.topology.id] = lipname
                        if soft == "Gromacs":
                            topfile.write('#include "toppar/%s.itp"\n' % lipname)
                    lipname = tops[lip.topology.id]
                    topolcompo.append([lipname, lip.number])
                    if lipname == lip.lipid.name:
                        shutil.copy(lip.topology.itp_file.url[1:], topdir)
                        if not mem.mem_file:
                            shutil.copy(lip.topology.gro_file.url[1:], grodir)
                    else:
                        infile = codecs.open(lip.topology.itp_file.url[1:], 'r', encoding='utf-8')
                        extension = os.path.splitext(lip.topology.itp_file.name)[1]
                        filedata = infile.read()
                        infile.close()
                        newdata = filedata.replace(' %s' % lip.lipid.name, lipname)
                        newdata2 = newdata.replace('%s ' % lip.lipid.name, lipname)
                        outfile = codecs.open('%s%s' % (os.path.join(topdir, lipname), extension),
                                              'w', encoding='utf-8')
                        outfile.write(newdata2)
                        outfile.close()
                        if not mem.mem_file:
                            infile = codecs.open(lip.topology.gro_file.url[1:], 'r', encoding='utf-8')
                            extension = os.path.splitext(lip.topology.gro_file.name)[1]
                            filedata = infile.read()
                            infile.close()
                            newdata = filedata.replace('%s ' % lip.lipid.name, lipname)
                            outfile = codecs.open('%s%s' % (os.path.join(grodir, lipname), extension),
                                                  'w', encoding='utf-8')
                            outfile.write(newdata)
                            outfile.close()

                # creation of the membrane file with the fifth digit 
                memcompo = copy.deepcopy(topolcompo)
                if mem.mem_file and fifthdigit == True:
                    if soft == "Gromacs":
                        memname2 = "%s_extended.gro" % os.path.splitext(os.path.basename(mem.mem_file.name))[0]
                        memfile2 = codecs.open(os.path.join(dirname, memname2), 'w', encoding='utf-8')
                        memfile2.write(headers[0])
                        memfile2.write(headers[1])
                        i = 0
                        resrename = True
                        while resrename == True and i < len(residues):
                            lipname = residues[i][0][0]
                            if lipname == memcompo[0][0][0:4]:
                                lipname = memcompo[0][0]
                                memcompo[0][1] -= 1
                                if memcompo[0][1] == 0:
                                   memcompo.pop(0)
                                   if len(memcompo) == 0:
                                       resrename = False
                            for atom in residues[i]:
                                if lipname[0:4] == atom[0]:
                                    memfile2.write('%5d%-5s%5s%5d%s' % (atom[2], lipname, atom[1], atom[3], atom[4]))
                                else:
                                    memfile2.write('%5d%-5s%5s%5d%s' % (atom[2], atom[0], atom[1], atom[3], atom[4]))
                            i += 1
                        while i < len(residues):
                            for atom in residues[i]:
                                memfile2.write('%5d%-5s%5s%5d%s' % (atom[2], atom[0], atom[1], atom[3], atom[4]))
                            i += 1
                        memfile2.write(headers[2])
                        memfile2.close() 
                    elif soft == "Charmm":
                        memname2 = "%s_extended.crd" % os.path.splitext(os.path.basename(mem.mem_file.name))[0]
                        memfile2 = codecs.open(os.path.join(dirname, memname2), 'w', encoding='utf-8')
                        memfile2.write("%10d  EXT\n" % len(residues))
                        i = 0
                        resrename = True
                        while resrename == True and i < len(residues):
                            lipname = residues[i][0][0]
                            if lipname == memcompo[0][0][0:4]:
                                lipname = memcompo[0][0]
                                memcompo[0][1] -= 1
                                if memcompo[0][1] == 0:
                                   memcompo.pop(0)
                                   if len(memcompo) == 0:
                                       resrename = False
                            for atom in residues[i]:
                                coord = atom[4].split()
                                memfile2.write('%10d%10d  %-8s  %-8s%20.10f%20.10f%20.10f  MEMB      %-8s        0.0000000000\n'
                                    % (atom[3], atom[2], lipname, atom[1], float(coord[0]), 
                                    float(coord[2]), float(coord[2]), str(atom[2])))
                            i += 1
                        while i < len(residues):
                            for atom in residues[i]:
                                memfile2.write('%10d%10d  %-8s  %-8s%20.10f%20.10f%20.10f  MEMB      %-8s        0.0000000000\n'
                                    % (atom[3], atom[2], atom[0], atom[1], float(coord[0]),
                                    float(coord[2]), float(coord[2]), str(atom[2])))
                            i += 1
                        memfile2.close() 
                    
                if soft == "Gromacs":
                    if 'Water' in othermol.keys() and os.path.isfile(os.path.join(dirname, ffdir, 'watermodels.dat')):
                        water = ''
                        for line in open(os.path.join(dirname, ffdir, 'watermodels.dat')):
                            if re.search(r'recommended', line):
                                water = line.split()[0]
                        if water:
                            if os.path.isfile(os.path.join(dirname, ffdir, '%s.itp' % water)):
                                topfile.write('\n; Include topology for water\n')
                                topfile.write('#include "%s%s.itp"' % (ffdir, water))
                    if 'Ion' in othermol.keys() and os.path.isfile(os.path.join(dirname, ffdir, 'ions.itp')):
                        topfile.write('\n; Include topology for ions\n')
                        topfile.write('#include "%sions.itp"\n' % ffdir)

                topfile.write('\n[ system ]\n')
                topfile.write('%s\n\n' % mem.name)
                topfile.write('[ molecules ]\n')
                if mem.mem_file:
                    for mol in memresidues:
                        if mol[2] != 'lipid':
                            topfile.write('%-6s%10s\n' % (mol[0], mol[1]))
                        else:
                            nbmol = int(mol[1])
                            i = 0
                            while i < nbmol:
                                mol = topolcompo.pop(0)
                                topfile.write('%-6s%10s\n' % (mol[0], mol[1]))
                                i += mol[1]
                else:
                    for mol in topolcompo:
                        topfile.write('%-6s%10s\n' % (mol[0], mol[1]))
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


class MembraneProtAutocomplete(autocomplete.Select2QuerySetView):

    def get_queryset(self):
        qs = MembraneProt.objects.all().order_by('prot')
        if self.q:
            qs = qs.filter(prot__icontains=self.q)
        return qs


class MembraneDoiAutocomplete(autocomplete.Select2QuerySetView):

    def get_queryset(self):
        qs = MembraneDoi.objects.none()
        return qs


class MembraneTagAutocomplete(autocomplete.Select2QuerySetView):

    def get_queryset(self):
        qs = MembraneTag.objects.all().order_by('tag')
        if self.q:
            qs = qs.filter(tag__icontains=self.q)
        return qs
