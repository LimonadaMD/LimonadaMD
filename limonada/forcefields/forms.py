from django import forms
from dal import autocomplete
from .models import Forcefield
from homepage.models import Reference


class ForcefieldForm(forms.ModelForm):

    #reference = forms.ModelChoiceField(
    #    queryset=Reference.objects.all(),
    #    widget=autocomplete.ModelSelect2(url='reference-autocomplete')
    #)

    class Meta:
        model = Forcefield
        widgets = {
             'reference': forms.CheckboxSelectMultiple, 
             #'reference': autocomplete.ModelSelect2Multiple(url='reference-autocomplete')
        }
        fields = ['name','forcefield_type','ff_file','mdp_file','software','description','reference']



