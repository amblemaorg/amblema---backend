# app/helpers/handler_files.py


from base64 import b64decode
import os
from mimetypes import guess_extension, guess_type

from werkzeug.utils import secure_filename

from app.helpers.error_helpers import CSTM_Exception
from resources.files import files_path
from flask import current_app

allowedExtensions = {'pdf', 'pptx', 'docx'}

def upload(file, name, path, ext):
    """Method that save a file on disk  
    Params: 
      file: base64 file
      name: string
      path: string
      ext: string
    """

    try:
        fh = open(path + name + ext, "wb")
        fh.write(b64decode(file))
        fh.close()
        return True
    except BaseException as e:
        raise CSTM_Exception(message="An error ocurred on uploading file",
                             status_code=400,
                             payload={"error": str(e)})

def validate_files(files, documentFiles):
    validFiles = []
    for file in files:
        if file in documentFiles:
            if not (files[file].filename and allowed_file(files[file].filename)):
                raise CSTM_Exception(message="File extension is not allowed",
                                status_code=400)
            validFiles.append({"field": file, "file": files[file]})
    return validFiles

def upload_files(files):
    uploaded_files = {}
    for file in files:
        filename = secure_filename(file['file'].filename)
        file['file'].save(os.path.join(files_path, filename))
        fileUrl = current_app.config.get('SERVER_URL') + '/resources/files/' + filename
        uploaded_files.update(
            {file['field']: {'name': filename, 'url':fileUrl }})
    return uploaded_files


    
def allowed_file(filename):
    
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowedExtensions


