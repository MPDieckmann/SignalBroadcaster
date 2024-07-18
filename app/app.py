"""
Signal Broadcaster - 2024
Copyright (C) 2024 MPDieckmann
This file is part of Signal Broadcaster.

Signal Broadcaster is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Signal Broadcaster is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Signal Broadcaster. If not, see
<https://www.gnu.org/licenses/>.
"""

# Import necessary libraries and modules
from flask import (
    Flask,
    render_template,
    render_template_string,
    request,
    redirect,
    url_for,
    flash,
    session,
    send_from_directory,
    send_file,
)
from flask_wtf import CSRFProtect
import os
from io import BytesIO
import yaml
import json
from functools import wraps
import requests
import logging
from datetime import datetime

APP_VERSION = "2024-07-24"
APP_DEVELOPERS = ["MPDieckmann"]

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the Flask application
app = Flask(__name__)
app.secret_key = os.getenv("APP_SECRET_KEY", "Signal's Secret Key")
app.config["APP_NAME"] = os.getenv("APP_NAME", "Signal Broadcaster")
app.config["APP_VERSION"] = APP_VERSION
app.config["APP_DEVELOPERS"] = APP_DEVELOPERS
csrf = CSRFProtect(app)  # CSRF protection
app.debug = True

# Configure session cookies
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

# Load user and contact information from YAML files
with open("config/users.yaml", "r") as file:
    users = yaml.safe_load(file)["users"]

with open("config/contacts.yaml", "r") as file:
    data: dict[str, list[dict[str, str]]] = yaml.safe_load(file)
    contacts = {contact["name"]: contact for contact in data.get("contacts", [])}
    groups: dict[str, dict[str, str | list[dict[str, str]]]] = {
        group["name"]: group for group in data.get("groups", [])
    }
    for group in groups.values():
        group["members"] = [
            contacts.get(member, None) for member in group.get("members", [])
        ]
    phones = {contact["phone"]: contact for contact in data.get("contacts", [])}

# Initialize a session for HTTP requests
session_requests = requests.Session()


@app.context_processor
def context_processor():
    """
    Adds global context variables to all templates.

    Returns:
        dict: A dictionary containing the current date and time, app details,
              and session information if the user is logged in.
    """
    data = {
        "now": datetime.now(),
        "app": {
            "name": app.config.get("APP_NAME", ""),
            "developers": app.config.get("APP_DEVELOPERS", []),
            "version": app.config.get("APP_VERSION", ""),
        },
    }

    if session.get("logged_in", False):
        data["contacts"] = contacts
        data["groups"] = groups
        data["session"] = session

    return data


@app.template_filter("json")
def template_filter_json(data):
    """
    Converts Python objects to JSON strings for use in templates.

    Args:
        data: The data to serialize.

    Returns:
        str: The JSON representation of the data, or an error message if serialization fails.
    """
    try:
        return json.dumps(data)
    except Exception:
        return "Failed to serialize " + type(data).__name__ + "."


@app.template_filter("yaml")
def template_filter_yaml(data):
    """
    Converts Python objects to YAML strings for use in templates.

    Args:
        data: The data to serialize.

    Returns:
        str: The YAML representation of the data, or an error message if serialization fails.
    """
    try:
        return yaml.dump(data)
    except Exception:
        return "Failed to serialize " + type(data).__name__ + "."


def get_accounts() -> list[str]:
    """
    Retrieves a list of accounts from the API.

    Returns:
        list: A list of account identifiers, or an empty list if the request fails.
    """
    try:
        response = session_requests.get("http://api/v1/accounts")
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error("Failed to get accounts: %s", e)
        return []


def check_user(username: str, password: str) -> bool:
    """
    Checks if the provided username and password match any user in the database.

    Args:
        username (str): The username to check.
        password (str): The password to check.

    Returns:
        bool: True if the credentials are valid, False otherwise.
    """
    for user in users:
        if user["username"] == username and user["password"] == password:
            return True
    return False


