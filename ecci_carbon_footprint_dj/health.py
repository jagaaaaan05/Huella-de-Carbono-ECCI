"""Health check endpoint for the load balancer.

Runs before the rest of the middleware so it answers even when the request
Host is the container IP (not in ALLOWED_HOSTS) and without HTTPS redirects.
"""

from django.db import connection
from django.http import JsonResponse

HEALTH_PATH = '/health/'


class HealthCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path != HEALTH_PATH:
            return self.get_response(request)

        try:
            connection.ensure_connection()
        except Exception:
            return JsonResponse({'status': 'error', 'database': 'unavailable'}, status=503)
        return JsonResponse({'status': 'ok'})
