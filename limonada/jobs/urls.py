from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^jobs', views.jobs, name='jobs'),
]
