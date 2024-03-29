# /app/blueprints/web_content/views.py

import os
from flask import request, send_file
from flask_restful import Resource
from flask.views import MethodView
from flask import send_from_directory

from app.blueprints.web_content import web_content_blueprint
from app.blueprints.web_content.models.web_content import WebContent, WebContentSchema
from app.blueprints.web_content.models.post_model import Post, PostSchema
from app.blueprints.web_content.services import WebContentService, SchoolPageContentService
from app.helpers.handler_request import getQueryParams
from app.helpers.query_filter import MongoQueryFilter
from app.services.generic_service import GenericServices
from resources.images import path_images
from resources.files import files_path


class WebContentView(MethodView):
    service = WebContentService(
        Model=WebContent,
        Schema=WebContentSchema)

    def get(self):
        page = None
        if 'page' in request.args:
            page = request.args.get('page')
        return self.service.getAllRecords(page=page)

    def post(self):
        jsonData = request.get_json()
        page = None
        if 'page' in request.args:
            page = [request.args.get('page')]
        return self.service.saveRecord(jsonData, only=page)


class SchoolPagesView(MethodView):
    service = SchoolPageContentService()

    def get(self):
        return self.service.getAllRecords()


class SchoolPageView(MethodView):
    service = SchoolPageContentService()

    def get(self, id):
        return self.service.get(id)


class PostView(MethodView):
    service = GenericServices(
        Model=Post,
        Schema=PostSchema
    )

    def get(self):
        filters = getQueryParams(request)
        return self.service.getAllRecords(filters=filters)

    def post(self):
        jsonData = request.get_json()
        return self.service.saveRecord(jsonData)


class PostViewPaginated(MethodView):
    service = GenericServices(
        Model=Post,
        Schema=PostSchema
    )

    def get(self, page_number):
        page_size = 8
        filters = getQueryParams(request)
        filtersWithOperator = []
        finalFilters = [{"field": "status", "value": "1"}]

        if filters != None:
            for f in filters:
                if f['field'] == 'title' or f['field'] == 'text':
                    filtersWithOperator.append(f)
                elif f['field'] == 'page_size':
                    page_size = int(f['value'])
                else:
                    finalFilters.append(f)

            queryfilter = MongoQueryFilter()
            filtersWithOperator = queryfilter.assignOperatorToFilters(
                filtersWithOperator,
                'icontains'
            )
            finalFilters.extend(filtersWithOperator)

        return self.service.getPaginatedRecords(filters=finalFilters, page=page_number, page_size=page_size)


class PostHandlerView(MethodView):
    service = GenericServices(
        Model=Post,
        Schema=PostSchema)

    def get(self, id):
        return self.service.getRecord(id)

    def put(self, id):
        jsonData = request.get_json()
        return self.service.updateRecord(
            recordId=id,
            jsonData=jsonData,
            partial=True)

    def delete(self, id):
        return self.service.deleteRecord(id)


class ImagesView(MethodView):
    def get(self, folder, imageId):
        filename = path_images+'/'+folder+'/'+imageId
        extension = os.path.splitext(filename)[1]
        return send_file(filename, mimetype='image/'+extension)


class FileView(MethodView):
    def get(self, folder, filename):
        files_path2 = files_path + '/' + folder + '/'
        return send_from_directory(files_path2, filename)


webContentView = WebContentView.as_view('webContentView')
schoolPageView = SchoolPageView.as_view('schoolPageView')
schoolPagesView = SchoolPagesView.as_view('schoolPagesView')
postView = PostView.as_view('postView')
postViewPaginated = PostViewPaginated.as_view('postViewPaginated')
postHandlerView = PostHandlerView.as_view('postHandlerView')
imagesView = ImagesView.as_view('imagesView')
fileView = FileView.as_view('fileView')

web_content_blueprint.add_url_rule(
    '/webcontent',
    view_func=webContentView,
    methods=['POST', 'GET']
)

web_content_blueprint.add_url_rule(
    '/schoolspage',
    view_func=schoolPagesView,
    methods=['GET']
)

web_content_blueprint.add_url_rule(
    '/schoolspage/<string:id>',
    view_func=schoolPageView,
    methods=['GET']
)

web_content_blueprint.add_url_rule(
    '/webcontent/posts',
    view_func=postView,
    methods=['POST', 'GET']
)

web_content_blueprint.add_url_rule(
    '/webcontent/posts/page/<int:page_number>',
    view_func=postViewPaginated,
    methods=['GET']
)

web_content_blueprint.add_url_rule(
    '/webcontent/posts/<string:id>',
    view_func=postHandlerView,
    methods=['PUT', 'GET', 'DELETE']
)

web_content_blueprint.add_url_rule(
    '/resources/images/<path:folder>/<string:imageId>',
    view_func=imagesView,
    methods=['GET']
)

web_content_blueprint.add_url_rule(
    '/resources/files/<path:folder>/<string:filename>',
    view_func=fileView,
    methods=['GET']
)
