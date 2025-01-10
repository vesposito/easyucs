/*
base.js is the javascript used to animate the page base.html

base.html is used as the base for all other html pages in EasyUCS.

base.js is therefore compiling all functions common to these different pages.
Some of these functions are called directly within the js files specific to these pages.
*/

// Global variables

// Major API Endpoints
var api_base_url = 'http://127.0.0.1:5001/api/v1';
var api_device_endpoint = '/devices';
var api_task_endpoint = '/tasks';
var api_config_endpoint = '/configs';
var api_inventory_endpoint = '/inventories';
var api_report_endpoint = '/reports';
var api_backup_endpoint = '/backups';
var api_notification_endpoint = '/notifications';
var api_log_endpoint = '/logs/session';
var api_orgs_endpoint = '/cache/orgs';
var repo_download_endpoint = 'http://127.0.0.1:5001/repo';
var api_repo_files_endpoint = '/repo/files';
var api_repo_upload_endpoint = '/repo/actions/upload';
var api_repo_url_download_endpoint = '/repo/actions/url/download';
var api_repo_checksum_endpoint = '/repo/actions/checksum';

var bulk_actions_limit = 500;
var tasks_displayed_limit = 200;

var device_types = null;
var selected_objects = {
    "device": [],
    "backup": [],
    "config": [],
    "inventory": [],
    "report": []
  };

// Task related
var displayed_tasks = [];
var notifications = 0;
var deviceTasksTable = null;

var devices_tasks_counts = {};
function getDeviceTasksCount(device_uuid) {
    if (!(device_uuid in devices_tasks_counts)){
        devices_tasks_counts[device_uuid] = 0;
    }
    return devices_tasks_counts[device_uuid];
}

function resetAllDeviceTasksCounts() {
    devices_tasks_counts = {};
    $(".device-tasks-counter-badge").text("0");
    $(".device-tasks-counter").hide();
}

function incrementDeviceTasksCount(device_uuid) {
    let new_value = getDeviceTasksCount(device_uuid) + 1;
    devices_tasks_counts[device_uuid] = new_value;
    let counter = $(".device-tasks-counter." + device_uuid);
    let badge = counter.find(".device-tasks-counter-badge");
    badge.text(new_value);
    counter.show();
}

// Logs related
var display_logs_bool = false;
var log_content = "";
var log_autoscrolling = true;
var log_level = "debug";


// Gets executed when DOM has loaded
$(document).ready(function() {
    $("body").tooltip({ selector: '[data-toggle=tooltip]' });

    // getFromDb(displayNotifications,"notification");
    getFromDb(processSavedSessionLogs, "log");
    getDevicesTypesInfo(function (device_types){
        saveDevicesTypesInfo(device_types);
        afterDOMloaded(); // Defined in local JS for each page
        getTasksFromDb();
    });
});

// Gets executed every X [in milliseconds]: here we are collecting tasks
window.setInterval(function() {
    getTasksFromDb();
}, 5000); // repeat every X [in milliseconds]


/**
 * Adds new logs to the existing log content, and saves them to the API
 * @param  {JSON} data - The data returned when getting the element's last logs from the API
 */
function addLogs(data) {
    if(!data){
      return;
    }
  
    data = JSON.parse(data);
    var logs = data["logs"]
    
    // If the logs content is empty, we do not need to add them
    if(logs != null){
        log_content += logs
        target_api_endpoint = api_base_url + api_log_endpoint;

        payload = {
            logs: log_content
        }

        // Sends an API call to update the log content
        httpRequestAsync("POST", target_api_endpoint, sampleCallback, payload);
    
        displayLogsToText();
    }    
}

/**
 * Adds 1 to the task notification counter, stores its value in the API, and updates the notification badge
 * @param  {JSON} data - The data returned when getting the element's logs from the API
 */
function addTaskNotification(){
    notifications += 1
    target_api_endpoint = api_base_url + api_notification_endpoint;
    payload = {
        notifications: notifications,
    }

    // Sends a call to the API to update the notification counter
    httpRequestAsync("POST", target_api_endpoint, sampleCallback, payload);

    // Updates the notification badge with the notification counter
    document.getElementById("new-task-badge").textContent = notifications;

    // Updates the tasks display
    getFromDb(displayTasks, "task");
}

/**
 * Creates an alert when an action is started
 * @param  {String} action_type_message - The message corresponding to the action
 */
function alertActionStarted(action_type_message){
  displayAlert("Action started", action_type_message, "success");
  getTasksFromDb();
//   addTaskNotification();
}

/**
 * Creates an alert when an object is fetched
 * @param  {String} object_type - The type of object
 */
function alertObjectFetched(object_type){
  displayAlert("Fetching task started", "Fetching "+ object_type, "success");
//   addTaskNotification();
  getTasksFromDb();
}

/**
 * Creates an alert when an object is pushed
 * @param  {String} object_type - The type of object
 */
function alertObjectPushed(object_type){
  displayAlert("Pushing task started", "Pushing " + object_type + " file to device", "success");
  getTasksFromDb();
//   addTaskNotification();
}


/**
 * Checks if a substring is contained in an array of strings: returns True if yes, False otherwise
 * @param  {Array} array - An array of strings 
 * @param  {String} substring - The substring to check
 */
function arrayContainsSubstring(array, substring){
    const matches = array.filter(element => {
        if(element){
            if (element.toLowerCase().indexOf(substring.toLocaleLowerCase()) !== -1) {
                return true;
            }
        }
    });
    if (matches.length > 0) {
        return true;
    } else {
        return false;
    }
}

/**
 * Cancels a task from the UI
 * @param  {String} task_uuid - The uuid of the task to cancel
 * @param  {String} task_name - The name of the task to cancel
 */
function cancelTask(task_uuid, task_name){
    event.preventDefault();
    removeEventPropagation(event);
    target_api_endpoint = api_base_url + api_task_endpoint + "/" + task_uuid + "/actions/cancel";

    // Sends a call to the API to cancel the task, and refreshes the tasks display by fetching the db
    httpRequestAsync("POST", target_api_endpoint, getFromDb.bind(null, displayTasks, "task"));

    // Displays the alert showing that the task was canceled
    displayAlert("Task Canceled", task_name, "warning")
}

/**
 * Capitalizes the first letter of a string
 * @param  {String} string - The string with the first letter to capitalize
 */
function capitalizeFirstLetter(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
}

/**
 * Capitalizes the first letter of each word in a string
 * @param  {String} string - The string
 */
function capitalizeWords(string) {
    string = string.replace(/[._-]/g, " ");
    return string.replace(/(^\w{1})|(\s+\w{1})/g, letter => letter.toUpperCase());
}

/**
 * Resets the task notification counter and removes the notification badge from UI
 */
