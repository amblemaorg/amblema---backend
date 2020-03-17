# app/helpers/document_metadata.py


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
    fileFields = []
    for field in document._fields:
        if hasattr(document._fields[field], 'is_file'):
            fileFields.append(document._fields[field].name)
    return fileFields
