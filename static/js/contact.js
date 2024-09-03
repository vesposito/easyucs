/*
contact.js is the javascript used to animate the page contact.html

All functions present here are solely used on the contact.html page
*/

/**
 * Refreshes dynamic data on the page
 */

function afterDOMloaded(){
    document.getElementById("navLinkContact").className += " active";

}

function refreshData(){
    // No dynamic data to refresh on this page
}

function sendMessage(){
    console.error("Sending Message Impossible: This function is not available yet");
    displayAlert("Impossible to send message", "Function not yet available.", "error")
}

