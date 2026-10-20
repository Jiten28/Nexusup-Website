import json
from urllib.parse import urlsplit
from django.http import JsonResponse
from django.views.decorators.http import require_GET,require_POST
from django.core.cache import cache
from django.urls import resolve,Resolver404
from . import services
from .models import Article,Category

def unavailable(exc):
    # Only deliberate validation/status text is returned, never raw HTTP/provider exceptions or keys.
    message=str(exc) if type(exc) is ValueError else 'Provider unavailable or rate limited. Please try again later.'
    return JsonResponse({'error':message[:250]},status=503)
@require_GET
def currency(request):
    try:return JsonResponse(services.currency(request.GET.get('base','INR').upper(),request.GET.get('quote','USD').upper()))
    except Exception as exc:return unavailable(exc)
@require_GET
def cities(request):
    try:return JsonResponse({'results':services.cities(request.GET.get('name','').strip())})
    except Exception as exc:return unavailable(exc)
@require_GET
def weather(request):
    try:return JsonResponse(services.weather(request.GET.get('lat',''),request.GET.get('lon','')))
    except Exception as exc:return unavailable(exc)
@require_GET
def languages(request):
    try:return JsonResponse({'languages':services.supported_languages(),'provider':__import__('django').conf.settings.TRANSLATION_PROVIDER})
    except Exception as exc:
        r=unavailable(exc);return r

def translation_payload(path):
    # Derive every translated string on the server: not an arbitrary paid translation proxy.
    parsed=urlsplit(path)
    if parsed.netloc or parsed.scheme:raise ValueError('Only local public page paths accepted')
    try:match=resolve(parsed.path)
    except Resolver404:raise ValueError('Unknown public page')
    if match.url_name not in ['home','stories','search','category','article','about','privacy','terms','contact']:raise ValueError('Page cannot be translated')
    payload={'ui:home':'Home','ui:blogs':'All stories','ui:latest':'Latest news','ui:explore':'Explore every perspective','ui:read':'Read story','ui:sample':'Sample story','ui:all':'All'}
    for c in Category.objects.all():payload[f'category:{c.pk}']=c.name
    posts=Article.objects.published().select_related('category','author','source')
    if match.url_name=='article':posts=posts.filter(slug=match.kwargs['slug'])
    elif match.url_name=='category':posts=posts.filter(category__slug=match.kwargs['slug'])
    for post in posts[:24]:
        for field in ['title','excerpt']:payload[f'article:{post.pk}:{field}']=getattr(post,field)
        if match.url_name=='article':
            for i,para in enumerate(post.paragraphs):payload[f'article:{post.pk}:p{i}']=para
    return payload
@require_POST
def translate(request):
    if len(request.body)>2048:return JsonResponse({'error':'Request too large'},status=400)
    if not request.session.session_key:request.session.create()
    if not cache.add('translate-limit:'+request.session.session_key,True,10):return JsonResponse({'error':'Please wait before translating again.'},status=429)
    try:
        data=json.loads(request.body);payload=translation_payload(data.get('path','/'))
        # Fixed server-side corpus, bounded request volume. Add shared production quotas before public use.
        keys=list(payload);texts=list(payload.values())
        if sum(map(len,texts))>45000:raise ValueError('Page exceeds translation size limit')
        values=services.translate_texts(texts,data.get('language','en'))
        return JsonResponse({'language':data.get('language'),'texts':dict(zip(keys,values)),'notice':'Machine translation. Original English remains available.'})
    except Exception as exc:return unavailable(exc)
