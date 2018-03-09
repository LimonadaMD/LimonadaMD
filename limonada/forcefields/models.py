import os
from django.contrib.auth.models import User
from django.db import models
from django.core.urlresolvers import reverse
from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver
from django.core.exceptions import ValidationError
from .choices import *


def validate_file_extension(value):
  ext = os.path.splitext(value.name)[1]
  valid_extensions = ['.zip']
  if not ext in valid_extensions:
    raise ValidationError(u'File not supported!')


def ff_path(instance, filename):
    return 'forcefields/Gromacs/{0}.ff.zip'.format(instance.name)						


def mdp_path(instance, filename):
    return 'forcefields/Gromacs/{0}.mdp.zip'.format(instance.name)						


class Forcefield(models.Model):									

    name = models.CharField(max_length=30,
                            unique=True)
    forcefield_type = models.CharField(max_length=2,
                                       choices=FFTYPE_CHOICES,
                                       default=ALLATOM) 
    ff_file = models.FileField(upload_to=ff_path,
                               validators=[validate_file_extension],			  
                               help_text="Use a zip file containing the forcefield directory as in <link>") 
    mdp_file = models.FileField(upload_to=mdp_path,
                               validators=[validate_file_extension],			  
                               help_text="Use a zip file containing the mdps for the version X of Gromacs as in <link>")
    software = models.CharField(max_length=2,     					
                                choices=SFTYPE_CHOICES,
                                default=GROMACS) 
    description = models.TextField(blank=True)					
    reference = models.ManyToManyField('homepage.Reference') 
    curator = models.ForeignKey(User,
                                on_delete=models.CASCADE)
    date = models.DateField(auto_now=True)

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('fflist')


def _delete_file(path):
    if os.path.isfile(path):
        os.remove(path)


@receiver(pre_delete, sender=Forcefield)
def delete_file_pre_delete_ff(sender, instance, *args, **kwargs):
    if instance.ff_file:
         _delete_file(instance.ff_file.path)
    if instance.mdp_file:
         _delete_file(instance.mdp_file.path)



