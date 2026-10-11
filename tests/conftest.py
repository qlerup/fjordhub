"""Isolated application boot and browser-like CSRF handling for route tests."""
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from flask.testing import FlaskClient
from werkzeug.datastructures import Headers

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
_data = tempfile.TemporaryDirectory(prefix='fjordhub-tests-')
os.environ.update(DATA_DIR=_data.name, APPS_DIR=str(Path(_data.name) / 'apps'),
                  FJORDHUB_SRC_DIR='', FJORDHUB_MEMORY_RECONCILE='0',
                  FJORDHUB_PUBLIC_URL='', FJORDHUB_TRUSTED_PROXIES='',
                  SECRET_KEY='synthetic-pytest-session-key-not-production')
from services.remote_registry import RemoteRegistry
from services.package_catalog import PackageCatalog

with patch.object(RemoteRegistry, '_start_background_refresh'), \
     patch.object(PackageCatalog, '_start_background_refresh'), \
     patch('docker.from_env', side_effect=RuntimeError('No Docker in unit tests')):
    import app as hub


class BrowserClient(FlaskClient):
    """Normal tests send a valid token, as csrf.js/HTML forms do in a browser.

    Security regressions explicitly use FlaskClient to test missing/bad tokens.
    Existing explicit onboarding/access-token checks remain in their handlers.
    """
    def open(self, *args, **kwargs):
        if kwargs.get('method', 'GET').upper() not in {'GET', 'HEAD', 'OPTIONS'}:
            headers = Headers(kwargs.get('headers'))
            data = kwargs.get('data')
            if 'X-CSRF-Token' not in headers and not (isinstance(data, dict) and data.get('csrf_token')):
                with self.session_transaction() as session:
                    import secrets
                    session.setdefault('hub_csrf', secrets.token_urlsafe(32))
                    headers['X-CSRF-Token'] = session['hub_csrf']
                kwargs['headers'] = headers
        return super().open(*args, **kwargs)


@pytest.fixture(autouse=True)
def browser_client(monkeypatch):
    monkeypatch.setattr(hub.app, 'test_client_class', BrowserClient)


def pytest_sessionfinish(session, exitstatus):
    _data.cleanup()
