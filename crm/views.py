import json
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Max, Prefetch, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt

from .models import Historico, Lead, PipelineStage


PUBLIC_LEAD_ALLOWED_ORIGINS = {
    'https://laudos.forcaeng.com.br',
    'https://www.laudos.forcaeng.com.br',
    'https://forcaeng.com.br',
    'https://www.forcaeng.com.br',
    'http://127.0.0.1:5500',
    'http://localhost:5500',
}


def is_public_lead_origin_allowed(origin):
    if not origin:
        return False

    normalized_origin = origin.rstrip('/')
    if normalized_origin in PUBLIC_LEAD_ALLOWED_ORIGINS:
        return True

    if normalized_origin.startswith('https://') and normalized_origin.endswith('.forcaeng.com.br'):
        return True

    if normalized_origin.startswith('http://localhost') or normalized_origin.startswith('http://127.0.0.1'):
        return True

    return False


def parse_money_br(raw_value):
    value = (raw_value or '').strip()
    if not value:
        return Decimal('0')
    normalized = value.replace('.', '').replace(',', '.')
    try:
        return Decimal(normalized)
    except Exception:
        return Decimal('0')


def ensure_pipeline_stages():
    PipelineStage.bootstrap_defaults()


def build_lead_observations(*, contact_name, company, email, description, documento, endereco, numero, bairro, cidade, estado, cep, page_url, referrer, utm_data):
    notes = []
    if contact_name:
        notes.append(f'Contato: {contact_name}')
    if company:
        notes.append(f'Empresa: {company}')
    if email:
        notes.append(f'E-mail: {email}')
    if documento:
        notes.append(f'Documento: {documento}')
    if description:
        notes.append(f'Descricao: {description}')
    address_parts = [part for part in [endereco, numero, bairro, cidade, estado, cep] if part]
    if address_parts:
        notes.append(f'Endereco: {" | ".join(address_parts)}')
    if page_url:
        notes.append(f'Pagina: {page_url}')
    if referrer:
        notes.append(f'Referrer: {referrer}')

    for label, value in utm_data:
        if value:
            notes.append(f'{label}: {value}')

    return '\n'.join(notes)


def map_service_choice(raw_service):
    service = (raw_service or '').strip().lower()
    service_map = {
        'spda': 'spda',
        'laudo de spda': 'spda',
        'eletrico': 'eletrico',
        'elétrico': 'eletrico',
        'laudo de instalacoes eletricas': 'eletrico',
        'laudo de instalações elétricas': 'eletrico',
        'ambos': 'ambos',
        'spda e instalacoes eletricas': 'ambos',
        'spda e instalações elétricas': 'ambos',
        'orcamento': 'orcamento',
        'orçamento': 'orcamento',
        'solicitar orçamento': 'orcamento',
        'solar': 'solar',
        'climatizacao': 'climatizacao',
    }
    return service_map.get(service, 'solar')


def create_lead_from_payload(payload, *, actor='site'):
    ensure_pipeline_stages()

    contact_name = (payload.get('full_name') or payload.get('name') or '').strip()
    company = (payload.get('company') or '').strip()
    lead_source = (payload.get('lead_source') or '').strip()
    raw_service = (payload.get('interest_service') or payload.get('service') or payload.get('servico') or '').strip()
    email = (payload.get('email') or '').strip()
    documento = (payload.get('documento') or '').strip()
    cep = (payload.get('cep') or '').strip()
    endereco = (payload.get('endereco') or '').strip()
    numero = (payload.get('numero') or '').strip()
    bairro = (payload.get('bairro') or '').strip()
    cidade = (payload.get('cidade') or '').strip()
    estado = (payload.get('estado') or '').strip()
    nome_razao = company or contact_name
    if not nome_razao:
        raise ValueError('Informe pelo menos o nome do contato ou da empresa.')

    utm_data = [
        ('utm_source', (payload.get('utm_source') or '').strip()),
        ('utm_medium', (payload.get('utm_medium') or '').strip()),
        ('utm_campaign', (payload.get('utm_campaign') or '').strip()),
        ('utm_term', (payload.get('utm_term') or '').strip()),
        ('utm_content', (payload.get('utm_content') or '').strip()),
    ]
    origem = (payload.get('origem') or payload.get('lead_source') or 'site').strip().lower()
    if origem not in {choice[0] for choice in Lead.ORIGEM_CHOICES}:
        origem = 'site'

    lead = Lead.objects.create(
        nome_razao=nome_razao,
        nome_contato=contact_name,
        empresa=company,
        whatsapp=(payload.get('whatsapp') or '').strip(),
        email=email,
        documento=documento,
        cep=cep,
        endereco=endereco,
        numero=numero,
        bairro=bairro,
        cidade=cidade,
        estado=estado,
        servico=map_service_choice(raw_service),
        servico_interesse=raw_service,
        origem=origem,
        page_url=(payload.get('page_url') or '').strip(),
        referrer=(payload.get('referrer') or '').strip(),
        utm_source=(payload.get('utm_source') or '').strip(),
        utm_medium=(payload.get('utm_medium') or '').strip(),
        utm_campaign=(payload.get('utm_campaign') or '').strip(),
        utm_term=(payload.get('utm_term') or '').strip(),
        utm_content=(payload.get('utm_content') or '').strip(),
        lead_source=lead_source,
        valor=parse_money_br(payload.get('valor')),
        observacoes=build_lead_observations(
            contact_name=contact_name,
            company=company,
            email=email,
            description=(payload.get('description') or payload.get('descricao') or '').strip(),
            documento=documento,
            endereco=endereco,
            numero=numero,
            bairro=bairro,
            cidade=cidade,
            estado=estado,
            cep=cep,
            page_url=(payload.get('page_url') or '').strip(),
            referrer=(payload.get('referrer') or '').strip(),
            utm_data=utm_data,
        ),
        estagio=PipelineStage.first_stage_key(),
    )
    Historico.objects.create(
        lead=lead,
        usuario=actor,
        tipo='nota',
        nota='Lead cadastrado via site/landing page.',
    )
    return lead


