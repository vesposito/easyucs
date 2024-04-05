/*
device.js is the javascript used to animate the page device.html

All functions present here are solely used on the device.html page
*/

// Global variables
var current_device_uuid = null;
var current_device = null;
var loaded_backup_list = null;
var loaded_config_list = null;
var loaded_inventory_list = null;
var loaded_report_list = null;
var configTable = null;
var reportTable = null;
var backupTable = null;
var inventoryTable = null;

// Gets executed when DOM has loaded
function afterDOMloaded() {
  configTable = createDataTable("#configTable", 3, 3);
  inventoryTable = createDataTable("#inventoryTable", 3, 3);
  reportTable = createDataTable("#reportTable", 3, 3);
  backupTable = createDataTable("#backupTable", 3, 3);

  // Adding class to menu element in base.html to reflect that it is open
  document.getElementById("navLinkDevices").className += " active" 

  // Forces page reload when using browser back button
  if(typeof window.performance != "undefined" && window.performance.navigation.type == 2){
    window.location.reload(true);
  }

  url = window.location.href;

  // Getting device UUID from URL
  current_device_uuid = url.substring(url.lastIndexOf('/') + 1); 

  refreshData();
};

// Gets executed every X [in milliseconds]: here we are collecting device logs
window.setInterval(function() {
  if(current_device_uuid){
    getDeviceLogs();
  }
}, 5000);

// Handles the display of collapsing elements in the Push Config, when different radio buttons are toggled
$('[name="push_type"]').on('change', function() {  
  if($(this).val() === "new_file") {
    $('#collapsedNewFile').collapse('show');
    $('#collapsedCatalogConfigs').collapse('hide');
    $('#collapsedImportedConfigs').collapse('hide');
  } else if($(this).val() === "config_catalog"){
    $('#collapsedCatalogConfigs').collapse('show');
    $('#collapsedNewFile').collapse('hide');
    $('#collapsedImportedConfigs').collapse('hide');
  } else if($(this).val() === "current_configs"){
    $('#collapsedImportedConfigs').collapse('show');
    $('#collapsedNewFile').collapse('hide');
    $('#collapsedCatalogConfigs').collapse('hide');
  }
});

/**
 * Claims the device to the selected intersight target
 */
function claimToIntersight(){
  var form_content = $('#claimToIntersightForm').serializeArray();
  var form_json = objectifyForm(form_content);
  if(!form_json.intersight_device_uuid){
    console.error("Error claiming to Intersight: wrong parameters specified");
    return
  }
  if(form_json.intersight_device_uuid == "null"){
    console.error("Error claiming to Intersight: missing target Intersight device");
    displayAlert("Error claiming to Intersight:", "Missing target Intersight device");
    return
  }
  const target_api_endpoint = api_base_url + api_device_endpoint + "/" + current_device_uuid + "/actions/claim_to_intersight";
  const action_type_message = "Claiming to Intersight";
  httpRequestAsync("POST", target_api_endpoint, alertActionStarted.bind(null,action_type_message), form_json);

  // Closes the modal
  $('#claimToIntersightModal').modal('toggle');
}

/**
 * Clears the Intersight Claim Status of the device
 */
function clearIntersightClaimStatus(){
  // The function gets executed only if the user confirms the warning
  Swal.fire({
    title: "Clearing Intersight Claim Status is an irreversible action. Do you wish to proceed?",
    showDenyButton: true,
    confirmButtonText: `Yes`,
    denyButtonText: `No`,
  }).then((result) => {
      if (result.isConfirmed) {
        const target_api_endpoint = api_base_url + api_device_endpoint + "/" + current_device_uuid + "/actions/clear_intersight_claim_status";
        const action_type_message = "Clear Intersight Claim Status";
        httpRequestAsync("POST", target_api_endpoint, alertActionStarted.bind(null, action_type_message));
      }
  });
}

/**
 * Clears the config of the device
 */
function clearConfig(){
  var form_content = $('#clearConfigForm').serializeArray();
  // Creates a list from all the orgs selected by the user
  var org_list = [];
  form_content.forEach(function (org) {
    if(org.name == "org_list"){
      org_list.push(org.value);
    }
  });
  var title_text = "";
  if(org_list.length === 0){
    title_text = "You are about to clear ALL existing orgs. This is an irreversible action. Do you wish to proceed?";
  } else {
    title_text = "You are about to clear the following orgs: " + org_list.toString() + ". This is an irreversible action. Do you wish to proceed?";
  }

  // The function gets executed only if the user confirms the warning
  Swal.fire({
    title: title_text,
    showDenyButton: true,
    confirmButtonText: `Yes`,
    denyButtonText: `No`,
  }).then((result) => {
    if (result.isConfirmed) {
      var query_json = {"orgs": org_list};

      const target_api_endpoint = api_base_url + api_device_endpoint + "/" + current_device_uuid + "/actions/clear_config";
      const action_type_message = "Clear Config";
      httpRequestAsync("POST", target_api_endpoint, alertActionStarted.bind(null, action_type_message), query_json);
    }
  });

  // Closes the modal
  $('#clearConfigModal').modal('toggle');
}

