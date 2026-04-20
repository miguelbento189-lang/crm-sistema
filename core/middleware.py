import os
import traceback
from pathlib import Path


class TunnelExceptionLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.enabled = os.getenv('LOG_TUNNEL_EXCEPTIONS', '').lower() in {'1', 'true', 'yes', 'on'}
        self.log_path = Path(__file__).resolve().parent.parent / 'logs' / 'tunnel-exceptions.log'

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if not self.enabled:
            return None

        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        forwarded_headers = {
            key: value
            for key, value in request.META.items()
            if key.startswith('HTTP_') or key in {'REMOTE_ADDR', 'SERVER_NAME', 'SERVER_PORT'}
        }

        with self.log_path.open('a', encoding='utf-8') as log_file:
            log_file.write('\n' + '=' * 80 + '\n')
            log_file.write(f'PATH: {request.path}\n')
            log_file.write(f'METHOD: {request.method}\n')
            log_file.write(f'EXCEPTION: {exception.__class__.__name__}: {exception}\n')
            log_file.write('HEADERS:\n')
            for key in sorted(forwarded_headers):
                log_file.write(f'  {key}: {forwarded_headers[key]}\n')
            log_file.write('TRACEBACK:\n')
            log_file.write(traceback.format_exc())

        return None