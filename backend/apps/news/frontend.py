"""Public-page dispatch only; API, admin, feeds and media remain Django-owned."""
from functools import wraps
from urllib.parse import urlsplit
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect


def public_page(legacy_view):
    @wraps(legacy_view)
    def dispatch(request, *args, **kwargs):
        if settings.PUBLIC_FRONTEND_MODE == 'legacy':
            return legacy_view(request, *args, **kwargs)
        target = settings.FRONTEND_URL.rstrip('/')
        current = urlsplit(request.build_absolute_uri('/'))
        origin = urlsplit(target)
        if (current.scheme, current.netloc.lower()) == (origin.scheme, origin.netloc.lower()):
            # Production serves React at the edge (see nginx-container.conf).
            # A direct backend request must not loop or masquerade as the legacy site.
            response = HttpResponse('React frontend is not being served here. Configure the React web server or FRONTEND_URL.', status=503, content_type='text/plain')
        else:
            response = HttpResponseRedirect(target + request.get_full_path())
        response['Cache-Control'] = 'no-store'
        return response
    return dispatch
