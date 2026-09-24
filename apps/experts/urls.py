from django.urls import path

from . import import_preview, views

urlpatterns = [
    path("import/", import_preview.preview, name="expert_import"),
    path("import/template/", import_preview.template, name="expert_import_template"),
    path("<str:kind>/", views.listing, name="expert_list"),
    path("<str:kind>/new/", views.edit, name="expert_new"),
    path("<str:kind>/for/<uuid:parent>/new/", views.edit, name="expert_child_new"),
    path("<str:kind>/<uuid:pk>/", views.detail, name="expert_detail"),
    path("<str:kind>/<uuid:pk>/edit/", views.edit, name="expert_edit"),
]
