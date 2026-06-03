# -*- coding: utf-8 -*-
from __future__ import print_function
import os
import sys

# Asegurar que el directorio raiz del proyecto este en el path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app

# Obtener instancia de configuracion, por defecto 'production' para produccion
config_instance = os.getenv('INSTANCE', 'production')
print("Usando instancia de configuracion: {}".format(config_instance))

try:
    app_instance = create_app(config_instance)
except Exception as e:
    print("Error al inicializar la aplicacion: {}".format(e))
    sys.exit(1)

with app_instance.app_context():
    try:
        from mongoengine.connection import get_db
        db = get_db()
    except Exception as e:
        print("Error al obtener la conexion de base de datos: {}".format(e))
        sys.exit(1)
        
    collection = db.requests_content_approval
    try:
        index_information = collection.index_information()
    except Exception as e:
        print("Error al leer informacion de indices: {}".format(e))
        sys.exit(1)
    
    print("Indices actuales en requests_content_approval:")
    for name, info in index_information.items():
        print("  - Nombre: {}, Info: {}".format(name, info))
    
    # Buscamos el indice sobre la clave 'project'
    target_index = None
    for name, info in index_information.items():
        key_info = info.get('key', [])
        # En pymongo antiguo (Python 2.7) el valor puede ser un dict o una lista de tuplas
        if isinstance(key_info, list):
            keys = [k[0] for k in key_info]
        else:
            keys = list(key_info.keys())
            
        # Si la unica clave es 'project', ese es el indice a eliminar
        if 'project' in keys and len(keys) == 1:
            target_index = name
            break
            
    if target_index:
        print("Eliminando indice obsoleto en la base de datos: {}".format(target_index))
        try:
            collection.drop_index(target_index)
            print("Indice {} eliminado con exito.".format(target_index))
        except Exception as e:
            print("Error al eliminar el indice {}: {}".format(target_index, e))
    else:
        print("No se encontro un indice obsoleto para la clave 'project'.")

    print("Re-creando indices para RequestContentApproval...")
    try:
        from app.models.request_content_approval_model import RequestContentApproval
        RequestContentApproval.ensure_indexes()
        print("Indices de RequestContentApproval creados/actualizados con exito!")
    except Exception as e:
        print("Error al crear/actualizar indices: {}".format(e))
