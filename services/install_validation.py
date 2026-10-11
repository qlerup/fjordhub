"""Validate administrator-supplied wizard values before any install side effect."""
import re
from pathlib import PurePosixPath, PureWindowsPath


_RESERVED = {'PATH', 'PYTHONPATH', 'LD_PRELOAD', 'LD_LIBRARY_PATH', 'COMPOSE_FILE',
             'COMPOSE_PROJECT_NAME', 'COMPOSE_PROFILES', 'COMPOSE_ENV_FILES',
             'DOCKER_HOST', 'DOCKER_CONTEXT', 'DOCKER_CONFIG', 'DOCKER_TLS_VERIFY',
             'DOCKER_CERT_PATH', 'FJORDHUB_API_KEY', 'FJORDHUB_URL', 'FJORDHUB_APP_ID'}
_SYSTEM_PATHS = ('/etc', '/proc', '/sys', '/dev', '/root', '/bin', '/sbin', '/usr',
                 '/boot', '/run', '/var/run', '/var/lib/docker')


def validate_install_values(definition, supplied):
    fields = {str(field.get('key')): field
              for step in definition.get('setup_steps', []) for field in step.get('fields', [])}
    if not isinstance(supplied, dict):
        raise ValueError('Installationsindstillinger skal være et objekt.')
    values = {}
    for key, value in supplied.items():
        if key not in fields or key in _RESERVED or not re.fullmatch('[A-Z][A-Z0-9_]*', key):
            raise ValueError('Installationsindstillinger indeholder et felt, som ikke er tilladt.')
        if not isinstance(value, (str, int, float, bool)) or any(c in str(value) for c in ('\r', '\n', '\x00')):
            raise ValueError('Installationsindstillinger skal være værdier på én linje.')
        values[key] = str(value)
    for key, field in fields.items():
        if field.get('type') != 'path':
            continue
        value = str(values.get(key, field.get('default', ''))).strip()
        if not value:
            continue
        normalized = value.replace('\\', '/')
        path = PurePosixPath(normalized)
        windows = PureWindowsPath(value)
        if normalized.startswith('//') or '..' in path.parts or ',' in value or '$' in value:
            raise ValueError('Vælg en absolut datamappe uden relative led eller miljøvariabler.')
        if windows.drive:
            if not windows.is_absolute() or len(windows.parts) < 2 or ':' in value[2:] or windows.parts[1].lower() in {'windows', 'program files', 'program files (x86)'}:
                raise ValueError('Vælg en datamappe, ikke en systemmappe eller diskrod.')
        elif not path.is_absolute() or str(path) == '/' or ':' in value or any(str(path) == root or str(path).startswith(root + '/') for root in _SYSTEM_PATHS):
            raise ValueError('Vælg en absolut datamappe uden for systemmapperne.')
    return values
