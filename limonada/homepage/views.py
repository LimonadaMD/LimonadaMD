from django.shortcuts import render
from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic import CreateView, DetailView, DeleteView, ListView, UpdateView 
from .models import Reference
from .forms import ReferenceForm


def homepage(request):
    return render(request, 'homepage/index.html')


class RefList(ListView):
    model = Reference
    template_name = 'homepage/references.html'


class RefCreate(CreateView):
    model = Reference
    form_class = ReferenceForm
    template_name = 'homepage/ref_form.html'

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.save()
        return HttpResponseRedirect(self.object.get_absolute_url()) 


class RefDetail(DetailView):
    model = Reference
    template_name = 'homepage/ref_detail.html'


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


class RefDelete(DeleteView):
    model = Reference
    template_name = 'homepage/ref_delete.html'

    def get_success_url(self):
        return reverse('reflist')
   

