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

Para validar localmente antes do deploy, rode `python manage.py check` e `python manage.py collectstatic --noinput`.
