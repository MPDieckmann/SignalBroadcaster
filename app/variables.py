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
import yaml


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
