import json
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "users"
    _id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(32), unique=True, nullable=False)            # internal username
    displayname = db.Column(db.String(64), nullable=False)                      # public displayname
    email = db.Column(db.String(32), unique=True, nullable=False)               # user email
    password = db.Column(db.String(32), nullable=False)                         # account password
    user_token= db.Column(db.String(64))                                        # current login session token, or null if not logged-in
    bookmarks = db.relationship('Bookmark', backref='user', lazy='dynamic')     # bookmarks

    def __repr__(self):
        return f'<User {self._id}-{self.username}-{self.email}-{self.displayname}>'

    def serialize(self):
        return {
            "_id": self._id,
            "name": self.username,
            "nick": self.displayname,
            "email": self.email,
            # this is only here to debug
            "password": self.password,
            "user_token": self.user_token
        }

class Entity(db.Model):
    __tablename__ = "entities"
    _id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    _tid = db.Column(db.Integer, nullable=False)                                        # per-type autoincremental id
    name = db.Column(db.String(32), unique=True, nullable=False)                        # entity display name
    description = db.Column(db.String(128))                                             # entity display description
    properties = db.Column(db.String(2048), nullable=False)                             # json-formatted string with all the required properties
    type_id = db.Column(db.Integer, db.ForeignKey("entity_types._id"), nullable=False)  # entitytype

    def get_tid_(self, type):
        return self.query.filter_by(type_id=type).count()+1

    # defining init to allow a custom id counter (tid, per-type id)
    def __init__(self, _tid=None, name=None, description=None, properties={}, type_id=None):
        self._tid= _tid if not _tid == None else self.get_tid_(type_id)
        self.name= name
        self.description= description
        self.properties= properties
        self.type_id= type_id

    def __repr__(self):
        return f'<Entity {self._id}-{self.type_id}-{self._tid}-{self.name}>'

    def serialize(self):
        return {
            "_id": self._id,
            "_tid": self._tid,
            "name": self.name,
            "description": self.description,
            "type_id": self.type_id,
            #"properties_str": self.properties,
            "properties": json.loads(self.properties)
        }

class EntityType(db.Model):
    __tablename__ = "entity_types"
    _id= db.Column(db.Integer, primary_key=True, autoincrement=True)
    name= db.Column(db.String(32), unique=True, nullable=False)         # type name
    link= db.Column(db.String(32), unique=True, nullable=False)         # api link name
    properties= db.Column(db.String(2048), nullable=False)              # required properties for its type

    # defining custom init that generates link if not provided
    def __init__(self, name=None, link=None, properties=None):
        self.name= name
        self.link= link if link else name
        self.properties= properties

    def __repr__(self):
        return f'<EntityType {self._id}-{self.name}-/api/{self.link}>'

    def serialize(self):
        return {
            "_id": self._id,
            "name": self.name,
            "link": self.link,
            "properties": self.properties.split('|')
        }
    
class Bookmark(db.Model):
    __tablename__ = "bookmarks"
    _id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users._id"), nullable=False)         # owner user id
    entity_id = db.Column(db.Integer, db.ForeignKey("entities._id"), nullable=False)    # entity this bookmark refeers to
    entity = db.relationship('Entity')

    def __repr__(self):
        return f'<Bookmark {self._id}-user{self.user_id}-entity{self.entity_id}>'

    def serialize(self):
        return {
            "_id": self._id,
            "user_id": self.user_id,
            "entity_id": self.entity_id,
        }