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
import shlex
import shutil
import subprocess

# third-party
import requests
import simplejson
from dal import autocomplete

# Django
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.mail import send_mail
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.urls import reverse
from django.db.models import Q
from django.db.models.functions import Substr
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.utils.text import slugify
from django.views.decorators.cache import never_cache
from django.views.generic import DetailView

# Django apps
from forcefields.models import Forcefield, Software
from limonada.functions import FileData
from membranes.models import Membrane, MembraneTopol

# local Django
from .forms import TopCommentForm, LipidForm, LmidForm, SelectLipidForm, SelectTopologyForm, TopologyForm
from .functions import findcgbonds
from .models import TopComment, Lipid, Topology


def molsize(filename):
    mol = open('%s.mol' % filename).readlines()
    rotmol = open('%s_rot.mol' % filename, 'w')
    for j in range(0, 4):
        rotmol.write(mol[j])
    X = []
    Y = []
    nb = int(mol[3][0:3])
    for j in range(4, nb+4):
        X.append(float(mol[j].split()[0]))
        Y.append(float(mol[j].split()[1]))
        rotmol.write('%10.4f%s %s' % (-float(mol[j][11:20]), mol[j][0:10], mol[j][21:]))
    for line in mol[j+1:]:
        rotmol.write('%s' % line)
    rotmol.close()
    R = (max(Y)-min(Y)) / (max(X)-min(X))
    return R


def lm_class():
    lm_dict = {}
    lm_class = {'category': []}
    for line in open('media/Lipid_Classification').readlines():
        name = line.split('[')[1].split(']')[0]
        line = line.strip()
        lname = len(name)
        lm_dict[name] = line
        if lname == 2:
            lm_class['category'].append([name, line])
        elif lname == 4:
            if name[0:2] not in lm_class.keys():
                lm_class[name[0:2]] = []
            lm_class[name[0:2]].append([name, line])
        elif lname == 6:
            if name[0:4] not in lm_class.keys():
                lm_class[name[0:4]] = []
            lm_class[name[0:4]].append([name, line])
        elif lname == 8:
            if name[0:6] not in lm_class.keys():
                lm_class[name[0:6]] = []
            lm_class[name[0:6]].append([name, line])
    return lm_class, lm_dict


def GetLmClass(request):
    classname = request.GET['classname']
    lmclass, lmdict = lm_class()
    result_set = []
    if classname in lmclass.keys():
        for option in lmclass[classname]:
            result_set.append({'name': option[0], 'line': option[1]})
    return HttpResponse(simplejson.dumps(result_set), content_type='application/json')


def li_index():
    lmclass, lmdict = lm_class()
    liindex = {}
    liid = []
    if Lipid.objects.filter(lmid__istartswith='LI').exists():
        for i in Lipid.objects.filter(lmid__istartswith='LI').values_list('lmid', flat=True):
            liid.append(i)
    for grp in lmdict.keys():
        if grp not in lmclass.keys():
            lgrp = len(grp)
            if lgrp == 4:
                liindex[grp] = 'LI%s00%04d' % (grp, 1)
            else:
                liindex[grp] = 'LI%s%04d' % (grp, 1)
            for lipid in liid:
                if lipid[2:lgrp+2] == grp:
                    if int(liindex[grp][lgrp+2:]) <= int(lipid[lgrp+2:]):
                        if lgrp == 4:
                            liindex[grp] = 'LI%s00%04d' % (grp, int(lipid[lgrp+2:])+1)
                        else:
                            liindex[grp] = 'LI%s%04d' % (grp, int(lipid[lgrp+2:])+1)
    return liindex


def GetLiIndex(request):
    data = {}
    liindex = li_index()
    for i in ['mainclass', 'subclass', 'l4class']:
        classname = request.GET[i]
        if classname in liindex.keys():
            data[i] = liindex[classname]
        else:
            data[i] = ""
    return HttpResponse(simplejson.dumps(data), content_type='application/json')


