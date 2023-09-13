/*
NOTE: This page is in construction, it will contain the configuration catalog with
pre-registered UCS configurations.

configs.js is the javascript used to animate the page configs.html

All functions present here are solely used on the configs.html page
*/

// Global variables
var device_type = null;
var system_catalog_device = null;
var catalog_configs = [];
var sorted_configs = {};
var selected_device_type = null;
var selected_categories = {
  "best-practices": [],
  "cvd": [],
  "samples": [],
  "custom": []
};
var dataTables = {}

// Gets executed when DOM has loaded
function afterDOMloaded(){
    // Forces page reload when using browser back button
    if(typeof window.performance != "undefined" && window.performance.navigation.type == 2){
        window.location.reload(true);
    }

    url = window.location.href;

    // Getting device type from URL
    device_type = url.substring(url.lastIndexOf('/') + 1); 

    // If the device type doesn't exist, we redirect to 404
    if(!(device_type in device_types)){
        window.location.replace("/404");
    }

    best_practicesTable = createDataTable("#best-practicesTable", 1);
    customTable = createDataTable("#customTable", 4, 4);
    cvdTable = createDataTable("#cvdTable", 1);
    samplesTable = createDataTable("#samplesTable", 1);

    // Shows "Configurations" menu element as selected + opens the dropdown menu
    document.getElementById("navLinkConfigCatalog").className += " active";
    document.getElementById("navItemConfigCatalog").className += " menu-is-opening menu-open";
    document.getElementById(device_type + "NavItem").className += " active";

    // We get all the devices when page is first loaded
    refreshData(); 
}


/**
 * Adds rows to DataTable element
 * @param  {String} category_type - The type of category
 * @param  {Object} config_list - The configurations in the category type
 */
function addConfigTableToContainer(category_type, config_list){
    var is_custom = false;
    var table = null;

    if(category_type.toLowerCase() == "custom"){
        is_custom = true;
    }

    table = getCategoryTable(category_type);

    // Clean table before new entries
    table.clear().draw();

    // Creates a row for each object loaded
    config_list.map( config => {
        var config_name = setObjectName(config, "config");
        var date_column_elem = '';
        var on_click = `window.location='/devices/${config.device_uuid}/config/${config.uuid}';`;

        if(is_custom){
            var date_timestamp = new Date(config.timestamp);
            date_timestamp = Date.parse(date_timestamp)/1000;
            date_column_elem = `
            <td data-order="${date_timestamp}" onclick="removeEventPropagation(event); window.location='/devices/${config.device_uuid}/config/${config.uuid}';">${config.timestamp}</td>
            `;
        }

        var url_columns_elem = 'No link associated';

        if(config.url && (config.url != undefined)){
            var config_url = `href="${config.url}"`;
            url_columns_elem = `<a ${config_url} target="_blank">More information</a>`;
        }

        var config_data = JSON.stringify({
            "config_name": config_name,
            "config_uuid": config.uuid,
            "config_type": category_type
        })

        table.row.add($(`
        <tr style="cursor: pointer;">
            <td>${config_data}</td>
            <td onclick="${on_click}">${config_name}</td>
            <td onclick="${on_click}">${config.subcategory}</td>
            <td onclick="${on_click}">${config.revision}</td>
            ${date_column_elem}
            <td>
            ${url_columns_elem}
            </td>
        </tr>`)).draw();
    });
}

/**
 * Deletes a list of selected objects
 * @param  {String} object_type - The type of object selected {backup/config/inventory/report}
 */
function deleteMultipleConfigs(category_type){
    var categ_name_list = [];
    var categ_uuid_list = [];
  
    if(selected_categories[category_type].length > bulk_actions_limit){
      raiseBulkActionLimitAlert(selected_categories[category_type].length);
      return
    }
  
    for(categ of selected_categories[category_type]){
        categ_name_list.push(" " + categ["config_name"]);
        categ_uuid_list.push(categ["config_uuid"]);
    }
    // The function gets executed only if the user confirms the warning
    Swal.fire({  
      title: "Do you really want to delete the following " + category_type + "  configurations?",
      text: categ_name_list,  
      showDenyButton: true, 
      confirmButtonText: `Yes`,  
      denyButtonText: `No`,
    }).then((result) => {  
        if (result.isConfirmed) {
          // Deletes the selected objects and refreshes the objects
          deleteMultipleFromDb(getCatalogConfigsFromDevice.bind(null, category_type), "config", system_catalog_device.device_uuid, categ_uuid_list);
        }
    });
}

