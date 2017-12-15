from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic import CreateView, DetailView, DeleteView, ListView, UpdateView
from .models import Forcefield 
from .forms import ForcefieldForm


class FfList(ListView):
    model = Forcefield
    template_name = 'forcefields/forcefields.html'

    def get_context_data(self, **kwargs):
        context_data = super(FfList, self).get_context_data(**kwargs)
        context_data['lipids'] = True
        return context_data


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

    def get_context_data(self, **kwargs):
        context_data = super(FfCreate, self).get_context_data(**kwargs)
        context_data['lipids'] = True
        return context_data


class FfDetail(DetailView):
    model = Forcefield
    template_name = 'forcefields/ff_detail.html'

    def get_context_data(self, **kwargs):
        context_data = super(FfDetail, self).get_context_data(**kwargs)
        context_data['lipids'] = True
        return context_data


class FfUpdate(UpdateView):
    model = Forcefield
    form_class = ForcefieldForm
    template_name = 'forcefields/ff_form.html'

    def form_valid(self, form):
        self.object = form.save() #commit=False)
        self.object.save()
        return HttpResponseRedirect(self.object.get_absolute_url())
        #return reverse('ffdetail', kwargs={'pk': self.object.pk,})

    def get_context_data(self, **kwargs):
        context_data = super(FfUpdate, self).get_context_data(**kwargs)
        context_data['lipids'] = True
        return context_data


class FfDelete(DeleteView):
    model = Forcefield
    template_name = 'forcefields/ff_delete.html'

    def get_success_url(self):
        return reverse('fflist')

    def get_context_data(self, **kwargs):
        context_data = super(FfDelete, self).get_context_data(**kwargs)
        context_data['lipids'] = True
        return context_data