/**
 * Clears the SEL logs of the device
 */
function clearSelLogs(){
  // The function gets executed only if the user confirms the warning
  Swal.fire({  
    title: "Clearing SEL Logs is an irreversible action. Do you wish to proceed?",
    showDenyButton: true, 
    confirmButtonText: `Yes`,  
    denyButtonText: `No`,
  }).then((result) => {  
      if (result.isConfirmed) {
        const target_api_endpoint = api_base_url + api_device_endpoint + "/" + current_device_uuid + "/actions/clear_sel_logs";
        const action_type_message = "Clear SEL Logs";
        httpRequestAsync("POST", target_api_endpoint, alertActionStarted.bind(null, action_type_message));
      }
  });
}

/**
 * Regenerates the SSL certificate of the device
 */
function regenerateCertificate(){
  // The function gets executed only if the user confirms the warning
  Swal.fire({
    title: "Regenerating SSL certificate is an irreversible action. Do you wish to proceed?",
    showDenyButton: true,
    confirmButtonText: `Yes`,
    denyButtonText: `No`,
  }).then((result) => {
      if (result.isConfirmed) {
        const target_api_endpoint = api_base_url + api_device_endpoint + "/" + current_device_uuid + "/actions/regenerate_certificate";
        const action_type_message = "Regenerate Certificate";
        httpRequestAsync("POST", target_api_endpoint, alertActionStarted.bind(null, action_type_message));
      }
  });
}

/**
 * Deletes the device
 * @param  {Event} event - The click event
 */
function deleteDevice(event){
  removeEventPropagation(event);

  // The function gets executed only if the user confirms the warning
  Swal.fire({  
    title: "Do you really want to delete this device?",
    text: current_device.device_name,  
    showDenyButton: true, 
    confirmButtonText: `Yes`,  
    denyButtonText: `No`,
  }).then((result) => {  
      if (result.isConfirmed) {
        // Redirects to homepage after delete
        deleteFromDb(redirectToHome, "device", current_device_uuid);
      }
  });


}

/**
 * Deletes a list of selected objects
 * @param  {String} object_type - The type of object selected {backup/config/inventory/report}
 */
function deleteMultipleObjects(object_type){
  var object_name_list = [];
  var object_uuid_list = [];

  if(selected_objects[object_type].length > bulk_actions_limit){
    raiseBulkActionLimitAlert(selected_objects[object_type].length);
    return
  }

  for(obj of selected_objects[object_type]){
    object_name_list.push(" " + obj["object_name"]);
    object_uuid_list.push(obj["object_uuid"]);
  }
  // The function gets executed only if the user confirms the warning
  Swal.fire({  
    title: "Do you really want to delete the following " + object_type + "  objects?",
    text: object_name_list,  
    showDenyButton: true, 
    confirmButtonText: `Yes`,  
    denyButtonText: `No`,
  }).then((result) => {  
      if (result.isConfirmed) {
        // Deletes the selected objects and refreshes the objects
        deleteMultipleFromDb(getObjectsFromDevice.bind(null, object_type), object_type, current_device_uuid, object_uuid_list);
      }
  });
}

/**
 * Displays a device
 * @param  {JSON} data - The data returned after getting a list of devices from the API
 */
function displayCatalogConfigs(data){
  if(!data){
      console.error('No data to display!');
      return
  }

  data = JSON.parse(data);

  if(!data.configs){
      console.error('No data to display!');
      return
  }

  var catalog_configs = data.configs;

  var catalog_configs_options_list = "";

  if(catalog_configs.length < 1){
    catalog_configs_options_list = `
    <option value="null">No catalog config available for device of type ${current_device.device_type_long}</option>
    `
  } else {
    catalog_configs.forEach(function (config) {
      config_name = setObjectName(config, "config");
      catalog_configs_options_list += `
        <option value="${config.uuid}">${config_name}</option>
      `
    });
  }

  document.getElementById('push_configs_catalog').innerHTML = catalog_configs_options_list;
}

/**
 * Hides the action "Claim to Intersight" in the Actions button
 */
function disableClaimToIntersight(){
  $("#action-claim-to-intersight").hide();
}

/**
 * Hides the action "Clear Config" in the Actions button
 */
function disableClearConfig(){
  $("#action-clear-config").hide();
}

/**
 * Displays the device
 * @param  {JSON} data - Optional: The data returned after getting a device from the API
 */
