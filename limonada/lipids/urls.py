from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from .views import LipList, LipCreate, LipDelete, LipDetail, LipUpdate, LipSearch
from .views import TopList, TopCreate, TopDelete, TopDetail, TopUpdate

urlpatterns = [
    url(r'^lipids/$', LipList.as_view(), name='liplist'),
    url(r'^lipids/search/$', LipSearch, name='lipsearch'),
    url(r'^lipids/create/$', LipCreate, name='lipcreate'),
    url(r'^lipids/(?P<slug>\w+)/$', LipDetail.as_view(), name='lipdetail'),
    url(r'^lipids/(?P<slug>\w+)/update/$', login_required(LipUpdate.as_view()), name='lipupdate'),
    url(r'^lipids/(?P<slug>\w+)/delete/$', login_required(LipDelete.as_view()), name='lipdelete'),
    url(r'^topologies/$', TopList.as_view(), name='toplist'),
    url(r'^topologies/create/$', login_required(TopCreate.as_view()), name='topcreate'),
    url(r'^topologies/(?P<pk>\d+)/$', TopDetail.as_view(), name='topdetail'),
    url(r'^topologies/(?P<pk>\d+)/update/$', login_required(TopUpdate.as_view()), name='topupdate'),
    url(r'^topologies/(?P<pk>\d+)/delete/$', login_required(TopDelete.as_view()), name='topdelete'),
]

