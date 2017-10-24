from django.conf.urls import url 
from .views import homepage, RefList, RefCreate, RefDelete, RefDetail, RefUpdate

urlpatterns = [
    url(r'^$', homepage, name='homepage'),
    url(r'^references/$', RefList.as_view(), name='reflist'),
    url(r'^references/create/$', RefCreate.as_view(), name='refcreate'),
    url(r'^references/(?P<pk>\d+)/$', RefDetail.as_view(), name='refdetail'),
    url(r'^references/(?P<pk>\d+)/update/$', RefUpdate.as_view(), name='refupdate'),
    url(r'^references/(?P<pk>\d+)/delete/$', RefDelete.as_view(), name='refdelete'),
]
