from django.contrib import admin
from django.urls import include, path
from . import views
urlpatterns = [
  path("create/", views.create, name='create'),
  path("download", views.download, name='download'),
]