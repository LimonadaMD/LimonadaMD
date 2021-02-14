# -*- coding: utf-8; Mode: python; tab-width: 4; indent-tabs-mode:nil; -*-
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
#
#    Limonada is accessible at https://limonada.univ-reims.fr/
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
import glob
import os
import random
import re
import shlex
import shutil
import subprocess
import tempfile
import zipfile
from contextlib import contextmanager

# Django
from django.conf import settings
from django.core.files.storage import FileSystemStorage


def Atom(a, extension, i):
    if extension == ".gro":
        try:
            # ==>   res name,        atom name,        res id,     atom id,       coord   atom index
            return (a[5:10].strip(), a[10:15].strip(), int(a[:5]), int(a[15:20]), a[20:], i)
        except ValueError:
            return 'error'
    elif extension == ".pdb":
        try:
            # ==>   res name,         atom name,        res id,        atom id,      coord
            return (a[17:21].strip(), a[11:16].strip(), int(a[22:26]), int(a[6:11]), a[30:], i)
        except ValueError:
            return 'error'


@contextmanager
def cd(newdir):
    """When combines with a "with" statement, it allows to change the working directory for the time of the "with"
       before going back to the previous working directory.

    Parameters
    ----------
    newdir : string
        defines the temporary working directory.
    """
    prevdir = os.getcwd()
    os.chdir(os.path.expanduser(newdir))
    try:
        yield
    finally:
        os.chdir(prevdir)


def residuetypes():
    """Limonada is mainly about lipids but membranes are also composed of other molecules like proteins or solvent.
       Identification of molecule types is based on the 'residuetypes.dat' file, a file primarily defined in the
       gromacs suite.

    Returns
    -------
    residues: dict of strings
        keywords are [Protein, DNA, RNA, Water, Ion] and values are the residues name.
    """
    residuefile = open(os.path.join(settings.MEDIA_ROOT, 'residuetypes.dat')).readlines()
    residues = {}
    for line in residuefile:
        residues[line.split()[0]] = line.split()[1]
    return residues


def gmxrun(lipname, ff_file, itp_file, gro_file, software):
    """When lipid topologies are added to the database through the "Topologies" form, the files consistency is
       first checked by running a small minimisation simulation. If error occurs, a log file named "gromacs.log" is
       created and the user has access to this file. The simulation is processed in a temporary directory. If an
       an error occurs, this directory is kept to let the user having access to the "gromacs.log" file.

    Parameters
    ----------
    lipname: string
        Lipid names (4 digits) have to be the same in the database and in the topology (itp) and structure files (gro).
    ff_file: string
        Pathway to the zip file containing the forcefield directory
    itp_file: file
        File object uploaded by the user for the topology file
    gro_file: file
        File object uploaded by the user for the structure file
    software: string
        4 digit acronym representing the software version to use for the simulation

    Returns
    -------
    error: bool
        True if errors occured
    rand: int
        Allow to reconstruct th path to the directory where the "gromacs.log" file has been created.
    """
    mediadir = settings.MEDIA_ROOT
    softpath = {'GR33': settings.GROMACS_33_PATH, 'GR40': settings.GROMACS_40_PATH, 'GR45': settings.GROMACS_45_PATH,
                'GR46': settings.GROMACS_46_PATH, 'GR50': settings.GROMACS_50_PATH, 'GR51': settings.GROMACS_51_PATH,
                'GR16': settings.GROMACS_16_PATH}
    softdir = softpath[software]
    installed = True
    if software in ['GR51', 'GR16', 'GR18']:
        if not os.path.isfile(os.path.join(softdir, 'gmx')):
            installed = False
    else:
        if not os.path.isfile(os.path.join(softdir, 'grompp')):
            installed = False

    rand = str(random.randrange(1000))
    while os.path.isdir(os.path.join(mediadir, 'tmp', rand)):
        rand = str(random.randrange(1000))

    error = False
    if installed:
        dirname = os.path.join(mediadir, 'tmp', rand)
        os.makedirs(dirname)

        ffzip = zipfile.ZipFile('%s%s' % (settings.BASE_DIR, ff_file))
        ffdir = os.path.join(dirname, ffzip.namelist()[0])
        ffzip.extractall(dirname)

        if software == 'GR40':
            copydir = ffdir
        else:
            copydir = dirname

        shutil.copy('media/em.mdp', copydir)

        fs = FileSystemStorage(location=copydir)
        fs.save('%s.itp' % lipname, itp_file)
        strext = os.path.splitext(gro_file.name)[1]
        fs.save('%s%s' % (lipname, strext), gro_file)

        topfile = open(os.path.join(copydir, 'topol.top'), 'w')
        topfile.write('')
        topfile.write('#include "%sforcefield.itp"\n\n' % ffdir)
        topfile.write('#include "./%s.itp"\n\n' % lipname)
        topfile.write('[ system ]\n')
        topfile.write('itp test\n\n')
        topfile.write('[ molecules ]\n')
        topfile.write('%s          1' % lipname)
        topfile.close()

        with cd(copydir):
            try:
                if software in ['GR51', 'GR16', 'GR18']:
                    args = shlex.split('%sgmx editconf -f %s%s -o box.gro -d 5' % (softdir, lipname, strext))
                else:
                    args = shlex.split('%seditconf -f %s%s -o box.gro -d 5' % (softdir, lipname, strext))
                process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                out, err = process.communicate()
            except OSError:
                err = 'editconf has failed or has not been found.'
            if os.path.isfile('box.gro'):
                try:
                    if software in ['GR51', 'GR16', 'GR18']:
                        args = shlex.split('%sgmx grompp -f em.mdp -p topol.top -c %s%s -o em.tpr' % (softdir, lipname,
                                                                                                      strext))
                    else:
                        args = shlex.split('%sgrompp -f em.mdp -p topol.top -c %s%s -o em.tpr' % (softdir, lipname,
                                                                                                  strext))
                    process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    out, err = process.communicate()
                except OSError:
                    err = 'grompp has failed or has not been found.'
            if not os.path.isfile('em.tpr'):
                error = True
                errorfile = open('gromacs.log', 'wb')
                errorfile.write(err)
                errorfile.close()
            if not error:
                if software in ['GR51', 'GR16', 'GR18']:
                    args = shlex.split('%sgmx mdrun -v -deffnm em' % softdir)
                else:
                    args = shlex.split('%smdrun -v -deffnm em' % softdir)
                process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                out, err = process.communicate()
                if not os.path.isfile('em.gro'):
                    error = True
                    errorfile = open('gromacs.log', 'wb')
                    errorfile.write(err)
                    errorfile.close()
        if not error:
            shutil.rmtree(dirname, ignore_errors=True)

    return error, rand


