/*
home.js is the javascript used to animate the page home.html

All functions present here are solely used on the home.html page

NOTE: the home.html page displays all the devices registered by the user in EasyUCS
*/

// Global variables
var loaded_device_list = [];
var filter_string = "";

var deviceTable = null;
var device_view = "grid";
const device_view_container_id = 'deviceViewContainer';

// The max number of elements displayed on the first load with the grid view
var max_grid_elements_displayed = 18;

// The number of elements we add to the display for each lazy load
var nb_additional_elements = 8;

var total_grid_elements_displayed = 0;


// Gets executed when DOM has loaded
function afterDOMloaded() {
  // Adding class to menu element in base.html to reflect that it is open
  document.getElementById("navLinkDevices").className += " active" 
  
  // Forces page reload when using browser back button
  if(typeof window.performance != "undefined" && window.performance.navigation.type == 2){
    window.location.reload(true);
  }

  var screen_width = window.innerWidth || document.documentElement.clientWidth || document.body.clientWidth;
  
  if(screen_width > 1800){
    max_grid_elements_displayed = 26;
    nb_additional_elements = 12; 
  } else if (screen_width > 2400){
    max_grid_elements_displayed = 50;
    nb_additional_elements = 20; 
  }

  // We get all the devices when page is first loaded
  refreshData(); 
};

/**
 * Lazy loading: Gets executed when the user reaches the end of the scrolling window
 * This loads new device elements.
 */
window.addEventListener('scroll', () => {

  // Only performs lazy loading if this is grid view and all the data hasn't yet been displayed
  if(device_view == "grid" && loaded_device_list.length > (total_grid_elements_displayed)){
    const {scrollHeight,scrollTop,clientHeight} = document.documentElement;

    // Fires when user has scrolled down the page (up to 5px before bottom)
    if(scrollTop + clientHeight > scrollHeight - 5){

      // Displays the loader
      addScrollLoader(device_view_container_id);

      // Only executes every 1.5sec to avoid firing multiple times in a row
      setTimeout(function() {
        const new_elements_displayed = Math.min(total_grid_elements_displayed + nb_additional_elements - 1, loaded_device_list.length);

        // Only adds the latest elements from the list
        addDevicesGridView(device_view_container_id, loaded_device_list, total_grid_elements_displayed, new_elements_displayed);
        total_grid_elements_displayed = new_elements_displayed;
      }
      , 1500); // Timeout of X [in milliseconds]
    }
  }
});

/**
 * Returns an HTML card for a device
 * @param  {device} device - The details of the device
 * @returns {String} innerHTML - The HTML content of the card
 */
