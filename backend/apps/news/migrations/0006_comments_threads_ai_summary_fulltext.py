from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('news', '0005_fetch_run_accounting')]
    operations = [
        migrations.AddField('newssource', 'fetch_full_text', models.BooleanField(default=False, help_text='Also read the full article page of each NEW story (respects robots.txt). Only tick this if the publisher permits reuse of their article text; requires rights confirmed.')),
        migrations.AddField('article', 'ai_summary', models.TextField(blank=True, help_text='AI-written summary of the text we hold for this story. Always shown with an AI label.')),
        migrations.AddField('article', 'ai_summary_at', models.DateTimeField(blank=True, null=True)),
        migrations.AddField('article', 'ai_summary_model', models.CharField(blank=True, max_length=80)),
        migrations.AddField('article', 'full_text_fetched_at', models.DateTimeField(blank=True, null=True)),
        migrations.AddField('comment', 'parent', models.ForeignKey(blank=True, help_text='Set for a reply. Replies are always one level deep.', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='replies', to='news.comment')),
        migrations.AddField('comment', 'rejected', models.BooleanField(default=False, help_text='Hidden for good (spam/abuse) but kept for the record.')),
        migrations.AddField('comment', 'is_editor', models.BooleanField(default=False, help_text='Shown with an "Editorial team" badge.')),
    ]
