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
import zipfile

# third-party
from dal import autocomplete

# Django
from django import forms
from django.conf import settings
from django.core.files.storage import default_storage
from django.forms.widgets import Select, Textarea, TextInput
from django.utils.safestring import mark_safe

# Django apps
from forcefields.choices import FFTYPE_CHOICES

# local Django
from .models import Forcefield, Software


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

        if name and soft:
            software = Software.objects.filter(name=soft)
            if Forcefield.objects.filter(
                    name=name, software=software).exclude(pk=self.instance.id).exists():
                self.add_error('name', mark_safe(
                    'This name is already taken by another forcefield entry for the %s software.' % (software.name)))

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
            except:
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
                mdpzip = zipfile.ZipFile(mediapath)
            except:
                self.add_error('mdp_file', mark_safe('Invalid ZIP file'))


class SelectForcefieldForm(forms.Form):

    software = forms.ModelMultipleChoiceField(queryset=Software.objects.all(),
                                              widget=autocomplete.ModelSelect2Multiple(url='software-autocomplete'),
                                              required=False)
    forcefield_type = forms.ChoiceField(choices=FFTYPE_CHOICES,
                                        widget=Select(attrs={'class': 'form-control'}),
                                        required=False)