def GetSoftVersionList(request):
    software = simplejson.loads(request.POST.get('software', None))
    version_list = []
    if software != "":
        version_list = Software.objects.filter(abbreviation__istartswith=software).order_by('order')
    data = []
    for version in version_list:
        data.append({'value': version.id, 'version': version.version})
    return HttpResponse(simplejson.dumps(data), content_type='application/json')


def GetFfList(request):
    software = simplejson.loads(request.POST.get('software', None))
    softlist = simplejson.loads(request.POST.get('version', None))
    if not softlist:
        softlist = []
    elif type(softlist) is str:
        softlist = softlist.split(",")
    op = request.POST.get('operator', None)
    ff_list = Forcefield.objects.all()
    if op == 'AND':
        software = Software.objects.filter(id=softlist[0]).values_list('abbreviation', flat=True)[0][:2]
    else:
        if software == "NA":
            softlist = Software.objects.all().values_list('id', flat=True)
        elif software != "" and not softlist:
            softlist = Software.objects.filter(abbreviation__istartswith=software).values_list('id', flat=True)
    if op == 'AND':
        if software == "NA":
            ff_list = Forcefield.objects.all()
        else:
            for i in softlist:
                ff_list = ff_list.filter(software=Software.objects.filter(id=i)[0])
    else:
        querylist = []
        for i in softlist:
            querylist.append(Q(software=Software.objects.filter(id=i)[0]))
        if querylist:
            ff_list = ff_list.filter(reduce(operator.or_, querylist)).distinct()
    data = []
    if ff_list and softlist:
        for ff in ff_list:
            data.append({'value': ff.id, 'name': ff.name})
    return HttpResponse(simplejson.dumps(data), content_type='application/json')


@never_cache
def LipList(request):

    lmclass, lmdict = lm_class()

    lipid_list = Lipid.objects.annotate(lmid_split=Substr('lmid', 3)).order_by('lmid_split')

    params = request.GET.copy()

    selectparams = {}
    for param in ['category', 'main_class', 'sub_class', 'l4_class', 'lipidid']:
        if param in request.GET.keys():
            if request.GET[param] != '':
                if param == 'lipidid':
                    liplist = request.GET[param].split(',')
                    selectparams['lipidid'] = liplist
                else:
                    selectparams[param] = request.GET[param]
    if 'category' in selectparams.keys():
        lipid_list = lipid_list.filter(core=lmdict[selectparams['category']])
    if 'main_class' in selectparams.keys():
        lipid_list = lipid_list.filter(main_class=lmdict[selectparams['main_class']])
    if 'sub_class' in selectparams.keys():
        lipid_list = lipid_list.filter(sub_class=lmdict[selectparams['sub_class']])
    if 'l4_class' in selectparams.keys():
        lipid_list = lipid_list.filter(l4_class=lmdict[selectparams['l4_class']])
    if 'lipidid' in selectparams.keys():
        form_select = SelectLipidForm({'lipidid': selectparams['lipidid']})
        if form_select.is_valid():
            querylist = []
            for i in liplist:
                querylist.append(Q(id=i))
            lipid_list = lipid_list.filter(reduce(operator.or_, querylist))
    else:
        form_select = SelectLipidForm()

    if 'curator' in request.GET.keys():
        try:
            curator = int(request.GET['curator'])
        except ValidationError:
            curator = 0
        if curator > 0:
            lipid_list = lipid_list.filter(curator=User.objects.filter(id=curator)[0])

    sort = request.GET.get('sort')
    sortdir = request.GET.get('dir')
    lipheaders = ['name', 'lmid', 'com_name', 'sys_name']
    if sort is not None and sort in lipheaders:
        if sort == 'lmid':
            lipid_list = lipid_list.annotate(lmid_split=Substr('lmid', 3)).order_by('lmid_split')
        else:
            lipid_list = lipid_list.order_by(sort)
        if sortdir == 'des':
            lipid_list = lipid_list.reverse()

    per_page = 25
    if 'per_page' in request.GET.keys():
        try:
            per_page = int(request.GET['per_page'])
        except ValidationError:
            per_page = 25
    if per_page not in [10, 25, 100]:
        per_page = 25
    paginator = Paginator(lipid_list, per_page)

    page = request.GET.get('page')
    try:
        lipids = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        lipids = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        lipids = paginator.page(paginator.num_pages)

    data = {}
    data['form_select'] = form_select
    data['page_objects'] = lipids
    data['per_page'] = per_page
    data['sort'] = sort
    if sort is not None and sort in lipheaders:
        data['dir'] = sortdir
    data['lipids'] = True
    data['params'] = params

    return render(request, 'lipids/lipids.html', data)


