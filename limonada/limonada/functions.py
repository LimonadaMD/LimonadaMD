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

# Django
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.mail import send_mail


def FileData(request, key, hiddenkey, filedata):
    """ Allows to save files uploaded in forms when invalid POST. If files are
        not saved and a new request.FILES is build these data are lost in the
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
        f = open(mediapath, 'rb')
        filedata[key] = SimpleUploadedFile(f.name, f.read())
    elif keypath:
        mediapath = os.path.join('media/', keypath)
        f = open(mediapath, 'rb')
        filedata[key] = SimpleUploadedFile(f.name, f.read())
    return filedata, keypath


def delete_file(path):
    if os.path.isfile(path):
        os.remove(path)

def review_notification(status, db_table, entry_id):
    if status == "creation":
        subject = 'There is a new entry on Limonada'
    else:
        subject = 'An entry has been updated on Limonada'
    if db_table == 'references':
        url = 'https://limonada.univ-reims.fr/%s/?id=%s' % (db_table, entry_id)
    else:
        url = 'https://limonada.univ-reims.fr/%s/%s/' % (db_table, entry_id)
    text = 'Please review the following %s entry:\n%s' % (db_table, url)
    send_mail(subject, text, settings.DEFAULT_FROM_EMAIL, [settings.DEFAULT_FROM_EMAIL, ])
