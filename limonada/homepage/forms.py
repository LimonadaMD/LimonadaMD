from django import forms
from django.forms.widgets import TextInput, Textarea
from django.forms import Form, ModelForm
from dal import autocomplete
from .models import Reference, validate_doi, validate_year       


class DoiForm(Form):

    doisearch = forms.CharField(widget=TextInput(attrs={'placeholder':'e.g., 10.1021/jp101759q'}), 
                                label="DOI",
                                validators=[validate_doi])


class ReferenceForm(ModelForm):

    refid   = forms.CharField(widget=TextInput(attrs={'size': '33', 
                                                      'placeholder':'e.g., Klauda2010b'}),
                              help_text="Format: AuthorYear[Index]", 
                              label="Name") 
    authors = forms.CharField(widget=TextInput(attrs={'size': '33'})) 
    title   = forms.CharField(widget=TextInput(attrs={'size': '33'})) 
    journal = forms.CharField(widget=TextInput(attrs={'size': '33'})) 
    volume  = forms.CharField(widget=TextInput(attrs={'size': '33'}),
                              required=False) 
    year    = forms.CharField(widget=TextInput(attrs={'size': '33'})) 
    doi     = forms.CharField(widget=TextInput(attrs={'size': '33',
                                                      'placeholder':'e.g., 10.1021/jp101759q'}),
                              required=False,
                              label="DOI")

    class Meta:
        model = Reference
        fields = ['refid','authors','title','journal','volume','year','doi'] 


class SelectForm(Form):

    year = forms.IntegerField(validators=[validate_year],
                              widget=TextInput(attrs={'size': '10'}), 
                              label="Year")


class MailForm(Form):

    subject  = forms.CharField(widget=TextInput(attrs={'size': '37'}),
                               required=False)
    comment  = forms.CharField(widget=Textarea(),
                               required=False)
    curation = forms.BooleanField(required=False,
                                  label="Request to become the new curator:")


