# app/services/state_service.py


from marshmallow import ValidationError
from mongoengine import NotUniqueError

from app.models.state_model import State, StateSchema
from app.helpers.error_helpers import RegisterNotFound
from app.helpers.document_metadata import getUniqueFields


def getAllStates():
    """
    get all available states records
    """
    stateSchema = StateSchema(exclude=("municipalities",))
    states = State.objects(status = True).all()
    return stateSchema.dump(states, many=True), 200


def saveState(jsonData):
    """
    Method that saves a new state record.   
    params: jsonData -> name<string>, polygon<array(coords)>
    """
    stateSchema = StateSchema()
    
    try:
        data = stateSchema.load(jsonData)
    except ValidationError as err:
        return err.messages, 400

    uniquesFields = getUniqueFields(State)
    fieldsForCheckDuplicates = []
    state = State()
    for field in data.keys():
        state[field] = data[field]
        if field in uniquesFields:
            fieldsForCheckDuplicates.append(
                {"field":field, "value":data[field]})
    isDuplicated = checkForDuplicates(fieldsForCheckDuplicates)
    if isDuplicated:
        return {
            "message": "Duplicated record found.",
            "data":isDuplicated}, 400
    try:
        state.save()
    except Exception as e:
        return {'status': 0, 'message': str(e)}, 400

    return stateSchema.dump(state), 201


def getState(stateId):
    """
    Return a state record filterd by its id
    """
    stateSchema = StateSchema()
    state = getOr404(stateId)
    return stateSchema.dump(state), 200

def updateState(stateId, jsonData):
    """
    Update a state record
    """
    stateSchema = StateSchema()
    try:
        data = stateSchema.load(jsonData, partial=("name"))
    except ValidationError as err:
        return err.messages, 400
    
    state = getOr404(stateId)
    has_changed = False
    uniquesFields = getUniqueFields(State)
    fieldsForCheckDuplicates = []
    for field in data.keys():
        if data[field] != state[field]:
            state[field] = data[field]
            has_changed = True
            if field in uniquesFields:
                fieldsForCheckDuplicates.append(
                    {"field":field, "value":data[field]})
    
    if has_changed:
        isDuplicated = checkForDuplicates(fieldsForCheckDuplicates)
        if isDuplicated:
            return {
                "message": "Duplicates record found.",
                "data": isDuplicated}, 400
        state.save()
    
    return stateSchema.dump(state), 200


def deleteState(stateId):
    """
    Delete (change status) a state record
    """
    state = getOr404(stateId)
    state.status = False
    state.save()
    
    return {"message": "State deleted successfully"}, 200
    


def getOr404(stateId):
    """
    Return a state record filterd by its id.
    Otherwise return a 404 not found error
    """
    
    state = State.objects(id=stateId, status=True).first()
    if not state:
        raise RegisterNotFound(message="State id not found",
                               status_code=404,
                               payload={"stateId": stateId})
    return state
    

def checkForDuplicates(attributes):
    """
    Return True if find an duplicate field  
    Return False otherwise

    Params.
      attributes: array. example [{"field":"name", "value":"Iribarren"}]
    """
    filterList = []
    
    if len(attributes):
        for f in attributes:
            filterList.append(Q(**{f['field']: f['value']}))
        
        states = State.objects.filter(
            reduce(operator.and_, attributes)
            ).all()
        if states:
            duplicates = []
            for state in states:
                for attr in attributes:
                    if attr['value'] == state[attr['field']]:
                        duplicates.append(attr)
            return duplicates
    return False