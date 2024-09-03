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
    tableFromTasks(task_list, taskTable);
    
}

/**
 * Refreshes dynamic data on the page
 */
function refreshData(){
}
