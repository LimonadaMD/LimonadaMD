from django.forms import ModelForm
from .models import Membrane, Composition


class MembraneForm(ModelForm):
    class Meta:
        model = Membrane
        fields = ['name','lipids','equilibration','mem_file','description','reference']


#class CompositionForm(ModelForm):
#    class Meta:
#        model = Composition
#        fields = ['number','side']



