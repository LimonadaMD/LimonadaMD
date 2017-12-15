from django.conf.urls import url 
from django.contrib.auth.decorators import login_required
from .views import homepage, RefList, RefCreate, RefDelete, RefUpdate 

urlpatterns = [
    url(r'^$', homepage, name='homepage'),
    url(r'^references/$', RefList.as_view(), name='reflist'),
    url(r'^references/create/$', login_required(RefCreate.as_view()), name='refcreate'),
    url(r'^references/(?P<pk>\d+)/update/$', login_required(RefUpdate.as_view()), name='refupdate'),
    url(r'^references/(?P<pk>\d+)/delete/$', login_required(RefDelete.as_view()), name='refdelete'),
]
