from django.conf.urls import url 
from django.contrib.auth.decorators import login_required
from .views import homepage, RefList, RefCreate, RefDelete, RefUpdate, ReferenceAutocomplete

urlpatterns = [
    url(r'^$', homepage, name='homepage'),
    url(r'^references/$', RefList, name='reflist'),
    url(r'^references/create/$', RefCreate, name='refcreate'),
    url(r'^references/(?P<pk>\d+)/update/$', RefUpdate, name='refupdate'),
    url(r'^references/(?P<pk>\d+)/delete/$', login_required(RefDelete.as_view()), name='refdelete'),
    url(r'^reference-autocomplete/$', ReferenceAutocomplete.as_view(), name='reference-autocomplete'),
]