function createDeviceCard(device, phantom=false){
  var device_version = "unknown"
  if(device.device_version != undefined){
    device_version = device.device_version;
  }
  var username_element = `
  <div class = "col-md-auto">
    Username: 
  </div>
  <div class = "col text-right text-truncate">
    ${device.username}
  </div> 
  `
  // Creates different UI elements and styles based on the device type
  if(device.device_type == "intersight"){
    username_element = `
    <div class = "col">
      Key ID: 
    </div>
    <div class = "col text-right text-truncate">
      ${device.key_id}
    </div>
    `
    avatar_src = "/static/img/intersight_logo.png";
    color = "bg-info"
  } else if (device.device_type == "imm_domain"){
    avatar_src = "/static/img/imm_domain_logo.png";
    color = "bg-success";
  } else if (device.device_type == "ucsm"){
    avatar_src = "/static/img/ucsm_logo.png";
    color = "bg-primary"
  } else if (device.device_type == "cimc"){
    avatar_src = "/static/img/cimc_logo.png";
    color = "bg-warning"
  } else if (device.device_type == "ucsc"){
    avatar_src = "/static/img/ucsc_logo.png";
    color = "bg-dark"
  }
  let onclick = "null";
  if (!phantom) {  
    onclick = `window.location='/devices/${device.device_uuid}';`
  }
  let device_tasks_count = getDeviceTasksCount(device.device_uuid);
  innerHTML = `
    <div class="${phantom && 'phantomDevice'} col-sm-6 col-md-4 col-xl-3 col-xxl-2">
        <div class="card card-widget widget-user-2" style="cursor: pointer;" 
        onclick=${onclick}>
          <div class="widget-user-header ${color}">
            <div class="widget-user-image">
              <img class="img-circle elevation-2" src=${avatar_src} alt="Device Type">
            </div>
              <p class="text-warning float-right device-tasks-counter ${device.device_uuid}" 
              style="${device_tasks_count > 0 ? "" : "display: none;"}" title="Ongoing tasks" data-toggle="tooltip">
                <i class="fa-solid fa-clock-rotate-left"></i>
                <span class="device-tasks-counter-badge">${device_tasks_count}</span>
              </p>
            <h3 class="widget-user-username text-truncate">${phantom ? "Adding device..." : device.device_name }</h3>
            <h5 class="widget-user-desc text-truncate">${phantom ? device.device_type : device.device_type_long}</h5>
          </div>
          <p title="User Label" class="m-0 badge-light badge ${device.user_label ? "text-dark" : "text-light"}">${device.user_label ? device.user_label : "."}</p>
          <div class="card-body">
            <ul class="nav flex-column">
              <li class="nav-item mw-100">
                <div class="row py-2">
                  ${username_element}
                </div>
              </li>
              <li class="nav-item mw-100">
                <div class="row py-2">
                  <div class = "col-md-auto">
                    Version: 
                  </div>
                  <div class = "col text-right text-truncate">
                  ${device_version}
                  </div>
                </div>
              </li>
              <li class="nav-item mw-100">
                <div class="row py-2">
                  <div class = "col-md-auto">
                  Target: 
                  </div>
                  <div class = "col flex text-right text-truncate">
                    ${device.target}
                  </div>
                </div>
              </li>
            </ul>
          </div>
          <div class="card-footer">
            <div class="row">
              <div class="col-md-6">
                <button type="button" class="btn btn-block btn-outline-secondary" onclick="toggleEditDeviceModal(event, '${device.device_uuid}')">Edit</button>
              </div>
              <div class="col-md-6">
                <button type="button" class="btn btn-block btn-outline-danger" onclick="deleteDevice(event, '${device.device_uuid}')">Delete</button>
              </div>
            </div>
          </div>
        </div>
    </div>
    `
    return innerHTML;
}

/**
 * Adds a Grid of cards to an HTML element for a list of devices
 * @param  {String} element_id - The ID of the DOM element in which to add the grid
 * @param  {Array} devices - The list of devices
 * @param  {Number} start_index - The first index of the list from which we start displaying
 * @param  {Number} stop_index - The last index of the list for which we stop displaying
 */
function addDevicesGridView(element_id, devices, start_index, stop_index){
  // If we have a search query, we filter the result of devices to display
  if(filter_string != ""){
    devices = devices.filter( device => {
      // The components on which we want to test the search query
      var filteredComponents = [device.device_name, device.device_type_long, device.device_version, 
        device.target, device.username, device.device_type];
      
      // If the search query is not part of the device, we do not display it
      if(!arrayContainsSubstring(filteredComponents, filter_string)){
        // Skips current device
        return false;
      }
      return true;
    });
  }

  // Creates a card for each device of the devices list within the start_index and stop_index
  devices.slice(start_index, stop_index).map( device => {
    // Adds the card to the DOM element
    document.getElementById(element_id).innerHTML += createDeviceCard(device);
  });

  // Removes the loader
  removeScrollLoader();
}


/**
 * Adds a table to an HTML element for a list of devices
 * @param  {String} element_id - The ID of the DOM element in which to add the table
 * @param  {Array} devices - The list of devices
 */
