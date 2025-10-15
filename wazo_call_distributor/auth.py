"""Authentication utilities for the call distributor plugin."""

from functools import wraps
from flask import request, g, current_app
from wazo_auth_client import Client as AuthClient
from .exceptions import UnauthorizedTenant

def get_auth_client():
    """Get or create an auth client."""
    if not hasattr(g, 'auth_client'):
        g.auth_client = AuthClient(**current_app.config['auth'])
    return g.auth_client

def get_token_tenant_uuid():
    """Get tenant UUID from token."""
    token = request.headers.get('X-Auth-Token')
    if not token:
        raise UnauthorizedTenant('No auth token provided')
    
    try:
        token_data = get_auth_client().token.get(token)
        return token_data['metadata'].get('tenant_uuid')
    except Exception as e:
        current_app.logger.error(f"Error validating token: {e}")
        raise UnauthorizedTenant('Invalid auth token')

def require_token(f):
    """Decorator to require valid auth token."""
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            get_token_tenant_uuid()
            return f(*args, **kwargs)
        except UnauthorizedTenant as e:
            return {'message': str(e)}, 401
    return decorated
