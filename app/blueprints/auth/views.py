# /app/auth/views.py


from flask import current_app
from flask import jsonify, request
from flask_restful import Resource, reqparse
from flask.views import MethodView
from flask_jwt_extended import (
    create_access_token, create_refresh_token, get_jti, get_raw_jwt,
    jwt_required, jwt_refresh_token_required, get_jwt_identity,
    set_access_cookies, set_refresh_cookies)

from app.blueprints.auth import auth_blueprint
from app.models.user_model import User
from app.schemas.user_schema import UserSchema
from .schemas import RecoverySchema, ChangePasswordSchema, LoginSchema
from app.helpers.ma_schema_validators import ValidationError


class LoginView(MethodView):
    """This class-based view handles user login and access token generation."""

    def post(self):
        schema = LoginSchema()
        try:
            jsonData = request.get_json()
            data = schema.load(jsonData)
            user = User.objects(email=data['email'], isDeleted=False).first()
            if not user:
                return {
                    "email": [
                        {"status": "5", "msg": "Record not found: {}".format(
                            data['email'])}
                    ]
                }, 400
            if not user.password_is_valid(data['password']):
                return {"password": [{"status": "14", "msg": "Password doesn't match"}]}, 400

            if user.role.status == "2":
                return {"role": [{"status": "15", "msg": "No authorized"}]}, 400

            userSchema = UserSchema(only=("id", "email", "name", "userType"))
            userJson = userSchema.dump(user)
            permissions = user.get_permissions()
            payload = userJson
            payload['permissions'] = permissions
            # Generate the access token.
            # This will be generated in login microservice
            access_token = create_access_token(payload)
            refresh_token = create_refresh_token(payload)

            resp = jsonify(
                {'msg': 'You logged in successfully',
                 'access_token': access_token,
                 'refresh_token': refresh_token
                 })
            #set_access_cookies(resp, access_token)
            #set_refresh_cookies(resp, refresh_token)
            return resp, 200

        except ValidationError as err:
            return err.normalized_messages(), 400

    @jwt_required
    def delete(self):
        """ Endpoint for revoking the current users access token"""

        return {"msg": "Access token revoked"}, 200


class TokenRefreshView(MethodView):
    """This class-based view handles user access token refresh."""
    @jwt_refresh_token_required
    def post(self):
        current_user = get_jwt_identity()
        access_token = create_access_token(current_user)
        return {'access_token': access_token}

    @jwt_refresh_token_required
    def delete(self):
        """ Endpoint for revoking the current users access token"""
        return {"msg": "Refresh token revoked"}, 200


class RecoveryPasswordView(MethodView):
    """This class-based view handles user recovery password function."""

    def post(self):
        schema = RecoverySchema()
        try:
            jsonData = request.get_json()
            data = schema.load(jsonData)
            user = User.objects(email=data['email']).first()
            if not user:
                return {"email": [{"status": "5", "msg": "Record not found"}]}, 400
            password = user.generatePassword()
            user.password = password
            user.setHashPassword()
            user.save()
            user.sendChangePasswordEmail(password)
            return {"msg": "Password changed successfully"}, 200

        except ValidationError as err:
            return err.normalized_messages(), 400


class ChangePasswordView(MethodView):
    """This class-based view handles user change password function."""

    def post(self):
        schema = ChangePasswordSchema()
        try:
            jsonData = request.get_json()
            data = schema.load(jsonData)
            if data['password'] != data['confirmPassword']:
                return {"password": [{"status": "14", "msg": "Password doesn't match"}]}, 400
            password = data['password']
            user = data['user']
            user.password = password
            user.setHashPassword()
            user.save()
            user.sendChangePasswordEmail(password)
            return {"msg": "Password changed successfully"}, 200

        except ValidationError as err:
            return err.normalized_messages(), 400


# Define the API resource
login_view = LoginView.as_view('login_view')
refresh_view = TokenRefreshView.as_view('refresh_view')
recovery_view = RecoveryPasswordView.as_view('recovery_view')
change_password_view = ChangePasswordView.as_view('change_password_view')


# Define the rule for the registration url --->  /auth/login
# Then add the rule to the blueprint
auth_blueprint.add_url_rule(
    '/auth/login',
    view_func=login_view,
    methods=['POST', 'DELETE']
)

# Define the rule for the registration url --->  /auth/login
# Then add the rule to the blueprint
auth_blueprint.add_url_rule(
    '/auth/refresh',
    view_func=refresh_view,
    methods=['POST', 'DELETE']
)

auth_blueprint.add_url_rule(
    '/auth/passwordrecovery',
    view_func=recovery_view,
    methods=['POST']
)

auth_blueprint.add_url_rule(
    '/auth/changepassword',
    view_func=change_password_view,
    methods=['POST']
)