@login_required
@never_cache
def LipCreate(request):
    imgpath = ''
    if request.method == 'POST' and 'search' in request.POST:
        form_search = LmidForm(request.POST)
        form_add = LipidForm()
        if form_search.is_valid():
            lm_data = {}
            lm_data['lmid'] = form_search.cleaned_data['lmidsearch']
            lm_response = requests.get('http://www.lipidmaps.org/rest/compound/lm_id/%s/all/json' % lm_data['lmid'])
            if 'lm_id' in lm_response.json().keys():
                lm_data_raw = lm_response.json()
            elif 'Row1' in lm_response.json().keys():
                lm_data_raw = lm_response.json()['Row1']
            for key in ['pubchem_cid', 'name', 'sys_name', 'formula', 'abbrev_chains']:
                if key == 'name' and 'name' in lm_data_raw.keys():
                    lm_data['com_name'] = lm_data_raw[key]
                elif key in lm_data_raw.keys():
                    lm_data[key] = lm_data_raw[key]
            filename = 'media/tmp/%s' % lm_data['lmid']
            url = 'http://www.lipidmaps.org/data/LMSDRecord.php?Mode=File&LMID=%s' % lm_data['lmid']
            response = requests.get(url)
            with open('%s.mol' % filename, 'wb') as f:
                f.write(response.content)
            f.close()
            R = molsize(filename)
            if R < 1:
                shutil.copy('%s_rot.mol' % filename, '%s.mol' % filename)
            try:
                args = shlex.split(
                    'obabel %s.mol -O %s.png -xC -xh 1200 -xw 1000 -x0 molfile -xd --title' % (filename, filename))
                process = subprocess.Popen(args, stdout=subprocess.PIPE)
                process.communicate()
            except OSError:
                pass
            if os.path.isfile('media/tmp/%s.png' % lm_data['lmid']):
                f = open('media/tmp/%s.png' % lm_data['lmid'], "rb")
                file_data = {'img': SimpleUploadedFile(name=f.name, content=f.read(), content_type="image/png")}
                imgpath = 'tmp/%s.png' % lm_data['lmid']
            else:
                file_data = {}
                imgpath = ''

            if os.path.isfile('%s_rot.mol' % filename):
                os.remove('%s_rot.mol' % filename)
            if os.path.isfile('%s.mol' % filename):
                os.remove('%s.mol' % filename)
            if 'pubchem_cid' in lm_data.keys():
                if lm_data['pubchem_cid'] != '':
                    try:
                        pubchem_response = requests.get(
                            'https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/%s/JSON/'
                            % lm_data['pubchem_cid'])
                        pubchem_data_raw = pubchem_response.json()['Record']
                        if pubchem_data_raw != []:
                            for s1 in pubchem_data_raw['Section']:
                                if s1['TOCHeading'] == 'Names and Identifiers':
                                    for s2 in s1['Section']:
                                        if s2['TOCHeading'] == 'Computed Descriptors':
                                            for s3 in s2['Section']:
                                                if s3['TOCHeading'] == 'IUPAC Name':
                                                    lm_data['iupac_name'] = s3['Information'][0]['StringValue']
                                        if s2['TOCHeading'] == 'Synonyms':
                                            for s3 in s2['Section']:
                                                if s3['TOCHeading'] == 'Depositor-Supplied Synonyms':
                                                    key1 = 'Information'
                                                    key2 = 'StringValueList'
                                                    nb = len(s3[key1][0][key2])
                                                    for i in range(nb):
                                                        if len(s3[key1][0][key2][nb-1-i]) == 4:
                                                            lm_data['name'] = s3[key1][0][key2][nb-1-i]
                    except KeyError:
                        pass
            form_add = LipidForm(lm_data, file_data)
            return render(request, 'lipids/lip_form.html', {
                'form_search': form_search, 'form_add': form_add, 'lipids': True, 'search': True, 'imgpath': imgpath})
    elif request.method == 'POST' and 'add' in request.POST:
        lmclass, lmdict = lm_class()
        form_search = LmidForm()
        file_data = {}
        file_data, imgpath = FileData(request, 'img', 'imgpath', file_data)
        form_add = LipidForm(request.POST, file_data)
        if form_add.is_valid():
            lipid = form_add.save(commit=False)
            name = form_add.cleaned_data['name']
            lmid = form_add.cleaned_data['lmid']
            com_name = form_add.cleaned_data['com_name']
            lipid.search_name = '%s - %s - %s' % (name, lmid, com_name)
            core = form_add.cleaned_data['core']
            main_class = form_add.cleaned_data['main_class']
            sub_class = form_add.cleaned_data['sub_class']
            l4_class = form_add.cleaned_data['l4_class']
            lipid.core = lmdict[core]
            lipid.main_class = lmdict[main_class]
            if sub_class != '':
                lipid.sub_class = lmdict[sub_class]
            if l4_class != '':
                lipid.l4_class = lmdict[l4_class]
            lipid.slug = slugify('%s' % (lmid), allow_unicode=True)
            lipid.curator = request.user
            lipid.save()
            if os.path.isfile("media/" + imgpath):
                os.remove("media/" + imgpath)
            return HttpResponseRedirect(reverse('liplist'))
    else:
        form_search = LmidForm()
        form_add = LipidForm()
    return render(request, 'lipids/lip_form.html', {
        'form_search': form_search, 'form_add': form_add, 'lipids': True, 'search': True, 'imgpath': imgpath})


