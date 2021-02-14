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
from django.db import transaction
from django.db.models import Q
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.views.generic import DeleteView

# Django apps
from forcefields.models import Forcefield
from limonada.functions import review_notification
from lipids.models import Lipid, Topology
from membranes.models import MembraneTopol
from properties.models import LI_Property

# local Django
from .forms import DoiForm, MailForm, ReferenceForm, AuthorsForm, SelectForm
from .models import Author, Reference, AuthorsList


def homepage(request):

    data = {'homepage': True}
    return render(request, 'homepage/index.html', data)


def links(request):

    data = {'links': True}
    return render(request, 'homepage/links.html', data)


def RefList(request):

    ref_list = Reference.objects.all().order_by('-year')

    params = request.GET.copy()

    selectparams = {}
    for param in ['author', 'year', 'id']:
        if param in request.GET.keys():
            if request.GET[param] != '':
                if param == 'author':
                    aulist = request.GET[param].split(',')
                    selectparams['author'] = aulist
                else:
                    selectparams[param] = request.GET[param]
    form_select = SelectForm(selectparams)
    if form_select.is_valid():
        if 'author' in selectparams.keys():
            querylist = []
            for i in aulist:
                querylist.append(Q(author=Author.objects.filter(id=i)[0]))
            ref_list = ref_list.filter(reduce(operator.and_, querylist))
        if 'year' in selectparams.keys():
            ref_list = ref_list.filter(year=selectparams['year'])
        if 'id' in selectparams.keys():
            ref_list = ref_list.filter(id=selectparams['id'])
    else:
        form_select = SelectForm()

    sort = request.GET.get('sort')
    sortdir = request.GET.get('dir')
    headers = ['refid', 'title', 'year']
    if sort is not None and sort in headers:
        ref_list = ref_list.order_by(sort)
        if sortdir == 'des':
            ref_list = ref_list.reverse()

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
    if sort is not None and sort in headers:
        data['dir'] = sortdir
    data['references'] = True
    data['params'] = params

    return render(request, 'homepage/references.html', data)


@login_required
@transaction.atomic
def RefCreate(request):
    if request.method == 'POST' and 'search' in request.POST:
        form_search = DoiForm(request.POST)
        form_authors = AuthorsForm()
        form_add = ReferenceForm()
        if form_search.is_valid():
            doi = form_search.cleaned_data['doisearch']
            url = 'https://dx.doi.org/%s' % doi
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
            form_authors = AuthorsForm(initial=doidata)
            return render(request, 'homepage/ref_form.html',
                          {'form_search': form_search, 'form_authors': form_authors, 'form_add': form_add,
                           'references': True, 'search': True})
    elif request.method == 'POST' and 'add' in request.POST:
        form_search = DoiForm()
        form_authors = AuthorsForm(request.POST)
        form_add = ReferenceForm(request.POST)
        if form_add.is_valid() and form_authors.is_valid():
            ref = form_add.save(commit=False)
            ref.curator = request.user
            ref.save()
            aupos = 0
            aulist = []
            authors = form_authors.cleaned_data['authors']
            for author in authors.split(','):
                aupos += 1
                fullname = author.strip()
                familly = author.strip().split()[0].strip()
                given = " ".join(author.strip().split()[1:]).strip()
                if not Author.objects.filter(fullname=fullname).count():
                    au = Author.objects.create(fullname=fullname, familly=familly, given=given, curator=request.user)
                else:
                    au = Author.objects.filter(fullname=fullname)[0]
                aulist.append(AuthorsList(reference=ref, author=au, position=aupos))
            with transaction.atomic():
                AuthorsList.objects.filter(reference=ref).delete()
                AuthorsList.objects.bulk_create(aulist)
            ref.save()
            review_notification("creation", "references", ref.pk)
            return HttpResponseRedirect(reverse('reflist'))
    else:
        form_search = DoiForm()
        form_authors = AuthorsForm()
        form_add = ReferenceForm()
    return render(request, 'homepage/ref_form.html',
                  {'form_search': form_search, 'form_authors': form_authors,
                   'form_add': form_add, 'references': True, 'search': True})


