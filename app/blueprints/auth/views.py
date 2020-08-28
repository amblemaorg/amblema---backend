# /app/auth/views.py


from flask import current_app
from flask import jsonify, request
from flask_restful import Resource, reqparse
from flask.views import MethodView
from flask_jwt_extended import (
    create_access_token, create_refresh_token, get_jti, get_raw_jwt,
    jwt_required, jwt_refresh_token_required, get_jwt_identity,
    set_access_cookies, set_refresh_cookies)
import copy

from app.blueprints.auth import auth_blueprint
from app.models.user_model import User
from app.models.school_user_model import SchoolUser
from app.models.sponsor_user_model import SponsorUser
from app.models.coordinator_user_model import CoordinatorUser
from app.models.admin_user_model import AdminUser
from app.schemas.user_schema import UserSchema
from app.schemas.school_user_schema import SchoolUserSchema
from app.schemas.sponsor_user_schema import SponsorUserSchema
from app.schemas.coordinator_user_schema import CoordinatorUserSchema
from app.schemas.admin_user_schema import AdminUserSchema
from app.models.project_model import Project
from app.models.school_year_model import SchoolYear
from .schemas import RecoverySchema, ChangePasswordSchema, LoginSchema
from app.helpers.ma_schema_validators import ValidationError


class LoginView(MethodView):
    """This class-based view handles user login and access token generation."""

    def post(self):
        schema = LoginSchema()

        try:
            site = request.args.get('site')
            jsonData = request.get_json()
            data = schema.load(jsonData)
            user = User.objects(email=data['email'], isDeleted=False).only(
                'id', 'role', 'userType', 'password').first()
            schema = UserSchema()
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

            # Generate the access token.
            # This will be generated in login microservice
            payloads = getUserPayload(user)
            access_token = create_access_token(payloads['accessPayload'])
            refresh_token = create_refresh_token(payloads['refreshPayload'])

            if site and site == 'peca':
                token = {
                    'msg': 'You logged in successfully',
                    'token_access': {
                        'access_token': access_token,
                        'refresh_token': refresh_token
                    }
                }
            else:
                token = {
                    'msg': 'You logged in successfully',
                    'access_token': access_token,
                    'refresh_token': refresh_token
                }
            resp = jsonify(token)

            # set_access_cookies(resp, access_token)
            # set_refresh_cookies(resp, refresh_token)
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
        user = User.objects(id=current_user['id']).first()
        payloads = getUserPayload(user)
        access_token = create_access_token(payloads['accessPayload'])
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


def getUserPayload(user):
    schema = UserSchema()
    refreshSchema = UserSchema(only=('id',))
    
    if user.userType == '1':  # admin
        user = AdminUser.objects(id=user.id).first()
        schema = AdminUserSchema()
    elif user.userType == '2':  # coordinator
        user = CoordinatorUser.objects(id=user.id).first()
        schema = CoordinatorUserSchema()
    elif user.userType == '3':  # sponsor
        user = SponsorUser.objects(id=user.id).first()
        schema = SponsorUserSchema()
    elif user.userType == '4':  # school
        user = SchoolUser.objects(id=user.id).first()
        schema = SchoolUserSchema()

    userJson = schema.dump(user)
    permissions = user.get_permissions()
    projectsJson = []
    projects = []
    activeSchoolYear = SchoolYear.objects(
        isDeleted=False, status="1").only('id', 'name').first()
    if activeSchoolYear:
        activeSchoolYear = {
            "id": str(activeSchoolYear.id),
            "name": activeSchoolYear.name
        }
    if user.userType == "2":
        projects = Project.objects(
            isDeleted=False, status="1", coordinator=user.id).exclude('stepsProgress',)
    elif user.userType == "3":
        projects = Project.objects(
            isDeleted=False, status="1", sponsor=user.id).exclude('stepsProgress',)
    elif user.userType == "4":
        projects = Project.objects(
            isDeleted=False, status="1", school=user.id).exclude('stepsProgress',)

    for project in projects:
        projectsJson.append(
            {
                'id': str(project.id),
                "code": project.code.zfill(7),
                "school": {
                    "id": str(project.school.id),
                    "name": project.school.name
                } if project.school else {},
                "coordinator": {
                    "id": str(project.coordinator.id),
                    "name": project.coordinator.name
                } if project.coordinator else {},
                "sponsor": {
                    "id": str(project.sponsor.id),
                    "name": project.sponsor.name
                } if project.sponsor else {},
                "phase": project.phase,
                "pecas": [
                    {
                        "id": str(peca.pecaId),
                        "schoolYear": {
                            "id": str(peca.schoolYear.id),
                            "name": peca.schoolYear.name
                        }
                    } for peca in project.schoolYears
                ]
            }
        )
    refreshJson = refreshSchema.dump(user)
    payload = userJson
    payload['projects'] = projectsJson
    payload['activeSchoolYear'] = activeSchoolYear
    payload['permissions'] = permissions
    

    return {'accessPayload': payload, 'refreshPayload': refreshJson}
