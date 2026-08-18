"""
WareMind AI — Smart Warehouse Operations & Order Fulfillment Intelligence Platform
Entry point for the Flask application.
"""
import os
from flask import Flask, jsonify
from config import Config
from database import db


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Ensure instance directory exists
    os.makedirs(os.path.join(os.path.dirname(__file__), "instance"), exist_ok=True)

    # Bind SQLAlchemy to app
    db.init_app(app)

    # Register blueprints
    from routes.dashboard import dashboard_bp
    from routes.inventory import inventory_bp
    from routes.orders import orders_bp
    from routes.exceptions import exceptions_bp
    from routes.analytics import analytics_bp
    from routes.copilot import copilot_bp
    from routes.simulation import simulation_bp
    from routes.auth import auth_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(exceptions_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(copilot_bp)
    app.register_blueprint(simulation_bp)
    app.register_blueprint(auth_bp)

    # Global error handlers
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Resource not found", "code": 404}), 404

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": "Bad request", "code": 400}), 400

    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        return jsonify({"error": "Internal server error", "code": 500}), 500

    # Create tables & auto-seed if empty
    with app.app_context():
        # Import all models so SQLAlchemy registers them before create_all
        import database.models  # noqa: F401
        db.create_all()

        from database.models import Product
        if Product.query.count() == 0:
            print("[INFO] No data found. Running seed script...")
            from database.seed import seed_database
            seed_database()

    return app


app = create_app()

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    print(f"[INFO] Starting WareMind AI on port {port}...")
    app.run(debug=False, host="0.0.0.0", port=port)

