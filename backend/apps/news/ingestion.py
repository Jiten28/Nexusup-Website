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
from django.utils.html import strip_tags, unescape
from html.parser import HTMLParser
from django.contrib.auth import get_user_model
from django.db import transaction,IntegrityError
from django.db.models import Q
from urllib.error import HTTPError, URLError
from .models import Article,Category,FetchRun,NewsSource
from .network import fetch_bytes
from .images import best_candidate, approved_remote_image

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
    normalized = urlunsplit(('https',host,p.path or '/',urlencode(sorted(query)),''))
    if len(normalized) > 1000:
        raise ValueError('Story URL exceeds the supported length')
    return normalized

class _FeedImageParser(HTMLParser):
    """Collect image candidates only from publisher-supplied feed HTML, never arbitrary pages."""
    def __init__(self):
        super().__init__(convert_charrefs=True); self.urls=[]
    def handle_starttag(self, tag, attrs):
        if tag.lower() != 'img': return
        attrs=dict(attrs)
        value=attrs.get('src') or attrs.get('data-src') or ''
        if value: self.urls.append(value.strip())

def _feed_text(value, limit=None):
    if isinstance(value, list):
        value='\n\n'.join(str(x.get('value','')) for x in value if isinstance(x,dict))
    raw=str(value or '')
    raw=re.sub(r'(?i)<\s*br\s*/?\s*>', '\n', raw)
    raw=re.sub(r'(?i)</\s*(?:p|div|li|h[1-6]|blockquote|article|section)\s*>', '\n\n', raw)
    text=unescape(strip_tags(raw))
    text=re.sub(r'\r\n?', '\n', text)
    text=re.sub(r'[ \t]+', ' ', text)
    text=re.sub(r'\n[ \t]+', '\n', text)
    text=re.sub(r'\n{3,}', '\n\n', text).strip()
    return text[:limit] if limit else text

class RSSAdapter:
    def parse(self,body):
        self.stats = {"fetched": 0, "parsed": 0, "rejected": 0}
        root = fromstring(body) # rejects malformed XML, entities and DTD entity expansion
        if root.tag.rsplit('}',1)[-1].lower() not in ('rss','feed','rdf'):
            raise NewsAPIError('Endpoint did not return an RSS or Atom document; review the feed URL.')
        parsed=feedparser.parse(body)
        if parsed.bozo and not parsed.entries: raise ValueError('Malformed or empty feed')
        rows=[]
        self.stats["fetched"] = min(len(parsed.entries), 100)
        for e in parsed.entries[:100]:
            title=_feed_text(e.get('title',''),220)
            link=e.get('link','')
            if not title or not link:continue
            try:url=normalize_url(link)
            except (ValueError,UnicodeError):continue
            stamp=None
            parts=e.get('published_parsed') or e.get('updated_parsed')
            if parts:
                try:stamp=datetime.fromtimestamp(calendar.timegm(parts),tz=dtzone.utc)
                except (ValueError,OverflowError):pass
            # RSS extensions and Atom enclosures vary. Prefer explicit image media, then
            # image enclosures, then an image explicitly embedded in feed-provided HTML.
            candidates=[]
            for key in ('media_content','media_thumbnail','enclosures'):
                for item in e.get(key,[]) or []:
                    candidate=item.get('url') or item.get('href','')
                    mime=(item.get('type') or '').lower()
                    if candidate and (mime.startswith('image/') or key in ('media_content','media_thumbnail')):
                        candidates.append((candidate,item.get('width')))
            feed_html='\n'.join(str(x.get('value','')) for x in (e.get('content') or []) if isinstance(x,dict))
            if not feed_html: feed_html=str(e.get('summary','') or '')
            image_parser=_FeedImageParser()
            try:image_parser.feed(feed_html)
            except Exception:pass
            candidates.extend((u,None) for u in image_parser.urls)
            # Widest declared https image; ties keep feed order. URLs are never rewritten.
            image=best_candidate(candidates)
            excerpt=_feed_text(e.get('summary',''),360)
            content=_feed_text(e.get('content') or '')
            # Avoid treating the short summary repeated in content:encoded as a full article.
            if content and len(content) < len(excerpt): content=''
            rows.append({'title':title,'url':url,'excerpt':excerpt,
                         'content':content[:50000], 'published':stamp,'guid':str(e.get('id',''))[:255],
                         'tags':[x.get('term','').lower() for x in e.get('tags',[])], 'image':image,
                         'publisher':_feed_text(e.get('author',''),120)})
        self.stats["parsed"] = len(rows)
        self.stats["rejected"] = self.stats["fetched"] - len(rows)
        return rows