/**
 * Displays a device
 * @param  {JSON} data - The data returned after getting a list of devices from the API
 * @param  {String} selected_tab - Optional: The tab already selected by the user
 */
function displayCatalogConfigs(selected_tab, data){
    if(!data){
        console.error('No data to display!');
        return
    }

    data = JSON.parse(data);

    if(!data.configs){
        console.error('No data to display!');
        return
    }

    // If the list is unchanged, no need to reload it
    if(_.isEqual(catalog_configs, data.devices)){
        return
    }

    catalog_configs = data.configs;

    // Creates a dictionary associating each config with its category
    sorted_configs = {};

    catalog_configs.map(config => {
        if(!sorted_configs[config.category]){
            sorted_configs[config.category] = [config];
        } else{
            sorted_configs[config.category].push(config);
        }
    });

    // Sorts the dictionary's keys by alphabetical order
    sorted_configs = sortObjectByKeys(sorted_configs);

    if(!sorted_configs["custom"]){
        sorted_configs["custom"] = [];
    }


    var is_first_elem = true;

    if(selected_tab){
        is_first_elem = false;
        $(`#nav-${selected_tab}`).addClass("show active");
        $(`#nav-${selected_tab}-tab`).addClass("active");
        $(`#nav-${selected_tab}-tab`).prop('aria-selected', true);
    }

    // For each config category, we create a specific nav tab and table
    for (config_category of Object.keys(sorted_configs)) {

        // We only display table tabs for categories that have configs (except for custom)
        $(`#nav-${config_category}`).removeClass("d-none");
        $(`#nav-${config_category}-tab`).removeClass("d-none");


        if(is_first_elem){
            // If this is the first element, we put the table tab active in the view
            $(`#nav-${config_category}`).addClass("show active");
            $(`#nav-${config_category}-tab`).addClass("active");
            $(`#nav-${config_category}-tab`).prop('aria-selected', true);
            is_first_elem = false;
        }

        addConfigTableToContainer(config_category, sorted_configs[config_category]);
    }
}

/**
 * Displays a device
 * @param  {JSON} data - The data returned after getting a list of devices from the API
 */
function displayTypedDevices(data){
    if(!data){
      console.error('No data to display!')
      return
    }
  
    data = JSON.parse(data);
    if(!data.devices){
    console.error('No data to display!')
    return
    }

    typed_devices = data.devices.filter(device => {
        return device.is_system == false;
    });

    var device_target_options_list = "";

    if(typed_devices.length < 1){
        device_target_options_list = `
      <option value="null">No devices of type ${device_type} available</option>
      `
    } else {
        typed_devices.forEach(function (device) {
        device_target_options_list += `
          <option value="${device.device_uuid}">${device.device_name}</option>
        `
      });
    }
  
    document.getElementById('push_config_device_target').innerHTML = device_target_options_list;
}

/**
 * Displays system devices
 * @param  {JSON} data - The data returned after getting a list of system devices from the API
 */
function displaySystemCatalogDevice(data){
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
        return device.device_type == device_type;
    });

    if(!system_catalog_device){
        console.error('No device of the type ' + device_type+ ' to display!')
        return
    }


    // Changes the style of the card based on the type of device
    if(device_type == "intersight"){
    avatar_src = "/static/img/intersight_logo.png";
    color = "bg-info";
    } else if (device_type == "ucsm"){
    avatar_src = "/static/img/ucsm_logo.png";
    color = "bg-primary";
    } else if (device_type == "cimc"){
    avatar_src = "/static/img/cimc_logo.png";
    color = "bg-warning";
    } else if (device_type == "ucsc"){
    avatar_src = "/static/img/ucsc_logo.png";
    color = "bg-dark";
    }

     // Creates the card and populates the container with it
    document.getElementById('deviceTypeDisplayContainer').innerHTML = 
    `
    <div>
        <div class="card card-widget widget-user-2 mb-0">
            <div class="${color} widget-user-header rounded">
                    <div>
                        <div class="widget-user-image">
                        <img class="img-circle elevation-2" src=${avatar_src} alt="Device Type">
                        </div>
                        <h3 class="widget-user-username">
                        Config Catalog
                        </h3>
                        <h5 class="widget-user-desc">
                        ${system_catalog_device.device_type_long}
                        </h5>
                    </div>
            </div>
        </div>
    </div>
    `;

    getCatalogConfigsFromDevice();
}

