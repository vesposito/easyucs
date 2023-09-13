/*
task.js is the javascript used to animate the page task.html

All functions present here are solely used on the task.html page

NOTE: task.html represents the detailed view for a single task, containing the different task steps
*/

// Global variables
var loaded_task = null;
var task_uuid = null;

// Gets executed when DOM has loaded
function afterDOMloaded() {
    // Forces page reload when using browser back button
    if(typeof window.performance != "undefined" && window.performance.navigation.type == 2){
        window.location.reload(true);
    }
    url = window.location.href;
    task_uuid = url.substring(url.lastIndexOf('/') + 1);

    refreshData();
};

// Gets executed every X [in milliseconds]: here we are fetching the tasks
window.setInterval(function() {
    if((loaded_task) && (loaded_task.status == "in_progress")){
        getTask(loaded_task.uuid);
    }
}, 5000);

/**
 * Displays a task in the UI
 * @param  {JSON} data - The data returned by getting the task from the API
 */
function displayTask(data){
    if(!data){
        console.error('No data to display!')
        return
    }

    data = JSON.parse(data)

    if(!data["task"]){
        console.error("Impossible to display task no data provided");
        return
    }

    loaded_task = data["task"];

    document.getElementById('TaskCardContainer').innerHTML = ``
    document.getElementById('taskDisplayContainer').innerHTML = ``

    var color = "info";
    var progress_bar = ``;
    var status_message = ``;
    var status_title = ``;
    var cancel_task = ``;

    if(loaded_task.status == "pending"){
        // If the task is in pending status, we do not display it
        window.location.href = "/tasks";
        return
    } else if(loaded_task.status == "in_progress"){
        cancel_task = `
        <div class="card-link" style = "cursor: pointer;" onclick = "cancelTask('${loaded_task.uuid}', '${loaded_task.description}' );"><i class="fas fa-times pr-1"></i>Cancel</div>
        `
        status_title = "In Progress"
        progress_bar = `
        <div class="progress my-1">
            <div class="progress-bar bg-success" role="progressbar" style="width: ${loaded_task.progress}%" aria-valuenow="${loaded_task.progress}" aria-valuemin="0" aria-valuemax="100"></div>
        </div>

        `;
    } else {
        status_message = `
        <p class="card-text">${loaded_task.status_message}</p>
        `;

        if (loaded_task.status == "successful"){
            color = "success";
            status_title = "Successful"
            status_message = ``
        } else {
            color = "danger";
            status_title = "Failed"
        }
    }

    
    // Populates the task display container with the task UI elements
    document.getElementById("TaskCardContainer").innerHTML += `
    <div class="callout callout-${color} text-dark">
        <h3>Task: ${loaded_task.description}</h3>
        <p class="m-0" ><b>${status_title}</b></p>
        ${status_message}
        ${progress_bar}
        <small class = "py-1" >EasyUCS Version: ${loaded_task.easyucs_version}</small>
        <div class="d-flex flex-row">
        ${cancel_task}
        </div>
    </div>
    `
  
    // Takes the steps from the task
    steps = loaded_task.steps


    if(loaded_task.status != "in_progress"){
        document.getElementById('taskDisplayContainer').innerHTML = `
        <div class="time-label">
            <span class="bg-${color} px-2">Ended: ${loaded_task.timestamp_stop}</span>
        </div>
        `
    }

    // For each step, populates the task display container with the step's UI elements
    steps.map(step => {
        var step_status = "";
        var step_bg = "primary";
        var step_time = "Not started";
        if(step.status){
            if(step.status == "successful"){
                step_bg = "success";
            } else if (step.status == "failed"){
                step_bg = "danger";
            } else if (step.status == "in_progress"){
                step_bg = "warning";
            }

            step_status = step.status.replace("_", " ");
            step_status = " - " + capitalizeFirstLetter(step_status);

            if(step.timestamp_stop){
                step_time = "Ended: " + step.timestamp_stop;
            } else {
                step_time = "Started: " + step.timestamp_start;
            }
        }
        if(!step.description){
            step.description = "Not started";
        } 
        document.getElementById('taskDisplayContainer').innerHTML += `
        <div>
        <!-- Before each timeline item corresponds to one icon on the left scale -->
            <span class="fa bg-${step_bg}">
                <!-- a strong element with the custom content, in this case a number -->
                <strong class="fa-stack-1x fa-icon-inner-text">${step.order} </strong>
            </span>
          <!-- Timeline item -->
          <div class="timeline-item">
          <!-- Time -->
            <span class="time"><i class="fas fa-clock"></i> ${step_time} </span>
            <!-- Header. Optional -->
            <h3 class="timeline-header"><a href="">${step.name.match(/[A-Z][a-z]+|[0-9]+/g).join(" ")}</a> ${step_status} </h3>
            <!-- Body -->
            <div class="timeline-body">
                ${step.description}
            </div>
          </div>
        </div>
        `;
    });
    


    

    // Populates the task display container with the task UI elements
    document.getElementById('taskDisplayContainer').innerHTML +=
    `
    <!-- The last icon means the story is complete -->
    <div class="time-label">
        <span class="bg-green px-2">Started: ${loaded_task.timestamp_start}</span>
    </div>
    `
}

/**
 * Gets a task from the API
 */
function getTask(){
    getFromDb(displayTask, "task", null, task_uuid);
}

/**
 * Refreshes dynamic data on the page
 */
function refreshData(){
    getTask();
}