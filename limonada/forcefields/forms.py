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
import zipfile

# third-party
from dal import autocomplete

# Django
from django import forms
from django.core.files.storage import default_storage
from django.db.models import Q
from django.forms.widgets import Select, Textarea, TextInput
from django.utils.safestring import mark_safe

# Django apps
from forcefields.choices import FFTYPE_CHOICES

# local Django
from .choices import SFTYPE_CHOICES
from .models import Forcefield, Software, FfComment


class ForcefieldAdminForm(forms.ModelForm):

    class Meta:
        model = Forcefield
        fields = ('__all__')
        widgets = {'reference': autocomplete.ModelSelect2Multiple(url='reference-autocomplete'),
                   'software': autocomplete.ModelSelect2Multiple(url='software-autocomplete'),
                   'curator': autocomplete.ModelSelect2(url='user-autocomplete')}


class ForcefieldForm(forms.ModelForm):

    name = forms.CharField(widget=TextInput(attrs={'class': 'form-control'}))
    forcefield_type = forms.ChoiceField(choices=FFTYPE_CHOICES,
                                        initial='AA',
                                        widget=Select(attrs={'class': 'form-control'}))
    ff_file = forms.FileField(label='Forcefield files')
    mdp_file = forms.FileField(label='Parameters files',
                               required=False)
    description = forms.CharField(widget=Textarea(attrs={'class': 'form-control'}),
                                  required=False)

    class Meta:
        model = Forcefield
        fields = ['name', 'forcefield_type', 'ff_file', 'mdp_file', 'software', 'description', 'reference']
        widgets = {'software': autocomplete.ModelSelect2Multiple(url='software-autocomplete'),
                   'reference': autocomplete.ModelSelect2Multiple(url='reference-autocomplete')}
        labels = {'reference': 'References'}

    def clean(self):
        cleaned_data = super(ForcefieldForm, self).clean()
        name = cleaned_data.get('name')
        soft = cleaned_data.get('software')[0]
        ff_file = cleaned_data.get('ff_file')
        mdp_file = cleaned_data.get('mdp_file')

        if soft.name == "Namd":
            self.add_error('software', mark_safe(
                'Forcefields cannot be added for %s.' % (soft.name)))

        if name and soft:
            softlist = Software.objects.filter(name=soft.name)
            ff_list = Forcefield.objects.all()
            querylist = []
            for i in softlist:
                querylist.append(Q(software=i))
            ff_list = ff_list.filter(reduce(operator.or_, querylist)).distinct()
            if ff_list.filter(name=name).exclude(pk=self.instance.id).exists():
                self.add_error('name', mark_safe(
                    'This name is already taken by another forcefield entry for the %s software.' % (soft.name)))

        if ff_file:
            path = os.path.join('tmp/', 'clean_%s' % ff_file.name)
            mediapath = os.path.join('media/', path)
            if os.path.isfile(mediapath):
                os.remove(mediapath)
            with default_storage.open(path, 'wb+') as destination:
                for chunk in ff_file.chunks():
                    destination.write(chunk)
            try:
                ffzip = zipfile.ZipFile(mediapath)
                if not ffzip.namelist():
                    self.add_error('ff_file', mark_safe('Empty ZIP file'))
            except zipfile.BadZipFile:
                self.add_error('ff_file', mark_safe('Invalid ZIP file'))

        if mdp_file:
            path = os.path.join('tmp/', 'clean_%s' % mdp_file.name)
            mediapath = os.path.join('media/', path)
            if os.path.isfile(mediapath):
                os.remove(mediapath)
            with default_storage.open(path, 'wb+') as destination:
                for chunk in mdp_file.chunks():
                    destination.write(chunk)
            try:
                zipfile.ZipFile(mediapath)
            except zipfile.BadZipFile:
                self.add_error('mdp_file', mark_safe('Invalid ZIP file'))


class SelectForcefieldForm(forms.Form):

    software = forms.ChoiceField(choices=(('', '---------'),) + SFTYPE_CHOICES,
                                 widget=Select(attrs={'class': 'form-control'}),
                                 required=False)
    softversion = forms.ModelChoiceField(queryset=Software.objects.all(),
                                         label='Version',
                                         required=False)
    forcefield_type = forms.ChoiceField(choices=(('', '---------'),) + FFTYPE_CHOICES,
                                        widget=Select(attrs={'class': 'form-control'}),
                                        required=False)


class FfCommentAdminForm(forms.ModelForm):

    class Meta:
        model = FfComment
        fields = ('__all__')
        widgets = {'user': autocomplete.ModelSelect2(url='user-autocomplete')}


class FfCommentForm(forms.ModelForm):

    class Meta:
        model = FfComment
        fields = ['comment']
        widgets = {'comment': Select(attrs={'class': 'form-control'})}