class NewsAPIAdapter:
    """Authorized metadata API. Configure provider rights before enabling a source."""
    def fetch(self, source):
        from .network import fetch_json
        from urllib.parse import urlencode
        from urllib.error import HTTPError, URLError
        query = urlsplit(source.feed_url)
        if query.scheme != 'https' or query.hostname != 'newsapi.org' or query.username or query.password or query.port not in (None,443) or query.fragment or query.path not in ('/v2/top-headlines','/v2/everything'):
            raise ValueError('NewsAPI requires its official HTTPS endpoint')
        if not settings.NEWS_API_KEY:
            raise NewsAPIError('NewsAPI key is not configured; set NEWS_API_KEY in backend/.env or the host environment.')
        args = dict(parse_qsl(query.query))
        if any(k.lower() == 'apikey' for k in args):
            raise NewsAPIError('Remove API credentials from the source URL; use NEWS_API_KEY only.')
        required = ('q','qInTitle','sources','domains') if query.path.endswith('everything') else ('q','sources','country','category')
        if not any(args.get(k, '').strip() for k in required):
            raise NewsAPIError('NewsAPI source URL needs a search term, source, domain, country or category selector appropriate to its endpoint.')
        self.stats = {'fetched':0,'parsed':0,'rejected':0}
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
            if isinstance(data,dict) and data.get('status') == 'error':
                code = data.get('code')
                if code in ('apiKeyInvalid','apiKeyDisabled','apiKeyMissing'):
                    raise NewsAPIError('NewsAPI rejected the configured credentials.')
                if code in ('rateLimited','apiKeyExhausted'):
                    raise NewsAPIError('NewsAPI rate limit reached; wait for the provider quota window.')
                raise NewsAPIError('NewsAPI returned an unexpected response shape or rejected the endpoint/query; review the configured query and plan.')
            if not isinstance(data,dict) or data.get('status') != 'ok' or not isinstance(data.get('articles'),list) or len(data['articles']) > 100:
                raise NewsAPIError('NewsAPI returned an unexpected response shape.')
            self.stats['fetched'] += len(data['articles'])
            for e in data['articles']:
                if not isinstance(e,dict): continue
                try: url=normalize_url(e.get('url',''))
                except (ValueError,UnicodeError,AttributeError): continue
                if not isinstance(e.get('title'),str) or (e.get('description') is not None and not isinstance(e['description'],str)):
                    continue
                title=strip_tags(e.get('title') or '').strip()[:220]
                if not title or title=='[Removed]': continue
                stamp=None
                try: stamp=datetime.fromisoformat((e.get('publishedAt') or '').replace('Z','+00:00'))
                except (ValueError,TypeError,AttributeError): pass
                if stamp and stamp.tzinfo is None: stamp=stamp.replace(tzinfo=dtzone.utc)
                source_data=e.get('source') if isinstance(e.get('source'),dict) else {}
                rows.append(dict(title=title,url=url,excerpt=_feed_text(e.get('description') or '',360),content='',published=stamp,guid='',tags=[],image=e.get('urlToImage') or '',publisher=strip_tags(source_data.get('name') if isinstance(source_data.get('name'),str) else '')[:120]))
            total=data.get('totalResults')
            if len(data['articles']) < 100 or not isinstance(total,int) or self.stats['fetched'] >= total:
                break
        self.stats['parsed'] = len(rows)
        self.stats['rejected'] = self.stats['fetched'] - len(rows)
        return rows
