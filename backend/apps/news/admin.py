from django.contrib import admin
from .models import Article,Category,Comment,ContactMessage,NewsSource,FetchRun,Tag
@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ['title','category','status','is_sample','published_at']
    list_filter = ['status','category','is_sample','source']
    search_fields = ['title','body']
    prepopulated_fields = {'slug':['title']}
    readonly_fields = ['updated_at','imported_at','source_url_hash']
    actions = ['make_central']
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
    list_display=['name','enabled','rights_confirmed','trusted','auto_publish','last_success_at','last_error']
    readonly_fields=['last_attempt_at','last_success_at','next_fetch_at','last_error']
    list_filter=['enabled','rights_confirmed','trusted','auto_publish','adapter']
    actions = ['fetch_selected_sources']

    @admin.action(description='Fetch selected sources once (requires global enablement and approved rights)', permissions=['change'])
    def fetch_selected_sources(self, request, queryset):
        from .ingestion import ingest
        for source in queryset:
            try:
                result = ingest(source)
                self.message_user(request, f'Source {source.pk}: {result}')
            except ValueError as exc:
                self.message_user(request, f'Source {source.pk}: {exc}', level='error')

@admin.register(FetchRun)
class FetchRunAdmin(admin.ModelAdmin):
    list_display=['source','started_at','state','success','fetched','parsed','rejected','duplicates','imported','published','error']
    readonly_fields=['source','started_at','state','success','fetched','parsed','rejected','duplicates','imported','skipped','published','error']
    def has_add_permission(self,request):return False

admin.site.register(Tag)
