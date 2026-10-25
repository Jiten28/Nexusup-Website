from django.contrib.syndication.views import Feed
from django.contrib.sitemaps import Sitemap
from django.conf import settings
from .models import Article
class LatestFeed(Feed):
    title = 'NexusUp — latest stories'
    description = 'Published stories from NexusUp. Illustrative samples are individually labeled.'
    link = '/'
    def items(self): return Article.objects.published().select_related('category','author')[:20]
    def item_title(self,item): return ('[SAMPLE] ' if item.is_sample else '') + item.title
    def item_description(self,item): return item.excerpt
    def item_pubdate(self,item): return item.published_at
    def item_link(self,item): return settings.FRONTEND_URL + item.get_absolute_url()
class ArticleSitemap(Sitemap):
    protocol = None  # follow FRONTEND_URL (http in local development, https in production)
    def items(self): return Article.objects.published()
    def lastmod(self,obj): return obj.updated_at
    def get_urls(self,page=1,site=None,protocol=None):
        from urllib.parse import urlsplit
        from types import SimpleNamespace
        parts=urlsplit(settings.FRONTEND_URL)
        return super().get_urls(page,SimpleNamespace(domain=parts.netloc,name='NexusUp'),parts.scheme)