def charmmrun(lipname, ff_file, str_file, pdb_file, software):
    """When lipid topologies are added to the database through the "Topologies" form, the files consistency is
       first checked by running a small minimisation simulation. If error occurs, a log file named "charmm.log" is
       created and the user has access to this file. The simulation is processed in a temporary directory. If an
       an error occurs, this directory is kept to let the user having access to the "charmm.log" file.

    Parameters
    ----------
    lipname: string
        Lipid names (4 digits) have to be the same in the database and in the topology (str) and structure files (pdb).
    ff_file: string
        Pathway to the zip file containing the forcefield directory
    str_file: file
        File object uploaded by the user for the topology file
    pdb_file: file
        File object uploaded by the user for the structure file
    software: string
        4 digit acronym representing the software version to use for the simulation

    Returns
    -------
    error: bool
        True if errors occured
    rand: int
        Allow to reconstruct th path to the directory where the "charmm.log" file has been created.
    """
    mediadir = settings.MEDIA_ROOT
    softpath = {'CH42': settings.CHARMM_42_PATH}
    softdir = softpath[software]
    installed = True
    if not os.path.isfile(os.path.join(softdir, 'charmm')):
        installed = False

    rand = str(random.randrange(1000))
    while os.path.isdir(os.path.join(mediadir, 'tmp', rand)):
        rand = str(random.randrange(1000))

    error = False
    if installed:
        dirname = os.path.join(mediadir, 'tmp', rand)
        os.makedirs(dirname)

        ffzip = zipfile.ZipFile('%s%s' % (settings.BASE_DIR, ff_file))
        ffzip.extractall(dirname)

        fs = FileSystemStorage(location=dirname)
        fs.save('%s.str' % lipname, str_file)
        strext = os.path.splitext(pdb_file.name)[1]
        fs.save('%s%s' % (lipname, strext), pdb_file)

        with cd(dirname):
            setupfile = open('setup.inp', 'w')
            setupfile.write('stream "toppar.str"\n')
            setupfile.write('stream "%s.str"\n' % lipname)
            setupfile.write('open unit 1 card read name "%s.pdb"\n' % lipname)
            setupfile.write('read sequ pdb unit 1\n')
            setupfile.write('bomlev -1\n')
            setupfile.write('generate "%s"\n' % lipname)
            setupfile.write('bomlev 0\n')
            setupfile.write('rewind unit 1\n')
            setupfile.write('read coor pdb unit 1\n')
            setupfile.write('close unit 1\n')
            setupfile.write('write psf card name "%s.psf"\n' % lipname)
            setupfile.write('write coor card name "%s.crd"\n' % lipname)
            setupfile.write('stop\n')
            setupfile.close()

            minfile = open('min.inp', 'w')
            minfile.write('stream "toppar.str"\n')
            minfile.write('stream "%s.str"\n' % lipname)
            minfile.write('read psf card name "%s.psf"\n' % lipname)
            minfile.write('read coor card name "%s.crd"\n' % lipname)
            minfile.write('shake bonh param sele all end\n')
            minfile.write('nbond inbfrq -1 elec fswitch vdw vswitch cutnb 16. ctofnb 12. ctonnb 10.\n')
            minfile.write('energy\n')
            minfile.write('coor copy comp\n')
            minfile.write('mini sd nstep 100\n')
            minfile.write('ioform extended\n')
            minfile.write('write coor card name min.crd\n')
            minfile.write('stop\n')
            minfile.close()

            try:
                args = shlex.split('%scharmm -i setup.inp' % (softdir))
                process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                out, err = process.communicate()
            except OSError:
                out = 'charmm has failed or has not been found.'
            if not os.path.isfile('%s.psf' % lipname):
                error = True
                errorfile = open('charmm.log', 'wb')
                errorfile.write(out)
                errorfile.close()
            if not error:
                try:
                    args = shlex.split('%scharmm -i min.inp' % (softdir))
                    process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    out, err = process.communicate()
                except OSError:
                    out = 'charmm has failed or has not been found.'
                if not os.path.isfile('min.crd'):
                    error = True
                    errorfile = open('charmm.log', 'wb')
                    errorfile.write(out)
                    errorfile.close()
        if not error:
            shutil.rmtree(dirname, ignore_errors=True)

    return error, rand