function displayDevice(data){
  if(!data){
    console.error('No data to display!')
    return
  }

  data = JSON.parse(data);

  if(!data.device || data.device.length == 0){
    console.error('No data to display!')
    redirectToHome();
    return
  }

  // We refresh the device displayed only if there were changes in the data
  if(_.isEqual(current_device, data.device)){
    return
  }

  // Stored the current device
  current_device = data.device;

  // Resets the DOM element
  document.getElementById('deviceCardContainer').innerHTML = "";
  var device_version = "unknown"
  if(current_device.device_version != undefined){
    device_version = current_device.device_version;
  }
  var username_element = `
  <div class = "col">
    Username: 
  </div>
  <div class = "col text-right text-truncate" data-toggle="tooltip" data-placement="right" title="${current_device.username}">
    ${current_device.username}
  </div> 
  `

  // Changes the style of the card based on the type of device
  if(current_device.device_type == "intersight"){
    username_element = `
    <div class = "col">
      Key ID: 
    </div>
    <div class = "col text-right text-truncate" data-toggle="tooltip" data-placement="right" title="${current_device.key_id}">
      ${current_device.key_id}
    </div>
    `
    avatar_src = "/static/img/intersight_logo.png";
    color = "bg-info";
    enableClearConfig();
  } else if (current_device.device_type == "ucsm"){
    avatar_src = "/static/img/ucsm_logo.png";
    color = "bg-primary";
    enableClaimToIntersight();
    enableClearIntersightClaimStatus();
    enableClearSelLogs();
    enableRegenerateCertificate();
  } else if (current_device.device_type == "cimc"){
    avatar_src = "/static/img/cimc_logo.png";
    color = "bg-warning";
    enableClaimToIntersight();
    enableClearIntersightClaimStatus();
    enableClearSelLogs();
    enableRegenerateCertificate();
  } else if (current_device.device_type == "ucsc"){
    avatar_src = "/static/img/ucsc_logo.png";
    color = "bg-dark";
  }

  // Resets claim information badge
  document.getElementById('deviceClaimContainer').innerHTML = ``;

  // Sets claim information badge if the device is claimed
  if(current_device.device_connector_claim_status){
    if(current_device.device_connector_claim_status == "claimed"){
      disableClaimToIntersight();
      var claimed_target = `${current_device.device_connector_ownership_name}`;
      if(current_device.intersight_device_uuid){
        claimed_target = `<a href="/devices/${current_device.intersight_device_uuid}">${current_device.device_connector_ownership_name}</a>`
      }

      document.getElementById('deviceClaimContainer').innerHTML = `
      <div class="card card-outline card-success">
        <div class="card-header align-middle">
          <div class = "user-block text-middle">
            <i class = "fas fa-check-circle text-success"></i>
            <span class="mx-2">Claimed to Intersight (${claimed_target}) by ${current_device.device_connector_ownership_user}</span>
          </div>
        </div>
      </div>
      `;
    }
  }

  // Creates the card and populates the container with it
  document.getElementById('deviceCardContainer').innerHTML = 
  `
  <div>
      <div class="card card-widget widget-user-2 mb-0">
        <div class="widget-user-header p-0">
          <div class = "row m-0">
            <div class = "col-md-6 ${color} p-3 d-flex flex-column justify-content-between rounded-left shadow">
              <div>
                <div class="widget-user-image">
                  <img class="img-circle elevation-2" src=${avatar_src} alt="Device Type">
                </div>
                <h3 class="widget-user-username text-truncate"data-toggle="tooltip" data-placement="top" title="${current_device.device_name}">
                ${current_device.device_name}
                </h3>
                <h5 class="widget-user-desc text-truncate" data-toggle="tooltip" data-placement="top" title="${current_device.device_type_long}">
                ${current_device.device_type_long}
                </h5>
              </div>
              <div class = "d-flex flex-row p-2">
                <div type = "button" class="mr-4 ${color} click-item" onclick="toggleEditDeviceModal(event)">
                  <i class="fas fa-edit"></i> Edit
                </div>
                <div type = "button" class="mr-4 ${color} click-item" onclick="deleteDevice(event)">
                  <i class="fas fa-trash"></i> Delete
                </div>
              </div>

            </div>

            <div class = "col-md-6 p-3 rounded-right">
              <ul class="nav flex-column">
                <li class="nav-item mw-100">
                  <div class="row p-2">
                    ${username_element}
                  </div>
                </li>
                <li class="nav-item mw-100">
                  <div class="row p-2">
                    <div class = "col">
                      Version: 
                    </div>
                    <div class = "col text-right text-truncate"data-toggle="tooltip" data-placement="right" title="${device_version}">
                    ${device_version}
                    </div>
                  </div>
                </li>
                <li class="nav-item mw-100">
                  <div class="row p-2">
                    <div class = "col">
                    Target: 
                    </div>
                    <div class = "col text-right text-truncate" data-toggle="tooltip" data-placement="right" title="${current_device.target}">
                      ${current_device.target}
                    </div>
                  </div>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
  </div>
  `;
}

/**
 * Displays the Intersight devices
 * @param  {JSON} data - Optional: The data returned after getting a list of devices from the API
 */
