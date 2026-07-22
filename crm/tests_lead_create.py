from decimal import Decimal
import json

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from crm.models import Historico, Lead, PipelineStage


class LeadCreateViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='cadastro_lead', password='senha123')
        PipelineStage.bootstrap_defaults()

    def test_post_lead_form_creates_lead_without_obsolete_field(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('crm:cadastrar_lead'),
            {
                'nome': 'Lead Cadastro Teste',
                'whatsapp': '34999999999',
                'email': 'lead@example.com',
                'servico': 'solar',
                'origem': 'site',
                'valor': '2500,00',
                'descricao': 'Lead criado via teste.',
            },
        )

        self.assertEqual(response.status_code, 302)
        lead = Lead.objects.get(nome_razao='Lead Cadastro Teste')
        self.assertEqual(lead.email, 'lead@example.com')
        self.assertEqual(lead.valor, Decimal('2500.00'))
        self.assertEqual(lead.servico, 'solar')
        self.assertEqual(lead.estagio, PipelineStage.first_stage_key())
        self.assertTrue(Historico.objects.filter(lead=lead, nota='Lead cadastrado no sistema.').exists())

    def test_post_lead_form_ignores_removed_legacy_service_categories(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('crm:cadastrar_lead'),
            {
                'nome': 'Lead Categoria Antiga',
                'whatsapp': '34999999999',
                'servico': 'eletrica',
                'origem': 'site',
            },
        )

        self.assertEqual(response.status_code, 302)
        lead = Lead.objects.get(nome_razao='Lead Categoria Antiga')
        self.assertEqual(lead.servico, 'solar')

    def test_create_stage_api_creates_new_pipeline_column(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('crm:api_criar_estagio'),
            data='{"nome": "Aguardando retorno"}',
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(PipelineStage.objects.filter(nome='Aguardando retorno').exists())

    def test_create_stage_api_requires_csrf_token(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.user)

        response = csrf_client.post(
            reverse('crm:api_criar_estagio'),
            data='{"nome": "Sem token"}',
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(PipelineStage.objects.filter(nome='Sem token').exists())

    def test_rename_stage_api_updates_stage_name(self):
        self.client.force_login(self.user)
        stage = PipelineStage.objects.get(chave='contactar')

        response = self.client.post(
            reverse('crm:api_renomear_estagio'),
            data='{"stage_key": "contactar", "nome": "Primeiro contato"}',
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        stage.refresh_from_db()
        self.assertEqual(stage.nome, 'Primeiro contato')

    def test_delete_stage_api_moves_leads_and_removes_stage(self):
        self.client.force_login(self.user)
        lead = Lead.objects.create(
            nome_razao='Lead em etapa removida',
            estagio='contactar',
            origem='site',
            servico='solar',
        )

        response = self.client.post(
            reverse('crm:api_excluir_estagio'),
            data='{"stage_key": "contactar", "destination_stage_key": "enviar"}',
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        lead.refresh_from_db()
        self.assertEqual(lead.estagio, 'enviar')
        self.assertFalse(PipelineStage.objects.filter(chave='contactar').exists())
        self.assertTrue(
            Historico.objects.filter(
                lead=lead,
                tipo='movimentacao',
                nota="Etapa 'A contactar' removida; lead realocado para 'Enviar proposta'.",
            ).exists()
        )

    def test_post_lead_form_without_name_returns_form_error(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse('crm:cadastrar_lead'), {'email': 'lead@example.com'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Informe o nome ou razão social do lead.')

    def test_public_lead_api_creates_lead_for_landing(self):
        response = self.client.post(
            reverse('crm:api_public_create_lead'),
            {
                'full_name': 'Miguel Bento',
                'company': 'Forca Engenharia',
                'whatsapp': '64999999999',
                'interest_service': 'spda',
                'lead_source': 'site',
                'page_url': 'https://laudos.forcaeng.com.br/',
                'referrer': 'google',
                'utm_campaign': 'campanha-laudos',
            },
            HTTP_ORIGIN='https://laudos.forcaeng.com.br',
        )

        self.assertEqual(response.status_code, 201)
        payload = json.loads(response.content)
        lead = Lead.objects.get(id=payload['lead_id'])
        self.assertEqual(lead.nome_razao, 'Forca Engenharia')
        self.assertEqual(lead.whatsapp, '64999999999')
        self.assertEqual(lead.servico, 'spda')
        self.assertEqual(lead.origem, 'site')
        self.assertEqual(lead.page_url, 'https://laudos.forcaeng.com.br/')
        self.assertEqual(lead.referrer, 'google')
        self.assertEqual(lead.utm_campaign, 'campanha-laudos')
        self.assertIn('Contato: Miguel Bento', lead.observacoes)
        self.assertEqual(response['Access-Control-Allow-Origin'], 'https://laudos.forcaeng.com.br')

    def test_public_lead_api_rejects_missing_name_and_company(self):
        response = self.client.post(reverse('crm:api_public_create_lead'), {'whatsapp': '64999999999'})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Lead.objects.count(), 0)