# -*- coding: utf-8; Mode: python; tab-width: 4; indent-tabs-mode:nil; -*-
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
#
#  Copyright (C) 2016-2020  Jean-Marc Crowet <jeanmarccrowet@gmail.com>
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
from forcefields.choices import FFTYPE_CHOICES, SFTYPE_CHOICES

# local Django
from .models import Forcefield


class ForcefieldForm(forms.ModelForm):

    name = forms.CharField(widget=TextInput(attrs={'class': 'form-control'}))
    forcefield_type = forms.ChoiceField(choices=FFTYPE_CHOICES,
                                        initial='AA',
                                        widget=Select(attrs={'class': 'form-control'}))
    ff_file = forms.FileField(label='Forcefield files')
    mdp_file = forms.FileField(label='Parameters files')
    software = forms.ChoiceField(choices=SFTYPE_CHOICES,
                                 initial='GR50',
                                 widget=Select(attrs={'class': 'form-control'}))
    description = forms.CharField(widget=Textarea(attrs={'class': 'form-control'}),
                                  required=False)

    class Meta:
        model = Forcefield
        fields = ['name', 'forcefield_type', 'ff_file', 'mdp_file', 'software', 'description', 'reference']
        widgets = {'reference': autocomplete.ModelSelect2Multiple(url='reference-autocomplete')}
        labels = {'reference': 'References'}


class ForcefieldAdminForm(forms.ModelForm):

    class Meta:
        model = Forcefield
        fields = ('__all__')
        widgets = {'reference': autocomplete.ModelSelect2Multiple(url='reference-autocomplete'),
                   'curator': autocomplete.ModelSelect2(url='user-autocomplete')}


class SelectForcefieldForm(forms.Form):

    software = forms.ChoiceField(choices=SFTYPE_CHOICES,
                                 widget=Select(attrs={'class': 'form-control'}),
                                 required=False)
    forcefield_type = forms.ChoiceField(choices=FFTYPE_CHOICES,
                                        widget=Select(attrs={'class': 'form-control'}),
                                        required=False)
