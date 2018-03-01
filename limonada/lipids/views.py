from django.contrib.auth.models import User
from django.shortcuts import render
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.core.files import File
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic import CreateView, DetailView, DeleteView, ListView, UpdateView, FormView
from django.conf import settings
from django.utils.text import slugify
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.contrib.auth.models import User
import operator
from .models import Lipid, Topology   
from .forms import LmidForm, LipidForm, SelectLipidForm, TopologyForm, SelectTopologyForm  
from membranes.models import MembraneTopol, Membrane 
from homepage.models import Reference
from forcefields.models import Forcefield
from dal import autocomplete
import json, os, os.path, time, shutil
import requests
import shlex, subprocess
from django.core.files.uploadedfile import SimpleUploadedFile
from forcefields.choices import *
import simplejson as json


def molsize(filename):
    mol = open("%s.mol" % filename).readlines()
    rotmol = open("%s_rot.mol" % filename,"w") 
    for j in range(0,4):
        rotmol.write(mol[j])
    X = []
    Y = []
    nb = int(mol[3][0:3])
    for j in range(4,nb+4):
        X.append(float(mol[j].split()[0]))
        Y.append(float(mol[j].split()[1]))
        rotmol.write(" %s%s %s" % (mol[j][11:20],mol[j][0:10],mol[j][21:]))
    for line in mol[j+1:]:
        rotmol.write("%s" % line)
    rotmol.close()
    R = (max(Y)-min(Y)) / (max(X)-min(X))
    return R


def LM_class():
    LM_dict = {}
    LM_class = {'category':[]}
    for line in open("media/Lipid_Classification").readlines():
        name = line.split("[")[1].split("]")[0]
        line = line.strip()
        l = len(name) 
        LM_dict[name] = line 
        if l == 2:
            LM_class['category'].append([name,line]) 
        elif l == 4: 
            if name[0:2] not in LM_class.keys(): 
                LM_class[name[0:2]] = []
            LM_class[name[0:2]].append([name,line]) 
        elif l == 6: 
            if name[0:4] not in LM_class.keys(): 
                LM_class[name[0:4]] = []
            LM_class[name[0:4]].append([name,line]) 
        elif l == 8: 
            if name[0:6] not in LM_class.keys(): 
                LM_class[name[0:6]] = []
            LM_class[name[0:6]].append([name,line]) 
    return LM_class, LM_dict


def LI_index():
    lmclass, lmdict = LM_class() 
    liindex = {}
    liid = []
    if Lipid.objects.filter(lmid__istartswith="LI").exists():
        for i in Lipid.objects.filter(lmid__istartswith="LI").values_list('lmid', flat=True):
           liid.append(i)
    for grp in lmdict.keys():
        if grp not in lmclass.keys(): 
            l = len(grp)
            for lipid in liid:
                if lipid[2:l+2] == grp:
                   if grp in liindex.keys():
                       if int(liindex[grp][l+2:]) <= int(lipid[l+2:]): 
                           liindex[grp] = "LI%s%04d" % (grp,int(lipid[l+2:])+1) 
                       liid.remove(lipid)
                   else: 
                       liindex[grp] = "LI%s%04d" % (grp,int(lipid[l+2:])+1) 
                       liid.remove(lipid)
            if grp not in liindex.keys(): 
                liindex[grp] = "LI%s%04d" % (grp,1)
    return liindex


def sf_ff_dict():
    sf_ff = {}
    for ff in Forcefield.objects.values_list('software', 'id', 'name'):
        if ff[0] not in sf_ff.keys():
            sf_ff[ff[0].encode("utf-8")] = []
        sf_ff[ff[0].encode("utf-8")].append([ff[1],ff[2].encode("utf-8")]) 
    return sf_ff


lipheaders = {'name': 'asc',
              'lmid': 'asc',
              'com_name': 'asc',
              'sys_name':  'asc',}


