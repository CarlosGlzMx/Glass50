let sheet_box = document.getElementById("sheet_box");
let thickness_box = document.getElementById("thickness_box");
let first_detail_box = document.getElementById("first_detail_box");
let second_detail_box = document.getElementById("second_detail_box");

// Global variable used in 3 separate functions
let possible_thickness;
let selected_thickness;
let unique_details;

sheet_box.addEventListener("change", reloadThickness);

function reloadThickness() {
  // Deactivates the select until the new options are set
  thickness_box.disabled = true;

  // Finds the id of the selected sheet name, to find its possibles thicknesses
  let selected_sheet = parseInt(sheet_box.value);

  // Resets the inner HTML and builds all the options, starting with "all"
  possible_thickness = [];
  thickness_box.innerHTML = "";
  thickness_box.innerHTML +=
    '<option value = "" selected disabled = "disabled">-</option>';
  thickness_box.innerHTML += '<option value = "Todos">Todos</option>';

  for (let i = 0; i < thickness.length; i++) {
    if (thickness[i]["sheet_id"] === selected_sheet) {
      possible_thickness.push(thickness[i]["thickness"]);
      thickness_box.innerHTML += `<option value = ${thickness[i]["id"]}>${thickness[i]["thickness"]}</option>`;
    }
  }

  // Restarts the select box with the new options
  thickness_box.disabled = false;
  clearFirstDetail();
  clearSecondDetail();
  thickness_box.addEventListener("change", reloadFirstDetail);
}

function reloadFirstDetail() {
  // Deactivates the select until the new options are set
  first_detail_box.disabled = true;

  // Finds the selected thickness by value, not by id. Considers the "all" option
  if (thickness_box.options[thickness_box.selectedIndex].text === "Todos") {
    selected_thickness = "Todos";
  } else {
    selected_thickness = parseInt(
      thickness_box.options[thickness_box.selectedIndex].text
    );
  }

  // Resets the inner HTML
  first_detail_box.innerHTML = "";
  first_detail_box.innerHTML += '<option value = "Ninguno" selected>Ninguno</option>';
  unique_details = [];

  // Cycles through the details checking if they can be applied to certain thickness
  for (let i = 0; i < details.length; i++) {
    // If the "all" option has been selected, all thicknesses in possible_thicknesses are considered
    if (
      details[i]["thickness"] === selected_thickness ||
      (selected_thickness === "Todos" &&
        possible_thickness.includes(details[i]["thickness"]) &&
        !unique_details.includes(details[i]["name"]))
    ) {
      first_detail_box.innerHTML += `<option value = '${details[i]["name"]}'>${details[i]["name"]}</option>`;
      unique_details.push(details[i]["name"]);
    }
  }

  // Restarts the select box with the new options
  first_detail_box.disabled = false;
  clearSecondDetail();
  first_detail_box.addEventListener("change", reloadSecondDetail);
}

function reloadSecondDetail() {
  // Deactivates the select until the new options are set
  second_detail_box.disabled = true;
  let selected_detail = first_detail_box.value;

  // Resets the inner HTML
  second_detail_box.innerHTML = "";
  second_detail_box.innerHTML += '<option value = "Ninguno" selected>Ninguno</option>';
  unique_details = [];

  // Same cycle but doesnt consider the detail selected as first
  for (let i = 0; i < details.length; i++) {
    // If the "all" option has been selected, all thicknesses in possible_thicknesses are considered
    if (
      details[i]["thickness"] === selected_thickness ||
      (selected_thickness === "Todos" &&
        possible_thickness.includes(details[i]["thickness"]))
    ) {
      if (
        details[i]["name"] != selected_detail &&
        !unique_details.includes(details[i]["name"])
      ) {
        second_detail_box.innerHTML += `<option value = '${details[i]["name"]}'>${details[i]["name"]}</option>`;
        unique_details.push(details[i]["name"]);
      }
    }
  }

  // Restarts the select box with new options
  if (selected_detail !== "Ninguno") {
    second_detail_box.disabled = false;
  }
}

// Function for demonstration when there are no values
sheet_box.addEventListener("mouseenter", function () {
  if (sheets.length === 0 || thickness.length === 0 || details.length === 0) {
    alert("No hay registros para las hojas, los espesores o los acabados");
  }
});

// Clear functions to manage out of order selection of values
function clearFirstDetail() {
  first_detail_box.disabled = true;
  first_detail_box.innerHTML = "";
  first_detail_box.innerHTML += '<option value = "Ninguno">Ninguno</option>';
}

function clearSecondDetail() {
  second_detail_box.disabled = true;
  second_detail_box.innerHTML = "";
  second_detail_box.innerHTML += '<option value = "Ninguno">Ninguno</option>';
}
