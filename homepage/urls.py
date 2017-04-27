from django.conf.urls import url

from . import views

app_name = 'dota'

urlpatterns = [
    url(r'^$', views.winrateHome, name='winrateHome'),
    url(r'^result/', views.winrateResult, name='winrateResult')
]
