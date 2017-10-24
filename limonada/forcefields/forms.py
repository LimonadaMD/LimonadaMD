from django import forms
from .models import Forcefield


class ForcefieldForm(forms.ModelForm):
    class Meta:
        model = Forcefield
        widgets = {
             'reference': forms.CheckboxSelectMultiple, 
        }
        fields = ['name','forcefield_type','ff_file','mdp_file','software','description','reference']




