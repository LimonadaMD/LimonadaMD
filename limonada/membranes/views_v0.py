from django.shortcuts import render, render_to_response
#from django.forms import formset_factory, inlineformset_factory
from .forms import MembraneForm, CompositionForm, MemFormSet


def membranes(request):
    return render(request, 'membranes/membranes.html')


def membrane_edit(request):
    if request.method == 'POST':
        form = MembraneForm(request.POST)
        if form.is_valid():
            form.save()
            return render(request, 'membranes/membranes.html')
    else:
        form = MembraneForm()
    return render(request, 'membranes/membrane_edit.html', {'form': form})


def MemCreate(request):
    #MemFormSet = formset_factory(CompositionForm, extra=1, can_delete=True)
    #MemFormSet = inlineformset_factory(Membrane, Composition, form=CompositionForm, extra=1)
    if request.method == 'POST':
        formset = MemFormSet(request.POST, request.FILES)
        if formset.is_valid():
            # do something with the formset.cleaned_data
            pass
    else:
        formset = MemFormSet()
    return render_to_response('membranes/mem_form.html', {'formset': formset})

