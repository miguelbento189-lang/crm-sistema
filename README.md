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