@login_required
@never_cache
def LipUpdate(request, slug=None):
    if Lipid.objects.filter(slug=slug).exists():
        lipid = Lipid.objects.get(slug=slug)
        if lipid.curator != request.user:
            return redirect('homepage')
        if request.method == 'POST':
            file_data = {}
            file_data, imgpath = FileData(request, 'img', 'imgpath', file_data)
            form_add = LipidForm(request.POST, file_data, instance=lipid)
            if form_add.is_valid():
                lipid = form_add.save(commit=False)
                name = form_add.cleaned_data['name']
                lmid = form_add.cleaned_data['lmid']
                com_name = form_add.cleaned_data['com_name']
                lipid.search_name = '%s - %s - %s' % (name, lmid, com_name)
                lipid.slug = slugify('%s' % (lmid), allow_unicode=True)
                lipid.save()
                if imgpath != '' and os.path.isfile("media/" + imgpath):
                    os.remove("media/" + imgpath)
                return HttpResponseRedirect(reverse('liplist'))
        else:
            imgpath = ''
            if lipid.img:
                imgpath = 'tmp/%s' % os.path.basename(lipid.img.name)
                shutil.copy(lipid.img.url[1:], 'media/tmp/')
            form_add = LipidForm(instance=lipid)
        return render(request, 'lipids/lip_form.html',
                      {'form_add': form_add, 'lipids': True, 'search': False, 'imgpath': imgpath})
    else:
        return HttpResponseRedirect(reverse('liplist'))