function cleanTaskNotification(){
    notifications = 0;

    // Removes the content of the notification badge
    document.getElementById("new-task-badge").textContent = "";

    target_api_endpoint = api_base_url + api_notification_endpoint;

    payload = {
        notifications: notifications,
    }
    // Sends a call to API to reset the notification counter
    httpRequestAsync("POST", target_api_endpoint, sampleCallback, payload);
}

/**
 * Closes the log panel
 */
function closeLogOffcanvas(){
    document.getElementById("log-canvas").style.height = "0";
    document.getElementById("placeholder-log-open").style.height = "0";

    // Saves the status of the log panel to closed
    display_logs_bool = false;

    // Updates the status of the log panel in the API
    updateLogBool();
}

/**
 * Creates a DataTable element in a HTML element
 * @param  {String} tableId - The ID of the HTML element in which to create the table
 * @param  {Number} order_column - Optional: The column with which the table is initially sorted (from the left)
 * @param  {Number} date_column - Optional: A column which contains a data attribute (from the left)
 */
function createDataTable(tableId, order_column, date_column){

    $.fn.DataTable.moment();

    if ($.fn.DataTable.isDataTable(tableId)) {
        $(tableId).DataTable().clear().destroy();
    }

    if(!order_column){
        order_column = 3;
    }

    // Sorts the table by order of order_column. Use desc order if order_column is the date_column, otherwise asc order
    if ( order_column == date_column ) {
        var order_direction = "desc"
    } else {
        var order_direction = "asc"
    }

    var dataTable = $(tableId).DataTable({
        "dom":  "<'row'<'col-sm-12 text-start col-md-6'f><'col-sm-12 text-end col-md-6'l>>" +
                "<'row'<'col-sm-12'tr>>" +
                "<'row'<'col-sm-12 col-md-5'i><'col-sm-12 col-md-7'p>>",
        "responsive": true, "lengthChange": true, "autoWidth": false,
        "paging": true,
        "orderClasses": false,
        // Defines the list of buttons available at the top of the table
        "buttons": ["copy", "csv", "excel", "pdf", "print", "colvis"],
        "lengthMenu": [ 10, 25, 50, 75, 100 ],

        "order": [[ order_column, order_direction ]],
        "deferRender": true,
        "deferLoading": true,
        "columnDefs": [
        {
            // The following lines define the behavior of column 0 (first on the left)
            "targets": 0,
            'searchable': false,
            'orderable': false,

            // Renders a checkbox item in the column element
            "render": function ( data, type, row ) { 
                return `<input type="checkbox" name="object_id" value='`
                + $('<div/>').text(data).html() + `' onclick = "handleCheckboxClick('${tableId}', this);">`;
            },
            "className": "text-center"
        },
        {
            // The following lines define the behavior of column 3 (from the left)
            "targets": [date_column],

            // We use MomentJS to properly format the date
            "render": function( data, type, row ) {
                return moment(data);
            }
        }
    ],
    
    });
    
    // Adds the buttons from the list defined above to the wrapper of the table
    dataTable.buttons().container().appendTo(tableId+'_wrapper .col-md-6:eq(0)');
    
    return dataTable;
}

/**
 * Deletes an object from the database
 * @param  {Function} callback - Optional: The function to execute while the call has returned
 * @param  {String} object_type - The type of object to delete {backup/config/device/inventory/report}
 * @param  {String} device_uuid - The ID of the device to which the object belongs
 * @param  {String} uuid - Optional: The ID of the object (stays null if the object is a device)
 */
function deleteFromDb(callback = null, object_type = null, device_uuid = null, uuid = null){
    if(!object_type){
        console.error("Impossible to delete object: no object_type specified");
        return
    }

    if(!device_uuid){
        console.error("Impossible to delete object " + object_type + ": no device_uuid specified");
        return       
    }

    if(object_type!="device" && !uuid){
        console.error("Impossible to delete object " + object_type + ": no uuid specified");
        return       
    }

    var target_api_endpoint= api_base_url + api_device_endpoint + "/" + device_uuid;

    // Builds the API endpoint based on the object type
    if(object_type == "device"){
        // Nothing to do
    }else if(object_type == "config"){
        target_api_endpoint+= api_config_endpoint;
    }else if(object_type == "inventory"){
        target_api_endpoint+= api_inventory_endpoint;
    }else if(object_type == "report"){
        target_api_endpoint+= api_report_endpoint;
    }else if(object_type == "backup"){
        target_api_endpoint+= api_backup_endpoint;
    }else{
        console.error("Impossible to delete object: incorrect object_type attribute");
        return
    }

    // Adds the object UUID to the end of the API endpoint
    if(uuid){
        target_api_endpoint+= "/" + uuid;
    }

    // Sends an DELETE request to the API
    httpRequestAsync("DELETE", target_api_endpoint, callback);
}

/**
 * Deletes multiple objects from the database
 * @param  {Function} callback - Optional: The function to execute while the call has returned
 * @param  {String} object_type - The type of object to delete {backup/config/device/inventory/report}
 * @param  {String} device_uuid - The ID of the device to which the object belongs
 * @param  {Array} object_list - Optional: The list of IDs of the objects (stays null if the object is a device)
 */
function deleteMultipleFromDb(callback = null, object_type = null, device_uuid = null, object_list = []){
    if(!object_type){
        console.error("Impossible to delete object: no object_type specified");
        return
    }

    if(object_type!="device" && !device_uuid){
        console.error("Impossible to delete objects " + object_type + ": no device_uuid specified");
        return       
    }

    var target_api_endpoint = "";
    var payload = {};

    // Builds the API endpoint and the payload based on the object type
    if(object_type == "device"){
        target_api_endpoint = api_base_url + api_device_endpoint;
        payload = {
            "device_uuids": object_list
        }
    }else if(object_type == "config"){
        target_api_endpoint = api_base_url + api_device_endpoint + "/" + device_uuid + api_config_endpoint;
        payload = {
            "config_uuids": object_list
        }
    }else if(object_type == "inventory"){
        target_api_endpoint = api_base_url + api_device_endpoint + "/" + device_uuid + api_inventory_endpoint;
        payload = {
            "inventory_uuids": object_list
        }
    }else if(object_type == "report"){
        target_api_endpoint = api_base_url + api_device_endpoint + "/" + device_uuid + api_report_endpoint;
        payload = {
            "report_uuids": object_list
        }
    }else if(object_type == "backup"){
        target_api_endpoint = api_base_url + api_device_endpoint + "/" + device_uuid + api_backup_endpoint;
        payload = {
            "backup_uuids": object_list
        }
    }else{
        console.error("Impossible to delete object: incorrect object_type attribute");
        return
    }

    target_api_endpoint += "/actions/delete";

    // Sends a POST request to the API
    httpRequestAsync("POST", target_api_endpoint, callback, payload);

    // Resets the list of selected objects
    selected_objects[object_type] = [];

    // Shows/Hides action button for the corresponding object
    toggleObjectActionsButton(selected_objects);
}

