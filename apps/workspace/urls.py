from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("intake/", views.intake, name="intake"),
    path("policies/", views.policies, name="policies"),
    path("health/", views.health, name="health"),
]
