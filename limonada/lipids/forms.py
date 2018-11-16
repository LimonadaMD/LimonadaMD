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
from django.utils.safestring import mark_safe

# Django apps
from forcefields.models import Forcefield, Software

# local Django
from .functions import gmxrun
from .models import TopComment, Lipid, Topology, validate_file_extension, validate_lmid, validate_name


class LipidAdminForm(forms.ModelForm):

    class Meta:
        model = Lipid
        fields = ('__all__')
        widgets = {'curator': autocomplete.ModelSelect2(url='user-autocomplete')}


class LmidForm(forms.Form):

    lmidsearch = forms.CharField(label='LipidMaps ID',
                                 widget=TextInput(attrs={'placeholder': 'e.g., LMGP01010005',
                                                         'class': 'form-control'}),
                                 validators=[validate_lmid])


class LipidForm(forms.ModelForm):

    name = forms.CharField(widget=TextInput(attrs={'placeholder': 'e.g., POPC',
                                                   'class': 'form-control'}),
                           validators=[validate_name])
    lmid = forms.CharField(validators=[validate_lmid])
    core = forms.CharField(label='Category',
                           widget=TextInput(attrs={'readonly': 'readonly',
                                                   'class': 'form-control'}),
                           required=False)
    main_class = forms.CharField(label='Main Class',
                                 widget=TextInput(attrs={'readonly': 'readonly',
                                                         'class': 'form-control'}),
                                 required=False)
    sub_class = forms.CharField(label='Sub Class',
                                widget=TextInput(attrs={'readonly': 'readonly',
                                                        'class': 'form-control'}),
                                required=False)
    l4_class = forms.CharField(label='Class Level 4',
                               widget=TextInput(attrs={'readonly': 'readonly',
                                                       'class': 'form-control'}),
                               required=False)
    com_name = forms.CharField(widget=TextInput(attrs={'class': 'form-control'}))
    sys_name = forms.CharField(label='Systematic Name',
                               widget=TextInput(attrs={'class': 'form-control'}),
                               required=False)
    iupac_name = forms.CharField(label='IUPAC Name',
                                 widget=TextInput(attrs={'class': 'form-control'}),
                                 required=False)
    formula = forms.CharField(label='Formula',
                              widget=TextInput(attrs={'class': 'form-control'}),
                              required=False)
    pubchem_cid = forms.CharField(label='PubChem CID',
                                  widget=TextInput(attrs={'class': 'form-control'}),
                                  required=False)
    img = forms.ImageField(widget=forms.FileInput(attrs={'accept': '.jpg,.png'}),
                           validators=[validate_file_extension],
                           required=False)

    class Meta:
        model = Lipid
        fields = ['name', 'lmid', 'core', 'main_class', 'sub_class', 'l4_class', 'com_name', 'sys_name', 'iupac_name',
                  'formula', 'pubchem_cid', 'img']


class SelectLipidForm(forms.Form):

    lipidid = forms.ModelMultipleChoiceField(label='Lipid',
                                             queryset=Lipid.objects.all(),
                                             widget=autocomplete.ModelSelect2Multiple(url='lipid-autocomplete'),
                                             required=False)
    category = forms.ChoiceField(label='Category',
                                 required=False)
    main_class = forms.ChoiceField(label='Main Class',
                                   required=False)
    sub_class = forms.ChoiceField(label='Sub Class',
                                  required=False)
    l4_class = forms.ChoiceField(label='Class Level 4',
                                 required=False)


class TopologyAdminForm(forms.ModelForm):

    class Meta:
        model = Topology
        fields = ('__all__')
        widgets = {'lipid': autocomplete.ModelSelect2(url='lipid-autocomplete'),
                   'software': autocomplete.ModelSelect2Multiple(url='software-autocomplete'),
                   'reference': autocomplete.ModelSelect2Multiple(url='reference-autocomplete'),
                   'curator': autocomplete.ModelSelect2(url='user-autocomplete')}


class TopologyForm(forms.ModelForm):

    forcefield = forms.ModelChoiceField(queryset=Forcefield.objects.all())
    itp_file = forms.FileField(label='Topology file')
    gro_file = forms.FileField(label='Structure file')
    version = forms.CharField(widget=TextInput(attrs={'class': 'form-control',
                                                      'placeholder': 'e.g., Klauda2010b'}))
    description = forms.CharField(widget=Textarea(attrs={'class': 'form-control'}),
                                  required=False)

    class Meta:
        model = Topology
        fields = ['software', 'forcefield', 'lipid', 'itp_file', 'gro_file', 'version', 'description', 'reference']
        widgets = {'lipid': autocomplete.ModelSelect2(url='lipid-autocomplete'),
                   'software': autocomplete.ModelSelect2Multiple(url='software-autocomplete'),
                   'reference': autocomplete.ModelSelect2Multiple(url='reference-autocomplete')}
        labels = {'reference': 'References'}

    def clean(self):
        cleaned_data = super(TopologyForm, self).clean()
        software = cleaned_data.get('software')
        ff = cleaned_data.get('forcefield')
        lipid = cleaned_data.get('lipid')
        version = cleaned_data.get('version')

        if lipid and ff and version:
            if Topology.objects.filter(
                    lipid=lipid, forcefield=ff, version=version).exclude(pk=self.instance.id).exists():
                self.add_error('version', mark_safe(
                    'This version name is already taken by another topology entry for this lipid and forcefield.'))

        if lipid and ff and software and 'itp_file' in cleaned_data.keys() and 'gro_file' in cleaned_data.keys():
            itp_file = cleaned_data['itp_file']
            gro_file = cleaned_data['gro_file']
            for soft in software:
                error, rand = gmxrun(lipid.name, ff.ff_file.url, itp_file, gro_file, soft.abbreviation)
                if error:
                    logpath = '/media/tmp/%s/gromacs.log' % rand
                    self.add_error('itp_file', mark_safe(
                        'Topology file is not valid. See <a class="text-success" href="%s">gromacs.log</a>' % logpath))

        return cleaned_data


class SelectTopologyForm(forms.Form):

    software = forms.ModelMultipleChoiceField(queryset=Software.objects.all(),
                                              widget=autocomplete.ModelSelect2Multiple(url='software-autocomplete'),
                                              required=False)
    forcefield = forms.ModelChoiceField(queryset=Forcefield.objects.all(),
                                        required=False)
    lipid = forms.ModelMultipleChoiceField(queryset=Lipid.objects.all(),
                                           widget=autocomplete.ModelSelect2Multiple(url='lipid-autocomplete'),
                                           required=False)
    category = forms.ChoiceField(label='Category',
                                 required=False)
    main_class = forms.ChoiceField(label='Main Class',
                                   required=False)
    sub_class = forms.ChoiceField(label='Sub Class',
                                  required=False)
    l4_class = forms.ChoiceField(label='Class Level 4',
                                 required=False)


class TopCommentAdminForm(forms.ModelForm):

    class Meta:
        model = TopComment
        fields = ('__all__')
        widgets = {'user': autocomplete.ModelSelect2(url='user-autocomplete')}


class TopCommentForm(forms.ModelForm):

    class Meta:
        model = TopComment
        fields = ['comment']
        widgets = {'comment': Select(attrs={'class': 'form-control'})}
