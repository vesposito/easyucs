import json
import jsonschema
import math
import os
import yaml

from flask import Flask, Response, request
from flask_cors import CORS

from device.manager import DeviceManager

app = Flask(__name__)
cors = CORS(app)

device_manager = DeviceManager()
device_manager.scan_repository()


def response_handle(response="", code=400, mimetype="application/json"):
    if code and not response:
        if code == 500:
            dict_response = {"message": "Exception - Internal Server Error"}
        elif code == 400:
            dict_response = {"message": "Invalid Request"}
        elif code == 404:
            dict_response = {"message": "Resource Not found"}
        elif code == 200:
            dict_response = {"message": "OK"}
        else:
            dict_response = {"message": "Unexpected Error Code"}
    elif response.__class__.__name__ == "str":
        dict_response = {"message": response}
    elif response.__class__.__name__ == "dict":
        dict_response = response
    json_response = json.dumps(dict_response, indent=4)
    final_response = Response(response=json_response, status=code, mimetype=mimetype)
    return final_response


def validate_json(payload, path):
    if payload and path:
        yaml_file = open(path)
        yaml_string = yaml_file.read()
        yaml_file.close()
        json_schema = yaml.load(yaml_string.replace("'", '"'))
        schema_path = 'file:///{0}/'.format(os.path.dirname(os.path.abspath(path)).replace("\\", "/"))
        resolver = jsonschema.RefResolver(schema_path, json_schema)

        try:
            jsonschema.validate(payload, json_schema, resolver=resolver)
            return True
        except jsonschema.ValidationError as err:
            print(err)
            return False
        except Exception as err:
            print(err)
            return False
    else:
        print("Payload or Path is missing")
        return False


@app.route("/")
def hello():
    device_manager.scan_repository()
    return "API easyUCS"


@app.route("/api/v1/devices", methods=['GET', 'POST'])
# @cross_origin()
def devices():
    if request.method == 'GET':
        try:
            page_size = int(request.args.get("pageSize", 0))
            page_number = int(request.args.get("pageNumber", 0))
            device_list = []
            for device in device_manager.device_list:
                device_list.append({"device-uuid": str(device.uuid), "name": device.name, "type": "ucs_system",
                                    "ip": device.target})
            device_dict = {"devices": device_list}

            if page_size and page_number:
                if len(device_list) // page_size:
                    total_page = math.ceil(len(device_list) / page_size)
                    if total_page >= page_number:
                        select_list = device_list[page_size * (page_number - 1): page_size * page_number]
                        device_dict = {"devices": select_list}

            response = response_handle(device_dict, 200)
        except Exception:
            response = response_handle(code=500)
        return response

    if request.method == 'POST':
        try:
            payload = request.json

            # Check if payload valid
            if not validate_json(payload=payload, path="api/specs/device_post.yaml"):
                response = response_handle(response="Invalid Payload", code=400)
                return response

            if "type" not in payload:
                payload["type"] = "ucsm"

            if device_manager.add_device(device_type=payload["type"], target=payload["ip"],
                                         username=payload["username"], password=payload["password"]):
                response = response_handle(code=200)
                device_manager.save_device(uuid=device_manager.device_list[-1].uuid)
            else:
                response = response_handle(code=500)
        except Exception:
            response = response_handle(code=500)
        return response


@app.route("/api/v1/devices/<device_uuid>", methods=['GET', 'DELETE', 'PUT'])
# @cross_origin()
def device_uuid(device_uuid):
    if request.method == 'GET':
        try:
            device = device_manager.find_device_by_uuid(device_uuid=device_uuid)
            if device:
                device_target = {"device-uuid": str(device.uuid), "name": device.name, "type": "ucs_system",
                                 "ip": device.target}
                device_dict = {"device": device_target}
                response = response_handle(device_dict, 200)
                return response
            else:
                response = response_handle(response="Device not found with UUID: " + device_uuid, code=404)
        except Exception:
            response = response_handle(code=500)
        return response

    if request.method == 'DELETE':
        try:
            if device_manager.remove_device(uuid=device_uuid):
                response = response_handle(code=200)
            else:
                response = response_handle(response="Device not found with UUID: " + device_uuid, code=404)
        except Exception:
            response = response_handle(code=500)
        return response

    if request.method == 'PUT':
        try:
            device = device_manager.find_device_by_uuid(device_uuid=device_uuid)
            if device:
                payload = request.json

                # Check if payload valid
                if not validate_json(payload=payload, path="api/specs/device_put.yaml"):
                    response = response_handle(response="Invalid Payload", code=400)
                    return response

                if "ip" in payload:
                    device.target = payload["ip"]
                if "username" in payload:
                    device.username = payload["username"]
                if "password" in payload:
                    device.password = payload["password"]

                device_manager.save_device(uuid=device.uuid)
                response = response_handle(code=200)
                return response
            else:
                response = response_handle(response="Device not found with UUID: " + device_uuid, code=404)
        except Exception:
            response = response_handle(code=500)
        return response