/**
 * Displays an alert badge
 * @param  {String} title - Optional: The title of the alert
 * @param  {String} body - Optional: The body of the alert
 * @param  {String} type - Optional: The type of alert {error/info/warning/success}
 */
function displayAlert(title = null, body = null, type = "error"){
    if(!title && !body){
        console.error("Impossible to display alert: no title nor body provided");
        return
    }
    
    Swal.fire({
        title: title,
        text: body,
        icon: type,
        toast: true,
        position: 'bottom',
        timer: 5000
    })
}

/**
 * Displays the logs in the log panel
 */
function displayLogsToText(){

    // We only open the log panel if the status of the display is open
    if(display_logs_bool){
        openLogOffcanvas();
    }

    // If there are no logs, we do not need to process them
    if(log_content == ""){
      return;
    }
  
    var logs_splitted, logs_length;
    var displayed_logs = "";
  
    var severity = {
          "emergency" : "0",
          "alert" : "1",
          "critical" : "2",
          "error" : "3",
          "warning" : "4",
          "notice" : "5",
          "info" : "6",
          "debug" : "7"
    };
      
    logs_splitted = log_content.split("\r");
  
    // Minus 1 to remove the '\r' at the end of logs
    logs_length = logs_splitted.length - 1;
  
    // We only display the logs that are more or equally severe to the severity level chosen
    for (index = 0; index < logs_length; ++index) {
      var lvl;
      lvl = logs_splitted[index].match(/:: ([\s\S]*?) ::/);
      if (severity[lvl[1].toLowerCase()] <= severity[log_level]) {
        displayed_logs += logs_splitted[index] + "\r";
      }
    }
  
    var log_textarea = document.getElementById("log-content");

    // Inputs the logs into the text area of the log panel
    log_textarea.value= displayed_logs;

    // Scrolls down if auto-scrolling is enabled by the user
    if (log_autoscrolling) {
          log_textarea.scrollTop = log_textarea.scrollHeight;
    }
}

/**
 * Displays the notification badge
 * @param  {JSON} data - The data returned when getting the notification counter from the API
 */
function displayNotifications(data){
    if(!data){
        console.error('No data to display!');
        return
    }
    data = JSON.parse(data);
    if(!data.notifications){
        return
    }

    notifications = data.notifications;

    // Updates the notification badge with the notification number
    document.getElementById("new-task-badge").textContent = notifications;
}


function tableFromTasks(task_list, taskTable, device_column = true) {
    // For each task, we create the specific row in the DataTable
    task_list.map( task => {
        var text_color = "text-dark";
        var status_title = "In progress";
        var status_message = ``;
        var on_click = `window.location='/task/${task.uuid}';`;
        var text_color = "text-dark";
        var status_title = "In progress";
        var status_message = ``;
        var on_click = `window.location='/task/${task.uuid}';`;


        if ( task.status == "pending" ) {
            var task_timestamp = "To be started";
        } else {
            var task_timestamp = moment(task.timestamp_start);
        }


        if(task.status == "in_progress"){
            status_title = "In progress";
            status_message = `
            <div class="progress">
                <div class="progress-bar bg-success" role="progressbar" style="width: ${task.progress}%" aria-valuenow="${task.progress}" aria-valuemin="0" aria-valuemax="100"></div>
            </div>
            `;
        } else {
            status_message = task.status_message;
            if (task.status == "successful"){
                text_color = "text-success";
                status_title = "Successful";
            } else if (task.status == "pending"){
                text_color = "text-info";
                status_title = "Pending";
                status_message = "Task in queue";
                on_click = "";
            } else {
                text_color = "text-danger";
                status_title = "Failed";
            }
        }
        device_column_content = device_column ? `<td><a href="/devices/${task.device_uuid}">${task.device_name}</a></td>` : "";
        taskTable.row.add($(`
        <tr style="cursor: pointer;">
            <td>${task.uuid}</td>
            <td class="${text_color}" onclick="${on_click}">${status_title}</td>
            <td onclick="${on_click}">${task.description}</td>
            <td onclick="${on_click}">${task.timestamp}</td>
            <td onclick="${on_click}">${status_message}</td>
            <td onclick="${on_click}">${task_timestamp}</td>
            ${device_column_content}
        </tr>`)).draw();
        });
        // Hides the checkbox column
        taskTable.column(0).visible(false);
}

/**
 * Displays the tasks in the UI
 * @param  {JSON} data - The data returned when getting the tasks from the API
 */
