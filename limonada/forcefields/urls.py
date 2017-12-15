from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from .views import FfList, FfCreate, FfDelete, FfUpdate, ReferenceAutocomplete

urlpatterns = [ 
    url(r'^forcefields/$', FfList.as_view(), name='fflist'),
    url(r'^forcefields/create/$', login_required(FfCreate.as_view()), name='ffcreate'),
    url(r'^forcefields/(?P<pk>\d+)/update/$', login_required(FfUpdate.as_view()), name='ffupdate'),
    url(r'^forcefields/(?P<pk>\d+)/delete/$', login_required(FfDelete.as_view()), name='ffdelete'),
    #url(r'^reference-autocomplete/$', ReferenceAutocomplete.as_view(), name='reference-autocomplete'),
]

