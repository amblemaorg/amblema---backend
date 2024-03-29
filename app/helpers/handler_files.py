# app/helpers/handler_files.py


from base64 import b64decode
from flask import current_app
import os
from mimetypes import guess_extension, guess_type
from pathlib import Path

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
        Path(path).mkdir(parents=True, exist_ok=True)
        fh = open(path + name + ext, "wb")
        fh.write(b64decode(file+"======="))
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
            #if documentFiles[file]['size']:
                #print(files[file].read())
                #files[file].save('/tmp/foo')
                #size = os.stat('/tmp/foo').st_size / 1024 
                #print(size)
                #if size > documentFiles[file]['size']:
                #    raise CSTM_Exception(
                #        message="File size is not allowed. Max size: {} KB".format(documentFiles[file]['size']),
                #        status_code=400)
            validFiles.append({"field": file, "file": files[file]})
    return validFiles


def upload_files(files, folder=''):
    uploaded_files = {}
    for file in files:
        filename = secure_filename(file['file'].filename)
        if folder:
            path = files_path + '/' + folder
        else:
            path = files_path
        Path(path).mkdir(parents=True, exist_ok=True)
        file['file'].save(os.path.join(path, filename))
        fileUrl = '/resources/files/' + \
            ((folder+'/') if folder else folder) + filename

        uploaded_files.update(
            {file['field']: {'name': filename, 'url': fileUrl}})
    return uploaded_files


def allowed_file(filename):

    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowedExtensions
