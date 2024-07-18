/*!
 * Signal Broadcaster - 2024
 * Copyright (C) 2024 MPDieckmann
 * This file is part of Signal Broadcaster.
 *
 * Signal Broadcaster is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * Signal Broadcaster is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Signal Broadcaster. If not, see
 * <https://www.gnu.org/licenses/>.
 */

// Dieses Skript ermöglicht es, dass die Checkbox in der Tabellen-
// Kopfzeile alle Einträge der selben Spalte ebenfalls auswählt und
// bei bei Abwahl eines Eintrages automatisch ebenfalls abgewählt
// wird

document.querySelectorAll(`table input[type="checkbox"]`).forEach((checkbox) => {
  checkbox.addEventListener("input", () => {
    const column = checkbox.closest("td, th");
    const nth = Array.from(column.parentElement.children).indexOf(column) + 1;
    const closest = checkbox.closest("thead, tbody, tfoot");
    if (closest.nodeName.toLowerCase() != "tbody") {
      closest.parentElement
        .querySelectorAll(`td:nth-child(${nth}) input[type="checkbox"], th:nth-child(${nth}) input[type="checkbox"]`)
        .forEach((_checkbox) => {
          _checkbox.checked = checkbox.checked;
        });
    } else {
      closest.parentElement
        .querySelectorAll(`thead *:nth-child(${nth}) input[type=checkbox], tfoot *:nth-child(${nth}) input[type=checkbox]`)
        .forEach((checkbox) => (checkbox.checked = false));
    }
  });
});
