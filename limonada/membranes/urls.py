from django.conf.urls import url
from .views import MemList, MemCreate, MemDelete, MemDetail, MemUpdate

urlpatterns = [
    #url(r'^membranes/$', membranes, name='membranes'),
    #url(r'^membrane_edit', membrane_edit, name='membrane_edit'),
    url(r'^membranes/$', MemList.as_view(), name='memlist'),
    url(r'^membranes/create/$', MemCreate, name='memcreate'),
    url(r'^membranes/(?P<pk>\w+)/$', MemDetail.as_view(), name='memdetail'),
    url(r'^membranes/(?P<pk>\w+)/update/$', MemUpdate, name='memupdate'),
    url(r'^membranes/(?P<pk>\w+)/delete/$', MemDelete.as_view(), name='memdelete'),
]
