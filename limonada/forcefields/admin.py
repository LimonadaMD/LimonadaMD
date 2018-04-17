from django.contrib import admin
from . import models
from .forms import ForcefieldAdminForm

class ForcefieldAdmin(admin.ModelAdmin):
    form = ForcefieldAdminForm


admin.site.register(models.Forcefield, ForcefieldAdmin)

