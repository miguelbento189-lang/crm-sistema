from django.contrib import admin

from .models import Historico, Lead, PipelineStage, SavedFilter


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('nome_razao', 'whatsapp', 'origem', 'estagio', 'valor', 'data_criacao')
    list_filter = ('estagio', 'origem', 'servico')
    search_fields = ('nome_razao', 'email', 'whatsapp', 'documento')


@admin.register(PipelineStage)
class PipelineStageAdmin(admin.ModelAdmin):
    list_display = ('nome', 'chave', 'ordem', 'criado_em')
    list_editable = ('ordem',)
    search_fields = ('nome', 'chave')


@admin.register(Historico)
class HistoricoAdmin(admin.ModelAdmin):
    list_display = ('lead', 'tipo', 'usuario', 'data')
    list_filter = ('tipo', 'data')
    search_fields = ('lead__nome_razao', 'usuario', 'nota')


@admin.register(SavedFilter)
class SavedFilterAdmin(admin.ModelAdmin):
    list_display = ('nome', 'usuario', 'criado_em')
    search_fields = ('nome', 'usuario__username')
