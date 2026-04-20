from django.db import migrations, models


def seed_default_pipeline_stages(apps, schema_editor):
    PipelineStage = apps.get_model('crm', 'PipelineStage')
    if PipelineStage.objects.exists():
        return

    defaults = [
        ('contactar', 'A contactar', 1),
        ('enviar', 'Enviar proposta', 2),
        ('negociacao', 'Em negociacao', 3),
        ('credito', 'Analise de credito', 4),
        ('followup', 'Follow up', 5),
        ('aprovada', 'Venda aprovada', 6),
        ('perdido', 'Perdido', 7),
    ]
    PipelineStage.objects.bulk_create(
        [PipelineStage(chave=chave, nome=nome, ordem=ordem) for chave, nome, ordem in defaults]
    )


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PipelineStage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=120)),
                ('chave', models.SlugField(max_length=50, unique=True)),
                ('ordem', models.PositiveIntegerField(db_index=True, default=1)),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['ordem', 'id'],
            },
        ),
        migrations.AlterField(
            model_name='lead',
            name='estagio',
            field=models.CharField(db_index=True, default='contactar', max_length=50),
        ),
        migrations.RunPython(seed_default_pipeline_stages, migrations.RunPython.noop),
    ]