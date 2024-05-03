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

### ----------------------------------------------------------------------------------------------- ###
### -------------------------------------------- LOGIN -------------------------------------------- ###
### ----------------------------------------------------------------------------------------------- ###

# ---------------------------------------------------------------------------- ENDPOINT: /login POST
# basic login
@app.route('/login', methods=['POST'])
def login():
    try:
        error, data= db_utils.check_valid_json_body(request)
        if error: return db_utils.response(400, error)
        error= db_utils.check_missing_properties_manual(data, ['account', 'password'])
        if error: return db_utils.response(400, error)
        account= data['account']
        user= User.query.filter_by(email=account, password=data['password']).first()
        if not user:
            user= User.query.filter_by(username=account, password=data['password']).first()
        if not user:
            return db_utils.response(400, "invalid account or password")
        token= db_utils.generate_token()
        user.user_token= token
        db.session.commit()
        return db_utils.response_200(token)
    except Exception as e:
        return db_utils.response_500(e.__repr__())

# ---------------------------------------------------------------------------- ENDPOINT: /logout [TOKEN] POST
# basic logout
@app.route('/logout', methods=['POST'])
def logout():
    try:
        error, user= db_utils.check_valid_auth(request)
        if error: return db_utils.response(400, error)
        user.user_token= None
        db.session.commit()
        return db_utils.response_200()
    except Exception as e:
        return db_utils.response_500(e.__repr__())

# ---------------------------------------------------------------------------- ENDPOINT: /me GET
# gets yourself
@app.route('/me', methods=['GET'])
def me():
    try:
        error, user= db_utils.check_valid_auth(request)
        if error: return db_utils.response(400, error)
        return db_utils.response_200(user.serialize())
    except Exception as e:
        return db_utils.response_500(e.__repr__())

### ----------------------------------------------------------------------------------------------- ###
### -------------------------------------------- USERS -------------------------------------------- ###
### ----------------------------------------------------------------------------------------------- ###

# ---------------------------------------------------------------------------- ENDPOINT: /api/user POST
# create new user
@app.route('/api/user', methods=['POST'])
def user_post():
    try:
        error, data= db_utils.check_valid_json_body(request)
        if error: return db_utils.response(400, error)
        error= db_utils.check_missing_properties(data, db.__metacolumns__['users'])
        if error: return db_utils.response(400, error)

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
            db_utils.perform_database_rowcount()
            return db_utils.response_200()
    except Exception as e:
        return db_utils.response_500(e.__repr__())

# ---------------------------------------------------------------------------- ENDPOINT: /api/user [TOKEN] DELETE
# requires TOKEN
# delete user
@app.route('/api/user', methods=['DELETE'])
def user_delete():
    try:
        error, user= db_utils.check_valid_auth(request)
        if error: return db_utils.response(400, error)
        db.session.delete(user)
        db.session.commit()
        db_utils.perform_database_rowcount()
        return db_utils.response_200()
    except Exception as e:
        return db_utils.response_500(e.__repr__())

# ---------------------------------------------------------------------------- ENDPOINT: /api/user/<int:id> GET
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

### ----------------------------------------------------------------------------------------------- ###
### ------------------------------------------ BOOKMARKS ------------------------------------------ ###
### ----------------------------------------------------------------------------------------------- ###

# ---------------------------------------------------------------------------- ENDPOINT: /api/bookmark[?id] [TOKEN] POST
# requires TOKEN
# toggle user bookmark, (only creates if ?id param given, also, with ?id param body is not required)
@app.route('/api/bookmark', methods=['POST'])
def userbookmark_post():
    try:
        error, user= db_utils.check_valid_auth(request)
        if error: return db_utils.response(400, error)

        id = request.args.get('id', type=int)
        if not id:
            error, data= db_utils.check_valid_json_body(request)
            if error: return db_utils.response(400, error)

            error= db_utils.check_missing_properties(data, db.__metacolumns__['bookmarks'], exceptions=["user_id"])
            if error: return db_utils.response(400, error)

            query= Bookmark.query.filter_by(user_id=user._id).first()
            if not query: # add it
                error, id= db_utils.get_json_id(data, 'entity_id')
                if error: return db_utils.response(400, error)
                entity= Entity.query.get(id)
                if not entity: return db_utils.response(400, f"no such entity with ID {id}")
                newbookmark= Bookmark(
                    user_id=user._id,
                    entity_id= id
                )
                db.session.add(newbookmark)
                db.session.commit()
                db_utils.perform_database_rowcount()
                return db_utils.response(200, "added")
            db.session.delete(query)
            db.session.commit()
            db_utils.perform_database_rowcount()
            return db_utils.response(200, "removed")
        else:
            bookmark= Bookmark.query.filter_by(user_id=user._id, entity_id=id).first()
            if bookmark: return db_utils.response(400, f"user {user.username} has already bookmarked entity with ID {id}")
            newbookmark= Bookmark(
                user_id=user._id,
                entity_id= id
            )
            db.session.add(newbookmark)
            db.session.commit()
            db_utils.perform_database_rowcount()
            return db_utils.response(200, "added")
    except Exception as e:
        return db_utils.response_500(e.__repr__())

