var IntervalGetLogs;
var IntervalGetProgression;
var autoscrolling = true;
var globalLogs = [];
var configurationFile = "";

function httpGetAsync(theUrl, callback) {
	var xmlHttp = new XMLHttpRequest();
	xmlHttp.onreadystatechange = function() {
		if (xmlHttp.readyState == 4 && xmlHttp.status == 200)
			callback(xmlHttp.responseText);
	}
	xmlHttp.open("GET", theUrl, true); // true for asynchronous
	xmlHttp.send(null);
}

function httpPostAsync(theUrl, callback, payload) {
	var xmlHttp = new XMLHttpRequest();
	xmlHttp.onreadystatechange = function() {
		if (xmlHttp.readyState == 4 && xmlHttp.status == 200)
			callback(xmlHttp.responseText);
	}
	xmlHttp.open("POST", theUrl, true); // true for asynchronous
	xmlHttp.setRequestHeader("Content-Type", "application/json; charset=utf-8");
	xmlHttp.send(payload);
}

function finish() {
	getLogs();
	getProgression();
	clearInterval(IntervalGetLogs);
	clearInterval(IntervalGetProgression);
	document.getElementById("submit").disabled = false
}

function getProgression() {
	httpGetAsync('/status', makeProgress);
	// Wait for some time before running this script again
}

function makeProgress(ret) {
	$(".progress-bar").css("width", ret + "%").text(ret + " %");
}

function getLogs() {
	httpGetAsync('/getlogs', addLogs);
}

function addLogs(logs) {

	var level, logs_splitted, logs_length, index;
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

	if (logs != "") {
		level = document
				.querySelector('input[name="inlineRadioOptions"]:checked').value;
		logs_splitted = logs.split("\r");
		// minus 1 to remove the '\r' at the end of logs
		logs_length = logs_splitted.length - 1;

		for (index = 0; index < logs_length; ++index) {
			var lvl;
			lvl = logs_splitted[index].match(/:: ([\s\S]*?) ::/);
			if (severity[lvl[1].toLowerCase()] <= severity[level]) {
				document.getElementById("logs").value += logs_splitted[index];
				document.getElementById("logs").value += "\r";
			}
		}
	}
	// To get the scroll bar to the bottom
	var textarea = document.getElementById("logs");
	if (autoscrolling) {
		textarea.scrollTop = textarea.scrollHeight;
	}
}

function getMetadata() {

	httpGetAsync('/getmetadata', buildTree);

}

function readLocalFile(filePath) {

	var file = filePath.files[0];
	var reader = new FileReader();

	reader.onload = function(e) {
		displayFile(e.target.result);
	}
	reader.readAsText(file);
}

function readRemoteFile(path, filename) {

	var payload = '{"path": "' + path + '","file": "' + filename + '"}';

	httpPostAsync('/readremotefile', displayFile, payload);
}

function displayFile(config_file) {

	try {
		var jsonobj = JSON.parse(config_file);
		$('#json-viewer').jsonViewer(jsonobj);
		configurationFile = jsonobj;
		document.getElementById("validated").innerHTML = "YES";
		document.getElementById("submit").disabled = false;
		}
	
	catch (e) {
		$('#json-viewer').jsonViewer();
		alert("Invalid JSON file: " + e);
		document.getElementById("validated").innerHTML = "NO";
		configurationFile = "";
		document.getElementById("submit").disabled = true;
		}	
}

function buildTree(metadata) {

	var tree = [];
	var list_file = JSON.parse(metadata);
	var revision = " -  revision: "

	Object
			.keys(list_file)
			.forEach(
					function(currentKey) {
						var found_category = false;
						var found_subcategory = false;
						for (var i = 0; i < tree.length; i++) {
							if (tree[i]["text"] == list_file[currentKey].metadata[0].category) {
								found_category = true;
								for (var j = 0; j < tree[i]["children"].length; j++) {
									if (tree[i]["children"][j]["text"] == list_file[currentKey].metadata[0].subcategory) {
										found_subcategory = true;
										tree[i]["children"][j]["children"]
												.push({
													"text" : list_file[currentKey].metadata[0].name  + revision.italics() + list_file[currentKey].metadata[0].revision,
													"file" : currentKey,
													"path" : list_file[currentKey].path,
													"revision" : list_file[currentKey].metadata[0].revision
												});
										break;
									}

								}
								if (!found_subcategory) {
									tree[i]["children"]
											.push({
												"text" : list_file[currentKey].metadata[0].subcategory,
												"children" : []
											});
									tree[i]["children"][j]["children"]
											.push({
												"text" : list_file[currentKey].metadata[0].name + revision.italics() + list_file[currentKey].metadata[0].revision,
												"file" : currentKey,
												"path" : list_file[currentKey].path,
												"revision" : list_file[currentKey].metadata[0].revision
											});
								}
								break;
							}
						}

						if (!found_category) {
							tree
									.push({
										"text" : list_file[currentKey].metadata[0].category
									});
							tree[i]["children"] = [];
							tree[i]["children"]
									.push({
										"text" : list_file[currentKey].metadata[0].subcategory,
										"children" : []
									});
							tree[i]["children"][0]["children"]
									.push({
										"text" : list_file[currentKey].metadata[0].name + revision.italics() + list_file[currentKey].metadata[0].revision,
										"file" : currentKey,
										"path" : list_file[currentKey].path,
										"revision" : list_file[currentKey].metadata[0].revision
									});

						}
						found_category = false;
						found_subcategory = false;
					});

	// alert(JSON.stringify(tree));
	// console.log(tree);

	$('#tree').jstree({
		'core' : {
			'data' : tree
		},
		"plugins" : [ "sort" ]
	});

	$('#tree')
	// listen for event
	.on('changed.jstree', function(e, data) {

		if (data.node.original.file) {
			readRemoteFile(data.node.original.path, data.node.original.file);
		}
	})
	// create the instance
	.jstree();

	$('#tree')
	// listen for event
	.on('hover_node.jstree', function(e, data) {
		$("#" + data.node.id).prop('title', data.node.original["file"]);
	})
	// create the instance
	.jstree();
}

