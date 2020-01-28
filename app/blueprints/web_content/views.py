# /app/blueprints/web_content/views.py

import os

from flask import request, send_file
from flask_restful import Resource
from flask.views import MethodView

from app.blueprints.web_content import web_content_blueprint
from app.blueprints.web_content.models.web_content import WebContent, WebContentSchema
from app.blueprints.web_content.services import WebContentService
from app.helpers.handler_request import getQueryParams
from resources.images import path_images


class WebContentView(MethodView):
    service = WebContentService(
        Model=WebContent,
        Schema=WebContentSchema)
    
    def get(self):
        return self.service.getAllRecords()

    def post(self):
        jsonData = request.get_json()
        return self.service.saveRecord(jsonData)


class HomePageView(MethodView):
    service  = WebContentService(
        Model=WebContent,
        Schema=WebContentSchema)
    
    def get(self):
        return self.service.getAllRecords(only=("homePage",))


class ImagesView(MethodView):
    
    def get(self, imageId):
        filename = path_images+'/'+imageId
        extension = os.path.splitext(filename)[1]
        return send_file(filename, mimetype='image/'+extension)


webContentView = WebContentView.as_view('webContentView')
homePageView = HomePageView.as_view('homePageView')
imagesView = ImagesView.as_view('imagesView')

web_content_blueprint.add_url_rule(
    '/webcontent',
    view_func=webContentView,
    methods=['POST', 'GET']
)
web_content_blueprint.add_url_rule(
    '/webcontent/home',
    view_func=homePageView,
    methods=['GET']
)
web_content_blueprint.add_url_rule(
    '/resources/images/<string:imageId>',
    view_func=imagesView,
    methods=['GET']
)
