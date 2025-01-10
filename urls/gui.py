# coding: utf-8
# !/usr/bin/env python

""" gui.py: Easy UCS Deployment Tool """
import os

from flasgger import Swagger
from flask import Flask, send_from_directory
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
    return send_from_directory(os.path.join(EASYUCS_ROOT, "api", "specs"), 'easyucs.yaml')


@app.route("/easyucs.json", methods=['GET'])
def api_spec():
    return send_from_directory(os.path.join(EASYUCS_ROOT, "api", "specs"), 'easyucs.json')

@app.route("/repository", methods=['GET'])
def repository():
    return render_template("html/repository.html", version=__version__)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('html/404.html'), 404
