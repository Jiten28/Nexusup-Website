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
    if not (settings.UTILITIES_NETWORK_ENABLED or settings.OPENWEATHER_API_KEY):raise ValueError('Weather/geocoding provider disabled. Manual coordinates are still available.')
    if not 2<=len(name)<=80:raise ValueError('Enter a city name, 2–80 characters.')
    data=cached('city:'+hashlib.sha256(name.lower().encode()).hexdigest(),86400,lambda:fetch_json('https://geocoding-api.open-meteo.com/v1/search?'+urlencode({'name':name,'count':5,'language':'en','format':'json'})))
    return [{'name':', '.join(str(r[k]) for k in ['name','admin1','country'] if r.get(k)),'latitude':r['latitude'],'longitude':r['longitude']} for r in data.get('results',[])]
def owm_to_wmo(i):
    # Map OpenWeatherMap condition ids onto the WMO-style codes the website widget already understands.
    i=int(i)
    if i==800:return 0
    if 801<=i<=804:return 3
    if 200<=i<300:return 95
    if 300<=i<600:return 61
    if 600<=i<700:return 71
    if 700<=i<800:return 45
    return 3
def weather(lat,lon):
    if not (settings.UTILITIES_NETWORK_ENABLED or (settings.WEATHER_PROVIDER=='openweathermap' and settings.OPENWEATHER_API_KEY)):raise ValueError('Weather provider disabled. Enable UTILITIES_NETWORK_ENABLED for evaluation, or configure a licensed commercial plan.')
    lat=float(lat);lon=float(lon)
    if not math.isfinite(lat) or not math.isfinite(lon) or not -90<=lat<=90 or not -180<=lon<=180:raise ValueError('Invalid coordinates')
    if settings.WEATHER_PROVIDER=='openweathermap':
        if not settings.OPENWEATHER_API_KEY:raise ValueError('OpenWeatherMap is selected but OPENWEATHER_API_KEY is not set in backend/.env.')
        def load_owm():
            # The key travels only server-to-OpenWeatherMap; errors are reduced to a safe message by the API layer.
            data=fetch_json('https://api.openweathermap.org/data/2.5/weather?'+urlencode({'lat':round(lat,2),'lon':round(lon,2),'units':'metric','appid':settings.OPENWEATHER_API_KEY}))
            w=(data.get('weather') or [{}])[0];main=data['main']
            return {'temperature':round(main['temp'],1),'weather_code':owm_to_wmo(w.get('id',0)),'condition':str(w.get('description','')).capitalize()[:60],'wind':round(float(data.get('wind',{}).get('speed',0))*3.6,1),'time':timezone.now().strftime('%Y-%m-%dT%H:%M:%S')+'Z','source':'OpenWeatherMap','attribution_url':'https://openweathermap.org/','units':'°C / km/h'}
        return cached(f'weather:owm:{lat:.2f}:{lon:.2f}',600,load_owm)
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


MYMEMORY_LANGS=[('hi','Hindi'),('bn','Bengali'),('ta','Tamil'),('te','Telugu'),('mr','Marathi'),('gu','Gujarati'),('kn','Kannada'),('ml','Malayalam'),('pa','Punjabi'),('ur','Urdu'),('ar','Arabic'),('es','Spanish'),('fr','French'),('de','German'),('pt','Portuguese'),('ru','Russian'),('ja','Japanese'),('zh-CN','Chinese (Simplified)'),('id','Indonesian'),('tr','Turkish'),('it','Italian')]
def _mymemory_one(text,target):
    q=text.strip()
    if not q:return text
    # MyMemory accepts at most ~500 bytes per request, so long text is cut on sentence ends.
    parts=[];cur=''
    for sent in __import__('re').split(r'(?<=[.!?])\s+',q):
        while len(sent.encode())>450:sent,rest=sent[:150],sent[150:];parts.append((cur+' '+sent).strip() if cur else sent);cur='';sent=rest
        if len((cur+' '+sent).encode())>450:parts.append(cur);cur=sent
        else:cur=(cur+' '+sent).strip()
    if cur:parts.append(cur)
    out=[]
    for part in parts:
        params={'q':part,'langpair':f'en|{target}'}
        if settings.MYMEMORY_EMAIL:params['de']=settings.MYMEMORY_EMAIL
        data=fetch_json('https://api.mymemory.translated.net/get?'+urlencode(params),timeout=settings.TRANSLATION_TIMEOUT)
        text_out=str(data.get('responseData',{}).get('translatedText',''))
        if str(data.get('responseStatus'))!='200' or data.get('quotaFinished') or text_out.upper().startswith('MYMEMORY WARNING') or not text_out:
            raise TranslationError('The free translation allowance for today is used up. Original English is shown; try again tomorrow or ask the site owner to add a MyMemory email or a self-hosted translator.')
        out.append(html.unescape(text_out))
    return ' '.join(out)
def _mymemory_cached(text,target):
    # Each sentence is remembered for a week, so the free daily allowance is only spent on text not seen before.
    key='mm:'+hashlib.sha256((target+'|'+text).encode()).hexdigest()
    hit=cache.get(key)
    if hit is not None:return hit
    out=_mymemory_one(text,target);cache.set(key,out,7*86400);return out
def languages():
    provider = settings.TRANSLATION_PROVIDER
    if provider == 'mymemory':
        return [{'code':c,'name':n} for c,n in MYMEMORY_LANGS]
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
        elif settings.TRANSLATION_PROVIDER == 'mymemory':
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=4) as pool:
                result = list(pool.map(lambda x: _mymemory_cached(x, target), texts))
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
