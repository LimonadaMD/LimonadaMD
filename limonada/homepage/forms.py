from django.forms import ModelForm
from .models import Reference       

class ReferenceForm(ModelForm):
    class Meta:
        model = Reference
        fields = ['authors','title','journal','num','pages','year','doi']


