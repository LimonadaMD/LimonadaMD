from django.db import models
from django.core.urlresolvers import reverse


class Reference(models.Model):

    authors = models.CharField(max_length=200)
    title = models.CharField(max_length=200,
                             unique=True)
    journal = models.CharField(max_length=200)
    num = models.CharField(max_length=30,
                           null=True)
    pages = models.CharField(max_length=30,
                             null=True)
    year = models.CharField(max_length=4)
    doi = models.CharField(max_length=30,
                           null=True)

    def __unicode__(self):
        return "%s et al. %s: %s" % (self.authors.split(",")[0],self.year, self.title)

    def get_absolute_url(self):
        return reverse('reflist')


