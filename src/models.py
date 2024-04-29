import json
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

PROPERTIES= {
    "user": [""]
}

class User(db.Model):
    __tablename__ = "users"
    _id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(32), unique=True, nullable=False)
    email = db.Column(db.String(32), unique=True, nullable=False)
    password = db.Column(db.String(32), nullable=False)
    bookmarks = db.relationship('Bookmark', backref='user', lazy='dynamic')

    def __repr__(self):
        return f'<User {self._id}-{self.username}-{self.email}>'

    def serialize(self):
        return {
            "_id": self._id,
            "name": self.username,
            "email": self.email
        }

class Entity(db.Model):
    __tablename__ = "entities"
    _id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    _tid = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(512))
    properties = db.Column(db.String(32768), nullable=False)
    type_id = db.Column(db.Integer, db.ForeignKey("entity_types._id"), nullable=False)

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
            "properties": json.loads(self.properties),
        }

class EntityType(db.Model):
    __tablename__ = "entity_types"
    _id= db.Column(db.Integer, primary_key=True, autoincrement=True)
    name= db.Column(db.String(32), unique=True, nullable=False)

    def __repr__(self):
        return f'<EntityType {self._id}-{self.name}>'

    def serialize(self):
        return {
            "_id": self._id,
            "name": self.name
        }
    
class Bookmark(db.Model):
    __tablename__ = "bookmarks"
    _id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users._id"), nullable=False)
    entity_id = db.Column(db.Integer, db.ForeignKey("entities._id"), nullable=False)
    entity = db.relationship('Entity')

    def __repr__(self):
        return f'<Bookmark {self._id}-user{self.user_id}-entity{self.entity_id}>'

    def serialize(self):
        return {
            "_id": self._id,
            "user_id": self.user_id,
            "entity_id": self.entity_id,
        }