function displayIntersightDevices(data){
    if(!data){
      console.error('No data to display!');
      return
    }

    data = JSON.parse(data);

    if(!data.devices){
      return
    }

    var loaded_devices = data.devices;

    var intersight_devices_list = `
        <option hidden disabled selected value> -- Select an option -- </option>
    `;

    var intersight_device_number = 0;

    // Only displays devices of type Intersight
    loaded_devices.forEach(function (device) {
      if(device.is_system == false){
          intersight_device_number += 1;
          intersight_devices_list += `
          <option value="${device.device_uuid}">${device.target} (${device.device_name})</option>
          `
      }
    });

    if(intersight_device_number == 0){
        intersight_devices_list = `
        <option value="null">No Intersight device is currently available</option>
        `
    }

    document.getElementById('target_device').innerHTML = intersight_devices_list;
}

/**
 * Displays the Intersight orgs
 * @param  {JSON} data - Optional: The data returned after getting a list of orgs from the API
 */
function displayIntersightOrgs(data){
    if(!data){
      console.error('No data to display!');
      return
    }

    data = JSON.parse(data);

    if(!data.orgs){
      return
    }

    var loaded_orgs = data.orgs;

    var intersight_orgs_list = `
        <option hidden disabled selected value> -- Select an option -- </option>
    `;

    var intersight_org_number = 0;

    intersight_org_names = Object.keys(loaded_orgs);

    // Only displays devices of type Intersight
    intersight_org_names.forEach(function (org) {
      intersight_org_number += 1;
      intersight_org_descr = loaded_orgs[org].description
      if(intersight_org_descr != ""){
        intersight_orgs_list += `
        <option value="${org}">${org} - ${intersight_org_descr}</option>
        `
      } else {
        intersight_orgs_list += `
        <option value="${org}">${org}</option>
        `
      }
    });

    if(intersight_org_number == 0){
        intersight_orgs_list = `
        <option value="null">No Intersight org is currently available</option>
        `
    }

    document.getElementById('orgs_list').innerHTML = intersight_orgs_list;
}


/**
 * Displays an object
 * @param  {JSON} data - Optional: The data returned after getting a list of objects from the API
 */
function displayObjects(data){
  if(!data){
    console.error("Impossible to display objects: no data received ");
    return
  }
  
  data = JSON.parse(data);

  var loaded_object = null;
  var object_type = null;
  var table = null;

  // Determines which object has been loaded
  if(data.backups){
    loaded_object = data.backups;
    // We refresh the object displayed only if there were changes in the data
    if(_.isEqual(loaded_backup_list, loaded_object)){
      return
    }
    loaded_backup_list = loaded_object;
    object_type = "backup";
    table = backupTable;
  } else if (data.configs){
    loaded_object = data.configs;
    // We refresh the object displayed only if there were changes in the data
    if(_.isEqual(loaded_config_list, loaded_object)){
      return
    }
    loaded_config_list = loaded_object;
    object_type = "config";
    table = configTable;
  } else if (data.inventories){
    loaded_object = data.inventories;
    // We refresh the object displayed only if there were changes in the data
    if(_.isEqual(loaded_inventory_list, loaded_object)){
      return
    }
    loaded_inventory_list = loaded_object;
    object_type = "inventory";
    table = inventoryTable;
  } else if (data.reports){
    loaded_object = data.reports;
    // We refresh the object displayed only if there were changes in the data
    if(_.isEqual(loaded_report_list, loaded_object)){
      return
    }
    loaded_report_list = loaded_object;
    object_type = "report";
    table = reportTable;
  } else if (data.orgs){
    console.log(data.orgs)
    loaded_object = data.orgs;
  } else {
    return
  }

  var current_table = table;

  // Clean table before new entries
  current_table.clear().draw();



  // Creates a row for each object loaded
  loaded_object.forEach(function (object) {
    var object_name = setObjectName(object, object_type);
    var date_timestamp = new Date(object.timestamp);
    var on_click = `window.location='/devices/${object.device_uuid}/${object_type}/${object.uuid}';`;
    date_timestamp = Date.parse(date_timestamp)/1000;

    var object_data = JSON.stringify({
      "object_name": object_name,
      "object_uuid": object.uuid,
      "object_type": object_type
    })

    current_table.row.add($(`
    <tr style="cursor: pointer;">
      <td>${object_data}</td>
      <td onclick="${on_click}">${object_name}</td>
      <td onclick="${on_click}">${object.origin}</td>
      <td data-order="${date_timestamp}" onclick="${on_click}">${object.timestamp}</td>
      <td onclick="${on_click}">${object.easyucs_version}</td>
    </tr>`)).draw();
  });

  // If the object is a config or an inventory, we also need to add it to the options when pushing config or generating report
  if(object_type == "config" || object_type == "inventory"){
    var object_options_list = "";

    if(loaded_object.length < 1){
      object_options_list = `
      <option value="null">No ${object_type} available on this device</option>
      `
    } else {
      loaded_object.forEach(function (object) {
        object_name = setObjectName(object, object_type);
        object_options_list += `
          <option value="${object.uuid}">${object_name}</option>
        `
      });
    }
    if(object_type == "config"){
      document.getElementById('configs_options').innerHTML = object_options_list;
      document.getElementById('push_configs_imported').innerHTML = object_options_list;
    } else if (object_type == "inventory"){
      document.getElementById('inventories_options').innerHTML = object_options_list;
    }
  } else if(object_type == "orgs"){
    console.log("youpi")
    var object_options_list = "";
    if(loaded_object.length < 1){
      object_options_list = `
      <option value="null">No ${object_type} available on this device</option>
      `
    } else {
      loaded_object.forEach(function (object) {
        object_name = setObjectName(object, object_type);
        object_options_list += `
          <option value="${object.uuid}">${object_name}</option>
        `
      });
    }
    if (object_type == "orgs"){
      document.getElementById('orgs_list').innerHTML = object_options_list;
    }
  }
}

