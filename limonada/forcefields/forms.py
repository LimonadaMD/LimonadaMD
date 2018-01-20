from django import forms
from dal import autocomplete
from .models import Forcefield
from homepage.models import Reference
from forcefields.choices import *


class ForcefieldForm(forms.ModelForm):

    class Meta:
        model = Forcefield
        fields = ['name','forcefield_type','ff_file','mdp_file','software','description','reference']
        widgets = {
            'reference': autocomplete.ModelSelect2Multiple(
                url='reference-autocomplete'
            )
        }


class SelectForcefieldForm(forms.Form):

    software = forms.ChoiceField(choices=SFTYPE_CHOICES,
                                 required=False)
    forcefield_type = forms.ChoiceField(choices = FFTYPE_CHOICES,
                                        required=False)


