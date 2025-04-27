from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase

db = SQLAlchemy()
bcrypt = Bcrypt()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dating app secret key'
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///dating.db"
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    from . import main
    from . import model
    from . import auth
    from . import blocks
    from . import likes
    from . import profile
    from . import proposals
    from . import preferences
    from . import events
    db.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(model.User, int(user_id))
    app.register_blueprint(main.main, urlprefix='/')
    app.register_blueprint(auth.auth, urlprefix='/')
    app.register_blueprint(blocks.blocks, urlprefix='/')
    app.register_blueprint(likes.likes, urlprefix='/')
    app.register_blueprint(profile.profile, urlprefix='/')
    app.register_blueprint(proposals.proposals, urlprefix='/')
    app.register_blueprint(preferences.preferences, urlprefix='/')
    app.register_blueprint(events.events, urlprefix='/')  

    return app