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

# Importieren der notwendigen Bibliotheken und Module
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

# Konfiguration des Loggings
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialisierung der Flask-App
app = Flask(__name__)
app.secret_key = os.getenv("APP_SECRET_KEY", "Signal's Secret Key")
app.config["APP_NAME"] = os.getenv("APP_NAME", "Signal Broadcaster")
app.config["APP_VERSION"] = APP_VERSION
app.config["APP_DEVELOPERS"] = APP_DEVELOPERS
csrf = CSRFProtect(app)  # Schutz gegen CSRF-Angriffe
app.debug = True

# Konfiguration der Session-Cookies
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

# Laden der Benutzer- und Kontaktinformationen aus YAML-Dateien
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

# Initialisierung einer Sitzung für HTTP-Anfragen
session_requests = requests.Session()


# Fügt den Shortcut now hinzu
@app.context_processor
def context_processor():
    data = {
        "now": datetime.now(),
        "app": {
            "name": app.config.get("APP_NAME", ""),
            "developers": app.config.get("APP_DEVELOPERS", []),
            "version": app.config.get("APP_VERSION", ""),
        },
    }

    if session.get("logged_in", False) == True:
        data["contacts"] = contacts
        data["groups"] = groups
        data["session"] = session

    return data


@app.template_filter("json")
def template_filter_json(data):
    try:
        return json.dumps(data)
    except Exception:
        return "Failed to serialize " + type(data).__name__ + "."


@app.template_filter("yaml")
def template_filter_json(data):
    try:
        return yaml.dump(data)
    except Exception:
        return "Failed to serialize " + type(data).__name__ + "."


# Funktion zum Abrufen von Accounts
def get_accounts() -> list[str]:
    try:
        response = session_requests.get("http://api/v1/accounts")
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error("Failed to get accounts: %s", e)
        return []


# Funktion zum Überprüfen von Benutzeranmeldedaten
def check_user(username, password) -> bool:
    for user in users:
        if user["username"] == username and user["password"] == password:
            return True
    return False


# Funktion zum Abrufen von Benutzerdetails
def get_user(username, password) -> dict[str, str] | None:
    for user in users:
        if user["username"] == username and user["password"] == password:
            return user
    return None


# Decorator zum Überprüfen, ob ein Benutzer eingeloggt ist
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" not in session:
            flash("Bitte melde Dich zunächst an.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


# Decorator zum Überprüfen, ob ein Gerät verlinkt ist
def link_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "device_linked" not in session:
            if session["phone"] in get_accounts():
                session["device_linked"] = True
                return f(*args, **kwargs)
            flash("Bitte verbinde zunächst Dein Gerät.", "error")
            return redirect(url_for("link"))
        return f(*args, **kwargs)

    return decorated_function


# Route für die Startseite
@app.route("/")
@login_required
@link_required
def index():
    return render_template("index.jinja", title="Startseite")


@app.route("/healthcheck")
def healthcheck():
    return "", 204


# Route für die Hilfeseite
@app.route("/help")
@login_required
@link_required
def help():
    return render_template("help.jinja", title="Hilfe")


@app.route("/info")
def info():
    return {
        "name": app.config.get("name", ""),
        "version": app.config.get("version", ""),
    }


# Route zum Senden von Nachrichten
@app.route("/send", methods=["POST"])
@login_required
@link_required
def send():
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

    # Nachrichten an Gruppenmitglieder senden
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

    # Nachrichten an einzelne Kontakte senden
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

    flash("Nachrichten erfolgreich gesendet!", "info")
    flash(json.dumps(messages), "success")

    return redirect(url_for("index"))


# Funktion zum Senden einer Nachricht
def send_message(
    sender: dict[str, str],
    message: str,
    contact: dict[str, str],
    group: dict[str, str] = None,
):
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


# Route für die Login-Seite
@app.route("/login", methods=["GET", "POST"])
def login():
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
            flash("Erfolgreich eingeloggt!", "success")
            for account in get_accounts():
                if account == session["phone"]:
                    return redirect(url_for("index"))
            return redirect(url_for("link"))
        else:
            flash("Benutzername oder Password falsch!", "danger")
    return render_template("login.jinja", title="Anmeldung")


# Route für die Geräteverlinkung
@app.route("/link", methods=["GET"])
@login_required
def link():
    if session["phone"] in get_accounts():
        session["device_linked"] = True
        return redirect(url_for("index"))
    return render_template("link.jinja", title="Gerät verbinden")


# Route zum Aufheben der Geräteverlinkung
@app.route("/unlink", methods=["GET", "POST"])
@login_required
@link_required
def unlink():
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
            flash("Verbindung zum Gerät wurde gelöscht", "success")
        except requests.RequestException as e:
            logger.error("Failed to unregister device: %s", e)
            flash(response.text if response else str(e), "danger")
        return logout()
    return render_template("unlink.jinja", title="Geräteverbindung löschen")


# Route zum Abrufen des QR-Codes für die Verlinkung
@app.route("/link/qrcode.png")
@login_required
def qrcode_png():
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
        flash("QR Code konnte nicht generiert werden!", "error")
        return redirect(url_for("link"))


# Route zum Ausloggen
@app.route("/logout")
def logout():
    session.clear()
    flash("Erfolgreich ausgeloggt!", "success")
    return redirect(url_for("login"))


# Route zum Senden von statischen Dateien
@app.route("/static/<path:path>")
def send_static(path):
    return send_from_directory("static", path)


# Starten der Flask-Anwendung im Debug-Modus
if __name__ == "__main__":
    app.run(debug=True)