class LipDetail(DetailView):
    model = Lipid
    template_name = 'lipids/lip_detail.html'

    def get_context_data(self, **kwargs):
        slug = self.kwargs['slug']
        context_data = super(LipDetail, self).get_context_data(**kwargs)
        context_data['lipids'] = True
        context_data['tops'] = Topology.objects.filter(lipid=Lipid.objects.get(slug=slug))
        return context_data


@login_required
def LipDelete(request, slug=None):
    if Lipid.objects.filter(slug=slug).exists():
        lip = Lipid.objects.get(slug=slug)
        if lip.curator != request.user:
            return redirect('homepage')
        mt = MembraneTopol.objects.filter(lipids=lip).distinct()
        top = Topology.objects.filter(lipid=lip).distinct()
        curator = True
        for obj in mt:
            if obj.curator != request.user:
                curator = False
        for obj in top:
            if obj.curator != request.user:
                curator = False
        if curator:
            if request.method == 'POST':
                lip.delete()
                for obj in mt:
                    m = obj.membrane
                    obj.delete()
                    if not MembraneTopol.objects.filter(membrane=m).count():
                        m.delete()
                for obj in top:
                    obj.delete()
                return HttpResponseRedirect(reverse('liplist'))
            return render(request, 'lipids/lip_delete.html',
                          {'lipids': True, 'lip': lip, 'nbtop': len(top), 'nbmem': len(mt)})
        return render(request, 'lipids/lip_notdelete.html',
                      {'lipids': True, 'lip': lip, 'nbtop': len(top), 'nbmem': len(mt)})


class LipAutocomplete(autocomplete.Select2QuerySetView):

    def get_queryset(self):
        qs = Lipid.objects.all().order_by('name')
        if self.q:
            qs = qs.filter(search_name__icontains=self.q)
        return qs


@never_cache
def TopList(request):

    lmclass, lmdict = lm_class()

    top_list = Topology.objects.all().order_by('forcefield', 'lipid__lmid')

    params = request.GET.copy()

    selectparams = {}
    selectclass = {}
    for param in ['software', 'softversion', 'forcefield', 'lipid', 'category', 'main_class', 'sub_class', 'l4_class']:
        if param in request.GET.keys():
            if request.GET[param] != '':
                if param == 'lipid':
                    liplist = request.GET[param].split(',')
                    selectparams['lipid'] = liplist
                elif param == 'software':
                    selectparams[param] = request.GET[param]
                elif param == 'softversion':
                    selectparams[param] = request.GET[param]
                elif param == 'forcefield':
                    selectparams[param] = request.GET[param]
                else:
                    selectclass[param] = request.GET[param]
    form_select = SelectTopologyForm(selectparams)
    if form_select.is_valid():
        if 'software' in selectparams.keys():
            softlist = Software.objects.filter(
                abbreviation__istartswith=selectparams['software']).values_list('id', flat=True)
            if softlist:
                querylist = []
                for i in softlist:
                    querylist.append(Q(software=Software.objects.filter(id=i)[0]))
                top_list = top_list.filter(reduce(operator.or_, querylist)).distinct()
            else:
                top_list = Topology.objects.none()
        if 'softversion' in selectparams.keys():
            top_list = top_list.filter(software=Software.objects.filter(id=selectparams['softversion'])[0])
        if 'forcefield' in selectparams.keys():
            top_list = top_list.filter(forcefield=Forcefield.objects.filter(id=selectparams['forcefield'])[0])
        if 'category' in selectclass.keys():
            top_list = top_list.filter(lipid__core=lmdict[selectclass['category']])
        if 'main_class' in selectclass.keys():
            top_list = top_list.filter(lipid__main_class=lmdict[selectclass['main_class']])
        if 'sub_class' in selectclass.keys():
            top_list = top_list.filter(lipid__sub_class=lmdict[selectclass['sub_class']])
        if 'l4_class' in selectclass.keys():
            top_list = top_list.filter(lipid__l4_class=lmdict[selectclass['l4_class']])
        if 'lipid' in selectparams.keys():
            querylist = []
            for i in liplist:
                querylist.append(Q(lipid=Lipid.objects.filter(id=i)[0]))
            top_list = top_list.filter(reduce(operator.or_, querylist))

    if 'topid' in request.GET.keys():
        try:
            topid = int(request.GET['topid'])
        except ValidationError:
            topid = 0
        if topid > 0:
            top_list = top_list.filter(id=topid)

    if 'curator' in request.GET.keys():
        try:
            curator = int(request.GET['curator'])
        except ValidationError:
            curator = 0
        if curator > 0:
            top_list = top_list.filter(curator=User.objects.filter(id=curator)[0])

    sort = request.GET.get('sort')
    sortdir = request.GET.get('dir')
    topheaders = ['version', 'forcefield', 'lipid']
    if sort is not None and sort in topheaders:
        if sort == 'forcefield':
            top_list = top_list.order_by('forcefield__name')
        elif sort == 'lipid':
            top_list = top_list.order_by('lipid__name')
        else:
            top_list = top_list.order_by(sort)
        if sortdir == 'des':
            top_list = top_list.reverse()

    per_page = 25
    if 'per_page' in request.GET.keys():
        try:
            per_page = int(request.GET['per_page'])
        except ValidationError:
            per_page = 25
    if per_page not in [10, 25, 100]:
        per_page = 25
    paginator = Paginator(top_list, per_page)

    page = request.GET.get('page')
    try:
        topologies = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        topologies = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        topologies = paginator.page(paginator.num_pages)

    data = {}
    data['form_select'] = form_select
    data['page_objects'] = topologies
    data['per_page'] = per_page
    data['sort'] = sort
    if sort is not None and sort in topheaders:
        data['dir'] = sortdir
    data['topologies'] = True
    data['params'] = params
    data['memtops'] = MembraneTopol.objects.all()
    data['mems'] = Membrane.objects.all()

    return render(request, 'lipids/topologies.html', data)


