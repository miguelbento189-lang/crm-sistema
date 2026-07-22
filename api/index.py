import json
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


def load_bootstrap_users():
	raw_value = os.environ.get('BOOTSTRAP_USERS_JSON', '').strip()
	if not raw_value:
		return []
	try:
		parsed = json.loads(raw_value)
	except json.JSONDecodeError:
		return []
	if not isinstance(parsed, list):
		return []
	users = []
	for item in parsed:
		if not isinstance(item, dict):
			continue
		username = str(item.get('username', '')).strip()
		password = str(item.get('password', '')).strip()
		if not username or not password:
			continue
		users.append({
			'username': username,
			'password': password,
			'is_staff': bool(item.get('is_staff', False)),
			'is_superuser': bool(item.get('is_superuser', False)),
		})
	return users


def ensure_bootstrap_users():
	users_to_create = load_bootstrap_users()
	if not users_to_create:
		return
	from django.contrib.auth import get_user_model

	user_model = get_user_model()
	for user_data in users_to_create:
		user, _ = user_model.objects.get_or_create(username=user_data['username'])
		user.is_staff = user_data['is_staff']
		user.is_superuser = user_data['is_superuser']
		user.is_active = True
		user.set_password(user_data['password'])
		user.save()


def ensure_sqlite_schema():
	marker_path = '/tmp/.django_migrated'
	if os.path.exists(marker_path):
		return
	django.setup()
	call_command('migrate', interactive=False, run_syncdb=True, verbosity=0)
	ensure_bootstrap_users()
	with open(marker_path, 'w', encoding='utf-8') as marker_file:
		marker_file.write('ok')


if should_bootstrap_sqlite():
	ensure_sqlite_schema()

app = get_wsgi_application()