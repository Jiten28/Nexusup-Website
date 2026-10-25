from django.core.management.base import BaseCommand
from django.utils.text import slugify
from apps.news.models import Category,NewsSource

# Additive candidates only. Every source is created DISABLED with rights NOT confirmed;
# nothing is fetched or published until the owner reviews each source's terms in admin.
CATEGORIES=['India','World','Politics','Sports','Entertainment','Health and Lifestyle','Cricket','Business','Stock Market','Investments','Technology','Science']
BBC_TERMS='https://www.bbc.co.uk/news/10628494'
BBC_NOTE='Candidate RSS metadata source. Use BBC News attribution; no BBC marks. Review current feed/reuse terms and image rights before enabling.'
BBC_FEEDS=[('BBC News \u2014 India','india','https://feeds.bbci.co.uk/news/world/asia/india/rss.xml'),
 ('BBC News \u2014 World','world','https://feeds.bbci.co.uk/news/world/rss.xml'),
 ('BBC News \u2014 Technology','technology','https://feeds.bbci.co.uk/news/technology/rss.xml'),
 ('BBC News \u2014 Business','business','https://feeds.bbci.co.uk/news/business/rss.xml'),
 ('BBC News \u2014 Science','science','https://feeds.bbci.co.uk/news/science_and_environment/rss.xml'),
 ('BBC News \u2014 Health','health-and-lifestyle','https://feeds.bbci.co.uk/news/health/rss.xml'),
 ('BBC News \u2014 Entertainment','entertainment','https://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml'),
 ('BBC News \u2014 Politics','politics','https://feeds.bbci.co.uk/news/politics/rss.xml'),
 ('BBC Sport','sports','https://feeds.bbci.co.uk/sport/rss.xml'),
 ('BBC Sport \u2014 Cricket','cricket','https://feeds.bbci.co.uk/sport/cricket/rss.xml')]
# NewsAPI: DEVELOPMENT/TESTING ONLY on the free plan (see docs/NEWS.md).
NEWSAPI_FEEDS=[('NewsAPI \u2014 Stock market','stock-market','https://newsapi.org/v2/everything?q=%22stock+market%22&language=en&sortBy=publishedAt'),
 ('NewsAPI \u2014 Investments','investments','https://newsapi.org/v2/everything?q=investing&language=en&sortBy=publishedAt'),
 ('NewsAPI \u2014 India business headlines','business','https://newsapi.org/v2/top-headlines?country=in&category=business')]
class Command(BaseCommand):
    help='Add missing category/source candidates only; sources disabled until rights review. Existing records unchanged.'
    def handle(self,*args,**o):
        for i,name in enumerate(CATEGORIES,10):
            # get_or_create by slug: existing categories (and their articles) are never touched.
            Category.objects.get_or_create(slug=slugify(name),defaults={'name':name,'position':i})
        added=0
        for rows,adapter,note in ((BBC_FEEDS,'rss',BBC_NOTE),(NEWSAPI_FEEDS,'newsapi','Candidate NewsAPI source. Free plan is development/testing only and grants no republication or image rights. Needs NEWS_API_KEY in backend/.env.')):
            for name,slug,url in rows:
                _,created=NewsSource.objects.get_or_create(feed_url=url,defaults={'name':name,'adapter':adapter,'default_category':Category.objects.get(slug=slug),'terms_url':BBC_TERMS if adapter=='rss' else 'https://newsapi.org/terms','reuse_notes':note,'interval_minutes':180 if adapter=='newsapi' else 30})
                added+=int(created)
        self.stdout.write(f'Missing categories added; {added} new source candidate(s) created disabled with rights unconfirmed. Existing sources/articles unchanged; nothing fetched.')
