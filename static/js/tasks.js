/*
tasks.js is the javascript used to animate the page tasks.html

All functions present here are solely used on the tasks.html page

NOTE: tasks.html represents the view for all tasks, accessible from the task notification panel
*/

// Global variables
var loaded_tasks = null;
var taskTable = null;

// Gets executed when DOM has loaded
function afterDOMloaded() {
    // Forces page reload when using browser back button
    if(typeof window.performance != "undefined" && window.performance.navigation.type == 2){
        window.location.reload(true);
    }

    // Initializes the DataTable that will contain the tasks
    taskTable = createDataTable("#taskTable", 3, 3);
};

/**
 * Displays the tasks in the UI
 * @param  {JSON} data - The data returned by getting the task from the API
 */
function displayPageTasks(task_list){
    loaded_tasks = task_list;

    // Clean table before new entries
    taskTable.clear().draw();

    // For each task, we create the specific row in the DataTable
    loaded_tasks.map( task => {
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


    taskTable.row.add($(`
    <tr style="cursor: pointer;">
        <td>${task.uuid}</td>
        <td class="${text_color}" onclick="${on_click}">${status_title}</td>
        <td onclick="${on_click}">${task.description}</td>
        <td onclick="${on_click}">${task.timestamp}</td>
        <td onclick="${on_click}">${status_message}</td>
        <td onclick="${on_click}">${task_timestamp}</td>
        <td><a href="/devices/${task.device_uuid}">${task.device_name}</a></td>
    </tr>`)).draw();
    });

    // Hides the checkbox column
    taskTable.column(0).visible(false);
}

/**
 * Refreshes dynamic data on the page
 */
function refreshData(){
}
