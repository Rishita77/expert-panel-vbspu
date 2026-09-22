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
