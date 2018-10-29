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

# Django
from django.contrib import admin

# local Django
from .models import MemComment, Composition, Membrane, MembraneTag, MembraneTopol, TopolComposition
from .forms import (MemCommentAdminForm, CompositionAdminForm, MembraneAdminForm, MembraneTopolAdminForm,
                    TopolCompositionAdminForm)


class MemCommentAdmin(admin.ModelAdmin):
    form = MemCommentAdminForm


class CompositionInline(admin.TabularInline):
    model = Composition
    form = CompositionAdminForm 
    extra = 1


class MembraneAdmin(admin.ModelAdmin):
    form = MembraneAdminForm 
    inlines = (CompositionInline,)


class TopolCompositionInline(admin.TabularInline):
    model = TopolComposition
    form = TopolCompositionAdminForm 
    extra = 1


class MembraneTopolAdmin(admin.ModelAdmin):
    form = MembraneTopolAdminForm 
    inlines = (TopolCompositionInline,)


admin.site.register(MemComment, MemCommentAdmin)
admin.site.register(MembraneTopol, MembraneTopolAdmin)
admin.site.register(MembraneTag)
admin.site.register(Membrane, MembraneAdmin)
