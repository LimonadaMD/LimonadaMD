from django.contrib import messages
from django.shortcuts import render, render_to_response
from django.core.urlresolvers import reverse
from django.db import IntegrityError, transaction
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic import CreateView, DetailView, DeleteView, ListView, UpdateView
from django.conf import settings
from .models import Membrane, Composition
from .forms import MembraneForm, CompositionForm, MemFormSet


class MemList(ListView):
    model = Membrane
    template_name = 'membranes/membranes.html'


def MemCreate(request):
    if request.method == 'POST':
        form = MembraneForm(request.POST, request.FILES)
        formset = MemFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            m = form.save()
            comp = [] 
            for lip in formset:
                topology = lip.cleaned_data.get('topology')
                number = lip.cleaned_data.get('number')
                side = lip.cleaned_data.get('side')
                try:
                    comp.append(Composition(membrane=m, topology=topology, number=number, side=side))
                except:
                    print("Empty composition field ...") 
            try:
                with transaction.atomic():
                    #Replace the old with the new
                    Composition.objects.filter(membrane=m).delete()
                    Composition.objects.bulk_create(comp)
                    # And notify our users that it worked
                    messages.success(request, 'You have updated your composition.')
            except IntegrityError: #If the transaction failed
                messages.error(request, 'There was an error saving your composition.')
                #return redirect(reverse('profile-settings'))
            return render(request, 'membranes/membranes.html')
    else:
        form = MembraneForm()
        formset = MemFormSet()
    return render(request, 'membranes/mem_form.html', {
        'form': form,
        'formset': formset
    })


class MemDetail(DetailView):
    model = Membrane
    template_name = 'membranes/mem_detail.html'


def MemUpdate(request, pk=None):
    m = Membrane.objects.get(pk=pk)
    if request.method == 'POST':
        form = MembraneForm(request.POST, request.FILES, instance=m)
        formset = MemFormSet(request.POST, instance=m)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            #comp = []
            #for lip in formset:
            #    topology = lip.cleaned_data.get('topology')
            #    number = lip.cleaned_data.get('number')
            #    side = lip.cleaned_data.get('side')
            #    if topology:
            #       comp.append(Composition(membrane=m, topology=topology, number=number, side=side))
            #try:
            #    with transaction.atomic():
            #      #Replace the old with the new
            #       m = Membrane.objects.get(pk=pk)
            #       Composition.objects.filter(membrane=m).delete()
            #       Composition.objects.bulk_create(comp)
            #      # And notify our users that it worked
            #       messages.success(request, 'You have updated your composition.')
            #except IntegrityError: #If the transaction failed
            #    messages.error(request, 'There was an error saving your composition.')
                #return redirect(reverse('profile-settings'))
            return render(request, 'membranes/membranes.html')
    else:
        form = MembraneForm(instance=m)
        formset = MemFormSet(instance=m)
    return render(request, 'membranes/mem_form.html', {
        'form': form,
        'formset': formset
    })


class MemDelete(DeleteView):
    model = Membrane
    template_name = 'membranes/mem_delete.html'

    def get_success_url(self):
        return reverse('memlist')


