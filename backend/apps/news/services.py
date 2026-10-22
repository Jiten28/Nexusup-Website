"""Explicitly configured, cached provider adapters. Never used by homepage rendering."""
import hashlib,html,json,math
from urllib.parse import urlencode,urlsplit
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from .network import fetch_json

def cached(key,ttl,fn,lock_ttl=15):
    val=cache.get(key)
    if val is not None:return val
    if not cache.add(key+':lock',True,lock_ttl):raise ValueError('Provider request in progress. Please retry shortly.')
    try:
        result=fn();cache.set(key,result,ttl);return result
    finally:cache.delete(key+':lock')
def currency(base,quote):
    if not settings.UTILITIES_NETWORK_ENABLED:raise ValueError('Currency provider is disabled. Enable UTILITIES_NETWORK_ENABLED after provider review.')
    allowed={'INR','USD','EUR','GBP','JPY','AUD','CAD','AED'}
    if base not in allowed or quote not in allowed:raise ValueError('Unsupported currency')
    if base==quote:return {'rate':1,'date':timezone.now().date().isoformat(),'source':'Identity conversion — no market rate required'}
    def load():
        data=fetch_json(f'https://api.frankfurter.dev/v2/rate/{base.lower()}/{quote.lower()}')
        rate=float(data['rate'])
        if not math.isfinite(rate) or rate<=0:raise ValueError('Invalid provider rate')
        return {'rate':rate,'date':data['date'],'source':'Frankfurter — daily blended reference rate; not a live quote'}
    return cached(f'fx:{base}:{quote}',3600,load)
def cities(name):
    if not settings.UTILITIES_NETWORK_ENABLED:raise ValueError('Weather/geocoding provider disabled. Manual coordinates are still available.')
    if not 2<=len(name)<=80:raise ValueError('Enter a city name, 2–80 characters.')
    data=cached('city:'+hashlib.sha256(name.lower().encode()).hexdigest(),86400,lambda:fetch_json('https://geocoding-api.open-meteo.com/v1/search?'+urlencode({'name':name,'count':5,'language':'en','format':'json'})))
    return [{'name':', '.join(str(r[k]) for k in ['name','admin1','country'] if r.get(k)),'latitude':r['latitude'],'longitude':r['longitude']} for r in data.get('results',[])]
def weather(lat,lon):
    if not settings.UTILITIES_NETWORK_ENABLED:raise ValueError('Weather provider disabled. Enable UTILITIES_NETWORK_ENABLED for evaluation, or configure a licensed commercial plan.')
    lat=float(lat);lon=float(lon)
    if not math.isfinite(lat) or not math.isfinite(lon) or not -90<=lat<=90 or not -180<=lon<=180:raise ValueError('Invalid coordinates')
    def load():
        host='customer-api.open-meteo.com' if settings.OPEN_METEO_API_KEY else 'api.open-meteo.com'
        params={'latitude':round(lat,2),'longitude':round(lon,2),'current':'temperature_2m,weather_code,wind_speed_10m','timezone':'UTC'}
        if settings.OPEN_METEO_API_KEY:params['apikey']=settings.OPEN_METEO_API_KEY
        data=fetch_json('https://'+host+'/v1/forecast?'+urlencode(params))
        current=data['current']
        return {'temperature':current['temperature_2m'],'weather_code':current['weather_code'],'wind':current['wind_speed_10m'],'time':current['time']+'Z','source':'Open-Meteo (CC BY 4.0)','attribution_url':'https://open-meteo.com/','units':'°C / km/h'}
    return cached(f'weather:{lat:.2f}:{lon:.2f}',600,load)

class TranslationError(ValueError):
    """Safe, deliberate operator/user message; provider bodies are never forwarded."""


def translation_identity():
    # Include instance and key fingerprint so switching endpoints/accounts cannot reuse stale capabilities.
    return hashlib.sha256(json.dumps([settings.TRANSLATION_PROVIDER, settings.LIBRETRANSLATE_URL,
                                      settings.TRANSLATION_API_KEY]).encode()).hexdigest()


def translation_json(path, data=None):
    from .translation_network import fetch_local_json
    try:
        base = settings.LIBRETRANSLATE_URL
        parsed = urlsplit(base)
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise TranslationError('Translation endpoint must not contain embedded credentials, query parameters or fragments.')
        if parsed.scheme == 'http':
            return fetch_local_json(base, path, data, timeout=settings.TRANSLATION_TIMEOUT)
        if parsed.scheme != 'https':
            raise TranslationError('Use loopback HTTP or a public HTTPS translation endpoint.')
        # Public HTTPS uses the existing SSRF-protected client. No weakening of feed policy.
        return fetch_json(base + path, data) if data is not None else fetch_json(base + path)
    except TranslationError:
        raise
    except Exception:
        raise TranslationError('Translation provider unavailable or returned an invalid response. Check the configured endpoint, installed models and timeout; original English is retained.') from None


