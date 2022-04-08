# app/services/diagnostic_service.py


from datetime import datetime

from flask import current_app
from marshmallow import ValidationError

from app.models.school_year_model import SchoolYear
from app.models.user_model import User
from app.helpers.error_helpers import RegisterNotFound
import os
class EmailsLostService():
    def run(self):
        if os.getenv('INSTANCE') != "production":
            emails = ["fidel.alejos@gmail.com","valmore_canelon1994@hotmail.com", "morejose.15@gmail.com", "valmore@binauraldev.com"]
        else:
            print("adasdadas")
            #emails = ["yelimargarita2015@hotmail.com","quintanasara4@gmail.com","edmalinda_131@hotmail.com","kuberniesi@hotmail.com","yelitzaderojas2@gmail.com","greeydym@gmail.com","erihannajobicsonka@gmail.com","bettyhcostera@hotmail.com","libmerviszerpa2@gmail.com","magastrid27@gmail.com","colinasdelangel@hotmail.com","jenaroaguirre010058@gmail.com","fundacion@madreluisa.org"]
        
        for email in emails:
            user = User.objects(email=email).first()
            if user:
                password = user.generatePassword()
                user.password = password
                user.setHashPassword()
                user.save()
                user.sendRegistrationEmail(password)
                
        return {"status":200, "msg": "Exito"},200