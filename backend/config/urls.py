from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from apps.news import views,api,rest
from apps.news.frontend import public_page
from apps.news.feeds import LatestFeed,ArticleSitemap
urlpatterns = [
    path('api/articles/',rest.ArticleList.as_view()),
    path('api/articles/<slug:slug>/',rest.ArticleDetail.as_view()),
    path('api/articles/<slug:slug>/related/',rest.related),
    path('api/articles/<slug:slug>/comments/',rest.submit),
    path('api/categories/',rest.Categories.as_view()),path('api/tags/',rest.Tags.as_view()),
    path('api/home/',rest.home),path('api/contact/',rest.submit),path('api/csrf/',rest.csrf),
    path('health/live/',rest.health),path('health/ready/',rest.readiness),
    path('api/currency/',api.currency), path('api/cities/',api.cities), path('api/weather/',api.weather),
    path('api/languages/',api.languages), path('api/translate/',api.translate),
    path('',public_page(views.home),name='home'), path('stories/',public_page(views.listing),name='stories'),
    path('search/',public_page(views.listing),name='search'), path('category/<slug:slug>/',public_page(views.listing),name='category'),
    path('story/<slug:slug>/',public_page(views.article),name='article'), path('contact/',public_page(views.contact),name='contact'),
    path('about/',public_page(views.info),{'slug':'about'},name='about'), path('privacy/',public_page(views.info),{'slug':'privacy'},name='privacy'),
    path('terms/',public_page(views.info),{'slug':'terms'},name='terms'),
    path('sources/',public_page(views.info),{'slug':'sources'},name='sources'),
    path('feed/',LatestFeed(),name='feed'), path('sitemap.xml',sitemap,{'sitemaps':{'articles':ArticleSitemap}},name='sitemap'),
    path('robots.txt',views.robots), path('ads.txt',views.ads), path('admin/',admin.site.urls),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)
    urlpatterns += static('/wp-content/uploads/',document_root=settings.MEDIA_ROOT)
handler404 = 'apps.news.views.not_found'
admin.site.site_header = 'NexusUp editorial — local demo'
