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

# Django
from django.contrib import admin

# local Django
from .models import Author, Reference, AuthorsList
from .forms import AuthorAdminForm, ReferenceAdminForm, AuthorsListAdminForm


class AuthorAdmin(admin.ModelAdmin):

    """Customize the look of the auto-generated admin for the Author model"""
    form = AuthorAdminForm


class AuthorsListInline(admin.TabularInline):

    """Customize the look of the auto-generated admin for the Author list of the Reference model"""
    model = AuthorsList
    form = AuthorsListAdminForm
    extra = 1


class ReferenceAdmin(admin.ModelAdmin):

    """Customize the look of the auto-generated admin for the Reference model"""
    form = ReferenceAdminForm
    inlines = (AuthorsListInline,)


admin.site.register(Author, AuthorAdmin) # Use the customized options
admin.site.register(Reference, ReferenceAdmin)
