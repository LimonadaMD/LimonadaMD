from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.views.generic import DetailView
from .forms import UserForm, ProfileForm
from .models import Profile


def UserCreate(request):
    if request.method == 'POST':
        user_form = UserForm(request.POST)
        profile_form = ProfileForm(request.POST)
        if user_form.is_valid() and profile_form.is_valid():
            username = user_form.cleaned_data['username'] 
            user_form.save()
            user = User.objects.get(username=username)
            user.profile.utype = profile_form.cleaned_data['utype']
            user.profile.institute = profile_form.cleaned_data['institute']  
            user.profile.position = profile_form.cleaned_data['position']
            user.save()
            messages.success(request, _('Your profile was successfully updated!'))
            return render(request, 'homepage/index.html')
        else:
            messages.error(request, _('Please correct the error below.'))
    else:
        user_form = UserForm()
        profile_form = ProfileForm()
    return render(request, 'users/user_form.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })


class UserDetail(DetailView):
    model = User
    template_name = 'users/user_detail.html'


#@login_required
#@transaction.atomic
def UserUpdate(request, pk=None):
    u = User.objects.get(pk=pk)
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=u)
        profile_form = ProfileForm(request.POST, instance=u.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, _('Your profile was successfully updated!'))
            return render(request, 'homepage/index.html')
            #return redirect('settings:profile')
        else:
            messages.error(request, _('Please correct the error below.'))
    else:
        user_form = UserForm(instance=u)
        profile_form = ProfileForm(instance=u.profile)
    return render(request, 'users/user_form.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })


