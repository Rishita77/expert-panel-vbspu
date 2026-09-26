from django.urls import include, path

from apps.accounts import views as accounts
from apps.cases import views
from apps.institutions import bulk_import as institution_bulk_import

urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),
    path("office/allocation/", include("apps.nominations.urls")),
    path("office/catalog/", include("apps.experts.urls")),
    path("office/reports/", include("apps.reporting.urls")),
    path("office/login/", accounts.sign_in, name="login"),
    path("office/login/verify-email/", accounts.email_otp_verify, name="email_otp_verify"),
    path("office/login/resend-email-code/", accounts.email_otp_resend, name="email_otp_resend"),
    path("office/logout/", accounts.sign_out, name="logout"),
    path("office/account/password/", accounts.password_change, name="password_change"),
    path(
        "office/institutions/import/",
        institution_bulk_import.upload,
        name="institution_bulk_import",
    ),
    path(
        "office/institutions/import/template/",
        institution_bulk_import.template,
        name="institution_import_template",
    ),
    path(
        "office/staff/<uuid:pk>/credentials/",
        accounts.issue_credentials,
        name="issue_credentials",
    ),
    path("office/", views.home, name="office_home"),
    path("office/<str:kind>/", views.listing, name="office_list"),
    path("office/<str:kind>/new/", views.edit, name="office_new"),
    path("office/<str:kind>/<uuid:pk>/", views.detail, name="office_detail"),
    path("office/<str:kind>/<uuid:pk>/edit/", views.edit, name="office_edit"),
    path("", include("apps.workspace.urls")),
]
