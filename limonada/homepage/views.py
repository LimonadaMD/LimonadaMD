from django.shortcuts import render, render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic import CreateView, DetailView, DeleteView, ListView, UpdateView 
from .models import Reference
from .forms import DoiForm, ReferenceForm, SelectForm
import json, requests, string, re


def homepage(request):

    data = { 'homepage' : True }
    return render(request, 'homepage/index.html', data)


headers = {'refid': 'asc',
           'title': 'asc',
           'year':  'asc',}

def RefList(request):

    ref_list = Reference.objects.all()

    params = request.GET.copy() 

    sort = request.GET.get('sort')
    if sort is not None:
        ref_list = ref_list.order_by(sort)
        if headers[sort] == "des":
            ref_list = ref_list.reverse()
            headers[sort] = "asc"
        else:
            headers[sort] = "des"

    per_page = 5
    if 'per_page' in request.GET.keys():
        try:
            per_page = int(request.GET['per_page'])
        except:
            per_page = 5
    paginator = Paginator(ref_list, per_page) 

    page = request.GET.get('page')
    try:
        refs = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        refs = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        refs = paginator.page(paginator.num_pages)

    form_select = SelectForm()

    data = {}
    data['form_select'] = form_select 
    data['refs'] = refs
    data['per_page'] = per_page
    data['sort'] = sort
    if sort is not None:
        data['dir'] = headers[sort] 
    data['references'] = True
    data['params'] = params

    return render_to_response('homepage/references.html', data, context_instance=RequestContext(request))


@login_required
def RefCreate(request):
    if request.method == 'POST' and 'search' in request.POST:
        form_search = DoiForm(request.POST)
        form_add = ReferenceForm()
        if form_search.is_valid():
            doi = form_search.cleaned_data['doisearch']
            url = "http://dx.doi.org/%s" % doi
            headers = {'Accept': 'application/citeproc+json'} 
            doidata = {}
            response = requests.get(url,headers=headers)
            doidata_raw = response.json() 
            if doidata_raw != []:
                if 'author' in doidata_raw.keys(): 
                    text = ""
                    for author in doidata_raw['author']:
                        text += "%s %s, " % (author["family"], author["given"])
                    doidata['authors'] = text[0:-2]
                if 'title' in doidata_raw.keys(): 
                    doidata['title'] = doidata_raw['title']
                if 'container-title' in doidata_raw.keys(): 
                    doidata['journal'] = doidata_raw['container-title']
                if 'volume' in doidata_raw.keys(): 
                    doidata['volume'] = doidata_raw['volume']
                if 'DOI' in doidata_raw.keys(): 
                    doidata['doi'] = doidata_raw['DOI']
                if 'created' in doidata_raw.keys(): 
                    if 'date-parts' in doidata_raw['created'].keys(): 
                        doidata['year'] = doidata_raw['created']['date-parts'][0][0]  
            if 'authors' in doidata.keys() and 'year' in doidata.keys():
                doidata['refid'] = "%s%s" % (doidata['authors'].split()[0],doidata['year']) 
            form_add = ReferenceForm(initial=doidata)
            return render(request, 'homepage/ref_form.html', {'form_search': form_search, 'form_add': form_add, 'references': True, 'search': True })
    elif request.method == 'POST' and 'add' in request.POST:
        form_search = DoiForm()
        form_add = ReferenceForm(request.POST)
        if form_add.is_valid():
            ref = form_add.save(commit=False)
            ref.curator = request.user 
            ref.save()
            return HttpResponseRedirect(reverse('reflist'))
    else:
        form_search = DoiForm()
        form_add = ReferenceForm()
    return render(request, 'homepage/ref_form.html', {'form_search': form_search, 'form_add': form_add, 'references': True, 'search': True})


@login_required
def RefUpdate(request, pk=None):
    if Reference.objects.filter(pk=pk).exists():
        ref = Reference.objects.get(pk=pk)
        if request.method == 'POST':
            form_add = ReferenceForm(request.POST, instance=ref)
            if form_add.is_valid():
                ref.refid   = form_add.cleaned_data['refid']
                ref.authors = form_add.cleaned_data['authors']
                ref.title   = form_add.cleaned_data['title']
                ref.journal = form_add.cleaned_data['journal']
                ref.volume  = form_add.cleaned_data['volume']
                ref.year    = form_add.cleaned_data['year']
                ref.doi     = form_add.cleaned_data['doi']    
                ref.save()
                return HttpResponseRedirect(reverse('reflist'))
        else:
            form_add = ReferenceForm(instance=ref)
        return render(request, 'homepage/ref_form.html', {'form_add': form_add, 'references': True, 'search': False})
    else:
        return HttpResponseRedirect(reverse('reflist'))


class RefDelete(DeleteView):
    model = Reference
    template_name = 'homepage/ref_delete.html'

    def get_success_url(self):
        return reverse('reflist')
   
    def get_context_data(self, **kwargs):
        context_data = super(RefDelete, self).get_context_data(**kwargs)
        context_data['references'] = True
        return context_data