function addDevicesTableView(element_id, devices){
  // We initialize the DOM element with an empty array
  document.getElementById(element_id).innerHTML = 
  `
  <div class = "col-md-12">
    <div class="tab-content" id="nav-tabContent">
      <div class="card">
        <div class="card-body">
          <form id="deviceActionForm" onchange="onSelectedObjectsChanged('device');">
            <div class="row">
              <div id="deviceTableButtonContainer" class="col-md-12 d-none">
                <button type="button" class="btn btn-success dropdown-toggle mb-3" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">Actions</button>
                <div class="dropdown-menu" aria-labelledby="dropdownMenuButton">
                  <a id="claimToIntersightAction" class="dropdown-item" type="submit" onclick="toggleClaimToIntersightMultipleDevicesModal(event)"><span class="mr-2" style="width: 20px; display: inline-block"><i class="fa-solid fa-cloud-arrow-up"></i></span>Claim Device(s) to Intersight</a>
                  <a id="ResetDeviceConnectorAction" class="dropdown-item" type="submit" onclick="ResetDeviceConnectorMultipleDevices()"><span class="mr-2" style="width: 20px; display: inline-block"><i class="fa-solid fa-plug-circle-xmark"></i></span>Reset Device(s) Intersight Device Connector</a>
                  <div class="dropdown-divider"></div>
                    <a class="dropdown-item" type="submit" onclick="deleteMultipleDevices()"><span class="mr-2" style="width:20px; display: inline-block"><i class="fa-solid fa-trash"></i></span>Delete Device(s)</a>
                  </div>
                </div>
              </div>
              <table id="deviceTable" class="table table-bordered table-striped table-hover">
                <thead>
                  <tr>
                    <th><input type="checkbox" id="deviceTable_selectAll" name="select_all" value="1" onclick = "handleSelectAll('device', this);"></th>
                    <th>Device type</th>
                    <th>Device name</th>
                    <th>User label</th>
                    <th>Creation date</th>
                    <th>Intersight claim status</th>
                    <th>Username</th>
                    <th>Version</th>
                    <th>Target</th>
                  </tr>
                </thead>
                <tbody>
                </tbody>
              </table>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
  `

  // Initializes the DataTable that will contain the devices
  deviceTable = createDataTable("#deviceTable", 4, 4);

  // Clean table before new entries
  deviceTable.clear().draw();

  // For each device, we create the specific row in the DataTable
  devices.map( device => {
    deviceTable.row.add($(createRowForDevice(device)));
  });
  deviceTable.draw();
  // Removes the loader
  removeScrollLoader();
}

/**
 * Adds a Scroll Loader to an HTML element
 * @param  {String} element_id - The ID of the DOM element in which to add the scroll loader
 * @param  {Boolean} full - Optional: Set to true if the loader must take its full parent component
 */
function addScrollLoader(element_id, full = false){
  if(full){
    document.getElementById(element_id).innerHTML = ``;
  }
  const scroll_loader_element = document.getElementById("loaderContainer");
  if(!scroll_loader_element){
    document.getElementById(element_id).innerHTML += `
    <div id = "loaderContainer" class = "col-md-12 d-flex flex-column justify-content-center align-items-center">
      <img src="/static/img/loader_dots.gif" alt="Loader" height="75" width="75">
    </div>
    `;
  }
}

/**
 * Claims to Intersight a list of selected devices - devices are selected through the checkboxes
 */
function claimToIntersightMultipleDevices(){

  if(selected_objects["device"].length > bulk_actions_limit){
    raiseBulkActionLimitAlert(selected_objects["device"].length);
    return
  }

  var object_name_list = [];
  var object_uuid_list = [];

  for(obj of selected_objects["device"]){
    object_name_list.push(" " + obj["device_name"]);
    object_uuid_list.push(obj["device_uuid"]);
  }

  var form_content = $('#claimToIntersightMultipleDevicesForm').serializeArray();
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

  form_json["device_uuids"] = object_uuid_list

  const target_api_endpoint = api_base_url + api_device_endpoint + "/actions/claim_to_intersight";
  const action_type_message = "Claiming device(s) to Intersight";
  httpRequestAsync("POST", target_api_endpoint, alertActionStarted.bind(null,action_type_message), form_json);

  // Closes the modal
  $('#claimToIntersightMultipleDevicesModal').modal('toggle');
}