function startScript() {

	var validated = document.getElementById("validated").innerHTML;
	var payload = "";

	// UCS Manager fields
	var setup = document.getElementById('setup').checked;
	var ipadd = document.getElementById('ip').value;
	var user_id = document.getElementById('user').value;
	var passwd = document.getElementById('pwd').value;
	var reset = "";
	var setup = [];

	// CIMC fields
	var setup_cimc = document.getElementById('setup-cimc').checked;
	var ipadd_cimc = document.getElementById('ip-cimc').value;
	var user_id_cimc = document.getElementById('user-cimc').value;
	var passwd_cimc = document.getElementById('pwd-cimc').value;
	var reset_cimc = "";
	var setup_cimc = "";

	// UCS Central fields
	var ipadd_ucsc = document.getElementById('ip-ucsc').value;
	var user_id_ucsc = document.getElementById('user-ucsc').value;
	var passwd_ucsc = document.getElementById('pwd-ucsc').value;

	if (setup) {
		if (!(validateIPaddress(document.getElementById('ip-fab-a').value))) {
			alert("You have entered an invalid IP address in field DHCP IP Fabric A !");
			return;
		}
		if (((document.getElementById('ip-fab-b').value) != "")
				&& !(validateIPaddress(document.getElementById('ip-fab-b').value))) {
			alert("You have entered an invalid IP address in field DHCP IP Fabric B !");
			return;
		}
	}

	if (setup_cimc) {
		if (!(validateIPaddress(document.getElementById('dhcp-ip-cimc').value))) {
			alert("You have entered an invalid IP address in field DHCP IP CIMC !");
			return;
		}
	}

	if (setup && validated != "YES") {
		alert("You have selected setup option, but your JSON file is not selected or not correctly formatted!");
		return;
	}

	if (setup_cimc && validated != "YES") {
		alert("You have selected setup option, but your JSON file is not selected or not correctly formatted!");
		return;
	}

	if (document.getElementById('reset').checked) {
		reset = "true";
	}

	if (document.getElementById('reset-cimc').checked) {
		reset_cimc = "true";
	}

	if (document.getElementById('setup').checked) {
		setup.push(document.getElementById('ip-fab-a').value);
		setup.push(document.getElementById('ip-fab-b').value);
	}

	if (document.getElementById('setup-cimc').checked) {
		setup_cimc = document.getElementById('dhcp-ip-cimc').value;
	}

	active_tab = $('ul#deviceTabs').find('li.active')[0].id

    if (active_tab == "ucsm") {
        payload = '{"ip": "' + ipadd + '","user": "' + user_id + '","pwd": "'
			+ passwd + '","reset": "' + reset + '","setup": '
			+ JSON.stringify(setup) + ',"ucs_type":"' + active_tab + '","config_json": ['
			+ JSON.stringify(configurationFile) + ']}';
    }
    else if (active_tab == "cimc") {
        payload = '{"ip": "' + ipadd_cimc + '","user": "' + user_id_cimc + '","pwd": "'
			+ passwd_cimc + '","reset": "' + reset_cimc + '","setup": "'
			+ setup_cimc + '","ucs_type":"' + active_tab + '","config_json": ['
			+ JSON.stringify(configurationFile) + ']}';
    }
    else if (active_tab == "ucsc") {
        payload = '{"ip": "' + ipadd_ucsc + '","user": "' + user_id_ucsc + '","pwd": "'
			+ passwd_ucsc + '","reset": "' + '","setup": "'
			+ '","ucs_type":"' + active_tab + '","config_json": ['
			+ JSON.stringify(configurationFile) + ']}';
    }

	$(".progress-bar").css("width", 0 + "%").text(0 + " %");

	// Reset progression bar & logs textarea in case we restart the script
	IntervalGetLogs = setInterval("getLogs()", 500);
	IntervalGetProgression = setInterval("getProgression()", 500);

	document.getElementById("logs").value = "";
	document.getElementById("submit").disabled = true;
	
	if (reset) {
		if (confirm("Are you sure you want to erase all configuration on "
				+ ipadd + "?") == false) {
			finish();
		}
	}

	if (reset-cimc) {
		if (confirm("Are you sure you want to erase all configuration on "
				+ ipadd-cimc + "?") == false) {
			finish();
		}
	}

	httpPostAsync('/init', finish, payload);
}

