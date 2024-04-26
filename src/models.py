from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    _id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(64), nullable=False)
    password = db.Column(db.String(80), nullable=False)

    def __repr__(self):
        return f'<User {self._id}-{self.username}>'

    def serialize(self):
        return {
            "_id": self._id,
            "name": self.username,
            "email": self.email
        }

class Entity(db.Model):
    _id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(255))
    type = db.Column(db.String(32), nullable=False)
    properties = db.Column(db.String(4096), nullable=False)

    def __repr__(self):
        return f'<Planet {self._id}-{self.name}>'

    def serialize(self):
        return {
            "_id": self._id,
            "name": self.name,
            "description": self.description,
            "type": self.type,
            "properties": self.properties,
        }
    
class Bookmark(db.Model):
    _id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    entity_id = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f'<Bookmark user-{self.user_id} entity-{self.entity_id}>'

    def serialize(self):
        return {
            "_id": self._id,
            "user": self.user_id,
            "entity": self.entity_id,
        }