/**
 * Changes the content of the form to create a new device based on the device type chosen
 * @param  {String} device_type - The type of the device chosen
 */
function completeDeviceForm(device_type){
  if(!device_type){
    console.error("Impossible to complete form: no device_type provided");
    return;
  }
  // Show the target input
  document.getElementById('target-input-container').classList.remove("d-none");  
  const targetElement = document.getElementById('target')
  targetElement.readOnly = false;
  targetElement.value = "";
  // Changes which elements are displayed based on the device type

  if(device_type == "intersight"){
    // Disable UCS specific sections
    document.getElementById('ucs-device-form').classList.add("d-none");
    document.getElementById('username').disabled = true;
    document.getElementById('password').disabled = true;
    // Show Intersight-specific sections
    document.getElementById('key_id').disabled = false;
    document.getElementById('private_key').disabled = false;
    document.getElementById('intersight-device-form').classList.remove("d-none");
    document.getElementById('intersight-type-choice').classList.remove("d-none");
    updateIntersightTargetSelector("saas");
    document.getElementById('deployment_type_saas').checked = true;
    document.getElementById('use-proxy-form').classList.remove("d-none");
  } else {
    // Show UCS specific sections
    document.getElementById('ucs-device-form').classList.remove("d-none");
    document.getElementById('username').disabled = false;
    document.getElementById('password').disabled = false; 
    // Disable Intersight-specific sections
    document.getElementById('intersight-device-form').classList.add("d-none");
    document.getElementById('intersight-type-choice').classList.add("d-none");
    document.getElementById('intersight-region-choice').classList.add("d-none");
    document.getElementById('key_id').disabled = true;
    document.getElementById('private_key').disabled = true;
  }
  document.getElementById('bypass-connection-check-form').classList.remove("d-none");
}

/**
 * Shows the region selector or hides it based on the deployment type chosen
 * @param {String} deploymentType // The type of deployment chosen, can be "saas" or "virtual"
 */
function updateIntersightTargetSelector(deploymentType) {
  const targetElement = document.getElementById("target");
  document.getElementById('target-input-container').classList.remove("d-none");
  if (deploymentType == "saas") {
    targetElement.readOnly = true;
    document.getElementById('intersight-region-choice').classList.remove("d-none");
    const defaultRegionChoice = document.getElementById("intersight_region_us");
    targetElement.value = defaultRegionChoice.value;
    defaultRegionChoice.checked = true;
  } else if (deploymentType == "virtual") {
    targetElement.readOnly = false;
    targetElement.value = "";
    document.getElementById('intersight-region-choice').classList.add("d-none");
  }
}

function updateIntersightTarget(regionUrl) {
  const targetElement = document.getElementById("target");
  targetElement.value = regionUrl;
}

/**
 * Creates a new device - Called when "Create" is pressed from the "Add device" modal
 */
