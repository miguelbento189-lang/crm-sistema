from django.shortcuts import redirect
from django.urls import path

from . import views


app_name = 'crm'


def redirect_system_home(request):
    if request.user.is_authenticated:
        return redirect('crm:crm_dashboard')
    return redirect('product_login')


urlpatterns = [
    path('', redirect_system_home, name='system_home'),
    path('crm/pipeline/', views.crm_dashboard_view, name='crm_dashboard'),
    path('crm/api/mover-lead/', views.api_mover_lead, name='api_mover_lead'),
    path('crm/api/criar-estagio/', views.api_criar_estagio, name='api_criar_estagio'),
    path('crm/api/reordenar-estagios/', views.api_reordenar_estagios, name='api_reordenar_estagios'),
    path('crm/api/renomear-estagio/', views.api_renomear_estagio, name='api_renomear_estagio'),
    path('crm/api/excluir-estagio/', views.api_excluir_estagio, name='api_excluir_estagio'),
    path('crm/lead/novo/', views.cadastrar_lead_view, name='cadastrar_lead'),
    path('crm/lead/<int:lead_id>/', views.lead_detail_view, name='lead_detail'),
    path('crm/lead/<int:lead_id>/deletar/', views.excluir_lead_view, name='deletar_lead'),
]
