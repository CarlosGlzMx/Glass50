# Allows managing SQL databases without CS50
import sqlite3

# All Flask required, allows sessions, rendering pages, and flashing messages
from flask import Flask, redirect, render_template, request, url_for

# Allows loading a flask app without a console
from pyfladesk import init_gui

# Allows obtaining the screen size for Windows
from win32api import GetSystemMetrics

# Opens the SQL database
base = sqlite3.connect("cristales.db", check_same_thread=False)
base.row_factory = sqlite3.Row
db = base.cursor()

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    base.commit()
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Jinja filter to display money in a format
def mxn(value):
    return f"${value:,.1f}"


# Custom filter
app.jinja_env.filters["mxn"] = mxn

# Main page is the one with quotes
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Obtains all values from the HTML quotation form
        length = float(request.form.get("length"))
        height = float(request.form.get("height"))
        sheet = int(request.form.get("sheet"))
        thickness = request.form.get("thickness")
        thickness = int(thickness) if thickness.isnumeric() else thickness
        details = [request.form.get("first_detail"), request.form.get("second_detail")]

        # Calculates all the possible quotations
        quotes = calculateQuotes(length, height, sheet, thickness, details)
        return render_template(
            "results.html", quotes=quotes, length=length, height=height
        )
    else:
        # Collects all database data that will be available to JavaScript
        db.execute("SELECT * FROM sheets ORDER BY name")
        sheets = [dict(row) for row in db.fetchall()]
        db.execute("SELECT * FROM thickness ORDER BY thickness")
        thickness = [dict(row) for row in db.fetchall()]
        db.execute("SELECT * FROM details ORDER BY name,thickness")
        details = [dict(row) for row in db.fetchall()]
        return render_template(
            "quote.html", sheets=sheets, thickness=thickness, details=details
        )


# Second page with the option for modifying prices
@app.route("/modify", methods=["GET", "POST"])
def modify():
    if request.method == "POST":
        # print(request.form)
        if "add_sheet" in request.form:
            return redirect(url_for("add_s"))
        elif "add_detail" in request.form:
            return redirect(url_for("add_d"))
        elif "change_sheet" in request.form:
            thickness = request.form.get("change_sheet")
            return redirect(url_for("change_s", thickness=thickness))
        elif "change_detail" in request.form:
            detail = request.form.get("change_detail")
            return redirect(url_for("change_d", detail=detail))
    else:
        db.execute("SELECT * FROM details ORDER BY name, thickness;")
        details = [dict(row) for row in db.fetchall()]
        db.execute("SELECT * FROM thickness ORDER BY sheet_id, thickness;")
        thicknesses = [dict(row) for row in db.fetchall()]
        db.execute("SELECT * FROM sheets;")
        sheets = [dict(row) for row in db.fetchall()]
        for row in thicknesses:
            for sheet in sheets:
                if row["sheet_id"] == sheet["id"]:
                    row["name"] = sheet["name"]
        return render_template("modify.html", details=details, thicknesses=thicknesses)


# Add new sheet with a form
@app.route("/add_s", methods=["GET", "POST"])
def add_s():
    if request.method == "POST":
        # Obtains data given to the form
        name = request.form.get("name").lower().capitalize()
        thickness = request.form.get("thickness")
        cost = request.form.get("price")

        # Checks if such name already exists
        db.execute("SELECT id FROM sheets WHERE name = ?", (name,))
        possible_names = db.fetchall()

        # Verifies if such name already exists
        if len(possible_names) == 0:
            # Updates sheets table
            db.execute("INSERT INTO sheets (name) VALUES (?)", (name,))
            db.execute("SELECT id FROM sheets WHERE name = ?", (name,))
            new_id = db.fetchall()[0]["id"]

            # Updates thickness table
            db.execute(
                "INSERT INTO thickness (sheet_id,thickness, cost) VALUES (?,?,?)",
                (new_id, thickness, cost),
            )
        else:
            # Verifies if such thickness has been added
            sheet_id = possible_names[0]["id"]
            db.execute(
                "SELECT * FROM thickness WHERE thickness = ? and sheet_id = ?",
                (thickness, sheet_id),
            )
            found_thickness = db.fetchall()

            # Only adds if it hasnt been added
            if len(found_thickness) == 0:
                db.execute(
                    "INSERT INTO thickness (sheet_id, thickness, cost) VALUES (?,?,?)",
                    (sheet_id, thickness, cost),
                )
        return redirect(url_for("modify"))
    else:
        return render_template("add_s.html")


