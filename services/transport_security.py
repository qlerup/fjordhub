"""Opt-in public HTTPS without removing direct HTTP access on a home LAN."""
from dataclasses import dataclass
import ipaddress
import os
import re
from urllib.parse import quote, quote_from_bytes, urlsplit

from flask import current_app, has_request_context, redirect, request
from flask.sessions import SecureCookieSessionInterface


@dataclass(frozen=True)
class TransportPolicy:
    public_url: str = ''
    hostname: str = ''
    authority: str = ''
    trusted_proxies: tuple = ()

    @classmethod
    def from_config(cls, public_url='', trusted_proxies=''):
        value = str(public_url or '').strip()
        networks = tuple(ipaddress.ip_network(item.strip(), strict=False)
                         for item in str(trusted_proxies or '').split(',') if item.strip())
        if not value:
            return cls(trusted_proxies=networks)
        message = 'FJORDHUB_PUBLIC_URL must be an HTTPS origin, for example https://hub.example.com'
        if any(ord(char) <= 32 or ord(char) == 127 for char in value) or '\\' in value:
            raise ValueError(message)
        try:
            parts = urlsplit(value)
            hostname = (parts.hostname or '').rstrip('.').encode('idna').decode('ascii').lower()
            port = parts.port
            if (parts.scheme != 'https' or not hostname or parts.username is not None
                    or parts.password is not None or parts.path not in ('', '/') or parts.query
                    or parts.fragment or '?' in value or '#' in value or port == 0):
                raise ValueError(message)
            try:
                address = ipaddress.ip_address(hostname)
                authority = f'[{address}]' if address.version == 6 else str(address)
                hostname = str(address)
            except ValueError:
                if len(hostname) > 253 or not all(re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?',
                                                             label) for label in hostname.split('.')):
                    raise ValueError(message)
                authority = hostname
            if port is not None and port != 443:
                authority += f':{port}'
        except (ValueError, UnicodeError) as exc:
            raise ValueError(message) from exc
        return cls(f'https://{authority}', hostname, authority, networks)

    def is_public_request(self):
        if not self.hostname or not has_request_context():
            return False
        try:
            hostname = (urlsplit('http://' + request.host).hostname or '').rstrip('.')
            return hostname.encode('idna').decode('ascii').lower() == self.hostname
        except (ValueError, UnicodeError):
            return False

    def is_https(self):
        if request.is_secure:
            return True
        try:
            peer = ipaddress.ip_address(request.environ.get('REMOTE_ADDR', ''))
        except ValueError:
            return False
        # A trusted last-hop proxy must overwrite this header with one value.
        # Do not trust client-provided Host/Forwarded/CF-Visitor headers or a chain.
        return (any(peer in network for network in self.trusted_proxies)
                and request.headers.get('X-Forwarded-Proto', '').strip().lower() == 'https')


class TransportSessionInterface(SecureCookieSessionInterface):
    """Request-specific settings; never mutate shared Flask config per request."""

    def get_cookie_name(self, app):
        name = super().get_cookie_name(app)
        if app.config['FJORDHUB_TRANSPORT_POLICY'].is_public_request():
            return name if name.startswith('__Host-') else '__Host-' + name
        return name

    def get_cookie_secure(self, app):
        return (app.config['FJORDHUB_TRANSPORT_POLICY'].is_public_request()
                or (has_request_context() and request.is_secure)
                or super().get_cookie_secure(app))

    def get_cookie_domain(self, app):
        if app.config['FJORDHUB_TRANSPORT_POLICY'].is_public_request():
            return None
        return super().get_cookie_domain(app)

    def get_cookie_path(self, app):
        if app.config['FJORDHUB_TRANSPORT_POLICY'].is_public_request():
            return '/'
        return super().get_cookie_path(app)


def configure_transport(app):
    app.config['FJORDHUB_TRANSPORT_POLICY'] = TransportPolicy.from_config(
        os.environ.get('FJORDHUB_PUBLIC_URL', ''), os.environ.get('FJORDHUB_TRUSTED_PROXIES', ''))
    app.session_interface = TransportSessionInterface()

    @app.before_request
    def public_https_redirect():
        policy = current_app.config['FJORDHUB_TRANSPORT_POLICY']
        if policy.is_public_request() and (not policy.is_https() or request.host.lower() != policy.authority):
            # Build from configured origin, never from a client-controlled forwarding header.
            path = quote(request.path, safe='/')
            query = quote_from_bytes(request.query_string, safe="!$&'()*+,-./:;=?@_~%")
            return redirect(policy.public_url + path + ('?' + query if query else ''), code=308)

    @app.after_request
    def public_https_headers(response):
        policy = current_app.config['FJORDHUB_TRANSPORT_POLICY']
        if policy.is_public_request() and policy.is_https():
            # No includeSubDomains or preload: other self-hosted apps remain independent.
            response.headers['Strict-Transport-Security'] = 'max-age=31536000'
            old_name = app.config['SESSION_COOKIE_NAME']
            if old_name != app.session_interface.get_cookie_name(app) and old_name in request.cookies:
                # Browsers stop automatically reusing the old non-Secure login cookie.
                response.delete_cookie(old_name, path=app.config.get('SESSION_COOKIE_PATH') or '/',
                                       domain=app.config.get('SESSION_COOKIE_DOMAIN'))
        return response