/**
 * Downloads a list of objects
 * @param  {String} object_type - The type of object selected {backup/config/inventory/report}
 */
async function downloadObjects(object_type){
  if(!object_type in ['backup', 'config', 'inventory', 'report']){
    console.error('Impossible to download object: wrong object type - ', object_type);
    return
  }

  if(selected_objects[object_type].length > bulk_actions_limit){
    raiseBulkActionLimitAlert(selected_objects[object_type].length);
    return
  }

  for(object of selected_objects[object_type]){
      download(object_type, current_device_uuid, object["object_uuid"]);

      // We wait 1sec before launching the download of the next object
      await new Promise(resolve => setTimeout(resolve, 1000));
  }
}

/**
 * Shows the action "Claim to Intersight" in the Actions button
 */
function enableClaimToIntersight(){
  $("#actions-separator").show();
  $("#action-claim-to-intersight").show();
}

/**
 * Shows the action "Clear Config" in the Actions button
 */
function enableClearConfig(){
  $("#actions-separator").show();
  $("#action-clear-config").show();
}

/**
 * Shows the action "Clear Intersight Claim Status" in the Actions button
 */
function enableClearIntersightClaimStatus(){
  $("#actions-separator").show();
  $("#action-clear-intersight-claim-status").show();
}

/**
 * Shows the action "Enable Clear SEL Logs" in the Actions button
 */
function enableClearSelLogs(){
  $("#actions-separator").show();
  $("#action-clear-sel-logs").show();
}

/**
 * Shows the action "Regenerate Certificate" in the Actions button
 */
function enableRegenerateCertificate(){
  $("#actions-separator").show();
  $("#action-regenerate-certificate").show();
}

/**
 * Fetches an object from the device
 * @param  {String} object_type - The type of object to fetch {backup/config/inventory}
 */
function fetchLiveObjectFromDevice(object_type){
  if (!object_type in ["backup", "config", "inventory"]){
    console.error("Impossible to fetch live " + object_type + " - Wrong object type");
    return
  }

  if(!current_device_uuid){
    console.error("Impossible to fetch live object of type: " + object_type + " from device - No device UUID provided");
    return
  }

  // Fetches the object and creates an alert
  fetchLiveObject(alertObjectFetched.bind(null, object_type), object_type, current_device_uuid);
}

/**
 * Generates a report from a config and an inventory
 */
function generateReport(){
  var params = {};
  var form_content = $('#generateReportForm').serializeArray();
  var form_json = objectifyForm(form_content);

  if(!form_json.inventory_uuid || !form_json.config_uuid){
    console.error("Error generating report: wrong parameters specified");
    return
  }

  if(form_json.inventory_uuid == "null" || form_json.config_uuid == "null"){
    console.error("Error generating report: missing config or inventory");
    displayAlert("Error generating report:", "Missing configuration or inventory");
    return
  } else {
    params["config_uuid"] = form_json.config_uuid;
    params["inventory_uuid"] = form_json.inventory_uuid;
  }

  // Get the output format
  var output_formats = [];
  if(form_json.output_format && ["docx", "pdf"].includes(form_json.output_format)){
    output_formats.push(form_json.output_format);
  } else {
    // We default to Word (docx)
    output_formats.push("docx");
  }
  params["output_formats"] = output_formats;

  target_api_endpoint = api_base_url + api_device_endpoint + "/" + current_device_uuid +"/reports/actions/generate";
  const action_type_message = "Generating Report";

  // Generates the report and creates an alert
  httpRequestAsync("POST", target_api_endpoint, alertActionStarted.bind(null,action_type_message), params);

  // Closes the modal
  $('#generateReportModal').modal('toggle');
}

/**
 * Gets a list of catalog configs for a device
 * @param  {String} selected_tab - Optional: The tab selected by the user
 */
function getCatalogConfigsFromDevice(data){
  if(!data){
    console.error('No data to display!')
    return
  }

  data = JSON.parse(data);

  if(!data.devices){
      console.error('No data to display!')
      return
  }


  system_catalog_device = data.devices.find(device => {
      return device.device_type == current_device.device_type;
  });

  if(!system_catalog_device){
      console.error('No device of the type ' + current_device.device_type + ' to display!')
      return
  }

  getFromDb(callback=displayCatalogConfigs, object_type="config", device_uuid=system_catalog_device.device_uuid);
}

