## CRM Sistema

Aplicacao Django para gestao comercial com pipeline em colunas, cadastro de leads e historico de atividades.

## Stack

- Django 5
- SQLite para uso local
- Render para deploy
- Cloudinary para arquivos estaticos e media

## Rodando localmente

1. Crie um ambiente virtual.
2. Instale as dependencias com `pip install -r requirements.txt`.
3. Copie `.env.example` para `.env` e ajuste as variaveis necessarias.
4. Rode `python manage.py migrate`.
5. Rode `python manage.py runserver`.

## Variaveis de ambiente

Use `.env.example` como base. As variaveis principais sao:

- `SECRET_KEY`
- `DEBUG`
- `DATABASE_URL`
- `ALLOWED_HOSTS`
- `CSRF_TRUSTED_ORIGINS`
- `CLOUDINARY_STORAGE_CLOUD_NAME`
- `CLOUDINARY_STORAGE_API_KEY`
- `CLOUDINARY_STORAGE_API_SECRET`

## Testes

Use `python manage.py test crm.tests_lead_create` para rodar a suite focada atual.

## Publicacao

O projeto esta preparado para subir em um repositorio GitHub separado deste diretorio. O arquivo `.env` continua ignorado e nao deve ser versionado.

Host de producao esperado:

- `crm.forcaeng.com.br`

Endpoint publico esperado para captura da landing:

- `https://crm.forcaeng.com.br/sistema/crm/api/public/leads/`

## Deploy estilo Vercel

O repositorio agora inclui arquivos para deploy serverless:

- `vercel.json`
- `build_files.sh`
- `.env.vercel.example`

Pontos importantes para esse tipo de deploy:

- nao use SQLite em producao
- configure `DATABASE_URL` para Postgres ou outro banco gerenciado
- configure `SECRET_KEY`, `ALLOWED_HOSTS` e `CSRF_TRUSTED_ORIGINS`
- se usar upload de arquivos, configure Cloudinary
- o host dinamico de preview da Vercel pode ser aceito via `VERCEL_URL`

Fluxo sugerido:

1. copie `.env.vercel.example` como base para as variaveis do projeto na plataforma
2. conecte o repositorio no provedor
3. use `python manage.py migrate` em um passo de post-deploy ou migration job
4. publique a branch `main`

## Checklist de deploy para o subdominio

1. aponte `crm.forcaeng.com.br` para o provedor escolhido
2. configure `ALLOWED_HOSTS=crm.forcaeng.com.br`
3. configure `CSRF_TRUSTED_ORIGINS=https://crm.forcaeng.com.br`
4. publique a branch `main`
5. rode as migracoes antes de validar o endpoint publico

## Deploy no Vercel (gratuito)

1. Entre no painel da Vercel e clique em Add New > Project.
2. Importe o repositorio do CRM: miguelbento189-lang/crm-sistema.
3. Em Build and Output Settings, mantenha as configuracoes do repositorio (o arquivo vercel.json ja esta preparado).
4. Em Environment Variables, configure no ambiente Production:
	- DJANGO_SETTINGS_MODULE=core.settings
	- DEBUG=False
	- SECRET_KEY=(valor forte)
	- USE_SQLITE=False
	- DATABASE_URL=(Postgres gerenciado)
	- BOOTSTRAP_USERS_JSON=(opcional apenas para fallback SQLite temporario)
	- ALLOWED_HOSTS=crm.forcaeng.com.br
	- CSRF_TRUSTED_ORIGINS=https://crm.forcaeng.com.br
	- VERCEL_URL=(deixe vazio; a Vercel injeta automaticamente)
	- USE_X_FORWARDED_HOST=True
	- SECURE_SSL_REDIRECT=True
	- SESSION_COOKIE_SECURE=True
	- CSRF_COOKIE_SECURE=True
	- DISABLE_STATIC_MANIFEST=True
5. Clique em Deploy.

Se estiver usando o fallback temporario com SQLite no Vercel, defina `BOOTSTRAP_USERS_JSON` com um array JSON de usuarios para recria-los a cada inicializacao, por exemplo `[{"username":"Miguel","password":"senha-forte"},{"username":"Rael","password":"outra-senha"}]`.

### Dominio crm.forcaeng.com.br

1. No projeto da Vercel, abra Settings > Domains.
2. Adicione crm.forcaeng.com.br.
3. A Vercel vai pedir um registro DNS tipo CNAME.
4. No DNS (Hostinger), remova o A record atual de crm (45.132.157.183) e crie:
	- Tipo: CNAME
	- Host: crm
	- Valor: cname.vercel-dns.com
5. Aguarde propagacao e valide a raiz:
	- https://crm.forcaeng.com.br/

### Validacao da integracao com landing

Depois do dominio ativo no Vercel, valide:

1. Endpoint publico:
	- https://crm.forcaeng.com.br/sistema/crm/api/public/leads/
2. Envio real pelo formulario da landing.
3. Entrada do lead no pipeline do CRM com origem/campanha/utm.

Para validar localmente antes do deploy, rode `python manage.py check` e `python manage.py collectstatic --noinput`.
