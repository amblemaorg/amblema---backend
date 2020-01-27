# /app/auth/views.py


from flask import jsonify
from flask_restful import Resource, reqparse
from flask.views import MethodView
from flask_jwt_extended import (
    create_access_token, create_refresh_token, get_jti, get_raw_jwt,
    jwt_required, jwt_refresh_token_required, get_jwt_identity,
    set_access_cookies, set_refresh_cookies)

from app.blueprints.auth import auth_blueprint
from app.models.user_model import User, UserSchema

class LoginView(MethodView):
    """This class-based view handles user login and access token generation."""

    def post(self):
        """Handle POST request for this view. Url ---> /auth/login"""
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('password', type=str, required=True,
                                help='The password parameter can not be null')
            parser.add_argument('email', type=str, required=True,
                                help='The email parameter can not be null')

            args = parser.parse_args()
            password = args['password'].strip()
            email = args['email'].strip().lower()

            user = User.objects(email=email).first()
            if not user or  not user.password_is_valid(password):
                return {"message": "Incorrect credectials"}, 400

            userSchema = UserSchema(only=("id", "firstName","userType"))
            userJson = userSchema.dump(user)
            permissions = user.get_permissions()
            payload = userJson
            payload['permissions']=permissions
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
            
        except Exception as e:
            # Create a response containing an string error message
            return {
                'message': str(e)
            }, 500

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


# Define the API resource
login_view = LoginView.as_view('login_view')
refresh_view = TokenRefreshView.as_view('refresh_view')


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
