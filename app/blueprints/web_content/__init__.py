# app/blueprints/web_content/__init__.py

from flask import Blueprint

# This instance of a Blueprint that represents the web content blueprint
web_content_blueprint = Blueprint('web_content', __name__)
from . import views