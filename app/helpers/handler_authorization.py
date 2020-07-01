# app/helpers/handler_authorization.py

from functools import wraps

from flask_jwt_extended.view_decorators import verify_jwt_in_request
from flask import current_app


def jwt_required(fn):
    """
    A decorator to protect a Flask endpoint.

    If you decorate an endpoint with this, it will ensure that the requester
    has a valid access token before allowing the endpoint to be called. This
    does not check the freshness of the access token.

    See also: :func:`~flask_jwt_extended.fresh_jwt_required`
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_app.config.get("TESTING"):
            verify_jwt_in_request()
        return fn(*args, **kwargs)
    return wrapper