def get_user(username: str, password: str) -> dict[str, str] | None:
    """
    Retrieves user details for the given username and password.

    Args:
        username (str): The username of the user.
        password (str): The password of the user.

    Returns:
        dict or None: User details if credentials are valid, None otherwise.
    """
    for user in users:
        if user["username"] == username and user["password"] == password:
            return user
    return None


def login_required(f):
    """
    Decorator to ensure that a user is logged in.

    Args:
        f (function): The view function to decorate.

    Returns:
        function: The decorated function that requires login.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" not in session:
            flash("Please log in first.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


def link_required(f):
    """
    Decorator to ensure that a device is linked.

    Args:
        f (function): The view function to decorate.

    Returns:
        function: The decorated function that requires device linking.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "device_linked" not in session:
            if session["phone"] in get_accounts():
                session["device_linked"] = True
                return f(*args, **kwargs)
            flash("Please link your device first.", "error")
            return redirect(url_for("link"))
        return f(*args, **kwargs)

    return decorated_function


@app.route("/")
@login_required
@link_required
def index():
    """
    Renders the homepage.

    Returns:
        str: The rendered HTML of the homepage template.
    """
    return render_template("index.jinja", title="Homepage")


@app.route("/healthcheck")
def healthcheck():
    """
    Health check endpoint to verify the server is running.

    Returns:
        tuple: An empty response with a 204 status code.
    """
    return "", 204


@app.route("/help")
@login_required
@link_required
def help():
    """
    Renders the help page.

    Returns:
        str: The rendered HTML of the help template.
    """
    return render_template("help.jinja", title="Help")


@app.route("/info")
def info():
    """
    Provides application information.

    Returns:
        dict: A dictionary containing the app's name and version.
    """
    return {
        "name": app.config.get("APP_NAME", ""),
        "version": app.config.get("APP_VERSION", ""),
    }


@app.route("/send", methods=["POST"])
@login_required
@link_required
def send():
    """
    Handles sending messages to contacts and groups.

    Returns:
        str: A redirect to the homepage with flash messages indicating success or failure.
    """
    sender = {
        "name": session.get("name", ""),
        "phone": session.get("phone", ""),
        "lang": session.get("lang", ""),
    }
    message_de = request.form.get("message_de", "")
    message_en = request.form.get("message_en", "")
    _contacts = request.form.getlist("contacts[]")
    _groups = request.form.getlist("groups[]")

    messages = []

    # Send messages to group members
    for _group in _groups:
        group = groups.get(_group, None)
        if group is None:
            continue
        for member in group.get("members", []):
            if member is None:
                continue
            match member.get("lang", None):
                case "de":
                    messages.append(send_message(sender, message_de, member, group))
                    break
                case "en":
                    messages.append(send_message(sender, message_en, member, group))
                    break
                case _:
                    messages.append(
                        send_message(
                            sender, message_de + "\n\n" + message_en, member, group
                        )
                    )
                    break

    # Send messages to individual contacts
    for _contact in _contacts:
        contact = contacts.get(_contact, None)
        if contact is None:
            continue
        match contact.get("lang", None):
            case "de":
                messages.append(send_message(sender, message_de, contact))
                break
            case "en":
                messages.append(send_message(sender, message_en, contact))
                break
            case _:
                messages.append(
                    send_message(sender, message_de + "\n\n" + message_en, contact)
                )
                break

    flash("Messages sent successfully!", "info")
    flash(json.dumps(messages), "success")

    return redirect(url_for("index"))


