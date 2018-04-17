from django import forms
from django.forms.widgets import PasswordInput, TextInput
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm


class SignUpForm(UserCreationForm):

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
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'utype','institution','position',)


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

