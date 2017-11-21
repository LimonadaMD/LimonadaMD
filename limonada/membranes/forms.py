from django import forms
from django.forms import ModelForm, BaseInlineFormSet
from django.forms import formset_factory, inlineformset_factory
from .models import Membrane, Composition
from django.forms.formsets import BaseFormSet
from lipids.models import Topology


class MembraneForm(ModelForm):
    class Meta:
        model = Membrane
        fields = ['name','equilibration','mem_file','description','reference']


class CompositionForm(ModelForm):
    class Meta:
        model = Composition
        fields = ['topology','number','side']

#MemFormSet = inlineformset_factory(Membrane, Composition, form=CompositionForm)
MemFormSet = inlineformset_factory(Membrane, Composition, form=CompositionForm, extra=1)
#MemFormSet = formset_factory(CompositionForm, extra=1, can_delete=True)


