"""
AE Discovery Tool — API Proxy
Handles Slack webhook and Salesforce API calls to avoid CORS issues.
Deployed as a Google Cloud Function.
"""
import json
import os
import urllib.request
import urllib.parse
import urllib.error

# CORS headers for GitHub Pages
ALLOWED_ORIGINS = [
    'https://kalanicuaresma.github.io',
    'http://localhost',
    'http://127.0.0.1',
    'null'  # for local file:// testing
]


def cors_headers(origin):
    """Return CORS headers if origin is allowed."""
    headers = {
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        'Access-Control-Max-Age': '3600',
    }
    if origin in ALLOWED_ORIGINS or any(origin.startswith(o) for o in ALLOWED_ORIGINS):
        headers['Access-Control-Allow-Origin'] = origin
    else:
        headers['Access-Control-Allow-Origin'] = ALLOWED_ORIGINS[0]
    return headers


def make_response(data, status=200, origin=''):
    """Create a Flask-style response tuple."""
    headers = cors_headers(origin)
    headers['Content-Type'] = 'application/json'
    return (json.dumps(data), status, headers)


def proxy(request):
    """
    Main Cloud Function entry point.
    Routes:
      POST /slack   — Forward message to Slack webhook
      POST /sf/auth — Exchange Salesforce OAuth code for tokens
      POST /sf/api  — Proxy Salesforce REST API calls
      POST /sf/refresh — Refresh Salesforce access token
    """
    origin = request.headers.get('Origin', '')

    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return ('', 204, cors_headers(origin))

    if request.method != 'POST':
        return make_response({'error': 'Method not allowed'}, 405, origin)

    try:
        body = request.get_json(silent=True) or {}
    except Exception:
        body = {}

    path = request.path.rstrip('/')
    action = body.get('action', '')

    # Route based on action field (simpler than path routing for single function)
    if action == 'slack':
        return handle_slack(body, origin)
    elif action == 'sf_auth':
        return handle_sf_auth(body, origin)
    elif action == 'sf_api':
        return handle_sf_api(body, origin)
    elif action == 'sf_refresh':
        return handle_sf_refresh(body, origin)
    elif action == 'health':
        return make_response({'status': 'ok', 'service': 'ae-discovery-api'}, 200, origin)
    else:
        return make_response({'error': 'Unknown action. Use: slack, sf_auth, sf_api, sf_refresh, health'}, 400, origin)


# ===== SLACK =====
def handle_slack(body, origin):
    """Forward a message to a Slack Incoming Webhook URL."""
    webhook_url = body.get('webhook_url', '')
    payload = body.get('payload', {})

    if not webhook_url or not webhook_url.startswith('https://hooks.slack.com/'):
        return make_response({'error': 'Invalid or missing webhook_url'}, 400, origin)

    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            webhook_url,
            data=data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            resp_body = resp.read().decode('utf-8')
            return make_response({'ok': True, 'slack_response': resp_body}, 200, origin)
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else str(e)
        return make_response({'error': f'Slack error ({e.code}): {error_body}'}, e.code, origin)
    except Exception as e:
        return make_response({'error': f'Slack request failed: {str(e)}'}, 500, origin)


# ===== SALESFORCE AUTH =====
def handle_sf_auth(body, origin):
    """Exchange OAuth authorization code for access + refresh tokens."""
    code = body.get('code', '')
    client_id = body.get('client_id', '')
    client_secret = body.get('client_secret', '')
    redirect_uri = body.get('redirect_uri', '')
    login_url = body.get('login_url', 'https://login.salesforce.com')

    if not all([code, client_id, client_secret, redirect_uri]):
        return make_response({'error': 'Missing required fields: code, client_id, client_secret, redirect_uri'}, 400, origin)

    try:
        token_url = f'{login_url}/services/oauth2/token'
        params = urllib.parse.urlencode({
            'grant_type': 'authorization_code',
            'code': code,
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': redirect_uri
        }).encode('utf-8')

        req = urllib.request.Request(token_url, data=params, method='POST')
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')

        with urllib.request.urlopen(req, timeout=15) as resp:
            token_data = json.loads(resp.read().decode('utf-8'))
            return make_response({
                'ok': True,
                'access_token': token_data.get('access_token', ''),
                'refresh_token': token_data.get('refresh_token', ''),
                'instance_url': token_data.get('instance_url', ''),
                'token_type': token_data.get('token_type', ''),
                'id': token_data.get('id', ''),
                'issued_at': token_data.get('issued_at', '')
            }, 200, origin)
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else str(e)
        return make_response({'error': f'Salesforce auth error ({e.code}): {error_body}'}, e.code, origin)
    except Exception as e:
        return make_response({'error': f'Salesforce auth failed: {str(e)}'}, 500, origin)


