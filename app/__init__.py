from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_uploads import UploadSet, configure_uploads, IMAGES, DOCUMENTS

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
socketio = SocketIO()

photos = UploadSet("photos", IMAGES)
documents = UploadSet("documents", DOCUMENTS)

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your_secret_key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
    app.config['UPLOADED_PHOTOS_DEST'] = 'app/static/images'
    app.config['UPLOADED_DOCUMENTS_DEST'] = 'app/static/uploads'

    db.init_app(app)
    login_manager.init_app(app)
    socketio.init_app(app)

    configure_uploads(app, photos)
    configure_uploads(app, documents)

    from app.routes import main
    app.register_blueprint(main)

    return app
