from django.contrib import admin
from . import models


class CompositionInline(admin.TabularInline):
    model = models.Composition
    extra = 1


class MembraneAdmin(admin.ModelAdmin):
    inlines = (CompositionInline,)


class TopolCompositionInline(admin.TabularInline):
    model = models.TopolComposition
    extra = 1


class MembraneTopolAdmin(admin.ModelAdmin):
    inlines = (TopolCompositionInline,)


admin.site.register(models.MembraneTopol, MembraneTopolAdmin)
admin.site.register(models.MembraneTag)
admin.site.register(models.Membrane, MembraneAdmin)