function displayTasks(data){    
    if(!data){
        console.error('No data to display!');
        return
    }

    data = JSON.parse(data);

    if(!data.tasks){
        console.error('No data to display!')
        return
    }

    var loaded_tasks = data.tasks;

    // We refresh the tasks displayed only if there were changes in the data
    if(_.isEqual(loaded_tasks, displayed_tasks)){
        return
    }

    // If there was a change in the tasks, we refresh the data to reflect the changes everywhere in the page
    if(displayed_tasks.length > 0){
        refreshData();
    }

    displayed_tasks = loaded_tasks;

    const url_path_type = location.pathname.split('/')[1];

    // If we are in the "tasks" page, we also trigger its display method
    if(url_path_type == "tasks"){
        // Defined in the tasks.js
        displayPageTasks(displayed_tasks);
    }

    var in_progress_tasks = [];
    var finished_tasks = [];
    var pending_tasks = [];
    resetAllDeviceTasksCounts();
    // Stores the tasks finished and in progress in two different arrays
    loaded_tasks.map( task => {
        if(task.status == "in_progress"){
            incrementDeviceTasksCount(task.device_uuid);
            in_progress_tasks.push(task);
        } else if (task.status == "pending"){
            incrementDeviceTasksCount(task.device_uuid);
            pending_tasks.push(task);
        } else {
            finished_tasks.push(task);
        }
    });
    // Display in progress and pending tasks count in the navbar tasks badge
    let tasksCount = in_progress_tasks.length + pending_tasks.length;
    if (tasksCount > 0){
        $("#tasks-complete-badge").hide();
        $("#task-count-badge").text(tasksCount);
    } else {
        $("#tasks-complete-badge").show();
        $("#task-count-badge").text("");
    }

    // Puts the tasks in progress first in the list of tasks
    loaded_tasks = [];
    loaded_tasks = [...in_progress_tasks, ...finished_tasks];

    var allTasksNumber = loaded_tasks.length;

    var pendingTasksNumber = pending_tasks.length;
    if(pendingTasksNumber > 0){
        $("#tasksPendingContainer").removeClass("d-none");
        $("#tasksPendingContainer").addClass("d-flex");
        $("#tasksPendingNumber").text(pendingTasksNumber);
    } else {
        $("#tasksPendingContainer").removeClass("d-flex");
        $("#tasksPendingContainer").addClass("d-none");
    }
    // Display device specific tasks if we are on the device page
    if (typeof current_device_uuid !== 'undefined') {
        let device_specific_tasks = loaded_tasks.filter(task => task.device_uuid == current_device_uuid);
        if (deviceTasksTable == null) {
            deviceTasksTable = createDataTable("#tasksTable", 3, 3);
        }
        deviceTasksTable.clear().draw();
        tableFromTasks(device_specific_tasks, deviceTasksTable, device_column = false);
    }
    // Only displays the first 10 tasks in the navbar tasks dropdown
    if(allTasksNumber > 10){
        loaded_tasks = loaded_tasks.slice(0, 10)
    }

    tasksNumber = loaded_tasks.length;

    document.getElementById("taskDropdownTitle").innerHTML = `Last Tasks (${tasksNumber})`;
    document.getElementById("taskDropdownFooter").innerHTML = `See All Tasks (${allTasksNumber})`;

    // Resets the content of the panel containing the tasks
    document.getElementById("taskCardsContainer").innerHTML = ``;

    // Creates elements based on the status of the task
    loaded_tasks.map( task => {
        var color = "callout-info";
        var progress_bar = ``;
        var time = ``;
        var status_message = ``;
        var status_title = ``;
        var cancel_task = ``;
        var task_description = truncateString(task.description, 50)

        if(task.status == "in_progress"){
            cancel_task = `
            <div class="card-link" style = "cursor: pointer;" onclick = "cancelTask('${task.uuid}', '${task_description}' );"><i class="fas fa-times pr-1"></i>Cancel</div>
            `
            status_title = "In Progress"
            progress_bar = `
            <div class="progress my-1">
                <div class="progress-bar bg-success" role="progressbar" style="width: ${task.progress}%" aria-valuenow="${task.progress}" aria-valuemin="0" aria-valuemax="100"></div>
            </div>

            `;
            time = `
            <small class="pb-1">Started: ${task.timestamp_start}</small>
            `;
        } else {
            status_message = `
            <p class="card-text">${truncateString(task.status_message, 70)}</p>
            `;
            time = `
            <small class = "py-1" >Ended: ${task.timestamp_stop}</small>
            `;

            if (task.status == "successful"){
                color = "callout-success";
                status_title = "Successful";
                status_message = ``;
            } else if (task.status == "pending"){
                color = "callout-info";
                status_title = "Pending";
                status_message = ``;
            } else {
                color = "callout-danger";
                status_title = "Failed";
            }
        }

        
        // Adds the HTML for all tasks to the panel containing the tasks
        document.getElementById("taskCardsContainer").innerHTML += `
        <div onclick="window.location='/task/${task.uuid}'" style = "cursor: pointer;" class="callout ${color} text-dark">
            <h5>${task_description}</h5>
            <p><b>${status_title}</b></p>
            ${status_message}
            ${progress_bar}
            ${time}
            <div class="d-flex flex-row">
            ${cancel_task}
            </div>
        </div>
        `
    });
}

/**
 * Downloads an object in the browser
 * @param  {String} object_type - The type of object to download {backup/config/inventory/report}
 * @param  {String} device_uuid - The ID of the device to which the object belongs
 * @param  {Array} object_list - The ID of the object
 */
function download(object_type = null, device_uuid = null, uuid = null){
    if(!object_type){
        console.error("Impossible to download object: no object_type specified");
        return
    }

    if(!device_uuid){
        console.error("Impossible to download object: no device_uuid specified");
        return
    }

    if(!uuid){
        console.error("Impossible to download object: no object uuid specified");
        return
    }

    var target_api_endpoint = api_base_url;

    // Builds the API Endpoint based on the object to download
    if(object_type == "config"){
        target_api_endpoint+= api_device_endpoint;
        if(device_uuid){
            target_api_endpoint+= "/" + device_uuid + api_config_endpoint;
        }
    }else if(object_type == "inventory"){
        target_api_endpoint+= api_device_endpoint;
        if(device_uuid){
            target_api_endpoint+= "/" + device_uuid + api_inventory_endpoint;
        }
    }else if(object_type == "report"){
        target_api_endpoint+= api_device_endpoint;
        if(device_uuid){
            target_api_endpoint+= "/" + device_uuid + api_report_endpoint;
        }
    }else if(object_type == "backup"){
        target_api_endpoint+= api_device_endpoint;
        if(device_uuid){
            target_api_endpoint+= "/" + device_uuid + api_backup_endpoint;
        }
    }else{
        console.error("Impossible to download object: incorrect object_type attribute");
        return
    }

    target_api_endpoint+= "/" + uuid + "/actions/download";

    // Downloads the object into the browser
    window.open(target_api_endpoint, '_self');
    return
}

/**
 * Fetches an object from a device
 * @param  {Function} callback - Optional: The function to execute while the call has returned
 * @param  {String} object_type - The type of object to fetch {backup/config/inventory}
 * @param  {String} device_uuid - The ID of the device to which the object belongs
 */
function fetchLiveObject(callback = null, object_type = null, device_uuid = null){
    if(!object_type){
        console.error("Impossible to fetch live object: no object_type specified");
        return
    }

    if(!device_uuid){
        console.error("No device_uuid specified to fetch live object " + object_type);
        return       
    }

    target_api_endpoint = api_base_url + api_device_endpoint + "/" + device_uuid;

    // Builds the API endpoint based on the object type
    if(object_type == "config"){
        target_api_endpoint+= api_config_endpoint;
        payload = {"force": false};
    }else if(object_type == "inventory"){
        target_api_endpoint+= api_inventory_endpoint;
        payload = {"force": false};
    }else if(object_type == "backup"){
        target_api_endpoint+= api_backup_endpoint;
        payload = {};
    }else{
        console.error("Impossible to fetch live object: incorrect object_type attribute");
        return
    }

    target_api_endpoint += "/actions/fetch";

    // Sends a POST request to the API endpoint
    httpRequestAsync("POST", target_api_endpoint, callback, payload);
}

/**
 * Gets an object from the database
 * @param  {Function} callback - Optional: The function to execute while the call has returned
 */
function getDevicesTypesInfo(callback = null){
    target_api_endpoint = api_base_url + api_device_endpoint + "/types"
    // Sends a GET request to the API
    httpRequestAsync(request_type="GET", theUrl=target_api_endpoint, callback=callback);
}

/**
 * Gets an object from the database
 * @param  {Function} callback - Optional: The function to execute while the call has returned
 * @param  {String} object_type - The type of object to get {backup/config/device/inventory/log/notification/orgs/report/task}
 * @param  {String} device_uuid - The ID of the device to which the object belongs
 * @param  {String} uuid - Optional: The ID of the object (stays null if the object is a device)
 * @param  {Array} filter - Optional: The filter to apply to the query, attribute should be one of {"==", "!=", ">", ">=", "<", "<="}
 * @param  {Array} order_by - Optional: The order with which to return the query [attribute_name, {asc/desc}]
 */
