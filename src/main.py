"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, Users, Bookmarks, Characters, Planets
import json
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, JWTManager
#from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_CONNECTION_STRING')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)


            ##### Inicio POST #####

#Creamos un nuevo usuario
@app.route('/users/new', methods=['POST'])
def add_new_user():
    body = json.loads(request.data)
    user_exist = Users.query.filter_by(email=body["email"]).first()

    for i in body:
        if body[i] == None:
            raise APIException('Hay campos vacíos', status_code=404)
    
    if user_exist is None:
        new_user = Users(
            username=body["username"],
            password=body["password"],
            first_name=body["first_name"],
            last_name=body["last_name"],
            email=body["email"],
            is_active=1)
        db.session.add(new_user)
        db.session.commit()
        response_body = {"message": "Usuario creado con éxito"}
        return jsonify(response_body), 200

    raise APIException('Ya existe un usuario con ese email', status_code=403)

#Creamos un nuevo favorito
@app.route('/user/bookmarks/new', methods=['POST'])
def add_new_bookmark():
    body = json.loads(request.data)
    user_exist = Bookmarks.query.filter_by(user_id=body["user_id"]).first()
    character_exist = Bookmarks.query.filter_by(character_id=body["character_id"]).first()
    planet_exist = Bookmarks.query.filter_by(planet_id=body["planet_id"]).first()    

    if user_exist is None:
        raise APIException('El usuario no existe', status_code=404)

    if body["character_id"] != None:
        if character_exist != None:
            if character_exist.character_id == int(body["character_id"]):
                raise APIException('El usuario ya tiene ese personaje como favorito', status_code=403)

    if body["planet_id"] != None:
        if planet_exist != None:
            if planet_exist.planet_id == int(body["planet_id"]):
                raise APIException('El usuario ya tiene ese planeta como favorito', status_code=403)

    new_user_bookmark = Bookmarks(
        user_id=body["user_id"],
        character_id=body["character_id"],
        planet_id=body["planet_id"])
    db.session.add(new_user_bookmark)
    db.session.commit()
    response_body = {"message": "Favorito creado con éxito"}
    return jsonify(response_body), 200

#Creamos un nuevo personaje
@app.route('/characters/new', methods=['POST'])
def add_new_character():
    body = json.loads(request.data)
    character_exist = Characters.query.filter_by(name=body["name"]).first()

    for i in body:
        if body[i] == None:
            raise APIException('Hay campos vacíos', status_code=404)

    if character_exist is None:
        new_character = Characters(
            name=body["name"],
            birth_year=body["birth_year"],
            gender=body["gender"],
            height=body["height"],
            skin_color=body["skin_color"],
            eye_color=body["eye_color"])
        db.session.add(new_character)
        db.session.commit()
        response_body = {"message": "Personaje creado con éxito"}
        return jsonify(response_body), 200

    raise APIException('Ya existe un personaje con ese nombre', status_code=403)

#Creamos un nuevo planeta
@app.route('/planets/new', methods=['POST'])
def add_new_planet():
    body = json.loads(request.data)
    planet_exist = Planets.query.filter_by(name=body["name"]).first()

    for i in body:
        if body[i] == None:
            raise APIException('Hay campos vacíos', status_code=404)

    if planet_exist is None:
        new_planet = Planets(
            name=body["name"],
            climate=body["climate"],
            diameter=body["diameter"],
            orbital_period=body["orbital_period"],
            rotation_period=body["rotation_period"],
            population=body["population"])
        db.session.add(new_planet)
        db.session.commit()
        response_body = {"message": "Planeta creado con éxito"}
        return jsonify(response_body), 200

    raise APIException('Ya existe un planeta con ese nombre', status_code=403)

            ##### Fin POST #####

            ##### Inicio GET #####

#Obtenemos todos los usuarios
@app.route('/users', methods=['GET'])
def get_all_users():
    users = Users.query.all() # esto obtiene todos los registros de la tabla User

    if users is None:
        raise APIException('No existen usuarios', status_code=404)

    results = list(map(lambda item: item.serialize(), users)) #esto serializa los datos del arrays users

    return jsonify(results), 200

