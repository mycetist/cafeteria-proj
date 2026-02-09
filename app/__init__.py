from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate

from config import get_config
from app.extensions import db, jwt


def create_app(config_name=None):
    app = Flask(__name__, 
                template_folder='../templates',
                static_folder='../static')
    
    config = get_config(config_name)
    app.config.from_object(config)
    
    init_extensions(app)
    register_blueprints(app)
    register_error_handlers(app)
    
    return app


def init_extensions(app):
    db.init_app(app)
    jwt.init_app(app)
    Migrate(app, db)
    CORS(app, origins=app.config['CORS_ORIGINS'])


def register_blueprints(app):
    from app.api import auth_bp, student_bp, cook_bp, admin_bp, common_bp
    from app.routes import pages_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(student_bp, url_prefix='/api')
    app.register_blueprint(cook_bp, url_prefix='/api/cook')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(common_bp, url_prefix='/api')
    app.register_blueprint(pages_bp)


def register_error_handlers(app):
    from flask import jsonify, render_template, request
    from werkzeug.exceptions import HTTPException, NotFound, Forbidden, InternalServerError
    
    @app.errorhandler(404)
    def handle_404(e):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Не найдено', 'message': 'Запрашиваемый ресурс не найден', 'status_code': 404}), 404
        return render_template('404.html'), 404
    
    @app.errorhandler(403)
    def handle_403(e):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Доступ запрещен', 'message': 'У вас нет прав для доступа к этому ресурсу', 'status_code': 403}), 403
        return render_template('403.html'), 403
    
    @app.errorhandler(500)
    def handle_500(e):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Внутренняя ошибка', 'message': 'Произошла внутренняя ошибка сервера', 'status_code': 500}), 500
        return render_template('500.html'), 500
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        if request.path.startswith('/api/'):
            response = {
                'error': e.name,
                'message': e.description,
                'status_code': e.code
            }
            return jsonify(response), e.code
        # For non-API requests, try to show appropriate error page
        if e.code == 404:
            return render_template('404.html'), 404
        elif e.code == 403:
            return render_template('403.html'), 403
        elif e.code >= 500:
            return render_template('500.html'), e.code
        return render_template('500.html'), 500
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        app.logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
        if request.path.startswith('/api/'):
            response = {
                'error': 'Internal Server Error',
                'message': str(e) if app.config['DEBUG'] else 'An unexpected error occurred',
                'status_code': 500
            }
            return jsonify(response), 500
        return render_template('500.html'), 500
