from django import forms
from django.forms.widgets import PasswordInput, TextInput, Select
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from verified_email_field.forms import VerifiedEmailField


class SignUpForm(UserCreationForm):

    ACADEMIC = "AC"
    COMMERCIAL = "CO"
    UTYPE_CHOICES = (
        (ACADEMIC, 'Academic'),
        (COMMERCIAL, 'Commercial'),
    )

    utype = forms.ChoiceField(choices=UTYPE_CHOICES)
    institution = forms.CharField(max_length=200,
                                  widget=TextInput(attrs={'class': 'form-control'}))
    position = forms.CharField(max_length=30,
                               widget=TextInput(attrs={'class': 'form-control'}))
    email = VerifiedEmailField(label='email', required=True)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'utype','institution','position',)
        widgets = {
            'username': TextInput( 
                attrs={'class': 'form-control'},
            ),
            'first_name': TextInput( 
                attrs={'class': 'form-control'},
            ),
            'last_name': TextInput( 
                attrs={'class': 'form-control'},
            ),
            #'password1': TextInput( 
            #    attrs={'class': 'form-control'},
            #),
            #'password2': TextInput( 
            #    attrs={'class': 'form-control'},
            #),
            #'utype': Select(
            #    attrs={'class': 'form-control'},
            #),
        }


class UpdateForm(forms.ModelForm):

    ACADEMIC = "AC"
    COMMERCIAL = "CO"
    UTYPE_CHOICES = (
        (ACADEMIC, 'Academic'),
        (COMMERCIAL, 'Commercial'),
    )

    utype = forms.ChoiceField(choices=UTYPE_CHOICES)
    institution = forms.CharField(max_length=200)
    position = forms.CharField(max_length=30)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'utype','institution','position',)


class LoginForm(AuthenticationForm):

    username = forms.CharField(widget=TextInput(attrs={'size': '10','placeholder':'Username'})) 
    password = forms.CharField(widget=PasswordInput(attrs={'size': '10','placeholder':'Password'}))

    class Meta:
        model = User
        fields = ('username', 'password',)

