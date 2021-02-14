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
from datetime import date, datetime, timedelta
import os
import shutil
import tempfile
from unidecode import unidecode

# third-party
import requests
from PIL import Image

# Django
from django.contrib.auth.models import User
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files import File
from django.core.files.images import ImageFile
from django.db import IntegrityError
from django.test import TestCase, override_settings
from django.utils import timezone
from django.utils.formats import localize

# Django apps
from forcefields.models import Forcefield, Software
from homepage.models import Reference

# local Django
from lipids.models import Lipid, TopologyResidue, Topology, TopComment


MEDIA_INIT = settings.MEDIA_ROOT
MEDIA_ROOT = os.path.join(tempfile.mkdtemp(), 'media')
MEDIA_TMP = os.path.join(MEDIA_ROOT, 'tmp')
MEDIA_LIPIDS = os.path.join(MEDIA_ROOT, 'lipids')
MEDIA_TOPOLOGIES = os.path.join(MEDIA_ROOT, 'topologies')


@override_settings(MEDIA_ROOT=MEDIA_ROOT) # Tests are run in a temporary media directory
class LipidModelTest(TestCase):

    def _create_image(self, ext, size):
        with tempfile.NamedTemporaryFile(suffix='.%s' % ext.lower(), delete=False, dir=MEDIA_ROOT) as f:
            image = Image.new('RGB', (size, size), 'white')
            if ext == 'JPG':
                image.save(f, 'JPEG')
            else:
                image.save(f, ext)
            #print(os.path.getsize(f.name))

        return open(f.name, mode='rb')

    @classmethod
    def setUpClass(cls):
        os.makedirs(MEDIA_ROOT, exist_ok=True) # The temporary media directory is created before running tests
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA_ROOT) # The temporary media directory is deleted at the end of the tests 
        super().tearDownClass()

    @classmethod
    def setUpTestData(cls):
        # Set up non-modified objects used by all test methods
        os.makedirs(MEDIA_TMP, exist_ok=True)
        os.makedirs(MEDIA_LIPIDS, exist_ok=True)
        # Some files needs to be copied from the original media dircetory to the temporary one
        shutil.copy(os.path.join(MEDIA_INIT, 'residuetypes.dat'),os.path.join(MEDIA_ROOT, 'residuetypes.dat'))
        # Required database entries are created before running tests
        User.objects.create_user('john', 'lennon@thebeatles.com', 'johnpassword')

    def setUp(self):
        # When a lipid is saved, the picture is moved from its original location to "media/lipids" directory, it then
        # needs to be created at each setup 
        self.image = self._create_image('PNG',200)
        # Creation a prototype lipid 
        LMID = 'LMGP01010005'
        self.lipid = Lipid(
            name = 'POPC',
            lmid = 'LMGP01010005',
            com_name = 'PC(16:0/18:1(9Z))',
            search_name = 'POPC - LMGP01010005 - PC(16:0/18:1(9Z))',
            sys_name = '',
            iupac_name = '',
            formula = '',
            core = 'Glycerophospholipids [GP]',
            main_class = 'Glycerophosphocholines [GP01]',
            sub_class = 'Diacylglycerophosphocholines [GP0101]',
            l4_class = '',
            pubchem_cid = '',
            img = ImageFile(self.image, name=self.image.name),
            curator = User.objects.get(id=1),
            slug = 'lmgp01010005',
        )

    def tearDown(self):
        self.image.close()
        if 'image2' in self.__dict__.keys():
            self.image2.close()

    def test_create(self):
        """Lipid must have name, lmid, com_name, search_name, core, main_class, sub_class and curator.
           Other field can be null and/or are assigned in the view 
           except for the date assigned at creation 
        """
        self.lipid.full_clean()
        self.lipid.save()
        self.assertEqual(1, self.lipid.pk)

    def test_name_max_length(self):
        self.lipid.save()
        max_length = self.lipid._meta.get_field('name').max_length
        self.assertEquals(max_length, 4)

    def test_name_shorter(self):
        """Lipid name must be 4 characters.
        """
        self.lipid.name = "AAA"
        # full_clean must be called to test ValidationErrors 
        self.assertRaises(ValidationError, self.lipid.full_clean)

    def test_name_alphanumeric(self):
        """Lipid name must be 4 alphanumeric characters.
        """
        self.lipid.name = "A%$*"
        # full_clean must be called to test ValidationErrors 
        self.assertRaises(ValidationError, self.lipid.full_clean)

    def test_name_not_in_residuetypes(self):
        """Lipid name must not be residuetypes.dat.
        """
        self.lipid.name = "ARGN"
        # full_clean must be called to test ValidationErrors 
        self.assertRaises(ValidationError, self.lipid.full_clean)

    def test_name_unique(self):
        'Lipid name must be unique'
        self.lipid.save()
        lip = Lipid(
            name = 'POPC',
            lmid = 'lmid',
            com_name = 'com_name',
            curator = User.objects.get(id=1),
        )
        self.assertRaises(IntegrityError, lip.save)

    def test_lmid_max_length(self):
        self.lipid.save()
        max_length = self.lipid._meta.get_field('lmid').max_length
        self.assertEquals(max_length, 20)

    def test_lmid_did_not_start_with_LM_or_LI(self):
        """Lipid LMID must start with LM or LI.
        """
        self.lipid.lmid = "XXGP01010005"
        self.assertRaises(ValidationError, self.lipid.full_clean)

    def test_lmid_must_exist(self):
        """Lipid LMID must exist.
        """
        self.lipid.lmid = "LMXX01010005"
        self.assertRaises(ValidationError, self.lipid.full_clean)

    def test_lmid_unique(self):
        'Lipid lmid must be unique'
        self.lipid.save()
        lip = Lipid(
            name = 'name',
            lmid = 'LMGP01010005',
            com_name = 'com_name',
            curator = User.objects.get(id=1),
        )
        self.assertRaises(IntegrityError, lip.save)

    def test_com_name_max_length(self):
        self.lipid.save()
        max_length = self.lipid._meta.get_field('com_name').max_length
        self.assertEquals(max_length, 200)

    def test_com_name_unique(self):
        'Lipid lmid must be unique'
        self.lipid.save()
        lip = Lipid(
            name = 'name',
            lmid = 'lmid',
            com_name = 'PC(16:0/18:1(9Z))',
            curator = User.objects.get(id=1),
        )
        self.assertRaises(IntegrityError, lip.save)

    def test_search_name_max_length(self):
        self.lipid.save()
        max_length = self.lipid._meta.get_field('search_name').max_length
        self.assertEquals(max_length, 300)

    def test_sys_name_max_length(self):
        self.lipid.save()
        max_length = self.lipid._meta.get_field('sys_name').max_length
        self.assertEquals(max_length, 200)

    def test_iupac_name_max_length(self):
        self.lipid.save()
        max_length = self.lipid._meta.get_field('iupac_name').max_length
        self.assertEquals(max_length, 500)

    def test_formula_max_length(self):
        self.lipid.save()
        max_length = self.lipid._meta.get_field('formula').max_length
        self.assertEquals(max_length, 30)

    def test_core_max_length(self):
        self.lipid.save()
        max_length = self.lipid._meta.get_field('core').max_length
        self.assertEquals(max_length, 200)

    def test_main_class_max_length(self):
        self.lipid.save()
        max_length = self.lipid._meta.get_field('main_class').max_length
        self.assertEquals(max_length, 200)

    def test_sub_class_max_length(self):
        self.lipid.save()
        max_length = self.lipid._meta.get_field('sub_class').max_length
        self.assertEquals(max_length, 200)

    def test_l4_class_max_length(self):
        self.lipid.save()
        max_length = self.lipid._meta.get_field('l4_class').max_length
        self.assertEquals(max_length, 200)

    def test_l4_class_can_be_blank(self):
        self.lipid.l4_class = ''
        self.lipid.save()
        self.assertEqual(1, self.lipid.pk)

    def test_pubchem_cid_max_length(self):
        self.lipid.save()
        max_length = self.lipid._meta.get_field('pubchem_cid').max_length
        self.assertEquals(max_length, 50)

    def test_img_extension(self):
        self.image2 = self._create_image('TIFF', 200)
        self.lipid.img = ImageFile(self.image2, name=self.image2.name)
        self.assertRaises(ValidationError, self.lipid.full_clean)

    #def test_img_size(self):
    #    self.image2 = self._create_image('PNG', 20000)
    #    self.lipid.img = ImageFile(self.image2, name=self.image2.name)
    #    self.assertRaises(ValidationError, self.lipid.full_clean)

    def test_img_upload_to(self):
        name = '%s%s' % (self.lipid.lmid, os.path.splitext(self.lipid.img.name)[1])
        self.lipid.full_clean()
        self.assertTrue(os.path.exists(os.path.join(MEDIA_LIPIDS, name)), 
            "The lipid picture is not uploaded at the correct location.")

    def test_remove_img_if_exist_at_upload_to(self):
        self.image2 = self._create_image('JPG', 200)
        name = '%s%s' % (self.lipid.lmid, os.path.splitext(self.image2.name)[1])
        shutil.copy(self.image2.name, os.path.join(MEDIA_LIPIDS, name))
        self.lipid.full_clean()
        self.lipid.save()
        self.assertFalse(os.path.exists(os.path.join(MEDIA_LIPIDS, name)),
            "The preexisting lipid picture has not been deleted.")

    def test_has_date(self):
        'Lipid must have automatic date.'
        self.lipid.save()
        self.assertEqual(self.lipid.date, date.today())

    def test_curator_on_delete_cascade(self):
        User.objects.create_user('paul', 'mccartney@thebeatles.com', 'paulpassword')
        self.lipid.curator = User.objects.get(id=2) 
        self.lipid.save()
        User.objects.filter(id=2).delete()
        nb_lipids = len(Lipid.objects.all())
        self.assertEquals(nb_lipids, 0)

    def test_object_name_is_search_name(self):
        'The lipid search name is defined in views and it is used as object name'
        self.lipid.search_name = 'name - lmid - com_name'
        self.lipid.save()
        #expected_object_name = f'{lipid.name} - {lipid.lmid} - {lipid.com_name}'
        expected_object_name = 'name - lmid - com_name'
        self.assertEquals(expected_object_name, str(self.lipid))

    def test_get_absolute_url(self):
        self.lipid.slug = 'lmgp01010005'
        self.lipid.save()
        self.assertEquals(self.lipid.get_absolute_url(), '/lipids/lmgp01010005/')


