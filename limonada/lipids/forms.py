from django import forms
from .models import Lipid, Topology
from .models import validate_lmid
from dal import autocomplete
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.forms.widgets import TextInput
from .models import validate_file_extension

class LmidForm(forms.Form):

    lmidsearch = forms.CharField(label="LM ID", 
                                 widget=TextInput(attrs={'placeholder':'e.g., LMGP01010005'}),
                                 validators=[validate_lmid])


class LipidForm(forms.ModelForm):

    name       = forms.CharField(widget=TextInput(attrs={'size': '33',
                                                         'placeholder':'e.g., POPC'}),
                                 help_text="Format: [0-9A-Z]{4}", # 1679616 possibilities 
                                 label="Name")
    lmid       = forms.CharField(label="LM ID", 
                                 widget=TextInput(attrs={'size': '33',  
                                                         'placeholder':'e.g., LMGP01010005'}),
                                 validators=[validate_lmid])
    main_class = forms.CharField(label="Main Class", 
                                 widget=TextInput(attrs={'size': '33'}))  
    sub_class  = forms.CharField(label="Sub Class", 
                                 widget=TextInput(attrs={'size': '33'}))  
    com_name   = forms.CharField(label="Common Name", 
                                 widget=TextInput(attrs={'size': '33'}))  
    sys_name   = forms.CharField(label="Systematic Name", 
                                 widget=TextInput(attrs={'size': '33'}),
                                 required=False)  
    iupac_name = forms.CharField(label="IUPAC Name", 
                                 widget=TextInput(attrs={'size': '33'}),
                                 required=False)  
    formula    = forms.CharField(label="Formula", 
                                 widget=TextInput(attrs={'size': '33'}),
                                 required=False)  
    img        = forms.ImageField(label="Picture", 
                                  widget=forms.FileInput(attrs={'accept':'.jpg,.png'}),
                                  validators=[validate_file_extension],
                                  required=False)

    class Meta:
        model = Lipid
        fields = ['name','lmid','main_class','sub_class','com_name','sys_name','iupac_name','formula','img']


#class SelectLipidForm(Form):



class TopologyForm(forms.ModelForm):
    class Meta:
        model = Topology
        fields = ['software','forcefield','lipid','itp_file','gro_file','map_file','version','description','reference']
        widgets = {
            'reference': autocomplete.ModelSelect2Multiple(
                url='reference-autocomplete'
            )
        }


#class SelectTopologyForm(Form):