/**
 * Gets the device corresponding to the UUID in the URL
 */
function getDevice(){
  if(!current_device_uuid){
    console.error("Impossible to get device - No device UUID provided");
    return
  }
  filter = ["is_system", "==", "false"];
  getFromDb(callback = displayDevice, object_type =  "device", device_uuid = current_device_uuid, uuid = null, filter = filter);
}

/**
 * Gets the logs of the device corresponding to the UUID in the URL
 */
function getDeviceLogs(){
  var target_api_endpoint = api_base_url + api_device_endpoint + "/" + current_device_uuid +"/logs";

  // When logs are fetched, they are added to the session logs
	httpRequestAsync("GET", target_api_endpoint, addLogs);
}

/**
 * Gets the list of Intersight devices from the API
 */
function getIntersightDevices(){
  // Only gets the Intersight devices
  var filter = ["device_type", "==", "intersight"]
  getFromDb(callback = displayIntersightDevices, object_type = "device", device_uuid = null, uuid = null, filter = filter);
}

/**
 * Gets the list of Intersight orgs from the API
 */
function getIntersightOrgs(){
  getFromDb(callback = displayIntersightOrgs, object_type = "orgs", device_uuid = current_device_uuid, uuid = null, filter = filter);
}

/**
 * Gets all existing objects of a certain type from the loaded device
 * @param  {String} object_type - The type of object to get {backup/config/inventory/report}
 */
function getObjectsFromDevice(object_type){
  if (!object_type in ["backup", "config", "inventory", "report"]){
    console.error("Impossible to get object of type: " + object_type + " - Wrong type");
    return
  }

  if(!current_device_uuid){
    console.error("Impossible to get object of type: " + object_type + " - No device UUID provided");
    return
  }

  // Displays the objects after loading them
  getFromDb(displayObjects, object_type, current_device_uuid);
}


/**
 * Gets the list of Intersight devices from the API
 */
function getSystemDevice(){
  // Only gets the Intersight devices
  var filter = ["system_usage", "==", "catalog"]
  getFromDb(callback = getCatalogConfigsFromDevice, object_type = "device", device_uuid = null, uuid = null, filter = filter);
}

/**
 * Imports a configuration to the device
 * @param  {Event} event - The event associated to the file import
 * @param  {Boolean} import_for_push - Set to true if the config is imported to be pushed on the device, false otherwise
 * @param  {FileList} files - The imported config file
 */
function importConfig(event, import_for_push = false, files){
  // import_for_push is set to true only when the importConfig function is used prior to pushing a new config file to the device
  if(import_for_push){
    if(files){
      pushToDb(pushConfig, "config", current_device_uuid, null, files);
    } else {
      console.error("No file(s) specified for import before pushing");
    }
    return
  }

  if(!event){
    console.error('Error while collecting the file(s)');
    return
  }

  var file_list = event.target.files;

  pushToDb(refreshObject.bind(null, "config"), "config", current_device_uuid, null, file_list);
}

/**
 * Imports an inventory to the device
 * @param  {Event} event - The event associated to the file import
 */
function importInventory(event){
  if(!event){
    console.error('Error while collecting the file(s)');
    return
  }
  var file_list = event.target.files;
  pushToDb(refreshObject.bind(null, "inventory"), "inventory", current_device_uuid, null, file_list);
}

/**
 * Opens the hidden DOM element to allow file import for a specific file type
 * @param  {String} file_type - The type of file to import {config/inventory}
 */
function openImportFileDialog(file_type){
  if(file_type == "config"){
    document.getElementById('importConfigDialog').click();
  }
  if(file_type == "inventory"){
    document.getElementById('importInventoryDialog').click();
  }
}

/**
 * Pushes a configuration to the device
 * @param  {JSON} data - Optional: The data returned after a config is imported (not used if the config pushed already exists)
 */
