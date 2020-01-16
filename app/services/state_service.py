# app/services/state_service.py


from marshmallow import ValidationError

from app.models.state_model import State, StateSchema, StateSchemaUpdate
from app.helpers.error_helpers import RegisterNotFound


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
    name, polygon = data["name"], data["polygon"]
    state = State(name=name, polygon= polygon)
    state.save()
    state.reload()
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
    stateSchemaUpd = StateSchemaUpdate()
    state = getOr404(stateId)
    try:
        data = stateSchemaUpd.load(jsonData)
    except ValidationError as err:
        return err.messages, 400
    name, polygon = data["name"], data["polygon"]

    has_changed = False

    if name and name != state.name:
        state.name = name
        has_changed = True
    if polygon and polygon != state.polygon:
        state.polygon = polygon
        has_changed = True

    if has_changed:
        state.save()
        state.reload()
    
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
    
