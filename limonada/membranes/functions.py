# -*- coding: utf-8; Mode: python; tab-width: 4; indent-tabs-mode:nil; -*-
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
#
#    Limonada is accessible at https://www.limonadamd.eu/
#    Copyright (C) 2016-2020 - The Limonada Team (see the AUTHORS file)
#
#    This file is part of Limonada.
#
#    Limonada is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Limonada is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Limonada.  If not, see <http://www.gnu.org/licenses/>.

# standard library
import os
import shlex
import subprocess

# Django
from django.conf import settings

# Django apps
from lipids.models import Lipid

aminoacids = ['ARG', 'HIS', 'LYS', 'ASP', 'GLU', 'SER', 'THR', 'ASN', 'GLN', 'CYS', 'GLY', 'PRO', 'ALA', 'VAL', 'ILE',
              'LEU', 'MET', 'PHE', 'TYR', 'TRP', 'ACE', 'NH2']


def Atom(a):
    try:
        # ==>   res name,        atom name,        res id,     atom id,       coord
        return (a[5:10].strip(), a[10:15].strip(), int(a[:5]), int(a[15:20]), a[20:])
    except ValueError:
        return 'error'


class Membrane:
    def __init__(self, filename=None):
        self.title = ''
        self.natoms = ''
        self.box = ''
        self.lipids = {}
        self.prot = []
        self.unkres = {}
        self.solvent = []
        self.nblf = 0

        lipids = Lipid.objects.all().values_list('name', flat=True)

        atoms = []
        lines = open(filename).readlines()
        if len(lines) > 3:
            self.title = lines[0]
            self.natoms = lines[1]
            self.box = lines[-1]
            for line in lines[2:-1]:
                atoms.append(Atom(line)) 
        if len(lines) > 3 and 'error' not in atoms:
            resid = ''
            resname = ''
            restype = ''
            resatoms = []
            for atom in atoms:
                if atom[2] != resid:
                    if restype == 'lipid':
                        if resname not in self.lipids.keys():
                            self.lipids[resname] = []
                        self.lipids[resname].append(LipidRes(resatoms))
                    elif restype == 'protein':
                        self.prot.append(resatoms)
                    elif restype == 'solvent' and len(resatoms) > 5:
                        if resname not in self.unkres.keys():
                            self.unkres[resname] = []
                        self.unkres[resname].append(resatoms)
                    elif resid != '':
                        self.solvent.append(resatoms)
                    resid = atom[2]
                    resname = atom[0]
                    resatoms = []
                    if resname in lipids:
                        restype = 'lipid'
                    elif resname in aminoacids:
                        restype = 'protein'
                    else:
                        restype = 'solvent'
                resatoms.append(atom)
            if restype == 'lipid':
                if resname not in self.lipids.keys():
                    self.lipids[resname] = []
                self.lipids[resname].append(LipidRes(resatoms))
            elif restype == 'protein':
                self.prot.append(resatoms)
            elif restype == 'solvent' and len(resatoms) > 5:
                if resname not in self.unkres.keys():
                    self.unkres[resname] = []
                self.unkres[resname].append(resatoms)
            else:
                self.solvent.append(resatoms)
        else:
            self.title = 'error'


class LipidRes:
    def __init__(self, atoms=None):
        self.name = atoms[0][0]
        if atoms[0][1][0:1] != "H":
            self.hgndx = atoms[0][3]
        elif atoms[1][1][0:1] != "H":
            self.hgndx = atoms[1][3]
        elif atoms[2][1][0:1] != "H":
            self.hgndx = atoms[2][3]
        else: 
            self.hgndx = atoms[3][3]
        self.atoms = atoms
        self.leaflet = ''


