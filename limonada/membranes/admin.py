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
from .models import (Composition, Membrane, MembraneProt, MembraneTag, MembraneTopol, MemComment,
                     TopolComposition)
from .forms import (CompositionAdminForm, MembraneAdminForm, MembraneTopolAdminForm, MemCommentAdminForm,
                    TopolCompositionAdminForm)


class CompositionInline(admin.TabularInline):

    """Customize the look of the auto-generated admin for Composition list (lipid with % and leaflet side)
    of the Membrane model"""
    model = Composition
    form = CompositionAdminForm
    extra = 1


class MembraneAdmin(admin.ModelAdmin):

    """Customize the look of the auto-generated admin for the Membrane model"""
    form = MembraneAdminForm
    inlines = (CompositionInline,)


class TopolCompositionInline(admin.TabularInline):

    """Customize the look of the auto-generated admin for the Composition list (lipid with its topology, 
    number and leaflet side) of the Membrane Topology model"""
    model = TopolComposition
    form = TopolCompositionAdminForm
    extra = 1


class MembraneTopolAdmin(admin.ModelAdmin):

    """Customize the look of the auto-generated admin for the Membrane model"""
    form = MembraneTopolAdminForm
    inlines = (TopolCompositionInline,)


class MemCommentAdmin(admin.ModelAdmin):

    """Customize the look of the auto-generated admin for the Membrane Comment model"""
    form = MemCommentAdminForm


admin.site.register(Membrane, MembraneAdmin) # Use the customized options
admin.site.register(MembraneProt)
admin.site.register(MembraneTag)
admin.site.register(MembraneTopol, MembraneTopolAdmin)
admin.site.register(MemComment, MemCommentAdmin)
