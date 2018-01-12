from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DetailView
from django.shortcuts import render, redirect
from .forms import SignUpForm, UpdateForm 


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.refresh_from_db()  # load the profile instance created by the signal
            user.profile.utype = form.cleaned_data.get('utype')
            user.profile.institute = form.cleaned_data.get('institute') 
            user.profile.position = form.cleaned_data.get('position')
            user.save()
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=user.username, password=raw_password)
            login(request, user)
            messages.success(request, _('Your profile was successfully updated!'))
            return redirect('homepage')
        else:
            messages.error(request, _('Please correct the error below.'))
    else:
        form = SignUpForm()
    return render(request, 'users/signup.html', {'form': form, 'homepage': True})


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
            user.profile.institute = form.cleaned_data.get('institute') 
            user.profile.position = form.cleaned_data.get('position')
            user.save()
            messages.success(request, _('Your profile was successfully updated!'))
            return redirect('homepage')
        else:
            messages.error(request, _('Please correct the error below.'))
    else:
        if request.user.is_authenticated(): 
            instance = request.user
            utype = request.user.profile.utype 
            institute = request.user.profile.institute 
            position = request.user.profile.position 
            form = UpdateForm(instance=instance, initial={'utype': utype, 'institute': institute, 'position': position})
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




