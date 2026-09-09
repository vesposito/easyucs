# coding: utf-8
# !/usr/bin/env python

""" gui.py: Easy UCS Deployment Tool """
import json
import os
import re
import warnings

from flasgger import Swagger
from flask import Flask, Response, request, send_from_directory
from flask.templating import render_template

from __init__ import __version__, EASYUCS_ROOT

app = Flask(__name__, template_folder="../templates", static_folder="../static")

# Configure swagger documentation at API endpoint '/apidocs'
app.config['SWAGGER'] = {
    'title': 'EasyUCS API',
    'uiversion': 3,
    'openapi': "3.0.3"
}
swagger_config = Swagger.DEFAULT_CONFIG
swagger_config["specs"][0]["endpoint"] = "easyucs"
swagger_config["specs"][0]["route"] = "/easyucs.json"
swagger = Swagger(app, config=swagger_config, template_file="../api/specs/easyucs.yaml")


def _dynamic_spec():
    # Read the spec from disk and override the servers list with the URL derived
    # from the incoming request, so the Swagger UI reflects the correct host and
    # port whether running standalone, behind gunicorn, or through an Apache
    # reverse proxy.
    # Note: gunicorn's default forwarded_allow_ips="127.0.0.1" means it reads
    # X-Forwarded-Proto from Apache and sets wsgi.url_scheme accordingly, so
    # request.host_url already reflects the correct scheme in all environments.
    spec_path = os.path.join(EASYUCS_ROOT, "api", "specs", "easyucs.json")
    try:
        with open(spec_path, "r", encoding="utf-8") as f:
            spec = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        return Response(
            json.dumps({"error": "Could not load API spec", "detail": str(exc)}),
            status=500,
            mimetype="application/json",
        )
    spec["servers"] = [{"url": request.host_url.rstrip("/") + "/api/v1"}]
    return Response(json.dumps(spec), mimetype="application/json")


# Flasgger registers its spec route inside its own blueprint (endpoint name
# "flasgger.easyucs", derived from swagger_config["specs"][0]["endpoint"]) before
# any @app.route decorators run. Flask always dispatches to the blueprint route
# first for identical paths, so the only reliable way to intercept it is to
# replace the view function directly.
if "flasgger.easyucs" in app.view_functions:
    app.view_functions["flasgger.easyucs"] = _dynamic_spec
else:
    warnings.warn(
        "flasgger.easyucs endpoint not found in app.view_functions; "
        "the dynamic API spec server URL override did not apply. "
        "Check the flasgger version or swagger_config endpoint name.",
        RuntimeWarning,
        stacklevel=1,
    )



@app.route("/", methods=['GET'])
def index():
    return render_template("html/home.html", version=__version__)


@app.route("/config-catalog/<device_type>", methods=['GET'])
def config_catalog(device_type):
    return render_template("html/config-catalog.html", version=__version__)


@app.route("/contact", methods=['GET'])
def contact():
    return render_template("html/contact.html", version=__version__)


@app.route("/devices/<device_uuid>/inventory/<inventory_uuid>", methods=['GET'])
def inventory(device_uuid, inventory_uuid):
    return render_template("html/object.html", version=__version__, object_type="Inventory")


@app.route("/devices/<device_uuid>", methods=['GET'])
def device(device_uuid):
    return render_template("html/device.html", version=__version__)


@app.route("/devices/<device_uuid>/config/<config_uuid>", methods=['GET'])
def config(device_uuid, config_uuid):
    return render_template("html/object.html", version=__version__, object_type="Config")


@app.route("/devices/<device_uuid>/backup/<backup_uuid>", methods=['GET'])
def backup(device_uuid, backup_uuid):
    return render_template("html/object.html", version=__version__, object_type="Backup")


@app.route("/devices/<device_uuid>/report/<report_uuid>", methods=['GET'])
def report(device_uuid, report_uuid):
    return render_template("html/object.html", version=__version__, object_type="Report")


@app.route("/task/<task_uuid>", methods=['GET'])
def task(task_uuid):
    return render_template("html/task.html", version=__version__)


@app.route("/tasks", methods=['GET'])
def tasks():
    return render_template("html/tasks.html", version=__version__)


@app.route("/easyucs.yaml", methods=['GET'])
def apispec():
    spec_path = os.path.join(EASYUCS_ROOT, "api", "specs", "easyucs.yaml")
    try:
        with open(spec_path, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError as exc:
        return Response(str(exc), status=500, mimetype="text/plain")
    # Replace the hardcoded servers URL with one derived from the incoming request.
    # We do a targeted string substitution rather than parsing YAML to avoid any
    # risk of altering key order, comments, or formatting.
    dynamic_url = request.host_url.rstrip("/") + "/api/v1"
    content = re.sub(
        r"(servers\s*:\s*\n\s*-\s*url\s*:\s*)['\"]?[^'\"\n]+['\"]?",
        r"\g<1>'" + dynamic_url + "'",
        content,
        count=1,
    )
    return Response(content, mimetype="application/yaml")


@app.route("/easyucs.json", methods=['GET'])
def api_spec():
    # In normal operation this route is shadowed by the flasgger.easyucs blueprint
    # route registered above. It acts as a fallback if the view_functions override
    # fails (e.g. after a flasgger upgrade that renames the endpoint).
    return _dynamic_spec()

@app.route("/repository", methods=['GET'])
def repository():
    return render_template("html/repository.html", version=__version__)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('html/404.html'), 404
