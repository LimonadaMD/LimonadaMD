from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from .views import FfList, FfCreate, FfDelete, FfUpdate

urlpatterns = [ 
    url(r'^forcefields/$', FfList, name='fflist'),
    url(r'^forcefields/create/$', login_required(FfCreate.as_view()), name='ffcreate'),
    url(r'^forcefields/(?P<pk>\d+)/update/$', login_required(FfUpdate.as_view()), name='ffupdate'),
    url(r'^forcefields/(?P<pk>\d+)/delete/$', login_required(FfDelete.as_view()), name='ffdelete'),
]