class TopologyResidueModelTest(TestCase):

    def setUp(self):
        self.topologyresidue = TopologyResidue(residue='POPC')

    def test_create(self):
        """TopologyResidue must have residue.
        """
        self.topologyresidue.full_clean()
        self.topologyresidue.save()
        self.assertEqual(1, self.topologyresidue.pk)

    def test_name_unique(self):
        'residue must be unique'
        self.topologyresidue.save()
        topres = TopologyResidue(residue='POPC') 
        self.assertRaises(IntegrityError, topres.save)

    def test_object_name(self):
        'The topology object name is the residue'
        expected_object_name = '%s' % self.topologyresidue.residue
        self.topologyresidue.save()
        self.assertEquals(expected_object_name, str(self.topologyresidue))


@override_settings(MEDIA_ROOT=MEDIA_ROOT) # Tests are run in a temporary media directory
class TopologyModelTest(TestCase):

    def _create_file(self, ext, nblines):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.%s' % ext.lower(), delete=False, dir=MEDIA_ROOT) as f:
            for i in range(nblines):
                f.write("%s\n" % ("x" * 100))
            #print(os.path.getsize(f.name))

        return open(f.name, mode='r')

    @classmethod
    def setUpClass(cls):
        os.makedirs(MEDIA_ROOT, exist_ok=True) # The temporary media directory is created before running tests
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA_ROOT) # The temporary media directory is deleted at the end of the tests 
        super().tearDownClass()

    @classmethod
    def setUpTestData(cls):
        # Set up non-modified objects used by all test methods
        os.makedirs(MEDIA_TMP, exist_ok=True)
        os.makedirs(MEDIA_TOPOLOGIES, exist_ok=True)
        # Required database entries are created before running tests
        User.objects.create_user('john', 'lennon@thebeatles.com', 'johnpassword')
        Software.objects.create(name='Gromacs')
        Forcefield.objects.create(name='martini 2.0', curator=User.objects.get(id=1))
        Lipid.objects.create(name='POPC', lmid='LMGP01010005', com_name='PC(16:0/18:1(9Z))', curator=User.objects.get(id=1))
        TopologyResidue.objects.create()
        Reference.objects.create(curator=User.objects.get(id=1), year=2015)

    def setUp(self):
        # When a topology is saved, the topology and structure files are moved from their original location to
        # "media/topologies" directory, they then needs to be created at each setup 
        self.topology_file = self._create_file('ITP',10)
        self.structure_file = self._create_file('GRO',10)
        # Creation a prototype topology 
        self.topology = Topology(
            forcefield = Forcefield.objects.get(id=1), 
            lipid = Lipid.objects.get(id=1), 
            itp_file = File(self.topology_file, self.topology_file.name),
            gro_file = File(self.structure_file, self.structure_file.name),
            version = 'Wassenaar2015',
            head = 'PO4',
            curator = User.objects.get(id=1),
        )

    def tearDown(self):
        self.topology_file.close()
        self.structure_file.close()
        if 'topology2_file' in self.__dict__.keys():
            self.topology2_file.close()

    def test_create(self):
        """Topology must have forcefield, lipid, itp_file, gro_file, version, head and curator.
           ManytoMany fields (software, residue and reference) are also required but have to be assigned after creation.  
           Other field can be blank or are assigned at creation 
        """
        self.topology.full_clean()
        self.topology.save()
        self.assertEqual(1, self.topology.pk)

    def test_forcefield_on_delete_cascade(self):
        Forcefield.objects.create(curator=User.objects.get(id=1))
        self.topology.forcefield = Forcefield.objects.get(id=2) 
        self.topology.save()
        Forcefield.objects.filter(id=2).delete()
        nb_topologies = len(Topology.objects.all())
        self.assertEquals(nb_topologies, 0)

    def test_lipid_on_delete_cascade(self):
        Lipid.objects.create(name='DPPC', lmid='LMGP01010564', com_name='PC(16:0/16:0)', curator=User.objects.get(id=1))
        self.topology.lipid = Lipid.objects.get(id=2) 
        self.topology.save()
        Lipid.objects.filter(id=2).delete()
        nb_topologies = len(Topology.objects.all())
        self.assertEquals(nb_topologies, 0)

    def test_topology_file_size(self):
        self.topology2_file = self._create_file('ITP', 2200)
        self.topology.itp_file = File(self.topology2_file, name=self.topology2_file.name)
        self.assertRaises(ValidationError, self.topology.full_clean)

    def test_topology_file_upload_to(self):
        self.topology.full_clean()
        self.topology.save()
        self.topology.software.add(Software.objects.get(id=1))
        self.topology.save()
        ext = os.path.splitext(self.topology.itp_file.name)[1]
        version = unidecode(self.topology.version).replace(' ', '_')
        forcefield = unidecode(self.topology.forcefield.name).replace(' ', '_')
        # ex.: topologies/Gromacs/Martini/POPC/version/POPC.itp
        path = '{0}/{1}/{2}/{3}/{2}{4}'.format(self.topology.software.all()[0].name, forcefield,
            self.topology.lipid.name, version, ext)
        self.assertTrue(os.path.exists(os.path.join(MEDIA_TOPOLOGIES, path)), 
            "The topology file has not been uploaded at the correct location.")

    def test_remove_topology_file_if_exist_at_upload_to(self):
        path = 'Gromacs/martini_2.0/POPC/Wassenaar2015'
        name = 'POPC.itp'
        os.makedirs(os.path.join(MEDIA_TOPOLOGIES, path), exist_ok=True)
        self.topology2_file = self._create_file('ITP', 10)
        shutil.copy(self.topology2_file.name, os.path.join(MEDIA_TOPOLOGIES, os.path.join(path, name)))
        ct1 = os.path.getctime(os.path.join(MEDIA_TOPOLOGIES, os.path.join(path, name)))
        self.topology.full_clean()
        self.topology.save()
        self.topology.software.add(Software.objects.get(id=1))
        self.topology.save()
        ct2 = os.path.getctime(os.path.join(MEDIA_TOPOLOGIES, os.path.join(path, name)))
        self.assertNotEquals(ct1, ct2)

    def test_has_date(self):
        'Topology must have automatic date.'
        self.topology.save()
        self.assertEqual(self.topology.date, date.today())

    def test_curator_on_delete_cascade(self):
        User.objects.create_user('paul', 'mccartney@thebeatles.com', 'paulpassword')
        self.topology.curator = User.objects.get(id=2) 
        self.topology.save()
        User.objects.filter(id=2).delete()
        nb_topologies = len(Topology.objects.all())
        self.assertEquals(nb_topologies, 0)

    def test_object_name(self):
        'The topology object name is build by the concatenation of the lipid name and the topology version'
        expected_object_name = '%s_%s' % (self.topology.lipid.name, self.topology.version)
        self.topology.save()
        self.assertEquals(expected_object_name, str(self.topology))

    def test_get_absolute_url(self):
        self.topology.save()
        self.assertEquals(self.topology.get_absolute_url(), '/topologies/%d/' % self.topology.pk)


class TopCommentModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Set up non-modified objects used by all test methods
        # Required database entries are created before running tests
        User.objects.create_user('john', 'lennon@thebeatles.com', 'johnpassword')
        Forcefield.objects.create(name='martini 2.0', curator=User.objects.get(id=1))
        Lipid.objects.create(name='POPC', lmid='LMGP01010005', com_name='PC(16:0/18:1(9Z))',
            curator=User.objects.get(id=1))
        Topology.objects.create(lipid=Lipid.objects.get(id=1), version='Wassenaar2015',
            forcefield=Forcefield.objects.get(id=1), curator=User.objects.get(id=1))

    def setUp(self):
        # Creation a prototype topology 
        self.topcomment = TopComment(
            topology = Topology.objects.get(id=1),
            user = User.objects.get(id=1),
        )

    def test_create(self):
        """TopComment must have topology and user.
           Other field can be blank or are assigned at creation 
        """
        self.topcomment.full_clean()
        self.topcomment.save()
        self.assertEqual(1, self.topcomment.pk)

    def test_topology_on_delete_cascade(self):
        Topology.objects.create(lipid=Lipid.objects.get(id=1),
            forcefield=Forcefield.objects.get(id=1), curator=User.objects.get(id=1))
        self.topcomment.topology = Topology.objects.get(id=2)
        self.topcomment.save()
        Topology.objects.filter(id=2).delete()
        nb_topcomment = len(TopComment.objects.all())
        self.assertEquals(nb_topcomment, 0)

    def test_curator_on_delete_cascade(self):
        User.objects.create_user('paul', 'mccartney@thebeatles.com', 'paulpassword')
        self.topcomment.user = User.objects.get(id=2)
        self.topcomment.save()
        User.objects.filter(id=2).delete()
        nb_topcomment = len(TopComment.objects.all())
        self.assertEquals(nb_topcomment, 0)

    def test_has_date(self):
        'TopComment must have automatic date.'
        self.topcomment.save()
        now = timezone.make_aware(datetime.now()) 
        test = False
        limit = self.topcomment.date + timedelta(seconds=1) 
        if now >= self.topcomment.date and now <= limit:
            test = True
        self.assertTrue(test)

    def test_object_name(self):
        """The TopComment object name is build by the concatenation of the username, the lipid name, the
        topology version and the date
        """
        self.topcomment.save()
        expected_object_name = '%s %s %s %s' % (self.topcomment.user.username, self.topcomment.topology.lipid.name,
            self.topcomment.topology.version, localize(self.topcomment.date))
        self.assertEquals(expected_object_name, str(self.topcomment))
