from django.conf.urls import url, include
from django.contrib.auth import views as auth_views
from .views import signup, update, userinfo, UserDetail
from .forms import LoginForm
from homepage.views import homepage

urlpatterns = [
    url(r'^login/$', auth_views.login, {'template_name': 'homepage/index.html', 'authentication_form': LoginForm }, name='login'),
    url(r'^logout/$', auth_views.logout, {'next_page': '/'}, name='logout'),
    url(r'^signup/$', signup, name='signup'),
    url(r'^update/$', update, name='update'),
    url(r'^userinfo/$', userinfo, name='userinfo'),
    url(r'^users/(?P<pk>\d+)/$', UserDetail.as_view(), name='userdetail'),
    url(r'^password_reset/$', auth_views.password_reset, name='password_reset'),
    url(r'^password_reset/done/$', auth_views.password_reset_done, name='password_reset_done'),
    url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        auth_views.password_reset_confirm, name='password_reset_confirm'),
    url(r'^reset/done/$', auth_views.password_reset_complete, name='password_reset_complete'),
    url(r'^verified-email-field/', include('verified_email_field.urls')),
]
