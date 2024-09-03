/*
repository.js is the javascript used to animate the page repository.html
All functions present here are solely used on the repository.html page
*/

// Global variables
let table = null;
let current_path = null;

// Utility functions
function formatTimestamp(timestamp) {
  if (timestamp === null) {
    return "-";
  }
  const date = new Date(timestamp);
  return date.toLocaleString();
}

function encodeFilename(filename) {
  // Encodes a filename to be safely injected in HTML
  // Returns a list of charcodes
  return Array.from(filename).map(char => char.charCodeAt(0));
}

function decodeFilename(charcodes) {
  // Decodes a list of charcodes to a string
  return charcodes.map(code => String.fromCharCode(code)).join('');
}

function injectFilename(filename) {
  return "decodeFilename([" + encodeFilename(filename)+ "])";
}

function escapeHtml (string) {
  const entityMap = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
    '/': '&#x2F;',
    '`': '&#x60;',
    '=': '&#x3D;'
  };
  return String(string).replace(/[&<>"'`=\/]/g, function (s) {
    return entityMap[s];
  });
}


function formatSizeBytes(bytes) {
  const sizes = ["Bytes", "KB", "MB", "GB", "TB"];
  if (bytes == 0) return "0 Byte";
  const i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)));
  // Round to 2 decimal places, adding Number.EPSILON to avoid floating point errors
  return Math.round((bytes / Math.pow(1024, i) + Number.EPSILON) * 100) / 100 + " " + sizes[i];
}

function setPathSearchParams(path) {
  // Adds the path to the URL as a search parameter to allow for back/forward navigation
  const url = new URL(window.location.href);
  url.searchParams.set("path", path);
  window.history.pushState({}, "", url);
}

function getPathFromURLSearch() {
  // Get path from search parameters
  const params = new URL(document.location).searchParams;
  params.get("path") ? setPath(params.get("path"), first_load=true) : setPath("/", first_load=true);
}

function setPath(path, first_load=false) {
  if (path === current_path) {
    return;
  }
  // Add trailing slash if not present
  if (! path.endsWith('/')) {
    path += '/';
  }
  // Go one folder up if path ends with ../
  if (path.endsWith('../')) {
    return setPath(path.split('/').slice(0, -3).join('/'))
  }
  current_path = path;
  if (!first_load) {
    setPathSearchParams(path);
  }
  updateBreadCrumbs();
  getFilesAndUpdateTable();
}

function afterDOMloaded() {
  table = $("#repositoryFilesTable").DataTable({
    responsive: true,
    lengthChange: false,
    autoWidth: false,
    order: [[0, "asc"]],
    columnDefs: [
      { targets: '_all', visible: true },
      { targets: 3, searchable: false }
    ],
    dom:  "<'row'<'col-sm-12 text-start'f>>" +
                "<'row'<'col-sm-12'tr>>" +
                "<'row'<'col-sm-12 col-md-5'i><'col-sm-12 col-md-7'p>>",
  });
  // Shows "Repository" menu element as selected
  document.getElementById("navLinkRepository").className += " active";
  getPathFromURLSearch();
}

window.onload = function () {
  // Add event listener for back/forward navigation
  // Update the content without reloading the page
  window.addEventListener("popstate", (event) => {
    getPathFromURLSearch();
  });
};

function updateBreadCrumbs() {
  let output = '<li class="breadcrumb-item"><a href="javascript: setPath(`/`)">Repository root</a></li>';
  const folders = current_path.split('/').filter(e => e !== '');
  folders.forEach((folder, index) => {
    const current_folder = folders.slice(0, index+1).join('/')
    output += '<li class="breadcrumb-item"><a href="javascript: setPath('+ injectFilename('/'+current_folder) +')">' + escapeHtml(folder) + '</a></li>'
  });
  const breadCrumbsNode = document.getElementById("repoPathBreadcrumbs")
  breadCrumbsNode.innerHTML = output;
  // Mark the last breadcrumb as active and add an 'aria-current' attribute
  breadCrumbsNode.lastChild.className += " active";
  breadCrumbsNode.lastChild.setAttribute("aria-current", "page");
}

