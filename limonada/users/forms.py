# -*- coding: utf-8; Mode: python; tab-width: 4; indent-tabs-mode:nil; -*-
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
#
#    Limonada is accessible at https://limonada.univ-reims.fr/
#    Copyright (C) 2016-2020 - The Limonada Team (see the AUTHORS file)
#
#    This file is part of Limonada.
#
#    Limonada is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Limonada is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Limonada.  If not, see <http://www.gnu.org/licenses/>.

# Django
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.forms.widgets import PasswordInput, Textarea, TextInput


class SignUpForm(UserCreationForm):

    ACADEMIC = 'AC'
    COMMERCIAL = 'CO'
    UTYPE_CHOICES = ((ACADEMIC, 'Academic'),
                     (COMMERCIAL, 'Commercial'))

    utype = forms.ChoiceField(choices=UTYPE_CHOICES)
    institution = forms.CharField(max_length=200,
                                  widget=TextInput(attrs={'class': 'form-control'}))
    position = forms.CharField(max_length=30,
                               widget=TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label='email',
                             max_length=200,
                             widget=TextInput(attrs={'class': 'form-control'}),
                             required=True)
    address = forms.CharField(widget=TextInput(attrs={'class': 'form-control'}),
                              required=False)
    miscellaneous = forms.CharField(widget=Textarea(attrs={'class': 'form-control'}),
                                    required=False)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'utype', 'institution',
                  'address', 'position', 'miscellaneous')
        widgets = {'username': TextInput(attrs={'class': 'form-control'}),
                   'first_name': TextInput(attrs={'class': 'form-control'}),
                   'last_name': TextInput(attrs={'class': 'form-control'})}

    def clean_email(self):
        email = self.cleaned_data.get('email')
        username = self.cleaned_data.get('username')
        if email and User.objects.filter(email=email).exclude(username=username).exists():
            raise forms.ValidationError(u'Email addresses must be unique.')
        return email


class UpdateForm(forms.ModelForm):

    ACADEMIC = 'AC'
    COMMERCIAL = 'CO'
    UTYPE_CHOICES = ((ACADEMIC, 'Academic'),
                     (COMMERCIAL, 'Commercial'))

    utype = forms.ChoiceField(choices=UTYPE_CHOICES)
    institution = forms.CharField(max_length=200,
                                  widget=TextInput(attrs={'class': 'form-control'}))
    position = forms.CharField(max_length=30,
                               widget=TextInput(attrs={'class': 'form-control'}))
    address = forms.CharField(widget=TextInput(attrs={'class': 'form-control'}),
                              required=False)
    miscellaneous = forms.CharField(widget=Textarea(attrs={'class': 'form-control'}),
                                    required=False)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'utype', 'institution', 'address', 'position',
                  'miscellaneous')
        widgets = {'first_name': TextInput(attrs={'class': 'form-control'}),
                   'last_name': TextInput(attrs={'class': 'form-control'}),
                   'email': TextInput(attrs={'class': 'form-control'})}


class LoginForm(AuthenticationForm):

    username = forms.CharField(widget=TextInput(attrs={'size': '10',
                                                       'class': 'form-control-sm',
                                                       'placeholder': 'Username'}))
    password = forms.CharField(widget=PasswordInput(attrs={'size': '10',
                                                           'class': 'form-control-sm',
                                                           'placeholder': 'Password'}))

    class Meta:
        model = User
        fields = ('username', 'password')
