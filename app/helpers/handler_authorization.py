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


ADMIN_ROLES = ('superadmin', 'admin')


def get_current_user():
    """
    Returns the active (not deleted) user of the current access token, or None.
    """
    from flask_jwt_extended import get_jwt_identity
    from app.models.user_model import User

    identity = get_jwt_identity()
    if not identity or not identity.get('id'):
        return None
    return User.objects(id=identity['id'], isDeleted=False).first()


def is_admin(user):
    """
    Admin is defined by role, not by userType (a coordinator may hold the admin role).
    """
    return bool(user and user.role and user.role.devName in ADMIN_ROLES)


def can_manage_user(caller, target):
    """
    A user can manage himself; admins can manage anyone except a superadmin,
    which only another superadmin can manage.
    """
    if not caller or not target:
        return False
    if str(caller.id) == str(target.id):
        return True
    if not is_admin(caller):
        return False
    if target.role and target.role.devName == 'superadmin':
        return caller.role.devName == 'superadmin'
    return True


def admin_required(fn):
    """
    Like jwt_required, but the requester must also hold an admin role.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_app.config.get("TESTING"):
            verify_jwt_in_request()
            if not is_admin(get_current_user()):
                return {"msg": "No authorized"}, 403
        return fn(*args, **kwargs)
    return wrapper
