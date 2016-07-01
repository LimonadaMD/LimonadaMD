from __future__ import unicode_literals

from django.db import models

# Create your models here.


class Forcefield(models.Model):
    UNKNOWN = "UN"
    ALLATOM = "AA"
    UNITEDATOM = "UA"
    COARSEGRAINED = "CG"
    FFTYPE_CHOICES = (
        (UNKNOWN, 'Unknown'),
        (ALLATOM, 'All atom'),
        (UNITEDATOM, 'United atom'),
        (COARSEGRAINED, 'Coarse grained')
    )

    forcefield_type = models.CharField(max_length=2,
                                       choices=FFTYPE_CHOICES,
                                       default=UNKNOWN,
                                       blank=False)

    name = models.CharField(blank=False)
    description = models.TextField()