/**
 * Downloads a list of objects
 * @param  {String} object_type - The type of object selected {backup/config/inventory/report}
 */
async function downloadConfigs(category_type){
    if(!category_type in ["best-practices", "custom", "cvd", "samples"]){
        console.error("Impossible to download configs, wrong category type: ", category_type);
        return
    }
  
    if(selected_categories[category_type].length > bulk_actions_limit){
      raiseBulkActionLimitAlert(selected_categories[category_type].length);
      return
    }
  
    for(config of selected_categories[category_type]){
        download("config", system_catalog_device.device_uuid, config["config_uuid"]);
  
        // We wait 1sec before launching the download of the next object
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
}

/**
 * Gets a list of catalog configs for a device
 * @param  {String} selected_tab - Optional: The tab selected by the user
 */
function getCatalogConfigsFromDevice(selected_tab){
    getFromDb(callback=displayCatalogConfigs.bind(null, selected_tab), object_type="config", device_uuid=system_catalog_device.device_uuid, uuid=null);
}

/**
 * Gets the table corresponding to the specified category type
 * @param  {String} category_type - The type of category
 */
function getCategoryTable(category_type){
    if(!category_type in ["best-practices", "custom", "cvd", "samples"]){
        console.error("Impossible to get category table: wrong category type: ", category_type);
        return
      }
  
      if(category_type == "best-practices"){
          table = best_practicesTable;
      } else if(category_type == "custom"){
          table = customTable;
      } else if (category_type == "cvd"){
          table = cvdTable;
      } else if (category_type == "samples"){
          table = samplesTable;
      } else {
          console.error("Impossible to handle select all: incorrect category type");
          return;
      }

      return table;
}

/**
 * Gets a list of devices corresponding to the type of device selected 
 */
function getTypedDevices(){

    // Only selects non-system devices
    filter = ["device_type", "==", device_type]
  
    // Gets the devices and displays them in the UI
    getFromDb(displayTypedDevices, "device", device_uuid=null, uuid=null, filter=filter);
  }

/**
 * Gets a list of devices from the db
 */
function getSystemCatalogDevices(){
    filter = ["system_usage", "==", "catalog"];

    // Gets the devices and displays them in the UI
    getFromDb(callback=displaySystemCatalogDevice, object_type="device", device_uuid=null, uuid=null, filter=filter);
}

/**
 * Checks all checkboxes in array when Select All is clicked
 * @param  {String} object_type - The type of object {backup/config/device/inventory/report}
 * @param  {Element} cb - The checkbox DOM element
 */
function handleSelectAll(category_type, cb){
    if(!category_type in ["best-practices", "custom", "cvd", "samples"]){
      console.error("Impossible to handle Select All: wrong category type: ", category_type);
      return;
    }

    table = getCategoryTable(category_type);
    
    // Get all rows with search applied
    var rows = table.rows({'search': 'applied' }).nodes();
  
    // Check/uncheck checkboxes for all rows in the table
    $('input[type="checkbox"]', rows).prop('checked', cb.checked);
  
    // Changes the style of the row in UI if checkbox checked
    if(cb.checked){
      $('input[type="checkbox"]', rows).closest('tr').addClass('selected');
    } else {
      $('input[type="checkbox"]', rows).closest('tr').removeClass('selected');
    }
}

/**
 * Imports a configuration to the device
 * @param  {Event} event - The event associated to the file import
 * @param  {Boolean} import_for_push - Set to true if the config is imported to be pushed on the device, false otherwise
 * @param  {FileList} files - The imported config file
 */
function importConfig(event){
    if(!event){
        console.error('Error while collecting the file(s)');
        return
    }

    var file_list = event.target.files;

    for(file of file_list){
        $.getJSON(file.name, function(json) {
            console.log(json); // this will show the info it in firebug console
        });
    }

    pushToDb(getCatalogConfigsFromDevice.bind(null, "custom"), "config", system_catalog_device.device_uuid, null, file_list);
}


/**
 * Opens the hidden DOM element to allow file import for a specific file type
 * @param  {String} file_type - The type of file to import {config/inventory}
 */
function openImportFileDialog(){
    document.getElementById('importConfigDialog').click();
}

/**
 * Stores selected objects - Executed each time the checkboxes checked in the respective object tables changes
 * @param  {String} object_type - The type of object {backup/config/device/inventory/report}
 */
function onSelectedCategoryChanged(category_type){
    if(!category_type in ["best-practices", "custom", "cvd", "samples"]){
        console.error("Impossible to handle change in selected category, wrong category type: ", category_type);
        return
    }
  
    table = getCategoryTable(category_type);
  
    var rows = table.rows().nodes();
    var chkbox_checked = $('input[type="checkbox"]:checked', rows);
  
    // Records selected objects for each type
    selected_categories[category_type] = [];
    
    // Iterate over all checkboxes checked in the table
    chkbox_checked.each(function(){
        const cb_value = JSON.parse(this.value);
        selected_categories[category_type].push(cb_value);
    });

  
    // Shows/Hides action button for the corresponding object
    toggleObjectActionsButton();
}

/**
 * Pushes a configuration to the device
 * @param  {JSON} data - Optional: The data returned after a config is imported (not used if the config pushed already exists)
 */
async function pushConfig(){

    var form_content = $('#pushConfigForm').serializeArray();
    var form_json = objectifyForm(form_content);
    
    if(!form_json.config_uuid){
        console.error("Error pushing config: no config specified");
        return
    }

    if(!form_json.device_uuid){
        console.error("Error pushing config: no device specified");
        return
    }

    // We collect the config UUID the user has selected
    new_config_uuid = form_json.config_uuid;
    push_device_uuid = form_json.device_uuid;
  
    if(new_config_uuid == ""){
        console.error("Error pushing config: empty config uuid");
        return
    }

    if(push_device_uuid == ""){
        console.error("Error pushing config: empty device uuid");
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
      if(device_type == "ucsm"){
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
      } else if (device_type == "cimc"){
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
    
    target_api_endpoint = api_base_url + api_device_endpoint + "/" + push_device_uuid +"/configs/" + new_config_uuid + "/actions/push";
    httpRequestAsync("POST", target_api_endpoint, alertObjectPushed.bind(null, "config"), params);
    $('#pushConfigModal').modal('toggle');
  }

/**
 * Refreshes dynamic data on the page
 */
function refreshData(){
    getSystemCatalogDevices(); 
}

/**
 * Shows DHCP IP fields when "setup" checkbox is checked for pushing a config
 */
function showFabricFields(){
    if(document.getElementById('setup').checked && device_type == "ucsm"){
      $('#collapsedFabricFields_ucsm').collapse('show');
      $('#collapsedFabricFields_cimc').collapse('hide');
    } else if (document.getElementById('setup').checked && device_type == "cimc") {
      $('#collapsedFabricFields_ucsm').collapse('hide');
      $('#collapsedFabricFields_cimc').collapse('show');
    } else {
      $('#collapsedFabricFields_ucsm').collapse('hide');
      $('#collapsedFabricFields_cimc').collapse('hide');
    }
  }

/**
 * Hides/Shows the device actions button based on the number of devices selected
 * @param  {Array} selected_objects- The dictionary of selected objects
 */
function toggleObjectActionsButton(){
    for(category_type of ['best-practices', 'custom', 'cvd', 'samples']){
        if(selected_categories[category_type].length > 0){
          $(`#${category_type}TableButtonContainer`).removeClass('d-none');
          
          if(selected_categories[category_type].length > 1){
            $(`#${category_type}PushTableButton`).addClass('disabled');
            } else {
                $(`#${category_type}PushTableButton`).removeClass('disabled');
            }

        } else {
          $(`#${category_type}TableButtonContainer`).addClass('d-none');
        }

    }
}

/**
 * Toggles the modal with the form to push a config
 * @param  {Event} event - The click event
 * @param  {Boolean} populate - If set to true, pre-populates some of the form fields
 */
function togglePushConfigModal(event, category_type){
    getTypedDevices();

    removeEventPropagation(event);
  
    // We pre-populate the selection drop-down with the selected config (the first in the array given that we only allow for one selected config)  
    var config_options_list = `
      <option value="${selected_categories[category_type][0]["config_uuid"]}">${selected_categories[category_type][0]["config_name"]}</option>
      `

    document.getElementById('push_configs_catalog').innerHTML = config_options_list;
    document.getElementById("push_configs_catalog").value= selected_categories[category_type][0]["config_uuid"];



    $('#pushConfigModal').modal('toggle');
}

