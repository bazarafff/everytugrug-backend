import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from dotenv import load_dotenv
from flask_mail import Mail

mail = Mail()
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
    mail.init_app(app)

    from app import models
    from app.routes.auth import auth_bp
    from app.routes.statements import stmt_bp
    from app.routes.budget import budget_bp
    from app.routes.summary import summary_bp
    from app.routes.alerts import alerts_bp
    from app.routes.accounts import account_bp
    from app.routes.goals import goal_bp
    from app.routes.khan_crawler_step import khan_crawler_step_bp
    from app.routes.statement_analysis import statement_analysis_bp

    app.register_blueprint(statement_analysis_bp)
    app.register_blueprint(khan_crawler_step_bp)
    app.register_blueprint(goal_bp, url_prefix="/goals")
    app.register_blueprint(account_bp, url_prefix="/accounts")
    app.register_blueprint(alerts_bp)   
    app.register_blueprint(summary_bp)
    app.register_blueprint(budget_bp, url_prefix="/budget")
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(stmt_bp, url_prefix="/statements")
    @app.route("/")
    def index():
        return {"message": "EveryTugrug API is live 🎉"}, 200
    return app
