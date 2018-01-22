from django import forms
from dal import autocomplete
from .models import Forcefield
from homepage.models import Reference
from forcefields.choices import *


class ForcefieldForm(forms.ModelForm):

    ff_file      = forms.FileField(label="Forcefield file",
                                   help_text="Use a zip file containing the forcefield directory as in <link>")
    mdp_file     = forms.FileField(label="Parameters file",
                                   help_text="Use a zip file containing the mdps for the version X of Gromacs as in <link>>")

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