def add_public_cors_headers(request, response):
    origin = (request.headers.get('Origin') or '').rstrip('/')
    if is_public_lead_origin_allowed(origin):
        response['Access-Control-Allow-Origin'] = origin
        response['Vary'] = 'Origin'
    response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
    response['Access-Control-Allow-Headers'] = 'Content-Type'
    return response


@login_required
def crm_dashboard_view(request):
    ensure_pipeline_stages()
    etapas_pipeline = list(PipelineStage.objects.order_by('ordem', 'id'))
    historicos_prefetch = Prefetch(
        'historicos',
        queryset=Historico.objects.only('lead_id', 'data', 'tipo', 'nota').order_by('-data'),
        to_attr='historicos_preview',
    )

    estagios_data = []
    for etapa in etapas_pipeline:
        leads_queryset = Lead.objects.filter(estagio=etapa.chave)
        leads_no_estagio = leads_queryset.prefetch_related(historicos_prefetch).order_by('-data_criacao')
        total_valor = leads_queryset.aggregate(total=Sum('valor'))['total'] or Decimal('0')
        estagios_data.append(
            {
                'chave': etapa.chave,
                'nome': etapa.nome,
                'qtd': leads_no_estagio.count(),
                'valor_total': total_valor,
                'leads': leads_no_estagio,
            }
        )

    negotiation_keys = [etapa.chave for etapa in etapas_pipeline if etapa.chave in {'negociacao', 'enviar', 'credito'}]
    if not negotiation_keys:
        negotiation_keys = [
            etapa.chave
            for etapa in etapas_pipeline
            if etapa.chave not in {'perdido', 'aprovada'}
        ][:3]

    q_instagram = Lead.objects.filter(origem='instagram').count()
    q_site = Lead.objects.filter(origem='site').count()
    q_indicacao = Lead.objects.filter(origem='indicacao').count()
    q_outros = Lead.objects.exclude(origem__in=['instagram', 'site', 'indicacao']).count()

    context = {
        'estagios': estagios_data,
        'etapas_pipeline': etapas_pipeline,
        'kpi_total_ativos': Lead.objects.exclude(estagio='perdido').count(),
        'kpi_valor_negociacao': Lead.objects.filter(estagio__in=negotiation_keys).aggregate(total=Sum('valor'))['total'] or Decimal('0'),
        'donut_series': json.dumps([q_site, q_instagram, q_indicacao, q_outros]),
        'donut_labels': json.dumps(['Site', 'Instagram', 'Indicacao', 'Outros']),
    }
    return render(request, 'crm/crm_dashboard.html', context)