# ===== SALESFORCE REFRESH =====
def handle_sf_refresh(body, origin):
    """Refresh an expired Salesforce access token."""
    refresh_token = body.get('refresh_token', '')
    client_id = body.get('client_id', '')
    client_secret = body.get('client_secret', '')
    login_url = body.get('login_url', 'https://login.salesforce.com')

    if not all([refresh_token, client_id, client_secret]):
        return make_response({'error': 'Missing: refresh_token, client_id, client_secret'}, 400, origin)

    try:
        token_url = f'{login_url}/services/oauth2/token'
        params = urllib.parse.urlencode({
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': client_id,
            'client_secret': client_secret
        }).encode('utf-8')

        req = urllib.request.Request(token_url, data=params, method='POST')
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')

        with urllib.request.urlopen(req, timeout=15) as resp:
            token_data = json.loads(resp.read().decode('utf-8'))
            return make_response({
                'ok': True,
                'access_token': token_data.get('access_token', ''),
                'instance_url': token_data.get('instance_url', ''),
                'issued_at': token_data.get('issued_at', '')
            }, 200, origin)
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else str(e)
        return make_response({'error': f'Token refresh error ({e.code}): {error_body}'}, e.code, origin)
    except Exception as e:
        return make_response({'error': f'Token refresh failed: {str(e)}'}, 500, origin)


# ===== SALESFORCE API PROXY =====
def handle_sf_api(body, origin):
    """
    Proxy a Salesforce REST API call.
    Supports: GET, POST, PATCH, DELETE
    """
    instance_url = body.get('instance_url', '')
    access_token = body.get('access_token', '')
    method = body.get('method', 'GET').upper()
    endpoint = body.get('endpoint', '')  # e.g., /services/data/v59.0/sobjects/Account
    sf_body = body.get('body', None)

    if not all([instance_url, access_token, endpoint]):
        return make_response({'error': 'Missing: instance_url, access_token, endpoint'}, 400, origin)

    # Security: only allow Salesforce API endpoints
    if not endpoint.startswith('/services/'):
        return make_response({'error': 'Invalid endpoint — must start with /services/'}, 400, origin)

    try:
        url = f'{instance_url}{endpoint}'
        data = json.dumps(sf_body).encode('utf-8') if sf_body else None

        req = urllib.request.Request(url, data=data, method=method)
        req.add_header('Authorization', f'Bearer {access_token}')
        req.add_header('Content-Type', 'application/json')
        req.add_header('Accept', 'application/json')

        with urllib.request.urlopen(req, timeout=30) as resp:
            resp_body = resp.read().decode('utf-8')
            try:
                resp_json = json.loads(resp_body)
            except json.JSONDecodeError:
                resp_json = {'raw': resp_body}
            return make_response({'ok': True, 'data': resp_json, 'status': resp.status}, 200, origin)

    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else str(e)
        try:
            error_json = json.loads(error_body)
        except (json.JSONDecodeError, TypeError):
            error_json = {'raw': error_body}

        # If 401, token may be expired
        if e.code == 401:
            return make_response({
                'error': 'Salesforce token expired — refresh needed',
                'sf_error': error_json,
                'needs_refresh': True
            }, 401, origin)

        return make_response({
            'error': f'Salesforce API error ({e.code})',
            'sf_error': error_json
        }, e.code, origin)
    except Exception as e:
        return make_response({'error': f'Salesforce API request failed: {str(e)}'}, 500, origin)
