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
import logging
import requests
from flask import flash, render_template, request, redirect, session, send_file, url_for
from flask_babel import gettext
from io import BytesIO

from app import app
from functions import (
    link_device,
    unlink_device,
    link_required,
    login_required,
    send_message,
    session_requests,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.route("/", endpoint="index")
@login_required
@link_required
async def index():
    """
    Renders the homepage.

    Returns:
        str: The rendered HTML of the homepage template.
    """
    return render_template(
        "index.jinja",
        title=(gettext("Hello %(name)s") % {"name": session.get("name")}),
    )


@app.route("/help", endpoint="help")
@login_required
@link_required
async def help():
    """
    Renders the help page.

    Returns:
        str: The rendered HTML of the help template.
    """
    return render_template(
        "help.jinja",
        title=gettext("Help"),
    )


@app.route("/send", methods=["POST"], endpoint="send")
@login_required
@link_required
async def send():
    """
    Handles sending messages to contacts and groups.

    Returns:
        str: A redirect to the homepage with flash messages indicating success or failure.
    """
    send_message()
    return redirect(url_for("index"))


@app.route("/link", methods=["GET"], endpoint="link")
@login_required
async def link():
    """
    Renders the device linking page.

    Returns:
        str: The rendered HTML of the link template, or redirects to the homepage if the device is already linked.
    """
    if link_device():
        return redirect(url_for("index"))
    return render_template(
        "link.jinja",
        title=gettext("Link Device"),
    )


@app.route("/unlink", methods=["GET", "POST"], endpoint="unlink")
@login_required
@link_required
async def unlink():
    """
    Handles device unlinking.

    Returns:
        str: The rendered HTML of the unlink template, or redirects to logout if unlinking is successful.
    """
    if (
        request.method == "POST"
        and request.form.get("unlink-device", "false") == "true"
    ):
        unlink_device()
        return redirect(url_for("login"))
    return render_template(
        "unlink.jinja",
        title=gettext("Unlink Device"),
    )


@app.route("/link/qrcode.png", endpoint="link_qrcode_png")
@login_required
async def link_qrcode_png():
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
        flash(gettext("QR Code could not be generated!"), "error")
        return redirect(url_for("link"))
