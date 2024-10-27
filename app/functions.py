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

import json
import requests
from flask import flash, redirect, render_template_string, request, session, url_for
from flask_babel import gettext
from functools import wraps
from logging import getLogger

from app import app
from variables import contacts, groups, users

logger = getLogger(__name__)

# Initialize a session for HTTP requests
session_requests = requests.Session()


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


def get_locale():
    lang_code = request.args.get("lang", None)

    if lang_code and lang_code in app.config["LANGUAGES"]:
        session["lang_code"] = lang_code
        return lang_code

    if session.get("lang_code", None):
        return session.get("lang_code")

    lang_code = request.accept_languages.best_match(app.config["LANGUAGES"])
    session["lang_code"] = lang_code

    return lang_code


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


def link_device():
    if session["phone"] in get_accounts():
        session["device_linked"] = True
        return True
    return False


def unlink_device():
    try:
        response = session_requests.post(
            "http://api/v1/unregister/" + session["phone"],
            json={"delete_local_data": True},
        )
        response.raise_for_status()
        flash(gettext("Device successfully unlinked."), "success")
    except requests.RequestException as e:
        logger.error("Failed to unregister device: %s", e)
        flash(response.text if response else str(e), "danger")
    logout_user()


def login_user():
    username = request.form.get("username", "")
    password = request.form.get("password", "")
    if check_user(username, password):
        user = get_user(username, password)
        session["logged_in"] = True
        session["username"] = user.get("username", "")
        session["name"] = user.get("name", "")
        session["phone"] = user.get("phone", "")
        session["lang"] = user.get("lang", "")
        flash(gettext("Successfully logged in!"), "success")
        return True
    flash(gettext("Incorrect username or password!"), "danger")
    return False


def logout_user():
    session.clear()
    flash(gettext("Successfully logged out!"), "success")


def send_message():
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
                    messages.append(_send_message(sender, message_de, member, group))
                case "en":
                    messages.append(_send_message(sender, message_en, member, group))
                case _:
                    messages.append(
                        _send_message(
                            sender, message_de + "\n\n" + message_en, member, group
                        )
                    )

    # Send messages to individual contacts
    for _contact in _contacts:
        contact = contacts.get(_contact, None)
        if contact is None:
            continue
        match contact.get("lang", None):
            case "de":
                messages.append(_send_message(sender, message_de, contact))
            case "en":
                messages.append(_send_message(sender, message_en, contact))
            case _:
                messages.append(
                    _send_message(sender, message_de + "\n\n" + message_en, contact)
                )

    flash(gettext("Messages sent successfully!"), "info")
    flash(json.dumps(messages), "success")


def _send_message(
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


# Decorators


def link_required(f):
    """
    Decorator to ensure that a device is linked.

    Args:
        f (function): The view function to decorate.

    Returns:
        function: The decorated function that requires device linking.
    """

    @wraps(f)
    async def decorated_function(*args, **kwargs):
        if "device_linked" not in session:
            if session["phone"] in get_accounts():
                session["device_linked"] = True
                return await f(*args, **kwargs)
            flash(gettext("Please link your device first."), "error")
            return redirect(url_for("link"))
        return await f(*args, **kwargs)

    return decorated_function


def login_required(f):
    """
    Decorator to ensure that a user is logged in.

    Args:
        f (function): The view function to decorate.

    Returns:
        function: The decorated function that requires login.
    """

    @wraps(f)
    async def decorated_function(*args, **kwargs):
        if "logged_in" not in session:
            flash(gettext("Please log in first."), "error")
            return redirect(url_for("login"))
        return await f(*args, **kwargs)

    return decorated_function
