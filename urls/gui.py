# coding: utf-8
# !/usr/bin/env python

""" gui.py: Easy UCS Deployment Tool """

from flask import Flask
from flask.templating import render_template

from __init__ import __version__

app = Flask(__name__, template_folder="../templates", static_folder="../static")

# api_url = "http://127.0.0.1:5001/api/v1"

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

@app.route("/repository", methods=['GET'])
def repository():
    return render_template("html/repository.html", version=__version__)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('html/404.html'), 404