function listFiles(path, callback) {
  let target_api_endpoint = api_base_url + api_repo_files_endpoint;
  if (path != "/") { // Can be removed once the backend API is fixed, as it should handle absolute paths
    target_api_endpoint += encodeURIComponent(path);
  }
  // Once the API fixed, just use the following line
  // target_api_endpoint += encodeURIComponent(path);
  httpRequestAsync("GET", target_api_endpoint, callback);
}

function getFilesAndUpdateTable() {
  listFiles(current_path, updateFilesTable);
}

function newFolder(form) {
  // Creates a folder from the form filled in the modal 
  const formData = new FormData(form);
  const data = {folder_name: formData.get("newFolderName")};
  let target_api_endpoint = api_base_url + api_repo_files_endpoint;
  httpRequestAsync("POST", target_api_endpoint + encodeURIComponent(current_path), getFilesAndUpdateTable, data);
  $("#newFolderModal").modal("toggle");
  form.reset();
}


function repoFileRow(file) {
  // Generates a table row filled with info about a file or folder
  const fileIcon = '<i class="mr-2 fa-regular fa-file"></i>';
  const folderIcon = '<i class="mr-2 fa-solid fa-folder"></i>';
  const checksums_types = ["md5", "sha1", "sha256"];
  let checksums = {};
  // for each type, get the attribute
  checksums_types.forEach(type => {
    if (file[type]) {
      checksums[type] = file[type];
    }
  });

  if (file.name === "..") {
    return [
      '<a class="repoFolderRow" href="javascript:setPath(' + injectFilename(current_path + file.name + "/")+ ')"><span>  ' + folderIcon + '</span> ' + escapeHtml(file.name)+'</a>',
      "-",
      "-",
      "-"
    ]
  }
  if (file.is_directory) {
    return [
      '<a class="repoFolderRow" href="javascript:setPath(' + injectFilename(current_path + file.name + "/")+ ')"><span> ' + folderIcon + '</span> ' + escapeHtml(file.name)+'</a>',
      "-",
      formatTimestamp(file.timestamp_last_modified),
      fileActions(file.name, file.is_directory)
    ]
  } else {
    return [
      '<span>' + fileIcon + '</span>' + escapeHtml(file.name),
      formatSizeBytes(file.size),
      formatTimestamp(file.timestamp_last_modified),
      fileActions(file.name, file.is_directory, checksums)
    ]
  }
}
function fileActions(filename, is_directory, checksums = null) {
  // Generates action buttons depending on the file type
  output = '<div class="btn-group" role="group" aria-label="Actions">'
  output += '<button class="btn btn-primary btn-sm" onclick="askFileRename(' + injectFilename(filename) + ')">Rename</button>';
  output += '<button class="btn btn-secondary btn-sm" onclick="askFileMove(' + injectFilename(filename) + ')">Move</button>';
  output+= '<button class="btn btn-danger btn-sm" onclick="askFileDeletion(' + injectFilename(filename) + ')">Delete</button>';
  if (!is_directory) {
    output += '<button class="btn btn-success btn-sm" onclick="downloadFile(' + injectFilename(filename) + ')">Download</button>';
    output += '<button class="btn btn-info btn-sm" onclick="copyDownloadLink(' + injectFilename(filename) + ', this)">Copy Link</button>';
    output += '<button class="btn btn-warning btn-sm" onclick="showChecksums(' + injectFilename(filename) + ', ' + JSON.stringify(checksums).replaceAll(`"`, `'`) + ')">Checksums</button>';
  }
  output += '</div>';
  return output;
}

function updateFilesTable(response) {
  const parsed = JSON.parse(response);
  const files = parsed.repofiles;
  // Display disk usage 
  const disk_usage = parsed.disk_utilization;
  $("#repoDiskUsage").text(`${formatSizeBytes(disk_usage.available)} available out of ${formatSizeBytes(disk_usage.total)}.`);
  // Compute the percentage to display in the progress bar
  const percentage = Math.round(disk_usage.used * 100 / disk_usage.total);
  const repoDiskUsageBar = document.getElementById("repoDiskUsageBar");
  repoDiskUsageBar.style.width = percentage + "%";
  repoDiskUsageBar.setAttribute("aria-valuenow", percentage);
  repoDiskUsageBar.textContent = percentage + "%";
  // Clear table and add rows from an API response
  table.clear().draw();
  if (current_path != '/') {
    // Add a .. folder to go back
    table.row.add(repoFileRow({name: "..", is_directory: true}));
  }
  files.forEach(file => {
    table.row.add(repoFileRow(file));
  });
  table.draw();
};