def amberrun(lipname, ff_file, lib_file, pdb_file, software):
    """When lipid topologies are added to the database through the "Topologies" form, the files consistency is
       first checked by running a small minimisation simulation. If error occurs, a log file named "amber.log" is
       created and the user has access to this file. The simulation is processed in a temporary directory. If an
       an error occurs, this directory is kept to let the user having access to the "amber.log" file.

    Parameters
    ----------
    lipname: string
        Lipid names (4 digits) have to be the same in the database and in the topology (lib) and structure files (pdb).
    ff_file: string
        Pathway to the zip file containing the forcefield directory
    lib_file: file
        File object uploaded by the user for the topology file
    pdb_file: file
        File object uploaded by the user for the structure file
    software: string
        4 digit acronym representing the software version to use for the simulation

    Returns
    -------
    error: bool
        True if errors occured
    rand: int
        Allow to reconstruct th path to the directory where the "amber.log" file has been created.
    """
    mediadir = settings.MEDIA_ROOT
    softpath = {'AM18': settings.AMBER_18_PATH}
    softdir = softpath[software]
    installed = True
    if not os.path.isfile(os.path.join(softdir, 'tleap')):
        installed = False
    if not os.path.isfile(os.path.join(softdir, 'sander')):
        installed = False

    rand = str(random.randrange(1000))
    while os.path.isdir(os.path.join(mediadir, 'tmp', rand)):
        rand = str(random.randrange(1000))

    error = False
    if installed:
        dirname = os.path.join(mediadir, 'tmp', rand)
        os.makedirs(dirname)

        ffzip = zipfile.ZipFile('%s%s' % (settings.BASE_DIR, ff_file))
        ffzip.extractall(dirname)

        shutil.copy('media/min.in', dirname)

        fs = FileSystemStorage(location=dirname)
        fs.save('%s.lib' % lipname, lib_file)
        strext = os.path.splitext(pdb_file.name)[1]
        fs.save('%s%s' % (lipname, strext), pdb_file)

        with cd(dirname):
            setupfile = open('tleap.in', 'w')
            for name in glob.glob('leaprc.*'):
                setupfile.write('source %s\n' % name)
            setupfile.write('loadoff %s.lib\n' % lipname)
            setupfile.write('LIPID = loadpdb %s.pdb\n' % lipname)
            setupfile.write('set LIPID box { 100.0 100.0 100.0 }\n')
            setupfile.write('saveAmberParm LIPID %s.prmtop %s.inpcrd\n' % (lipname, lipname))
            setupfile.write('quit\n')
            setupfile.close()

            try:
                args = shlex.split('%stleap -s -f tleap.in' % (softdir))
                process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                out, err = process.communicate()
            except OSError:
                out = 'tleap has failed or has not been found.'
            if not os.path.isfile('%s.inpcrd' % lipname):
                error = True
                errorfile = open('amber.log', 'wb')
                errorfile.write(out)
                errorfile.close()
            if not error:
                try:
                    args = shlex.split(
                        '%ssander -O -i min.in -o min.out -p %s.prmtop -c %s.inpcrd -r min.rst' % (softdir, lipname,
                                                                                                   lipname))
                    process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    out, err = process.communicate()
                except OSError:
                    out = 'sander has failed or has not been found.'
                if not os.path.isfile('min.rst'):
                    error = True
                    errorfile = open('amber.log', 'wb')
                    errorfile.write(out)
                    errorfile.close()
        if not error:
            shutil.rmtree(dirname, ignore_errors=True)

    return error, rand


