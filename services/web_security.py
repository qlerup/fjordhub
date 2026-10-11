"""Session request protection shared by forms and JSON browser requests."""
import secrets

from flask import jsonify, request, session


def csrf_token():
    if not session.get('hub_csrf'):
        session['hub_csrf'] = secrets.token_urlsafe(32)
    return session['hub_csrf']


def check_csrf():
    if request.method in {'GET', 'HEAD', 'OPTIONS'}:
        return None
    supplied = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token', '')
    # Existing onboarding and access-token forms have their own session-bound
    # tokens. Their handlers additionally validate the specific token they use.
    expected = [session.get(key, '') for key in ('hub_csrf', 'onboarding_csrf', 'access_token_csrf')]
    if not supplied or not any(value and secrets.compare_digest(supplied, value) for value in expected):
        return jsonify(ok=False, error='Genindlæs siden og prøv igen.', csrf_required=True), 403
    return None
