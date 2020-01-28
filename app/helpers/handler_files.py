# app/helpers/handler_files.py


from base64 import b64decode

from app.helpers.error_helpers import CSTM_Exception

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