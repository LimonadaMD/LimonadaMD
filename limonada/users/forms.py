from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.forms.widgets import PasswordInput, TextInput
from django.contrib.auth.models import User


class SignUpForm(UserCreationForm):

    ACADEMIC = "AC"
    COMMERCIAL = "CO"
    UTYPE_CHOICES = (
        (ACADEMIC, 'Academic'),
        (COMMERCIAL, 'Commercial'),
    )

    utype = forms.ChoiceField(choices=UTYPE_CHOICES)
    institute = forms.CharField(max_length=200)
    position = forms.CharField(max_length=30)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'utype','institute','position',)


