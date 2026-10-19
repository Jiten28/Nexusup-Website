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

class Article(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PUBLISHED = 'published', 'Published'
    title = models.CharField(max_length=220)
    slug = models.SlugField(max_length=240, unique=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    author = models.ForeignKey(get_user_model(), on_delete=models.PROTECT)
    excerpt = models.CharField(max_length=360)
    body = models.TextField(help_text='Plain text. Blank lines separate paragraphs; HTML is escaped.')
    image_path = models.CharField(max_length=350, blank=True, validators=[RegexValidator(r'^(?!/)(?!.*(?:\.\.|\\))[A-Za-z0-9_./-]+$','Use a safe relative media path.')])
    image_alt = models.CharField(max_length=220, blank=True)
    image_credit = models.CharField(max_length=220, blank=True)
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
    def reading_minutes(self): return max(1, (len(self.body.split()) + 199) // 200)
    @property
    def paragraphs(self): return self.body.split('\n\n')

class Comment(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='comments')
    name = models.CharField(max_length=80)
    body = models.TextField(max_length=2000)
    approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ['created_at']
    def __str__(self): return f'{self.name}: {self.body[:40]}'

class ContactMessage(models.Model):
    name = models.CharField(max_length=80)
    email = models.EmailField()
    message = models.TextField(max_length=4000)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f'{self.name} — {self.created_at:%Y-%m-%d}'
