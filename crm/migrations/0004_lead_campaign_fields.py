# Generated manually for landing/CRM integration

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0003_alter_lead_servico'),
    ]

    operations = [
        migrations.AddField(
            model_name='lead',
            name='page_url',
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name='lead',
            name='referrer',
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name='lead',
            name='utm_source',
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name='lead',
            name='utm_medium',
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name='lead',
            name='utm_campaign',
            field=models.CharField(blank=True, max_length=160),
        ),
        migrations.AddField(
            model_name='lead',
            name='utm_term',
            field=models.CharField(blank=True, max_length=160),
        ),
        migrations.AddField(
            model_name='lead',
            name='utm_content',
            field=models.CharField(blank=True, max_length=160),
        ),
    ]