def send_message(
    sender: dict[str, str],
    message: str,
    contact: dict[str, str],
    group: dict[str, str] = None,
) -> tuple[bool, int, dict | str]:
    """
    Sends a message to a contact or group.

    Args:
        sender (dict): Information about the sender.
        message (str): The message content.
        contact (dict): The contact to receive the message.
        group (dict, optional): The group to send the message to. Defaults to None.

    Returns:
        tuple: A tuple containing success status, HTTP status code, and response data or error message.
    """
    try:
        message = render_template_string(
            "{% autoescape false %}" + message + "{% endautoescape %}",
            sender=sender,
            contact=contact,
            group=group,
        )
    except Exception as e:
        logger.error("Error rendering message template: %s", e)
        return False, 500, str(e)

    try:
        response = session_requests.post(
            url="http://api/v2/send",
            headers={"Content-Type": "application/json;charset=UTF-8"},
            json={
                "number": sender["phone"],
                "recipients": [contact.get("phone", "")],
                "message": message,
            },
        )
        response.raise_for_status()
        return response.ok, response.status_code, response.json()
    except requests.RequestException as e:
        logger.error("Request failed: %s", e)
        return False, response.status_code if response else 500, str(e)


@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Handles user login.

    Returns:
        str: The rendered HTML of the login template or a redirect to the homepage if already logged in.
    """
    if session.get("logged_in", False):
        return redirect(url_for("index"))
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if check_user(username, password):
            user = get_user(username, password)
            session["logged_in"] = True
            session["username"] = user.get("username", "")
            session["name"] = user.get("name", "")
            session["phone"] = user.get("phone", "")
            session["lang"] = user.get("lang", "")
            flash("Successfully logged in!", "success")
            for account in get_accounts():
                if account == session["phone"]:
                    return redirect(url_for("index"))
            return redirect(url_for("link"))
        else:
            flash("Incorrect username or password!", "danger")
    return render_template("login.jinja", title="Login")


@app.route("/link", methods=["GET"])
@login_required
def link():
    """
    Renders the device linking page.

    Returns:
        str: The rendered HTML of the link template, or redirects to the homepage if the device is already linked.
    """
    if session["phone"] in get_accounts():
        session["device_linked"] = True
        return redirect(url_for("index"))
    return render_template("link.jinja", title="Link Device")


@app.route("/unlink", methods=["GET", "POST"])
@login_required
@link_required
def unlink():
    """
    Handles device unlinking.

    Returns:
        str: The rendered HTML of the unlink template, or redirects to logout if unlinking is successful.
    """
    if (
        request.method == "POST"
        and request.form.get("unlink-device", "false") == "true"
    ):
        try:
            response = session_requests.post(
                "http://api/v1/unregister/" + session["phone"],
                json={"delete_local_data": True},
            )
            response.raise_for_status()
            flash("Device connection removed", "success")
        except requests.RequestException as e:
            logger.error("Failed to unregister device: %s", e)
            flash(response.text if response else str(e), "danger")
        return logout()
    return render_template("unlink.jinja", title="Unlink Device")


@app.route("/link/qrcode.png")
@login_required
def qrcode_png():
    """
    Retrieves the QR code for linking the device.

    Returns:
        Response: The QR code image, or a redirect to the link page if the QR code could not be generated.
    """
    try:
        response = session_requests.get(
            "http://api/v1/qrcodelink?device_name=" + app.config.get("APP_NAME")
        )
        response.raise_for_status()
        return send_file(
            BytesIO(response.content),
            mimetype=response.headers["Content-Type"],
        )
    except requests.RequestException as e:
        logger.error("Failed to get QR code: %s", e)
        flash("QR Code could not be generated!", "error")
        return redirect(url_for("link"))


@app.route("/logout")
def logout():
    """
    Logs out the current user by clearing the session.

    Returns:
        str: A redirect to the login page with a flash message indicating successful logout.
    """
    session.clear()
    flash("Successfully logged out!", "success")
    return redirect(url_for("login"))


@app.route("/static/<path:path>")
def send_static(path):
    """
    Serves static files from the static directory.

    Args:
        path (str): The path to the static file.

    Returns:
        Response: The requested static file.
    """
    return send_from_directory("static", path)


# Run the Flask application in debug mode
if __name__ == "__main__":
    app.run(debug=True)