function getFromDb(callback = null, object_type = null, device_uuid = null, uuid = null, filter = null, order_by = null
    , page_number = null, page_size = null){
    if(!object_type){
        console.error("Impossible to get object: no object_type specified");
        return
    }

    if(filter){
        var allowed_filters = ["==", "!=", ">", ">=", "<", "<="];
        // Verifies that filter is an array
        if(!Array.isArray(filter)){ 
            console.error("Incorrect filter type!");
            return
        }
        if(filter.length != 3){
            console.error("Incorrect filter array length, should be 3!");
            return
        }
        // Verifies that the filter is valid
        if(!allowed_filters.includes(filter[1])){ 
            console.error("filter attribute should contain one of '==', '!=', '>', '>=', '<', '<='");
            return
        } 
    }

    if(order_by){
        var allowed_order_by= ["asc", "desc"]
        // Verifies that order_by is an array
        if(!Array.isArray(order_by)){ 
            console.error("Incorrect order_by type!");
            return
        }
        if(order_by.length != 2){
            console.error("Incorrect order_by array length, should be 2!");
            return
        }
        // Verifies that the order_by is valid
        if(!allowed_order_by.includes(order_by[1])){ 
            console.error("order_by attribute should be one of 'asc', 'desc'");
            return
        }    
    }

    if(page_number){
        if(!Number.isFinite(page_number)){
            console.error("page_number attribute is not a finite number");
            return
        }
    }

    if(page_size){
        if(!Number.isFinite(page_number)){
            console.error("page_number attribute is not a finite number");
            return
        }
    }

    var target_api_endpoint = api_base_url;
    
    // Builds the API endpoint based on the object type
    if(object_type == "device"){
        target_api_endpoint+= api_device_endpoint;
        if(device_uuid){
            target_api_endpoint+= "/" + device_uuid;
        }
    }else if(object_type == "config"){
        if(device_uuid){
            target_api_endpoint+= api_device_endpoint + "/" + device_uuid + api_config_endpoint;
        }else{
            target_api_endpoint+= api_config_endpoint;
        }
    }else if(object_type == "inventory"){
        if(device_uuid){
            target_api_endpoint+= api_device_endpoint + "/" + device_uuid + api_inventory_endpoint;
        } else {
            target_api_endpoint+= api_inventory_endpoint;
        }
    }else if(object_type == "report"){
        if(device_uuid){
            target_api_endpoint+= api_device_endpoint + "/" + device_uuid + api_report_endpoint;
        } else {
            target_api_endpoint+= api_report_endpoint;
        }
    } else if (object_type == "backup"){
        if(device_uuid){
            target_api_endpoint+= api_device_endpoint + "/" + device_uuid + api_backup_endpoint;
        } else {
            target_api_endpoint+= api_report_endpoint;
        }
    } else if(object_type == "task"){
        target_api_endpoint+= api_task_endpoint;
    } else if (object_type == "notification"){
        target_api_endpoint+= api_notification_endpoint;
    } else if (object_type == "log"){
        target_api_endpoint+= api_log_endpoint;
    } else if (object_type == "orgs"){
        if(device_uuid){
            target_api_endpoint+= api_device_endpoint + "/" + device_uuid + api_orgs_endpoint;
        } else {
            console.error("Impossible to get orgs: missing device UUID");
            return
        }
    } else {
        console.error("Impossible to get object: incorrect object_type attribute - " + object_type);
        return
    }

    // Adds the ID of the object to the endpoint
    if(uuid){
        target_api_endpoint+= "/" + uuid;
    }

    var url_params = {};
    if(filter){
        url_params["filter_attribute"] = filter[0];
        url_params["filter_type"] = filter[1];
        url_params["filter_value"] = filter[2];
    }

    if(order_by){
        url_params["order_by_attribute"] = order_by[0];
        url_params["order_by_direction"] = order_by[1];
    }

    if(page_number){
        url_params["page_number"] = page_number;
    }

    if(page_size){
        url_params["page_size"] = page_size;
    }

    // Sends a GET request to the API
    httpRequestAsync(request_type="GET", theUrl=target_api_endpoint, callback=callback, payload=null, url_params=url_params);
}

/**
 * Gets the tasks from the db with the limit set by tasks_displayed_limit
 */
function getTasksFromDb(){
    var page_size = tasks_displayed_limit;
    var page_number = 0;
    getFromDb(displayTasks, "task", null, null, null, null, page_number, page_size);
}

/**
 * Gets the JSON of an object from the file repository
 * @param  {Function} callback - Optional: The function to execute while the call has returned
 * @param  {String} object_type - The type of object to get {config/inventory}
 * @param  {String} device_uuid - The ID of the device to which the object belongs
 * @param  {String} uuid - The ID of the object
 */
function getJson(callback = null, object_type = null, device_uuid = null, uuid = null){
    if(!object_type){
        console.error("Impossible to get object JSON: no object_type specified");
        return
    }

    if(!device_uuid){
        console.error("Impossible to get object JSON: no device_uuid specified");
        return
    }

    if(!uuid){
        console.error("Impossible to get object JSON: no object uuid specified");
        return
    }

    var target_api_endpoint = api_base_url;

    // Build the API endpoint based on the object type
    if(object_type == "config"){
        target_api_endpoint+= api_device_endpoint;
        if(device_uuid){
            target_api_endpoint+= "/" + device_uuid + api_config_endpoint;
        }
    }else if(object_type == "inventory"){
        target_api_endpoint+= api_device_endpoint;
        if(device_uuid){
            target_api_endpoint+= "/" + device_uuid + api_inventory_endpoint;
        }
    }else{
        console.error("Impossible to get object JSON: incorrect object_type attribute");
        return
    }

    target_api_endpoint+= "/" + uuid + "/actions/download";

    // Sends GET request to the API
    httpRequestAsync("GET", target_api_endpoint, callback);
}

/**
 * Gets an object name based on its type and uuid
 * @param  {String} object_type - The type of object {backup/config/device/inventory/report}
 * @param  {String} object_uuid - The uuid of the object
 */
function getObjectName(object_type, object_uuid){
    if(!object_type || !object_uuid){
      console.error("Impossible to get object name: wrong parameters specified!");
      return
    }
  
    if(!object_type in ["backup", "config", "device", "inventory", "report"]){
      console.error("Impossible to get object name: object type not supported: " + object_type);
      return
    }
  
    var search_list = null;
  
    // Gets the list of the loaded object type (ex: loaded_config_list)
    var search_list = eval("loaded_" + object_type + "_list");

    var object_name = "";

    // If the object is a device, the uuid is the device_uuid
    if(object_type == "device"){
        for(object of search_list){
            if(object.device_uuid == object_uuid){
              object_name = setObjectName(object, object_type)
              break
            }
        }
    } else {
        for(object of search_list){
            if(object.uuid == object_uuid){
              object_name = setObjectName(object, object_type)
              break
            }
        }
    }
  
    return object_name;
}

