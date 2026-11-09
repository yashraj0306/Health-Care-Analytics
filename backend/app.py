"""Flask application factory.   Run:  python app.py   (http://localhost:5000)"""
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from flask import Flask, jsonify, send_from_directory  # noqa: E402
from flask_cors import CORS  # noqa: E402
from werkzeug.exceptions import HTTPException  # noqa: E402

from config import Config  # noqa: E402
from services.errors import ApiError  # noqa: E402
from services.store import DatasetStore  # noqa: E402

log = logging.getLogger("healthcare")


def create_app(overrides=None):
    app = Flask(__name__, static_folder=None)
    app.config.from_object(Config)
    app.config.update(overrides or {})
    for k in ("DATA_DIR", "UPLOAD_DIR", "MODEL_DIR", "DB_PATH"):
        app.config[k] = Path(app.config[k])

    CORS(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})
    store = DatasetStore(app.config["DB_PATH"], app.config["UPLOAD_DIR"],
                         app.config["MODEL_DIR"], app.config["DATA_DIR"])
    app.extensions["store"] = store
    if app.config["AUTO_REGISTER_DEFAULT"]:
        try:
            store.ensure_default(app.config["DEFAULT_DATASET"])
        except Exception:  # never block startup on a bad default file
            log.exception("Could not register the default dataset")

    from api import bp
    app.register_blueprint(bp)

    @app.errorhandler(ApiError)
    def api_error(e):
        return jsonify(e.to_dict()), e.status

    @app.errorhandler(HTTPException)
    def http_error(e):
        code = {413: "file_too_large", 404: "not_found", 405: "method_not_allowed"}.get(e.code, "http_error")
        msg = "File exceeds the 50 MB upload limit." if e.code == 413 else e.description
        return jsonify({"error": {"code": code, "message": msg}}), e.code

    @app.errorhandler(Exception)
    def unexpected(e):
        log.exception("Unhandled error")
        return jsonify({"error": {"code": "internal_error",
                                  "message": "Unexpected server error. See the backend log."}}), 500

    # Serve the built frontend (npm run build) when present — optional.
    dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
    if dist.exists():
        @app.get("/", defaults={"path": ""})
        @app.get("/<path:path>")
        def spa(path):
            if path and (dist / path).is_file():
                return send_from_directory(dist, path)
            return send_from_directory(dist, "index.html")
    return app


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    create_app().run(host="127.0.0.1", port=int(os.environ.get("PORT", 5000)), debug=False, threaded=True)
