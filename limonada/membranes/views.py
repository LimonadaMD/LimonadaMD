# -*- coding: utf-8 -*-
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
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from contextlib import contextmanager
import simplejson
from .models import MembraneTopol, TopolComposition, Membrane, Composition, MembraneTag
from .forms import MembraneTopolForm, MembraneForm, CompositionForm, MemFormSet, SelectMembraneForm 
from .functions import membraneanalysis 
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from homepage.models import Reference
from lipids.models import Lipid, Topology
from forcefields.models import Forcefield
from lipids.views import sf_ff_dict
from django.db.models import Q
from dal import autocomplete
import operator
import os, random
import shutil, zipfile
from django.core.files.uploadedfile import SimpleUploadedFile
from string import ascii_lowercase as abc
import codecs


def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file))


@contextmanager
def cd(newdir):
    prevdir = os.getcwd()
    os.chdir(os.path.expanduser(newdir))
    try:
        yield
    finally:
        os.chdir(prevdir)


def display_data(request, data, **kwargs):
    return render(request, 'membranes/posted-data.html', dict(data=data, **kwargs))


headers = {'name': 'asc',
           'equilibration':  'asc',}


def MemList(request):

    mem_list = MembraneTopol.objects.all()

    params = request.GET.copy()

    selectparams = {}
    for param in ['equilibration','lipid','tags','nbliptypes','nblipids']:
        if param in request.GET.keys():
            if request.GET[param] != "":
                if param == 'lipid':
                    liplist = request.GET[param].split(',')
                    selectparams['lipid'] = liplist
                if param == 'tags':
                    taglist = request.GET[param].split(',')
                    selectparams['tags'] = taglist
                else:
                    selectparams[param] = request.GET[param]
    form_select = SelectMembraneForm(selectparams)
    if form_select.is_valid():
        if 'equilibration' in selectparams.keys():
            mem_list = mem_list.filter(equilibration__gte=selectparams['equilibration'])
        if 'lipid' in selectparams.keys():
            querylist = []
            for i in liplist:
                querylist.append(Q(lipids=Lipid.objects.filter(id=i)))
            mem_list = mem_list.filter(reduce(operator.or_, querylist)).distinct()  
        if 'tags' in selectparams.keys(): 
            querylist = []
            for i in taglist:
                querylist.append(Q(membrane=Membrane.objects.filter(tag=i)))
            mem_list = mem_list.filter(reduce(operator.or_, querylist)).distinct()  
        if 'nbliptypes' in  selectparams.keys():
            mem_list = mem_list.filter(membrane=Membrane.objects.filter(nb_liptypes__gt=selectparams['nbliptypes']))
        if 'nblipids' in  selectparams.keys(): 
            mem_list = mem_list.filter(nb_lipids__gt=selectparams['nblipids'])

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

    per_page = 25
    if 'per_page' in request.GET.keys():
        try:
            per_page = int(request.GET['per_page'])
        except:
            per_page = 25
    if per_page not in [10,25,100]:
        per_page = 25
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
    data['params'] = params
    data['comps'] = Composition.objects.all()

    return render(request, 'membranes/membranes.html', data)