# ---------------------------------------------------------------------------- ENDPOINT: /api/bookmark[?id] [TOKEN] DELETE
# requires TOKEN
# delete all user bookmarks, (only one if ?id param given)
@app.route('/api/bookmark', methods=['DELETE'])
def userbookmark_deleteall():
    try:
        error, user= db_utils.check_valid_auth(request)
        if error: return db_utils.response(400, error)
        id = request.args.get('id', type=int)
        if not id:
            query= Bookmark.query.filter_by(user_id=user._id).all()
            if not query: return db_utils.response(200, f"no bookmarks for user '{user.username}'")
            db.session.delete(query)
            db.session.commit()
            db_utils.perform_database_rowcount()
        bookmark= Bookmark.query.filter_by(user_id=user._id, entity_id=id).first()
        if not bookmark: return db_utils.response(400, f"user '{user.username}' has not bookmarked entity with ID {id}")
        db.session.delete(bookmark)
        db.session.commit()
        db_utils.perform_database_rowcount()
        return db_utils.response_200()
    except Exception as e:
        return db_utils.response_500(e.__repr__())

# ---------------------------------------------------------------------------- ENDPOINT: /api/bookmark[?id] [TOKEN] GET
# requires TOKEN
# get all user bookmarks, (get true/false str of a single bookmark if ?id param given)
@app.route('/api/bookmark', methods=['GET'])
def userbookmark_getall():
    try:
        error, user = db_utils.check_valid_auth(request)
        if error: return db_utils.response(400, error)
        id = request.args.get('id', type=int)
        if not id:
            query= Bookmark.query.filter_by(user_id=user._id).all()
            if not query: return db_utils.response(200, f"no bookmarks for user '{user.username}'")
            return db_utils.response_200([e.serialize() for e in query])
        bookmark= Bookmark.query.filter_by(user_id=user._id, entity_id=id).first()
        return db_utils.response(200, "true" if bookmark else "false")
    except Exception as e:
        return db_utils.response_500(e.__repr__())

### ----------------------------------------------------------------------------------------------- ###
### ---------------------------------------- ENTITIY TYPES ---------------------------------------- ###
### ----------------------------------------------------------------------------------------------- ###

# ---------------------------------------------------------------------------- ENDPOINT: /api/entitytype POST
# create new entitytype
@app.route('/api/entitytype', methods=['POST'])
def entitytype_post():
    try:
        error, data= db_utils.check_valid_json_body(request)
        if error: return db_utils.response(400, error)
        error= db_utils.check_missing_properties(data, db.__metacolumns__['entity_types'])
        if error: return db_utils.response(400, error)

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
            db_utils.perform_database_fullcount()
        return db_utils.response_200()
    except Exception as e:
        return db_utils.response_500(e.__repr__())

# ---------------------------------------------------------------------------- ENDPOINT: /api/entitytype?id DELETE
# delete an entitytype (if no entities using it)
@app.route('/api/entitytype', methods=['DELETE'])
def entitytype_get():
    try:
        id = request.args.get('id', type=int)
        if not id: return db_utils.response(400, "missing required parameter id")
        entitytype = EntityType.query.get(id)
        if not entitytype: return db_utils.response(400, f"no such entity_type with ID {id}")
        query= Entity.query.filter_by(type_id=id).count()
        if query > 0: return db_utils.response(400, "unable to delete entity_type while it has entities using it")
        db.session.delete(entitytype)
        db.session.commit()
        db_utils.perform_database_fullcount()
    except Exception as e:
        return db_utils.response_500(e.__repr__())

# ---------------------------------------------------------------------------- ENDPOINT: /api/entitytype GET
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

### ----------------------------------------------------------------------------------------------- ###
### ------------------------------------------- ENTITIES ------------------------------------------ ###
### ----------------------------------------------------------------------------------------------- ###

