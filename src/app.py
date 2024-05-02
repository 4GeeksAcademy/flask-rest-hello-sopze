"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os, signal, db_utils, tools, json
from flask import Flask, request, jsonify
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin

from models import db, User, Entity, EntityType, Bookmark # only 4 needed
import db_utils # didnt imported * from there because this way calls are d_utils.#func# in code so you know where they're implemented

### ----------------------------------------------------------------------------------------------- ###
### ---------------------------------------- INITIALIZATION --------------------------------------- ###
### ----------------------------------------------------------------------------------------------- ###

app = Flask(__name__)
app.url_map.strict_slashes = False
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/swapi.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

db.__ENTITYTYPEMAPS__= {}

### ----------------------------------------------------------------------------------------------- ###
### ------------------------------------------- GENERAL ------------------------------------------- ###
### ----------------------------------------------------------------------------------------------- ###

# api error handling
@app.errorhandler(APIException)
def handle_invalid_usage(error): return jsonify(error.to_dict()), error.status_code

# ---------------------------------------------------------------------------- ENDPOINT: /
# generate index page
@app.route('/')
def sitemap(): 
    rawnames= db.__ENTITYTYPEMAPS__['link2type'].keys() if db.__ENTITYTYPEMAPS__['link2type'] else None
    if rawnames:
        filterlinks= [f"/api/entity/{n}" for n in rawnames]
        return generate_sitemap(app, filterlinks)
    return generate_sitemap(app)

# ---------------------------------------------------------------------------- ENDPOINT: /dev/test
@app.route('/dev/test', methods=['GET'])
def api_code_test():
    txt="dev endpoint i used to test several things"
    print(txt)
    return db_utils.response(418, "I'm a teapot", txt)

# get API endpoints for each type
# ---------------------------------------------------------------------------- ENDPOINT: /api
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
    return db_utils.response_200(result)

### ----------------------------------------------------------------------------------------------- ###
### -------------------------------------------- USERS -------------------------------------------- ###
### ----------------------------------------------------------------------------------------------- ###

# ---------------------------------------------------------------------------- ENDPOINT: /dev/user
# get all user
# different route to denote this wouldn't be part of the public api
@app.route('/dev/user', methods=['GET'])
def user_getall():
    try:
        query= User.query.all()
        if not query:
            return db_utils.response(200, "no registered users")
        return db_utils.response_200([e.serialize() for e in query])
    except Exception as e:
        return db_utils.response_500(e.__repr__())

# ---------------------------------------------------------------------------- ENDPOINT: /api/user/<int:id>
# get user by username
@app.route('/api/user/<name>', methods=['GET'])
def user_get(name):
    try:
        result= User.query.filter_by(username=name).first()
        if not result:
            return db_utils.response(404, f"no such user with name: {name}")
        if result.username == "teapot":
            return db_utils.response(418, "i'm a teapot", result.serialize())
        return db_utils.response_200(result.serialize())
    except Exception as e:
        return db_utils.response_500(e.__repr__())

# ---------------------------------------------------------------------------- ENDPOINT: /api/user POST
# create new user
@app.route('/api/user', methods=['POST'])
def user_post():
    try:
        valid, data= db_utils.check_valid_json_body(request)
        if not valid: return data
        error= db_utils.check_missing_properties(data, db.__metacolumns__['users'])
        if error: return db_utils.response(400, f"Missing required property '{error}'")
        newuser= User(
            username=data['username'],
            displayname=data['displayname'],
            email=data['email'],
            password=data['password']
        )
        if User.query.filter_by(email=newuser.email).first(): return db_utils.response(400, "email already registered")
        elif User.query.filter_by(username=newuser.username).first(): return db_utils.response(400, "username already taken")
        else:
            db.session.add(newuser)
            db.session.commit()
            db_utils.refresh_entity_type_registry()
            return db_utils.response_200()
    except Exception as e:
        return db_utils.response_500(e.__repr__())

### ----------------------------------------------------------------------------------------------- ###
### ---------------------------------------- ENTITIY TYPES ---------------------------------------- ###
### ----------------------------------------------------------------------------------------------- ###

