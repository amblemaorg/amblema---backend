# AmbLeMa - Backend
## Correr por primera vez en local
1. Correr bd mongo del proyecto https://gitlab.binauraldev.com/binaural/proyectos/backend/custom/db/amblema---db.git  
2. Correr el siguiente comando para crear la bd local: `docker exec -i amblema_mongodb bash -c "mongo -u root -p garden86 --eval \"db.getSiblingDB('amblema').createUser({user: 'amblema',pwd: 'garden86',roles: [{role: 'readWrite',db: 'amblema'}]})\""`  
3. Importar bd de producción  

## Correr en local
1. Crear o sobreescribir el archivo .env con la siguiente informacion:  
INSTANCE=development  
BACK_PORT=10505  
DB_URL=mongodb://amblema:garden86@mongo:27017/amblema  
TESTING_DB_URL=mongodb://amblema:garden86@mongo:27017/amblema_testing  
SERVER_URL=http://localhost:10505  
JWT_SECRET_KEY=someamblemakey  
DB_NETWORK=amblema---db_db_network  
SMTP_USERNAME=AKIAUWIPZVS7AXY7FPNT  
SMTP_PASSWORD=BGxWko2RkC/JqPwgq57pxJbH4qlwlmyCu1NCK2NHr6vq  
SMTP_FROM=info.fixerfriend@gmail.com  
SMTP_HOST=email-smtp.us-east-1.amazonaws.com  
SMTP_PORT=587  

2. Correr proyecto en docker con el comando `docker-compose up`   