@login_required
@transaction.atomic
def RefUpdate(request, pk=None):
    if Reference.objects.filter(pk=pk).exists():
        ref = Reference.objects.get(pk=pk)
        text = ''
        for author in ref.authorslist_set.all():
            text += '%s %s, ' % (author.author.familly, author.author.given)
        text = text[0:-2]
        if request.method == 'POST':
            form_add = ReferenceForm(request.POST, instance=ref)
            form_authors = AuthorsForm(request.POST)
            if form_add.is_valid() and form_authors.is_valid():
                ref.refid = form_add.cleaned_data['refid']
                ref.title = form_add.cleaned_data['title']
                ref.journal = form_add.cleaned_data['journal']
                ref.volume = form_add.cleaned_data['volume']
                ref.year = form_add.cleaned_data['year']
                ref.doi = form_add.cleaned_data['doi']
                ref.save()
                aupos = 0
                aulist = []
                authors = form_authors.cleaned_data['authors']
                for author in authors.split(','):
                    aupos += 1
                    fullname = author.strip()
                    familly = author.strip().split()[0].strip()
                    given = " ".join(author.strip().split()[1:]).strip()
                    if not Author.objects.filter(fullname=fullname).count():
                        au = Author.objects.create(fullname=fullname, familly=familly, given=given,
                                                   curator=request.user)
                    else:
                        au = Author.objects.filter(fullname=fullname)[0]
                    aulist.append(AuthorsList(reference=ref, author=au, position=aupos))
                with transaction.atomic():
                    AuthorsList.objects.filter(reference=ref).delete()
                    AuthorsList.objects.bulk_create(aulist)
                ref.save()
                review_notification("update", "references", ref.pk)
                return HttpResponseRedirect(reverse('reflist'))
        else:
            form_authors = AuthorsForm(initial={'authors': text})
            form_add = ReferenceForm(instance=ref)
        return render(request, 'homepage/ref_form.html',
                      {'form_authors': form_authors, 'form_add': form_add, 'references': True, 'search': False})
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
        qs = Reference.objects.all().order_by('refid')
        if self.q:
            qs = qs.filter(refid__icontains=self.q)
        return qs


@login_required
def mail(request):

    params = request.GET.copy()

    name = ''
    obj = ''
    objtype = ''
    objnames = {'lipid': 'lipid', 'topid': 'topology', 'ffid': 'forcefield', 'memid': 'membrane',
                'liproperty': 'propid', 'refid': 'reference'}
    for param in ['lipid', 'topid', 'ffid', 'memid', 'propid', 'refid']:
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
                elif param == 'propid':
                    if LI_Property.objects.filter(id=i).exists():
                        obj = LI_Property.objects.filter(id=i)
                        name = obj.values_list('search_name', flat=True)[0]
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
        if form.is_valid():
            curation = form.cleaned_data['curation']
            subject = form.cleaned_data['subject']
            comment = form.cleaned_data['comment']
            if curation:
                send_mail(subject, comment, settings.DEFAULT_FROM_EMAIL,
                          [email, settings.DEFAULT_FROM_EMAIL])
            else:
                send_mail(subject, comment, settings.DEFAULT_FROM_EMAIL, [email, ])
            if 'lipid' in request.GET.keys():
                return redirect('liplist')
            if 'topid' in request.GET.keys():
                return redirect('toplist')
            if 'ffid' in request.GET.keys():
                return redirect('fflist')
            if 'memid' in request.GET.keys():
                return redirect('memlist')
            if 'propid' in request.GET.keys():
                return redirect('memlist')
            if 'refid' in request.GET.keys():
                return redirect('reflist')
    return render(request, 'homepage/mail.html', data)


class AuthorAutocomplete(autocomplete.Select2QuerySetView):

    def get_queryset(self):
        qs = Author.objects.all().order_by('familly')
        if self.q:
            qs = qs.filter(familly__icontains=self.q)
        return qs
