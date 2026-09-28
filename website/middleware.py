from django.conf import settings
from django.http import HttpResponse

from .ratelimit import get_client_ip, is_rate_limited


class SecurityHeadersMiddleware:
    """Adds a Content-Security-Policy and related hardening headers to every
    response. Kept strict (no 'unsafe-inline' anywhere) by moving all JS/CSS
    that used to be inline into static files.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        gs_bucket = settings.GS_BUCKET_NAME
        img_sources = "'self' data:"
        if gs_bucket:
            img_sources += f" https://storage.googleapis.com"

        response["Content-Security-Policy"] = (
            "default-src 'self'; "
            f"img-src {img_sources}; "
            "style-src 'self' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "script-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        response["Referrer-Policy"] = "same-origin"
        response["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=()"
        )
        response["Cross-Origin-Opener-Policy"] = "same-origin"
        response["Cross-Origin-Resource-Policy"] = "same-origin"
        response.setdefault("X-Content-Type-Options", "nosniff")
        return response


class AdminBruteForceMiddleware:
    """Rate-limits POSTs to the (hidden) Django admin login by IP. The admin
    login is the one entry point that doesn't go through our own rate-limited
    views, so it's covered separately here.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.login_path = f"/{settings.ADMIN_URL}login/"

    def __call__(self, request):
        if (
            settings.RATE_LIMIT_ACTIVE
            and request.method == "POST"
            and request.path == self.login_path
        ):
            ip = get_client_ip(request)
            if is_rate_limited(
                f"admin-login:{ip}",
                settings.RATE_LIMIT_LOGIN_MAX,
                settings.RATE_LIMIT_LOGIN_WINDOW,
            ):
                return HttpResponse(
                    "Demasiados intentos. Intenta de nuevo en unos minutos.",
                    status=429,
                )
        return self.get_response(request)
