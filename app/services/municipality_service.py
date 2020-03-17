# app/services/municipality_service.py


from datetime import datetime
from functools import reduce
import operator

from marshmallow import ValidationError
from mongoengine import Q

from app.models.state_model import (
    State,
    Municipality,
    MunicipalitySchema)
from app.helpers.error_helpers import RegisterNotFound
from app.helpers.document_metadata import getUniqueFields


def getAllMunicipalities(stateId):
    """
    get all available municipalities records in state
    """
    municipalitySchema = MunicipalitySchema()
    municipalities = getStateOr404(
        stateId).municipalities.filter(isDeleted=False)
    return municipalitySchema.dump(municipalities, many=True), 200


def saveMunicipality(stateId, jsonData):
    """
    Method that saves a new municipality record.   
    param: jsonData -> name<string>, polygon<array(coords)>  
    param: stateId
    """
    municipalitySchema = MunicipalitySchema()
    try:
        data = municipalitySchema.load(jsonData)
    except ValidationError as err:
        return err.messages, 400

    uniquesFields = getUniqueFields(Municipality)
    fieldsForCheckDuplicates = []
    municipality = Municipality()
    for field in data.keys():
        municipality[field] = data[field]
        if field in uniquesFields:
            fieldsForCheckDuplicates.append(
                {"field": field, "value": data[field]})

    state = getStateOr404(stateId)
    isDuplicated = checkForDuplicates(stateId, fieldsForCheckDuplicates)
    if isDuplicated:
        for field in isDuplicated:
            raise ValidationError(
                {field["field"]: [{"status": "5",
                                   "msg": "Duplicated record found: '{}'".format(field["value"])}]}
            )
    state.municipalities.append(municipality)
    state.save()
    return municipalitySchema.dump(municipality), 201


def getMunicipality(stateId, municipalityId):
    """
    Return a municipality record filterd by its id
    """
    municipalitySchema = MunicipalitySchema()
    municipality = getMunicipalityOr404(stateId, municipalityId)
    return municipalitySchema.dump(municipality), 200


def updateMunicipality(stateId, municipalityId, jsonData):
    """
    Update a municipality record
    """
    municipalitySchema = MunicipalitySchema()
    try:
        data = municipalitySchema.load(jsonData, partial=("name",))
    except ValidationError as err:
        return err.messages, 400

    municipality = getMunicipalityOr404(stateId, municipalityId)
    has_changed = False
    uniquesFields = getUniqueFields(Municipality)
    fieldsForCheckDuplicates = []
    for field in data.keys():
        if data[field] != municipality[field]:
            municipality[field] = data[field]
            has_changed = True
            if field in uniquesFields:
                fieldsForCheckDuplicates.append(
                    {"field": field, "value": data[field]})

    if has_changed:
        isDuplicated = checkForDuplicates(stateId, fieldsForCheckDuplicates)
        if isDuplicated:
            for field in isDuplicated:
                raise ValidationError(
                    {field["field"]: [{"status": "5",
                                       "msg": "Duplicated record found: '{}'".format(field["value"])}]}
                )
        municipality.updateAt = datetime.utcnow()
        State.objects(
            id=stateId,
            municipalities__id=municipalityId
        ).update(set__municipalities__S=municipality)

    return municipalitySchema.dump(municipality), 200


def deleteMunicipality(stateId, municipalityId):
    """
    Delete (change status) a municipality record
    """
    municipality = getMunicipalityOr404(stateId, municipalityId)
    municipality.isDeleted = True
    municipality.updateAt = datetime.utcnow()
    State.objects(
        id=stateId,
        municipalities__id=municipalityId
    ).update(set__municipalities__S=municipality)
    return {"message": "Municipality deleted successfully"}, 200


def getStateOr404(stateId):
    """
    Return a state record filterd by its id.
    Otherwise return a 404 not found error
    """
    state = State.objects(id=stateId, isDeleted=False).first()
    if not state:
        raise RegisterNotFound(message="State id not found",
                               status_code=404,
                               payload={"stateId": stateId})
    return state


def getMunicipalityOr404(stateId, municipalityId):
    """
    Return a municipality record filterd by its id.
    Otherwise return a 404 not found error
    """
    state = State.objects(
        id=stateId,
        municipalities__id=municipalityId,
        isDeleted=False,
        municipalities__isDeleted=False).first()
    if not state:
        raise RegisterNotFound(message="State id not found",
                               status_code=404,
                               payload={"stateId": stateId})
    municipality = state.municipalities.filter(
        id=municipalityId, isDeleted=False).first()
    if not municipality:
        raise RegisterNotFound(message="Municipality id not found",
                               status_code=404,
                               payload={"municipalityId": municipalityId})
    return municipality


def checkForDuplicates(stateId, attributes):
    """
    Return True if find an duplicate field  
    Return False otherwise

    Params.
      stateId: string
      attributes: array. example [{"field":"name", "value":"Iribarren"}]
    """
    filterList = []

    if len(attributes):
        for f in attributes:
            filterList.append(Q(**{f['field']: f['value']}))

        states = State.objects.filter(
            Q(id=stateId)
            & (reduce(operator.or_, attributes))
        ).all()
        if states:
            duplicates = []
            for state in states:
                for municipality in state.municipalities:
                    for attr in attributes:
                        if attr['value'] == municipality[attr['field']]:
                            duplicates.append(attr)
            return duplicates
    return False