def LipList(request):

    lmclass, lmdict = LM_class() 

    lipid_list = Lipid.objects.all()

    params = request.GET.copy()

    selectparams = {}
    for param in ['category','main_class','sub_class','l4_class','lipidid']:
        if param in request.GET.keys():
            if request.GET[param] != "":
                if param == 'lipidid':
                    liplist = request.GET[param].split(',')
                    selectparams['lipidid'] = liplist
                else:
                    selectparams[param] = request.GET[param]
    if 'category' in selectparams.keys():
        lipid_list = lipid_list.filter(core=lmdict[selectparams['category']])
    if 'main_class' in selectparams.keys():
        lipid_list = lipid_list.filter(main_class=lmdict[selectparams['main_class']])
    if 'sub_class' in selectparams.keys():
        lipid_list = lipid_list.filter(sub_class=lmdict[selectparams['sub_class']])
    if 'l4_class' in selectparams.keys():
        lipid_list = lipid_list.filter(l4_class=lmdict[selectparams['l4_class']])
    if 'lipidid' in selectparams.keys(): 
        form_select = SelectLipidForm({'lipidid':selectparams['lipidid']})
        if form_select.is_valid():
            querylist = []
            for i in liplist:
                querylist.append(Q(id=i))
            lipid_list = lipid_list.filter(reduce(operator.or_, querylist))
    else:
        form_select = SelectLipidForm()

    sort = request.GET.get('sort')
    if sort is not None:
        lipid_list = lipid_list.order_by(sort)
        if lipheaders[sort] == "des":
            lipid_list = lipid_list.reverse()
            lipheaders[sort] = "asc"
        else:
            lipheaders[sort] = "des"

    per_page = 4
    if 'per_page' in request.GET.keys():
        try:
            per_page = int(request.GET['per_page'])
        except:
            per_page = 4
    if per_page not in [4,10,25]:
        per_page = 4
    paginator = Paginator(lipid_list, per_page)

    page = request.GET.get('page')
    try:
        lipids = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        lipids = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        lipids = paginator.page(paginator.num_pages)

    data = {}
    data['form_select'] = form_select
    data['page_objects'] = lipids
    data['per_page'] = per_page
    data['sort'] = sort
    if sort is not None:
        data['dir'] = lipheaders[sort]
    data['lipids'] = True
    data['params'] = params

    return render(request,'lipids/lipids.html', data)