#Obtenemos un usuario dependiendo de su ID
@app.route('/user/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = Users.query.filter_by(id=user_id).first()

    if user is None:
        raise APIException('El usuario ingresado no existe', status_code=404)

    return jsonify(user.serialize()), 200

#Obtenemos todos los favoritos de un usuario
@app.route('/user/<int:user_id>/bookmarks', methods=['GET'])
def get_all_user_bookmarks(user_id):
    bookmarks = Bookmarks.query.filter_by(user_id=user_id).all() # esto obtiene todos los registros de la tabla User
    
    if bookmarks is None:
        raise APIException('El usuario no tiene favoritos', status_code=404)

    results = list(map(lambda item: item.serialize(), bookmarks)) #esto serializa los datos del arrays users

    return jsonify(results), 200

#Obtenemos un favorito dependiendo de la ID del usuario y de la ID del favorito
@app.route('/user/<int:user_id>/bookmark/<int:bookmark_id>', methods=['GET'])
def get_one_user_bookmark(user_id, bookmark_id):
    bookmark = Bookmarks.query.filter_by(id=bookmark_id).first()

    if bookmark is None:
        raise APIException('El favorito ingresado no existe', status_code=404)
    if bookmark.user_id != bookmark_id:
        raise APIException('El favorito no pertenece al usuario ingresado', status_code=404)

    return jsonify(bookmark.serialize()), 200

#Obtenemos todos los personajes
@app.route('/characters', methods=['GET'])
def get_all_characters():
    characters = Characters.query.all() # esto obtiene todos los registros de la tabla User

    if characters is None:
        raise APIException('No existen personajes', status_code=404)

    results = list(map(lambda item: item.serialize(), characters)) #esto serializa los datos del arrays users

    return jsonify(results), 200

#Obtenemos un personaje dependiendo de su ID
@app.route('/character/<int:character_id>', methods=['GET'])
def get_character(character_id):
    character = Characters.query.filter_by(id=character_id).first()

    if character is None:
        raise APIException('El personaje ingresado no existe', status_code=404)

    return jsonify(character.serialize()), 200

#Obtenemos todos los planetas
@app.route('/planets', methods=['GET'])
def get_all_planets():
    planets = Planets.query.all() # esto obtiene todos los registros de la tabla User

    if planets is None:
        raise APIException('No existen planetas', status_code=404)

    results = list(map(lambda item: item.serialize(), planets)) #esto serializa los datos del arrays users

    return jsonify(results), 200

#Obtenemos un planeta dependiendo de su ID
@app.route('/planet/<int:planet_id>', methods=['GET'])
def get_planet(planet_id):
    planet = Planets.query.filter_by(id=planet_id).first()

    if planet is None:
        raise APIException('El planeta ingresado no existe', status_code=404)

    return jsonify(planet.serialize()), 200

            ##### Fin GET #####

           ##### Inicio PUT #####

#Actualizamos un usuario dependiendo de su ID
@app.route('/users/update/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    body = json.loads(request.data)

    user = Users.query.filter_by(id=user_id).first()
    username_exist = Users.query.filter_by(username=body["username"]).first()
    email_exist = Users.query.filter_by(email=body["email"]).first()

    if user is None:
        raise APIException('El usuario ingresado no existe', status_code=404)
    if not username_exist is None:
        raise APIException('Ya existe otro usuario con ese nick', status_code=403)
    if not email_exist is None:
        raise APIException('Ya existe otro usuario con ese email', status_code=403)

    if "username" in body:
        user.username = body["username"]
    if "password" in body:
        user.password = body["password"]
    if "first_name" in body:
        user.first_name = body["first_name"]
    if "last_name" in body:
        user.last_name = body["last_name"]
    if "email" in body:
        user.email = body["email"]
    if "is_active" in body:
        user.is_active = body["is_active"]
    
    db.session.commit()
    response_body = {"message": "Usuario actualizado con éxito"}
    return jsonify(response_body), 200

#Actualizamos un personaje dependiendo de su ID
@app.route('/characters/update/<int:character_id>', methods=['PUT'])
def update_character(character_id):
    body = json.loads(request.data)
    
    character = Characters.query.filter_by(id=character_id).first()
    name_exist = Characters.query.filter_by(name=body["name"]).first()

    if character is None:
        raise APIException('El personaje ingresado no existe', status_code=404)
    if not name_exist is None:
        raise APIException('Ya existe otro personaje con ese nombre', status_code=403)

    if "name" in body:
        character.name = body["name"]
    if "birth_year" in body:
        character.birth_year = body["birth_year"]
    if "gender" in body:
        character.gender = body["gender"]
    if "height" in body:
        character.height = body["height"]
    if "skin_color" in body:
        character.skin_color = body["skin_color"]
    if "eye_color" in body:
        character.eye_color = body["eye_color"]
    
    db.session.commit()
    response_body = {"message": "Personaje actualizado con éxito"}
    return jsonify(response_body), 200

#Actualizamos un planeta dependiendo de su ID
@app.route('/planets/update/<int:planet_id>', methods=['PUT'])
def update_planet(planet_id):
    body = json.loads(request.data)
    
    planet = Planets.query.filter_by(id=planet_id).first()
    name_exist = Planets.query.filter_by(name=body["name"]).first()

    if planet is None:
        raise APIException('El planeta ingresado no existe', status_code=404)
    if not name_exist is None:
        raise APIException('Ya existe otro planeta con ese nombre', status_code=403)

    if "name" in body:
        planet.name = body["name"]
    if "climate" in body:
        planet.climate = body["climate"]
    if "diameter" in body:
        planet.diameter = body["diameter"]
    if "orbital_period" in body:
        planet.orbital_period = body["orbital_period"]
    if "rotation_period" in body:
        planet.rotation_period = body["rotation_period"]
    if "population" in body:
        planet.population = body["population"]
    
    db.session.commit()
    response_body = {"message": "Planeta actualizado con éxito"}
    return jsonify(response_body), 200

           ##### Fin PUT #####

           ##### Inicio DELETE #####

#Eliminamos un usuario dependiendo de su ID
@app.route('/users/delete/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = Users.query.filter_by(id=user_id).first()

    if user is None:
        raise APIException('El usuario ingresado no existe', status_code=404)

    db.session.delete(user)
    db.session.commit()
    response_body = {"message": "Usuario "+user.username+" eliminado con éxito"}
    return jsonify(response_body), 200

#Eliminamos un favorito dependiendo de su ID
@app.route('/bookmarks/delete/<int:bookmark_id>', methods=['DELETE'])
def delete_bookmark(bookmark_id):
    bookmark = Bookmarks.query.filter_by(id=bookmark_id).first()
    
    if bookmark is None:
        raise APIException('El favorito no existe', status_code=404)

    db.session.delete(bookmark)
    db.session.commit()
    response_body = {"message": "Favorito eliminado con éxito"}
    return jsonify(response_body), 200

#Eliminamos un personaje dependiendo de su ID
@app.route('/characters/delete/<int:character_id>', methods=['DELETE'])
def delete_character(character_id):
    character = Characters.query.filter_by(id=character_id).first()
    
    if character is None:
        raise APIException('El personaje ingresado no existe', status_code=404)

    db.session.delete(character)
    db.session.commit()
    response_body = {"message": "Personaje "+character.name+" eliminado con éxito"}
    return jsonify(response_body), 200

#Eliminamos un planeta dependiendo de su ID
@app.route('/planets/delete/<int:planet_id>', methods=['DELETE'])
def delete_planet(planet_id):
    planet = Planets.query.filter_by(id=planet_id).first()
    
    if planet is None:
        raise APIException('El planeta ingresado no existe', status_code=404)

    db.session.delete(planet)
    db.session.commit()
    response_body = {"message": "Planeta "+planet.name+" eliminado con éxito"}
    return jsonify(response_body), 200
           ##### Fin DELETE #####

           ##### Inicio JWT #####

# Setup the Flask-JWT-Extended extension
app.config["JWT_SECRET_KEY"] = "super-secret"  # Change this!
jwt = JWTManager(app)

# Create a route to authenticate your users and return JWTs. The
# create_access_token() function is used to actually generate the JWT.
@app.route("/login", methods=["POST"])
def login():
    username = request.json.get("username", None)
    password = request.json.get("password", None)

    user = Users.query.filter_by(username=username).first()

    if user is None:
        raise APIException('El usuario ingresado no existe', status_code=401)

    if username != user.username or password != user.password:
        raise APIException('Usuario o contraseña incorrectos', status_code=401)

    access_token = create_access_token(identity=username)
    response_body = {
        "access_token": access_token,
        "user": user.serialize()
    }
    return jsonify(response_body)


# Protect a route with jwt_required, which will kick out requests
# without a valid JWT present.
@app.route("/profile", methods=["GET"])
@jwt_required()
def profile():
    # Access the identity of the current user with get_jwt_identity
    current_user = get_jwt_identity()

    user = Users.query.filter_by(username=current_user).first()

    if user is None:
        raise APIException('No tienes permitido hacer esto', status_code=401)

    response_body = {
        "user": user.serialize()
    }
    return jsonify(response_body), 200

# Protect a route with jwt_required, which will kick out requests
# without a valid JWT present.
@app.route("/isauth", methods=["GET"])
@jwt_required()
def is_auth():
    return jsonify(get_jwt_identity()), 200
           ##### Fin JWT #####

# this only runs if `$ python src/main.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
