# Signal Broadcaster

![License](https://img.shields.io/github/license/MPDieckmann/SignalBroadcaster)
![Issues](https://img.shields.io/github/issues/MPDieckmann/SignalBroadcaster)

Signal Broadcaster is a web application that integrates with Signal to facilitate sending messages to contacts and groups. It utilizes Flask for the web interface and communicates with the Signal CLI REST API to send messages.

## Features

- **Send Messages**: Dispatch messages to individual contacts or groups.
- **User Authentication**: Secure access with login functionality.
- **Device Management**: Link and unlink devices with Signal.
- **Configuration**: Manage user and contact information through YAML files.

## Setup

1. **Clone the Repository**

   ```bash
   git clone https://github.com/MPDieckmann/SignalBroadcaster.git
   cd SignalBroadcaster
   ```

2. **Set Up Docker**

   Ensure Docker and Docker Compose are installed on your system.

3. **Configuration**

   Create the following configuration files in the root directory:

   - `.env` (you can use `.env.template` as a template)
   - `users.yaml` (you can use `users.yaml.template` as a template)
   - `contacts.yaml` (you can use `contacts.yaml.template` as a template)

4. **Build and Start**

   ```bash
   docker-compose up -d --build
   ```

   This command builds the Docker images and starts the services as defined in `compose.yaml`.

5. **Access the Application**

   Open your web browser and navigate to `http://localhost:80` to access the Signal Broadcaster web application.

## Usage

- **Login**: Access the login page at `/login`.
- **Send Messages**: Use the main interface to compose and send messages to contacts and groups.
- **Link Device**: Navigate to `/link` to link your Signal device with the application.
- **Help**: Navigate to `/help` to get a small tutorial on how to use the service.

## Dependencies

- **[Python](https://python.org)**: [PSF License](https://docs.python.org/3/license.html)
- **[uWSGI](https://github.com/unbit/uwsgi)**: [GPL-2.0 License + Linking Exception](https://github.com/unbit/uwsgi/blob/master/LICENSE)
- **[Flask](https://github.com/pallets/flask)**: [BSD 3-Clause License](https://github.com/pallets/flask/blob/main/LICENSE.txt)
- **[Flask-Babel](https://github.com/python-babel/flask-babel)**: [BSD 3-Clause License](https://github.com/python-babel/flask-babel/blob/master/LICENSE)
- **[Flask-WTF](https://github.com/wtforms/flask-wtf)**: [BSD 3-Clause License](https://github.com/wtforms/flask-wtf/blob/main/LICENSE.rst)
- **[Requests](https://github.com/psf/requests)**: [Apache License 2.0](https://github.com/psf/requests/blob/main/LICENSE)
- **[PyYAML](https://github.com/yaml/pyyaml)**: [MIT License](https://github.com/yaml/pyyaml/blob/master/LICENSE)

## License

Signal Broadcaster is licensed under the GNU General Public License v3.0 (GPL-3.0). See the [LICENSE](LICENSE) file for details.
