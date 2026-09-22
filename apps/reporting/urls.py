from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="reporting_home"),
    path("<slug:slug>/", views.report, name="reporting_report"),
    path("<slug:slug>/export.csv", views.export_csv, name="reporting_export"),
]
