from django.db import models
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
import requests, datetime


def validate_year(value):
    if value < 1950 or value > datetime.datetime.now().year:
        raise ValidationError(
            _('Year must be > 1950 and < %(value)s'),
           # _('%(value)s is not valid'),
           # code='invalid',
            params={'value': datetime.datetime.now().year},
        )


def validate_doi(value):
    url = "http://dx.doi.org/%s" % value
    headers = {'Accept': 'application/citeproc+json'}
    try:
        response = requests.get(url,headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as err:
        raise ValidationError(
            _('%(value)s is not valid'),
            code='invalid',
            params={'value': value},
        )


class Reference(models.Model):

    refid = models.CharField(max_length=200,
                             help_text="Format: AuthorYear[Index]",
                             unique=True)
    authors = models.CharField(max_length=200)
    title = models.CharField(max_length=200)
    journal = models.CharField(max_length=200)
    volume = models.CharField(max_length=30,
                              null=True)
    year = models.PositiveSmallIntegerField(validators=[validate_year])
    doi = models.CharField(max_length=30,
                           validators=[validate_doi],
                           unique=True,
                           null=True)
    curator = models.ForeignKey(User,
                                on_delete=models.CASCADE)
    date = models.DateField(auto_now=True)

    def __unicode__(self):
        return self.refid

    def get_absolute_url(self):
        return reverse('reflist')


