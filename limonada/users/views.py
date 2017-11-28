from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import render, redirect
from .forms import SignUpForm 


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
        if request.user.is_authenticated(): 
            instance = request.user
            instance.last_name = "test" 
            instance.institute = "test" 
            form = SignUpForm(instance=instance)
            #form = SignUpForm(instance=request.user)
        else:
            form = SignUpForm()
    return render(request, 'users/signup.html', {'form': form, 'homepage': True})


@login_required
def userinfo(request):
    return render(request, 'users/user_detail.html', {'homepage': True})


