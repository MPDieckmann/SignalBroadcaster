# Signal Broadcaster - 2024
# Copyright (C) 2024 MPDieckmann
# This file is part of Signal Broadcaster.
#
# Signal Broadcaster is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Signal Broadcaster is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Signal Broadcaster. If not, see
# <https://www.gnu.org/licenses/>.

FROM python:3.12

RUN update-ca-certificates

WORKDIR /app
RUN chown 1000:1000 /app/

COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

USER 1000:1000

COPY --chown=1000:1000 *.py /app/
COPY --chown=1000:1000 static /app/static
COPY --chown=1000:1000 templates /app/templates
COPY --chown=1000:1000 translations /app/translations

RUN pybabel compile -d translations

ENV APP_SECRET_KEY "Signal's Secret Key"
ENV APP_NAME "Signal Broadcaster"
ENV APP_VERSION 2024.10.27

EXPOSE 8080

HEALTHCHECK --interval=300s --timeout=30s --start-period=5s --retries=3 CMD ["curl", "--fail", "http://localhost:8080/healthcheck"]

CMD ["uwsgi", "--http", ":8080", "--socket", ":8081", "--enable-threads", "--module", "app:app"]