/*function initScript(config_json) {

	var ipadd = document.getElementById('ip').value;
	var user_id = document.getElementById('user').value;
	var passwd = document.getElementById('pwd').value;

	var reset = "";
	var setup = [];

	if (document.getElementById('reset').checked) {
		reset = "true";
	}

	if (document.getElementById('setup').checked) {
		setup.push(document.getElementById('ip-fab-a').value);
		setup.push(document.getElementById('ip-fab-b').value);
	}

	var payload = '{"ip": "' + ipadd + '","user": "' + user_id + '","pwd": "'
			+ passwd + '","reset": "' + reset + '","setup": '
			+ JSON.stringify(setup) + ',"config_json": [' + config_json + ']}';

	$(".progress-bar").css("width", 0 + "%").text(0 + " %");

	// Reset progression bar & logs textarea in case we restart the script
	IntervalGetLogs = setInterval("getLogs()", 500);
	IntervalGetProgression = setInterval("getProgression()", 500);

	document.getElementById("logs").value = "";
	document.getElementById("submit").disabled = true;

	if (reset) {
		if (confirm("Are you sure you want to erase all configuration on "
				+ ipadd + " ?") == false) {
			finish();
		}
	}

	httpPostAsync('/init', finish, payload);
}*/

function disconnect() {
	httpGetAsync('/disconnect', display);
}

function validateIPaddress(ipaddress) {
	var ipformat = /^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
	if (ipaddress.match(ipformat)) {
		return (true);
	}
	return (false);
}

function fabricFields() {
	if (document.getElementById('setup').checked) {
		document.getElementById('ip-fab-a').disabled = false;
		document.getElementById('ip-fab-b').disabled = false;
	} else {
		document.getElementById('ip-fab-a').disabled = true;
		document.getElementById('ip-fab-b').disabled = true;
	}
}

function cimcFields() {
	if (document.getElementById('setup-cimc').checked) {
		document.getElementById('dhcp-ip-cimc').disabled = false;
	} else {
		document.getElementById('dhcp-ip-cimc').disabled = true;
	}
}

document.addEventListener("DOMContentLoaded", function(event) {
	var input = document.getElementById('config_file');
	document.getElementById("submit").disabled = true;
	input.onclick = function() {
		this.value = null;
		document.getElementById("validated").innerHTML = "N/A";
		document.getElementById("submit").disabled = true;
		configurationFile = "";
    	$('#json-viewer').jsonViewer();
	};

	input.onchange = function() {
		readLocalFile(this)
	};
});

$(document)
		.ready(
				function() {
					$('#toggle_event_editing button')
							.click(
									function() {
										if ($(this).hasClass('locked_active')
												|| $(this).hasClass(
														'unlocked_inactive')) {
											/* code to do when unlocking */
											/*
											 * var textarea =
											 * document.getElementById("logs");
											 * textarea.scrollTop = 0;
											 */
											autoscrolling = false;
										} else {
											/* code to do when locking */
											autoscrolling = true;
										}
										/* reverse locking status */
										$('#toggle_event_editing button')
												.eq(0)
												.toggleClass(
														'locked_inactive locked_active btn-default btn-primary');
										$('#toggle_event_editing button')
												.eq(1)
												.toggleClass(
														'unlocked_inactive unlocked_active btn-primary btn-default');
									});
					/* $('#tree').treeview({data: getTree()}); */
					getMetadata();
				});

$(document).ready(
		function() {
			$(document).tooltip(
					{
						track : true,
						position : {
							my : "center bottom-20",
							at : "center top",
							using : function(position, feedback) {
								$(this).css(position);
								$("<div>").addClass("arrow").addClass(
										feedback.vertical).addClass(
										feedback.horizontal).appendTo(this);
							}
						}
					});
		});

$(document).ready(function() {
	$('a[data-toggle="tab"]').on('shown.bs.tab', function(e) {
		e.target // newly activated tab
		e.relatedTarget // previous active tab
		document.getElementById("submit").disabled = true;
		document.getElementById("validated").innerHTML = "NO";
		configurationFile ="";
		document.getElementById("config_file").value = "";
		$('#json-viewer').jsonViewer();	
	})
});
