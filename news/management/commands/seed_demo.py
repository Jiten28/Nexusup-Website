import json
from pathlib import Path
from datetime import timedelta
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify
from news.models import Article,Category
class Command(BaseCommand):
    help = 'Create clearly labeled samples in a local SQLite demo only. Idempotent; never overwrites existing articles.'
    @transaction.atomic
    def handle(self,*args,**options):
        if not settings.DEBUG or settings.DB_ENGINE != 'sqlite':
            raise CommandError('Sample seeding is restricted to the local SQLite demo.')
        author,created=get_user_model().objects.get_or_create(username='demo-editor',defaults={'first_name':'NexusUp','last_name':'Demo Desk','is_active':False})
        if created: author.set_unusable_password();author.save()
        cats={}
        for n,name in enumerate(['Cricket','Business','Stock Market','Investments','Technology','Science']):
            c,_=Category.objects.get_or_create(slug=slugify(name),defaults={'name':name,'position':n});cats[c.slug]=c
        rows=json.loads((Path(__file__).resolve().parents[2]/'demo_data.json').read_text())
        body=("This is original sample copy for the NexusUp redesign demo. It is not a migrated WordPress article and should not be read as factual reporting. The headline and summary demonstrate a possible editorial voice rather than an account of an actual event.\n\n"
              "A useful story starts by making space for context. What has changed? Which details are established, and which questions remain open? A calmer reading experience helps readers distinguish the two without getting lost in the noise.\n\n"
              "For this demonstration, imagine an editor gathering notes, checking sources and deciding what a reader needs to understand first. The finished production article would include verified facts, appropriate attribution, publication dates, image credits and a clear corrections process. None of those checks can be inferred from a reference image alone.\n\n"
              "The design gives that work room to breathe: readable type, clear categories and a focused page. You can save this sample in your browser, copy its local link or leave a fictional comment for moderation. These are local demonstration workflows, not a connection to the current website.\n\n"
              "Before launch, replace this entire sample with reviewed content, clear the demo records and complete a verified migration on an isolated staging copy. No live scores, financial claims or production records are supplied here.")
        for n,(cat,title,excerpt,image) in enumerate(rows):
            Article.objects.get_or_create(slug=slugify(title),defaults={'title':title,'category':cats[cat],'author':author,'excerpt':excerpt,'body':body,'image_path':image,'image_alt':'Reference cricket photograph; context and rights unverified' if cat=='cricket' else 'Reference finance illustration; rights unverified','image_credit':'Supplied WordPress reference archive. Rights and original credit require verification.','status':'published','published_at':timezone.now()-timedelta(hours=n+1),'featured':n in [0,3,4],'is_sample':True})
        self.stdout.write(self.style.SUCCESS('Sample content ready. No production data was imported.'))
