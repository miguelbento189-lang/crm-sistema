# Copilot instructions for Portfolio CRM

This file gives targeted, actionable guidance for AI coding agents working in this repository.

1) Project overview
- **Type:** Django 5 monorepo web app (project root uses `manage.py`). See [manage.py](manage.py#L1-L20).
- **Apps:** primary app is `crm` (business logic, templates, integrations). App templates live under `crm/templates/crm` and shared templates under [templates](templates).
- **Key services:** external catalog integration at [crm/integrations/edeltec.py](crm/integrations/edeltec.py#L1-L40); business engines under `services/` and `crm/services/` (example: [crm/services/kpi_engine.py](crm/services/kpi_engine.py#L1-L40)).

2) Important configuration & conventions
- **Settings:** main config is [core/settings.py](core/settings.py#L1-L80). Note: `cloudinary_storage` must be listed before admin/static apps (project relies on that ordering).
- **Storage & media:** Cloudinary is configured in `core/settings.py` (CLOUDINARY_STORAGE + `DEFAULT_FILE_STORAGE`) — credentials are present in the file; prefer environment variables via `python-decouple` in future changes.
- **Database:** uses `dj_database_url` and expects `DATABASE_URL` / Neon defaults in `core/settings.py`.
- **Static files:** `whitenoise.storage.CompressedManifestStaticFilesStorage` is used; run `collectstatic` before deployments.
- **PWA:** service worker is at `static/js/serviceworker.js` and configured in settings (`PWA_SERVICE_WORKER_PATH`).

3) Developer workflows (commands)
- Install deps: `pip install -r requirements.txt` ([requirements.txt](requirements.txt#L1-L20)).
- Local dev: `python manage.py migrate` then `python manage.py runserver` ([manage.py](manage.py#L1-L20)).
- Collect static for production: `python manage.py collectstatic --noinput` (because settings use Manifest/Whitenoise storage).
- Shell for quick DB/ORM checks: `python manage.py shell`.

4) Patterns & project-specific guidance
- **App structure:** Business logic lives in `crm` (models, views, templates). Prefer adding new domain code as service classes under `crm/services/` or top-level `services/` rather than sprawling utility modules.
- **Integrations:** External API clients (example: Edeltec) are plain Python clients with synchronous `requests` calls and internal mapping/normalization logic. See [crm/integrations/edeltec.py](crm/integrations/edeltec.py#L1-L200) for how pagination, auth, stock rules, and category mapping are handled. Follow the same pattern for new integrations (client class + _process methods + defensive timeouts).
- **Business rules:** Encapsulate domain logic in service classes (see `KPIEngine` in [crm/services/kpi_engine.py](crm/services/kpi_engine.py#L1-L200)). Use Django ORM queries inside these classes and return serializable dicts for views/templates.
- **Templates & static:** Templates use app-level organization `crm/templates/crm/*.html`. Static assets live in `static/` and are referenced as usual via `{% static %}`.

5) Safety, secrets, and missing artifacts
- The repository contains hard-coded Cloudinary and DB connection strings in `core/settings.py`. Treat these as secrets: avoid echoing them in commits or logs. When modifying settings prefer `python-decouple` environment variables.
- README.md is empty — do not assume it contains setup docs; use the commands above as canonical.

6) What to look for when editing
- Respect installed app ordering in `core/settings.py` when adding storage/admin-related apps.
- If you change static/media behavior, validate `collectstatic` and local file serving with `runserver` + `whitenoise`.
- When adding integrations, add unit-friendly boundaries (small pure functions) to make offline testing possible (current clients use `requests` directly).

7) Quick references
- Settings: [core/settings.py](core/settings.py#L1-L120)
- Integrations example: [crm/integrations/edeltec.py](crm/integrations/edeltec.py#L1-L200)
- Business engine example: [crm/services/kpi_engine.py](crm/services/kpi_engine.py#L1-L200)
- Entrypoint: [manage.py](manage.py#L1-L20)
- Dependencies: [requirements.txt](requirements.txt#L1-L30)

If anything above is unclear or you'd like additional examples (unit tests, a sample migration, or a small README section), tell me which area to expand.
