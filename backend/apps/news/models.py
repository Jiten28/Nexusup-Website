from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.core.validators import RegexValidator
from django.contrib.auth import get_user_model

class Category(models.Model):
    name = models.CharField(max_length=80)
    slug = models.SlugField(unique=True)
    position = models.PositiveSmallIntegerField(default=0)
    class Meta:
        ordering = ['position', 'name']
        verbose_name_plural = 'categories'
    def __str__(self): return self.name
    def get_absolute_url(self): return reverse('category', args=[self.slug])

class PublishedQuerySet(models.QuerySet):
    def published(self):
        return self.filter(status='published', published_at__lte=timezone.now())

class Tag(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(unique=True)
    def __str__(self): return self.name

class NewsSource(models.Model):
    name = models.CharField(max_length=100)
    feed_url = models.URLField(max_length=500)
    adapter = models.CharField(max_length=30, default='rss', help_text='Registered server-side adapter name, not executable code.')
    enabled = models.BooleanField(default=False)
    rights_confirmed = models.BooleanField(default=False)
    terms_url = models.URLField(blank=True)
    reuse_notes = models.TextField(blank=True)
    default_category = models.ForeignKey(Category, on_delete=models.PROTECT)
    category_map = models.JSONField(default=dict, blank=True, help_text='Provider category name to existing category slug.')
    allow_images = models.BooleanField(default=False)
    image_hosts = models.JSONField(default=list, blank=True, help_text='Explicit approved image hostnames; permission still required.')
    trusted = models.BooleanField(default=False, help_text="Explicit editorial trust; separate from permission to auto-publish.")
    auto_publish = models.BooleanField(default=False, help_text='Default is editorial review. Imports never become featured automatically.')
    fetch_full_text = models.BooleanField(default=False, help_text='Also read the full article page of each NEW story (respects robots.txt). Only tick this if the publisher permits reuse of their article text; requires rights confirmed.')
    interval_minutes = models.PositiveIntegerField(default=30)
    next_fetch_at = models.DateTimeField(null=True, blank=True)
    last_attempt_at = models.DateTimeField(null=True, blank=True)
    last_success_at = models.DateTimeField(null=True, blank=True)
    last_error = models.CharField(max_length=300, blank=True)
    def clean(self):
        from django.core.exceptions import ValidationError
        if not isinstance(self.category_map,dict) or any(not isinstance(k,str) or not isinstance(v,str) for k,v in self.category_map.items()):
            raise ValidationError({'category_map':'Use an object mapping feed category names to category slugs.'})
        if not isinstance(self.image_hosts,list) or any(not isinstance(h,str) or not h or '/' in h or ':' in h for h in self.image_hosts):
            raise ValidationError({'image_hosts':'Use a list of approved hostnames, without scheme or path.'})
        if self.interval_minutes<5:
            raise ValidationError({'interval_minutes':'Minimum interval is five minutes.'})
    def __str__(self): return self.name

class FetchRun(models.Model):
    source = models.ForeignKey(NewsSource, on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=False)
    imported = models.PositiveIntegerField(default=0)
    skipped = models.PositiveIntegerField(default=0)
    error = models.CharField(max_length=300, blank=True)
    state = models.CharField(max_length=12, default='legacy', choices=[('legacy','Legacy'),('running','Running'),('success','Success'),('failed','Failed'),('blocked','Blocked'),('deferred','Deferred')])
    fetched = models.PositiveIntegerField(default=0)
    parsed = models.PositiveIntegerField(default=0)
    rejected = models.PositiveIntegerField(default=0)
    duplicates = models.PositiveIntegerField(default=0)
    published = models.PositiveIntegerField(default=0)
    class Meta: ordering = ['-started_at']

class Article(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PUBLISHED = 'published', 'Published'
    source = models.ForeignKey(NewsSource, null=True, blank=True, on_delete=models.SET_NULL)
    canonical_source_url = models.URLField(max_length=1000, blank=True)
    source_url_hash = models.CharField(max_length=64, null=True, blank=True, unique=True)
    normalized_title_hash = models.CharField(max_length=64, blank=True, null=True, unique=True)
    tags = models.ManyToManyField(Tag, blank=True)
    publisher_name = models.CharField(max_length=120, blank=True)
    source_guid = models.CharField(max_length=255, blank=True)
    source_published_at = models.DateTimeField(null=True, blank=True)
    imported_at = models.DateTimeField(null=True, blank=True)
    remote_image_url = models.URLField(max_length=1000, blank=True)
    breaking_until = models.DateTimeField(null=True, blank=True, help_text='Editorially verified breaking status expires automatically; samples never qualify.')
    title = models.CharField(max_length=220)
    slug = models.SlugField(max_length=240, unique=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    author = models.ForeignKey(get_user_model(), on_delete=models.PROTECT)
    excerpt = models.CharField(max_length=360)
    body = models.TextField(help_text='Plain text. Blank lines separate paragraphs; HTML is escaped.')
    image_path = models.CharField(max_length=350, blank=True, validators=[RegexValidator(r'^(?!/)(?!.*(?:\.\.|\\))[A-Za-z0-9_./-]+$','Use a safe relative media path.')])
    image_alt = models.CharField(max_length=220, blank=True)
    image_credit = models.CharField(max_length=220, blank=True)
    ai_summary = models.TextField(blank=True, help_text='AI-written summary of the text we hold for this story. Always shown with an AI label.')
    ai_summary_at = models.DateTimeField(null=True, blank=True)
    ai_summary_model = models.CharField(max_length=80, blank=True)
    full_text_fetched_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT)
    published_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    featured = models.BooleanField(default=False)
    is_sample = models.BooleanField(default=True)
    legacy_wordpress_id = models.PositiveBigIntegerField(null=True, blank=True, unique=True)
    seo_description = models.CharField(max_length=170, blank=True)
    objects = PublishedQuerySet.as_manager()
    class Meta:
        ordering = ['-published_at', '-id']
        indexes = [models.Index(fields=['status','published_at'])]
    def __str__(self): return self.title
    def get_absolute_url(self): return reverse('article', args=[self.slug])
    @property
    def image_src(self):
        from django.conf import settings
        from django.core.files.storage import default_storage
        return default_storage.url(self.image_path) if self.image_path else self.remote_image_url
    @property
    def source_label(self):
        return (self.publisher_name or self.source.name) if self.source_id else (self.author.get_full_name() or self.author.username)
    @property
    def display_date(self):
        return self.source_published_at if self.imported_at else self.published_at
    @property
    def reading_minutes(self): return max(1, (len(self.body.split()) + 199) // 200)
    @property
    def paragraphs(self): return self.body.split('\n\n')

class Comment(models.Model):
    """A comment or a reply (parent set). Nothing is public until an editor approves it."""
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies',
                               help_text='Set for a reply. Replies are always one level deep.')
    name = models.CharField(max_length=80)
    body = models.TextField(max_length=2000)
    approved = models.BooleanField(default=False)
    rejected = models.BooleanField(default=False, help_text='Hidden for good (spam/abuse) but kept for the record.')
    is_editor = models.BooleanField(default=False, help_text='Shown with an "Editorial team" badge.')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ['created_at']
    @property
    def status(self): return 'rejected' if self.rejected else 'approved' if self.approved else 'pending'
    def __str__(self): return f'{self.name}: {self.body[:40]}'

class ContactMessage(models.Model):
    name = models.CharField(max_length=80)
    email = models.EmailField()
    message = models.TextField(max_length=4000)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f'{self.name} — {self.created_at:%Y-%m-%d}'
