#!/usr/bin/env python
# coding: utf-8

""" easyucs_gui.py: Easy UCS Deployment Tool """
from easyucs import __author__, __copyright__,  __version__, __status__

from easyucs.device.device import UcsImc, UcsSystem, BlindUcs, GenericUcsDevice
from easyucs.easyucs import create_ucs_device, init_process

from flask import Flask, request, abort, jsonify
from flask.templating import render_template
from argparse import Namespace

import json, os

app = Flask(__name__)

ucs_device = None


@app.route("/")
def index():
    return render_template("html/index.html")


@app.route('/connect', methods=['POST'])
def connect():
    if not request.json:
        abort(400)
    payload = request.json
    global ucs_device

    ucs_device = UcsSystem(target=payload["ip"], user=payload["user"], password=payload["pwd"])

    try:
        ucs_device.connect()
        return "ucs_device connected"
    except:
        return "ucs_device NOT connected"


@app.route("/disconnect")
def disconnect():
    ucs_device.disconnect()
    return "ucs_device disconnected"


@app.route('/init', methods=['POST'])
def init():
    if not request.json:
        abort(400)
    payload = request.json
    config_json = ""
    global ucs_device

    if isinstance(payload["setup"], list):
        setup = payload["setup"]
    else:
        setup = [payload["setup"]]

    args = Namespace(ip=payload["ip"], username=payload["user"], password=payload["pwd"], log=True,
                     logfile=None, reset=payload["reset"], setup=setup, ucstype=payload["ucs_type"],
                     yes=True, scope="config", action="push")

    ucs_device = create_ucs_device(args)

    if len(payload["config_json"]):
        config_json = payload["config_json"][0]
    else:
        config_json = ""

    try:
        init_process(ucs_device, args, config_json)
        return "Script done"
    except:
        return "Script error"


@app.route("/status")
def get_progression():
    global ucs_device

    try:
        status = ucs_device.get_task_progression()
        return str(status)
    except:
        return "error in get_progression"


@app.route("/getlogs")
def get_logs():
    global ucs_device

    try:
        log_str = ucs_device.get_logs()
        return log_str
    except:
        return "error in get_logs"


@app.route("/validatejson", methods=['POST'])
def validatejson():
    global ucs_device

    if ucs_device.config_manager._validate_config_from_json(config_json=request.data.decode()):
        return jsonify(status="valid")
    else:
        return jsonify(status="invalid")


@app.route("/getmetadata")
def getmetadata():
    meta = {}

    for root, dirs, files in os.walk("samples"):
        for file in files:
            if file.endswith(".json"):
                # print(os.path.join(root, file))
                with open(os.path.join(root, file)) as json_data:
                    try:
                        d = json.load(json_data)
                    except:
                        print("in get_metadata :: bad json file: ", file)

                    if 'easyucs' in d.keys():
                        if 'metadata' in d['easyucs'].keys():
                            # Add the path to metadata
                            d['easyucs']['path'] = root.replace('\\', '\\\\')
                            d1 = {file: d['easyucs']}
                            meta.update(d1)
    return json.dumps(meta)


@app.route("/readremotefile", methods=['POST'])
def readremotefile():
    config_file = {}

    if not request.json:
        abort(400)
        
    payload = request.json

    root = payload["path"]
    file = payload["file"]

#     with open(os.path.join(root, file)) as json_data:
#         try:
#             d = json.load(json_data)
#         except:
#             print("in getremotefile :: bad json file: ", file)
#             return
# 
#     return json.dumps({key: d[key] for key in ['sys']})

    with open(os.path.join(root, file)) as json_data:
        return json_data.read()


if __name__ == "__main__":
    app.run(threaded=True)
