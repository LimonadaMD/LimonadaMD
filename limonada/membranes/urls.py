from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from .views import MemList, MemCreate, MemDelete, MemDetail, MemUpdate, GetLipTops, GetFiles, MembraneTagAutocomplete
from .forms import MemFormSet

urlpatterns = [
    url(r'^membranes/$', MemList, name='memlist'),
    url(r'^membranes/create/$', MemCreate, {'formset_class': MemFormSet, 'template': 'membranes/mem_form.html'}, name='memcreate'),
    url(r'^membranes/(?P<pk>\d+)/$', MemDetail.as_view(), name='memdetail'),
    url(r'^membranes/(?P<pk>\d+)/update/$', MemUpdate, name='memupdate'),
    url(r'^membranes/(?P<pk>\d+)/delete/$', login_required(MemDelete.as_view()), name='memdelete'),
    url(r'^getliptops/$', GetLipTops, name='getliptops'),
    url(r'^getfiles/$', GetFiles, name='getfiles'),
    url(r'^membranetag-autocomplete/$', MembraneTagAutocomplete.as_view(create_field='tag'), name='membranetagautocomplete'),
    url(r'^tag-autocomplete/$', MembraneTagAutocomplete.as_view(), name='tag-autocomplete'),
]
