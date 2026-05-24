import os
import importlib
import pkgutil
from app import create_app
import app.models
from mongoengine.base.common import _document_registry
from mongoengine import Document

config_instance = os.getenv('INSTANCE')
app_instance = create_app(config_instance)

with app_instance.app_context():
    print("Cargando todos los modelos...")
    # Dynamically import all modules in app.models to ensure they are registered
    for _, module_name, _ in pkgutil.iter_modules(app.models.__path__):
        importlib.import_module('app.models.' + module_name)

    print("Iniciando la creacion manual de indices para TODOS los modelos...")
    
    for class_name, doc_cls in _document_registry.items():
        if issubclass(doc_cls, Document) and not doc_cls._meta.get('abstract', False):
            try:
                print("Indexando: " + class_name)
                doc_cls.ensure_indexes()
            except Exception as e:
                print("Error indexando " + class_name + ": " + str(e))
                
    print("!Todos los indices de la base de datos fueron creados con exito!")
