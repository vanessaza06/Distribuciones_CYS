import os, sys, django
sys.path.insert(0, os.path.abspath('.'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.middleware import MessageMiddleware
from app.views.metodo_de_pago.views import lista_metodos_pago
import re

rf = RequestFactory()
req = rf.get('/metodos-pago/')
middleware = SessionMiddleware(lambda r: None)
middleware.process_request(req)
req.session.save()
msg_middleware = MessageMiddleware(lambda r: None)
msg_middleware.process_request(req)

req.user = AnonymousUser()
req.session['usuario_id'] = 1
res = lista_metodos_pago(req)
html = res.content.decode('utf-8')

for m in re.finditer(r'(<(?:button|a)[^>]*class="[^"]*(?:btn|mp-tab|mp-turno|paginate)[^"]*"[^>]*>[\s\S]*?<\/(?:button|a)>)', html):
    tag = m.group(1).strip()
    tag_cleaned = re.sub(r'\s+', ' ', tag)
    print("BUTTON:", tag_cleaned[:180])

