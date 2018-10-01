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
from django.forms import ModelForm, formset_factory
from django.forms.widgets import NumberInput, Select, Textarea, TextInput

# Django apps
from forcefields.choices import SFTYPE_CHOICES
from lipids.models import Lipid

# local Django
from .models import Composition, Membrane, MembraneTag, MembraneTopol, TopolComposition


class MembraneTopolForm(ModelForm):

    name = forms.CharField(label='Name',
                           widget=TextInput(attrs={'class': 'form-control'}))
    software = forms.ChoiceField(choices=SFTYPE_CHOICES,
                                 initial='GR50',
                                 widget=Select(attrs={'class': 'form-control'}))
    temperature = forms.IntegerField(label='Temperature (°K)',
                                     widget=NumberInput(attrs={'class': 'form-control'}))
    equilibration = forms.IntegerField(label='Equilibration (ns)',
                                       widget=NumberInput(attrs={'class': 'form-control'}))
    mem_file = forms.FileField(label='Membrane file',
                               required=False)
    description = forms.CharField(widget=Textarea(attrs={'class': 'form-control'}),
                                  required=False)

    class Meta:
        model = MembraneTopol
        fields = ['name', 'software', 'forcefield', 'temperature', 'equilibration', 'mem_file', 'description',
                  'reference']
        widgets = {'reference': autocomplete.ModelSelect2Multiple(url='reference-autocomplete'),
                   'forcefield': Select(attrs={'class': 'form-control'})}
        labels = {'reference': 'References'}


class MembraneTopolAdminForm(ModelForm):

    class Meta:
        model = MembraneTopol
        fields = ('__all__')
        widgets = {'reference': autocomplete.ModelSelect2Multiple(url='reference-autocomplete'),
                   'membrane': autocomplete.ModelSelect2(url='membrane-autocomplete'),
                   'curator': autocomplete.ModelSelect2(url='user-autocomplete')}


class MembraneForm(ModelForm):

    class Meta:
        model = Membrane
        fields = ['tag']
        widgets = {'tag': autocomplete.ModelSelect2Multiple(url='membranetagautocomplete',
                                                            attrs={'data-placeholder': 'e.g., plasma membrane'})}


class MembraneAdminForm(ModelForm):

    class Meta:
        model = Membrane
        fields = ('__all__')
        widgets = {'tag': autocomplete.ModelSelect2Multiple(url='tag-autocomplete')}


class CompositionForm(ModelForm):

    number = forms.IntegerField(widget=NumberInput(attrs={'class': 'form-control-sm'}))

    class Meta:
        model = TopolComposition
        fields = ['lipid', 'topology', 'number', 'side']
        widgets = {'lipid': autocomplete.ModelSelect2(url='lipid-autocomplete',
                                                      attrs={'class': 'dal-lipid'}),
                   'side': Select(attrs={'class': 'form-control-sm'})}


MemFormSet = formset_factory(CompositionForm)


class TopolCompositionAdminForm(ModelForm):

    class Meta:
        model = TopolComposition
        fields = ('__all__')
        widgets = {'lipid': autocomplete.ModelSelect2(url='lipid-autocomplete'),
                   'topology': autocomplete.ModelSelect2(url='topology-autocomplete')}


class CompositionAdminForm(ModelForm):

    class Meta:
        model = Composition
        fields = ('__all__')
        widgets = {'lipid': autocomplete.ModelSelect2(url='lipid-autocomplete')}


class SelectMembraneForm(forms.Form):

    lipids = forms.ModelMultipleChoiceField(queryset=Lipid.objects.all(),
                                            widget=autocomplete.ModelSelect2Multiple(url='lipid-autocomplete'),
                                            required=False)
    tags = forms.ModelMultipleChoiceField(queryset=MembraneTag.objects.all(),
                                          widget=autocomplete.ModelSelect2Multiple(url='tag-autocomplete'),
                                          required=False)
    nbliptypes = forms.IntegerField(label='Lipid species > ',
                                    widget=NumberInput(attrs={'class': 'form-control'}),
                                    required=False)
    nblipids = forms.IntegerField(label='Lipids > ',
                                  widget=NumberInput(attrs={'class': 'form-control'}),
                                  required=False)
    equilibration = forms.IntegerField(label='Equilibration (ns) > ',
                                       widget=NumberInput(attrs={'class': 'form-control'}),
                                       required=False)
