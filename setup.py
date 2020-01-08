from setuptools import setup

setup(
    name='fvac',
    author='Greudys Godoy',
    version='0.1',
    description='Services for FVAC application',
    url='',
    install_requires = [
        'flask',
        'flask-cors',
        'flask-mongoengine',
        'flask_restful',
        'PyJWT',
        'flask-jwt-extended',
        'flask-bcrypt',
        'coverage'
    ]
)