async function pushConfig(data){
  new_config_uuid = "";
  var push_type = document.querySelector('input[name="push_type"]:checked').value;

  // If the config to push is from a new file
  if(push_type == "new_file"){
    /* 
    If there is data, it means that pushConfig is used as a callback from importConfig:
    This happens when the user pushes a new config file and the config has successfully been imported
    Before the file has been imported, it will then first go in the else to import the config before the push
    */
    if(data){
      var form_content = $('#pushConfigForm').serializeArray();
      var form_json = objectifyForm(form_content);
      data = JSON.parse(data);

      // We collect the config UUID of the config imported by the user
      new_config_uuid = data.config.uuid;

    // Otherwise, we first need to import the config before pushing it
    } else {
      // We collect the config file the user has selected
      var new_config_files = document.getElementById("push_configs_new");
      
      if(!new_config_files || new_config_files.files.length<=0){
        console.error("Error pushing config: no config file specified");
      } else {
        // We import the config and push the config as callback within importConfig
        importConfig(null, true, new_config_files.files);
      }
      return
    }
  
  // Otherwise, the config already exists and we only need to push it
  } else {
    var form_content = $('#pushConfigForm').serializeArray();
    var form_json = objectifyForm(form_content);
    
    if(!form_json.config_uuid){
      console.error("Error pushing config: no config specified");
      return
    }

    // We collect the config UUID the user has selected
    new_config_uuid = form_json.config_uuid;
  }

  if(new_config_uuid == ""){
    console.error("Error pushing config: empty config uuid");
    return
  }

  var setup = [];
  var params = {};

  params["reset"] = false;

  // We delete the form parameters as we only want to collect them if the user has checked the corresponding checkboxes
  delete form_json["config_uuid"];    
  delete form_json["dhcp_ip_fabA"];
  delete form_json["dhcp_ip_fabB"];
  delete form_json["dhcp_ip_cimc"];

  // If the user has checked the reset checkbox
  if(form_json.reset && form_json.reset == "on"){
    var user_confirmation = await Swal.fire({  
      title: "Do you really want to erase all configuration on this device?",
      text: current_device.device_name,
      showDenyButton: true, 
      confirmButtonText: `Yes`,  
      denyButtonText: `No`,
    }).then((result) => {  
        if (result.isConfirmed) {
          form_json.reset = true;
          params["reset"] = true;  
          return true; 
        } else {
          return false;
        }
    });

    if(!user_confirmation){
      return
    }
  }

  // If the user has checked the setup checkbox
  if(form_json.setup && form_json.setup == "on"){

    // Checks the device type to collect the relevant parameters
    if(current_device.device_type == "ucsm"){
      dhcp_ip_fabA = document.getElementById('dhcp_ip_fabA').value;
      dhcp_ip_fabB = document.getElementById('dhcp_ip_fabB').value;

      // Checks if the IP address of the DHCP IP are correct
      if(!validateIPaddress(dhcp_ip_fabA)){
        displayAlert("Impossible to push config", "DHCP IP of Fabric A is not an IP address", "error");
        return
      }
      if(!validateIPaddress(dhcp_ip_fabB)){
        displayAlert("Impossible to push config", "DHCP IP of Fabric B is not an IP address", "error");
        return
      }
      setup.push(dhcp_ip_fabA);
      setup.push(dhcp_ip_fabB);
    } else if (current_device.device_type == "cimc"){
      dhcp_ip_cimc = document.getElementById('dhcp_ip_cimc').value;

      // Checks if the IP address of the DHCP IP is correct
      if(!validateIPaddress(dhcp_ip_cimc)){
        displayAlert("Impossible to push config", "DHCP IP of CIMC is not an IP address", "error");
        return
      }
      setup.push(dhcp_ip_cimc);
    }

    // Sets the DHCP IP values in the parameter dictionary
    params["fi_ip_list"] = setup;
  }


  target_api_endpoint = api_base_url + api_device_endpoint + "/" + current_device_uuid +"/configs/" + new_config_uuid + "/actions/push";
  httpRequestAsync("POST", target_api_endpoint, alertObjectPushed.bind(null, "config"), params);
  $('#pushConfigModal').modal('toggle');
}

/**
 * Redirects the user to the homepage
 */
function redirectToHome(){
  window.location.href = "/";
}

/**
 * Refreshes dynamic data on the page
 */
function refreshData(){
  getDevice();
  getObjectsFromDevice("backup");
  getObjectsFromDevice("config");
  getObjectsFromDevice("inventory");
  getObjectsFromDevice("report");
}

/**
 * Refreshes dynamic data linked to a specific object type on the page
 * @param  {String} object_type - The type of object to fetch {backup/config/inventory}
 */
function refreshObject(object_type){
  if (!object_type in ["backup", "config", "inventory", "report"]){
    console.error("Impossible to refresh object " + object_type + ": Wrong object type");
    return;
  }
  getObjectsFromDevice(object_type);
}

/**
 * Shows DHCP IP fields when "setup" checkbox is checked for pushing a config
 */
function showFabricFields(){
  if(document.getElementById('setup').checked && current_device.device_type == "ucsm"){
    $('#collapsedFabricFields_ucsm').collapse('show');
    $('#collapsedFabricFields_cimc').collapse('hide');
  } else if (document.getElementById('setup').checked && current_device.device_type == "cimc") {
    $('#collapsedFabricFields_ucsm').collapse('hide');
    $('#collapsedFabricFields_cimc').collapse('show');
  } else {
    $('#collapsedFabricFields_ucsm').collapse('hide');
    $('#collapsedFabricFields_cimc').collapse('hide');
  }
}

/**
 * Toggles the modal with the form to perform a claim to intersight
 * @param  {Event} event - The click event
 */
function toggleClaimToIntersightModal(event){
  removeEventPropagation(event);
  getIntersightDevices();
  $('#claimToIntersightModal').modal('toggle');
}

