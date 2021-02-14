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

# third-party
from dal import autocomplete

# Django
from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.generic import DetailView

# Django apps
from limonada.functions import review_notification

# local Django
from .forms import SignUpForm, UpdateForm
from .functions import account_activation_token


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.refresh_from_db()  # load the profile instance created by the signal
            user.profile.utype = form.cleaned_data.get('utype')
            user.profile.institution = form.cleaned_data.get('institution')
            user.profile.position = form.cleaned_data.get('position')
            user.profile.address = form.cleaned_data.get('address')
            user.profile.miscellaneous = form.cleaned_data.get('miscellaneous')
            user.is_active = False
            user.save()
            review_notification("creation", "users", user.pk)
            current_site = get_current_site(request)
            email = form.cleaned_data.get('email')
            subject = 'Activate your LimonadaMD account.'
            message = render_to_string('users/activation_email.html',
                                       {'user': user, 'domain': current_site.domain,
                                        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                                        'token': account_activation_token.make_token(user)})
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email, ])
            return render(request, 'users/activation_confirm.html', {'homepage': True})
    else:
        form = SignUpForm()
    return render(request, 'users/signup.html', {'form': form, 'homepage': True})


def activation(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)
        return redirect('homepage')
    else:
        return render(request, 'users/activation_invalid.html', {'homepage': True})


@login_required
def update(request):
    if request.method == 'POST':
        form = UpdateForm(request.POST)
        if form.is_valid():
            user = request.user
            user.first_name = form.cleaned_data.get('first_name')
            user.last_name = form.cleaned_data.get('last_name')
            user.email = form.cleaned_data.get('email')
            user.profile.utype = form.cleaned_data.get('utype')
            user.profile.institution = form.cleaned_data.get('institution')
            user.profile.position = form.cleaned_data.get('position')
            user.profile.address = form.cleaned_data.get('address')
            user.profile.miscellaneous = form.cleaned_data.get('miscellaneous')
            user.save()
            review_notification("update", "users", user.pk)
            return redirect('homepage')
    elif request.user.is_authenticated:
        instance = request.user
        utype = request.user.profile.utype
        institution = request.user.profile.institution
        position = request.user.profile.position
        address = request.user.profile.address
        miscellaneous = request.user.profile.miscellaneous
        form = UpdateForm(instance=instance,
                          initial={'utype': utype, 'institution': institution, 'position': position,
                                   'address': address, 'miscellaneous': miscellaneous})
    return render(request, 'users/update.html', {'form': form, 'homepage': True})


@login_required
def userinfo(request):
    return render(request, 'users/user_infos.html', {'homepage': True})


class UserDetail(DetailView):
    model = User
    template_name = 'users/user_detail.html'

    def get_context_data(self, **kwargs):
        context_data = super(UserDetail, self).get_context_data(**kwargs)
        context_data['homepage'] = True
        return context_data


class UserAutocomplete(autocomplete.Select2QuerySetView):

    def get_queryset(self):
        qs = User.objects.all()
        if self.q:
            qs = qs.filter(username__icontains=self.q)
        return qs
