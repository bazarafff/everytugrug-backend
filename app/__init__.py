import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from dotenv import load_dotenv

from .config import Config

# Load environment variables from .env file
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    print("🔍 SQLALCHEMY_DATABASE_URI =", app.config.get("SQLALCHEMY_DATABASE_URI"))
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)

    from app import models
    from app.routes.auth import auth_bp
    from app.routes.statements import stmt_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(stmt_bp, url_prefix="/statements")

    return app
