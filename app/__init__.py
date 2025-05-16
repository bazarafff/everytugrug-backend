import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()

def create_app():
    app = Flask(__name__)

    # Config
    config_class = os.getenv("FLASK_ENV", "development")
    if config_class == "production":
        app.config.from_object("app.config.ProductionConfig")
    else:
        app.config.from_object("app.config.DevelopmentConfig")

    # Extensions
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)

    # Routes
    from app.routes.auth import auth_bp
    from app.routes.statements import stmt_bp
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(stmt_bp, url_prefix="/statements")

    @app.route("/")
    def index():
        return {"message": "EveryTugrug API is running successfully! OMG bazaraaa u so sexy"}

    return app



    