def formsetdata(mem_file, ff):
    fname = os.path.splitext(mem_file.name)[0]
    ext = os.path.splitext(mem_file.name)[1]
    rand = str(random.randrange(1000))
    while os.path.isdir(os.path.join(settings.MEDIA_ROOT, "tmp", rand)): 
       rand = random.randrange(1000)
    dirname = os.path.join(settings.MEDIA_ROOT, "tmp", rand)
    os.makedirs(dirname)
    fs = FileSystemStorage(location=dirname)  
    f = fs.save(mem_file.name, mem_file)

    merrors = []
    compo, membrane = membraneanalysis(mem_file.name, rand)
    if membrane.prot == True: 
        merrors.append("Upload of membranes containing proteins is not allowed at the moment.")
    if len(membrane.unkres) > 0:
        merrors.append("The following residues are not yet part of Limonada: %s." % ", ".join(membrane.unkres))
    if membrane.nblf > 2:
        merrors.append("Several membranes are present in the structure file.") 
    if len(compo["unk"].keys()) > 0 and len(membrane.unkres) == 0:
        merrors.append("Several lipids are not part of the membrane.") 

    file_data = ""
    if len(merrors) > 0:
        data = {
            'form-TOTAL_FORMS': 1,
            'form-INITIAL_FORMS': '0',
            'form-MAX_NUM_FORMS': '',
        }
    else:
        nb = len(compo["up"].keys()) + len(compo["lo"].keys())
        data = {
            'form-TOTAL_FORMS': nb+1,
            'form-INITIAL_FORMS': '0',
            'form-MAX_NUM_FORMS': '',
        }
        i = 0
        for lip in compo["up"].keys():
            lid = Lipid.objects.filter(name=lip).values_list('id', flat=True)[0]
            data['form-%d-lipid'%(i)] = lid
            data['form-%d-topology'%(i)] = ""
            if ff != "":
                if Topology.objects.filter(lipid=lid,forcefield=ff).exists():
                    topid = Topology.objects.filter(lipid=lid,forcefield=ff).values_list('id', flat=True)[0] 
                    data['form-%d-topology'%(i)] = topid
            data['form-%d-number'%(i)] = compo["up"][lip] 
            data['form-%d-side'%(i)] = "UP"
            i += 1
        for lip in compo["lo"].keys():
            lid = Lipid.objects.filter(name=lip).values_list('id', flat=True)[0]
            data['form-%d-lipid'%(i)] = lid
            data['form-%d-topology'%(i)] = ""
            if ff != "":
                if Topology.objects.filter(lipid=lid,forcefield=ff).exists():
                    topid = Topology.objects.filter(lipid=lid,forcefield=ff).values_list('id', flat=True)[0] 
                    data['form-%d-topology'%(i)] = topid
            data['form-%d-number'%(i)] = compo["lo"][lip] 
            data['form-%d-side'%(i)] = "LO"
            i += 1
        sortedgrofilepath = os.path.join(dirname, "%s_sorted.gro" % fname ) 
        if os.path.isfile(sortedgrofilepath):
            f = file("media/tmp/%s/%s_sorted.gro" % ( rand, fname ))
            file_data = {'mem_file':SimpleUploadedFile(f.name,f.read())}

    return merrors, data, file_data, rand, fname 