/**
 * Toggles the modal with the form to perform a clear config
 * @param  {Event} event - The click event
 */
function toggleClearConfigModal(event){
  removeEventPropagation(event);
  getIntersightOrgs();
  $('#clearConfigModal').modal('toggle');
}

/**
 * Toggles the modal with the form to edit a device
 * @param  {Event} event - The click event
 */
function toggleEditDeviceModal(event){
  removeEventPropagation(event);

  // Populates the fields of the modal
  document.getElementById('edit_device_label').innerText = "Editing device: " + current_device.device_name;
  document.getElementById('edit_target').value = current_device.target;

  // Shows the relevant form elements based on the device type
  if(current_device.device_type == "intersight"){
    document.getElementById('intersight-device-edit-form').classList.remove('d-none');
    document.getElementById('ucs-device-edit-form').classList.add('d-none');
    document.getElementById('edit-bypass-version-checks-form').classList.remove('d-none');
    document.getElementById('edit_key_id').value = current_device.key_id;
    document.getElementById('edit_key_id').disabled = false;
    document.getElementById('edit_private_key').disabled = false;
    document.getElementById('edit_username').disabled = true;
    document.getElementById('edit_password').disabled = true;
    document.getElementById('edit_bypass_version_checks').disabled = false;
    if(current_device.bypass_version_checks){
        document.getElementById('edit_bypass_version_checks').checked = true;
    }
  } else {
    document.getElementById('intersight-device-edit-form').classList.add('d-none');
    document.getElementById('ucs-device-edit-form').classList.remove('d-none');
    document.getElementById('edit-bypass-version-checks-form').classList.remove('d-none');
    document.getElementById('edit_username').value = current_device.username;
    document.getElementById('edit_key_id').disabled = true;
    document.getElementById('edit_private_key').disabled = true;
    document.getElementById('edit_username').disabled = false;
    document.getElementById('edit_password').disabled = false;
    document.getElementById('edit_bypass_version_checks').disabled = false;
    if(current_device.bypass_version_checks){
        document.getElementById('edit_bypass_version_checks').checked = true;
    }
  }

  document.getElementById('editDeviceSubmitButton').setAttribute('onclick',`updateDevice()`);
  $('#editDeviceModal').modal('toggle');
}

/**
 * Toggles the modal with the form to generate a report
 * @param  {Event} event - The click event
 */
function toggleGenerateReportModal(event){
  removeEventPropagation(event);
  $('#generateReportModal').modal('toggle');
}

/**
 * Hides/Shows the object actions button based on the number of objects selected and the object type
 * @param  {Object} selected_objects - The dictionary containing the list of selected objects for each type
 */
function toggleObjectActionsButton(selected_objects){
  for(object_type of ['backup', 'config', 'inventory', 'report']){
    if(selected_objects[object_type].length > 0){
      $(`#${object_type}TableButtonContainer`).removeClass('d-none');
    } else {
      $(`#${object_type}TableButtonContainer`).addClass('d-none');
    }
  }

  // Only allows the push operation if a single config is selected
  if(selected_objects['config'].length > 1){
    $('#pushConfigTableButton').addClass('disabled');
  } else {
    $('#pushConfigTableButton').removeClass('disabled');
  }
}

/**
 * Toggles the modal with the form to push a config
 * @param  {Event} event - The click event
 * @param  {Boolean} populate - If set to true, pre-populates some of the form fields
 */
function togglePushConfigModal(event, populate = false){
  getSystemDevice();

  removeEventPropagation(event);

  // If the user pushes a config by selecting it from the table,we pre-populate the form fields
  if(populate){
    // We pre-select the import config radio button
    document.getElementById("current_configs").checked = true;
    // We trigger the collapsed elements to show import config in the popup
    $('#collapsedImportedConfigs').collapse('show');
    $('#collapsedNewFile').collapse('hide');
    $('#collapsedCatalogConfigs').collapse('hide');
    // We pre-populate the selection drop-down with the selected config (the first in the array given that we only allow for one selected config)  
    document.getElementById("push_configs_imported").value= selected_objects["config"][0]["object_uuid"];
  }
  $('#pushConfigModal').modal('toggle');
}

/**
 * Updates the device
 */
function updateDevice(){
  form_content = $('#editDeviceForm').serializeArray();
  form_json = objectifyForm(form_content);

  // If the password is unchanged, we don't send it for update
  if(form_json.password == ""){
    delete form_json.password;
  }

  // If the private_key is unchanged, we don't send it for update
  if(form_json.private_key == ""){
    delete form_json.private_key;
  }

  // Adapt bypass_version_checks value to boolean
  if(form_json.bypass_version_checks == "on"){
    form_json.bypass_version_checks = true
  } else if(!form_json.bypass_version_checks){
    form_json.bypass_version_checks = false
  }

  // Reloads the device from the db after performing the update
  updateToDb(getDevice, "device", current_device_uuid, null, form_json);

  // Closes the modal
  $('#editDeviceModal').modal('toggle');
}


