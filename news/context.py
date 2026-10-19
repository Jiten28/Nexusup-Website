from django.conf import settings
from .models import Category
def site(request):
    return {'categories':Category.objects.all(), 'media_url':settings.MEDIA_URL, 'site_url':settings.SITE_URL,
            'canonical_url': settings.SITE_URL + request.path, 'demo_mode':True}
