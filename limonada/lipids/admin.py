from django.contrib import admin
from . import models

class LipidAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('lmid',)}

admin.site.register(models.Lipid, LipidAdmin)
admin.site.register(models.Topology)

