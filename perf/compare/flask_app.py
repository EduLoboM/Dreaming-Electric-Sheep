"""
Flask WSGI benchmark application (default stack).
Runs on Granian with --interface wsgi.
"""
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from flask import Flask, Response, jsonify, request
from jinja2 import Template
from perf.compare.mock_db import (
    clamp_queries,
    get_single_world,
    get_multiple_worlds,
    get_fortunes_sorted,
    update_multiple_worlds,
    FORTUNES_HTML_TEMPLATE,
)

app = Flask(__name__)
_JINJA_TEMPLATE = Template(FORTUNES_HTML_TEMPLATE, autoescape=True)


@app.route("/plaintext")
def plaintext():
    return Response("Hello, World!", mimetype="text/plain")


@app.route("/json")
def handle_json():
    return jsonify({"message": "Hello, World!"})


@app.route("/db")
def single_query():
    return jsonify(get_single_world())


@app.route("/queries")
def multiple_queries():
    queries = request.args.get("queries")
    n = clamp_queries(queries)
    return jsonify(get_multiple_worlds(n))


@app.route("/fortunes")
def fortunes():
    items = get_fortunes_sorted()
    return Response(_JINJA_TEMPLATE.render(fortunes=items), mimetype="text/html")


@app.route("/updates")
def data_updates():
    queries = request.args.get("queries")
    n = clamp_queries(queries)
    return jsonify(update_multiple_worlds(n))
