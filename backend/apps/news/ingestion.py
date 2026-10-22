"""Scheduled metadata ingestion. Existing manual records and featured choices are never overwritten."""
import hashlib,calendar,re,json,unicodedata,logging
from django.conf import settings
from datetime import datetime,timedelta,timezone as dtzone
from urllib.parse import urlsplit,urlunsplit,parse_qsl,urlencode
from email.utils import parsedate_to_datetime
import feedparser
from defusedxml.ElementTree import fromstring
from django.utils import timezone
from django.utils.text import slugify
from django.utils.html import strip_tags
from django.contrib.auth import get_user_model
from django.db import transaction,IntegrityError
from .models import Article,Category,FetchRun,NewsSource
from .network import fetch_bytes

logger = logging.getLogger(__name__)


class NewsAPIError(ValueError):
    """A deliberately non-sensitive provider diagnostic safe for operators."""

def normalize_url(value):
    p=urlsplit(value.strip())
    if p.scheme not in ('http','https') or not p.hostname or p.username or p.password: raise ValueError('Invalid story URL')
    # URL normalization is not fetching; do not resolve article hosts or scrape articles.
    import ipaddress
    try:
        if not ipaddress.ip_address(p.hostname).is_global: raise ValueError('Private article URL')
    except ValueError as e:
        if str(e)=='Private article URL':raise
    if p.hostname.lower() in ('localhost','localhost.localdomain') or p.port not in (None,80,443):raise ValueError('Private/invalid article URL')
    host=p.hostname.lower().encode('idna').decode()
    query=[(k,v) for k,v in parse_qsl(p.query,keep_blank_values=True) if not k.lower().startswith('utm_') and k.lower() not in ('fbclid','gclid','mc_cid','mc_eid')]
    return urlunsplit(('https',host,p.path or '/',urlencode(sorted(query)),''))

class RSSAdapter:
    def parse(self,body):
        fromstring(body) # rejects malformed XML, entities and DTD entity expansion
        parsed=feedparser.parse(body)
        if parsed.bozo and not parsed.entries: raise ValueError('Malformed or empty feed')
        rows=[]
        for e in parsed.entries[:100]:
            title=strip_tags(e.get('title','')).strip()[:220]
            link=e.get('link','')
            if not title or not link:continue
            try:url=normalize_url(link)
            except (ValueError,UnicodeError):continue
            stamp=None
            parts=e.get('published_parsed') or e.get('updated_parsed')
            if parts:
                try:stamp=datetime.fromtimestamp(calendar.timegm(parts),tz=dtzone.utc)
                except (ValueError,OverflowError):pass
            image=''
            for item in e.get('media_content',[])+e.get('media_thumbnail',[])+e.get('enclosures',[]):
                candidate=item.get('url') or item.get('href','')
                if candidate and (item.get('type','').startswith('image/') or 'media_' in str(e.keys())):
                    image=candidate;break
            rows.append({'title':title,'url':url,'excerpt':strip_tags(e.get('summary','')).strip()[:360],
                         'published':stamp,'guid':str(e.get('id',''))[:255],'tags':[x.get('term','').lower() for x in e.get('tags',[])], 'image':image})
        return rows
class NewsAPIAdapter:
    """Authorized metadata API. Configure provider rights before enabling a source."""
    def fetch(self, source):
        from .network import fetch_json
        from urllib.parse import urlencode
        from urllib.error import HTTPError, URLError
        query = urlsplit(source.feed_url)
        if query.scheme != 'https' or query.hostname != 'newsapi.org' or query.path not in ('/v2/top-headlines','/v2/everything'):
            raise ValueError('NewsAPI requires its official HTTPS endpoint')
        if not settings.NEWS_API_KEY:
            raise NewsAPIError('NewsAPI key is not configured; set NEWS_API_KEY in backend/.env or the host environment.')
        args = dict(parse_qsl(query.query)); args.pop('apiKey',None)
        rows=[]
        for page in range(1,settings.NEWS_API_MAX_PAGES+1):
            page_args={**args,'pageSize':'100','page':str(page)}
            endpoint=urlunsplit(('https','newsapi.org',query.path,urlencode(page_args),''))
            try:
                data=fetch_json(endpoint,headers={'X-Api-Key':settings.NEWS_API_KEY})
            except HTTPError as exc:
                if exc.code in (401,403):
                    raise NewsAPIError('NewsAPI rejected the configured credentials.') from exc
                if exc.code == 429:
                    raise NewsAPIError('NewsAPI rate limit reached; wait for the provider quota window.') from exc
                raise NewsAPIError(f'NewsAPI HTTP failure ({exc.code}).') from exc
            except (TimeoutError,URLError,OSError) as exc:
                raise NewsAPIError('NewsAPI request timed out or the provider is unavailable.') from exc
            except (json.JSONDecodeError,UnicodeDecodeError) as exc:
                raise NewsAPIError('NewsAPI returned invalid JSON.') from exc
            if not isinstance(data,dict) or data.get('status') != 'ok' or not isinstance(data.get('articles'),list):
                raise NewsAPIError('NewsAPI returned an unexpected response shape.')
            for e in data['articles']:
                if not isinstance(e,dict): continue
                try: url=normalize_url(e.get('url',''))
                except (ValueError,UnicodeError,AttributeError): continue
                title=strip_tags(e.get('title') or '').strip()[:220]
                if not title or title=='[Removed]': continue
                stamp=None
                try: stamp=datetime.fromisoformat((e.get('publishedAt') or '').replace('Z','+00:00'))
                except (ValueError,TypeError,AttributeError): pass
                if stamp and stamp.tzinfo is None: stamp=stamp.replace(tzinfo=dtzone.utc)
                source_data=e.get('source') if isinstance(e.get('source'),dict) else {}
                rows.append(dict(title=title,url=url,excerpt=strip_tags(e.get('description') or '')[:360],published=stamp,guid='',tags=[],image=e.get('urlToImage') or '',publisher=strip_tags(source_data.get('name') or '')[:120]))
            total=data.get('totalResults')
            if len(data['articles']) < 100 or not isinstance(total,int) or len(rows) >= total:
                break
        return rows
