from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from .views import LipList, LipCreate, LipDelete, LipDetail, LipUpdate, LipAutocomplete 
from .views import TopList, TopCreate, TopDelete, TopUpdate

urlpatterns = [
    url(r'^lipids/$', LipList, name='liplist'),
    url(r'^lipids/create/$', LipCreate, name='lipcreate'),
    url(r'^lipids/(?P<slug>\w+)/$', LipDetail.as_view(), name='lipdetail'),
    url(r'^lipids/(?P<slug>\w+)/update/$', LipUpdate, name='lipupdate'),
    url(r'^lipids/(?P<slug>\w+)/delete/$', login_required(LipDelete.as_view()), name='lipdelete'),
    url(r'^lipid-autocomplete/$', LipAutocomplete.as_view(), name='lipid-autocomplete'),
    url(r'^topologies/$', TopList, name='toplist'),
    url(r'^topologies/create/$', login_required(TopCreate.as_view()), name='topcreate'),
    url(r'^topologies/(?P<pk>\d+)/update/$', login_required(TopUpdate.as_view()), name='topupdate'),
    url(r'^topologies/(?P<pk>\d+)/delete/$', login_required(TopDelete.as_view()), name='topdelete'),
]

