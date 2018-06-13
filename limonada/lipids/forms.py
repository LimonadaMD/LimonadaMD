from django import forms
from .models import Lipid, Topology
from .models import validate_lmid, validate_name
from forcefields.models import Forcefield 
from homepage.models import Reference 
from dal import autocomplete
#from django.core.exceptions import ValidationError
from django.forms import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.forms.widgets import TextInput, NumberInput, Select, Textarea
from .models import validate_file_extension
from .functions import gmxrun
from forcefields.choices import *
from django.utils.safestring import mark_safe
import os
from django.conf import settings


class LmidForm(forms.Form):

    lmidsearch = forms.CharField(label="LipidMaps ID", 
                                 widget=TextInput(attrs={'placeholder':'e.g., LMGP01010005'}),
                                 validators=[validate_lmid])


class LipidForm(forms.ModelForm):

    name       = forms.CharField(widget=TextInput(attrs={'size': '33',
                                                         'placeholder':'e.g., POPC'}),
                                 validators=[validate_name],
                                 label="Name")
    lmid       = forms.CharField(label="LM/LI ID", 
                                 widget=TextInput(attrs={'readonly':'readonly',
                                                         'class':'text-success',
                                                         'size': '33'}),
                                 validators=[validate_lmid])
    core         = forms.CharField(label="Category",
                                   widget=TextInput(attrs={'readonly':'readonly',
                                                           'size': '33'}),
                                   required=False)
    main_class   = forms.CharField(label="Main Class",
                                   widget=TextInput(attrs={'readonly':'readonly',
                                                           'size': '33'}),
                                   required=False)
    sub_class    = forms.CharField(label="Sub Class",
                                   widget=TextInput(attrs={'readonly':'readonly',
                                                           'size': '33'}),
                                   required=False)
    l4_class     = forms.CharField(label="Class Level 4",
                                   widget=TextInput(attrs={'readonly':'readonly',
                                                           'size': '33'}),
                                   required=False)
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
        fields = ['name','lmid','core','main_class','sub_class','l4_class','com_name','sys_name','iupac_name','formula','img']


class SelectLipidForm(forms.Form):

    category     = forms.ChoiceField(label="Category",  
                                     required=False)
    main_class   = forms.ChoiceField(label="Main Class",  
                                     required=False)
    sub_class    = forms.ChoiceField(label="Sub Class",
                                     required=False)
    l4_class     = forms.ChoiceField(label="Class Level 4",
                                     required=False)
    lipidid = forms.ModelMultipleChoiceField(label="Lipid",  
                                             queryset=Lipid.objects.all(),
                                             widget=autocomplete.ModelSelect2Multiple(url='lipid-autocomplete'),
                                             required=False)


class TopologyForm(forms.ModelForm):

    software     = forms.ChoiceField(choices=SFTYPE_CHOICES,
                                     initial="GR50",  
                                     widget=Select(attrs={'style': 'width: 340px'}))
    itp_file     = forms.FileField(label="Topology file")
    gro_file     = forms.FileField(label="Structure file")
    version      = forms.CharField(widget=TextInput(attrs={'style': 'width: 340px'}),
                                   help_text="Format: AuthorYear[Index]",)
    description  = forms.CharField(widget=Textarea(attrs={'style': 'width: 340px'}),
                                   required=False)  

    class Meta:
        model = Topology
        fields = ['software','forcefield','lipid','itp_file','gro_file','version','description','reference']
        widgets = {
            'lipid': autocomplete.ModelSelect2(
                url='lipid-autocomplete',
                attrs={'style': 'width: 340px'}
            ),
            'reference': autocomplete.ModelSelect2Multiple(
                url='reference-autocomplete',
                attrs={'style': 'width: 340px'}
            ),
        }
        labels = {
            'reference': 'References'
        }

    #def clean_version(self):
    #    version = self.cleaned_data['version']
    #    test = True
    #    if test:
    #        raise ValidationError('%s is not valid' % software)
    #    return version        

    def clean(self):
        cleaned_data = super(TopologyForm, self).clean()
        software = cleaned_data.get("software")
        ff = cleaned_data.get("forcefield")
        lipid = cleaned_data.get("lipid")
        version = cleaned_data.get("version")

        if lipid and ff and version:
            if Topology.objects.filter(lipid=lipid,forcefield=ff,version=version).exclude(pk=self.instance.id).exists():
                self.add_error('version', mark_safe('This version name is already taken by another topology entry for this lipid and forcefield.'))

        if lipid and ff and software and 'itp_file' in self.files and 'gro_file' in self.files:
            itp_file = self.files['itp_file']
            gro_file = self.files['gro_file']
            error, rand = gmxrun(lipid.name,ff.ff_file.url,ff.mdp_file.url,itp_file,gro_file,software)
            if error:
                #raise ValidationError('Topology file is not valid. See gromacs.log')
                logpath = "/media/tmp/%s/gromacs.log" % rand
                self.add_error('itp_file', mark_safe('Topology file is not valid. See <a class="text-success" href="%s">gromacs.log</a>' % logpath))


class TopologyAdminForm(forms.ModelForm):
    class Meta:
        model = Topology
        fields = ('__all__')
        widgets = {
            'lipid': autocomplete.ModelSelect2(
                url='lipid-autocomplete',
            ),
            'reference': autocomplete.ModelSelect2Multiple(
                url='reference-autocomplete',
            ),
        }


class SelectTopologyForm(forms.Form):

    software = forms.ChoiceField(required=False)
    forcefield = forms.ChoiceField(required=False)
    lipid = forms.ModelMultipleChoiceField(queryset=Lipid.objects.all(), 
                                           widget=autocomplete.ModelSelect2Multiple(url='lipid-autocomplete'),
                                           required=False)




