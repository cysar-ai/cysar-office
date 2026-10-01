import odoo
from odoo.http.router import Application

_call = Application.__call__


def _call_with_forwarded_host(self, environ, start_response):
    """O acesso público é HTTPS, mas o proxy entrega a requisição como HTTP.

    O Google recusa redirect_uri em HTTP. Com proxy_mode ligado, esta
    camada garante host e protocolo antes de o Odoo montar a URI.
    """
    if odoo.tools.config.get("proxy_mode"):
        environ["wsgi.url_scheme"] = "https"
        if not environ.get("HTTP_X_FORWARDED_HOST") and environ.get("HTTP_HOST"):
            environ["HTTP_X_FORWARDED_HOST"] = environ["HTTP_HOST"]
        environ["HTTP_X_FORWARDED_PROTO"] = "https"
    return _call(self, environ, start_response)


Application.__call__ = _call_with_forwarded_host
