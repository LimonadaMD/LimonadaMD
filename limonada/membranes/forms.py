from django.conf import settings
from django import forms
from django.forms import ModelForm, BaseInlineFormSet, fields
from django.forms import formset_factory, inlineformset_factory
from .models import Membrane, Composition
from django.forms.formsets import BaseFormSet
from lipids.models import Topology


class MembraneForm(ModelForm):
    class Meta:
        model = Membrane
        fields = ['name','equilibration','mem_file','description','reference','curator']


class CompositionForm(ModelForm):
    class Meta:
        model = Composition
        fields = ['topology','number','side']


MemFormSet = formset_factory(CompositionForm)