def membraneanalysis(filename, rand):
    dirname = os.path.join(settings.MEDIA_ROOT, 'tmp', rand)
    fname = os.path.splitext(filename)[0]
    grofilepath = os.path.join(dirname, filename)
    ndxfilepath = os.path.join(dirname, '%s_hg.ndx' % fname)
    fatslimfilepath = os.path.join(dirname, '%s_fatslim-hg' % fname)
    sortedgrofilepath = os.path.join(dirname, '%s_sorted.gro' % fname)

    compo = {}
    compo['unk'] = {}
    membrane = Membrane(grofilepath)
    if membrane.title != 'error':
        ndx = []
        for lipid in membrane.lipids.keys():
            for res in membrane.lipids[lipid]:
                ndx.append(res.hgndx)
        ndxfile = open(ndxfilepath, 'w')
        ndxfile.write('[ headgroups ]\n')
        i = 0
        lines = ''
        for index in sorted(ndx):
            i += 1
            if i == 16:
                i = 1
                lines += '\n'
            lines += '%d ' % index
        ndxfile.write(lines)
        ndxfile.close()

        error = False
        try:
            env = os.environ
            env['PYTHONIOENCODING'] = 'utf-8'
            args = shlex.split(
                'fatslim membranes --conf %s --output-index-hg %s -n %s' % (grofilepath, fatslimfilepath, ndxfilepath))
            process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
            out, err = process.communicate()
        except OSError:
            error = True
        if not os.path.isfile(fatslimfilepath + '_0000.ndx'):
            error = True

        if not error:
            ndx = {}
            ndxfile = open(fatslimfilepath + '_0000.ndx').readlines()
            for line in ndxfile:
                if line[:1] == '[':
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
                            membrane.lipids[lipid][i].leaflet = 'up'
            if len(ndx.keys()) > 1:
                leaflet = ndx.keys()[1]
                for lipid in membrane.lipids.keys():
                    for res in membrane.lipids[lipid]:
                        if str(res.hgndx) in ndx[leaflet]:
                            res.leaflet = 'lo'
            membrane.nblf = len(ndx.keys())

            compo = {}
            compo['up'] = {}
            compo['lo'] = {}
            compo['unk'] = {}
            for lipid in membrane.lipids.keys():
                nbup = 0
                nblo = 0
                nbunk = 0
                for res in membrane.lipids[lipid]:
                    if res.leaflet == 'up':
                        nbup += 1
                    elif res.leaflet == 'lo':
                        nblo += 1
                    elif res.leaflet == 'unk':
                        nbunk += 1
                if nbup > 0:
                    compo['up'][lipid] = nbup
                if nblo > 0:
                    compo['lo'][lipid] = nblo
                if nbunk > 0:
                    compo['unk'][lipid] = nbunk

            outfile = open(sortedgrofilepath, 'w')
            outfile.write(membrane.title)
            outfile.write(membrane.natoms)
            ri = 0
            ai = 0
            for res in membrane.prot:
                ri += 1
                if ri == 100000:
                    ri = 0
                for atom in res:
                    ai += 1
                    if ai == 100000:
                        ai = 0
                    rn = atom[0]
                    an = atom[1]
                    coord = atom[4]
                    outfile.write('%5d%-5s%5s%5d%s' % (ri, rn, an, ai, coord))
            for resname in membrane.unkres.keys():
                for res in membrane.unkres[resname]:
                    ri += 1
                    if ri == 100000:
                        ri = 0
                    for atom in res:
                        ai += 1
                        if ai == 100000:
                            ai = 0
                        rn = atom[0]
                        an = atom[1]
                        coord = atom[4]
                        outfile.write('%5d%-5s%5s%5d%s' % (ri, rn, an, ai, coord))
            for leaflet in ['up','lo','unk']:
                for key in sorted(compo[leaflet], key=compo[leaflet].__getitem__, reverse=True):
                    for lipid in membrane.lipids[key]:
                        if lipid.leaflet == leaflet:
                            ri += 1
                            if ri == 100000:
                                ri = 0
                            rn = lipid.name
                            for atom in lipid.atoms:
                                ai += 1
                                if ai == 100000:
                                    ai = 0
                                an = atom[1]
                                coord = atom[4]
                                outfile.write('%5d%-5s%5s%5d%s' % (ri, rn, an, ai, coord))
            for res in membrane.solvent:
                ri += 1
                if ri == 100000:
                    ri = 0
                for atom in res:
                    ai += 1
                    if ai == 100000:
                        ai = 0
                    rn = atom[0]
                    an = atom[1]
                    coord = atom[4]
                    outfile.write('%5d%-5s%5s%5d%s' % (ri, rn, an, ai, coord))
            outfile.write(membrane.box)
            outfile.close()

    return compo, membrane
