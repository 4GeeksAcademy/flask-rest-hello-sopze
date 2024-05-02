import sys, io, re, db_utils
from models import db, User, Entity, EntityType, Bookmark
from random import randrange, randint

def generate_html_links():
    template= "<script>document.write('<a class=\"tool-%CLASS%\" onClick=\"fetch(`${window.location.href}/execute?tool=%TOOL_ID%`);\">%LABEL%</a>');</script>"
    def _local_getstr(id, css, label) -> str: return template.replace("%TOOL_ID%", str(id)).replace("%CLASS%", css).replace("%LABEL%", label)
    return [
        _local_getstr(1,  "nope", "Wipe Database"),
        _local_getstr(2,  "db", "Clear Database"),
        _local_getstr(3,  "db", "Reset Database"),
        _local_getstr(4,  "db", "Print Database"),
        _local_getstr(5,  "user", "Add random User"),
        _local_getstr(6,  "user", "Modify random User"),
        _local_getstr(7,  "user", "Delete random User"),
        _local_getstr(8,  "type", "Add random EntityType"),
        _local_getstr(9,  "entity", "Add random Entity"),
        _local_getstr(10, "entity", "Delete random Entity"),
        _local_getstr(11, "bookmark", "Add random Bookmark"),
        _local_getstr(12, "bookmark", "Delete random Bookmark")
    ]

# could've done this in JS directly sending a randomized POST request as frontend would normally do, but I 
# wanted to create them "without" actually leaving the backend (except for the button)

def execute_tool(id):
    if not id:      return -1
    #elif id == 1:   return database_wipe() #pls dont xd
    elif id == 2:   return database_clear()
    elif id == 3:   return database_reset()
    elif id == 4:   return database_print()
    elif id == 5:   return create_random_user()
    elif id == 6:   return modify_random_user()
    elif id == 7:   return _delete_random(User.query.filter_by(user_token=None).all())
    elif id == 8:   return create_random_entitytype()
    elif id == 9:   return create_random_entity()
    elif id == 10:  return _delete_random(Entity.query.all())
    elif id == 11:  return create_random_bookmark()
    elif id == 12:  return _delete_random(Bookmark.query.all())

def _is_table_empty(table):
    return not table in db.__rowcounts__ or db.__rowcounts__[table] == 0
    
def _delete_random(entitylist):
    if entitylist:
        entity= entitylist[randrange(len(entitylist))]
        print(f"deleted Entity: {entity}")
        db.session.delete(entity)
        db.session.commit()
        return 1
    return 0

def create_random_user():
    entity= User(
        username= db_utils.generate_random_str(8, 12, charset=db_utils.CHARSET_ALPHA),
        displayname= db_utils.generate_random_str(8, 20, charset=db_utils.CHARSET_ALPHANUMERIC),
        email= db_utils.generate_random_email_str(8, 12),
        password= db_utils.generate_random_str(8, 12, charset=db_utils.CHARSET_ALPHANUMERIC),
    )
    db.session.add(entity)
    db.session.commit()
    print(f"created User: {entity}")
    return 1
    
def modify_random_user():
    entitylist= Entity.query.filter_by(user_token=None).all()
    if entitylist:
        # chances of getting modified are 33% for each column
        entity= entitylist[randrange(len(entitylist))]
        prev_name= ""
        if randint(2): 
            entity.username= db_utils.generate_random_str(8, 12, charset=db_utils.CHARSET_ALPHA)
            prev_name= f" (previous name: '{entity.username}')"
        if randint(2): entity.displayname= db_utils.generate_random_str(8, 20, charset=db_utils.CHARSET_ALPHANUMERIC)
        if randint(2): entity.email= db_utils.generate_random_email_str(8, 12)
        if randint(2): entity.password= db_utils.generate_random_str(8, 12, charset=db_utils.CHARSET_ALPHANUMERIC)
        db.session.commit()
        print(f"modified User: {entity}{prev_name}")
    return 0

