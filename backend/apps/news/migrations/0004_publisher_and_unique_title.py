from django.db import migrations, models

def nullable_hashes(apps, schema_editor):
    # Preserve every article. Empty historical defaults are NOT real hashes.
    Article=apps.get_model('news','Article'); alias=schema_editor.connection.alias
    Article.objects.using(alias).filter(normalized_title_hash='').update(normalized_title_hash=None)
    seen=set()
    for article in Article.objects.using(alias).exclude(normalized_title_hash=None).order_by('pk').iterator():
        if article.normalized_title_hash in seen:
            Article.objects.using(alias).filter(pk=article.pk).update(normalized_title_hash=None)
        else:seen.add(article.normalized_title_hash)

class Migration(migrations.Migration):
    dependencies=[('news','0003_editorial_trust_tags_dedup')]
    operations=[
        migrations.AddField(model_name='article',name='publisher_name',field=models.CharField(blank=True,max_length=120)),
        migrations.AlterField(model_name='article',name='normalized_title_hash',field=models.CharField(blank=True,null=True,max_length=64)),
        migrations.RunPython(nullable_hashes,migrations.RunPython.noop),
        migrations.AlterField(model_name='article',name='normalized_title_hash',field=models.CharField(blank=True,null=True,max_length=64,unique=True)),
    ]