@login_required
#@transaction.atomic
def MemCreate(request, formset_class, template):
    rand = ""
    fname = ""
    merrors = []
    if request.method == 'POST' and 'add' in request.POST:
        topform = MembraneTopolForm(request.POST, request.FILES)
        memform = MembraneForm(request.POST)
        formset = formset_class(request.POST)
        if topform.is_valid() and memform.is_valid() and formset.is_valid():
            # Create a new MembraneTopol object
            mt = topform.save(commit=False)
            mt.curator = request.user
            mt.save()
            nb_lipids = 0 
            nb_lipup = 0 
            nb_liplo = 0 
            topcomp = []
            for lip in formset:
                lipid = lip.cleaned_data.get('lipid')
                topology = lip.cleaned_data.get('topology')
                number = lip.cleaned_data.get('number')
                side = lip.cleaned_data.get('side')
                if lipid:
                    nb_lipids += number
                    if side == "UP":
                        nb_lipup += number
                    else:
                        nb_liplo += number
                    topcomp.append(TopolComposition(membrane=mt, lipid=lipid, topology=topology, number=number, side=side))
            refs = topform.cleaned_data['reference']
            for ref in refs:
                mt.reference.add(ref)
            mt.nb_lipids = nb_lipids

            # Build a unique name based on the lipid composition
            lipupnames = {}
            lipupnumbers = {}
            liplonames = {}
            liplonumbers = {}
            liptypes = []
            for lip in formset:
                lipid = lip.cleaned_data.get('lipid')
                if lipid:
                    number = lip.cleaned_data.get('number')
                    side = lip.cleaned_data.get('side')
                    if side == "UP":
                        nb = ("%7.4f" % (100*float(number)/nb_lipup)).rstrip('0').rstrip('.') 
                        if lipid.name in lipupnames.keys(): 
                            nb = ("%7.4f" % (100*(float(number)+float(lipupnumbers[lipid.name]))/nb_lipup)).rstrip('0').rstrip('.') 
                        lipupnames[lipid.name] = "u" + lipid.name + nb 
                        lipupnumbers[lipid.name] = nb 
                    else:
                        nb = ("%7.4f" % (100*float(number)/nb_liplo)).rstrip('0').rstrip('.') 
                        if lipid.name in liplonames.keys(): 
                            nb = ("%7.4f" % (100*(float(number)+float(liplonumbers[lipid.name]))/nb_liplo)).rstrip('0').rstrip('.') 
                        liplonames[lipid.name] = "l" + lipid.name + nb 
                        liplonumbers[lipid.name] = nb 
                    if lipid not in liptypes:
                        liptypes.append(lipid) 
            name = ""
            compodata = "[ leaflet_1 ]\n"
            for key in sorted(lipupnumbers, reverse=True):
               name += "-" + lipupnames[key]
               compodata += "%10s%10s\n" % (lipupnames[key][1:5],lipupnames[key][5:])
            compodata += "\n[ leaflet_2 ]\n"
            for key in sorted(liplonumbers, reverse=True):
               name += "-" + liplonames[key]
               compodata += "%10s%10s\n" % (liplonames[key][1:5],liplonames[key][5:])

            # Create a new Membrane object if it doesn't exists
            if Membrane.objects.filter(name=name[1:]).exists():
                m = Membrane.objects.get(name=name[1:]) 
                tags = memform.cleaned_data['tag']
                for tag in tags:
                    if tag not in m.tag.all():
                        m.tag.add(tag)
                m.save()
            else:
                m = memform.save(commit=False)
                m.name = name[1:] 
                m.nb_liptypes = len(liptypes)
                m.save()
                tags = memform.cleaned_data['tag']
                for tag in tags:
                    m.tag.add(tag)
                m.save()
                comp = []
                for lip in formset:
                    lipid = lip.cleaned_data.get('lipid')
                    number = lip.cleaned_data.get('number')
                    side = lip.cleaned_data.get('side')
                    if lipid:
                        if side == "UP":
                            comp.append(Composition(membrane=m, lipid=lipid, number=100*float(number)/nb_lipup, side=side))
                        else:
                            comp.append(Composition(membrane=m, lipid=lipid, number=100*float(number)/nb_liplo, side=side))
                try:
                    with transaction.atomic():
                        Composition.objects.filter(membrane=m).delete()
                        Composition.objects.bulk_create(comp)
                        messages.success(request, 'You have updated your composition.')
                except IntegrityError:
                    messages.error(request, 'There was an error saving your composition.')

            rand = request.POST['rand']
            fname = request.POST['fname']
            mempath = "media/tmp/%s/%s_sorted.gro" % ( rand, fname )
            if not request.FILES and os.path.isfile(mempath):
                newmempath = 'media/membranes/LIM{0}_{1}.gro'.format(mt.id,mt.name) 
                shutil.copy(mempath, newmempath)
                mt.mem_file = 'membranes/LIM{0}_{1}.gro'.format(mt.id,mt.name) 
            compofile = open('media/membranes/LIM{0}_{1}.txt'.format(mt.id,mt.name),"w")
            compofile.write(compodata)
            compofile.close() 
            mt.compo_file = 'membranes/LIM{0}_{1}.txt'.format(mt.id,mt.name) 

            mt.membrane = m
            mt.save()

            if rand:
                shutil.rmtree(os.path.join(settings.MEDIA_ROOT, "tmp", rand), ignore_errors=True)

            # Create the composition objects
            try:
                with transaction.atomic():
                    TopolComposition.objects.filter(membrane=mt).delete()
                    TopolComposition.objects.bulk_create(topcomp)
                    messages.success(request, 'You have updated your composition.')
            except IntegrityError: 
                messages.error(request, 'There was an error saving your composition.')

            return HttpResponseRedirect(reverse('memlist'))
    else:
        if request.method == 'POST':
            topform = MembraneTopolForm(request.POST, request.FILES)
            memform = MembraneForm(request.POST)
            mem_file = request.FILES['mem_file']
            data = {
                'form-TOTAL_FORMS': 1,
                'form-INITIAL_FORMS': '0',
                'form-MAX_NUM_FORMS': '',
            }
            if 'forcefield' in topform.data:
                ff = topform.data['forcefield']
                merrors, data, file_data, rand, fname = formsetdata(mem_file, ff)
                if file_data != "":
                    topform = MembraneTopolForm(request.POST, file_data)
            formset = MemFormSet(data)
        else:
            topform = MembraneTopolForm()
            memform = MembraneForm()
            formset = formset_class()
    return render(request, template, {
        'topform': topform, 
        'memform': memform, 
        'formset': formset,
        'sf_ff' : sf_ff_dict(),
        'tops': Topology.objects.all(),
        'ffs' : Forcefield.objects.all(),
        'membranes': True,
        'memcreate': True,
        'merrors': merrors,
        'rand': rand,
        'fname': fname 
    })


