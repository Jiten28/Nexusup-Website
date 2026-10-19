from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib import messages
from django.core.cache import cache
from django.conf import settings
from django.http import HttpResponse, Http404
from django.views.decorators.http import require_GET
from .models import Article, Category
from .forms import CommentForm, ContactForm

def published():
    return Article.objects.published().select_related('category','author')

def home(request):
    posts = published()
    hero = posts.filter(featured=True).first() or posts.first()
    return render(request,'news/home.html',{'hero':hero,'highlights':posts.exclude(pk=hero.pk)[:3] if hero else [],'latest':posts[:6],'picks':posts.filter(featured=True)[:3]})

def listing(request, slug=None):
    category = get_object_or_404(Category,slug=slug) if slug else None
    q = request.GET.get('q','').strip()[:150]
    posts = published()
    if category: posts = posts.filter(category=category)
    if q: posts = posts.filter(Q(title__icontains=q)|Q(excerpt__icontains=q)|Q(body__icontains=q))
    page = Paginator(posts,6).get_page(request.GET.get('page'))
    return render(request,'news/list.html',{'page_obj':page,'selected_category':category,'q':q,'result_count':posts.count()})

def throttle(request, scope):
    # Demo-only per-session throttle, NOT a production anti-abuse solution.
    if not request.session.session_key: request.session.create()
    key = f'{scope}:{request.session.session_key}'
    return not cache.add(key,True,timeout=30)

def article(request,slug):
    post = get_object_or_404(published(),slug=slug)
    form = CommentForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        if throttle(request,'comment'):
            form.add_error(None,'Please wait 30 seconds before submitting again.')
        else:
            comment = form.save(commit=False); comment.article = post; comment.save()
            messages.success(request,'Saved locally for moderation. Your comment is not public until approved.')
            return redirect(post.get_absolute_url()+'#discussion')
    return render(request,'news/article.html',{'article':post,'form':form,'comments':post.comments.filter(approved=True),'related':published().filter(category=post.category).exclude(pk=post.pk)[:3]})

def contact(request):
    form = ContactForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        if throttle(request,'contact'): form.add_error(None,'Please wait 30 seconds before submitting again.')
        else:
            form.save(); messages.success(request,'Demo message saved locally. No email was sent.')
            return redirect('contact')
    return render(request,'news/contact.html',{'form':form})

def info(request,slug):
    pages = {
        'about':('A clearer view of what matters.','NexusUp is being reimagined as an accessible, independent-feeling editorial experience. This is a separate local redesign demo, not the live publication. Every seeded story is sample content, not verified reporting.'),
        'privacy':('Demo privacy notice','This local demo stores submitted comments, contact names, email addresses and messages in its demo database. Do not enter sensitive or real personal information. Bookmarks and theme preferences are stored in this browser. A session cookie supports forms and the admin. No analytics, advertising trackers, translation requests or outbound email are enabled. Clear demo.sqlite3 and browser storage to reset. This notice is not a production privacy policy.'),
        'terms':('Demo terms & editorial note','Sample articles demonstrate layout and workflow only. They are not factual news, financial advice or match predictions. Supplied images are local reference assets whose ownership and publication rights remain unverified. Production editorial, rights, accessibility and legal review are required before launch.'),
    }
    if slug not in pages: raise Http404
    title,body=pages[slug]
    return render(request,'news/info.html',{'title':title,'body':body})

@require_GET
def ads(request):
    if not settings.ADS_TXT_ENABLED:
        return HttpResponse('# Local demo: advertising disabled. Original publisher declaration is in docs/reference-ads.txt.\n',content_type='text/plain')
    return HttpResponse((settings.BASE_DIR/'docs/reference-ads.txt').read_text(),content_type='text/plain')

@require_GET
def robots(request):
    return HttpResponse('User-agent: *\nDisallow: /\n# Demo must not be indexed. Review robots policy before any approved launch.\n',content_type='text/plain')

def not_found(request,exception):
    return render(request,'404.html',status=404)
