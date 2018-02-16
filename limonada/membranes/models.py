import os
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver
from django.core.exceptions import ValidationError


def validate_file_extension(value):
  ext = os.path.splitext(value.name)[1]
  valid_extensions = ['.gro','.pdb']
  if not ext in valid_extensions:
    raise ValidationError(u'File not supported!')


def directory_path(instance, filename):
    ext = os.path.splitext(filename)[1]
    return 'membranes/{0}{1}'.format(instance.name,ext)				


class MembraneTopol(models.Model):

    membrane = models.ForeignKey('Membrane',
                                 on_delete=models.CASCADE)
    equilibration = models.PositiveIntegerField()
    mem_file = models.FileField(upload_to=directory_path,		
                                help_text=".pdb and .gro files are supported",
                                validators=[validate_file_extension])
    forcefield = models.ForeignKey('forcefields.Forcefield',
                                   on_delete=models.CASCADE)
    nb_lipids = models.PositiveIntegerField() 
    version = models.CharField(max_length=30,
                               help_text="YearAuthor")
    description = models.TextField(blank=True)
    reference = models.ManyToManyField('homepage.Reference')
    date = models.DateField(auto_now=True)
    curator = models.ForeignKey(User,
                                on_delete=models.CASCADE)

    def __unicode__(self):
        return self.version


class Membrane(models.Model):

    name = models.TextField(unique=True)						
    lipids = models.ManyToManyField('lipids.Lipid',
                                    through='Composition')
    organism = models.CharField(max_length=30,
                                blank=True) 
    organel = models.CharField(max_length=30, 
                               blank=True) 

    def __unicode__(self):
        return self.name


class Composition(models.Model):

    UPPER = "UP"
    LOWER = "LO"
    LEAFLET_CHOICES = (
        (UPPER, 'Upper leaflet'),
        (LOWER, 'Lower leaflet'),
    )

    membrane = models.ForeignKey(Membrane, 
                                 on_delete=models.CASCADE)
    lipid = models.ForeignKey('lipids.Lipid', 
                              on_delete=models.CASCADE)
    number = models.DecimalField(max_digits=6, decimal_places=4) 
    side = models.CharField(max_length=2,
                            choices=LEAFLET_CHOICES,
                            default=UPPER)


def _delete_file(path):
    if os.path.isfile(path):
        os.remove(path)


@receiver(pre_delete, sender=Membrane)
def delete_file_pre_delete_mem(sender, instance, *args, **kwargs):
    if instance.mem_file:
         _delete_file(instance.mem_file.path)


