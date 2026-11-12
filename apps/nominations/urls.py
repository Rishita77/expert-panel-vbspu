from django.urls import path

from . import views

urlpatterns = [
    path("run/<uuid:pk>/replace/<uuid:outgoing>/", views.choose_member, {"locked": False}, name="replace_proposed"),
    path("final-selection/<uuid:pk>/replace/<uuid:outgoing>/", views.choose_member, {"locked": True}, name="replace_locked"),
    path("documents/", views.document_queue, name="document_queue"),
    path("demo/", views.demo, name="allocation_demo"),
    path("request/<uuid:pk>/", views.workbench, name="allocation_workbench"),
    path("run/<uuid:pk>/", views.run_detail, name="allocation_run"),
    path(
        "run/<uuid:pk>/final-selection/start/",
        views.start_final_selection,
        name="final_selection_start",
    ),
    path("final-selection/<uuid:pk>/", views.final_selection, name="final_selection"),
    path(
        "final-selection/<uuid:pk>/change/start/",
        views.panel_change_start,
        name="panel_change_start",
    ),
    path("panel-change/<uuid:pk>/", views.panel_change, name="panel_change"),
    path("letter/<uuid:pk>/", views.letter, name="letter"),
    path("letter/<uuid:pk>/download/", views.letter_download, name="letter_download"),
    path("run/<uuid:pk>/letter/start/", views.start_offer_letter, name="offer_letter_start"),
    path(
        "final-selection/<uuid:pk>/letter/start/",
        views.start_final_letter,
        name="final_letter_start",
    ),
    path(
        "panel-change/<uuid:pk>/letter/start/",
        views.start_change_letter,
        name="change_letter_start",
    ),
]
