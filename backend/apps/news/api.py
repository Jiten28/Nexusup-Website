import json
from urllib.parse import urlsplit
from django.http import JsonResponse
from django.views.decorators.http import require_GET,require_POST
from django.core.cache import cache
from django.urls import resolve,Resolver404
from . import services
from .models import Article,Category
from .ui_strings import UI_STRINGS

def unavailable(exc):
    # Only deliberate validation/status text is returned, never raw HTTP/provider exceptions or keys.
    message=str(exc) if type(exc) is ValueError or isinstance(exc, services.TranslationError) else 'Provider unavailable or rate limited. Please try again later.'
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

def translation_payload(path,ids=None):
    # Derive every translated string on the server: not an arbitrary paid translation proxy.
    if not isinstance(path,str) or len(path)>1024:
        raise ValueError('Invalid public page path')
    parsed=urlsplit(path)
    if parsed.netloc or parsed.scheme:raise ValueError('Only local public page paths accepted')
    try:match=resolve(parsed.path)
    except Resolver404:raise ValueError('Unknown public page')
    if match.url_name not in ['home','stories','search','category','article','about','privacy','terms','contact']:raise ValueError('Page cannot be translated')
    payload=dict(UI_STRINGS)
    for c in Category.objects.all():payload[f'category:{c.pk}']=c.name
    from .rest import public
    posts=public(include_samples=match.url_name=='article')
    if match.url_name=='article':posts=posts.filter(slug=match.kwargs['slug'])
    elif match.url_name=='category':posts=posts.filter(category__slug=match.kwargs['slug'])
    chosen=list(posts[:24])
    # Stories added by "Load more" are named by id; only PUBLIC stories are ever looked up, so this is not a free-text proxy.
    extra=[int(i) for i in (ids or []) if isinstance(i,int) and not isinstance(i,bool)][:24]
    if extra:chosen+=list(public().filter(pk__in=extra).exclude(pk__in=[p.pk for p in chosen])[:max(0,48-len(chosen))])
    for post in chosen:
        for field in ['title','excerpt']:payload[f'article:{post.pk}:{field}']=getattr(post,field)
        if match.url_name=='article':
            for i,para in enumerate(post.paragraphs):payload[f'article:{post.pk}:p{i}']=para
            if getattr(post,'ai_summary',''):payload[f'article:{post.pk}:summary']=post.ai_summary
    return payload
@require_POST
def translate(request):
    if len(request.body)>4096:return JsonResponse({'error':'Request too large'},status=400)
    # Rate-limit without creating database sessions merely for translation.
    import hashlib
    client = request.META.get('REMOTE_ADDR','unknown')
    limit_key = hashlib.sha256(client.encode()).hexdigest()
    if not cache.add('translate-limit:'+limit_key,True,10):return JsonResponse({'error':'Please wait before translating again.'},status=429)
    try:
        data=json.loads(request.body)
        if not isinstance(data,dict) or data.get('source','en') != 'en' or not isinstance(data.get('language','en'),str):
            raise ValueError('Expected a JSON object with source English and a target language code.')
        ids=data.get('ids',[])
        if not isinstance(ids,list):raise ValueError('ids must be a list of story numbers.')
        payload=translation_payload(data.get('path','/'),ids)
        # Fixed server-side corpus, bounded request volume. Add shared production quotas before public use.
        keys=list(payload);texts=list(payload.values())
        if sum(map(len,texts))>45000:raise ValueError('Page exceeds translation size limit')
        values=services.translate_texts(texts,data.get('language','en'))
        return JsonResponse({'source':'en','language':data.get('language','en'),'texts':dict(zip(keys,values)),'notice':'Machine translation. Original English remains available.'})
    except Exception as exc:return unavailable(exc)
