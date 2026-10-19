"""Explicitly configured, cached provider adapters. Never used by homepage rendering."""
import hashlib,html,json,math
from urllib.parse import urlencode,urlsplit
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from .network import fetch_json

def cached(key,ttl,fn):
    val=cache.get(key)
    if val is not None:return val
    if not cache.add(key+':lock',True,15):raise ValueError('Provider request in progress. Please retry shortly.')
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

def languages():
    provider=settings.TRANSLATION_PROVIDER
    if provider=='google':
        if not settings.TRANSLATION_API_KEY:raise ValueError('Google Cloud Translation requires a server-side API key and billing configuration.')
        data=fetch_json('https://translation.googleapis.com/language/translate/v2/languages?'+urlencode({'key':settings.TRANSLATION_API_KEY,'target':'en'}))
        return [{'code':x['language'],'name':x.get('name',x['language'])} for x in data['data']['languages']]
    if provider=='libre':
        data=fetch_json(settings.LIBRETRANSLATE_URL+'/languages')
        # LibreTranslate explicitly reports supported English target pairs.
        english=next((x for x in data if x['code']=='en'),None)
        targets=english.get('targets',[]) if english else []
        return [{'code':x['code'],'name':x['name']} for x in data if x['code']=='en' or x['code'] in targets]
    raise ValueError('Translation is not configured. Original English remains available. Configure Google Cloud Translation or an approved LibreTranslate instance.')
def supported_languages():return cached('translation-languages:'+settings.TRANSLATION_PROVIDER,3600,languages)
def translate_texts(texts,target):
    if target not in {x['code'] for x in supported_languages()}:raise ValueError('Language is not supported by the configured provider.')
    if target=='en':return texts
    token=hashlib.sha256(json.dumps([settings.TRANSLATION_PROVIDER,target,texts],ensure_ascii=False).encode()).hexdigest()
    def load():
        if settings.TRANSLATION_PROVIDER=='google':
            data=fetch_json('https://translation.googleapis.com/language/translate/v2?'+urlencode({'key':settings.TRANSLATION_API_KEY}),{'q':texts,'source':'en','target':target,'format':'text'})
            result=[html.unescape(x['translatedText']) for x in data['data']['translations']]
        elif settings.TRANSLATION_PROVIDER=='libre':
            data=fetch_json(settings.LIBRETRANSLATE_URL+'/translate',{'q':texts,'source':'en','target':target,'format':'text','api_key':settings.TRANSLATION_API_KEY})
            result=data['translatedText'];result=[result] if isinstance(result,str) else result
        else:raise ValueError('Translation unavailable')
        if len(result)!=len(texts) or any(not isinstance(x,str) for x in result):raise ValueError('Invalid translation response')
        return result
    return cached('translated:'+token,86400,load)