def languages():
    provider = settings.TRANSLATION_PROVIDER
    if provider == 'google':
        if not settings.TRANSLATION_API_KEY:
            raise TranslationError('Google Cloud Translation requires a server-side API key and billing configuration; no paid fallback is automatic.')
        data = fetch_json('https://translation.googleapis.com/language/translate/v2/languages?' + urlencode({'key':settings.TRANSLATION_API_KEY,'target':'en'}))
        return [{'code':x['language'],'name':x.get('name',x['language'])} for x in data['data']['languages']]
    if provider == 'libre':
        data = translation_json('/languages')
        if not isinstance(data, list) or len(data) > 300 or any(
            not isinstance(x,dict) or not isinstance(x.get('code'),str) or not isinstance(x.get('name'),str)
            or not 1 <= len(x['code']) <= 20 or not 1 <= len(x['name']) <= 100 for x in data
        ):
            raise TranslationError('Invalid translation language response; check the installed models.')
        english = next((x for x in data if x['code'] == 'en'), None)
        if not english or not isinstance(english.get('targets'), list) or any(not isinstance(t,str) for t in english['targets']):
            raise TranslationError('The translator does not report supported English model pairs.')
        targets = set(english['targets']) | {'en'}
        return [{'code':x['code'],'name':x['name']} for x in data if x['code'] in targets]
    raise TranslationError('Translation is not configured. Original English remains available; configure an approved self-hosted LibreTranslate instance.')


def supported_languages():
    return cached('translation-languages:' + translation_identity(), 3600, languages, lock_ttl=max(15, settings.TRANSLATION_TIMEOUT + 5))


def translate_texts(texts, target):
    if not isinstance(texts,list) or len(texts) > 256 or any(not isinstance(t,str) or len(t)>5000 for t in texts) or sum(map(len,texts)) > 45000:
        raise TranslationError('Translation input exceeds the supported text limits (256 strings, 5000 characters per string, 45000 total).')
    if not isinstance(target,str) or len(target)>20:
        raise TranslationError('Invalid target language.')
    if target == 'en':
        return texts[:]  # English passthrough never contacts a provider or changes originals.
    if target not in {x['code'] for x in supported_languages()}:
        raise TranslationError('Language is not supported by the configured provider.')
    token = hashlib.sha256(json.dumps([translation_identity(),'en',target,texts], ensure_ascii=False).encode()).hexdigest()
    def load():
        if settings.TRANSLATION_PROVIDER == 'google':
            data = fetch_json('https://translation.googleapis.com/language/translate/v2?' + urlencode({'key':settings.TRANSLATION_API_KEY}), {'q':texts,'source':'en','target':target,'format':'text'})
            result = [html.unescape(x['translatedText']) for x in data['data']['translations']]
        elif settings.TRANSLATION_PROVIDER == 'libre':
            result = []
            # Bound batch sizes, retaining original ordering. No article or provider metadata is sent.
            for offset in range(0,len(texts),16):
                batch = texts[offset:offset+16]
                payload = {'q':batch,'source':'en','target':target,'format':'text'}
                if settings.TRANSLATION_API_KEY:
                    payload['api_key'] = settings.TRANSLATION_API_KEY
                data = translation_json('/translate', payload)
                translated = data.get('translatedText') if isinstance(data,dict) else None
                if isinstance(translated,str) and len(batch)==1:
                    translated = [translated]
                if not isinstance(translated,list) or len(translated)!=len(batch) or any(not isinstance(x,str) for x in translated):
                    raise TranslationError('Invalid translation response; original English is retained.')
                if any(len(x)>20000 for x in translated):
                    raise TranslationError('Translation response exceeds the supported text limits.')
                result.extend(translated)
        else:
            raise TranslationError('Translation unavailable; no fallback service was contacted.')
        if len(result)!=len(texts) or any(not isinstance(x,str) for x in result):
            raise TranslationError('Invalid translation response')
        if sum(map(len,result)) > 180000:
            raise TranslationError('Translation response exceeds the total output limit.')
        return result
    return cached('translated:' + token, 86400, load, lock_ttl=settings.TRANSLATION_TIMEOUT * 16 + 15)