/**
 * Gets the table corresponding to a certain object type
 * @param  {String} object_type - The type of object to get {backup/config/device/inventory/report}
 */
function getObjectTable(object_type){
    if(!object_type in ["backup", "config", "device", "inventory", "report"]){
      console.error("Impossible to handle change in selected objects: wrong object type: ", object_type);
      return
    }
  
    object_table = null;
  
    // Gets the corresponding table based on the object type
    if(object_type == "backup"){
      object_table = backupTable;
    } else if (object_type == "config"){
      object_table = configTable;
    } else if (object_type == "device"){
      object_table = deviceTable;
    } else if (object_type == "inventory"){
      object_table = inventoryTable;
    } else if (object_type == "report"){
      object_table = reportTable;
    }
    
    return object_table;
}

/**
 * Ticks the select All checkbox based on the checkboxes selected
 * @param  {String} tableId - The ID of the table on which to handle the checkbox click
 * @param  {Element} cb - The checkbox DOM element
 */
function handleCheckboxClick(tableId, cb){
    // If checkbox is not checked
    if(!cb.checked){
        $(cb).closest('tr').removeClass('selected');
    } else {
        $(cb).closest('tr').addClass('selected');
    }
    
    updateDataTableSelectAllCtrl(tableId);
}

/**
 * Handles the HTTP response returned by a query
 * @param  {Function} success_callback - Optional: The function to execute while the call has returned successfully
 * @param  {DOMString} received_http_response - The HTTP response returned by the query
 * @param  {Function} error_callback - Optional: The function to execute while the call has returned an error
 */
function handleHttpResponse(success_callback, received_http_response, error_callback=null){
    supported_error_status_codes = [400, 404, 500];

    if(!received_http_response){
        console.error("Impossible to handle response: no response specified");
    }
    
    // A value of 4 means that the response is complete
    if (received_http_response.readyState == 4){

        // The callback is executed only if the status is valid (200)
        if(received_http_response.status == 200){

            // Executes the callback function if specified
            if(success_callback){
                success_callback(received_http_response.responseText);
            }
        } else if (received_http_response.status == 0){
            // No need to handle response as this request was aborted
            return;
        } else {
            // If the returned code is supported by EasyUCS, we return the associated error message
            if(supported_error_status_codes.includes(received_http_response.status)){
                alert_message = JSON.parse(received_http_response.responseText)["message"];
                displayAlert(received_http_response.statusText, alert_message);
            // Otherwise, we only return the error status
            } else {
                displayAlert(received_http_response.statusText);
            }
            if (error_callback){
                error_callback(received_http_response.responseText);
            }
            // We refresh the data on the page since we got an error
            // refreshData();
            // Todo: handle the error in a more user-friendly way
        }
    }
}

/**
 * Handles the HTTP response returned by a query
 * @param  {String} request_type - The request type to be performed {GET/PUT/POST/DELETE}
 * @param  {String} theUrl - URL on which to execute the request
 * @param  {Function} success_callback - Optional: The function to execute while the call has returned successfully
 * @param  {FormData|JSON} payload - Optional: The payload to pass to the request
 * @param  {Object} url_params - Optional: A dictionary where keys are the parameter names and values are their values
 * @param  {Function} error_callback - Optional: The function to execute while the call has returned an error
 */
function httpRequestAsync(request_type = null, theUrl = null, success_callback = null, payload = null, url_params = null, error_callback = null){
    var allowed_request_types = ["GET", "PUT", "POST", "DELETE"]

    if(!request_type){
        console.error("HTTP Request Error: no request type specified!");
        return;
    }
    if(!allowed_request_types.includes(request_type)){
        console.error("HTTP Request Error: request type not supported!");
        return;
    }
    if(!theUrl){
        console.error("HTTP " + request_type + " Error: no URL specified");
        return;
    }

    if(url_params == {}){
        url_params = null;
    }

    var xmlHttp = new XMLHttpRequest();

    // Gets executed when a response to the request has been received
    xmlHttp.onreadystatechange = function() {
        handleHttpResponse(success_callback, xmlHttp, error_callback);
    }

    if(url_params && Object.keys(url_params).length > 0){
        theUrl += "?";
        for([key, value] of Object.entries(url_params)){
            theUrl += `${key}=${value}&`
        }
        // Removes the last element of the string (the last "&"")
        theUrl = theUrl.slice(0, -1)
    }

    // Creates the HTTP request
    xmlHttp.open(request_type, theUrl, true); // true for asynchronous

    // If we have a payload, we pass it to the request
    if(payload){
        // If the payload is not JSON, we convert it to JSON first
        if(!(payload instanceof FormData)){
            payload = JSON.stringify(payload);
            xmlHttp.setRequestHeader("Content-Type", "application/json");
        }
        // Sends the request with the payload
        xmlHttp.send(payload);
    } else {
        // Sends the request without payload
        xmlHttp.send(null);
    }
}

/**
 * Checks all checkboxes in array when Select All is clicked
 * @param  {String} object_type - The type of object {backup/config/device/inventory/report}
 * @param  {Element} cb - The checkbox DOM element
 */
