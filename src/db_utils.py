import os, sys, json, signal
from flask import jsonify
from random import randrange, randint
from models import db, User, Entity, EntityType, Bookmark # only 4 needed

# I made this extra module cos app.py was getting too long

__RUNMODES__= ("migrate", "upgrade", "init", "revision", "wipedb")
__TYPE_MAP__= {
#   sql_alchemy     python
    "string":       "str",
    "integer":      "int",
    "boolean":      "bool"
}

CONTENT_TYPE_JSON= {'Content-Type': 'application/json'}

CHARSET_DEFAULT= "abcdefghijklmnopqrstuvwxyz0123456789_"
CHARSET_ALPHA= "abcdefghijklmnopqrstuvwxyz"
CHARSET_ALPHANUMERIC= "abcdefghijklmnopqrstuvwxyz0123456789"
CHARSET_CONSONANTS= "bcdfghjklmnpqrstvwxyz"
CHARSET_VOWELS= "aeiou"
CHARSET_NUMBERS= "0123456789"

# hacky way of determine if this module is running through 'pipenv run XXXX'
def get_running_mode():
    for mode in __RUNMODES__:
        if mode in sys.argv: return mode
    return "normal"

def proccess_columns_metadata():
    db.__metacolumns__= {
        "users": get_columns_meta(User.__table__.columns),
        "entity_types": get_columns_meta(EntityType.__table__.columns),
        "entities": get_columns_meta(Entity.__table__.columns),
        "bookmarks": get_columns_meta(Bookmark.__table__.columns)
    }
    def __meta_repr__(metacolumns):
        result= []
        for k in metacolumns.keys():
            meta= metacolumns[k]
            mstr= []
            type_str= meta[0][0]
            mstr.append(f"{type_str}\033[1;90m(\033[1;91m{meta[0][1].length}\033[1;90m)\033[1;94m") if type_str== 'str' else mstr.append(type_str)
            if meta[1] or meta[2]: 
                mstr.append('\033[1;97m:\033[1;93m')
                if meta[1]: mstr.append('N')
                if meta[2]: mstr.append('U')
            mstrfull= "".join(mstr)
            result.append(f"\033[1;94m{k}\033[1;97m:\033[1;93m{mstrfull}\033[1;97m")
        return " | ".join(result)
    print("\033[1;92m\ntable columns: \033[1;90m(\033[1;93mN\033[1;90m= nullable, \033[1;93mU\033[1;90m= unique)\n ", "\n  ".join([f"\033[4;97m{key}\033[24m: \033[0;94m{__meta_repr__(db.__metacolumns__[key])}" for key in db.__metacolumns__.keys()]), "\n\033[0m")     

def perform_database_rowcount():
    try:
        lc= [ User.query.count(), EntityType.query.count(), Entity.query.count(), Bookmark.query.count() ]
        db.__rowcounts__= {
            "total": lc[0] + lc[1] + lc[2] + lc[3],
            "users": lc[0],
            "entity_types": lc[1],
            "entities": lc[2],
            "bookmarks": lc[3]
        }
        print("\033[1;92m\ndatabase row count:\n", " | ".join([f"\033[1;94m{db.__rowcounts__[key]} \033[4;97m{key}\033[0m" for key in db.__rowcounts__.keys()])[:-2], "\n\033[0m")
    except:
        print("\033[1;91m\napp.py -> FATAL: unable to read starwars database tables, did you forgot to run \033[4;93mpipenv run upgrade\033[24;91m?\033[0m\n")
        db.__rowcounts__['total']=-1
        os.kill(os.getpid(), signal.SIGTERM)

def refresh_entity_type_registry():
    db.__ENTITYTYPEMAPS__= { "type2id": {}, "link2type": {}, "id2type": {}, }
    for t in EntityType.query.all():
        db.__ENTITYTYPEMAPS__["type2id"][t.name]= t._id
        db.__ENTITYTYPEMAPS__["link2type"][t.link]= t.name
        db.__ENTITYTYPEMAPS__["id2type"][t._id]= t.name

# generates a random string of a given size using a given charset
def generate_random_str(min:int, max:int=None, charset:str=CHARSET_DEFAULT) -> str:
    if not max or max < min: max= min
    generated= []
    charset_size= len(charset)
    for _ in range(randint(min, max)):
        generated.append(CHARSET_DEFAULT[randrange(charset_size)])
    return "".join(generated)

# generates a random email alike string of a given size
def generate_random_email_str(min:int, max:int=None) -> str:
    return "".join([generate_random_str(min, max, CHARSET_DEFAULT), '@', generate_random_str(5, 8, CHARSET_ALPHA), '.com'])

