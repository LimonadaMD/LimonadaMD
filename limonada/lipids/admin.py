from django.contrib import admin
from . import models
from .forms import TopologyAdminForm


class LipidAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('lmid',)}


class TopologyAdmin(admin.ModelAdmin):
    form = TopologyAdminForm


admin.site.register(models.Lipid, LipidAdmin)
admin.site.register(models.Topology, TopologyAdmin)

