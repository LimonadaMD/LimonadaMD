from django.conf import settings
from django import forms
from django.forms import ModelForm, BaseInlineFormSet, fields
from django.forms import formset_factory, inlineformset_factory
from .models import Membrane, Composition
from django.forms.formsets import BaseFormSet
from lipids.models import Lipid, Topology
from dal import autocomplete


class MembraneForm(ModelForm):

    class Meta:
        model = Membrane
        fields = ['name','equilibration','mem_file','description','reference']
        widgets = {
            'reference': autocomplete.ModelSelect2Multiple(
                url='reference-autocomplete'
            ),
        }



class CompositionForm(ModelForm):
    class Meta:
        model = Composition
        fields = ['topology','number','side']


MemFormSet = formset_factory(CompositionForm)


class SelectMembraneForm(forms.Form):

    equilibration = forms.IntegerField(label="Equilibration greater than (ns):",
                                       widget=forms.NumberInput(attrs={'style': 'width:12ch',}), 
                                       required=False)
    lipid = forms.ModelMultipleChoiceField(queryset=Lipid.objects.all(),
                                           widget=autocomplete.ModelSelect2Multiple(url='lipid-autocomplete'),
                                           required=False)