function createDevice(){
  // Disable helper inputs which shouldn't be sent to the API
  document.getElementById('intersight_region_eu').disabled = true;
  document.getElementById('intersight_region_us').disabled = true;
  document.getElementById('deployment_type_saas').disabled = true;
  document.getElementById('deployment_type_virtual').disabled = true;
  // Collects the content of the form and transforms it into an object
  form_content = $('#createDeviceForm').serializeArray();
  form_json = objectifyForm(form_content);

  if(form_json.bypass_connection_checks) {
    // Set bypass_connection_checks to true if the checkbox is checked, false otherwise
    form_json.bypass_connection_checks = form_json.bypass_connection_checks == "on";
  } 
  if (form_json.use_proxy) {
    // Set use_proxy to true if the checkbox is checked, false otherwise
    form_json.use_proxy = form_json.use_proxy == "on";
  }
  if (device_view == "table"){
    let phantomRow = createRowForDevice(form_json, phantom=true);
    deviceTable.row.add($(phantomRow)).draw();
  } else if (device_view == "grid"){
    // Creates a phantom card to display the device before it is added to the db
    let phantomCard = document.createElement("div");
    const target_container = document.getElementById(device_view_container_id);
    target_container.insertBefore(phantomCard, target_container.firstChild);
    phantomCard.outerHTML = createDeviceCard(form_json, phantom=true);
  }
  // Pushed the new device to the db
  pushToDb(getDevices, "device", null, form_json);
  // Closes the modal
  $('#newDeviceModal').modal('toggle');
  // Resets the form
  document.getElementById("createDeviceForm").reset();
  // Hide the device details form
  document.getElementById('target-input-container').classList.add("d-none");
  document.getElementById('ucs-device-form').classList.add("d-none");
  document.getElementById('intersight-device-form').classList.add("d-none");
  document.getElementById('intersight-type-choice').classList.add("d-none");
  document.getElementById('intersight-region-choice').classList.add("d-none");
  document.getElementById('bypass-connection-check-form').classList.add("d-none");
}

/**
 * Deletes a device
 * @param  {Event} event - The event generated by the click
 * @param  {String} device_uuid - The ID of the device to delete
 */
function deleteDevice(event, device_uuid){
  event.preventDefault();
  removeEventPropagation(event);

  // The function gets executed only if the user confirms the warning
  Swal.fire({  
    title: "Do you really want to delete this device?",
    text: getObjectName("device", device_uuid),  
    showDenyButton: true, 
    confirmButtonText: `Yes`,  
    denyButtonText: `No`,
  }).then((result) => {  
      if (result.isConfirmed) {
        // Deletes the device from the db and refreshes the device list in the UI
        deleteFromDb(getDevices, "device", device_uuid);
      }
  });
}

/**
 * Deletes a list of selected devices - devices are selected through the checkboxes
 */
function deleteMultipleDevices(){

  if(selected_objects["device"].length > bulk_actions_limit){
    raiseBulkActionLimitAlert(selected_objects["device"].length);
    return
  }

  var object_name_list = [];
  var object_uuid_list = [];

  for(obj of selected_objects["device"]){
    object_name_list.push(" " + obj["device_name"]);
    object_uuid_list.push(obj["device_uuid"]);
  }

  // The function gets executed only if the user confirms the warning
  Swal.fire({  
    title: "Do you really want to delete the following device objects?",
    text: object_name_list,  
    showDenyButton: true, 
    confirmButtonText: `Yes`,  
    denyButtonText: `No`,
  }).then((result) => {  
      if (result.isConfirmed) {
        // Deletes the selected objects and refreshes the objects
        deleteMultipleFromDb(getDevices, 'device', null, object_uuid_list);
      }
  });
}


/**
 * Resets the Device Connector of a list of selected devices - devices are selected through the checkboxes
 */
function ResetDeviceConnectorMultipleDevices(){

  if(selected_objects["device"].length > bulk_actions_limit){
    raiseBulkActionLimitAlert(selected_objects["device"].length);
    return
  }

  var object_name_list = [];
  var object_uuid_list = [];

  for(obj of selected_objects["device"]){
    object_name_list.push(" " + obj["device_name"]);
    object_uuid_list.push(obj["device_uuid"]);
  }

  var form_json = {};

  // The function gets executed only if the user confirms the warning
  Swal.fire({
    title: "Do you really want to reset the Device Connector of the following device objects?",
    text: object_name_list,
    showDenyButton: true,
    confirmButtonText: `Yes`,
    denyButtonText: `No`,
  }).then((result) => {
    if (result.isConfirmed) {
      form_json["device_uuids"] = object_uuid_list

      const target_api_endpoint = api_base_url + api_device_endpoint + "/actions/reset_device_connector";
      const action_type_message = "Resetting the Device Connector of device(s)";
      httpRequestAsync("POST", target_api_endpoint, alertActionStarted.bind(null,action_type_message), form_json);
    }
  });
}


