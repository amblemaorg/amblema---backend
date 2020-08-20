from setuptools import setup

setup(
    name='amblema',
    author='BinauralDev',
    version='0.1',
    description='Services for amblema application',
    url='',
    install_requires=[
        'flask',
        'flask-cors',
        'flask-mongoengine',
        'flask_restful',
        'PyJWT',
        'flask-jwt-extended',
        'flask-bcrypt',
        'coverage',
        'marshmallow',
        'blinker',
        'Flask-Script',
        'flask-compress',
        'Pillow'    
    ]
)
