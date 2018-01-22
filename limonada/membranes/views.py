from django.conf import settings
from django.contrib import messages
from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.db import IntegrityError, transaction
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.views.generic import CreateView, DetailView, DeleteView, ListView, UpdateView
from django.contrib.auth.models import User
from .models import Membrane, Composition
from .forms import MembraneForm, CompositionForm, MemFormSet, SelectMembraneForm 
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from lipids.models import Lipid, Topology
from django.db.models import Q
import operator


def display_data(request, data, **kwargs):
    return render(request, 'membranes/posted-data.html', dict(data=data, **kwargs))


headers = {'name': 'asc',
           'equilibration':  'asc',}


def MemList(request):

    mem_list = Membrane.objects.all()

    params = request.GET.copy()

    selectparams = {}
    for param in ['equilibration','lipid']:
        if param in request.GET.keys():
            if request.GET[param] != "":
                if param == 'lipid':
                    liplist = request.GET[param].split(',')
                    selectparams['lipid'] = liplist
                else:
                    selectparams[param] = request.GET[param]
    form_select = SelectMembraneForm(selectparams)
    if form_select.is_valid():
        if 'equilibration' in selectparams.keys():
            mem_list = mem_list.filter(equilibration__gte=selectparams['equilibration'])
        if 'lipid' in selectparams.keys():
            querylist = []
            for i in liplist:
                querylist.append(Q(lipid=Lipid.objects.filter(id=i)))
            top_list = Topology.objects.filter(reduce(operator.or_, querylist))  
            mem_list = mem_list.filter(lipids=top_list)

    if 'memid' in request.GET.keys(): 
        try:
            memid = int(request.GET['memid'])
        except:
            memid = 0
        if memid > 0:
            mem_list = mem_list.filter(id=memid)

    if 'curator' in request.GET.keys():
        try:
            curator = int(request.GET['curator'])
        except:
            curator = 0
        if curator > 0:
            mem_list = mem_list.filter(curator=User.objects.filter(id=curator))

    sort = request.GET.get('sort')
    if sort is not None:
        mem_list = mem_list.order_by(sort)
        if headers[sort] == "des":
            mem_list = mem_list.reverse()
            headers[sort] = "asc"
        else:
            headers[sort] = "des"

    per_page = 4
    if 'per_page' in request.GET.keys():
        try:
            per_page = int(request.GET['per_page'])
        except:
            per_page = 4
    if per_page not in [4,10,25]:
        per_page = 4
    paginator = Paginator(mem_list, per_page)

    page = request.GET.get('page')
    try:
        membranes = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        membranes = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        membranes = paginator.page(paginator.num_pages)

    data = {}
    data['form_select'] = form_select
    data['page_objects'] = membranes
    data['per_page'] = per_page
    data['sort'] = sort
    if sort is not None:
        data['dir'] = headers[sort]
    data['membranes'] = True
    data['memcreate'] = True
    data['params'] = params
    data['comps'] = Composition.objects.all()

    return render(request, 'membranes/membranes.html', data)


@login_required
#@transaction.atomic
def MemCreate(request, formset_class, template):
    if request.method == 'POST':
        form = MembraneForm(request.POST, request.FILES)
        formset = formset_class(request.POST)
        if form.is_valid() and formset.is_valid():
            m = form.save(commit=False)
            m.curator = request.user
            m.save()
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
            return render(request, 'membranes/membranes.html', {'membranes', True})
    else:
        form = MembraneForm()
        formset = formset_class()
    return render(request, template, {
        'form': form, 
        'formset': formset,
        'membranes': True
    })


@login_required
@transaction.atomic
def MemUpdate(request, pk=None):
    m = Membrane.objects.get(pk=pk)
    if request.method == 'POST':
        form = MembraneForm(request.POST, request.FILES, instance=m)
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
            return HttpResponseRedirect(reverse('memlist'))
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
        'membranes' : True
    })


class MemDelete(DeleteView):
    model = Membrane
    template_name = 'membranes/mem_delete.html'

    def get_success_url(self):
        return reverse('memlist')

    def get_context_data(self, **kwargs):
        context_data = super(MemDelete, self).get_context_data(**kwargs)
        context_data['membranes'] = True
        return context_data

