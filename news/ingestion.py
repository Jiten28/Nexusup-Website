"""Scheduled metadata ingestion. Existing manual records and featured choices are never overwritten."""
import hashlib,calendar,re
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
ADAPTERS={'rss':RSSAdapter}
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
        rows=adapter().parse(fetch_bytes(source.feed_url))
        if dry_run:return {'eligible':len(rows),'imported':0,'skipped':0,'dry_run':True}
        author,created=get_user_model().objects.get_or_create(username='news-feed-editor',defaults={'first_name':'NexusUp','last_name':'Source Desk','is_active':False})
        if created:author.set_unusable_password();author.save()
        for row in rows:
            digest=hashlib.sha256(row['url'].encode()).hexdigest()
            if Article.objects.filter(source_url_hash=digest).exists():skipped+=1;continue
            cat=source.default_category
            for tag in row['tags']:
                slug=source.category_map.get(tag)
                if slug:cat=Category.objects.filter(slug=slug).first() or cat;break
            image=''
            if source.allow_images and row['image']:
                parsed=urlsplit(row['image'])
                if parsed.scheme=='https' and parsed.hostname in source.image_hosts:image=row['image'][:1000]
            try:
                with transaction.atomic():
                    Article.objects.create(title=row['title'],slug=(slugify(row['title'])[:170] or 'news')+'-'+digest[:16],
                        category=cat,author=author,excerpt=row['excerpt'],body='Read the original publisher for the complete report. This entry contains feed metadata only.',
                        source=source,canonical_source_url=row['url'],source_url_hash=digest,source_guid=row['guid'],
                        source_published_at=row['published'],published_at=row['published'] or now,imported_at=now,
                        remote_image_url=image,image_alt=row['title'] if image else '',image_credit=source.name if image else '',
                        status='published' if source.auto_publish else 'draft',featured=False,is_sample=False)
                imported+=1
            except IntegrityError:skipped+=1
        source.last_success_at=now;source.last_error='';source.save(update_fields=['last_success_at','last_error'])
        FetchRun.objects.create(source=source,success=True,imported=imported,skipped=skipped)
        return {'imported':imported,'skipped':skipped}
    except Exception as exc:
        # Never store credentials/URLs or raw provider responses in public/admin errors.
        error=type(exc).__name__+': fetch/parse failed; check source availability, format and provider limits.'
        if not dry_run:
            source.last_error=error;source.save(update_fields=['last_error'])
            FetchRun.objects.create(source=source,success=False,error=error,imported=imported,skipped=skipped)
        raise ValueError(error) from exc
