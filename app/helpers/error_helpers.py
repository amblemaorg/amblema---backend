from flask import jsonify
from flask_restful import Api



class CustomApi(Api):
    """
    Custom class API for handle errors.   
    This fix bugs on gunicorn server
    """
    def handle_error(self, e):
        for val in current_app.error_handler_spec.values():
            for handler in val.values():
                registered_error_handlers = list(filter(lambda x: isinstance(e, x), handler.keys()))
                if len(registered_error_handlers) > 0:
                    raise e
        return super().handle_error(e)

class RegisterNotFound(Exception):
    """
    Custom Exception for errors handler
    """
    status_code = 404

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv

class CSTM_Exception(Exception):
    """
    Custom Exception for errors handler
    """
    status_code = 404

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


def handleNotFound(error):
    """
    Method that convert exception error into json response
    """
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response