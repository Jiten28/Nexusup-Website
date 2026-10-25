from django.contrib import admin
from .models import Article,Category,Comment,ContactMessage,NewsSource,FetchRun,Tag
@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ['title','category','status','is_sample','published_at']
    list_filter = ['status','category','is_sample','source']
    search_fields = ['title','body']
    prepopulated_fields = {'slug':['title']}
    readonly_fields = ['updated_at','imported_at','source_url_hash']
    actions = ['publish_selected','make_central']
    @admin.action(description='Publish selected articles now')
    def publish_selected(self,request,queryset):
        from django.utils import timezone
        n=queryset.filter(status='draft').update(status='published',published_at=timezone.now())
        self.message_user(request,f'{n} article(s) published.')
    @admin.action(description='Make ONE selected published article the central featured story')
    def make_central(self,request,queryset):
        if queryset.count()!=1 or not queryset.published().exists():
            self.message_user(request,'Select exactly one currently published article.',level='error');return
        from django.db import transaction
        with transaction.atomic():
            Article.objects.filter(featured=True).update(featured=False)
            queryset.update(featured=True)
        self.message_user(request,'Central featured story changed. Imports will not replace it.')
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug':['name']}
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['name','article','approved','created_at']
    list_filter = ['approved']
    actions = ['approve']
    @admin.action(description='Approve selected comments')
    def approve(self,request,queryset): queryset.update(approved=True)
@admin.register(ContactMessage)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['name','email','created_at']
    readonly_fields = ['name','email','message','created_at']
    def has_add_permission(self,request): return False

