from django.contrib.auth.models import User
from django.db import models
from django.db.models import Max
from django.utils.text import slugify


class PipelineStage(models.Model):
    DEFAULT_STAGES = [
        ('contactar', 'A contactar', 1),
        ('enviar', 'Enviar proposta', 2),
        ('negociacao', 'Em negociacao', 3),
        ('credito', 'Analise de credito', 4),
        ('followup', 'Follow up', 5),
        ('aprovada', 'Venda aprovada', 6),
        ('perdido', 'Perdido', 7),
    ]

    nome = models.CharField(max_length=120)
    chave = models.SlugField(max_length=50, unique=True)
    ordem = models.PositiveIntegerField(default=1, db_index=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['ordem', 'id']

    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        stage_model = self.__class__
        if not self.chave:
            base_slug = slugify(self.nome)[:44] or 'etapa'
            candidate = base_slug
            suffix = 2
            while stage_model.objects.exclude(pk=self.pk).filter(chave=candidate).exists():
                suffix_text = f'-{suffix}'
                candidate = f'{base_slug[:50 - len(suffix_text)]}{suffix_text}'
                suffix += 1
            self.chave = candidate

        if not self.ordem:
            self.ordem = (stage_model.objects.exclude(pk=self.pk).aggregate(max_ordem=Max('ordem'))['max_ordem'] or 0) + 1

        super().save(*args, **kwargs)

    @classmethod
    def bootstrap_defaults(cls):
        if cls.objects.exists():
            return
        cls.objects.bulk_create(
            [cls(chave=chave, nome=nome, ordem=ordem) for chave, nome, ordem in cls.DEFAULT_STAGES]
        )

    @classmethod
    def first_stage_key(cls):
        return cls.objects.order_by('ordem', 'id').values_list('chave', flat=True).first() or 'contactar'

    @classmethod
    def label_for_key(cls, chave):
        if not chave:
            return ''
        nome = cls.objects.filter(chave=chave).values_list('nome', flat=True).first()
        return nome or chave.replace('-', ' ').replace('_', ' ').title()


class Lead(models.Model):
    SERVICO_CHOICES = [
        ('solar', 'Energia Solar'),
        ('climatizacao', 'Climatizacao'),
    ]

    ORIGEM_CHOICES = [
        ('site', 'Site / Google'),
        ('instagram', 'Instagram'),
        ('indicacao', 'Indicacao'),
        ('passante', 'Passante'),
        ('ativo', 'Prospeccao ativa'),
    ]

    nome_razao = models.CharField(max_length=255, verbose_name='Nome/Razao Social')
    whatsapp = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    documento = models.CharField(max_length=20, blank=True)
    cep = models.CharField(max_length=10, blank=True)
    endereco = models.CharField(max_length=255, blank=True)
    numero = models.CharField(max_length=10, blank=True)
    bairro = models.CharField(max_length=100, blank=True)
    cidade = models.CharField(max_length=100, blank=True)
    estado = models.CharField(max_length=2, blank=True)
    servico = models.CharField(max_length=50, choices=SERVICO_CHOICES, default='solar')
    origem = models.CharField(max_length=50, choices=ORIGEM_CHOICES, default='site')
    valor = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    estagio = models.CharField(max_length=50, default='contactar', db_index=True)
    observacoes = models.TextField(blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data_criacao']

    def __str__(self):
        return self.nome_razao

    def get_estagio_display(self):
        return PipelineStage.label_for_key(self.estagio)

    @property
    def historicos_recentes_card(self):
        return list(self.historicos.order_by('-data')[:3])


class Historico(models.Model):
    TIPO_CHOICES = [
        ('nota', 'Nota interna'),
        ('ligacao', 'Ligacao'),
        ('whatsapp', 'WhatsApp'),
        ('visita', 'Visita tecnica'),
        ('email', 'E-mail'),
        ('movimentacao', 'Movimentacao'),
    ]

    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='historicos')
    usuario = models.CharField(max_length=150, blank=True)
    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES, default='nota')
    nota = models.TextField()
    data = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data']

    def __str__(self):
        return f'{self.lead} - {self.get_tipo_display()}'


class SavedFilter(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='crm_saved_filters')
    nome = models.CharField(max_length=120)
    filtros = models.JSONField(default=dict, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nome']

    def __str__(self):
        return self.nome
