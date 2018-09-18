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
from django.forms import Form, ModelForm
from django.forms.widgets import Textarea, TextInput, CheckboxInput

# local Django
from .models import Reference, validate_doi, validate_year


class DoiForm(Form):

    doisearch = forms.CharField(widget=TextInput(attrs={'placeholder': 'e.g., 10.1021/jp101759q',
                                                        'class': 'form-control'}),
                                label='DOI',
                                validators=[validate_doi])


class ReferenceForm(ModelForm):

    refid = forms.CharField(widget=TextInput(attrs={'placeholder': 'e.g., Klauda2010b',
                                                    'class': 'form-control'}),
                            label='Name')
    authors = forms.CharField(widget=TextInput(attrs={'class': 'form-control'}))
    title = forms.CharField(widget=TextInput(attrs={'class': 'form-control'}))
    journal = forms.CharField(widget=TextInput(attrs={'class': 'form-control'}))
    volume = forms.CharField(widget=TextInput(attrs={'class': 'form-control'}),
                             required=False)
    year = forms.CharField(widget=TextInput(attrs={'class': 'form-control'}))
    doi = forms.CharField(widget=TextInput(attrs={'class': 'form-control',
                                                  'placeholder': 'e.g., 10.1021/jp101759q'}),
                          required=False,
                          label='DOI')

    class Meta:
        model = Reference
        fields = ['refid', 'authors', 'title', 'journal', 'volume', 'year', 'doi']


class ReferenceAdminForm(ModelForm):

    class Meta:
        model = Reference
        fields = ('__all__')
        widgets = {'curator': autocomplete.ModelSelect2(url='user-autocomplete')}


class SelectForm(Form):

    year = forms.IntegerField(validators=[validate_year],
                              widget=TextInput(attrs={'size': '10',
                                                      'class': 'form-control'}),
                              label='Year')


class MailForm(Form):

    subject = forms.CharField(widget=TextInput(attrs={'size': '37',
                                                      'class': 'form-control'}),
                              required=False)
    comment = forms.CharField(widget=Textarea(attrs={'class': 'form-control'}),
                              required=False)
    curation = forms.BooleanField(required=False,
                                  widget=CheckboxInput(attrs={'class':'your_class'}),
                                  label='Request to become the new curator:')
