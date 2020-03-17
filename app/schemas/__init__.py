from flask import current_app
from marshmallow import fields


fields.Field.default_error_messages["invalid"] = [{
    "status": "1", "msg": "Invalid field"}]
fields.Field.default_error_messages["required"] = [{
    "status": "2", "msg": "Required field"}]
fields.Field.default_error_messages["null"] = [{
    "status": "3", "msg": "Not allowed null"}]
fields.Field.default_error_messages["validator_failed"] = [{
    "status": "4", "msg": "Validator error"}]
fields.String.default_error_messages["invalid"] = [{
    "status": "1", "msg": "Invalid string"}]
fields.Integer.default_error_messages["invalid"] = [{
    "status": "1", "msg": "Invalid integer"}]
fields.DateTime.default_error_messages["invalid"] = [{
    "status": "1", "msg": "Invalid Datetime"}]
fields.Date.default_error_messages["invalid"] = [{
    "status": "1", "msg": "Invalid Date"}]