@app.route("/api/v1/devices/<device_uuid>/reset", methods=['POST'])
# @cross_origin()
def device_uuid_reset(device_uuid):
    if request.method == 'POST':
        try:
            payload = request.json

            # Check if payload valid
            if not validate_json(payload=payload, path="api/specs/device_id.yaml"):
                response = response_handle(response="Invalid Payload", code=400)
                return response

            device = device_manager.find_device_by_uuid(device_uuid=device_uuid)
            if device:
                if payload["password"] == device.password:
                    if device.reset(erase_virtual_drives=False, erase_flexflash=False, clear_sel_logs=False):
                        # TODO : Find a way to get the serial and mac
                        response = response_handle(response={"serial_number": "", "mac_address": ""}, code=200)
                    else:
                        response = response_handle(response="Reset failed", code=500)
                else:
                    response = response_handle(response="Admin password mismatch", code=400)
            else:
                response = response_handle(response="Device not found with UUID: " + device_uuid, code=404)
        except Exception:
            response = response_handle(code=500)
        return response


@app.route("/api/v1/devices/<device_uuid>/configs", methods=['GET', 'POST'])
# @cross_origin()
def device_uuid_configs(device_uuid):
    if request.method == 'GET':
        try:
            device = device_manager.find_device_by_uuid(device_uuid=device_uuid)
            if device:
                page_size = int(request.args.get("pageSize", 0))
                page_number = int(request.args.get("pageNumber", 0))
                config_list = []
                for config in device.config_manager.config_list:
                    config_list.append({"config-uuid": str(config.uuid), "timestamp": config.timestamp,
                                        "origin": config.origin})
                config_dict = {"devices": config_list}

                if page_size and page_number:
                    if len(config_dict) // page_size:
                        total_page = math.ceil(len(config_list) / page_size)
                        if total_page >= page_number:
                            select_list = config_list[page_size * (page_number - 1): page_size * page_number]
                            config_dict = {"devices": select_list}

                response = response_handle(config_dict, 200)
            else:
                response = response_handle(response="Device not found with UUID: " + device_uuid, code=404)
        except Exception:
            response = response_handle(code=500)
        return response

    if request.method == 'POST':
        try:
            device = device_manager.find_device_by_uuid(device_uuid=device_uuid)
            if device:
                try:
                    file = request.files['file']
                    json_file = file.read().decode("utf-8").replace("'", '"')
                except Exception:  # FIXME: Handle various exception cases - should only support JSON files for now
                    response = response_handle(response="Error while reading config file.", code=500)
                    return response

                if device.config_manager.import_config(import_format="json", config=json_file):
                    # Export the latest config (the imported config)
                    directory = device_manager.REPOSITORY_FOLDER_NAME + "/" + str(device.uuid) + "/configs"
                    filename = "config-" + str(device.config_manager.config_list[-1].uuid) + ".json"
                    device.config_manager.export_config(directory=directory, filename=filename)

                    response = response_handle(code=200)
                else:
                    response = response_handle(response="Impossible ton convert the file to a config", code=500)
            else:
                response = response_handle(response="Device not found with UUID: " + device_uuid, code=404)
        except Exception as err:
            print(err)
            response = response_handle(code=500)
        return response


# Fetch a new config for a device
@app.route("/api/v1/devices/<device_uuid>/configs/fetch", methods=['POST'])
# @cross_origin()
def device_uuid_configs_fetch_config(device_uuid):
    if request.method == 'POST':
        try:
            payload = request.json

            # Check if payload valid
            if not validate_json(payload=payload, path="api/specs/device_id.yaml"):
                response = response_handle(response="Invalid Payload", code=400)
                return response

            device = device_manager.find_device_by_uuid(device_uuid=device_uuid)
            if device:
                if payload["password"] == device.password:
                    if device.connect():

                        device.config_manager.fetch_config()
                        device.disconnect()
                        directory = device_manager.REPOSITORY_FOLDER_NAME + "/" + str(device.uuid) + "/configs"
                        filename = "config-" + str(device.config_manager.get_latest_config().uuid) + ".json"

                        # Creating folder for configs
                        if not os.path.exists(directory):
                            os.makedirs(directory)

                        device.config_manager.export_config(directory=directory, filename=filename)
                        response = response_handle(code=200,
                                                   response=str(device.config_manager.get_latest_config().uuid))
                    else:
                        response = response_handle(code=501)
                else:
                    response = response_handle(response="Admin password mismatch", code=400)
            else:
                response = response_handle(code=404)
        except Exception as err:
            print(err)
            response = response_handle(code=500)
        return response