function askFileDeletion(name) {
  // Ask for confirmation before deleting a file
  if (confirm("Are you sure you want to delete the file: " + name + "?")) {
    deleteFile(name);
  }
}

function deleteFile(name) {
  // URL encode the path
  let target_api_endpoint = api_base_url + api_repo_files_endpoint;
  httpRequestAsync("DELETE", target_api_endpoint + encodeURIComponent(current_path + name), getFilesAndUpdateTable);
}

function askFileRename(name) {
  // Open the modal to rename a file
  $("#renameFileModal").modal("toggle");
  $("#renameFileOldName").val(name);
  $("#renameFileNewName").val(name);
}

function renameFile() {
  // URL encode the path
  let target_api_endpoint = api_base_url + api_repo_files_endpoint;
  const old_name = $("#renameFileOldName").val();
  const new_name = $("#renameFileNewName").val();
  let target = current_path + new_name;
  if (target.startsWith('/')) {
    // The backend API expects relative paths only
    // To remove once the backend API is fixed
    target = target.slice(1);
  }
  const data = {target_path: target};
  httpRequestAsync("PUT", target_api_endpoint + encodeURIComponent(current_path + old_name), getFilesAndUpdateTable, data);
  $("#renameFileModal").modal("toggle");
}

function downloadFile(filename) {
  // Downloads a file
  download_url = repo_download_endpoint + current_path + filename;
  window.open(download_url);
}

function copyDownloadLink(filename, button) {
  // Copies the download link to the clipboard
  download_url = repo_download_endpoint + current_path + filename;
  navigator.clipboard.writeText(download_url).then(null, function () {
    alert('Failed to copy download link');
  });
  button.textContent = "✓ Link Copied";
  setTimeout(function() {
    button.textContent = "Copy Link";
  }, 2000);
}

function fileUploadURL() {
  // Returns the URL to upload a file
  let api_target = api_base_url + api_repo_upload_endpoint 
  if ( current_path != '/') {
    api_target += encodeURIComponent(current_path);
  }
  return api_target;
}

Dropzone.options.fileUpload = {
  url: fileUploadURL,
  chunking: true,
  forceChunking: true,
  maxFilesize: 10240, // 10GB
  chunkSize: 10485760, // 10MB
  params(files, xhr, chunk) {
    if (chunk) {
      return {
        uuid: chunk.file.upload.uuid,
        chunk_index: chunk.index,
        total_file_size: chunk.file.size,
        dzchunksize: this.options.chunkSize,
        total_chunk_count: chunk.file.upload.totalChunkCount,
        chunk_byte_offset: chunk.index * this.options.chunkSize,
      };
    }
  },
  success(file) {
    $("#uploadFileModal").modal("hide");
    Dropzone.forElement(fileUpload).removeFile(file);
    displayAlert("Upload success", `File "${file.name}" successfully uploaded`, "success");
    getFilesAndUpdateTable();
  },
  error(file, response) {
    $("#uploadFileModal").modal("hide");
    Dropzone.forElement(fileUpload).removeFile(file);
    displayAlert(`Error uploading "${file.name}"`, `${response.message}`);
    getFilesAndUpdateTable();
  },
}

function askFileMove(name) {
  // Open the modal to move a file
  $("#moveFileModal").modal("toggle");
  $("#moveFileName").val(name);
  $("#moveFileTarget").val(current_path);
  listFiles(current_path, updateFolderSelectList);
}

function updateFolderSelectList(response) {
  // Update the folder selection list in the move file modal  
  const folderSelectList = document.getElementById("folderSelectList");
  folderSelectList.innerHTML = "";
  const files = JSON.parse(response).repofiles;
  if ($("#moveFileTarget").val() != '/') {
    // Add a .. folder to go back
    folderSelectList.innerHTML += folderSelectListItem("..");
  }
  files.forEach(file => {
    if (file.is_directory) {
      folderSelectList.innerHTML += folderSelectListItem(file.name);
    }
  });
}