@login_required
def LipCreate(request):
    liindex = LI_index()
    if request.method == 'POST' and 'search' in request.POST:
        form_search = LmidForm(request.POST)
        form_add = LipidForm()
        if form_search.is_valid():
            lm_data = {}
            lm_data['lmid'] = form_search.cleaned_data['lmidsearch']
            lm_response = requests.get("http://www.lipidmaps.org/rest/compound/lm_id/%s/all/json" % lm_data['lmid'])
            lm_data_raw = lm_response.json()
            for key in ["pubchem_cid", "name", "sys_name","formula","abbrev_chains"]:
                if key == "name" and 'name' in lm_data_raw.keys():
                    lm_data['com_name'] = lm_data_raw[key]
                elif key in lm_data_raw.keys():
                    lm_data[key] = lm_data_raw[key]
            filename = "media/tmp/%s" % lm_data['lmid']
            url = "http://www.lipidmaps.org/data/LMSDRecord.php?Mode=File&LMID=%s" % lm_data['lmid']
            response = requests.get(url)
            with open("%s.mol" % filename, 'wb') as f:
                f.write(response.content)
            f.close()
            R = molsize(filename)
            if R < 1:
                shutil.copy("%s_rot.mol" % filename, "%s.mol" % filename)
            args = shlex.split("obabel %s.mol -O %s.png -xC -xh 1200 -xw 1000 -x0 molfile -xd --title" % (filename,filename))
            process = subprocess.Popen(args, stdout=subprocess.PIPE)
            process.communicate()
            lipid = Lipid(name="temp", lmid=lm_data['lmid'], com_name=lm_data['com_name'], img="tmp/%s.png" % lm_data['lmid'])
            file_data = { 'img': lipid.img }
            if os.path.isfile("%s_rot.mol" % filename): 
                os.remove("%s_rot.mol" % filename)
            if os.path.isfile("%s.mol" % filename): 
                os.remove("%s.mol" % filename)
            if lm_data["pubchem_cid"] != "":
                try:
                    pubchem_response = requests.get("https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/%s/JSON/" % lm_data["pubchem_cid"])
                    pubchem_data_raw = pubchem_response.json()["Record"]
                    if pubchem_data_raw != []:
                        for s1 in pubchem_data_raw["Section"]: 
                            if s1["TOCHeading"] == "Names and Identifiers":
                                for s2 in s1["Section"]: 
                                    if s2["TOCHeading"] == "Computed Descriptors":
                                        for s3 in s2["Section"]: 
                                            if s3["TOCHeading"] == "IUPAC Name":
                                                lm_data["iupac_name"] = s3["Information"][0]['StringValue']
                                    if s2["TOCHeading"] == "Synonyms":
                                        for s3 in s2["Section"]: 
                                            if s3["TOCHeading"] == "Depositor-Supplied Synonyms":
                                                nb = len(s3["Information"][0]['StringValueList'])
                                                for i in range(nb):
                                                    if len(s3["Information"][0]['StringValueList'][nb-1-i]) == 4:
                                                        lm_data["name"] = s3["Information"][0]['StringValueList'][nb-1-i]   
                except KeyError:
                    pass
            form_add = LipidForm(lm_data, file_data)
            return render(request, 'lipids/lip_form.html', {'form_search': form_search, 'form_add': form_add, 'lipids': True, 'search': True, 'imgpath': "tmp/%s.png" % lm_data['lmid'] })
    elif request.method == 'POST' and 'add' in request.POST:
        lmclass, lmdict = LM_class() 
        form_search = LmidForm()
        form_add = LipidForm(request.POST, request.FILES)
        if form_add.is_valid():
            lipid = form_add.save(commit=False)
            name = form_add.cleaned_data['name']
            lmid = form_add.cleaned_data['lmid']
            com_name = form_add.cleaned_data['com_name']
            lipid.search_name = '%s - %s - %s' % (name,lmid,com_name)
            core = form_add.cleaned_data['core']
            main_class = form_add.cleaned_data['main_class']
            sub_class = form_add.cleaned_data['sub_class']
            l4_class = form_add.cleaned_data['l4_class']
            lipid.core = lmdict[core]
            lipid.main_class = lmdict[main_class]
            if sub_class != "": 
                lipid.sub_class = lmdict[sub_class]
            if l4_class != "": 
                lipid.l4_class = lmdict[l4_class]
            imgpath = "media/tmp/%s.png" % lmid 
            if not request.FILES and os.path.isfile(imgpath):
                shutil.copy(imgpath, "media/lipids/%s.png" % lmid) 
                lipid.img = "lipids/%s.png" % lmid 
            if os.path.isfile(imgpath):
                os.remove(imgpath)
            lipid.slug = slugify('%s' % (lmid), allow_unicode=True)
            lipid.curator = request.user
            lipid.save()
            return HttpResponseRedirect(reverse('liplist'))
    else:
        form_search = LmidForm()
        form_add = LipidForm()
    return render(request, 'lipids/lip_form.html', {'form_search': form_search, 'form_add': form_add, 'lipids': True, 'search': True, 'liindex': liindex })


@login_required
def LipUpdate(request, slug=None):
    if Lipid.objects.filter(slug=slug).exists():
        lipid = Lipid.objects.get(slug=slug)
        if request.method == 'POST':
            form_add = LipidForm(request.POST, request.FILES, instance=lipid)
            if form_add.is_valid():
                lipid = form_add.save(commit=False)
                name = form_add.cleaned_data['name']
                lmid = form_add.cleaned_data['lmid']
                com_name = form_add.cleaned_data['com_name']
                lipid.search_name = '%s - %s - %s' % (name,lmid,com_name)
                lipid.slug = slugify('%s' % (lmid), allow_unicode=True)
                lipid.save()
                return HttpResponseRedirect(reverse('liplist'))
        else:
            form_add = LipidForm(instance=lipid)
        return render(request, 'lipids/lip_form.html', {'form_add': form_add, 'lipids': True, 'search': False})
    else:
        return HttpResponseRedirect(reverse('liplist'))


class LipDetail(DetailView):
    model = Lipid
    template_name = 'lipids/lip_detail.html'

    def get_context_data(self, **kwargs):
        slug = self.kwargs['slug']
        context_data = super(LipDetail, self).get_context_data(**kwargs)
        context_data['lipids'] = True
        context_data['tops'] = Topology.objects.filter(lipid=Lipid.objects.get(slug=slug))
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


