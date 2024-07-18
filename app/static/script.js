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

// This script allows the checkbox in the table header to select or deselect all
// checkboxes in the same column. It also ensures that when a checkbox in a row
// is deselected, the corresponding checkbox in the header is updated accordingly.

document.querySelectorAll('table input[type="checkbox"]').forEach((checkbox) => {
  checkbox.addEventListener("input", () => {
    // Find the column where the checkbox is located
    const column = checkbox.closest("td, th");
    // Determine the index of the column (1-based)
    const nth = Array.from(column.parentElement.children).indexOf(column) + 1;
    // Find the closest ancestor that is either a thead, tbody, or tfoot
    const closest = checkbox.closest("thead, tbody, tfoot");
    
    if (closest.nodeName.toLowerCase() !== "tbody") {
      // If the checkbox is in the header or footer, update all checkboxes in that column
      closest.parentElement
        .querySelectorAll(`td:nth-child(${nth}) input[type="checkbox"], th:nth-child(${nth}) input[type="checkbox"]`)
        .forEach((_checkbox) => {
          _checkbox.checked = checkbox.checked;
        });
    } else {
      // If the checkbox is in the body of the table, uncheck all checkboxes in the corresponding column
      closest.parentElement
        .querySelectorAll(`thead *:nth-child(${nth}) input[type=checkbox], tfoot *:nth-child(${nth}) input[type=checkbox]`)
        .forEach((checkbox) => (checkbox.checked = false));
    }
  });
});