/**
 * Displays a device
 * @param  {JSON} data - Optional: The data returned after getting a list of devices from the API
 * @param  {Array} devices - Optional: A list of devices
 */
function displayDevices(data, devices){
  /* 
    NOTE: this function can either be used after getting the devices from the API
    or with the already-loaded list of devices in the UI
  */

  // delete all phantom device cards and rows
  $(".phantomDevice").remove();
  if (deviceTable != undefined) {
    deviceTable.row($('.phantomRow')).remove().draw();
  }

  if(!data && !devices){
    console.error('No data to display!')
    return
  }

  // If the function is used as a callback after getting the devices
  if(data){
    data = JSON.parse(data);
    if(!data.devices){
      console.error('No data to display!')
      return
    }

    // We remove all devices that are flagged as "hidden"
    data.devices = data.devices.filter(device => !device.is_hidden);

    // We refresh the devices displayed only if there were changes in the data
    if(_.isEqual(loaded_device_list, data.devices)){
      return
    }
    loaded_device_list = data.devices;
  }

  // If the function is used with the already-loaded list of devices
  if(devices){
    loaded_device_list = devices;
  }

  document.getElementById(device_view_container_id).innerHTML = "";

  if(device_view == "grid"){
    // We only display the first max_grid_elements_displayed elements to avoid overloading the front-end
    total_grid_elements_displayed = Math.min(max_grid_elements_displayed - 1, loaded_device_list.length);
    addDevicesGridView(device_view_container_id, loaded_device_list, 0, total_grid_elements_displayed);
    // Scrolls to the top of the view
    window.scrollTo(0, 0);
  } else if (device_view == "table"){
    addDevicesTableView(device_view_container_id, loaded_device_list);
  }
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
 * Gets a list of devices from the db
 */
function getDevices(){

  // Only selects non-system devices
  filter = ["is_system", "==", "false"]

  // Gets the devices and displays them in the UI
  getFromDb(displayDevices, "device", device_uuid=null, uuid=null, filter=filter);
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
 * Gets executed when the input of the search bar has changed
 */
function onSearchChanged(){
  filter_string = document.getElementById("deviceSearch").value;
  displayDevices(null, loaded_device_list);
}

/**
 * Refreshes dynamic data on the page
 */
function refreshData(){
  removeScrollLoader();
  getDevices();
}

/**
 * Removes a Scroll Loader element
 */
function removeScrollLoader(){
  const scroll_loader_element = document.getElementById("loaderContainer");
  if(scroll_loader_element){
    scroll_loader_element.remove();
  }
}

/**
 * Toggles the modal with the form to perform a claim to intersight
 * @param  {Event} event - The click event
 */
function toggleClaimToIntersightMultipleDevicesModal(event){
  removeEventPropagation(event);
  getIntersightDevices();
  $('#claimToIntersightMultipleDevicesModal').modal('toggle');
}

/**
 * Hides/Shows the device actions button based on the number of devices selected
 * @param  {Array} selected_objects- The dictionary of selected objects
 */
function toggleObjectActionsButton(selected_objects){
  if(selected_objects["device"].length > 0){
    $('#deviceTableButtonContainer').removeClass('d-none');
  } else {
    $('#deviceTableButtonContainer').addClass('d-none');
    return;
  }

  var allowed_actions = [];

  // We initialize the list of available actions with every action possible
  for([device_type, device_props] of Object.entries(device_types)){
    allowed_actions = [...new Set([...allowed_actions, ...device_props["available_actions"]])];
  }
  
  for(device of selected_objects["device"]){
    var device_actions = device_types[device["device_type"]]["available_actions"]
    allowed_actions = allowed_actions.filter(value => device_actions.includes(value));
  }

  if(allowed_actions.includes("claim_to_intersight")){
    $("#claimToIntersightAction").removeClass('d-none');
  } else {
    $("#claimToIntersightAction").addClass('d-none');
  }

  if(allowed_actions.includes("reset_device_connector")){
    $("#ResetDeviceConnectorAction").removeClass('d-none');
  } else {
    $("#ResetDeviceConnectorAction").addClass('d-none');
  }
}

/**
 * Changes the display of view buttons
 * @param  {String} view_type - The type of view {grid/table}
 */
function toggleDeviceView(view_type){
  if(view_type in ["grid", "table"]){
    console.error("Impossible to display view: wrong view type");
    return
  }

  if(view_type == "grid"){
    $(btnToggleGridView).addClass('active');
    $(btnToggleTableView).removeClass('active');
    $("#deviceSearchContainer").removeClass("d-none");
  }

  if(view_type == "table"){
    $(btnToggleTableView).addClass('active');
    $(btnToggleGridView).removeClass('active');
    $("#deviceSearchContainer").addClass("d-none");
  }

  if(view_type != device_view){
    addScrollLoader(device_view_container_id, full = true);
    setTimeout(function (){
      // Re-displays the devices according to the selected view
      displayDevices(null, loaded_device_list);
    }, 200);
    // Stores the current view
    device_view = view_type;
  }
}

/**
 * Toggles the modal to edit a device
 * @param  {Event} event - The event generated by the click
 * @param  {String} device_uuid - The ID of the device to edit
 */
function toggleEditDeviceModal(event, device_uuid){
  event.preventDefault();
  removeEventPropagation(event);

  // Stores the device identified by the ID
  var device = loaded_device_list.find(device => {
    return device.device_uuid === device_uuid
  })

  document.getElementById('edit_device_label').innerText = "Editing device: " + device.device_name;
  document.getElementById('edit_target').value = device.target;
  document.getElementById('edit_user_label').value = device.user_label;

  // Displays the form elements according to the device type
  if(device.device_type == "intersight"){
    document.getElementById('intersight-device-edit-form').classList.remove('d-none');
    document.getElementById('ucs-device-edit-form').classList.add('d-none');
    document.getElementById('edit-bypass-version-checks-form').classList.remove('d-none');
    document.getElementById('edit_key_id').value = device.key_id;
    document.getElementById('edit_key_id').disabled = false;
    document.getElementById('edit_private_key').disabled = false;
    document.getElementById('edit_username').disabled = true;
    document.getElementById('edit_password').disabled = true;
    document.getElementById('edit_bypass_version_checks').disabled = false;
    if(device.bypass_version_checks){
        document.getElementById('edit_bypass_version_checks').checked = true;
    }
  } else {
    document.getElementById('intersight-device-edit-form').classList.add('d-none');
    document.getElementById('ucs-device-edit-form').classList.remove('d-none');
    document.getElementById('edit-bypass-version-checks-form').classList.remove('d-none');
    document.getElementById('edit_username').value = device.username;
    document.getElementById('edit_key_id').disabled = true;
    document.getElementById('edit_private_key').disabled = true;
    document.getElementById('edit_username').disabled = false;
    document.getElementById('edit_password').disabled = false;
    document.getElementById('edit_bypass_version_checks').disabled = false;
    if(device.bypass_version_checks){
        document.getElementById('edit_bypass_version_checks').checked = true;
    }
  }

  document.getElementById('editDeviceSubmitButton').setAttribute('onclick',`updateDevice('${device_uuid}')`);
  $('#editDeviceModal').modal('toggle');
}

/**
 * Toggles the modal to create a new device
 */
function toggleNewDeviceModal(){
  $('#newDeviceModal').modal('toggle');
  // Show all the form elements
  document.getElementById('intersight_region_eu').disabled = false;
  document.getElementById('intersight_region_us').disabled = false;
  document.getElementById('deployment_type_saas').disabled = false;
  document.getElementById('deployment_type_virtual').disabled = false;
}

/**
 * Updates a device
 * @param  {String} device_uuid - The ID of the device to update
 */
function updateDevice(device_uuid){
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

  updateToDb(getDevices, "device", device_uuid, null, form_json);

  // Closes the modal
  $('#editDeviceModal').modal('toggle');
}