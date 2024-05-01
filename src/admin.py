import os
from flask_admin import Admin
from models import db, User, Entity, EntityType, Bookmark
from flask_admin.contrib.sqla import ModelView

def setup_admin(app):
    app.secret_key = os.environ.get('FLASK_APP_KEY', 'default_key')
    app.config['FLASK_ADMIN_SWATCH'] = os.environ.get('BOOTSTRAP_THEME', 'slate')
    admin = Admin(app, template_mode='bootstrap3')

    admin.add_view(ModelView(User, db.session))
    admin.add_view(ModelView(Entity, db.session))
    admin.add_view(ModelView(EntityType, db.session))
    admin.add_view(ModelView(Bookmark, db.session))