ADAPTERS={'rss':RSSAdapter,'newsapi':NewsAPIAdapter}
def register_adapter(name,adapter): ADAPTERS[name]=adapter # application-controlled API adapters can be registered here

def ingest(source,dry_run=False):
    if not source.enabled or not source.rights_confirmed:raise ValueError('Source must be enabled and rights confirmed.')
    now=timezone.now()
    if source.next_fetch_at and source.next_fetch_at>now:return {'imported':0,'skipped':0,'deferred':True}
    if not dry_run:
        # Database-backed claim prevents overlapping scheduler jobs for the same source.
        claimed=NewsSource.objects.filter(pk=source.pk).filter(__import__('django').db.models.Q(next_fetch_at__isnull=True)|__import__('django').db.models.Q(next_fetch_at__lte=now)).update(last_attempt_at=now,next_fetch_at=now+timedelta(minutes=max(5,source.interval_minutes)))
        if not claimed:return {'imported':0,'skipped':0,'deferred':True}
    imported=skipped=0
    try:
        adapter=ADAPTERS.get(source.adapter)
        if not adapter:raise ValueError('Unknown source adapter')
        instance=adapter()
        rows=instance.fetch(source) if hasattr(instance,'fetch') else instance.parse(fetch_bytes(source.feed_url))
        prepared=[]
        for row in rows:
            digest=hashlib.sha256(row['url'].encode()).hexdigest()
            title_hash=hashlib.sha256(re.sub(r'\W+',' ',unicodedata.normalize('NFKC',row['title']).casefold()).strip().encode()).hexdigest()
            duplicate=Article.objects.filter(source_url_hash=digest).exists() or Article.objects.filter(normalized_title_hash=title_hash).exists()
            if row['guid']: duplicate=duplicate or Article.objects.filter(source=source,source_guid=row['guid']).exists()
            if duplicate:skipped+=1;continue
            prepared.append((row,digest,title_hash))
        if dry_run:
            return {'eligible':len(rows),'would_import':len(prepared),'imported':0,'skipped':skipped,'dry_run':True}
        with transaction.atomic():
            author,created=get_user_model().objects.get_or_create(username='news-feed-editor',defaults={'first_name':'NexusUp','last_name':'Source Desk','is_active':False})
            if created:author.set_unusable_password();author.save()
            for row,digest,title_hash in prepared:
                cat=source.default_category
                for tag in row['tags']:
                    slug=source.category_map.get(tag)
                    if slug:cat=Category.objects.filter(slug=slug).first() or cat;break
                image=''
                if source.allow_images and row['image']:
                    parsed=urlsplit(row['image'])
                    if parsed.scheme=='https' and parsed.hostname in source.image_hosts:image=row['image'][:1000]
                try:
                    with transaction.atomic():  # Savepoint lets a concurrent duplicate be skipped.
                        Article.objects.create(title=row['title'],slug=(slugify(row['title'])[:170] or 'news')+'-'+digest[:16],
                            category=cat,author=author,excerpt=row['excerpt'],body='Read the original publisher for the complete report. This entry contains feed metadata only.',
                            normalized_title_hash=title_hash,publisher_name=row.get('publisher',''),source=source,canonical_source_url=row['url'],source_url_hash=digest,source_guid=row['guid'],
                            source_published_at=row['published'],published_at=row['published'] or now,imported_at=now,
                            remote_image_url=image,image_alt=row['title'] if image else '',image_credit=source.name if image else '',
                            status='published' if source.trusted and source.auto_publish and row['published'] else 'draft',featured=False,is_sample=False)
                    imported+=1
                except IntegrityError:skipped+=1
            source.last_success_at=now;source.last_error='';source.save(update_fields=['last_success_at','last_error'])
            FetchRun.objects.create(source=source,success=True,imported=imported,skipped=skipped)
        return {'imported':imported,'skipped':skipped}
    except Exception as exc:
        # Never store credentials/URLs or raw provider responses in public/admin errors.
        error=str(exc) if isinstance(exc,NewsAPIError) else type(exc).__name__+': fetch/parse failed; check source availability, format and provider limits.'
        logger.warning('News ingestion failed for source_id=%s: %s',source.pk,error)
        if not dry_run:
            source.last_error=error;source.save(update_fields=['last_error'])
            FetchRun.objects.create(source=source,success=False,error=error,imported=imported,skipped=skipped)
        raise ValueError(error) from exc
