from django.urls import path

from . import import_preview, views

urlpatterns = [
    path("import/", import_preview.preview, name="expert_import"),
    path("import/experts/", import_preview.bulk_expert_import, name="bulk_expert_import"),
    path("import/experts/template/", import_preview.bulk_expert_template, name="bulk_expert_template"),
    path("import/references/", import_preview.references, name="expert_references"),
    path("import/template/<str:kind>/", import_preview.template, name="expert_template"),
    path("<str:kind>/", views.listing, name="expert_list"),
    path("<str:kind>/new/", views.edit, name="expert_new"),
    path("<str:kind>/for/<uuid:parent>/new/", views.edit, name="expert_child_new"),
    path("<str:kind>/<uuid:pk>/", views.detail, name="expert_detail"),
    path("<str:kind>/<uuid:pk>/edit/", views.edit, name="expert_edit"),
]
