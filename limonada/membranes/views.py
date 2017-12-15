from django.conf import settings
from django.contrib import messages
from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.db import IntegrityError, transaction
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic import CreateView, DetailView, DeleteView, ListView, UpdateView
from .models import Membrane, Composition
from .forms import MembraneForm, CompositionForm, MemFormSet


def display_data(request, data, **kwargs):
    return render(request, 'membranes/posted-data.html', dict(data=data, **kwargs))


class MemList(ListView):
    model = Membrane
    template_name = 'membranes/membranes.html'

    def get_context_data(self, **kwargs):
        context_data = super(MemList, self).get_context_data(**kwargs)
        context_data['lipids'] = True
        return context_data


@login_required
#@transaction.atomic
def MemCreate(request, formset_class, template):
    if request.method == 'POST':
        form = MembraneForm(request.POST, request.FILES)
        formset = formset_class(request.POST)
        if form.is_valid() and formset.is_valid():
            m = form.save()
            #data = formset.cleaned_data
            comp = [] 
            for lip in formset:
                topology = lip.cleaned_data.get('topology')
                number = lip.cleaned_data.get('number')
                side = lip.cleaned_data.get('side')
                if topology:
                    comp.append(Composition(membrane=m, topology=topology, number=number, side=side))
            try:
                with transaction.atomic():
                    #Replace the old with the new
                    Composition.objects.filter(membrane=m).delete()
                    Composition.objects.bulk_create(comp)
                    # And notify our users that it worked
                    messages.success(request, 'You have updated your composition.')
            except IntegrityError: #If the transaction failed
                messages.error(request, 'There was an error saving your composition.')
            #return display_data(request, data)
            return render(request, 'membranes/membranes.html') #, {'lipids', True})
    else:
        form = MembraneForm()
        formset = formset_class()
    return render(request, template, {
        'form': form, 
        'formset': formset,
#        'lipids': True
    })


class MemDetail(DetailView):
    model = Membrane
    template_name = 'membranes/mem_detail.html'

    def get_context_data(self, **kwargs):
        context_data = super(MemDetail, self).get_context_data(**kwargs)
        context_data['lipids'] = True
        return context_data


@login_required
@transaction.atomic
def MemUpdate(request, pk=None):
    m = Membrane.objects.get(pk=pk)
    if request.method == 'POST':
        form = MembraneForm(request.POST, request.FILES) #, instance=m)
        formset = MemFormSet(request.POST) #, instance=m)
        if form.is_valid() and formset.is_valid():
            m = form.save()
            comp = []
            for lip in formset:
                topology = lip.cleaned_data.get('topology')
                number = lip.cleaned_data.get('number')
                side = lip.cleaned_data.get('side')
                if topology:
                   comp.append(Composition(membrane=m, topology=topology, number=number, side=side))
            try:
                with transaction.atomic():
                  #Replace the old with the new
                   m = Membrane.objects.get(pk=pk)
                   Composition.objects.filter(membrane=m).delete()
                   Composition.objects.bulk_create(comp)
                  # And notify our users that it worked
                   messages.success(request, 'You have updated your composition.')
            except IntegrityError: #If the transaction failed
                messages.error(request, 'There was an error saving your composition.')
                #return redirect(reverse('profile-settings'))
            return render(request, 'membranes/membranes.html', {'lipids': True})
    else:
        form = MembraneForm(instance=m)
        c = Composition.objects.filter(membrane=m)
        data = {
           'form-TOTAL_FORMS': len(c)+1,
           'form-INITIAL_FORMS': '0',
           'form-MAX_NUM_FORMS': '',
        }
        i = 0
        for lip in c:
           data['form-%d-topology'%(i)] = lip.topology
           data['form-%d-number'%(i)] = lip.number
           data['form-%d-side'%(i)] = lip.side
           i += 1
        formset = MemFormSet(data)
    return render(request, 'membranes/mem_form.html', {
        'form': form,
        'formset': formset,
        'lipids' : True
    })


class MemDelete(DeleteView):
    model = Membrane
    template_name = 'membranes/mem_delete.html'

    def get_success_url(self):
        return reverse('memlist')

    def get_context_data(self, **kwargs):
        context_data = super(MemDelete, self).get_context_data(**kwargs)
        context_data['lipids'] = True
        return context_data

