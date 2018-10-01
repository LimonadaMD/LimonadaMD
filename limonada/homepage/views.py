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

# third-party
import requests
from dal import autocomplete

# Django
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.views.generic import DeleteView

# Django apps
from forcefields.models import Forcefield
from lipids.models import Lipid, Topology
from membranes.models import MembraneTopol

# local Django
from .forms import DoiForm, MailForm, ReferenceForm, SelectForm
from .models import Reference


def homepage(request):

    data = {'homepage': True}
    return render(request, 'homepage/index.html', data)


headers = {'refid': 'asc',
           'title': 'asc',
           'year': 'asc'}


def RefList(request):

    ref_list = Reference.objects.all()

    params = request.GET.copy()

    form_select = SelectForm()
    if 'year' in request.GET.keys():
        year = request.GET['year']
        if year != '':
            form_select = SelectForm({'year': year})
            if form_select.is_valid():
                ref_list = Reference.objects.filter(year=year)

    sort = request.GET.get('sort')
    if sort is not None:
        ref_list = ref_list.order_by(sort)
        if headers[sort] == 'des':
            ref_list = ref_list.reverse()
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
    paginator = Paginator(ref_list, per_page)

    page = request.GET.get('page')
    try:
        refs = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        refs = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        refs = paginator.page(paginator.num_pages)

    data = {}
    data['form_select'] = form_select
    data['page_objects'] = refs
    data['per_page'] = per_page
    data['sort'] = sort
    if sort is not None:
        data['dir'] = headers[sort]
    data['references'] = True
    data['params'] = params

    return render(request, 'homepage/references.html', data)


@login_required
def RefCreate(request):
    if request.method == 'POST' and 'search' in request.POST:
        form_search = DoiForm(request.POST)
        form_add = ReferenceForm()
        if form_search.is_valid():
            doi = form_search.cleaned_data['doisearch']
            url = 'http://dx.doi.org/%s' % doi
            headers = {'Accept': 'application/citeproc+json'}
            doidata = {}
            response = requests.get(url, headers=headers)
            doidata_raw = response.json()
            if doidata_raw != []:
                if 'author' in doidata_raw.keys():
                    text = ''
                    for author in doidata_raw['author']:
                        text += '%s %s, ' % (author['family'], author['given'])
                    doidata['authors'] = text[0:-2]
                if 'title' in doidata_raw.keys():
                    doidata['title'] = doidata_raw['title']
                if 'container-title' in doidata_raw.keys():
                    doidata['journal'] = doidata_raw['container-title']
                if 'volume' in doidata_raw.keys():
                    doidata['volume'] = doidata_raw['volume']
                if 'DOI' in doidata_raw.keys():
                    doidata['doi'] = doidata_raw['DOI']
                if 'created' in doidata_raw.keys():
                    if 'date-parts' in doidata_raw['created'].keys():
                        doidata['year'] = doidata_raw['created']['date-parts'][0][0]
            if 'authors' in doidata.keys() and 'year' in doidata.keys():
                doidata['refid'] = '%s%s' % (doidata['authors'].split()[0], doidata['year'])
            form_add = ReferenceForm(initial=doidata)
            return render(request, 'homepage/ref_form.html',
                          {'form_search': form_search, 'form_add': form_add, 'references': True, 'search': True})
    elif request.method == 'POST' and 'add' in request.POST:
        form_search = DoiForm()
        form_add = ReferenceForm(request.POST)
        if form_add.is_valid():
            ref = form_add.save(commit=False)
            ref.curator = request.user
            ref.save()
            return HttpResponseRedirect(reverse('reflist'))
    else:
        form_search = DoiForm()
        form_add = ReferenceForm()
    return render(request, 'homepage/ref_form.html',
                  {'form_search': form_search, 'form_add': form_add, 'references': True, 'search': True})


@login_required
def RefUpdate(request, pk=None):
    if Reference.objects.filter(pk=pk).exists():
        ref = Reference.objects.get(pk=pk)
        if request.method == 'POST':
            form_add = ReferenceForm(request.POST, instance=ref)
            if form_add.is_valid():
                ref.refid = form_add.cleaned_data['refid']
                ref.authors = form_add.cleaned_data['authors']
                ref.title = form_add.cleaned_data['title']
                ref.journal = form_add.cleaned_data['journal']
                ref.volume = form_add.cleaned_data['volume']
                ref.year = form_add.cleaned_data['year']
                ref.doi = form_add.cleaned_data['doi']
                ref.save()
                return HttpResponseRedirect(reverse('reflist'))
        else:
            form_add = ReferenceForm(instance=ref)
        return render(request, 'homepage/ref_form.html', {'form_add': form_add, 'references': True, 'search': False})
    else:
        return HttpResponseRedirect(reverse('reflist'))