@admin.register(NewsSource)
class NewsSourceAdmin(admin.ModelAdmin):
    """Where you manage news feeds. Typical flow: Add recommended sources -> tick sources ->
    'Approve' -> 'Fetch now' -> open Articles and publish (or turn on auto-publish)."""
    change_list_template = 'admin/news/newssource/change_list.html'
    list_display=['name','default_category','enabled','rights_confirmed','allow_images','trusted','auto_publish','article_count','picture_count','last_success_at','last_error']
    readonly_fields=['last_attempt_at','last_success_at','next_fetch_at','last_error']
    list_filter=['enabled','rights_confirmed','trusted','auto_publish','adapter']
    actions = ['approve_sources','fetch_selected_sources','get_saved_pictures','auto_publish_sources','disable_sources']

    def article_count(self, obj): return obj.article_set.count()
    article_count.short_description = 'Articles'

    def picture_count(self, obj): return obj.article_set.exclude(remote_image_url='', image_path='').count()
    picture_count.short_description = 'With picture'

    @staticmethod
    def feed_image_hosts(source):
        """Hostnames of the pictures the feed itself links to (https only). Nothing is guessed."""
        from .ingestion import ADAPTERS
        from .network import fetch_bytes
        from urllib.parse import urlparse
        hosts = set()
        if source.adapter == 'rss' and ADAPTERS.get('rss'):
            for row in ADAPTERS['rss']().parse(fetch_bytes(source.feed_url)):
                u = urlparse(row.get('image') or '')
                if u.scheme == 'https' and u.hostname: hosts.add(u.hostname.lower())
        return hosts

    def get_urls(self):
        from django.urls import path
        return [path('add-recommended/', self.admin_site.admin_view(self.add_recommended), name='news_newssource_add_recommended')] + super().get_urls()

    def add_recommended(self, request):
        from django.core.management import call_command
        from django.http import HttpResponseRedirect
        from django.urls import reverse
        if request.method == 'POST' and self.has_add_permission(request):
            call_command('configure_sources', verbosity=0)
            self.message_user(request, 'Recommended categories and sources added. They are OFF until you approve them below.')
        return HttpResponseRedirect(reverse('admin:news_newssource_changelist'))

    def changelist_view(self, request, extra_context=None):
        from django.conf import settings
        if not settings.NEWS_FETCH_ENABLED:
            self.message_user(request, 'Fetching is switched off. Set NEWS_FETCH_ENABLED=1 in backend/.env and restart the server.', level='warning')
        return super().changelist_view(request, extra_context)

    @admin.action(description='1. Approve: I have permission to use these feeds (enable + confirm rights + allow their pictures)', permissions=['change'])
    def approve_sources(self, request, queryset):
        for source in queryset:
            hosts = set()
            try:
                hosts = self.feed_image_hosts(source)
            except Exception as exc:
                self.message_user(request, f'{source.name}: could not read the feed to find picture hosts ({type(exc).__name__}: {exc}). Approved without pictures.', level='warning')
            source.enabled = True
            source.rights_confirmed = True
            if hosts:
                source.allow_images = True
                source.image_hosts = sorted(set(source.image_hosts or []) | hosts)
            source.save()
            note = ', '.join(sorted(hosts)) or ('none found' if source.adapter == 'rss' else 'not automatic for NewsAPI: its pictures come from many different publishers, so list the hosts you are allowed to use yourself')
            self.message_user(request, f'{source.name}: approved. Picture hosts: {note}.')

    @admin.action(description='2. Fetch now (news text and pictures)', permissions=['change'])
    def fetch_selected_sources(self, request, queryset):
        from .ingestion import ingest
        for source in queryset:
            try:
                result = ingest(source)
                self.message_user(request, f'{source.name}: {result}')
            except ValueError as exc:
                self.message_user(request, f'{source.name}: {exc}', level='error')
            except Exception as exc:  # never show a crash page; show what went wrong instead
                self.message_user(request, f'{source.name}: unexpected {type(exc).__name__}: {exc}', level='error')

    @admin.action(description='2b. Get pictures for stories already saved (fills the picture hosts from the feed if they are empty)', permissions=['change'])
    def get_saved_pictures(self, request, queryset):
        from io import StringIO
        from django.core.management import call_command
        for source in queryset:
            if not (source.enabled and source.rights_confirmed):
                self.message_user(request, f'{source.name}: approve it first (action 1).', level='error'); continue
            try:
                if source.allow_images and not source.image_hosts:
                    hosts = self.feed_image_hosts(source)
                    if hosts:
                        source.image_hosts = sorted(hosts); source.save(update_fields=['image_hosts'])
                if not source.allow_images:
                    self.message_user(request, f'{source.name}: "Allow images" is off, so no pictures can be used. Run action 1 (or tick it in the source) if you have permission.', level='warning'); continue
                out = StringIO()
                call_command('backfill_images', source=source.pk, apply=True, stdout=out)
                self.message_user(request, f'{source.name}: ' + ' | '.join(l.strip() for l in out.getvalue().splitlines() if l.strip()))
            except Exception as exc:
                self.message_user(request, f'{source.name}: {type(exc).__name__}: {exc}', level='error')

    @admin.action(description='3. Publish new stories from these sources automatically (trusted + auto-publish)', permissions=['change'])
    def auto_publish_sources(self, request, queryset):
        n = queryset.filter(enabled=True, rights_confirmed=True).update(trusted=True, auto_publish=True)
        self.message_user(request, f'{n} source(s) will publish new stories automatically. Others were skipped (approve them first).')

    @admin.action(description='Switch off (disable) selected sources', permissions=['change'])
    def disable_sources(self, request, queryset):
        self.message_user(request, f'{queryset.update(enabled=False, auto_publish=False)} source(s) disabled.')

@admin.register(FetchRun)
class FetchRunAdmin(admin.ModelAdmin):
    list_display=['source','started_at','state','success','fetched','parsed','rejected','duplicates','imported','published','error']
    readonly_fields=['source','started_at','state','success','fetched','parsed','rejected','duplicates','imported','skipped','published','error']
    def has_add_permission(self,request):return False

admin.site.register(Tag)
