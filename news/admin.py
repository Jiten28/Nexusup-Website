from django.contrib import admin
from .models import Article,Category,Comment,ContactMessage
@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ['title','category','status','is_sample','published_at']
    list_filter = ['status','category','is_sample']
    search_fields = ['title','body']
    prepopulated_fields = {'slug':['title']}
    readonly_fields = ['updated_at']
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