@app.route("/api/v1/devices/<device_uuid>/configs/<config_uuid>", methods=['GET', 'DELETE'])
# @cross_origin()
def device_uuid_config_uuid(device_uuid, config_uuid):
    if request.method == 'GET':
        try:
            device = device_manager.find_device_by_uuid(device_uuid=device_uuid)
            if device:
                config = device.config_manager.find_config_by_uuid(uuid=config_uuid)
                if config:
                    config_target = {"config-uuid": str(config.uuid), "timestamp": config.timestamp,
                                     "origin": config.origin}
                    config_dict = {"config": config_target}
                    response = response_handle(config_dict, 200)
                else:
                    response = response_handle(response="Config not found with UUID: " + config_uuid, code=404)
            else:
                response = response_handle(response="Device not found with UUID: " + device_uuid, code=404)
        except Exception:
            response = response_handle(code=500)
        return response

    if request.method == 'DELETE':
        try:
            device = device_manager.find_device_by_uuid(device_uuid=device_uuid)
            if device:
                if device.config_manager.remove_config(uuid=config_uuid):
                    response = response_handle(code=200)
                else:
                    response = response_handle(response="Config not found with UUID: " + config_uuid, code=404)
            else:
                response = response_handle(response="Device not found with UUID: " + device_uuid, code=404)
        except Exception:
            response = response_handle(code=500)
        return response


@app.route("/api/v1/devices/<device_uuid>/inventories", methods=['GET', 'POST'])
# @cross_origin()
def device_uuid_inventories(device_uuid):
    if request.method == 'GET':
        try:
            device = device_manager.find_device_by_uuid(device_uuid=device_uuid)
            if device:
                page_size = int(request.args.get("pageSize", 0))
                page_number = int(request.args.get("pageNumber", 0))
                inventory_list = []
                for inventory in device.inventory_manager.inventory_list:
                    inventory_list.append({"inventory-uuid": str(inventory.uuid), "timestamp": inventory.timestamp,
                                           "origin": inventory.origin})
                inventory_dict = {"devices": inventory_list}

                if page_size and page_number:
                    if len(inventory_dict) // page_size:
                        total_page = math.ceil(len(inventory_list) / page_size)
                        if total_page >= page_number:
                            select_list = inventory_list[page_size * (page_number - 1): page_size * page_number]
                            inventory_dict = {"devices": select_list}

                response = response_handle(inventory_dict, 200)
            else:
                response = response_handle(response="Device not found with UUID: " + device_uuid, code=404)
        except Exception:
            response = response_handle(code=500)
        return response

    if request.method == 'POST':
        try:
            device = device_manager.find_device_by_uuid(device_uuid=device_uuid)
            if device:
                try:
                    file = request.files['file']
                    json_file = file.read().decode("utf-8").replace("'", '"')
                except Exception:  # FIXME: Handle various exception cases - should only support JSON files for now
                    response = response_handle(response="Error while reading inventory file.", code=500)
                    return response

                if device.inventory_manager.import_inventory(import_format="json", inventory=json_file):
                    # Export the latest inventory (the imported inventory)
                    directory = device_manager.REPOSITORY_FOLDER_NAME + "/" + str(device.uuid) + "/inventories"
                    filename = "inventory-" + str(device.inventory_manager.inventory_list[-1].uuid) + ".json"
                    device.inventory_manager.export_inventory(directory=directory, filename=filename)

                    response = response_handle(code=200)
                else:
                    response = response_handle(response="Impossible ton convert the file to a inventory", code=500)
            else:
                response = response_handle(response="Device not found with UUID: " + device_uuid, code=404)
        except Exception as err:
            print(err)
            response = response_handle(code=500)
        return response


@app.route("/api/v1/devices/<device_uuid>/inventories/<inventory_uuid>", methods=['GET', 'DELETE'])
# @cross_origin()
def device_uuid_inventory_uuid(device_uuid, inventory_uuid):
    if request.method == 'GET':
        try:
            device = device_manager.find_device_by_uuid(device_uuid=device_uuid)
            if device:
                inventory = device.inventory_manager.find_inventory_by_uuid(uuid=inventory_uuid)
                if inventory:
                    inventory_target = {"inventory-uuid": str(inventory.uuid), "timestamp": inventory.timestamp,
                                        "origin": inventory.origin}
                    inventory_dict = {"inventory": inventory_target}
                    response = response_handle(inventory_dict, 200)
                else:
                    response = response_handle(response="inventory not found with UUID: " + inventory_uuid, code=404)
            else:
                response = response_handle(response="Device not found with UUID: " + device_uuid, code=404)
        except Exception:
            response = response_handle(code=500)
        return response

    if request.method == 'DELETE':
        try:
            device = device_manager.find_device_by_uuid(device_uuid=device_uuid)
            if device:
                if device.inventory_manager.remove_inventory(uuid=inventory_uuid):
                    response = response_handle(code=200)
                else:
                    response = response_handle(response="inventory not found with UUID: " + inventory_uuid, code=404)
            else:
                response = response_handle(response="Device not found with UUID: " + device_uuid, code=404)
        except Exception:
            response = response_handle(code=500)
        return response


@app.route("/files/specs/<path>")
def specs_file(path):
    try:
        file_dict = yaml.load(open('./api/specs/' + str(path)))
        response = response_handle(file_dict, 200)
    except FileNotFoundError:
        response = response_handle(response="File not found with path: " + str(path), code=404)
    except Exception:
        response = response_handle(code=500)
    return response