# creates a random named entitytype, link is not provided so it will be copied from name
def create_random_entitytype():
    def _gen_random_property():
        propname= db_utils.generate_random_str(4,10)
        typemode= randrange(100)
        if typemode > 30:
            if typemode > 50:
                if typemode < 85: propname+=":int"
                else: propname+=":bool"
            if typemode % 10 > 7: propname+= "[]" if ':' in propname else ":str[]"
        return propname
    entity= EntityType(
        name= db_utils.generate_random_str(8, 12, charset=db_utils.CHARSET_ALPHA),
        properties= "|".join([_gen_random_property() for _ in range(randint(5,10))])
    )
    db.session.add(entity)
    db.session.commit()
    print(f"created EntityType: {entity}")
    return 2
    
def create_random_entity():
    typelist= EntityType.query.all()
    if typelist:
        _type= typelist[randrange(len(typelist))]
        _properties= ""
        for k in _type.properties.split("|"):
            type, array= "str", False
            if ':' in k:
                type= re.search(r"(?<=:)[^\[]+", k)[0]
                array= '[]' in k
                k = re.search(r"^[^:]*", k)[0]
            if type == "str":
                val= f"\"{db_utils.generate_random_str(4, 16, charset=db_utils.CHARSET_DEFAULT)}\""
                if array: val= f"[{val}]"
                _properties+= f"\"{k}\": {val}, "
            elif array: _properties+= f"\"{k}\": [], "
            elif type == "int": _properties+= f"\"{k}\": {str(randrange(16))}, "
            elif type == "bool": _properties+= f"\"{k}\": {'true' if randrange(2) > 0 else 'false'}, "
        _properties= f"{{{_properties[:-2]}}}"
        entity= Entity(
            name= db_utils.generate_random_str(12, 24, charset=db_utils.CHARSET_ALPHA),
            description= db_utils.generate_random_str(8, 12, charset=db_utils.CHARSET_ALPHA + "   "), # 3 spaces so more chances to get a space xd
            properties= _properties,
            type_id= _type._id
        )
        db.session.add(entity)
        db.session.commit()
        print(f"created Entity: {entity}")
    return 1
    
def create_random_bookmark():
    userlist, entitylist= User.query.all(), Entity.query.all()
    if userlist and entitylist:
        entity= Bookmark(
            user_id= userlist[randrange(len(userlist))]._id,
            entity_id= entitylist[randrange(len(entitylist))]._id
        )
        db.session.add(entity)
        db.session.commit()
        print(f"created Bookmark: {entity}")
        return 1
    else: return 0

# ---------------------------------------------------------------------------- DEVELOPER TOOLS

# drops ALL tables, destroys the database
def database_wipe():
    try:
        db.reflect()
        db.drop_all()
        db.session.commit()
        print("\033[1;91m\napp.py -> database was \033[4;93mwiped\033[24;91m succesfully\033[0m")
    except Exception as e:
        print("\033[1;91m\napp.py -> \033[4;91munable to wipe database\033[0m")
    return 0

# print all tables in an ugly string, used to debug
def database_print():
    _print, _dbstr= sys.stdout, io.StringIO()
    sys.stdout= _dbstr
    print(db.metadata.tables)
    sys.stdout= _print

    _dbstr.replace("(, ", "\n(\n").replace("}, ", "},\n")
    print(_dbstr)
    return 0

# clears the data, but doesn't destroy the database
def database_clear():
    try:
        db_utils.clear_database(True)
        db_utils.perform_database_rowcount()
    except Exception as e:
        print("couldn't clear", e.__repr__())
    return 2

# this is just for not having to manually create them each time the Codespace starts
# also called when server goes live if DB is empty and ENV tells to
def database_reset():
    try:
        db_utils.clear_database(False)
        db_utils.load_rows_from_file(db_utils.__DB_DEFAULTS_FILE__)
        db_utils.perform_database_rowcount()
    except Exception as e:
        print("couldn't reset", e.__repr__())
    return 2