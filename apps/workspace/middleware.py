from django.utils.translation import get_language

from .translations import translate_html_to_english


class PreviewHeadersMiddleware:
    """Preview input is neither stored nor made cacheable."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response["Cache-Control"] = "no-store"
        response["X-Robots-Tag"] = "noindex, nofollow"
        response["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response


class InterfaceTranslationMiddleware:
    """Translate controlled interface text after templates and forms are rendered."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if (
            get_language() != "en"
            or response.streaming
            or not response.get("Content-Type", "").startswith("text/html")
        ):
            return response
        response.content = translate_html_to_english(response.content.decode("utf-8")).encode("utf-8")
        response["Content-Language"] = "en"
        return response
