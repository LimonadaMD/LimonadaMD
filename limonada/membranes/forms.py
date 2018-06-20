# -*- coding: utf-8 -*-
from django.conf import settings
from django import forms
from django.forms import ModelForm, BaseInlineFormSet, fields
from django.forms import formset_factory, inlineformset_factory
from django.forms.widgets import TextInput, Select, Textarea, NumberInput
from .models import MembraneTopol, Membrane, TopolComposition, MembraneTag
from django.forms.formsets import BaseFormSet
from lipids.models import Lipid, Topology
from dal import autocomplete
from homepage.models import Reference
from forcefields.choices import *


class MembraneTopolForm(ModelForm):

    name          = forms.CharField(label="Name",
                                    widget=TextInput(attrs={'size': '33'}))
    software     = forms.ChoiceField(choices=SFTYPE_CHOICES,
                                     initial="GR50",
                                     widget=Select(attrs={'style': 'width: 340px'}))
    temperature   = forms.IntegerField(label="Temperature (°K)",
                                       widget=NumberInput(attrs={'style': 'width: 340px'}))
    equilibration = forms.IntegerField(label="Equilibration (ns)",
                                       widget=NumberInput(attrs={'style': 'width: 340px'}))
    mem_file      = forms.FileField(label="Membrane file",
                                    required=False)
    description   = forms.CharField(widget=Textarea(attrs={'style': 'width: 340px'}),
                                    required=False)

    class Meta:
        model = MembraneTopol
        fields = ['name','software','forcefield','temperature','equilibration','mem_file','description','reference']
        widgets = {
            'reference': autocomplete.ModelSelect2Multiple(
                url='reference-autocomplete',
                attrs={'style': 'width: 340px'},
            ),
            'forcefield': Select(
                attrs={'style': 'width: 340px'},
            )        
        }
        labels = {
            'reference': 'References'
        }


class MembraneForm(ModelForm):

    class Meta:
        model = Membrane
        fields = ['tag']
        widgets = {
            'tag': autocomplete.ModelSelect2Multiple(
                url='membranetagautocomplete',
                attrs={'style': 'width: 340px'},
            ),
        }


class CompositionForm(ModelForm):

    number = forms.IntegerField(widget=NumberInput(attrs={'style': 'width: 75px'}))

    class Meta:
        model = TopolComposition
        fields = ['lipid','topology','number','side']
        widgets = {
            'lipid': autocomplete.ModelSelect2(
                url='lipid-autocomplete',
                attrs={'class':'dal-lipid',
                       'style': 'width: 50px'},
            ),
            'topology': Select(
                attrs={'style': 'width: 115px'},
            ),
        }


MemFormSet = formset_factory(CompositionForm)


class SelectMembraneForm(forms.Form):

    lipids = forms.ModelMultipleChoiceField(queryset=Lipid.objects.all(),
                                            widget=autocomplete.ModelSelect2Multiple(url='lipid-autocomplete'),
                                            required=False)
    tags = forms.ModelMultipleChoiceField(queryset=MembraneTag.objects.all(),
                                          widget=autocomplete.ModelSelect2Multiple(url='tag-autocomplete'),
                                          required=False)
    nbliptypes = forms.IntegerField(label="Number of lipid species greater than:",
                                    widget=forms.NumberInput(attrs={'style': 'width:12ch',}), 
                                    required=False)
    nblipids = forms.IntegerField(label="Number of lipids greater than:",
                                  widget=forms.NumberInput(attrs={'style': 'width:12ch',}), 
                                  required=False)
    equilibration = forms.IntegerField(label="Equilibration greater than (ns):",
                                       widget=forms.NumberInput(attrs={'style': 'width:12ch',}), 
                                       required=False)



