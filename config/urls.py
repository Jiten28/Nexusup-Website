from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from news import views,api
from news.feeds import LatestFeed,ArticleSitemap
urlpatterns = [
    path('api/currency/',api.currency), path('api/cities/',api.cities), path('api/weather/',api.weather),
    path('api/languages/',api.languages), path('api/translate/',api.translate),
    path('',views.home,name='home'), path('stories/',views.listing,name='stories'),
    path('search/',views.listing,name='search'), path('category/<slug:slug>/',views.listing,name='category'),
    path('story/<slug:slug>/',views.article,name='article'), path('contact/',views.contact,name='contact'),
    path('about/',views.info,{'slug':'about'},name='about'), path('privacy/',views.info,{'slug':'privacy'},name='privacy'),
    path('terms/',views.info,{'slug':'terms'},name='terms'),
    path('feed/',LatestFeed(),name='feed'), path('sitemap.xml',sitemap,{'sitemaps':{'articles':ArticleSitemap}},name='sitemap'),
    path('robots.txt',views.robots), path('ads.txt',views.ads), path('admin/',admin.site.urls),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)
    urlpatterns += static('/wp-content/uploads/',document_root=settings.MEDIA_ROOT)
handler404 = 'news.views.not_found'
admin.site.site_header = 'NexusUp editorial — local demo'
