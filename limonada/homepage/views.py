from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic import CreateView, DetailView, DeleteView, ListView, UpdateView 
from .models import Reference
from .forms import ReferenceForm


def homepage(request):

    data = { 'homepage' : True }
    return render(request, 'homepage/index.html', data)


class RefList(ListView):
    model = Reference
    template_name = 'homepage/references.html'

    def get_context_data(self, **kwargs):
        context_data = super(RefList, self).get_context_data(**kwargs)
        context_data['lipids'] = True
        return context_data


class RefCreate(CreateView):
    model = Reference
    form_class = ReferenceForm
    template_name = 'homepage/ref_form.html'

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.save()
        return HttpResponseRedirect(self.object.get_absolute_url()) 

    def get_context_data(self, **kwargs):
        context_data = super(RefCreate, self).get_context_data(**kwargs)
        context_data['lipids'] = True
        return context_data


class RefUpdate(UpdateView):
    model = Reference
    form_class = ReferenceForm
    template_name = 'homepage/ref_form.html'

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.save()
        return HttpResponseRedirect(self.object.get_absolute_url()) 
        #return reverse('refdetail', kwargs={
        #    'pk': self.object.pk,
        #})

    def get_context_data(self, **kwargs):
        context_data = super(RefUpdate, self).get_context_data(**kwargs)
        context_data['lipids'] = True
        return context_data


class RefDelete(DeleteView):
    model = Reference
    template_name = 'homepage/ref_delete.html'

    def get_success_url(self):
        return reverse('reflist')
   
    def get_context_data(self, **kwargs):
        context_data = super(RefDelete, self).get_context_data(**kwargs)
        context_data['lipids'] = True
        return context_data



