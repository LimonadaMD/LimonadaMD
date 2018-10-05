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
import random
import re
import shlex
import shutil
import subprocess
import zipfile
from contextlib import contextmanager

# Django
from django.conf import settings
from django.core.files.storage import FileSystemStorage


@contextmanager
def cd(newdir):
    prevdir = os.getcwd()
    os.chdir(os.path.expanduser(newdir))
    try:
        yield
    finally:
        os.chdir(prevdir)


def gmxrun(lipname, ff_file, mdp_file, itp_file, gro_file, software):

    mediadir = settings.MEDIA_ROOT
    error = False

    if software == 'GR45':
        softdir = settings.GROMACS_45_PATH
    elif software == 'GR50':
        softdir = settings.GROMACS_50_PATH

    rand = str(random.randrange(1000))
    while os.path.isdir(os.path.join(mediadir, 'tmp', rand)):
        rand = random.randrange(1000)
    dirname = os.path.join(mediadir, 'tmp', rand)
    os.makedirs(dirname)

    ffzip = zipfile.ZipFile('%s%s' % (settings.BASE_DIR, ff_file))
    ffdir = os.path.join(dirname, ffzip.namelist()[0])
    ffzip.extractall(dirname)

    mdpzip = zipfile.ZipFile('%s%s' % (settings.BASE_DIR, mdp_file))
    mdpzip.extractall(dirname)

    fs = FileSystemStorage(location=dirname)
    fs.save('%s.itp' % lipname, itp_file)
    fs.save('%s.gro' % lipname, gro_file)

    topfile = open(os.path.join(dirname, 'topol.top'), 'w')
    topfile.write('')
    topfile.write('#include "%sforcefield.itp"\n\n' % ffdir)
    topfile.write('#include "./%s.itp"\n\n' % lipname)
    topfile.write('[ system ]\n')
    topfile.write('itp test\n\n')
    topfile.write('[ molecules ]\n')
    topfile.write('%s          1' % lipname)
    topfile.close()

    with cd(dirname):
        try:
            args = shlex.split('%sgrompp -f em.mdp -p topol.top -c %s.gro -o em.tpr -maxwarn 1' % (softdir, lipname))
            process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = process.communicate()
        except OSError:
            err = 'grompp has failed or has not been found.'
        if not os.path.isfile('em.tpr'):
            error = True
            errorfile = open('gromacs.log', 'w')
            errorfile.write(err)
            errorfile.close()
        if not error:
            args = shlex.split('%smdrun -v -deffnm em' % softdir)
            process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = process.communicate()
            if not os.path.isfile('em.gro'):
                error = True
                errorfile = open('gromacs.log', 'w')
                errorfile.write(err)
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