def response(status, message, data=None):
    return jsonify({ "message": message, "result": data } if not data == None else { "message": message }), status, CONTENT_TYPE_JSON

def response_200(data=None): return response(200, "ok", data)
def response_400(data=None): return response(400, "BAD REQUEST", data)
def response_500(data=None): return response(500, "SERVER ERROR", data)

# basic common tests for any POST/PUT request (header, json etc...)
# returns [false , an-error-response] if fails or [true, the-json-data] if succeeds
def check_valid_json_body(request):
    if not 'Content-Type' in request.headers or not request.headers['Content-Type'] == "application/json":
        return False, response(400, "Content-Type must be 'application/json'")
    if not request.data:
        return False, response(400, "Body must contain entity data")
    try:
        data= request.json
        if not data:
            return False, response(400, "Body contains an empty JSON")
    except:
        return False, response(400, "Body contains invalid JSON data")
    return True, data

# get any model's columns metadata
def get_columns_meta(columns):
    meta= {}
    for c in columns.values():
        if c.name[0] != '_': # ignore -privates-
            ctype= type(c.type).__name__.lower()
            pytype= __TYPE_MAP__[ctype] if ctype in __TYPE_MAP__ else 'str'
            meta[c.name]= [ [pytype, c.type], c.nullable, c.unique ] # 'columnname'= [[ python type, db value type], nullable, unique]
    return meta

# check a dict keys against metacolumns (with columns names and nullable)
def check_missing_properties(data, metacolumns, exceptions={}, additions=None):
    for p in list(metacolumns.keys()) + additions:
        if not p in data and not p in exceptions and not metacolumns[p][1]:
            return p
    return None

# check if value is assignable to a column type
def get_value_for_column(value, column_type):
    vtype= type(value).__name__.lower()
    is_string= column_type[0] == 'str'
    try:
        final_value= _get_value()
        def _get_value():
            n= column_type[0]
            if n == 'str': 
                if vtype=='str':
                    if len(value) <= column_type[1].length: return value
                elif len(str(value)) <= column_type[1].length: return str(value)
            elif n == vtype: return value
            elif vtype == 'str':
                if n == 'int' and value.isnumeric(): return int(value)
                elif n == 'bool':
                    vl= value.lower()
                    if vl=="true" or vl=="false": return bool(value)
            return None
        length_str= f", maxlength: {column_type.length}" if is_string else ""
        print(f"vtype: {vtype}, ctype: {column_type[0]}, value: {value}, finalvalue:{final_value}{length_str}")
        return True, final_value
    except:
        print(f"Couldn't parse value for column: {value}, {column_type}")
    return False, None

# get env variable safe with default fallback
def get_environ(name:str, default:any=None) -> any:
    if name in os.environ: return os.environ[name]
    return default

# earse all
def clear_database(commit):
    if db.__rowcounts__['total'] > 0:
        for table in db.metadata.sorted_tables:
            db.session.execute(table.delete())
    if commit:
        db.session.commit()

# this is NOT planned to be additive as it DOES NOT check for duplicates
def load_rows_from_file(filepath):
    try:
        json_data= json.load(open(filepath,"r"))
        types_changed= False

        if 'user' in json_data:
            for user_data in json_data["user"]:
                db.session.add(User(
                    username=user_data[0],
                    displayname=user_data[1],
                    email=user_data[2],
                    password=user_data[3]
                ))

        if 'entity_type' in json_data:
            # entity types first as they need to be commited (we do need their autogenerated _id later)
            for entity_type_data in json_data["entity_type"]:
                db.session.add(EntityType(
                    name=entity_type_data[0],
                    link=entity_type_data[1],
                    properties=entity_type_data[2]
                ))
            types_changed= True

        if 'entity' in json_data:
            if types_changed: # committing is needed as we need to update the 'typename to type_id' registry to be able to create entities
                db.session.commit()
                refresh_entity_type_registry()
            for entity_data in json_data["entity"]:
                _type_id= db.__ENTITYTYPEMAPS__['type2id'][entity_data[0]]
                if _type_id:
                    db.session.add(Entity(
                        type_id= db.__ENTITYTYPEMAPS__['type2id'][entity_data[0]], # this is why entity_types are commited first
                        name= entity_data[1],
                        description= entity_data[2],
                        properties= json.dumps(entity_data[3]) # dump properties to json string
                    ))
                else: print(f"Couldn't add entity: invalid type '{entity_data[0]}'")
        db.session.commit()
    except Exception as e:
        print(f"Couldn't read file: {filepath}", e.__repr__())

__DB_AUTOFILL__= get_environ('DB_AUTOFILL', True)
__RUNNING_MODE__= get_running_mode()
__DB_DEFAULTS_FILE__= get_environ('DB_DEFAULTS_FILE', "data/defaults.json")