function folderSelectListItem(folderName) {
  // Generates a list item for the folder selection list
  return `<button type="button" onclick="folderSelect(${injectFilename(folderName)})" class="py-2 list-group-item list-group-item-action"><i class="fa-solid fa-folder"></i>  ${escapeHtml(folderName)}</button>`
}
function folderSelect(folderName) {
  // Updates the target folder in the move file modal and lists the files in the selected folder
  let new_path = $("#moveFileTarget").val() + folderName + '/';
  if (new_path.endsWith('../')) {
    // Go one folder up if path ends with ../
    new_path = new_path.split('/').slice(0, -3).join('/');
  }
  if (! new_path.endsWith("/")) {
    new_path += "/";
  }
  $("#moveFileTarget").val(new_path);
  listFiles(new_path, updateFolderSelectList);
}

function moveFile() {
  // Asks the API to move a file to a new location
  const target_api_endpoint = api_base_url + api_repo_files_endpoint;
  const name = $("#moveFileName").val();
  let target = $("#moveFileTarget").val() + name;
  if (target.startsWith('/')) {
    // The backend API expects relative paths only
    // To remove once the backend API is fixed
    target = target.slice(1);
  }
  const data = {target_path: target};
  httpRequestAsync("PUT", target_api_endpoint + encodeURIComponent(current_path + name), getFilesAndUpdateTable, data);
  $("#moveFileModal").modal("toggle");
}

function prefillUrlDownloadName(url) {
  // Prefill the upload URL input with the current path
  document.getElementById("urlDownloadName").value = new URL(url).pathname.split('/').pop();;
}

function urlDownload(form) {
  const fd = new FormData(form);
  let target_api_endpoint = api_base_url + api_repo_url_download_endpoint;
  if (current_path != "/") {
    // Can be removed once the backend API is fixed
    target_api_endpoint += encodeURIComponent(current_path);
  }
  const data = {
    url: fd.get("urlDownloadURL"),
    filename: fd.get("urlDownloadName"),
    verify_ssl: fd.get("urlDownloadVerifySSL") == "on",
  };
  httpRequestAsync("POST", target_api_endpoint, (e) => trackTask(JSON.parse(e).task, "Downloading " + escapeHtml(data.filename)), data);
  $("#urlDownloadModal").modal("toggle");
}

function showChecksums(filename, checksums) {
  // Shows the checksums of a file
  let output = "";
  document.getElementById("checksumsModalName").textContent = filename;
  if (Object.keys(checksums).length == 0) {
    output = "No checksums available for this file.";
  }
  for (const [key, value] of Object.entries(checksums)) {
    output += `<div class="form-group">
      <label for="sum-${key}">${key.toUpperCase()}</label>
      <input type="text" class="form-control" name="sum-${key}" value="${value}" readonly onclick="copyInputValue(this)" />
    </div>`;
  }
  document.getElementById("checksumsModalBody").innerHTML = output;
  
  $("#checksumsModal").modal("toggle");
}

function copyInputValue(input) {
  // Copies the value of an input to the clipboard
  navigator.clipboard.writeText(input.value).then(null, function () {
    alert('Failed to copy value');
  });
  const original_value = input.value;
  setTimeout(function() {
    input.value = original_value;
  }, 2000);
  input.value = "✓ Copied";
}

function computeChecksums(filename) {
  let target_api_endpoint = api_base_url + api_repo_checksum_endpoint;
  target_api_endpoint += encodeURIComponent(current_path + filename);
  httpRequestAsync("POST", target_api_endpoint, (e) => trackTask(JSON.parse(e).task, "Computing checksums for " + filename));
  $("#checksumsModal").modal("toggle");
}

function getTask(task_uuid, callback) {
  let target_api_endpoint = api_base_url + api_task_endpoint + '/' + task_uuid;
  httpRequestAsync("GET", target_api_endpoint, callback);
}

function trackTask(task, message, call_count=0, interval=5000) {
  // Tracks a task until it is successful
  if (call_count == 0) {
    alertActionStarted(message);
  } else if (call_count > 12) {
    // Stop after 5s * 12 = 60s
    return;
  }
  call_count++;
  setTimeout(function() {
    getTask(task, function(response) {
      const parsed = JSON.parse(response).task;
      if (parsed.status == "successful") {
        displayAlert(parsed.status_message, message, "success");
        getFilesAndUpdateTable();
      } else if (parsed.status == "failed") {
        displayAlert(parsed.status_message, message);
      }
    }
    );
  }, interval);
}