from django import forms
from django.forms.widgets import TextInput
from django.forms import Form, ModelForm
from .models import Reference, validate_doi       


class DoiForm(Form):

    doisearch = forms.CharField(widget=TextInput(attrs={'placeholder':'e.g., 10.1021/jp101759q'}), 
                                label="DOI",
                                validators=[validate_doi])


class ReferenceForm(ModelForm):

    refid   = forms.CharField(widget=TextInput(attrs={'size': '33', 
                                                      'placeholder':'e.g., Klauda2010b'}),
                              help_text="Format: AuthorYear[Index]", 
                              label="Name") 
    authors = forms.CharField(widget=TextInput(attrs={'size': '33'})) #,'placeholder':''}))
    title   = forms.CharField(widget=TextInput(attrs={'size': '33'})) #,'placeholder':''}))
    journal = forms.CharField(widget=TextInput(attrs={'size': '33'})) #,'placeholder':''}))
    volume  = forms.CharField(widget=TextInput(attrs={'size': '33'}),
                              required=False) #,'placeholder':''}))
    year    = forms.CharField(widget=TextInput(attrs={'size': '33'})) #,'placeholder':''}))
    doi     = forms.CharField(widget=TextInput(attrs={'size': '33',
                                                      'placeholder':'e.g., 10.1021/jp101759q'}),
                              required=False,
                              label="DOI")

    class Meta:
        model = Reference
        fields = ['refid','authors','title','journal','volume','year','doi'] 


class SelectForm(Form):

    year = forms.CharField(widget=TextInput(attrs={'size': '4'}), 
                           label="Year")