# ---------------------------------------------------------------------------- ENDPOINT: /api/entity POST
# create new entity
@app.route('/api/entity', methods=['POST'])
def entity_post():
    try:
        error, data= db_utils.check_valid_json_body(request)
        if error: return db_utils.response(400, error)
        error= db_utils.check_missing_properties(data, db.__metacolumns__['entities'], remaps=[{"type_id", "type"}])
        if error: return db_utils.response(400, error)

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
            db_utils.perform_database_rowcount()
        return db_utils.response_200()
    except Exception as e:
        return db_utils.response_500(e.__repr__())

# this was taking too long, i'll eventually finish this but not now xD
# ---------------------------------------------------------------------------- ENDPOINT: /api/entity PUT
# modify an entity
#@app.route('/api/entity', methods=['PUT'])
#def entity_put():
#    try:
#        error, data= db_utils.check_valid_json_body(request)
#        if error: return db_utils.response(400, error)
#        error, id= db_utils.get_json_id(data)
#        if error: return db_utils.response(400, error)
#
#        entity= Entity.query.get(id)
#        if not entity: return db_utils.response(400, f"no entity with ID '{id}'")
#
#        error= db_utils.check_invalid_properties(data, db.__metacolumns__['entities'], remaps={"type_id","type"})
#        if error: return db_utils.response(400, error) .response(400, f"Invalid property '{error}'")
#        if 'type' in data and not data['type'] in db.__ENTITYTYPEMAPS__['type2id']: return db_utils.response(400, "invalid entity type")
#
#        entity= Entity.query.get(id)
#        if not entity: return db_utils.response(400, f"no such entity with ID {id}")
#
#        print(entity.keys())
#        
#        return db_utils.response_200()
#    except Exception as e:
#        return db_utils.response_500(e.__repr__())

# ---------------------------------------------------------------------------- ENDPOINT: /api/entity?id DELETE
# delete an entity
@app.route('/api/entity', methods=['DELETE'])
def entity_delete(type, id):
    try:
        id = request.args.get('id', type=int)
        if not id: return db_utils.response(400, "missing required parameter id")
        entity = Entity.query.get(id)
        if not entity: return db_utils.response(400, f"no such entity with ID {id}")
        db.session.delete(entity)
        db.session.commit()
        db_utils.perform_database_rowcount()
        return db_utils.response_400(f"invalid entity type: {type}")
    except Exception as e:
        return db_utils.response_500(e.__repr__())

# ---------------------------------------------------------------------------- ENDPOINT: /api/entity GET
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

# ---------------------------------------------------------------------------- ENDPOINT: /api/entity/<type> GET
# get all entities of type
@app.route('/api/entity/<type>', methods=['GET'])
def entity_getall_type(type):
    try:
        link= db.__ENTITYTYPEMAPS__["link2type"][type]
    except:
        return db_utils.response_400(f"invalid entity type: {type}")
    return typedentity_getall(link)

# ---------------------------------------------------------------------------- ENDPOINT: /api/entity/<type>/<id> GET
# get a single entity of type, by id
@app.route('/api/entity/<type>/<int:id>', methods=['GET'])
def entity_get_type(type, id):
    try:
        link= db.__ENTITYTYPEMAPS__["link2type"][type]
    except:
        return db_utils.response_400(f"invalid entity type: {type}")
    return typedentity_get(link, id)

### ----------------------------------------------------------------------------------------------- ###
### --------------------------------------------- DEV --------------------------------------------- ###
### ----------------------------------------------------------------------------------------------- ###

# ---------------------------------------------------------------------------- ENDPOINT: /dev/user GET
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

# ---------------------------------------------------------------------------- ENDPOINT: /dev/bookmark GET
# different route to denote this wouldn't be part of the public api
@app.route('/dev/bookmark', methods=['GET'])
def bookmarks_getall():
    try:
        query= Bookmark.query.all()
        if not query:
            return db_utils.response(200, "no bookmarks")
        return db_utils.response_200([e.serialize() for e in query])
    except Exception as e:
        return db_utils.response_500(e.__repr__())

# ---------------------------------------------------------------------------- ENDPOINT: /dev/test GET
@app.route('/dev/test', methods=['GET'])
def api_code_test():
    txt="dev endpoint i used to make code tests"
    print(txt)
    return db_utils.response(418, "I'm a teapot", txt)

### ----------------------------------------------------------------------------------------------- ###
### -------------------------------------------- TOOLS -------------------------------------------- ###
### ----------------------------------------------------------------------------------------------- ###

# ---------------------------------------------------------------------------- ENDPOINT: /execute?toolid=<int> GET
@app.route('/execute', methods=['GET','HEAD'])
def execute():
    try:
        id = request.args.get('tool', type=int)
        if not id: return db_utils.response(400, "no executed") # fail silently
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