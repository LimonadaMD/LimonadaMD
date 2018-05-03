from django import forms
from dal import autocomplete
from django.forms.widgets import TextInput, Select, Textarea
from .models import Forcefield
from homepage.models import Reference
from forcefields.choices import *


class ForcefieldForm(forms.ModelForm):

    name               = forms.CharField(widget=TextInput(attrs={'size': '33'}))
    forcefield_type    = forms.ChoiceField(choices=FFTYPE_CHOICES,
                                           initial="AA",
                                           widget=Select(attrs={'style': 'width: 340px'}))
    ff_file            = forms.FileField(label="Forcefield files")
                                         #help_text="Use a zip file containing the forcefield directory as in <link>")
    mdp_file           = forms.FileField(label="Parameters files")
                                         #help_text="Use a zip file containing the mdps for the version X of Gromacs as in <link>")
    software           = forms.ChoiceField(choices=SFTYPE_CHOICES,
                                           initial="GR",
                                           widget=Select(attrs={'style': 'width: 340px'}))
    description        = forms.CharField(widget=Textarea(attrs={'style': 'width: 340px'}),
                                         required=False)

    class Meta:
        model = Forcefield
        fields = ['name','forcefield_type','ff_file','mdp_file','software','description','reference']
        widgets = {
            'reference': autocomplete.ModelSelect2Multiple(
                url='reference-autocomplete',
                attrs={'style': 'width: 340px'},
            )
        }
        labels = {
            'reference': 'References'
        }


class ForcefieldAdminForm(forms.ModelForm):
    class Meta:
        model = Forcefield
        fields = ('__all__')
        widgets = {
            'reference': autocomplete.ModelSelect2Multiple(
                url='reference-autocomplete',
            ),
        }


class SelectForcefieldForm(forms.Form):

    software = forms.ChoiceField(choices=SFTYPE_CHOICES,
                                 required=False)
    forcefield_type = forms.ChoiceField(choices = FFTYPE_CHOICES,
                                        required=False)