@login_required
@transaction.atomic
def MemUpdate(request, pk=None):
    rand = ""
    fname = ""
    merrors = []
    mt = MembraneTopol.objects.get(pk=pk)
    if request.method == 'POST' and 'add' in request.POST:
        topform = MembraneTopolForm(request.POST, request.FILES, instance=mt)
        memform = MembraneForm(request.POST, instance=mt.membrane)
        formset = MemFormSet(request.POST) #, instance=m)
        if topform.is_valid() and memform.is_valid() and formset.is_valid():
            # Update the MembraneTopol object
            mt = topform.save()
            nb_lipids = 0
            nb_lipup = 0
            nb_liplo = 0
            topcomp = []
            for lip in formset:
                lipid = lip.cleaned_data.get('lipid')
                if lipid:
                    topology = lip.cleaned_data.get('topology')
                    number = lip.cleaned_data.get('number')
                    side = lip.cleaned_data.get('side')
                    if lipid:
                        nb_lipids += number
                        if side == "UP":
                            nb_lipup += number
                        else:
                            nb_liplo += number
                        topcomp.append(TopolComposition(membrane=mt, lipid=lipid, topology=topology, number=number, side=side))
            mt.nb_lipids = nb_lipids

            # Build a unique name based on the lipid composition
            lipupnames = {}
            lipupnumbers = {}
            liplonames = {}
            liplonumbers = {}
            liptypes = []
            for lip in formset:
                lipid = lip.cleaned_data.get('lipid')
                if lipid:
                    number = lip.cleaned_data.get('number')
                    side = lip.cleaned_data.get('side')
                    if side == "UP":
                        nb = ("%7.4f" % (100*float(number)/nb_lipup)).rstrip('0').rstrip('.') 
                        if lipid.name in lipupnames.keys(): 
                            nb = ("%7.4f" % (100*(float(number)+float(lipupnumbers[lipid.name]))/nb_lipup)).rstrip('0').rstrip('.') 
                        lipupnames[lipid.name] = "u" + lipid.name + nb 
                        lipupnumbers[lipid.name] = nb 
                    else:
                        nb = ("%7.4f" % (100*float(number)/nb_liplo)).rstrip('0').rstrip('.') 
                        if lipid.name in liplonames.keys(): 
                            nb = ("%7.4f" % (100*(float(number)+float(liplonumbers[lipid.name]))/nb_liplo)).rstrip('0').rstrip('.') 
                        liplonames[lipid.name] = "l" + lipid.name + nb 
                        liplonumbers[lipid.name] = nb 
                    if lipid not in liptypes:
                        liptypes.append(lipid)
            name = ""
            compodata = "[ leaflet_1 ]\n"
            for key in sorted(lipupnumbers, reverse=True):
               name += "-" + lipupnames[key]
               compodata += "%10s%10s\n" % (lipupnames[key][1:5],lipupnames[key][5:])
            compodata += "\n[ leaflet_2 ]\n"
            for key in sorted(liplonumbers, reverse=True):
               name += "-" + liplonames[key]
               compodata += "%10s%10s\n" % (liplonames[key][1:5],liplonames[key][5:])

            # Create a new Membrane object if it changed and doesn't exists
            if Membrane.objects.filter(name=name[1:]).exists():
                m = Membrane.objects.get(name=name[1:])
                tags = memform.cleaned_data['tag']
                for tag in tags:
                    if tag not in m.tag.all():
                        m.tag.add(tag)
                m.save()
            else:
                m = memform.save(commit=False)
                m.name = name[1:]
                m.nb_liptypes = len(liptypes)
                m.save()
                tags = memform.cleaned_data['tag']
                for tag in tags:
                    m.tag.add(tag)
                m.save()
                comp = []
                for lip in formset:
                    lipid = lip.cleaned_data.get('lipid')
                    if lipid:
                        number = lip.cleaned_data.get('number')
                        side = lip.cleaned_data.get('side')
                        if lipid:
                            if side == "UP":
                                comp.append(Composition(membrane=m, lipid=lipid, number=100*float(number)/nb_lipup, side=side))
                            else:
                                comp.append(Composition(membrane=m, lipid=lipid, number=100*float(number)/nb_liplo, side=side))
                try:
                    with transaction.atomic():
                        Composition.objects.filter(membrane=m).delete()
                        Composition.objects.bulk_create(comp)
                        messages.success(request, 'You have updated your composition.')
                except IntegrityError:
                    messages.error(request, 'There was an error saving your composition.')

            rand = request.POST['rand']
            fname = request.POST['fname']
            mempath = "media/tmp/%s/%s_sorted.gro" % ( rand, fname )
            if not request.FILES and os.path.isfile(mempath):
                newmempath = 'media/membranes/LIM{0}_{1}.gro'.format(mt.id,mt.name)
                shutil.copy(mempath, newmempath)
                mt.mem_file = 'membranes/LIM{0}_{1}.gro'.format(mt.id,mt.name)
            compofile = open('media/membranes/LIM{0}_{1}.txt'.format(mt.id,mt.name),"w")
            compofile.write(compodata)
            compofile.close()
            mt.compo_file = 'membranes/LIM{0}_{1}.txt'.format(mt.id,mt.name) 

            mt.membrane = m
            mt.save()

            if rand:
                shutil.rmtree(os.path.join(settings.MEDIA_ROOT, "tmp", rand), ignore_errors=True)

            # Create the composition objects
            try:
                with transaction.atomic():
                    TopolComposition.objects.filter(membrane=mt).delete()
                    TopolComposition.objects.bulk_create(topcomp)
                    messages.success(request, 'You have updated your composition.')
            except IntegrityError: 
                messages.error(request, 'There was an error saving your composition.')

            return HttpResponseRedirect(reverse('memlist'))
    else:
        if request.method == 'POST':
            topform = MembraneTopolForm(request.POST, request.FILES)
            memform = MembraneForm(request.POST)
            file_data = ""
            mem_file = request.FILES['mem_file']
            data = {
                'form-TOTAL_FORMS': 1,
                'form-INITIAL_FORMS': '0',
                'form-MAX_NUM_FORMS': '',
            }
            if 'forcefield' in topform.data:
                ff = topform.data['forcefield']
                merrors, data, file_data, rand, fname = formsetdata(mem_file, ff)
                if file_data != "":
                    topform = MembraneTopolForm(request.POST, file_data)
            formset = MemFormSet(data)
        else:
            topform = MembraneTopolForm(instance=mt)
            memform = MembraneForm(instance=mt.membrane)
            c = TopolComposition.objects.filter(membrane=mt)
            data = {
               'form-TOTAL_FORMS': len(c)+1,
               'form-INITIAL_FORMS': '0',
               'form-MAX_NUM_FORMS': '',
            }
            i = 0
            for lip in c:
               data['form-%d-lipid'%(i)] = lip.lipid
               data['form-%d-topology'%(i)] = lip.topology
               data['form-%d-number'%(i)] = lip.number
               data['form-%d-side'%(i)] = lip.side
               i += 1
            formset = MemFormSet(data)
    return render(request, 'membranes/mem_form.html', {
        'topform': topform,
        'memform': memform,
        'formset': formset,
        'sf_ff' : sf_ff_dict(),
        'tops': Topology.objects.all(),
        'ffs' : Forcefield.objects.all(),
        'membranes': True,
        'merrors': merrors,
        'rand': rand,
        'fname': fname
    })


