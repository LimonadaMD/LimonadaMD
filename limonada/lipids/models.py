import os
from django.db import models
from django.core.urlresolvers import reverse
from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver
from django.utils.text import slugify
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from forcefields.choices import *


def validate_lmid(value):
    if value[0:2] != "LM" and value[0:2] != "LI":
        raise ValidationError(
            _('Invalid LMID - it must start with "LM" or "LI"'),
            code='invalid',
            params={'value': value},
        )


def validate_file_extension(value):
  ext = os.path.splitext(value.name)[1]
  valid_extensions = ['.png','.jpg']
  if not ext in valid_extensions:
    raise ValidationError(u'File not supported!')


def img_path(instance, filename):
    ext = os.path.splitext(filename)[1]    
    return 'lipids/{0}{1}'.format(instance.lmid,ext)			
																	 
def directory_path(instance, filename):
    ext = os.path.splitext(filename)[1]    
    #ex.: topologies/Gromacs/Martini/POPC/version/POPC.{itp,gro,map,png} (we assume gromacs for now)
    return 'topologies/{0}/{1}/{2}/{3}/{2}{4}'.format(instance.software,instance.forcefield,instance.lipid.name,instance.version,ext)	
																	# write a procedure to check the well functioning of the topology 
																	# itp AA and UA must contain REST_ON on chiral and db, and CG Z retraint
class Lipid(models.Model):

    name = models.CharField(max_length=4,							
                            unique=True)
    lmid = models.CharField(max_length=20, 							# if not in LipidMaps, create a new ID by using LI (for limonada) + subclass + id (increment) 
                            unique=True)							
    com_name = models.CharField(max_length=200, 
                                unique=True)						  
    search_name = models.CharField(max_length=300,						  
                                   null=True)   					 
    sys_name = models.CharField(max_length=200, 
                                null=True)   					 
    iupac_name = models.CharField(max_length=500, 					
                                  null=True)   					 
    formula = models.CharField(max_length=30, 
                               null=True)   					 
    core = models.CharField(max_length=200,  
                                  null=True)   					 
    main_class = models.CharField(max_length=200,  
                                  null=True)   					 
    sub_class = models.CharField(max_length=200,   
                                 null=True)   					 	
    l4_class = models.CharField(max_length=200,   
                                 null=True)   					 	
    img = models.ImageField(upload_to=img_path,          			
                           validators=[validate_file_extension],
                           null=True)
    curator = models.ForeignKey(User,
                                on_delete=models.CASCADE)
    date = models.DateField(auto_now=True)
    slug = models.SlugField()							

    def __unicode__(self):
        return self.search_name

    def get_absolute_url(self):
        return reverse('liplist')


class Topology(models.Model):                                       # If not in CG recommend use of CGtools  

    software = models.CharField(max_length=2,
                                choices=SFTYPE_CHOICES,
                                default=GROMACS)
    forcefield = models.ForeignKey('forcefields.Forcefield', 
                                   on_delete=models.CASCADE)
    lipid = models.ForeignKey(Lipid,                                 
                              on_delete=models.CASCADE)
    itp_file = models.FileField(upload_to=directory_path)			 
    gro_file = models.FileField(upload_to=directory_path)  			 
    map_file = models.FileField(upload_to=directory_path)  			 
    version = models.CharField(max_length=30,
                               help_text="YearAuthor")
    description = models.TextField(blank=True)
    reference = models.ManyToManyField('homepage.Reference') 
    date = models.DateField(auto_now=True)
    curator = models.ForeignKey(User,
                                on_delete=models.CASCADE)						 

    def __unicode__(self):
        return "%s_%s" % (self.lipid.name,self.version)

    def get_absolute_url(self):
        return reverse('toplist')


def _delete_file(path):
    if os.path.isfile(path):
        os.remove(path)


@receiver(pre_delete, sender=Lipid)
def delete_file_pre_delete_lip(sender, instance, *args, **kwargs):
    if instance.img:
         _delete_file(instance.img.path)


@receiver(pre_delete, sender=Topology)
def delete_file_pre_delete_top(sender, instance, *args, **kwargs):
    if instance.itp_file:
         _delete_file(instance.itp_file.path)
    if instance.gro_file:
         _delete_file(instance.gro_file.path)
    if instance.map_file:
         _delete_file(instance.map_file.path)




