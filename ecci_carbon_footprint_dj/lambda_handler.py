"""AWS Lambda entry point.

Serves Django behind CloudFront through a Lambda function URL, and runs
management commands when invoked directly:

    aws lambda invoke --function-name huella-staging \
        --cli-binary-format raw-in-base64-out \
        --payload '{"manage": ["migrate", "--noinput"]}' out.json
"""

import hmac
import io
import os
from contextlib import redirect_stderr, redirect_stdout

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecci_carbon_footprint_dj.settings')

from apig_wsgi import make_lambda_handler  # noqa: E402
from django.core.management import call_command  # noqa: E402
from django.core.wsgi import get_wsgi_application  # noqa: E402

application = get_wsgi_application()
_http_handler = make_lambda_handler(application, binary_support=True)

ORIGIN_SECRET = os.getenv('ORIGIN_VERIFY_SECRET', '')


def _forbidden():
    return {'statusCode': 403, 'headers': {'content-type': 'text/plain'}, 'body': 'Forbidden'}


def _run_management_command(event):
    # Variables extra para comandos como createsuperuser --noinput.
    os.environ.update({k: str(v) for k, v in event.get('env', {}).items()})
    output = io.StringIO()
    try:
        with redirect_stdout(output), redirect_stderr(output):
            call_command(*event['manage'])
    except Exception as exc:  # noqa: BLE001
        return {'ok': False, 'output': output.getvalue(), 'error': repr(exc)}
    finally:
        for key in event.get('env', {}):
            os.environ.pop(key, None)
    return {'ok': True, 'output': output.getvalue()}


def handler(event, context):
    if 'manage' in event:
        return _run_management_command(event)

    headers = event.get('headers') or {}

    # Solo CloudFront conoce el secreto: bloquea el acceso directo a la URL de la función.
    if ORIGIN_SECRET and not hmac.compare_digest(headers.get('x-origin-verify', ''), ORIGIN_SECRET):
        return _forbidden()

    # CloudFront envía el Host de la función; la función de CloudFront guarda el original aquí.
    forwarded_host = headers.get('x-forwarded-host')
    if forwarded_host:
        headers['host'] = forwarded_host

    return _http_handler(event, context)
