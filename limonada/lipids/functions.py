#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, random, shutil
import shlex, subprocess
import zipfile
from contextlib import contextmanager 
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


def gmxrun(lipname,ff_file,mdp_file,itp_file,gro_file,software):
    
    mediadir = settings.MEDIA_ROOT
    error = False

    if software == "GR45":
       softdir = settings.GROMACS_45_PATH
    elif software == "GR50":
       softdir = settings.GROMACS_50_PATH

    rand = str(random.randrange(1000))
    while os.path.isdir(os.path.join(mediadir, "tmp", rand)):
       rand = random.randrange(1000)
    dirname = os.path.join(mediadir, "tmp", rand)
    os.makedirs(dirname)

    ffzip = zipfile.ZipFile("%s%s" % (settings.BASE_DIR,ff_file))
    ffdir = os.path.join(dirname,ffzip.namelist()[0])
    ffzip.extractall(dirname)

    mdpzip = zipfile.ZipFile("%s%s" % (settings.BASE_DIR,mdp_file))
    mdpzip.extractall(dirname)

    fs = FileSystemStorage(location=dirname)
    fs.save("%s.itp" % lipname, itp_file)
    fs.save("%s.gro" % lipname, gro_file)
    
    topfile = open(os.path.join(dirname,"topol.top"),"w")
    topfile.write("")
    topfile.write("#include \"%sforcefield.itp\"\n\n" % ffdir)   
    topfile.write("#include \"./%s.itp\"\n\n" % lipname)   
    topfile.write("[ system ]\n")   
    topfile.write("itp test\n\n")   
    topfile.write("[ molecules ]\n")   
    topfile.write("%s          1" % lipname)   
    topfile.close()    

    with cd(dirname):
        try:
            args = shlex.split("%sgrompp -f em.mdp -p topol.top -c %s.gro -o em.tpr -maxwarn 1" % (softdir,lipname) )
            process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = process.communicate()
        except:
            err = "grompp has failed or has not been found."
        if not os.path.isfile("em.tpr"): 
            error = True
            errorfile = open("gromacs.log","w") 
            errorfile.write(err)
            errorfile.close()
        if error == False:
            args = shlex.split("%smdrun -v -deffnm em" % softdir)
            process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = process.communicate()
            if not os.path.isfile("em.gro"): 
                error = True
                errorfile = open("gromacs.log","w") 
                errorfile.write(err)
                errorfile.close()
    if error == False:        
        shutil.rmtree(dirname, ignore_errors=True)

    return error, rand 

    




