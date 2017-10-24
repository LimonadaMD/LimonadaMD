from django.db import models


def directory_path(instance, filename):
    return 'membranes/{0}'.format(filename)							# use name property instead of filename 


class Membrane(models.Model):

    name = models.CharField(max_length=200)							# help_text to set guidelines to format the name? (no space or special character)
    lipids = models.ManyToManyField('lipids.Topology',
                                    through='Composition')
    equilibration =  models.CharField(max_length=30,				# help_text="ex.: During 250 ns"
                                      default="Not done")
    mem_file = models.FileField(upload_to=directory_path)			# pdb or gro (in forms.py)
    description = models.TextField(blank=True)
    reference = models.ManyToManyField('homepage.Reference')
    date = models.DateField(auto_now=True)
    #curator = models.ManyToManyField('users.User', 						
    #                                 on_delete=models.SET_NULL)

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


