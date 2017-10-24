from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^membranes', views.membranes, name='membranes'),
    url(r'^membrane_edit', views.membrane_edit, name='membrane_edit'),
]
