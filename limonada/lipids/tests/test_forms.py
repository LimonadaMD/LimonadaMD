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
import os
import shutil
import tempfile

# Django
from django.contrib.auth.models import User
from django.conf import settings
from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

# Django apps
from forcefields.models import Forcefield, Software

# local Django
from lipids.forms import TopologyForm 
from lipids.models import Lipid, Topology


MEDIA_INIT = settings.MEDIA_ROOT
MEDIA_ROOT = os.path.join(tempfile.mkdtemp(), 'media')
MEDIA_TMP = os.path.join(MEDIA_ROOT, 'tmp')
MEDIA_LIPIDS = os.path.join(MEDIA_ROOT, 'lipids')
MEDIA_TOPOLOGIES = os.path.join(MEDIA_ROOT, 'topologies')


@override_settings(MEDIA_ROOT=MEDIA_ROOT) # Tests are run in a temporary media directory
class TopologyFormTest(TestCase):

    def _create_file(self, ext, url):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.%s' % ext.lower(), delete=False, dir=MEDIA_ROOT) as f:
            response = requests.get(url)
            f.write(response.content)
            f.close()

        return SimpleUploadedFile(f.name, f.read())

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
        # Load lipid topology, lipid structure and forcefield file
        url = 'https://limonada.univ-reims.fr/media/topologies/Gromacs/martini_2.0/POPC/Wassenaar2015/POPC.itp'
        self.topology_file = self._create_file('ITP', url)
        url = 'https://limonada.univ-reims.fr/media/topologies/Gromacs/martini_2.0/POPC/Wassenaar2015/POPC.gro'
        self.structure_file = self._create_file('GRO', url)
        url = 'https://limonada.univ-reims.fr/media/forcefields/Gromacs/martini_2.0.ff.zip'
        self.forcefield_file = self._create_file('ZIP', url)
        # Required database entries are created before running tests
        User.objects.create_user('john', 'lennon@thebeatles.com', 'johnpassword')
        Forcefield.objects.create(name='martini 2.0', curator=User.objects.get(id=1))
        Lipid.objects.create(name='POPC', lmid='LMGP01010005', com_name='PC(16:0/18:1(9Z))',
            curator=User.objects.get(id=1))
        Topology.objects.create(lipid=Lipid.objects.get(id=1), version='Wassenaar2015',
            forcefield=Forcefield.objects.get(id=1), curator=User.objects.get(id=1))

    def setUp(self):
        # When a topology is saved, the topology and structure files are moved from their original location to
        # "media/topologies" directory, they then needs to be created at each setup 

    def tearDown(self):
        self.topology_file.close()
        self.structure_file.close()
        self.forcefield_file.close()

    def test_form_is_valid(self):
        lipid = 'POPC - LMGP01010005 - PC(16:0/18:1(9Z))'
        ff = Forcefield.objects.get(id=1)
        version = 'Version'
        form = TopologyForm(data={'lipid': lipid, 'forcefield': ff, 'version': version})
        self.assertTrue(form.is_valid())

#    def test_version_name_is_unique(self):

