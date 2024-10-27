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
    render_template,
    request,
    redirect,
    session,
    # send_from_directory,
    url_for,
)
from flask_babel import gettext
import logging

from functions import (
    get_accounts,
    login_user,
    logout_user,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


from app import app


@app.route("/about", endpoint="about")
async def about():
    """
    Renders the about page.

    Returns:
        str: The rendered HTML of the about template.
    """
    return render_template(
        "about.jinja",
        title=gettext("About the Project"),
    )


@app.route("/info", endpoint="info")
async def info():
    """
    Provides application information.

    Returns:
        dict: A dictionary containing the app's name and version.
    """
    return {
        "name": app.config.get("APP_NAME", ""),
        "version": app.config.get("APP_VERSION", ""),
    }


@app.route("/login", methods=["GET", "POST"], endpoint="login")
async def login():
    """
    Handles user login.

    Returns:
        str: The rendered HTML of the login template or a redirect to the homepage if already logged in.
    """
    if session.get("logged_in", False):
        return redirect(url_for("index"))
    if request.method == "POST":
        if login_user():
            for account in get_accounts():
                if account == session["phone"]:
                    return redirect(url_for("index"))
            return redirect(url_for("link"))
    return render_template(
        "login.jinja",
        title=gettext("Login"),
    )


@app.route("/logout", endpoint="logout")
async def logout():
    """
    Logs out the current user by clearing the session.

    Returns:
        str: A redirect to the login page with a flash message indicating successful logout.
    """
    logout_user()
    return redirect(url_for("login"))


# @app.route("/static/<path:path>", endpoint="static")
# async def static(path):
#     """
#     Serves static files from the static directory.

#     Args:
#         path (str): The path to the static file.

#     Returns:
#         Response: The requested static file.
#     """
#     return send_from_directory("static", path)


@app.route("/healthcheck", endpoint="healthcheck")
async def healthcheck():
    """
    Health check endpoint to verify the server is running.

    Returns:
        tuple: An empty response with a 204 status code.
    """
    return "", 204
