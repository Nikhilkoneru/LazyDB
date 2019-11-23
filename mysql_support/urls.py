from django.urls import path
from . import views

urlpatterns = [
                  path("mysql", views.index, name='index')
              ]