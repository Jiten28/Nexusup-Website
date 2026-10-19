from django.core.management.base import BaseCommand
from news.models import Category,NewsSource
class Command(BaseCommand):
    help='Add missing category/source candidates only; sources disabled until rights review. Existing records unchanged.'
    def handle(self,*args,**o):
        for i,name in enumerate(['India','World','Politics','Sports','Entertainment','Health and Lifestyle'],10):
            from django.utils.text import slugify
            Category.objects.get_or_create(slug=slugify(name),defaults={'name':name,'position':i})
        for name,slug,url in [('BBC News — India','india','https://feeds.bbci.co.uk/news/world/asia/india/rss.xml'),('BBC News — World','world','https://feeds.bbci.co.uk/news/world/rss.xml')]:
            NewsSource.objects.get_or_create(feed_url=url,defaults={'name':name,'default_category':Category.objects.get(slug=slug),'terms_url':'https://www.bbc.co.uk/news/10628494','reuse_notes':'Candidate RSS metadata source. Use BBC News attribution; no BBC marks. Review current feed/reuse terms and image rights before enabling.'})
        self.stdout.write('Missing categories/source candidates added; feeds disabled, no articles fetched.')
