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

# third-party
from dal import autocomplete

# Django
from django import forms
from django.contrib.auth.models import User
from django.forms.widgets import Select
from django.forms.widgets import Textarea

# Django apps
from membranes.models import MembraneTopol

# local Django
from .choices import PROPTYPE_CHOICES
from .models import LI_Property


class LI_PropertyAdminForm(forms.ModelForm):

    class Meta:
        model = LI_Property
        fields = ('__all__')
        widgets = {'membranetopol': autocomplete.ModelSelect2(url='membranetopol-autocomplete'),
                   'software': autocomplete.ModelSelect2Multiple(url='analysissoftware-autocomplete'),
                   'curator': autocomplete.ModelSelect2(url='user-autocomplete')}


class LI_PropertyForm(forms.ModelForm):

    prop = forms.ChoiceField(label='Property',
                             choices=PROPTYPE_CHOICES,
                             widget=Select(attrs={'class': 'form-control'}))
    data_file = forms.FileField(label='Data file',
                                required=True)
    description = forms.CharField(widget=Textarea(attrs={'class': 'form-control'}),
                                  required=False)

    class Meta:
        model = LI_Property
        fields = ['prop', 'membranetopol', 'data_file', 'software', 'description']
        widgets = {'membranetopol': autocomplete.ModelSelect2(url='membranetopol-autocomplete'),
                   'software': autocomplete.ModelSelect2(url='analysissoftware-autocomplete')}
        labels = {'membranetopol': 'Membrane'}


class SelectForm(forms.Form):

    propid = forms.ModelMultipleChoiceField(label='Property',
                                            queryset=LI_Property.objects.all(),
                                            widget=autocomplete.ModelSelect2Multiple(url='prop-autocomplete'),
                                            required=False)
    memid = forms.ModelMultipleChoiceField(label='Membrane',
                                           queryset=MembraneTopol.objects.all(),
                                           widget=autocomplete.ModelSelect2Multiple(url='membranetopol-autocomplete'),
                                           required=False)