def findcgbonds(itp_file):

    bonds = []
    infile = open('%s%s' % (settings.BASE_DIR, itp_file)).readlines()
    bondsection = False
    for line in infile:
        if line[0:1] == '[':
            if re.search('bonds', line):
                bondsection = True
            else:
                bondsection = False
        if bondsection:
            linearr = line.strip().split()
            if line.strip() != '':
                if line[0:1] != '[' and line[0:1] != ';' and line[0:1] != '#' and len(linearr) >= 2:
                    bonds.append([int(linearr[0])-1, int(linearr[1])-1])

    return bonds


def atnames(gro_file):

    mediadir = settings.MEDIA_ROOT
    rand = str(random.randrange(1000))
    while os.path.isdir(os.path.join(mediadir, 'tmp', rand)):
        rand = str(random.randrange(1000))

    dirname = os.path.join(mediadir, 'tmp', rand)
    os.makedirs(dirname)

    fs = FileSystemStorage(location=dirname)
    strext = os.path.splitext(gro_file.name)[1]
    fs.save('lipid%s' % strext, gro_file)

    names = []
    lines = open(os.path.join(dirname, 'lipid%s' % strext)).readlines()
    if strext == ".gro":
        if len(lines) > 3:
            for line in lines[2:-1]:
                try:
                    names.append(line[10:15].strip())
                except ValueError:
                    names.append('error')
    elif strext == ".pdb":
        for line in lines:
            if line[:6] == "ATOM  ":
                try:
                    names.append(line[12:16].strip())
                except ValueError:
                    names.append('error')

    shutil.rmtree(dirname, ignore_errors=True)

    return names


def findresname(str_file, soft):

    mediadir = settings.MEDIA_ROOT
    rand = str(random.randrange(1000))
    while os.path.isdir(os.path.join(mediadir, 'tmp', rand)):
        rand = str(random.randrange(1000))

    dirname = os.path.join(mediadir, 'tmp', rand)
    os.makedirs(dirname)

    fs = FileSystemStorage(location=dirname)
    strext = os.path.splitext(str_file.name)[1]
    fs.save('lipid%s' % strext, str_file)

    resname = ""
    infile = open(os.path.join(dirname, 'lipid%s' % strext)).readlines()
    if soft == "Charmm":
        for line in infile:
            if re.search('^RESI ', line):
                resname = line.split()[1]

    shutil.rmtree(dirname, ignore_errors=True)

    return resname


def get_residues(structure_file):

    mediadir = settings.MEDIA_ROOT
    rand = str(random.randrange(1000))
    while os.path.isdir(os.path.join(mediadir, 'tmp', rand)):
        rand = str(random.randrange(1000))

    dirname = os.path.join(mediadir, 'tmp', rand)
    os.makedirs(dirname)

    fs = FileSystemStorage(location=dirname)
    ext = os.path.splitext(structure_file.name)[1]
    fs.save('lipid%s' % ext, structure_file)

    error = False
    residues = []
    lines = open(os.path.join(dirname, 'lipid%s' % ext)).readlines()
    if ext == ".gro":
        if len(lines) > 3:
            title = lines[0]
            box = lines[-1]
            resi = -1
            for line in lines[2:-1]:
                atom = Atom(line, ext, 0)
                if atom == 'error':
                    error = True
                if not residues:
                    residues.append(atom[0])
                    resi = atom[2]
                if atom[2] != resi:
                    resi = atom[2]
                    residues.append(atom[0])
        else:
            error = True
    elif extension == ".pdb":
        for line in lines:
            if line[:6] == "TITLE ":
                title = line
            elif line[:6] == "CRYST1":
                box = line
            elif line[:6] == "ATOM  ":
                atom = Atom(line, ext, 0)
                if atom == 'error':
                    error = True
                if not residues:
                    residues.append(atom[0])
                    resi = atom[2]
                if atom[2] != resi:
                    resi = atom[2]
                    residues.append(atom[0])

    if error == True:
        residues = []

    shutil.rmtree(dirname, ignore_errors=True)

    return residues
