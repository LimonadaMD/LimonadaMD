from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from .views import MemList, MemCreate, MemDelete, MemUpdate, TestAutocomplete
from .forms import MemFormSet

urlpatterns = [
    url(r'^membranes/$', MemList, name='memlist'),
    url(r'^membranes/create/$', MemCreate, {'formset_class': MemFormSet, 'template': 'membranes/mem_form.html'}, name='memcreate'),
    url(r'^membranes/(?P<pk>\w+)/update/$', MemUpdate, name='memupdate'),
    url(r'^membranes/(?P<pk>\w+)/delete/$', login_required(MemDelete.as_view()), name='memdelete'),
    url(r'^membranes/test_autocomplete/$', TestAutocomplete, name='testautocomplete'),
]