@never_cache
def TopDetail(request, pk=None):
    if Topology.objects.filter(pk=pk).exists():
        topology = Topology.objects.get(pk=pk)
        bonds = []
        if topology.forcefield.forcefield_type == 'CG':
            bonds = findcgbonds(topology.itp_file.url)
        if request.method == 'POST':
            form = TopCommentForm(request.POST)
            if form.is_valid():
                comment = form.save(commit=False)
                comment.topology = topology
                comment.user = request.user
                comment.save()
                if request.user != topology.curator:
                    email = request.user.email
                    subject = 'New comment on your Limonada entry %s_%s' % (topology.lipid.name, topology.version)
                    message = ''.join(
                        ('Dear Mr/Ms %s %s,' % (topology.curator.first_name, topology.curator.last_name),
                         '\n\n%s %s has published ' % (comment.user.first_name, comment.user.last_name),
                         'the following comment on %s.\n\n' % (comment.date.strftime("%b. %d, %Y at %H:%M")),
                         '%s\n\nSincerely,\nThe Limonada Team' % (comment.comment)))
                    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email, ])
                form = TopCommentForm()
        else:
            form = TopCommentForm()
        comments = TopComment.objects.filter(topology=topology)
        return render(request, 'lipids/top_detail.html',
                      {'topology': topology, 'comments': comments, 'form': form, 'cgbonds': bonds, 'topologies': True})


