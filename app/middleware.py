from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.templating import Jinja2Templates

from .i18n import set_locale, _


class LanguageMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, templates: Jinja2Templates):
        super().__init__(app)
        self.templates = templates

    async def dispatch(self, request: Request, call_next):
        if 'language' not in request.session: request.session['language'] = 'tr'

        lang = request.session.get('language') or request.headers.get("Accept-Language", "en")
        await set_locale(request, lang)

        self.templates.env.globals['_'] = _
        self.templates.env.globals['lang'] = lang

        response = await call_next(request)
        return response
