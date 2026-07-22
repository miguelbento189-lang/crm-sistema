import os

import django
from django.core.management import call_command
from django.core.wsgi import get_wsgi_application


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')


def should_bootstrap_sqlite():
	return (
		not os.environ.get('DATABASE_URL')
		and any(
			os.environ.get(name)
			for name in ('VERCEL_URL', 'VERCEL_ENV', 'VERCEL')
		)
	)


def ensure_sqlite_schema():
	marker_path = '/tmp/.django_migrated'
	if os.path.exists(marker_path):
		return
	django.setup()
	call_command('migrate', interactive=False, run_syncdb=True, verbosity=0)
	with open(marker_path, 'w', encoding='utf-8') as marker_file:
		marker_file.write('ok')


if should_bootstrap_sqlite():
	ensure_sqlite_schema()

app = get_wsgi_application()