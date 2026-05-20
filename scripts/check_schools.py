# -*- coding: utf-8 -*-
from pymongo import MongoClient
import pprint

client = MongoClient('mongodb://amblema:garden86@mongo:27017/amblema?authSource=admin')
db = client['amblema']

print("\nSpecific Bolivar Query:")
bolivar = db.users.find_one({'_cls': 'User.SchoolUser', 'name': {'$regex': 'Bol'}})
if bolivar:
    project_ref = bolivar.get('project', {}).get('id')
    project = db.projects.find_one({'_id': project_ref})
    print("Bolivar SchoolYears count:", len(project.get('schoolYears', [])))