# Add new detail with a form
@app.route("/add_d", methods=["GET", "POST"])
def add_d():
    if request.method == "POST":
        # Collects values from the form
        name = request.form.get("name").lower().capitalize()
        thickness = request.form.get("thickness")
        cost = request.form.get("price")
        cost_type = request.form.get("cost_type")

        # Checks if such detail already exists
        db.execute(
            "SELECT * FROM details WHERE name = ? AND thickness = ?", (name, thickness)
        )
        existing_detail = db.fetchall()
        if len(existing_detail) == 0:
            # Adds to the details table
            db.execute(
                "INSERT INTO details (name,thickness, cost, type) VALUES (?,?,?,?)",
                (name, thickness, cost, cost_type),
            )
        return redirect(url_for("modify"))
    else:
        return render_template("add_d.html")


# Modify a sheet
@app.route("/change_s", methods=["GET", "POST"])
def change_s():
    global thickness_id
    if request.method == "POST":
        if "modifying" in request.form:
            new_cost = request.form.get("price")
            db.execute(
                "UPDATE thickness SET cost = ? WHERE id = ?", (new_cost, thickness_id)
            )
        elif "deleting" in request.form:
            cleanEmptySheet(thickness_id)
            db.execute("DELETE FROM thickness WHERE id = ?", (thickness_id,))
        return redirect(url_for("modify"))
    else:
        thickness_id = request.args["thickness"]
        db.execute("SELECT * FROM thickness WHERE id = ?", (thickness_id,))
        thickness = dict(db.fetchall()[0])
        db.execute("SELECT * FROM sheets WHERE id = ?", (thickness["sheet_id"],))
        thickness["name"] = db.fetchall()[0]["name"]
        return render_template("change_s.html", thickness=thickness)


# Modify a detail
@app.route("/change_d", methods=["GET", "POST"])
def change_d():
    global detail_id
    if request.method == "POST":
        if "modifying" in request.form:
            new_cost = request.form.get("price")
            new_type = request.form.get("cost_type")
            db.execute(
                "UPDATE details SET cost = ?, type = ? WHERE id = ?",
                (new_cost, new_type, detail_id),
            )
        elif "deleting" in request.form:
            db.execute("DELETE FROM details WHERE id = ?", (detail_id,))
        return redirect(url_for("modify"))
    else:
        detail_id = request.args["detail"]
        db.execute("SELECT * FROM details WHERE id = ?", (detail_id,))
        detail = dict(db.fetchall()[0])
        return render_template("change_d.html", detail=detail)


