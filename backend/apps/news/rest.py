"""Public read-only editorial API; write forms retain Django CSRF and moderation."""
from django.db.models import Q, Count
from django.db.models.functions import Coalesce
from django.db import connection
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST
from django.core.cache import cache
from rest_framework import serializers, generics
from rest_framework.pagination import PageNumberPagination
from .models import Article, Category, Tag
from .forms import ContactForm, CommentForm
import json

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model=Category; fields=['id','name','slug']
class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model=Tag; fields=['id','name','slug']
class ArticleSerializer(serializers.ModelSerializer):
    category=CategorySerializer(read_only=True)
    tags=TagSerializer(many=True,read_only=True)
    image=serializers.SerializerMethodField()
    source_name=serializers.CharField(source='source_label',read_only=True)
    date=serializers.DateTimeField(source='display_date',read_only=True)
    reading_minutes=serializers.IntegerField(read_only=True)
    content_kind=serializers.SerializerMethodField()
    def get_content_kind(self,obj):
        if not (obj.source_id or obj.imported_at): return 'editorial'
        fallback='Read the original publisher for the complete report. This entry contains feed metadata only.'
        return 'feed_content' if (obj.body or '').strip() and (obj.body or '').strip() != fallback else 'feed_summary'
    class Meta:
        model=Article
        fields=['id','title','slug','excerpt','category','tags','image','image_alt','image_credit','source_name','canonical_source_url','date','featured','is_sample','reading_minutes','content_kind']
    def get_image(self,obj):
        value=obj.image_src
        return self.context['request'].build_absolute_uri(value) if value else ''
class DetailSerializer(ArticleSerializer):
    comments=serializers.SerializerMethodField()
    class Meta(ArticleSerializer.Meta):
        fields=ArticleSerializer.Meta.fields+['body','comments']
    def get_comments(self,obj):
        return list(obj.comments.filter(approved=True).values('name','body','created_at')[:100])
class Pagination(PageNumberPagination):
    page_size=12; page_size_query_param='page_size'; max_page_size=24

def public(include_samples=False,light=False):
    qs=Article.objects.published()
    if not light:qs=qs.select_related('category','author','source').prefetch_related('tags')
    qs=qs.order_by(Coalesce('source_published_at','published_at').desc(),'-id')
    # Retain labeled samples for sample-only installations, never rank them over real news.
    if not include_samples and qs.filter(is_sample=False).exists():
        qs=qs.filter(is_sample=False)
    return qs
class ArticleList(generics.ListAPIView):
    serializer_class=ArticleSerializer; pagination_class=Pagination
    def get_queryset(self):
        q=public(); args=self.request.query_params
        term=args.get('q','').strip()[:120]
        if term:q=q.filter(Q(title__icontains=term)|Q(excerpt__icontains=term)|Q(body__icontains=term))
        if args.get('category'):q=q.filter(category__slug=args['category'][:80])
        if args.get('tag'):q=q.filter(tags__slug=args['tag'][:80])
        if args.get('featured')=='1':q=q.filter(featured=True)
        exclude=[int(x) for x in args.get('exclude','').split(',')[:24] if x.isdigit()]
        return q.exclude(pk__in=exclude).distinct()
class ArticleDetail(generics.RetrieveAPIView):
    serializer_class=DetailSerializer; lookup_field='slug'
    def get_queryset(self):return public(include_samples=True)
class CategoryListSerializer(CategorySerializer):
    # Number of publicly visible stories, so the UI can hide empty categories instead of
    # linking to pages that can only say "No stories yet".
    article_count=serializers.SerializerMethodField()
    class Meta(CategorySerializer.Meta):
        fields=CategorySerializer.Meta.fields+['article_count']
    def get_article_count(self,obj):return self.context.get('counts',{}).get(obj.pk,0)
class Categories(generics.ListAPIView):
    queryset=Category.objects.all(); serializer_class=CategoryListSerializer
    def get_serializer_context(self):
        context=super().get_serializer_context()
        rows=public(light=True).order_by().values('category_id').annotate(n=Count('id'))
        context['counts']={r['category_id']:r['n'] for r in rows}
        return context
class Tags(generics.ListAPIView):
    queryset=Tag.objects.all(); serializer_class=TagSerializer
@require_GET
def home(request):
    qs=public(); featured=list(qs.filter(featured=True)[:1])
    supporting=list(qs.exclude(pk__in=[a.pk for a in featured])[:4]) if featured else []
    feature=featured+supporting # Primary story first in DOM/screen-reader order.
    remaining=qs.exclude(pk__in=[a.pk for a in feature])
    carousel=list(remaining.exclude(image_path='',remote_image_url='')[:4])
    if len(carousel)<4:
        carousel += list(remaining.exclude(pk__in=[a.pk for a in carousel])[:4-len(carousel)])
    serialize=lambda rows: ArticleSerializer(rows,many=True,context={'request':request}).data
    return JsonResponse({'carousel':serialize(carousel),'featured':serialize(feature),'excluded':[a.pk for a in feature+carousel]})
@require_GET
def related(request,slug):
    from django.shortcuts import get_object_or_404
    article=get_object_or_404(public(include_samples=True),slug=slug)
    data=ArticleSerializer(public(include_samples=True).filter(is_sample=article.is_sample,category=article.category).exclude(pk=article.pk)[:4],many=True,context={'request':request}).data
    return JsonResponse({'results':data})
@require_GET
def health(request): return JsonResponse({'status':'ok'})
@require_GET
def readiness(request):
    try:
        with connection.cursor() as cursor:cursor.execute('SELECT 1');cursor.fetchone()
        return JsonResponse({'status':'ready','database':connection.vendor})
    except Exception:return JsonResponse({'status':'unavailable'},status=503)
@require_GET
@ensure_csrf_cookie
def csrf(request): return JsonResponse({'csrfToken':get_token(request)})
@require_POST
@csrf_protect
def submit(request,slug=None):
    if len(request.body)>10000:return JsonResponse({'error':'Request too large'},status=400)
    # Per-session plus per-IP limit (shared cache/reverse-proxy limit required for multiworker).
    key='forms:'+request.META.get('REMOTE_ADDR','')
    if not cache.add(key,True,10):return JsonResponse({'error':'Please wait before submitting again'},status=429)
    try:data=json.loads(request.body)
    except (ValueError,TypeError):return JsonResponse({'error':'Invalid JSON'},status=400)
    form=CommentForm(data) if slug else ContactForm(data)
    if not form.is_valid():return JsonResponse({'errors':form.errors},status=400)
    obj=form.save(commit=False)
    if slug:
        from django.shortcuts import get_object_or_404
        obj.article=get_object_or_404(public(include_samples=True),slug=slug)
    obj.save()
    return JsonResponse({'message':'Received for editorial review.' if slug else 'Message received by the local editorial inbox.'},status=201)
