from django.conf.urls import url
from .views import MemList, MemCreate, MemDelete, MemDetail, MemUpdate
from .forms import MemFormSet

urlpatterns = [
    url(r'^membranes/$', MemList.as_view(), name='memlist'),
    url(r'^membranes/create/$', MemCreate, {'formset_class': MemFormSet, 'template': 'membranes/mem_form.html'}, name='memcreate'),
    url(r'^membranes/(?P<pk>\w+)/$', MemDetail.as_view(), name='memdetail'),
    url(r'^membranes/(?P<pk>\w+)/update/$', MemUpdate, name='memupdate'),
    url(r'^membranes/(?P<pk>\w+)/delete/$', MemDelete.as_view(), name='memdelete'),
]