function handleSelectAll(object_type, cb){
    if(!object_type in ["backup", "config", "device", "inventory", "report"]){
      console.error("Impossible to handle Select All: wrong object type: ", object_type);
      retur
    }
  
    object_table = getObjectTable(object_type);
    
    // Get all rows with search applied
    var rows = object_table.rows({'search': 'applied' }).nodes();
  
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
 * Returns a form array under the form of a JS object
 * @param  {Array} formArray - Form array to objectify
 */
function objectifyForm(formArray) {
    // Serialize data function
    var return_object = {};
    for (var i = 0; i < formArray.length; i++){
        return_object[formArray[i]['name']] = formArray[i]['value'];
    }
    return return_object;
}

/**
 * Stores selected objects - Executed each time the checkboxes checked in the respective object tables changes
 * @param  {String} object_type - The type of object {backup/config/device/inventory/report}
 */
function onSelectedObjectsChanged(object_type){
    if(!object_type in ["backup", "config", "inventory", "report"]){
      console.error("Impossible to handle change in selected objects: wrong object type: ", object_type);
      return
    }
  
    object_table = getObjectTable(object_type);
  
    var rows = object_table.rows().nodes();
    var chkbox_checked = $('input[type="checkbox"]:checked', rows);
  
    // Records selected objects for each type
    selected_objects[object_type] = [];
    
    // Iterate over all checkboxes checked in the table
    chkbox_checked.each(function(){
        const cb_value = JSON.parse(this.value);
        selected_objects[object_type].push(cb_value);
    });

  
    // Shows/Hides action button for the corresponding object
    toggleObjectActionsButton(selected_objects);
}

/**
 * Opens the log panel
 */
function openLogOffcanvas(){
    removeEventPropagation(event);

    // Height of the log panel
    const log_height = 200;

    document.getElementById("log-canvas").style.height = log_height + "px";
    document.getElementById("placeholder-log-open").style.height = log_height + "px";

    // Scrolls down the page to the value of the panel height 
    if(!display_logs_bool){
        window.scrollBy(0, log_height);
    }

    // We update the log display boolean to reflect its status
    display_logs_bool = true;
    updateLogBool();
}

/**
 * Processes the logs saved in the API (session logs)
 * @param  {JSON} data - The data returned when getting the logs saved in the API
 */
function processSavedSessionLogs(data){
    if(!data){
        console.error('No data to display!')
        return;
    }
    data = JSON.parse(data);

    // If there is no logs saved, nothing to do
    if(!data.logs && !data.displayLogsBool){
        return;
    }

    // Saves the status of the log panel display
    if(data.displayLogsBool){
        display_logs_bool = data.displayLogsBool;
    }

    // Adds the content of the saved session logs to the current log content
    log_content = data.logs;

    // Displays the logs in the UI
    displayLogsToText();
}

/**
 * Pushes an object to the database
 * @param  {Function} callback - Optional: The function to execute while the call has returned
 * @param  {String} object_type - The type of object to push {config/device/inventory}
 * @param  {String} device_uuid - The ID of the device to which the object belongs
 * @param  {JSON} payload - Optional: The parameters of the device to create
 * @param  {Array} file_list - Optional: List of files to push
 */
function pushToDb(callback = null, object_type = null, device_uuid = null, payload = null, file_list = null){
    if(!object_type){
        console.error("Impossible to push object: no object_type specified");
        return
    }

    if(object_type != "device" && !device_uuid){
        console.error("No device_uuid specified to push object " + object_type);
        return       
    }

    if(object_type == "device" && !payload){
        console.error("Impossible to push device: no payload specified");
        return
    }

    if(object_type != "device"){
        if(!file_list){
            console.error("Impossible to push " + object_type + ": no file(s) specified");
            return
        }
        if(file_list.length < 1){
            console.error("Impossible to push " + object_type + ": no file(s) specified");
            return
        }
    }

    var file_type = "";
    var target_api_endpoint= api_base_url + api_device_endpoint;

    // Builds the API Endpoint and the file type based on the object type
    if(object_type == "device"){
        httpRequestAsync("POST", target_api_endpoint, callback, payload, null, callback);
        return
    }else if(object_type == "config"){
        target_api_endpoint+= "/" + device_uuid + api_config_endpoint;
        file_type = "config_file";
    }else if(object_type == "inventory"){
        target_api_endpoint+= "/" + device_uuid + api_inventory_endpoint;
        file_type = "inventory_file";
    }else{
        console.error("Impossible to push object: incorrect object_type attribute");
        return
    }
  
    if(file_list){
        // Creates the payload to send containing the list of the files to push
        Array.from(file_list).forEach(function (file){
            var form_data = new FormData();
            form_data.append(file_type, file);
            httpRequestAsync("POST", target_api_endpoint, callback, form_data);
          });
    }
}

/**
 * Raises an alert when number of concurrent actions exceeds the limit set by bulk_actions_limit
 * @param  {Number} actions_number - Optional: List of files to push
 */
function raiseBulkActionLimitAlert(actions_number){
    displayAlert("Impossible to perform action", "Number of concurrent actions (" + actions_number +") exceeds limit of " + bulk_actions_limit, "error")
}

/**
 * Removes the propagation of an event to the underlying DOM elements
 * @param  {Event} event - The event for which propagation should be removed
 */
function removeEventPropagation(event){
    // Removes event propagation for standard browsers
    if (event.stopPropagation) {
          event.stopPropagation();
    // Removes event propagation for IE6-8
    } else {
          event.cancelBubble = true;
    }
}

/**
 * Removes the elements flagged as system from an array of objects
 * @param  {Array} objects - The array of objects
 */
function removeSystemObjectsFromList(objects){
    objects = objects.filter(object => !(object.is_system));
    return objects
}

/**
 * Sample callback for debug purposes
 */
function sampleCallback(){
    console.debug("Call successful");
}

/**
 * Sets the available actions for each device type
 * @param  {JSON} data - The object for which the name is set
 */
async function saveDevicesTypesInfo(data){
    if(!data){
        console.error("no data available");
        return
    }

    data = JSON.parse(data);

    if(!data.types){
        console.error("no data available");
        return
    }

    device_types = data.types;

    document.getElementById("ConfigCatalogMenuContainer").innerHTML = ``;

    for([device_type, device_type_params] of Object.entries(device_types)){
        document.getElementById("ConfigCatalogMenuContainer").innerHTML += `
        <li class="nav-item">
            <a id="${device_type}NavItem" href="/config-catalog/${device_type}" class="nav-link">
            <i class="far fa-circle nav-icon"></i>
            <p>${device_type_params["display_name"]}</p>
            </a>
        </li>
        `
    }
}

/**
 * Sets the name of an EasyUCS Object
 * @param  {Object} object - The object for which the name is set
 * @param  {String} object_type - The type of the object {backup/config/device/inventory/report}
 */
function setObjectName(object, object_type){
    if(!object){
        console.error("Impossible to set object name: no object provided");
        return
    }
    
    var object_name = "";

    // If the object already has a name, we keep it as is
    if(object.name != undefined){
        object_name = object.name;

    // Otherwise, we build the name based on the object type and the time at which it was created
    } else {
        if(object_type == "config"){
            object_name = "Config - " + object.timestamp;
        } else if (object_type == "device"){
            object_name = object.device_name;
        } else if (object_type == "inventory"){
            object_name = "Inventory - " + object.timestamp;
        } else if (object_type == "report"){
            object_name = "Report - " + object.timestamp;
        } else if (object_type == "backup"){
            object_name = "Backup - " + object.timestamp;
        }
        else {
            console.error("Error setting object name: object_type not supported");
            return;
        }
    }
    return object_name;
}

/**
 * Sorts an Object (dictionnary) by key, aplphabetically
 * @param  {Object} object - The object for which to sort
 */
function sortObjectByKeys(object) {
    return Object.keys(object).sort().reduce((r, k) => (r[k] = object[k], r), {});
}


/**
 * Toggles the autoscroll button
 * @param  {Boolean} autoscroll - True if autoscroll is on, False otherwise
 */
function toggleLogAutoscroll(autoscroll){
    if(autoscroll){
      log_autoscrolling = true;
      // Changes the button classes to reflect that ON is pressed
      document.getElementById("btn_autoscroll_on").className = "btn btn-primary";
      document.getElementById("btn_autoscroll_off").className = "btn btn-default";
    } else {
      log_autoscrolling = false;
    // Changes the button classes to reflect that OFF is pressed
      document.getElementById("btn_autoscroll_on").className = "btn btn-default";
      document.getElementById("btn_autoscroll_off").className = "btn btn-primary";
    }
}

/**
 * Toggles the log level button
 * @param  {Element} el - The button DOM element
 */
function toggleLogLevel(el){
    log_level = $(el).text().toLowerCase();
    $("#logLevelBtnGroup .btn").removeClass("btn-primary");
    $("#logLevelBtnGroup .btn").addClass("btn-default");
    $(el).removeClass("btn-default");
    $(el).addClass("btn-primary");
    displayLogsToText();
}

/**
 * Truncates a string to the desired length
 * @param  {String} str - The string to truncate
 * @param  {Number} max_str_size - The maximum size of the string
 */
function truncateString(str, max_str_size){
    if (str.length <= max_str_size) { return str; }
    const subString = str.substr(0, max_str_size-1); // the original check
    return (subString.substr(0, subString.lastIndexOf(" ")) ) + "&hellip;";
};

/**
 * Updates the UI of the "select all" checkbox of a table
 * @param  {String} tableId - The ID of the table on which to handle the checkbox click
 */
function updateDataTableSelectAllCtrl(tableId){
    var table = $(tableId).DataTable();
    var rows = table.rows().nodes();
    var chkbox_all = $('input[type="checkbox"]', rows);
    var chkbox_checked = $('input[type="checkbox"]:checked', rows);
    var chkbox_select_all  = $(tableId+"_selectAll").get(0);
 
    // If none of the checkboxes are checked
    if(chkbox_checked.length === 0){
       chkbox_select_all.checked = false;
       if('indeterminate' in chkbox_select_all){
          chkbox_select_all.indeterminate = false;
       }
 
    // If all of the checkboxes are checked
    } else if (chkbox_checked.length === chkbox_all.length){
       chkbox_select_all.checked = true;
       if('indeterminate' in chkbox_select_all){
          chkbox_select_all.indeterminate = false;
       }
 
    // If some of the checkboxes are checked
    } else {
       chkbox_select_all.checked = true;
       if('indeterminate' in chkbox_select_all){
          chkbox_select_all.indeterminate = true;
       }
    }
}

/**
 * Updates the log display panel status in the API
 */
function updateLogBool() {
    target_api_endpoint = api_base_url + api_log_endpoint;
    payload = {
        displayLogsBool: display_logs_bool
    }
    httpRequestAsync("POST", target_api_endpoint, sampleCallback, payload);
}

/**
 * Updates an object in the database
 * @param  {Function} callback - Optional: The function to execute while the call has returned
 * @param  {String} object_type - The type of object to update {config/device/inventory}
 * @param  {String} device_uuid - The ID of the device to which the object belongs
 * @param  {JSON} payload - The parameters of the object to update
 * @param  {Array} object_file - Optional: List of files to update
 */
function updateToDb(callback = null, object_type = null, device_uuid = null, uuid = null, payload = null, object_file = null){
    if(!callback){
        console.error("Impossible to update object: no callback specified");
        return
    }

    if(!object_type){
        console.error("Impossible to update object: no object_type specified");
        return
    }

    if(!device_uuid){
        console.error("No device_uuid specified to update object " + object_type);
        return       
    }

    if(object_type != "device" && !uuid){
        console.error("No uuid specified to update object " + object_type);
        return       
    }

    if(object_type == "device" && !payload){
        console.error("Impossible to update device: no payload specified");
        return
    }

    if(object_type != "device"){
        if(!object_file){
            console.error("Impossible to update " + object_type + ": no file specified");
            return
        }
    }

    var file_type = "";
    var target_api_endpoint= api_base_url + api_device_endpoint + "/" + device_uuid;

    // Builds the API endpoint and file type based on the object type
    if(object_type == "device"){
        httpRequestAsync("PUT", target_api_endpoint, callback, payload);
        return
    }else if(object_type == "config"){
        target_api_endpoint+= api_config_endpoint;
        file_type = "config_file";
    }else if(object_type == "inventory"){
        target_api_endpoint+= api_inventory_endpoint;
        file_type = "inventory_file";
    }else{
        console.error("Impossible to update object: incorrect object_type attribute");
        return
    }

    if(uuid){
        target_api_endpoint+= "/" + uuid;
    }
  
    if(object_file){
        // Creates the payload to send containing the list of the files to push
        var form_data = new FormData();
        form_data.append(file_type, object_file);
        httpRequestAsync("PUT", target_api_endpoint, callback, form_data);
    };
}

/**
 * Validates if an IP Address respects IPv4 format
 * @param  {String} ipaddress - The IP Address to validate
 */
function validateIPaddress(ipaddress) {  
    if (/^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/.test(ipaddress)) {  
      return (true); 
    }  
    return (false)  ;
} 

// Used to display the all devices list table and the subdevices list table
function createRowForDevice(device, phantom=false){
    let device_version = "unknown";
    let claimed = "N/A";
    let on_click = phantom ? 'null' : `window.location='/devices/${device.device_uuid}';`
    if(device.device_version != undefined){
      device_version = device.device_version;
    }
  
    if(device.device_connector_claim_status){
      if(device.device_connector_claim_status == "claimed"){
        if(device.intersight_device_uuid){
          claimed_target = `<a href="/devices/${device.intersight_device_uuid}">${device.device_connector_ownership_name}</a>`
        } else {
          claimed_target = `${device.device_connector_ownership_name}`
        }
        claimed = `Claimed to Intersight (${claimed_target})`;
      } else {
        claimed = "Not claimed";
      }
    }
  
    let date_timestamp = new Date(device.timestamp);
    date_timestamp = Date.parse(date_timestamp)/1000;
  
    let device_data = JSON.stringify({
      "device_name": device.device_name,
      "device_uuid": device.uuid,
      "device_type": device.device_type
    })
  
    return `
    <tr class="${phantom ? 'phantomRow table-warning' : ''}" style="cursor: pointer;">
      <td class = "text-middle">${device_data}</td>
      <td class = "text-middle" onclick="${on_click}">${phantom ? device.device_type : device.device_type_long}</td>
      <td class = "text-middle" onclick="${on_click}">${device.device_name}</td>
      <td class = "text-middle" onclick="${on_click}">${device.user_label ? device.user_label : ""}</td>
      <td class = "text-middle" data-order="${date_timestamp}"  onclick="${on_click}">${device.timestamp}</td>
      <td class = "text-middle" onclick="${on_click}">${claimed}</td>
      <td class = "text-middle" onclick="${on_click}">${device.username}</td>
      <td class = "text-middle" onclick="${on_click}">${device_version}</td>
      <td class = "text-middle" onclick="${on_click}">${device.target}</td>
    </tr>`
  }