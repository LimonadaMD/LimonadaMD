from django.conf.urls import url
from .views import UserCreate, UserDetail, UserUpdate

urlpatterns = [
    url(r'^users/create/$', UserCreate, name='usercreate'),
    url(r'^users/(?P<pk>\d+)/$', UserDetail.as_view(), name='userdetail'),
    url(r'^users/(?P<pk>\d+)/update/$', UserUpdate, name='userupdate'),
]
