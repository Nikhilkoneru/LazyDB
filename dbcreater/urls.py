from django.urls import path
from . import views

urlpatterns = [
  path("create", views.create, name='create'),
  path("downloads", views.download, name='downloads'),
  path("", views.index, name='index'),
  path("assistant_hook", views.assistant_hook, name='assistant_hook'),
]