import os
from django.db import models
from django.core.urlresolvers import reverse
from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver
from django.utils.text import slugify


def img_path(instance, filename):
    ext = os.path.splitext(filename)[1]    
    return 'lipids/{0}/{0}{1}'.format(instance.lmid,ext)			
																	 
def directory_path(instance, filename):
    ext = os.path.splitext(filename)[1]    
    #ex.: topologies/Gromacs/Martini/POPC/version/POPC.{itp,gro,map,png} (we assume gromacs for now)
    return 'topologies/{0}/{1}/{2}/{3}/{2}{4}'.format(instance.software,instance.forcefield,instance.lipid.name,instance.version,ext)	
																	# write a procedure to check the well functioning of the topology 
																	# itp AA and UA must contain REST_ON on chiral and db, and CG Z retraint
class Lipid(models.Model):

    name = models.CharField(max_length=4,							# helt_text to set guidelines to format the name => [0-9A-Z]{4} (=> 1679616 possibilities)
                            unique=True)
    lmid = models.CharField(max_length=20, 							# if not in LipidMaps, create a new ID by using LI (for limonada) + subclass + id (increment) 
                            unique=True)							
    com_name = models.CharField(max_length=200, 
                                unique=True)						# name, lmid and com_name are unique because they can be used indifferently in the builder  
    sys_name = models.CharField(max_length=200, 
                                null=True)   					 
    iupac_name = models.CharField(max_length=200, 					
                                  null=True)   					 
    formula = models.CharField(max_length=30, 
                               null=True)   					 
    main_class = models.CharField(max_length=200,  
                                  null=True)   					 
    sub_class = models.CharField(max_length=200,   
                                 null=True)   					 	# sys_name, iupac_name, formula, main_class, sub_class will be used in case of the implementation of a search fct
    img = models.FileField(upload_to=img_path,          			# add a button to download the mol file from LipidMaps and be able to draw the lipid image
                           null=True)
    date = models.DateField(auto_now=True)
    #curator = models.ManyToManyField('users.User',						 
    #                                 on_delete=models.SET_NULL)
    slug = models.SlugField()							

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('liplist')

    def save(self, *args, **kwargs):
        if not self.id:
            self.slug = slugify(self.lmid)
        super(Lipid, self).save(*args, **kwargs)
    

class Topology(models.Model):                                       # must be in CG before adding (specify the version) else recommend use of CGtools  

    GROMACS = "GR"
    SFTYPE_CHOICES = (
        (GROMACS, 'Gromacs'),
    )

    software = models.CharField(max_length=2,
                                choices=SFTYPE_CHOICES,
                                default=GROMACS)
    forcefield = models.ForeignKey('forcefields.Forcefield', 
                                   on_delete=models.CASCADE)
    lipid = models.ForeignKey(Lipid,                                 
                              on_delete=models.CASCADE)
    itp_file = models.FileField(upload_to=directory_path)			# itp (in forms.py) 
    gro_file = models.FileField(upload_to=directory_path)  			# gro (in forms.py) 
    map_file = models.FileField(upload_to=directory_path)  			# map (in forms.py) 
    version = models.CharField(max_length=30)  						# help_text to set guidelines to format the version name => YearAuthor
    description = models.TextField(blank=True)
    reference = models.ManyToManyField('homepage.Reference') 
    date = models.DateField(auto_now=True)
    #curator = models.ManyToManyField('users.User',						 
    #                                 on_delete=models.SET_NULL)

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
    if instance.itp_file:
         _delete_file(instance.itp_file.path)
    if instance.gro_file:
         _delete_file(instance.gro_file.path)
    if instance.map_file:
         _delete_file(instance.map_file.path)




