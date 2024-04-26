"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap, clear_database_records
from admin import setup_admin
from models import db, User, Entity, Bookmark

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

 # push the context, otherwise jsonify doesnt work on root level (__RESPONSE_XXX declarations)
app.app_context().push()

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

__CONTENT_TYPE= {'Content-Type': 'application/json'}

__RESPONSE_400= jsonify({ "message": "400 BAD REQUEST" }), 400, __CONTENT_TYPE
__RESPONSE_500= jsonify({ "message": "500 SERVER ERROR" }), 500, __CONTENT_TYPE

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)

# destroys the entire database, also drops ALL tables
@app.route('/db/wipe', methods=['GET'])
def database_wipe():
    db.reflect()
    db.drop_all()
    db.session.commit()
    return jsonify({"message":"ok" }), 200, __CONTENT_TYPE

# this is just for not having to manually create them xd
@app.route('/db/reset', methods=['GET'])
def database_reset():
    for table in reversed(db.metadata.sorted_tables):
        db.session.execute(table.delete())
    db.session.add(User(username="defaultuser", email="default@email.com", password="1234"))
    db.session.add(User(username="teapot", email="teapot@jemail.com", password="imateapot1998"))
    db.session.add(User(username="elmandangas", email="mandangas69hotpenis@jemail.com", password="5678"))
    db.session.add(User(username="almejitafresca", email="ginebraenmivagina@jemail.com", password="abcd"))
    db.session.commit()
    return jsonify({"message":"ok" }), 200, __CONTENT_TYPE

### -------------------------------- USERS -------------------------------- ###

@app.route('/dev/users', methods=['GET'])
def user_getall():
    try:
        query= User.query.all()
        if not query:
            return jsonify({ "message": f"no registered users" }), 204, __CONTENT_TYPE
        return jsonify({"message":"ok", "result":[e.serialize() for e in query]}), 200, __CONTENT_TYPE
    except:
        return __RESPONSE_500

@app.route('/dev/user/<int:id>', methods=['GET'])
def user_get(id):
    try:
        user= User.query.get(id)
        if not user:
            return jsonify({ "message": f"no such user with id: {id}" }), 404, __CONTENT_TYPE
        if user.username == "teapot":
            return jsonify({ "message": "i'm a teapot" }), 418, __CONTENT_TYPE # easter egg xd
        return jsonify({"message":"ok", "result":User.query.get(id).serialize() }), 200, __CONTENT_TYPE
    except:
        return __RESPONSE_500

### GET API ENDPOINTS ###
# (required by my starwars page)

@app.route('/api', methods=['GET'])
def apimap():
    result= {
        "films": f"/api/entity/films", 
        "people": f"/api/entity/people", 
        "planets": f"/api/entity/planets", 
        "species": f"/api/entity/species", 
        "starships": f"/api/entity/starships", 
        "vehicles": f"/api/entity/vehicles"
    }
    return jsonify({"message":"ok", "result":result }), 200, __CONTENT_TYPE

### -------------------------------- ENTITIES -------------------------------- ###

@app.route('/api/entity', methods=['GET'])
def entity_getall():
    result= Entity.query.all()
    if not result:
        return jsonify({ "message": f"no registered entities" }), 200, __CONTENT_TYPE
    return jsonify({"message":"ok", "result":[e.serialize() for e in result]}), 200, __CONTENT_TYPE

@app.route('/api/entity/<int:id>', methods=['GET'])
def entity_get(id):
    try:
        result= Entity.query.get(id)
        if not result:
            return jsonify({ "message": f"no such entity with id: {id}" }), 404, __CONTENT_TYPE
        return jsonify({"message":"ok", "result":result.serialize()}), 200, __CONTENT_TYPE
    except:
        return __RESPONSE_500
    
def entitytype_getall(ptype):
    result= Entity.query.filter_by(type=ptype).all()
    if not result:
        return jsonify({ "message": f"no such entities of type '{ptype}'" }), 404, __CONTENT_TYPE
    return jsonify({"message":"ok", "result":[e.serialize() for e in result]}), 200, __CONTENT_TYPE

def entitytype_get(ptype, id):
    try:
        result= Entity.query.filter_by(type=ptype).get(id)
        if not result:
            return jsonify({ "message": f"no such entity '{ptype}' with id: {id}" }), 404, __CONTENT_TYPE
        return jsonify({"message":"ok", "result":result.serialize()}), 200, __CONTENT_TYPE
    except:
        return __RESPONSE_500

### -------------------------------- FILMS -------------------------------- ###

@app.route('/api/entity/films', methods=['GET'])
def entity_getall_film():
    return entitytype_getall("film")

@app.route('/api/entity/films/<int:id>', methods=['GET'])
def entity_get_film(id):
    return entitytype_get("film", id)

### -------------------------------- PEOPLE -------------------------------- ###

@app.route('/api/entity/people', methods=['GET'])
def entity_getall_people():
    return entitytype_getall("people")

@app.route('/api/entity/people/<int:id>', methods=['GET'])
def entity_get_people(id):
    return entitytype_get("people", id)

### -------------------------------- PLANETS -------------------------------- ###

@app.route('/api/entity/planets', methods=['GET'])
def entity_getall_planet():
    return entitytype_getall("planet")

@app.route('/api/entity/planets/<int:id>', methods=['GET'])
def entity_get_planet(id):
    return entitytype_get("planet", id)

### -------------------------------- SPECIES -------------------------------- ###

@app.route('/api/entity/species', methods=['GET'])
def entity_getall_species():
    return entitytype_getall("species")

@app.route('/api/entity/species/<int:id>', methods=['GET'])
def entity_get_species(id):
    return entitytype_get("species", id)

### -------------------------------- STARSHIPS -------------------------------- ###

@app.route('/api/entity/starships', methods=['GET'])
def entity_getall_starship():
    return entitytype_getall("starship")

@app.route('/api/entity/starships/<int:id>', methods=['GET'])
def entity_get_starship(id):
    return entitytype_get("starship", id)

### -------------------------------- VEHICLES -------------------------------- ###

@app.route('/api/entity/vehicles', methods=['GET'])
def entity_getall_vehicle():
    return entitytype_getall("vehicle")

@app.route('/api/entity/vehicles/<int:id>', methods=['GET'])
def entity_get_vehicle(id):
    return entitytype_get("vehicle", id)

### -------------------------------- BOOKMARKS -------------------------------- ###

# this one requires the userid as parameter in the BODY as userid=<int>, no URL params
@app.route('/api/user/bookmarks', methods=['GET'])
def userbookmarks_getall():
    try:
        if not request or not request.data:
            return jsonify({ "message": "missing body, this endpoint requires body= { \"userid\": <int> }" }), 400, __CONTENT_TYPE
        json = request.get_json(force=True)
        if not json or not json.userid:
            return jsonify({ "message": "no 'userid' given, this endpoint requires body= { \"userid\": <int> }" }), 400, __CONTENT_TYPE
        query= Bookmark.query.filter_by(user_id= json.userid).all()
        return jsonify({"message":"ok", "result":[e.serialize() for e in query]}), 200, __CONTENT_TYPE
    except:
        return __RESPONSE_500

# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
