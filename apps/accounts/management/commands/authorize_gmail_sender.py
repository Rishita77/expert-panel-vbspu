"""Authorize the dedicated Gmail sender once and store its refresh token locally."""

import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Open Google's one-time sender authorization and save a local refresh token."

    def add_arguments(self, parser):
        parser.add_argument(
            "--client-secrets",
            default=settings.BASE_DIR / ".local" / "gmail-oauth-client.json",
            help="Google OAuth desktop-client JSON file.",
        )
        parser.add_argument(
            "--output",
            default=settings.BASE_DIR / ".local" / "gmail-oauth-refresh-token.json",
            help="Local private output file for the Railway refresh-token secret.",
        )

    def handle(self, *args, **options):
        from google_auth_oauthlib.flow import InstalledAppFlow

        client_path = Path(options["client_secrets"])
        output_path = Path(options["output"])
        if not client_path.is_file():
            raise CommandError("Google OAuth desktop-client JSON file नहीं मिला।")
        if output_path.exists():
            raise CommandError("स्थानीय refresh-token file पहले से मौजूद है। पहले उसे सुरक्षित रखें या हटाएँ।")
        flow = InstalledAppFlow.from_client_secrets_file(
            client_path, scopes=["https://www.googleapis.com/auth/gmail.send"]
        )
        credentials = flow.run_local_server(port=0, open_browser=True, prompt="consent")
        if not credentials.refresh_token:
            raise CommandError(
                "Google ने refresh token नहीं दिया। पहले पुरानी अनुमति हटाकर पुनः प्रयास करें।"
            )
        output_path.write_text(
            json.dumps({"refresh_token": credentials.refresh_token}, indent=2), encoding="utf-8"
        )
        self.stdout.write(
            self.style.SUCCESS(
                "स्थानीय refresh-token file बन गई है। इसका मान Railway secret में रखें; "
                "इसे source control में न डालें।"
            )
        )
