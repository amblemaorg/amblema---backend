# app/helpers/document_metadata.py



def getUniqueFields(document):
    """
    Method that return all fields which  
    must be uniques
    """
    uniquesFields = []
    for field in document._fields:
        if document._fields[field].unique:
            uniquesFields.append(document._fields[field].name)
    return uniquesFields