"""Admin-only Cloudflare endpoints; global hub middleware also enforces CSRF."""
from flask import Blueprint, jsonify, render_template, request
from flask_login import current_user
from services.cloudflare import CloudflareError


def create_cloudflare_blueprint(service):
    bp = Blueprint('cloudflare', __name__)

    @bp.before_request
    def admin():
        if not current_user.is_authenticated or not current_user.is_admin:
            return jsonify(ok=False, error='Kræver administratoradgang.'), 403

    @bp.after_request
    def private(response):
        response.headers['Cache-Control'] = 'no-store'
        return response

    @bp.errorhandler(CloudflareError)
    def invalid(exc):
        return jsonify(ok=False, error=str(exc)), 400

    def body():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            raise CloudflareError('Forventede et JSON-objekt.')
        return data

    @bp.get('/settings/cloudflare')
    def page():
        return render_template('cloudflare.html', active_page='settings')

    @bp.route('/api/cloudflare/settings', methods=['GET', 'POST'])
    def settings():
        if request.method == 'POST':
            service.enable(body().get('enabled'))
        return jsonify(ok=True, **service.settings())

    @bp.post('/api/cloudflare/domains')
    def connect():
        data = body()
        result = service.connect(data.get('name'), data.get('token'),label=data.get('label'))
        return jsonify(ok=True, **service.settings(), **result)

    @bp.delete('/api/cloudflare/domains/<int:domain_id>')
    def disconnect(domain_id):
        service.disconnect(domain_id)
        return jsonify(ok=True)

    @bp.get('/api/cloudflare/domains/<int:domain_id>')
    def overview(domain_id):
        return jsonify(ok=True, **service.overview(domain_id))

    @bp.post('/api/cloudflare/domains/<int:domain_id>/records')
    def create_record(domain_id):
        return jsonify(ok=True, record=service.save_record(domain_id, body()))

    @bp.post('/api/cloudflare/domains/<int:domain_id>/addresses')
    def create_address(domain_id):
        return jsonify(ok=True,record=service.create_address(domain_id,body()))

    @bp.route('/api/cloudflare/domains/<int:domain_id>/records/<record_id>', methods=['PATCH', 'DELETE'])
    def record(domain_id, record_id):
        if request.method == 'DELETE':
            service.delete_record(domain_id, record_id)
            return jsonify(ok=True)
        return jsonify(ok=True, record=service.save_record(domain_id, body(), record_id))

    @bp.route('/api/cloudflare/domains/<int:domain_id>/tunnels/<tunnel_id>/routes', methods=['POST', 'DELETE'])
    def tunnel_route(domain_id, tunnel_id):
        service.route(domain_id, tunnel_id, body(), delete=request.method == 'DELETE')
        return jsonify(ok=True)

    return bp
