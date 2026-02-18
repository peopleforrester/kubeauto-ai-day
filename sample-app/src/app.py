# ABOUTME: Sample Flask application for the KubeAuto Day IDP demo.
# ABOUTME: Serves HTTP endpoints instrumented with OpenTelemetry auto-instrumentation.

from flask import Flask, jsonify
from typing import Any

app = Flask(__name__)


@app.route("/")
def index() -> tuple[Any, int]:
    """Root endpoint returning platform info."""
    return jsonify({
        "app": "kubeauto-sample-app",
        "platform": "KubeAuto Day IDP",
        "status": "healthy",
    }), 200


@app.route("/health")
def health() -> tuple[Any, int]:
    """Health check endpoint for Kubernetes probes."""
    return jsonify({"status": "ok"}), 200


@app.route("/ready")
def ready() -> tuple[Any, int]:
    """Readiness check endpoint for Kubernetes probes."""
    return jsonify({"status": "ready"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