class RefDelete(DeleteView):
    model = Reference
    template_name = 'homepage/ref_delete.html'

    def get_success_url(self):
        return reverse('reflist')

    def get_context_data(self, **kwargs):
        context_data = super(RefDelete, self).get_context_data(**kwargs)
        context_data['references'] = True
        return context_data


class ReferenceAutocomplete(autocomplete.Select2QuerySetView):

    def get_queryset(self):
        qs = Reference.objects.all()
        if self.q:
            qs = qs.filter(refid__icontains=self.q)
        return qs


@login_required
def mail(request):

    params = request.GET.copy()

    name = ''
    obj = ''
    objtype = ''
    objnames = {'lipid': 'lipid', 'topid': 'topology', 'ffid': 'forcefield', 'memid': 'membrane', 'refid': 'reference'}
    for param in ['lipid', 'topid', 'ffid', 'memid', 'refid']:
        if param in request.GET.keys():
            if request.GET[param] != '':
                objtype = objnames[param]
                i = request.GET[param]
                if param == 'lipid':
                    if Lipid.objects.filter(id=i).exists():
                        obj = Lipid.objects.filter(id=i)
                        name = obj.values_list('search_name', flat=True)[0]
                        url = '#'
                elif param == 'topid':
                    if Topology.objects.filter(id=i).exists():
                        obj = Topology.objects.filter(id=i)
                        version = obj.values_list('version', flat=True)[0]
                        lid = obj.values_list('lipid', flat=True)[0]
                        lname = Lipid.objects.filter(id=lid).values_list('name', flat=True)[0]
                        name = '%s_%s' % (lname, version)
                        url = '#'
                elif param == 'ffid':
                    if Forcefield.objects.filter(id=i).exists():
                        obj = Forcefield.objects.filter(id=i)
                        name = obj.values_list('name', flat=True)[0]
                        url = '#'
                elif param == 'memid':
                    if MembraneTopol.objects.filter(id=i).exists():
                        obj = MembraneTopol.objects.filter(id=i)
                        name = obj.values_list('name', flat=True)[0]
                        url = '#'
                elif param == 'refid':
                    if Reference.objects.filter(id=i).exists():
                        obj = Reference.objects.filter(id=i)
                        name = obj.values_list('refid', flat=True)[0]
                        url = '#'

    subject = ''
    comment = ''
    curator = ''
    if name != '':
        curatorid = obj.values_list('curator', flat=True)[0]
        firstname = User.objects.filter(id=curatorid).values_list('first_name', flat=True)[0]
        lastname = User.objects.filter(id=curatorid).values_list('last_name', flat=True)[0]
        curator = '%s %s' % (firstname, lastname)
        email = User.objects.filter(id=curatorid).values_list('email', flat=True)[0]
        subject = 'Request concerning a Limonada entry'
        curation = '\nIf it is more convenient, the curation can also be changed.'
        comment = ''.join(('Dear Mr/Ms %s,\n\n%s %s ' % (curator, request.user.first_name, request.user.last_name),
                          'is making the following comment on the %s entry (%s) for which ' % (objtype, name),
                          'you are the current curator.\n\n\nCould you please address these comments and/or reply ',
                          'him/her at %s?\n%s\n\nSincerely,\nThe Limonada Team' % (email, curation)))
    form = MailForm({'subject': subject, 'comment': comment})

    data = {}
    data['homepage'] = True
    data['curator'] = curator
    data['curator_id'] = curatorid
    data['objecttype'] = objtype
    data['name'] = name
    data['object_url'] = url
    data['form'] = form
    data['params'] = params

    if request.method == 'POST':
        form = MailForm(request.POST)
        print request.POST
        if form.is_valid():
            curation = form.cleaned_data['curation']
            subject = form.cleaned_data['subject']
            comment = form.cleaned_data['comment']
            if curation:
                send_mail(subject, comment, settings.VERIFIED_EMAIL_MAIL_FROM,
                          [email, 'jean-marc.crowet@univ-reims.fr'])
            else:
                send_mail(subject, comment, settings.VERIFIED_EMAIL_MAIL_FROM, [email, ])
            if 'lipid' in request.GET.keys():
                return redirect('liplist')
            if 'topid' in request.GET.keys():
                return redirect('toplist')
            if 'ffid' in request.GET.keys():
                return redirect('fflist')
            if 'memid' in request.GET.keys():
                return redirect('memlist')
            if 'refid' in request.GET.keys():
                return redirect('reflist')
    return render(request, 'homepage/mail.html', data)