# ---------------------------------------------------------------------------- ENDPOINT: /api/entitytype
# get all entitytype
@app.route('/api/entitytype', methods=['GET'])
def entitytype_getall():
    try:
        result= EntityType.query.all()
        if not result:
            return db_utils.response(200, "no registered entity types")
        return db_utils.response_200([e.serialize() for e in result])
    except Exception as e:
        return db_utils.response_500(e.__repr__())

# ---------------------------------------------------------------------------- ENDPOINT: /api/entitytype/<int:id>
# get entitytype by _id or name
@app.route('/api/entitytype/<param>', methods=['GET'])
def entitytype_get(param):
    try:
        result= EntityType.query.get(int(param)) if param.isdigit() else EntityType.query.filter_by(name=param).first()
        if not result:
            return db_utils.response(404, f"no such entity type with id/name: {param}")
        return db_utils.response_200(result.serialize())
    except Exception as e:
        return db_utils.response_500(e.__repr__())

# ---------------------------------------------------------------------------- ENDPOINT: /api/entitytype POST
# create new entitytype
@app.route('/api/entitytype', methods=['POST'])
def entitytype_post():
    try:
        valid, data= db_utils.check_valid_json_body(request)
        if not valid: return data
        error= db_utils.check_missing_properties(data, db.__metacolumns__['entity_types'])
        if error: return db_utils.response(400, f"Missing required property '{error}'")
        newtype= EntityType(
            name=data['name'],
            link=data['link'] if 'link' in data else None,
            properties=data['properties']
        )
        if EntityType.query.filter_by(link=newtype.link).first(): return db_utils.response(400, "link is already in use")
        elif EntityType.query.filter_by(name=newtype.name).first(): return db_utils.response(400, "type name already registered")
        else: 
            db.session.add(newtype)
            db.session.commit()
            db_utils.refresh_entity_type_registry()
        return db_utils.response_200()
    except Exception as e:
        return db_utils.response_500(e.__repr__())

### ----------------------------------------------------------------------------------------------- ###
### ------------------------------------------- ENTITIES ------------------------------------------ ###
### ----------------------------------------------------------------------------------------------- ###

# ---------------------------------------------------------------------------- ENDPOINT: /api/entity
# get all entities
@app.route('/api/entity', methods=['GET'])
def entity_getall():
    try:
        result= Entity.query.all()
        if not result:
            return db_utils.response(200, "no registered entities")
        return db_utils.response_200([e.serialize() for e in result])
    except Exception as e:
        return db_utils.response_500(e.__repr__())

# ---------------------------------------------------------------------------- ENDPOINT: /api/entity  POST
# create new entities
@app.route('/api/entity', methods=['POST'])
def entity_post():
    try:
        valid, data= db_utils.check_valid_json_body(request)
        if not valid: return data
        error= db_utils.check_missing_properties(data, db.__metacolumns__['entities'], exceptions=["type_id"], additions=["type"])
        if error: return db_utils.response(400, f"Missing required property '{error}'")
        if not data['type'] in db.__ENTITYTYPEMAPS__['type2id']: return db_utils.response(400, "invalid entity type")
        newentity= Entity(
            name=data['name'],
            description= data['description'] if 'description' in data else "",
            type_id= db.__ENTITYTYPEMAPS__['type2id'][data['type']],
            properties= json.dumps(data['properties']) # dump properties to json string
        )
        if Entity.query.filter_by(name=newentity.name).first(): return db_utils.response(400, "entity name is already in use")
        else: 
            db.session.add(newentity)
            db.session.commit()
            db_utils.refresh_entity_type_registry()
        return db_utils.response_200()
    except Exception as e:
        return db_utils.response_500(e.__repr__())

# -------------------------------------------------- HELPERS
# get all entities of given type
def typedentity_getall(typename):
    try:
        _type_id= db.__ENTITYTYPEMAPS__["type2id"][typename]
        if not _type_id:
            return db_utils.response(404, f"no such entity type '{typename}'")
        result= Entity.query.filter_by(type_id=_type_id).all()
        if not result:
            return db_utils.response(404, f"no entities registered of type '{typename}")
        return db_utils.response_200([e.serialize() for e in result])
    except Exception as e:
        return db_utils.response_500(e.__repr__())

