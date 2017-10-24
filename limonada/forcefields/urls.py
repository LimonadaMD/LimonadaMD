from django.conf.urls import url
from .views import FfList, FfCreate, FfDelete, FfDetail, FfUpdate

urlpatterns = [ 
    url(r'^forcefields/$', FfList.as_view(), name='fflist'),
    url(r'^forcefields/create/$', FfCreate.as_view(), name='ffcreate'),
    url(r'^forcefields/(?P<pk>\d+)/$', FfDetail.as_view(), name='ffdetail'),
    url(r'^forcefields/(?P<pk>\d+)/update/$', FfUpdate.as_view(), name='ffupdate'),
    url(r'^forcefields/(?P<pk>\d+)/delete/$', FfDelete.as_view(), name='ffdelete'),
]

