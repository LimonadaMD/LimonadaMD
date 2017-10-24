from django.shortcuts import render
from .forms import MembraneForm

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


