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

# Django
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile


def FileData(request, key, hiddenkey, filedata):
    """ Allows to save files uploaded in forms when invalid POST. If files are
        not saved and a new request.FILES build these data are lost in the
        refreshed form. Local path to the saved files also needs to be passed
        as hidden field.
    """
    keypath = request.POST[hiddenkey]
    if key in request.FILES.keys():
        keyfile = request.FILES[key]
        keypath = os.path.join('tmp/', keyfile.name)
        mediapath = os.path.join('media/', keypath) 
        if os.path.isfile(mediapath):
            os.remove(mediapath)
        with default_storage.open(keypath, 'wb+') as destination:
            for chunk in keyfile.chunks():
                destination.write(chunk)
        f = file(mediapath)
        filedata[key] = SimpleUploadedFile(f.name, f.read())
    elif keypath:
        mediapath = os.path.join('media/', keypath) 
        f = file(mediapath)
        filedata[key] = SimpleUploadedFile(f.name, f.read())
    return filedata, keypath
