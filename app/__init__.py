from flask import Flask
from .config import Config
from .models.database import db

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(Config)
    db.init_app(app)

    # register blueprints
    from .routes.api.auth import bp as auth_bp
    # from .routes.api.households import bp as households_bp
    from .routes.web.dashboard import bp as dashboard_bp
    from .routes.web.map import bp as map_bp
    from .routes.web.administration import bp as administration_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    # app.register_blueprint(households_bp, url_prefix="/api/households")
    app.register_blueprint(dashboard_bp, url_prefix="/admin")
    app.register_blueprint(map_bp, url_prefix="/admin")
    app.register_blueprint(administration_bp, url_prefix="/admin")

    @app.route("/")
    def index():
        return "Welcome to My Project Backend"

    return app



