from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import redirect, resolve_url
from django.utils.http import urlencode


class LoginRequiredMiddleware:
    """
    Exige sesión iniciada en TODAS las rutas, salvo las listadas en
    settings.LOGIN_EXEMPT_URLS (prefijos de ruta) y la propia página de login.

    - Peticiones normales: redirige al login con ?next=
    - Peticiones AJAX / fetch: responde 401 en JSON
    - Peticiones htmx: responde 401 con cabecera HX-Redirect al login
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.login_url = resolve_url(settings.LOGIN_URL)
        self.exentas = tuple(getattr(settings, "LOGIN_EXEMPT_URLS", ()))

    def __call__(self, request):
        if request.user.is_authenticated or self._es_publica(request.path_info):
            return self.get_response(request)

        siguiente = urlencode({"next": request.get_full_path()})
        destino = f"{self.login_url}?{siguiente}"

        # htmx (hx-boost / hx-get ...)
        if request.headers.get("HX-Request"):
            respuesta = JsonResponse({"error": "No autenticado"}, status=401)
            respuesta["HX-Redirect"] = destino
            return respuesta

        # AJAX / fetch
        es_ajax = (
            request.headers.get("X-Requested-With") == "XMLHttpRequest"
            or "application/json" in request.headers.get("Accept", "")
        )
        if es_ajax:
            return JsonResponse(
                {"error": "No autenticado", "login_url": destino}, status=401
            )

        return redirect(destino)

    def _es_publica(self, path):
        if path == self.login_url:
            return True
        return path.startswith(self.exentas)