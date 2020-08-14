# app/helpers/document_metadata.py
from flask import current_app
import inspect

def getUniqueFields(document):
    """
    Method that return all fields which  
    must be uniques
    """
    uniquesFields = []
    for field in document._fields:
        if hasattr(document._fields[field], 'unique_c'):
            uniquesFields.append(document._fields[field].name)
    return uniquesFields


def getFileFields(document):
    """
    Method that return all fields wich
    are received as file
    """
    fileFields = {}
    for field in document._fields:
        if hasattr(document._fields[field], 'is_file'):
            size = None
            attributes = inspect.getmembers(
                document._fields[field], lambda a:not(inspect.isroutine(a)))
            attributes = [a for a in attributes if a[0] == 'size']
            if attributes:
                size = attributes[0][1]
            fileFields[document._fields[field].name] = {'size': size}
    return fileFields