# get entity of given type and _tid
def typedentity_get(typename, tid):
    try:
        _type_id= db.__ENTITYTYPEMAPS__["type2id"][typename]
        if not _type_id:
            return db_utils.response(404, f"no such entity type '{typename}'")
        result= Entity.query.filter_by(type_id=_type_id,_tid=tid).first()
        if not result:
            return db_utils.response(404, f"no such entity '{typename}' with id: {tid}")
        return db_utils.response_200(result.serialize())
    except Exception as e:
        return db_utils.response_500(e.__repr__())

# ---------------------------------------------------------------------------- ENDPOINT: /api/entity/<type>
# get all entities of type 
@app.route('/api/entity/<type>', methods=['GET'])
def entity_getall_type(type):
    try:
        link= db.__ENTITYTYPEMAPS__["link2type"][type]
    except:
        return db_utils.response_400(f"invalid entity type: {type}")
    return typedentity_getall(link)

# ---------------------------------------------------------------------------- ENDPOINT: /api/entity/<type>/<id>
# get a single entity of type, by id
@app.route('/api/entity/<type>/<int:id>', methods=['GET'])
def entity_get_type(type, id):
    try:
        link= db.__ENTITYTYPEMAPS__["link2type"][type]
    except:
        return db_utils.response_400(f"invalid entity type: {type}")
    return typedentity_get(link, id)

### ----------------------------------------------------------------------------------------------- ###
### ------------------------------------------ BOOKMARKS ------------------------------------------ ###
### ----------------------------------------------------------------------------------------------- ###

# ---------------------------------------------------------------------------- ENDPOINT: /dev/bookmarks
# different route to denote this wouldn't be part of the public api
@app.route('/dev/bookmarks', methods=['GET'])
def bookmarks_getall():
    try:
        query= Bookmark.query.all()
        if not query:
            return db_utils.response(200, "no bookmarks")
        return db_utils.response_200([e.serialize() for e in query])
    except Exception as e:
        return db_utils.response_500(e.__repr__())

# ---------------------------------------------------------------------------- ENDPOINT: /api/user/bookmarks
# this one requires the token as a header
@app.route('/api/user/bookmarks', methods=['GET'])
def userbookmarks_getall():
    try:
        if not 'user-token' in request.headers:
            return db_utils.response(400, "missing token", "required header not present: name: 'user-token', content: a logged-in user session indentifier")
        usertoken= request.headers['user-token']
        query= Bookmark.query.filter_by(token=usertoken).first()
        if not query:
            return db_utils.response(400, "invalid token", "token does not point to any current user session")
        return db_utils.response_200([e.serialize() for e in query])
    except Exception as e:
        return db_utils.response_500(e.__repr__())

### ----------------------------------------------------------------------------------------------- ###
### -------------------------------------------- TOOLS -------------------------------------------- ###
### ----------------------------------------------------------------------------------------------- ###

# ---------------------------------------------------------------------------- ENDPOINT: /execute?toolid=<int>
@app.route('/execute', methods=['GET'])
def execute():
    try:
        id = request.args.get('tool', type=int)
        if not id:
            return db_utils.response(203, "nothing was executed") # fail silently
        result= tools.execute_tool(id)
        if result > 0:
            db_utils.perform_database_rowcount()
            if result== 2: db_utils.refresh_entity_type_registry()
        return db_utils.response(203, "executed")
    except Exception as e:
        return db_utils.response_500(e.__repr__())

### ----------------------------------------------------------------------------------------------- ###
### ---------------------------------------- MAIN + STARTUP --------------------------------------- ###
### ----------------------------------------------------------------------------------------------- ###

# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)

# very early initialization depending on running mode
with app.app_context():

    # only if ran through 'flask db run' (what pipenv run start does)
    if db_utils.__RUNNING_MODE__ == 'normal':
        db.__rowcounts__= {}
        db_utils.proccess_columns_metadata()
        print("\033[F\033[F")
        db_utils.perform_database_rowcount()

        # fill database on startup if FULLY empty (and if configured to)
        if db_utils.__DB_AUTOFILL__ and db.__rowcounts__['total']==0:
            db_utils.load_rows_from_file(db_utils.__DB_DEFAULTS_FILE__)
        
        db_utils.refresh_entity_type_registry()
    else:
        if db_utils.__RUNNING_MODE__ == 'wipedb':
            tools.database_wipe()
            os.kill(os.getpid(), signal.SIGTERM)