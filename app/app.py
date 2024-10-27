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
import logging
import os
import yaml
from datetime import datetime
from flask import Flask, session
from flask_babel import Babel, _
from flask_wtf import CSRFProtect

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the Flask application
app = Flask(__name__)
app.secret_key = os.getenv("APP_SECRET_KEY", "Signal's Secret Key")
app.config.update(
    APP_NAME=os.getenv("APP_NAME", "Signal Broadcaster"),
    APP_VERSION=os.getenv("APP_VERSION"),
    APP_DEVELOPERS=["MPDieckmann"],
    LANGUAGES=["en", "de"],
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    BABEL_DEFAULT_LOCALE="en",
)
csrf = CSRFProtect(app)

import public_routes
import protected_routes
from functions import get_locale
from variables import contacts, groups


babel = Babel(app, locale_selector=get_locale)


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


# Run the Flask application in debug mode
if __name__ == "__main__":
    app.run(debug=True)