class MemDelete(DeleteView):
    model = MembraneTopol
    template_name = 'membranes/mem_delete.html'

    def get_success_url(self):
        return reverse('memlist')

    def get_context_data(self, **kwargs):
        context_data = super(MemDelete, self).get_context_data(**kwargs)
        context_data['membranes'] = True
        return context_data


def GetLipTops(request):
    lipid_id = request.GET['lip']
    ff_id = request.GET['ff']
    topologies = []
    if lipid_id and ff_id:
        if Lipid.objects.filter(id=lipid_id).exists() and Forcefield.objects.filter(id=ff_id).exists():
            topologies = Topology.objects.filter(lipid=Lipid.objects.get(id=lipid_id),forcefield=Forcefield.objects.get(id=ff_id))
    result_set = []
    for top in topologies:
        result_set.append({'value': top.id, 'name': top.version})
    return HttpResponse(simplejson.dumps(result_set), content_type='application/json')


def GetFiles(request):
    image_data = ""
    if "memid" in request.GET.keys():
        memid = request.GET["memid"]  
        if memid != "":
            if MembraneTopol.objects.filter(id=memid).exists():
                mem = MembraneTopol.objects.get(id=memid)

                mediadir = settings.MEDIA_ROOT
                rand = str(random.randrange(1000))
                while os.path.isdir(os.path.join(mediadir, "tmp", rand)):
                   rand = random.randrange(1000)
                dirname = os.path.join(mediadir, "tmp", rand, mem.name)
                os.makedirs(dirname)
                topdir = os.path.join(dirname, "toppar")  
                os.makedirs(topdir)

                ffzip = zipfile.ZipFile(mem.forcefield.ff_file.url[1:])
                ffdir = ffzip.namelist()[0]
                ffzip.extractall(dirname)

                mdpzip = zipfile.ZipFile(mem.forcefield.mdp_file.url[1:])
                mdpzip.extractall(dirname)

                topfile = open(os.path.join(dirname,"topol.top"),"w")
                topfile.write("")
                topfile.write("#include \"%sforcefield.itp\"\n\n" % ffdir)

                shutil.copy(mem.mem_file.url[1:],dirname)
                tops = {}
                for lip in mem.topolcomposition_set.all():
                    if lip.topology.id not in tops.keys():
                        lipname = lip.lipid.name 
                        i = 0
                        while lipname in tops.values():
                            lipname = "%s%s" % (lip.lipid.name,abc[i:i+1]) 
                            i +=1
                        tops[lip.topology.id] = lipname
                        topfile.write("#include \"toppar/%s.itp\"\n" % lipname)
                    lipname = tops[lip.topology.id] 
                    if lipname == lip.lipid.name:
                        shutil.copy(lip.topology.itp_file.url[1:],topdir)
                    else:
                        infile = codecs.open(lip.topology.itp_file.url[1:], "r", encoding="utf-8")
                        filedata = infile.read()
                        infile.close()
                        newdata = filedata.replace(" %s" % lip.lipid.name,lipname)
                        newdata2 = newdata.replace("%s " % lip.lipid.name,lipname)
                        outfile = codecs.open("%s_test.itp" % os.path.join(topdir,lipname) ,'w', encoding="utf-8")
                        outfile.write(newdata2)
                        outfile.close() 
                topfile.write("\n[ system ]\n")
                topfile.write("itp test\n\n")
                topfile.write("[ molecules ]\n")
                for lip in mem.topolcomposition_set.all():
                    topfile.write("%-6s%10s\n" % (tops[lip.topology.id],lip.number))
                topfile.close()

                zipf = zipfile.ZipFile('%s.zip' % os.path.join(mediadir, "tmp", rand, mem.name), 'w', zipfile.ZIP_DEFLATED)
                with cd(os.path.join(mediadir, "tmp", rand)):
                    zipdir(mem.name, zipf)
                    image_data = open('%s.zip' % mem.name, "rb").read() 
                zipf.close()

                shutil.rmtree(os.path.join(mediadir, "tmp", rand), ignore_errors=True)

    response = HttpResponse(image_data, content_type="text/plain")
    response['Content-Disposition'] = 'attachment; filename=%s.zip' % mem.name 
    return response


class MembraneTagAutocomplete(autocomplete.Select2QuerySetView):

    def get_queryset(self):
        qs = MembraneTag.objects.all()
        if self.q:
            qs = qs.filter(tag__icontains=self.q)
        return qs


