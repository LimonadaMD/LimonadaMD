from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^builder/', views.builder, name='builder'),
]