# Applies quotation rules to obtain the prices
def calculateQuotes(l, h, type, thickness, details):
    # Length and height are numbers, type and thickness are ids (or "all"), details is a list with names
    quotes = []
    area = l * h
    perimeter = 2 * l + 2 * h

    # Selected sheet name is obtained, because only id was passed
    db.execute("SELECT name FROM sheets WHERE id = ?", (type,))
    selected_sheet = db.fetchall()[0]["name"]

    # Prepares the case where the "all" option has been selected
    if thickness == "Todos":
        query_thickness = "thickness"
    else:
        db.execute("SELECT thickness FROM thickness WHERE id = ?;", (thickness,))
        query_thickness = str(db.fetchall()[0]["thickness"])

    # Selects the thicknesses available for the sheet id
    db.execute(
        "SELECT * FROM thickness WHERE sheet_id = ? AND thickness ="
        + query_thickness
        + " ORDER BY thickness;",
        (type,),
    )
    options = [dict(row) for row in db.fetchall()]
    query_thickness_tuple = tuple([option["thickness"] for option in options])

    # Corrects if a disabled box was submitted
    for i in range(len(details)):
        if details[i] is None:
            details[i] = "Ninguno"

    # Corrects in the case of an automatically added trailing comma
    query_thickness_tuple = (
        "(" + str(query_thickness_tuple[0]) + ")"
        if len(query_thickness_tuple) == 1
        else query_thickness_tuple
    )

    # Selects the details as well
    db.execute(
        "SELECT * FROM details WHERE name in "
        + str(tuple(details))
        + " AND thickness IN "
        + str(query_thickness_tuple)
        + " ORDER BY name;"
    )
    detail_options = [dict(row) for row in db.fetchall()]

    # In order to post non repeated pairs, they are stored
    sorted_pairs = []

    # Triple for cycle, checks all the possible sheets with its possible details
    for option in options:
        material_cost = option["cost"] * area
        if details[0] != "Ninguno":
            for first_detail in detail_options:
                first_cost = calculateDetail(
                    first_detail["type"], area, perimeter, first_detail["cost"]
                )
                if (
                    details[1] != "Ninguno"
                    and first_detail["thickness"] == option["thickness"]
                ):
                    for second_detail in detail_options:
                        if (
                            second_detail["thickness"] == option["thickness"]
                            and second_detail != first_detail
                        ):
                            second_cost = calculateDetail(
                                second_detail["type"],
                                area,
                                perimeter,
                                second_detail["cost"],
                            )
                            if (
                                sorted([first_detail["name"], second_detail["name"]])
                                not in sorted_pairs
                            ):
                                quotes.append(
                                    {
                                        "type": selected_sheet,
                                        "thickness": option["thickness"],
                                        "details": [
                                            first_detail["name"],
                                            second_detail["name"],
                                        ],
                                        "material_cost": material_cost,
                                        "detail_cost": first_cost + second_cost,
                                        "cost": material_cost
                                        + first_cost
                                        + second_cost,
                                    }
                                )
                                sorted_pairs.append(
                                    sorted(
                                        [first_detail["name"], second_detail["name"]]
                                    )
                                )
                elif first_detail["thickness"] == option["thickness"]:
                    quotes.append(
                        {
                            "type": selected_sheet,
                            "thickness": option["thickness"],
                            "details": [first_detail["name"], "NA"],
                            "material_cost": material_cost,
                            "detail_cost": first_cost,
                            "cost": material_cost + first_cost,
                        }
                    )
        else:
            quotes.append(
                {
                    "type": selected_sheet,
                    "thickness": option["thickness"],
                    "details": ["NA", "NA"],
                    "material_cost": material_cost,
                    "detail_cost": 0,
                    "cost": material_cost,
                }
            )

    # Quote is a list of dictionaries, one for each possible quotation
    return quotes


# Helper function to simplify calculateQuotes()
def calculateDetail(type, area, perimeter, cost):
    if type == "Lineal":
        return cost * perimeter
    elif type == "Cuadrado":
        return cost * area


# Helper function to delete a sheet from a table if all variations have been deleted
def cleanEmptySheet(thick_id):
    db.execute("SELECT * FROM thickness WHERE id = ?", (thick_id,))
    sheet_to_check = db.fetchall()[0]["sheet_id"]
    db.execute("SELECT * FROM thickness WHERE sheet_id = ?", (sheet_to_check,))
    if len(db.fetchall()) <= 1:
        db.execute("DELETE FROM sheets WHERE id = ?", (sheet_to_check,))


# Test so that Flask starts from python
if __name__ == "__main__":
    init_gui(
        app,
        window_title="Sistema de cotizaciones",
        icon="static/logo.png",
        width=GetSystemMetrics(0),
        height=GetSystemMetrics(1),
    )
