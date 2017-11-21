from django.contrib import admin
from . import models


class CompositionInline(admin.TabularInline):
    model = models.Composition
    extra = 1


class MembraneAdmin(admin.ModelAdmin):
    inlines = (CompositionInline,)


admin.site.register(models.Membrane, MembraneAdmin)


