from django import forms
#from django.forms import Form, ModelForm
from .models import Lipid, Topology
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _


class LmidForm(forms.Form):
    lmid = forms.CharField(label="LMID") 

    def clean_lmid(self):
        data = self.cleaned_data['lmid']
#        if data[0:1] != "LM":
#            raise ValidationError(_('Invalid LMID - it must start with "LM"'))
        return data      


class LipidForm(forms.ModelForm):
    class Meta:
        model = Lipid
        fields = ['name','lmid','com_name','sys_name','iupac_name','formula','main_class','sub_class','img']


class TopologyForm(forms.ModelForm):
    class Meta:
        model = Topology
        fields = ['software','forcefield','lipid','itp_file','gro_file','map_file','version','description','reference']


