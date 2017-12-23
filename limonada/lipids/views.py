from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic import CreateView, DetailView, DeleteView, ListView, UpdateView
from django.conf import settings
#from django.core.files.storage import FileSystemStorage
from .models import Lipid, Topology   
from .forms import LmidForm, LipidForm, TopologyForm
import json
import requests


class LipList(ListView):
    model = Lipid
    template_name = 'lipids/lipids.html'

    def get_context_data(self, **kwargs):
        context_data = super(LipList, self).get_context_data(**kwargs)
        context_data['lipids'] = True
        return context_data


def LipSearch(request):
    if request.method == 'POST':
        form = LmidForm(request.POST)
        if form.is_valid():
            lmid = form.cleaned_data['lmid']
            url = reverse('lipcreate', kwargs={'lmid': lmid})
            return HttpResponseRedirect(url)
    else:
        form = LmidForm()
    return render(request, 'lipids/lip_search.html', {'form': form, 'lipids': True})


@login_required
def LipCreate(request):
    lmid = ""
    if request.method == 'POST' and request.FILES:
        form = LipidForm(request.POST, request.FILES)
        if form.is_valid():
            name = form.cleaned_data['name']
            lmid = form.cleaned_data['lmid']
            com_name = form.cleaned_data['com_name']
            sys_name = form.cleaned_data['sys_name']
            iupac_name = form.cleaned_data['iupac_name']
            formula = form.cleaned_data['formula']
            main_class = form.cleaned_data['main_class']
            sub_class = form.cleaned_data['sub_class']
            img = form.cleaned_data['img']
            lipid = Lipid(name=name,lmid=lmid,com_name=com_name,sys_name=sys_name,iupac_name=iupac_name,formula=formula,main_class=main_class,sub_class=sub_class,img=img)
            lipid.save()
            return HttpResponseRedirect(reverse('liplist'))
    else:
        if 'lmid' in request.GET.keys():
            lm_data = {}
            lm_data['lmid'] = request.GET['lmid']
            lm_response = requests.get("http://www.lipidmaps.org/rest/compound/lm_id/%s/all/json" % lm_data['lmid'])
            lm_data_raw = lm_response.json()
            if lm_data_raw != []:
                for key in ["pubchem_cid", "name", "sys_name", "main_class", "sub_class", "core","formula","abbrev_chains"]:
                    if key == "name":
                        lm_data['com_name'] = lm_data_raw[key]
                    else:
                        lm_data[key] = lm_data_raw[key]
            if lm_data["pubchem_cid"] != "":
                try:
                    pubchem_response = requests.get("https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/%s/JSON/" % lm_data["pubchem_cid"])
                    pubchem_data_raw = pubchem_response.json()["Record"]
                    if pubchem_data_raw != []:
                        lm_data["iupac_name"] = pubchem_data_raw["Section"][2]["Section"][1]["Section"][0]["Information"][0]['StringValue']
                except KeyError:
                    pass
            form = LipidForm(initial=lm_data)
    return render(request, 'lipids/lip_form.html', {'form': form, 'lipids': True, 'lipcreate': True })


class LipDetail(DetailView):
    model = Lipid
    template_name = 'lipids/lip_detail.html'

    def get_context_data(self, **kwargs):
        slug = self.kwargs['slug']
        context_data = super(LipDetail, self).get_context_data(**kwargs)
        context_data['lipids'] = True
        context_data['tops'] = Topology.objects.filter(lipid=Lipid.objects.get(slug=slug))
        return context_data


class LipUpdate(UpdateView):
    model = Lipid
    form_class = LipidForm
    template_name = 'lipids/lip_form.html'

    def form_valid(self, form):
        self.object = form.save() 
        self.object.save()
        return HttpResponseRedirect(self.object.get_absolute_url())

    def get_context_data(self, **kwargs):
        context_data = super(LipUpdate, self).get_context_data(**kwargs)
        context_data['lipids'] = True
        context_data['lipcreate'] = False
        return context_data


class LipDelete(DeleteView):
    model = Lipid
    template_name = 'lipids/lip_delete.html'

    def get_success_url(self):
        return reverse('liplist')

    def get_context_data(self, **kwargs):
        context_data = super(LipDelete, self).get_context_data(**kwargs)
        context_data['lipids'] = True
        return context_data


class TopList(ListView):
    model = Topology
    template_name = 'lipids/topologies.html'

    def get_context_data(self, **kwargs):
        context_data = super(TopList, self).get_context_data(**kwargs)
        context_data['lipids'] = True
        return context_data


class TopCreate(CreateView):
    model = Topology
    form_class = TopologyForm
    template_name = 'lipids/top_form.html'

    def form_valid(self, form):
        self.object = form.save() 
        self.object.save()
        return HttpResponseRedirect(self.object.get_absolute_url())

    def get_context_data(self, **kwargs):
        context_data = super(TopCreate, self).get_context_data(**kwargs)
        context_data['lipids'] = True
        return context_data


class TopDetail(DetailView):
    model = Topology
    template_name = 'lipids/top_detail.html'

    def get_context_data(self, **kwargs):
        context_data = super(TopDetail, self).get_context_data(**kwargs)
        context_data['lipids'] = True
        return context_data


class TopUpdate(UpdateView):
    model = Topology
    form_class = TopologyForm
    template_name = 'lipids/top_form.html'

    def form_valid(self, form):
        self.object = form.save() 
        self.object.save()
        return HttpResponseRedirect(self.object.get_absolute_url())

    def get_context_data(self, **kwargs):
        context_data = super(TopUpdate, self).get_context_data(**kwargs)
        context_data['lipids'] = True
        return context_data


class TopDelete(DeleteView):
    model = Topology
    template_name = 'lipids/top_delete.html'

    def get_success_url(self):
        return reverse('toplist')

    def get_context_data(self, **kwargs):
        context_data = super(TopDelete, self).get_context_data(**kwargs)
        context_data['lipids'] = True
        return context_data




