from django.shortcuts import render
from django.core.urlresolvers import reverse
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


def LipSearch(request):
    if request.method == 'POST':
        form = LmidForm(request.POST)
        if form.is_valid():
            lmid = form.cleaned_data['lmid']
            url = reverse('lipcreate', kwargs={'lmid': lmid})
            return HttpResponseRedirect(url)
    else:
        form = LmidForm()
    return render(request, 'lipids/lip_search.html', {'form': form})


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
    return render(request, 'lipids/lip_form.html', {'form': form})


class LipDetail(DetailView):
    model = Lipid
    template_name = 'lipids/lip_detail.html'


class LipUpdate(UpdateView):
    model = Lipid
    form_class = LipidForm
    template_name = 'lipids/lip_form.html'

    def form_valid(self, form):
        self.object = form.save() 
        self.object.save()
        return HttpResponseRedirect(self.object.get_absolute_url())


class LipDelete(DeleteView):
    model = Lipid
    template_name = 'lipids/lip_delete.html'

    def get_success_url(self):
        return reverse('liplist')


class TopList(ListView):
    model = Topology
    template_name = 'lipids/topologies.html'


class TopCreate(CreateView):
    model = Topology
    form_class = TopologyForm
    template_name = 'lipids/top_form.html'

    def form_valid(self, form):
        self.object = form.save() 
        self.object.save()
        return HttpResponseRedirect(self.object.get_absolute_url())


class TopDetail(DetailView):
    model = Topology
    template_name = 'lipids/top_detail.html'


class TopUpdate(UpdateView):
    model = Topology
    form_class = TopologyForm
    template_name = 'lipids/top_form.html'

    def form_valid(self, form):
        self.object = form.save() 
        self.object.save()
        return HttpResponseRedirect(self.object.get_absolute_url())


class TopDelete(DeleteView):
    model = Topology
    template_name = 'lipids/top_delete.html'

    def get_success_url(self):
        return reverse('toplist')





