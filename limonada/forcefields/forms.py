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
from dal import autocomplete

# Django
from django import forms
from django.forms.widgets import Select, Textarea, TextInput

# Django apps
from forcefields.choices import FFTYPE_CHOICES

# local Django
from .models import Forcefield, Software


class ForcefieldForm(forms.ModelForm):

    name = forms.CharField(widget=TextInput(attrs={'class': 'form-control'}))
    forcefield_type = forms.ChoiceField(choices=FFTYPE_CHOICES,
                                        initial='AA',
                                        widget=Select(attrs={'class': 'form-control'}))
    ff_file = forms.FileField(label='Forcefield files')
    mdp_file = forms.FileField(label='Parameters files')
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
        softindex = cleaned_data.get('software')[0]

        if name and softindex:
            software = Software.objects.filter(name=softindex)
            if Forcefield.objects.filter(
                    name=name, software=software).exclude(pk=self.instance.id).exists():
                self.add_error('name', mark_safe(
                    'This name is already taken by another forcefield entry for the %s software.' % (software.abbreviation)))


class ForcefieldAdminForm(forms.ModelForm):

    class Meta:
        model = Forcefield
        fields = ('__all__')
        widgets = {'reference': autocomplete.ModelSelect2Multiple(url='reference-autocomplete'),
                   'software': autocomplete.ModelSelect2Multiple(url='software-autocomplete'),
                   'curator': autocomplete.ModelSelect2(url='user-autocomplete')}


class SelectForcefieldForm(forms.Form):

    software = forms.ModelMultipleChoiceField(queryset=Software.objects.all(),
                                              widget=autocomplete.ModelSelect2Multiple(url='software-autocomplete'),
                                              required=False)
    forcefield_type = forms.ChoiceField(choices=FFTYPE_CHOICES,
                                        widget=Select(attrs={'class': 'form-control'}),
                                        required=False)
