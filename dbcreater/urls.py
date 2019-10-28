from django.contrib import admin
from django.urls import include, path
from . import views
urlpatterns = [
  path("create/", views.create, name='create'),
  path("download", views.download, name='download'),
  path("index", views.index, name='index'),
  path("assistant_hook/", views.assistant_hook, name='assistant_hook'),
]