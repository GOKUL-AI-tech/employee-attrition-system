import os
from flask import Flask, jsonify, send_from_directory
from database import init_db, close_db, BASE

DIST = os.path.join(os.path.dirname(BASE), "frontend", "dist")


def create_app():
    app = Flask(__name__, static_folder=None)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    init_db()
    app.teardown_appcontext(close_db)

    from routes.auth import bp as auth_bp
    from routes.employees import bp as emp_bp
    from routes.predict import bp as pred_bp
    from routes.analytics import bp as ana_bp
    from routes.reports import bp as rep_bp
    for b in (auth_bp, emp_bp, pred_bp, ana_bp, rep_bp):
        app.register_blueprint(b)

    with app.app_context():
        import ml_service
        ml_service.ensure_ready()

    @app.errorhandler(404)
    def nf(e):
        return jsonify(error="Not found"), 404

    # Serve the built React app if present (optional; dev uses the Vite server)
    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def spa(path):
        if os.path.isdir(DIST):
            f = os.path.join(DIST, path)
            return send_from_directory(DIST, path if path and os.path.isfile(f) else "index.html")
        return jsonify(message="API running. Start the frontend with `npm run dev` in /frontend.")

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5000, debug=False)
