#!/usr/bin/env python
# -*- coding: utf-8 -*-

from lipids.models import Lipid 
import sys, os
import shlex, subprocess
from django.conf import settings

aminoacids = [ "ARG","HIS","LYS","ASP","GLU","SER","THR","ASN","GLN","CYS","GLY","PRO","ALA","VAL","ILE","LEU","MET","PHE","TYR","TRP" ]


def Atom(a):
    # ==>   res name, atom name, res id,     atom id,       x,               y,               z
    return (a[5:10].strip(),  a[10:15].strip(),  int(a[:5]), int(a[15:20]), float(a[20:28]), float(a[28:36]), float(a[36:44]))


class Membrane:
    def __init__(self, filename=None):
        self.title   = ""
        self.natoms  = ""
        self.box     = ""
        self.prot    = False
        self.unkres  = []
        self.lipids  = {}
        self.rest    = []
        self.nblf    = ""

        lipids = Lipid.objects.all().values_list('name', flat=True)

        lines = open(filename).readlines()
        self.title   = lines[0]
        self.natoms  = lines[1] 
        self.box     = lines[-1] 
        atoms = [Atom(i) for i in lines[2:-1]]
        resatoms = []
        resid = ""
        resname = ""
        restype = ""
        for atom in atoms:
           if atom[2] != resid:
               if restype == "lipid": 
                   if resname not in self.lipids.keys():
                       self.lipids[resname] = []
                   self.lipids[resname].append(LipidRes(resatoms))
               elif resid != "":
                   self.rest.append(resatoms)
               if restype == "solvent" and len(resatoms) > 5: #once in place check with forcefield files 
                   if resname not in self.unkres:
                      self.unkres.append(resname)   
               resid = atom[2]
               resname = atom[0]
               resatoms = []
               if resname in lipids:
                   restype = "lipid"
               elif resname in aminoacids:
                   restype = "protein"
                   self.prot = True
               else:   
                   restype = "solvent" 
           resatoms.append(atom)
        if restype == "lipid":
            if resname not in self.lipids.keys():
                self.lipids[resname] = []
            self.lipids[resname].append(LipidRes(resatoms))
        else:
            self.rest.append(resatoms)


class LipidRes:
    def __init__(self, atoms=None):
        self.name    = ""
        self.leaflet = ""
        self.hgndx   = ""
        self.atoms   = []

        self.name    = atoms[0][0]
        self.hgndx   = atoms[0][3] 
        self.atoms   = atoms

        
def membraneanalysis(filename,rand):
    dirname = os.path.join(settings.MEDIA_ROOT, "tmp", rand)
    fname = os.path.splitext(filename)[0]
    ext = os.path.splitext(filename)[1]
    grofilepath = os.path.join(dirname, filename) 
    ndxfilepath = os.path.join(dirname, "%s_hg.ndx" % fname)
    fatslimfilepath = os.path.join(dirname, "%s_fatslim-hg" % fname ) 
    sortedgrofilepath = os.path.join(dirname, "%s_sorted.gro" % fname ) 

    membrane = Membrane(grofilepath)

    ndx = []
    for lipid in membrane.lipids.keys():
        for res in membrane.lipids[lipid]:
           ndx.append(res.hgndx)
    ndxfile = open(ndxfilepath,"w")
    ndxfile.write("[ headgroups ]\n")
    i = 0
    lines = ""
    for index in sorted(ndx):
        i += 1
        if i == 16:
           i = 1
           lines += "\n"
        lines += "%d " % index
    ndxfile.write(lines)
    ndxfile.close()

    env = os.environ
    env['PYTHONIOENCODING'] = 'utf-8'
    args = shlex.split("fatslim membranes --conf %s --output-index-hg %s -n %s" % (grofilepath,fatslimfilepath,ndxfilepath)) 
    process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,env=env)
    out, err = process.communicate()
    #print out
    #print err

    ndx = {}
    ndxfile = open(fatslimfilepath + "_0000.ndx").readlines()
    for line in ndxfile:
       if line[:1] == "[":
          leaflet = line.split()[1]
          ndx[leaflet] = []
       else:
          for index in line.split():
              ndx[leaflet].append(index) 

    if len(ndx.keys()) > 0:
        leaflet = ndx.keys()[0] 
        for lipid in membrane.lipids.keys():
            for i in range(len(membrane.lipids[lipid])):
                if str(membrane.lipids[lipid][i].hgndx) in ndx[leaflet]:
                    membrane.lipids[lipid][i].leaflet = "up"
    if len(ndx.keys()) > 1:
        leaflet = ndx.keys()[1] 
        for lipid in membrane.lipids.keys():
            for res in membrane.lipids[lipid]:
                if str(res.hgndx) in ndx[leaflet]:
                    res.leaflet = "lo"
    membrane.nblf = len(ndx.keys())

    compo = {}
    compo["up"] = {}
    compo["lo"] = {}
    compo["unk"] = {}
    for lipid in membrane.lipids.keys():
        nbup = 0
        nblo = 0
        nbunk = 0
        for res in membrane.lipids[lipid]:
           if res.leaflet == "up":
               nbup += 1
           elif res.leaflet == "lo":
               nblo += 1
           elif res.leaflet == "":
               nbunk += 1
        if nbup > 0:
           compo["up"][lipid] = nbup
        if nblo > 0:
           compo["lo"][lipid] = nblo
        if nbunk > 0:
           compo["unk"][lipid] = nbunk

    outfile = open(sortedgrofilepath,"w")
    outfile.write(membrane.title)
    outfile.write(membrane.natoms)
    ri = 0
    ai = 0
    for key in sorted(compo["up"], reverse=True):    
        for lipid in membrane.lipids[key]:
            if lipid.leaflet == "up":
                ri += 1
                rn = lipid.name
                for atom in lipid.atoms:
                    ai += 1
                    an = atom[1]
                    x = atom[4]
                    y = atom[5]
                    z = atom[6]
                    outfile.write("%5d%-5s%5s%5d%8.3f%8.3f%8.3f\n"%(ri,rn,an,ai,x,y,z))
    for key in sorted(compo["lo"], reverse=True):    
        for lipid in membrane.lipids[key]:
            if lipid.leaflet == "lo":
                ri += 1
                rn = lipid.name
                for atom in lipid.atoms:
                    ai += 1
                    an = atom[1]
                    x = atom[4]
                    y = atom[5]
                    z = atom[6]
                    outfile.write("%5d%-5s%5s%5d%8.3f%8.3f%8.3f\n"%(ri,rn,an,ai,x,y,z))
    for res in membrane.rest:    
        ri += 1
        for atom in res:
            ai += 1
            rn = atom[0]
            an = atom[1]
            x = atom[4]
            y = atom[5]
            z = atom[6]
            outfile.write("%5d%-5s%5s%5d%8.3f%8.3f%8.3f\n"%(ri,rn,an,ai,x,y,z))
    outfile.write(membrane.box)
    outfile.close()

    return compo, membrane