ADAPTERS={'rss':RSSAdapter,'newsapi':NewsAPIAdapter}
def register_adapter(name,adapter): ADAPTERS[name]=adapter # application-controlled API adapters can be registered here

def safe_fetch_error(exc):
    """Only deliberate application diagnostics; never provider bodies/URLs/tracebacks."""
    if isinstance(exc, NewsAPIError):
        return str(exc)[:300]
    if isinstance(exc, HTTPError):
        if exc.code in (401, 403):
            return f'HTTP {exc.code}: feed access denied; review endpoint permissions and publisher terms.'
        if exc.code == 429:
            return 'HTTP 429: publisher rate limit; wait before retrying.'
        return f'HTTP {exc.code}: provider request failed; check endpoint availability.'
    if isinstance(exc, (TimeoutError, URLError, OSError)):
        return 'Provider timed out or is unavailable; check connectivity and retry after the source interval.'
    return type(exc).__name__ + ': fetch/parse failed; check source configuration and provider format; stored content retained.'


def ingest(source, dry_run=False):
    """One explicit source attempt. Dry runs never write even blocked/failed records.

    Non-dry attempts record blocked/deferred outcomes too. No in-process scheduler.
    A database outage cannot itself be recorded in that unavailable database.
    """
    # Internal caller metadata avoids attributing a concurrent worker's run to this invocation.
    source._last_fetch_run_id = None
    def blocked(message):
        if not dry_run:
            source._last_fetch_run_id = FetchRun.objects.create(source=source, state='blocked', success=False, error=message).pk
        raise ValueError(message)

    if not settings.NEWS_FETCH_ENABLED:
        blocked('News fetching is disabled. Review rights and set NEWS_FETCH_ENABLED=1 explicitly before fetching.')
    if not source.enabled or not source.rights_confirmed:
        blocked('Source must be enabled and rights confirmed; no permission flags were changed.')
    # Re-read approval/trust: never publish using stale in-memory permissions.
    source.refresh_from_db()
    if not source.enabled or not source.rights_confirmed:
        blocked('Source must be enabled and rights confirmed; no permission flags were changed.')
    now = timezone.now()
    def deferred():
        if not dry_run:
            source._last_fetch_run_id = FetchRun.objects.create(source=source, state='deferred', error='Source is not due or another worker claimed it.').pk
        return {'imported':0,'skipped':0,'deferred':True}
    if source.next_fetch_at and source.next_fetch_at > now:
        return deferred()
    if not dry_run:
        claimed = NewsSource.objects.filter(pk=source.pk, enabled=True, rights_confirmed=True).filter(
            Q(next_fetch_at__isnull=True) | Q(next_fetch_at__lte=now)
        ).update(last_attempt_at=now, next_fetch_at=now + timedelta(minutes=max(5, source.interval_minutes)))
        if not claimed:
            return deferred()
    counters = dict(fetched=0, parsed=0, rejected=0, duplicates=0, published=0)
    imported = skipped = 0
    instance = None
    run = None
    try:
        if not dry_run:
            run = FetchRun.objects.create(source=source, state='running')
            source._last_fetch_run_id = run.pk
        adapter = ADAPTERS.get(source.adapter)
        if not adapter:
            raise NewsAPIError('Unknown source adapter; use rss for RSS/Atom or newsapi for official NewsAPI endpoints.')
        instance = adapter()
        rows = instance.fetch(source) if hasattr(instance, 'fetch') else instance.parse(fetch_bytes(source.feed_url))
        counters.update(getattr(instance, 'stats', dict(fetched=len(rows), parsed=len(rows), rejected=0)))
        prepared, seen_urls, seen_titles, seen_guids = [], set(), set(), set()
        for row in rows:
            digest = hashlib.sha256(row['url'].encode()).hexdigest()
            title_hash = hashlib.sha256(re.sub(r'\W+', ' ', unicodedata.normalize('NFKC', row['title']).casefold()).strip().encode()).hexdigest()
            duplicate = digest in seen_urls or title_hash in seen_titles or (row['guid'] and row['guid'] in seen_guids)
            duplicate = duplicate or Article.objects.filter(Q(source_url_hash=digest) | Q(normalized_title_hash=title_hash)).exists()
            if row['guid']:
                duplicate = duplicate or Article.objects.filter(source=source, source_guid=row['guid']).exists()
            if duplicate:
                skipped += 1
                counters['duplicates'] += 1
                continue
            seen_urls.add(digest); seen_titles.add(title_hash)
            if row['guid']: seen_guids.add(row['guid'])
            prepared.append((row, digest, title_hash))
        if dry_run:
            return {'eligible':len(rows),'would_import':len(prepared),'imported':0,'skipped':skipped,'dry_run':True}
        with transaction.atomic():
            # Lock the source before creating articles, rechecking permissions after network I/O.
            current = NewsSource.objects.select_for_update().get(pk=source.pk)
            if not current.enabled or not current.rights_confirmed:
                raise NewsAPIError('Source approval was revoked during fetch; no articles were saved.')
            author = None
            if prepared:
                author, created = get_user_model().objects.get_or_create(username='news-feed-editor', defaults={
                    'first_name':'NexusUp','last_name':'Source Desk','is_active':False})
                if created:
                    author.set_unusable_password(); author.save()
            for row, digest, title_hash in prepared:
                cat = current.default_category
                for tag in row['tags']:
                    slug = current.category_map.get(tag)
                    if slug:
                        cat = Category.objects.filter(slug=slug).first() or cat
                        break
                image = approved_remote_image(row['image'], current.allow_images, current.image_hosts)
                publish = bool(current.trusted and current.auto_publish and row['published'] and row['published'] <= now)
                try:
                    with transaction.atomic():
                        Article.objects.create(title=row['title'], slug=(slugify(row['title'])[:170] or 'news')+'-'+digest[:16],
                            category=cat, author=author, excerpt=row['excerpt'],
                            body=(row.get('content') or '').strip() or 'Read the original publisher for the complete report. This entry contains feed metadata only.',
                            normalized_title_hash=title_hash, publisher_name=row.get('publisher',''), source=current,
                            canonical_source_url=row['url'], source_url_hash=digest, source_guid=row['guid'],
                            source_published_at=row['published'], published_at=row['published'] or now, imported_at=now,
                            remote_image_url=image, image_alt=row['title'] if image else '', image_credit=current.name if image else '',
                            status='published' if publish else 'draft', featured=False, is_sample=False)
                    imported += 1
                    counters['published'] += int(publish)
                except IntegrityError:
                    # Only actual concurrent duplicates are skips; schema/other failures roll back.
                    dup = Article.objects.filter(Q(source_url_hash=digest) | Q(normalized_title_hash=title_hash)).exists()
                    if not dup:
                        raise
                    skipped += 1; counters['duplicates'] += 1
            current.last_success_at=now; current.last_error=''
            current.save(update_fields=['last_success_at','last_error'])
            FetchRun.objects.filter(pk=run.pk).update(state='success', success=True, imported=imported, skipped=skipped, **counters)
        # Preserve the established service result contract; detailed counts are on FetchRun.
        return {'imported':imported,'skipped':skipped}
    except Exception as exc:
        error = safe_fetch_error(exc)
        logger.warning('News ingestion failed for source_id=%s: %s', source.pk, error)
        if not dry_run:
            counters.update(getattr(instance, 'stats', {}))
            counters['published'] = 0  # Outer atomic block rolled back all article writes.
            NewsSource.objects.filter(pk=source.pk).update(last_error=error)
            if run is not None:
                FetchRun.objects.filter(pk=run.pk).update(state='failed', success=False, error=error, imported=0, skipped=skipped, **counters)
            else:
                source._last_fetch_run_id = FetchRun.objects.create(source=source, state='failed', success=False, error=error, imported=0, skipped=skipped, **counters).pk
        raise ValueError(error) from None
