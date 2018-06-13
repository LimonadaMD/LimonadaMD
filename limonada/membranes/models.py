import os
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver
from django.core.exceptions import ValidationError
from django.conf import settings
from forcefields.choices import *


def validate_file_extension(value):
  ext = os.path.splitext(value.name)[1]
  valid_extensions = ['.gro','.pdb']
  if not ext in valid_extensions:
    raise ValidationError(u'File not supported!')


def directory_path(instance, filename):
    ext = os.path.splitext(filename)[1]
    filepath = 'membranes/LIM{0}_{1}{2}'.format(instance.id,instance.name,ext)
    if os.path.isfile(os.path.join(settings.MEDIA_ROOT, filepath)):
       os.remove(os.path.join(settings.MEDIA_ROOT, filepath))
    return filepath


class MembraneTopol(models.Model):

    name = models.CharField(max_length=30)
                            #help_text="AuthorYear_Mammal1024")
    membrane = models.ForeignKey('Membrane',
                                 null=True,
                                 on_delete=models.CASCADE)
    lipids = models.ManyToManyField('lipids.Lipid',
                                    through='TopolComposition')
    temperature = models.PositiveIntegerField()
    equilibration = models.PositiveIntegerField()
    mem_file = models.FileField(upload_to=directory_path,		
                                help_text=".pdb and .gro files are supported",
                                validators=[validate_file_extension],
                                blank=True, 
                                null=True)
    compo_file = models.FileField(upload_to=directory_path,		
                                  blank=True, 
                                  null=True)
    software = models.CharField(max_length=4,
                                choices=SFTYPE_CHOICES,
                                default=GROMACS50)
    forcefield = models.ForeignKey('forcefields.Forcefield',                     
                                   on_delete=models.CASCADE)
    nb_lipids = models.PositiveIntegerField(null=True) 
    description = models.TextField(blank=True)
    reference = models.ManyToManyField('homepage.Reference')
    date = models.DateField(auto_now=True)
    curator = models.ForeignKey(User,
                                on_delete=models.CASCADE)
    # salt []

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.id is None:
            saved_mem_file = self.mem_file
            self.mem_file = None
            super(MembraneTopol, self).save(*args, **kwargs)
            self.mem_file = saved_mem_file
        super(MembraneTopol, self).save(*args, **kwargs)


class TopolComposition(models.Model):

    UPPER = "UP"
    LOWER = "LO"
    LEAFLET_CHOICES = (
        (UPPER, 'Upper leaflet'),
        (LOWER, 'Lower leaflet'),
    )

    membrane = models.ForeignKey(MembraneTopol, 
                                 on_delete=models.CASCADE)
    lipid = models.ForeignKey('lipids.Lipid', 
                              on_delete=models.CASCADE)
    topology = models.ForeignKey('lipids.Topology', 
                                  on_delete=models.CASCADE)
    number = models.PositiveIntegerField() 
    side = models.CharField(max_length=2,
                            choices=LEAFLET_CHOICES,
                            default=UPPER)


class Membrane(models.Model):

    name = models.TextField(unique=True,null=True,blank=True)						
    lipids = models.ManyToManyField('lipids.Lipid',
                                    through='Composition')
    tag = models.ManyToManyField('membranes.MembraneTag', 
                                 blank=True) 
    nb_liptypes = models.PositiveIntegerField(null=True) 

    def __unicode__(self):
        return self.name


class MembraneTag(models.Model):

    tag = models.CharField(max_length=30,
                           unique=True) 

    def __unicode__(self):
        return self.tag


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
    number = models.DecimalField(max_digits=7, decimal_places=4) 
    side = models.CharField(max_length=2,
                            choices=LEAFLET_CHOICES,
                            default=UPPER)


def _delete_file(path):
    if os.path.isfile(path):
        os.remove(path)


@receiver(pre_delete, sender=MembraneTopol)
def delete_file_pre_delete_mem(sender, instance, *args, **kwargs):
    if instance.mem_file:
         _delete_file(instance.mem_file.path)
    if instance.compo_file:
         _delete_file(instance.compo_file.path)


