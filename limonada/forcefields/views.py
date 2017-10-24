from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic import CreateView, DetailView, DeleteView, ListView, UpdateView
from .models import Forcefield 
from .forms import ForcefieldForm


class FfList(ListView):
    model = Forcefield
    template_name = 'forcefields/forcefields.html'


class FfCreate(CreateView):
    model = Forcefield
    form_class = ForcefieldForm
    template_name = 'forcefields/ff_form.html'

    def form_valid(self, form):
        self.object = form.save() #commit=False)
        #refs = form.cleaned_data['reference']
        #for ref in refs:
        #    self.object.reference.add(ref)
        self.object.save()
        return HttpResponseRedirect(self.object.get_absolute_url())


class FfDetail(DetailView):
    model = Forcefield
    template_name = 'forcefields/ff_detail.html'


class FfUpdate(UpdateView):
    model = Forcefield
    form_class = ForcefieldForm
    template_name = 'forcefields/ff_form.html'

    def form_valid(self, form):
        self.object = form.save() #commit=False)
        self.object.save()
        return HttpResponseRedirect(self.object.get_absolute_url())
        #return reverse('ffdetail', kwargs={'pk': self.object.pk,})


class FfDelete(DeleteView):
    model = Forcefield
    template_name = 'forcefields/ff_delete.html'

    def get_success_url(self):
        return reverse('fflist')


