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


class Membrane(models.Model):

    name = models.CharField(max_length=200,
                            unique=True)							# help_text to set guidelines to format the name? (no space or special character)
    lipids = models.ManyToManyField('lipids.Topology',
                                    through='Composition')
    equilibration = models.PositiveSmallIntegerField()
    mem_file = models.FileField(upload_to=directory_path,		
                                help_text=".pdb and .gro files are supported",
                                validators=[validate_file_extension])
    description = models.TextField(blank=True)
    reference = models.ManyToManyField('homepage.Reference')
    date = models.DateField(auto_now=True)
    curator = models.ForeignKey(User,
                                on_delete=models.CASCADE)

    def __unicode__(self):
        return self.name


class Composition(models.Model):

    UNKNOWN = "UN"
    UPPER = "UP"
    LOWER = "LO"
    LEAFLET_CHOICES = (
        (UNKNOWN, 'Unknown'),
        (UPPER, 'Upper leaflet'),
        (LOWER, 'Lower leaflet'),
    )

    membrane = models.ForeignKey(Membrane, 
                                 on_delete=models.CASCADE)
    topology = models.ForeignKey('lipids.Topology', 
                                 on_delete=models.CASCADE)
    number = models.IntegerField()
    side = models.CharField(max_length=2,
                            choices=LEAFLET_CHOICES,
                            default=UNKNOWN)


def _delete_file(path):
    if os.path.isfile(path):
        os.remove(path)


@receiver(pre_delete, sender=Membrane)
def delete_file_pre_delete_mem(sender, instance, *args, **kwargs):
    if instance.mem_file:
         _delete_file(instance.mem_file.path)


