from django.conf.urls import url
from .views import LipList, LipCreate, LipDelete, LipDetail, LipUpdate, LipSearch
from .views import TopList, TopCreate, TopDelete, TopDetail, TopUpdate

urlpatterns = [
    url(r'^lipids/$', LipList.as_view(), name='liplist'),
    url(r'^lipids/search/$', LipSearch, name='lipsearch'),
    url(r'^lipids/create/$', LipCreate, name='lipcreate'),
    url(r'^lipids/(?P<slug>\w+)/$', LipDetail.as_view(), name='lipdetail'),
    url(r'^lipids/(?P<slug>\w+)/update/$', LipUpdate.as_view(), name='lipupdate'),
    url(r'^lipids/(?P<slug>\w+)/delete/$', LipDelete.as_view(), name='lipdelete'),
    url(r'^topologies/$', TopList.as_view(), name='toplist'),
    url(r'^topologies/create/$', TopCreate.as_view(), name='topcreate'),
    url(r'^topologies/(?P<pk>\d+)/$', TopDetail.as_view(), name='topdetail'),
    url(r'^topologies/(?P<pk>\d+)/update/$', TopUpdate.as_view(), name='topupdate'),
    url(r'^topologies/(?P<pk>\d+)/delete/$', TopDelete.as_view(), name='topdelete'),
]