class LipAutocomplete(autocomplete.Select2QuerySetView):

    def get_queryset(self):
        qs = Lipid.objects.all()
        if self.q:
            qs = qs.filter(search_name__icontains=self.q)
        return qs


topheaders = {'software'  : 'asc',
              'forcefield': 'asc',
              'lipid'     : 'asc',
              'version'   : 'asc',}


def TopList(request):

    top_list = Topology.objects.all()

    params = request.GET.copy()

    selectparams = {} 
    for param in ['software','forcefield','lipid']:  
        if param in request.GET.keys():
            if request.GET[param] != "":
                if param == 'lipid':
                    liplist = request.GET[param].split(',')
                    selectparams['lipid'] = liplist 
                else:
                    selectparams[param] = request.GET[param] 
    if 'software' in selectparams.keys(): 
        top_list = top_list.filter(software=selectparams['software'])
    if 'forcefield' in selectparams.keys(): 
        top_list = top_list.filter(forcefield=Forcefield.objects.filter(id=selectparams['forcefield']))
    if 'lipid' in selectparams.keys(): 
        form_select = SelectTopologyForm({'lipid':selectparams['lipid']})
        if form_select.is_valid():
            querylist = [] 
            for i in liplist: 
                querylist.append(Q(lipid=Lipid.objects.filter(id=i)))
            top_list = top_list.filter(reduce(operator.or_, querylist))
    else:
        form_select = SelectTopologyForm()

    if 'topid' in request.GET.keys():
        try:
            topid = int(request.GET['topid'])
        except:
            topid = 0
        if topid > 0:
            top_list = top_list.filter(id=topid)

    if 'curator' in request.GET.keys():
        try:
            curator = int(request.GET['curator'])
        except:
            curator = 0
        if curator > 0:
            top_list = top_list.filter(curator=User.objects.filter(id=curator))

    sort = request.GET.get('sort')
    if sort is not None:
        top_list = top_list.order_by(sort)
        if topheaders[sort] == "des":
            top_list = top_list.reverse()
            topheaders[sort] = "asc"
        else:
            topheaders[sort] = "des"

    per_page = 4
    if 'per_page' in request.GET.keys():
        try:
            per_page = int(request.GET['per_page'])
        except:
            per_page = 4
    if per_page not in [4,10,25]:
        per_page = 4
    paginator = Paginator(top_list, per_page)

    page = request.GET.get('page')
    try:
        topologies = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        topologies = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        topologies = paginator.page(paginator.num_pages)

    data = {}
    data['form_select'] = form_select
    data['page_objects'] = topologies
    data['per_page'] = per_page
    data['sort'] = sort
    if sort is not None:
        data['dir'] = topheaders[sort]
    data['topologies'] = True
    data['sfchoices'] = SFTYPE_CHOICES
    data['params'] = params
    data['memtops'] = MembraneTopol.objects.all()
    data['mems'] = Membrane.objects.all()

    return render(request, 'lipids/topologies.html', data)


class TopCreate(CreateView):
    model = Topology
    form_class = TopologyForm
    template_name = 'lipids/top_form.html'

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.curator = self.request.user
        self.object.save()
        refs = form.cleaned_data['reference']
        for ref in refs:
            self.object.reference.add(ref)
        return HttpResponseRedirect(self.object.get_absolute_url())

    def get_context_data(self, **kwargs):
        context_data = super(TopCreate, self).get_context_data(**kwargs)
        context_data['ffs'] = Forcefield.objects.all()
        context_data['sf_ff'] = sf_ff_dict() 
        context_data['topologies'] = True
        context_data['topcreate'] = True
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
        context_data['ffs'] = Forcefield.objects.all()
        context_data['sf_ff'] = sf_ff_dict() 
        context_data['topologies'] = True
        return context_data


class TopDelete(DeleteView):
    model = Topology
    template_name = 'lipids/top_delete.html'

    def get_success_url(self):
        return reverse('toplist')

    def get_context_data(self, **kwargs):
        context_data = super(TopDelete, self).get_context_data(**kwargs)
        context_data['topologies'] = True
        return context_data