@login_required
def api_mover_lead(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error'}, status=400)

    try:
        ensure_pipeline_stages()
        data = json.loads(request.body)
        lead = Lead.objects.get(id=data.get('lead_id'))
        antigo_estagio = lead.estagio
        novo_estagio = (data.get('novo_estagio') or '').strip()
        if not PipelineStage.objects.filter(chave=novo_estagio).exists():
            raise ValueError('Etapa de destino invalida.')
        lead.estagio = novo_estagio
        lead.save(update_fields=['estagio'])
        Historico.objects.create(
            lead=lead,
            usuario=request.user.username,
            tipo='movimentacao',
            nota=f"Moveu de '{PipelineStage.label_for_key(antigo_estagio)}' para '{PipelineStage.label_for_key(lead.estagio)}'",
        )
        return JsonResponse({'status': 'ok'})
    except Exception as exc:
        return JsonResponse({'status': 'error', 'message': str(exc)}, status=400)


@login_required
def api_criar_estagio(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error'}, status=400)

    try:
        ensure_pipeline_stages()
        data = json.loads(request.body)
        nome = (data.get('nome') or '').strip()
        if len(nome) < 3:
            raise ValueError('Informe um nome com pelo menos 3 caracteres.')

        stage = PipelineStage(
            nome=nome,
            ordem=(PipelineStage.objects.aggregate(max_ordem=Max('ordem'))['max_ordem'] or 0) + 1,
        )
        stage.save()
        return JsonResponse(
            {
                'status': 'ok',
                'stage': {
                    'chave': stage.chave,
                    'nome': stage.nome,
                    'ordem': stage.ordem,
                },
            }
        )
    except Exception as exc:
        return JsonResponse({'status': 'error', 'message': str(exc)}, status=400)


@login_required
def api_reordenar_estagios(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error'}, status=400)

    try:
        ensure_pipeline_stages()
        data = json.loads(request.body)
        ordered_keys = data.get('stage_keys') or []
        if not ordered_keys:
            raise ValueError('Nenhuma etapa enviada para ordenação.')

        stages = {stage.chave: stage for stage in PipelineStage.objects.filter(chave__in=ordered_keys)}
        if len(stages) != len(ordered_keys):
            raise ValueError('A ordenação contém etapas inválidas.')

        updated_stages = []
        with transaction.atomic():
            for index, key in enumerate(ordered_keys, start=1):
                stage = stages[key]
                if stage.ordem != index:
                    stage.ordem = index
                    updated_stages.append(stage)

            if updated_stages:
                PipelineStage.objects.bulk_update(updated_stages, ['ordem'])

        return JsonResponse({'status': 'ok'})
    except Exception as exc:
        return JsonResponse({'status': 'error', 'message': str(exc)}, status=400)


@login_required
def api_renomear_estagio(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error'}, status=400)

    try:
        ensure_pipeline_stages()
        data = json.loads(request.body)
        chave = (data.get('stage_key') or '').strip()
        nome = (data.get('nome') or '').strip()
        if len(nome) < 3:
            raise ValueError('Informe um novo nome com pelo menos 3 caracteres.')

        stage = get_object_or_404(PipelineStage, chave=chave)
        stage.nome = nome
        stage.save(update_fields=['nome'])
        return JsonResponse({'status': 'ok', 'stage': {'chave': stage.chave, 'nome': stage.nome}})
    except Exception as exc:
        return JsonResponse({'status': 'error', 'message': str(exc)}, status=400)


@login_required
def api_excluir_estagio(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error'}, status=400)

    try:
        ensure_pipeline_stages()
        data = json.loads(request.body)
        stage_key = (data.get('stage_key') or '').strip()
        destination_key = (data.get('destination_stage_key') or '').strip()

        stage = get_object_or_404(PipelineStage, chave=stage_key)
        all_stages = list(PipelineStage.objects.order_by('ordem', 'id'))
        if len(all_stages) <= 1:
            raise ValueError('Não é possível excluir a última etapa da pipeline.')

        if not destination_key:
            raise ValueError('Selecione a etapa de destino para realocar os leads.')

        if destination_key == stage_key:
            raise ValueError('A etapa de destino precisa ser diferente da etapa removida.')

        destination_stage = get_object_or_404(PipelineStage, chave=destination_key)
        lead_ids = list(Lead.objects.filter(estagio=stage.chave).values_list('id', flat=True))

        with transaction.atomic():
            if lead_ids:
                Lead.objects.filter(id__in=lead_ids).update(estagio=destination_stage.chave)
                Historico.objects.bulk_create(
                    [
                        Historico(
                            lead_id=lead_id,
                            usuario=request.user.username,
                            tipo='movimentacao',
                            nota=f"Etapa '{stage.nome}' removida; lead realocado para '{destination_stage.nome}'.",
                        )
                        for lead_id in lead_ids
                    ]
                )

            stage.delete()

            remaining_stages = list(PipelineStage.objects.order_by('ordem', 'id'))
            for index, remaining_stage in enumerate(remaining_stages, start=1):
                remaining_stage.ordem = index
            PipelineStage.objects.bulk_update(remaining_stages, ['ordem'])

        return JsonResponse(
            {
                'status': 'ok',
                'moved_leads': len(lead_ids),
                'destination_stage_name': destination_stage.nome,
            }
        )
    except Exception as exc:
        return JsonResponse({'status': 'error', 'message': str(exc)}, status=400)


@login_required
def cadastrar_lead_view(request):
    ensure_pipeline_stages()
    if request.method == 'POST':
        data = request.POST
        nome_razao = (data.get('nome') or data.get('nome_razao') or '').strip()
        servico = map_service_choice(data.get('servico') or 'solar')

        if not nome_razao:
            messages.error(request, 'Informe o nome ou razão social do lead.')
            return render(request, 'crm/lead_form.html', {'form_data': data})

        lead = Lead.objects.create(
            nome_razao=nome_razao,
            nome_contato=(data.get('nome_contato') or '').strip(),
            empresa=(data.get('empresa') or '').strip(),
            whatsapp=(data.get('whatsapp') or '').strip(),
            email=(data.get('email') or '').strip(),
            documento=(data.get('documento') or '').strip(),
            cep=(data.get('cep') or '').strip(),
            endereco=(data.get('endereco') or '').strip(),
            numero=(data.get('numero') or '').strip(),
            bairro=(data.get('bairro') or '').strip(),
            cidade=(data.get('cidade') or '').strip(),
            estado=(data.get('estado') or '').strip(),
            servico=servico,
            origem=(data.get('origem') or 'site').strip(),
            page_url=(data.get('page_url') or '').strip(),
            referrer=(data.get('referrer') or '').strip(),
            utm_source=(data.get('utm_source') or '').strip(),
            utm_medium=(data.get('utm_medium') or '').strip(),
            utm_campaign=(data.get('utm_campaign') or '').strip(),
            utm_term=(data.get('utm_term') or '').strip(),
            utm_content=(data.get('utm_content') or '').strip(),
            lead_source=(data.get('lead_source') or '').strip(),
            servico_interesse=(data.get('servico_interesse') or data.get('service') or '').strip(),
            valor=parse_money_br(data.get('valor')),
            observacoes=(data.get('descricao') or '').strip(),
            estagio=PipelineStage.first_stage_key(),
        )
        Historico.objects.create(
            lead=lead,
            usuario=request.user.username,
            tipo='nota',
            nota='Lead cadastrado no sistema.',
        )
        messages.success(request, 'Lead cadastrado com sucesso.')
        return redirect('crm:crm_dashboard')

    return render(request, 'crm/lead_form.html')


@csrf_exempt
def api_public_create_lead(request):
    if request.method == 'OPTIONS':
        return add_public_cors_headers(request, JsonResponse({'status': 'ok'}))

    if request.method != 'POST':
        return add_public_cors_headers(request, JsonResponse({'status': 'error', 'message': 'Metodo nao permitido.'}, status=405))

    try:
        if request.content_type and 'application/json' in request.content_type:
            payload = json.loads(request.body or '{}')
        else:
            payload = request.POST

        lead = create_lead_from_payload(payload, actor='landing-page')
        return add_public_cors_headers(
            request,
            JsonResponse({'status': 'ok', 'lead_id': lead.id, 'stage': lead.estagio}, status=201),
        )
    except ValueError as exc:
        return add_public_cors_headers(request, JsonResponse({'status': 'error', 'message': str(exc)}, status=400))
    except Exception:
        return add_public_cors_headers(
            request,
            JsonResponse({'status': 'error', 'message': 'Falha ao cadastrar lead.'}, status=500),
        )


@login_required
def lead_detail_view(request, lead_id):
    ensure_pipeline_stages()
    lead = get_object_or_404(Lead, id=lead_id)

    if request.method == 'POST':
        nota = (request.POST.get('nota') or '').strip()
        tipo = (request.POST.get('tipo') or 'nota').strip()
        if nota:
            Historico.objects.create(
                lead=lead,
                usuario=request.user.username,
                tipo=tipo,
                nota=nota,
            )
            messages.success(request, 'Atividade registrada com sucesso.')
        return redirect('crm:lead_detail', lead_id=lead.id)

    return render(
        request,
        'crm/lead_detail.html',
        {
            'lead': lead,
            'historico': lead.historicos.order_by('-data'),
        },
    )


@login_required
def excluir_lead_view(request, lead_id):
    lead = get_object_or_404(Lead, id=lead_id)
    if request.method == 'POST':
        lead.delete()
        messages.success(request, 'Lead removido com sucesso.')
    return redirect('crm:crm_dashboard')
