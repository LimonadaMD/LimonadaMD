from __future__ import unicode_literals

from django.db import models


# Create your models here.


# class Lipid(models.Model):
#    name = models.CharField()
#    lmid = models.CharField

class PoCReference(object):
    def __init__(self, authors, title, journal, num, pages, year, doi):
        self.authors = authors
        self.title = title
        self.journal = journal
        self.num = num
        self.pages = pages
        self.year = year
        self.doi = doi


ref_example = PoCReference("Jambeck, J. P. M. and Lyubartsev, A. P.",
                           "An Extension and Further Validation of an All-Atomistic Force Field "
                           "for Biological Membranes",
                           "J. Chem. Theory Comput.",
                           "8",
                           "2938 2948",
                           "2012",
                           "10.1021/ct300342n")


class PoCGMXTopology(object):
    format = "GROMACS"

    def __init__(self, parent, forcefield, itp_file, gro_file, version="1", references=[], idnum=1,
                 name="unknown"):
        self.parent = parent
        self.forcefield = forcefield
        self.itp_file = itp_file
        self.gro_file = gro_file
        self.version = version
        self.references = references
        self.idnum = idnum
        self.name = name


top_example = PoCGMXTopology(None, "Slipids", "popc.itp", "popc.gro",
                             references=[ref_example])


class PoCMembrane(object):
    def __init__(self, name, lipids, forcefield, idnum=1, equilibration="Not done"):
        self.name = name
        self.lipids = lipids
        if type(lipids) == int:
            self.nlipids = lipids
        else:
            nlipids = 0
            for lipid in lipids:
                nlipids += lipid[0]
            self.nlipids = nlipids
        self.forcefield = forcefield
        self.idnum = idnum
        self.equilibration = equilibration


membrane_example = PoCMembrane("PLPC/POPC Membrane",
                               [
                                   (64, PoCGMXTopology(None, "Slipids", "dummy.itp",
                                                       "dummy.gro", name="POPC")),
                                   (64, PoCGMXTopology(None, "Slipids", "dummy.itp",
                                                       "dummy.gro", name="PLPC"))
                               ],
                               "Slipids",
                               idnum=1,
                               equilibration="250 ns")


class PoCLipid(object):
    def __init__(self):
        self.name = "POPC"
        self.lmid = "LMGP01010005"

        top_example.parent = self
        self.topologies = [
            top_example,
            PoCGMXTopology(self, "Gromos 54a7", "popc.itp", "popc.gro"),
            PoCGMXTopology(self, "Martini", "popc.itp", "popc.gro"),
        ]

        self.membranes = [
            PoCMembrane("Pure POPC Membrane", 128, "Slipids"),
            membrane_example,
            PoCMembrane("Plasma Membrane", 19280, "Martini"),
        ]