@login_required
@never_cache
def TopCreate(request):
    itppath = ''
    gropath = ''
    if request.method == 'POST':
        file_data = {}
        file_data, itppath = FileData(request, 'itp_file', 'itppath', file_data)
        file_data, gropath = FileData(request, 'gro_file', 'gropath', file_data)
        form = TopologyForm(request.POST, file_data)
        if form.is_valid():
            top = form.save(commit=False)
            top.curator = request.user
            top.save()
            softwares = form.cleaned_data['software']
            for soft in softwares:
                top.software.add(soft)
            refs = form.cleaned_data['reference']
            for ref in refs:
                top.reference.add(ref)
            top.save()
            if os.path.isfile('media/' + itppath):
                os.remove('media/' + itppath)
            if os.path.isfile('media/' + gropath):
                os.remove('media/' + gropath)
            return HttpResponseRedirect(reverse('toplist'))
    else:
        form = TopologyForm()
    return render(request, 'lipids/top_form.html',
                  {'form': form, 'topologies': True, 'topcreate': True, 'itppath': itppath, 'gropath': gropath})


@login_required
@never_cache
def TopUpdate(request, pk=None):
    if Topology.objects.filter(pk=pk).exists():
        top = Topology.objects.get(pk=pk)
        version_init = top.version
        software_init = top.software.all()[0].name
        forcefield_init = top.forcefield
        dir_init = 'media/topologies/%s/%s/%s/%s' % (top.software.all()[0].name, top.forcefield, top.lipid.name,
                                                     top.version)
        if top.curator != request.user:
            return redirect('homepage')
        if request.method == 'POST':
            file_data = {}
            file_data, itppath = FileData(request, 'itp_file', 'itppath', file_data)
            file_data, gropath = FileData(request, 'gro_file', 'gropath', file_data)
            form = TopologyForm(request.POST, file_data, instance=top)
            if form.is_valid():
                top = form.save(commit=False)
                top.software.clear()
                softwares = form.cleaned_data['software']
                for soft in softwares:
                    top.software.add(soft)
                top.reference.clear()
                refs = form.cleaned_data['reference']
                for ref in refs:
                    top.reference.add(ref)
                top.save()
                if os.path.isfile('media/' + itppath):
                    os.remove('media/' + itppath)
                if os.path.isfile('media/' + gropath):
                    os.remove('media/' + gropath)
                if version_init != top.version or software_init != top.software.all()[0].name or forcefield_init != top.forcefield:
                    if os.path.isdir(dir_init):
                        shutil.rmtree(dir_init, ignore_errors=True)
                return HttpResponseRedirect(reverse('toplist'))
        else:
            itppath = 'tmp/%s' % os.path.basename(top.itp_file.name)
            shutil.copy(top.itp_file.url[1:], 'media/tmp/')
            gropath = 'tmp/%s' % os.path.basename(top.gro_file.name)
            shutil.copy(top.gro_file.url[1:], 'media/tmp/')
            form = TopologyForm(instance=top)
        return render(request, 'lipids/top_form.html',
                      {'form': form, 'topologies': True, 'itppath': itppath, 'gropath': gropath})
    else:
        return HttpResponseRedirect(reverse('toplist'))


@login_required
def TopDelete(request, pk=None):
    if Topology.objects.filter(pk=pk).exists():
        top = Topology.objects.get(pk=pk)
        if top.curator != request.user:
            return redirect('homepage')
        mt = MembraneTopol.objects.filter(topolcomposition__topology=top).distinct()
        comments = TopComment.objects.filter(topology=top)
        curator = True
        for obj in mt:
            if obj.curator != request.user:
                curator = False
        if curator:
            if request.method == 'POST':
                top.delete()
                for obj in mt:
                    m = obj.membrane
                    obj.delete()
                    if not MembraneTopol.objects.filter(membrane=m).count():
                        m.delete()
                for obj in comments:
                    obj.delete()
                return HttpResponseRedirect(reverse('toplist'))
            return render(request, 'lipids/top_delete.html', {'topologies': True, 'top': top, 'nbmem': len(mt)})
        return render(request, 'lipids/top_notdelete.html', {'topologies': True, 'top': top, 'nbmem': len(mt)})


class TopAutocomplete(autocomplete.Select2QuerySetView):

    def get_queryset(self):
        qs = Topology.objects.all()
        if self.q:
            qs = qs.filter(version__icontains=self.q)
        return qs
