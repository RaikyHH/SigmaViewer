# Sigma Rule Viewer & Collector

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A self-hosted, containerized web application to collect, search, and view Sigma detection rules from various sources. This project provides both a configurable Python collector and a user-friendly Flask-based web interface, all designed to run seamlessly with Docker.



## Features

- **Clean Web Interface**: An intuitive, responsive UI to browse and analyze rules.
- **Powerful Search**: Full-text search across rule titles, descriptions, and raw content.
- **Advanced Filtering**: Filter rules by Level, Status, and MITRE ATT&CK techniques.
- **Detailed View**: Inspect all rule metadata, including formatted detection logic, references, and the original raw YAML.
- **Persistent Storage**: Rules are stored in a local SQLite database, giving you full control over your data.
- **Extensible Collector**: Easily configure `config.json` to pull Sigma rules from various GitHub repositories, single files, or text blobs.
- **Containerized**: Both the viewer and collector are fully containerized for easy, cross-platform deployment using Docker Compose.

## Getting Started

This guide will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

You need to have [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/) installed on your system.

### Installation & Configuration

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/RaikyHH/SigmaViewer.git
    cd SigmaViewer
    ```

2.  **Prepare the Data Directory:**
    The application uses a mounted host directory to persist data. Create a directory on your host machine that will store the database and rule files.
    ```bash
    mkdir ./sigma-data
    ```

3.  **Configure the Collector:**
    Create a configuration file for the collector inside the new data directory.
    ```bash
    touch ./sigma-data/config.json
    ```
    Populate `sigma-data/config.json` with the sources you want to collect rules from. Here is an example configuration:
    ```json
    [
        {
            "name": "SigmaHQ Windows",
            "url": "[https://api.github.com/repos/SigmaHQ/sigma/contents/rules/windows](https://api.github.com/repos/SigmaHQ/sigma/contents/rules/windows)",
            "type": "github_repo_folder",
            "github_token": "",
            "enabled": true
        },
        {
            "name": "SigmaHQ Linux",
            "url": "[https://api.github.com/repos/SigmaHQ/sigma/contents/rules/linux](https://api.github.com/repos/SigmaHQ/sigma/contents/rules/linux)",
            "type": "github_repo_folder",
            "github_token": "",
            "enabled": true
        },
        {
            "name": "Single Rule Example",
            "url": "[https://raw.githubusercontent.com/SigmaHQ/sigma/master/rules/windows/process_creation/proc_creation_win_lolbas_forfiles.yml](https://raw.githubusercontent.com/SigmaHQ/sigma/master/rules/windows/process_creation/proc_creation_win_lolbas_forfiles.yml)",
            "type": "single_file_yaml",
            "enabled": false
        }
    ]
    ```

### Running the Application

We recommend using Docker Compose to manage both the collector and the viewer services.

1.  **Create a `docker-compose.yml` file** in the root of the project with the following content:

    ```yaml
    version: '3.8'

    services:
      collector:
        image: ghcr.io/raikyhh/sigma-collector:latest # Or your own collector image
        container_name: sigma-collector
        volumes:
          - ./sigma-data:/data
        restart: on-failure

      viewer:
        build: . # Build the viewer from the local Dockerfile
        image:  ghcr.io/raikyhh/sigma-viewer:latest
        container_name: sigma-viewer
        volumes:
          - ./sigma-data:/data
        ports:
          - "5000:5000"
        restart: unless-stopped
        depends_on:
          - collector

    volumes:
      sigma-data:
        driver: local
        driver_opts:
          type: 'none'
          o: 'bind'
          device: './sigma-data'
    ```

2.  **Launch the services:**
    Run the following command from the project root. This will build the viewer image, pull the collector image, and start both containers.
    ```bash
    docker-compose up --build -d
    ```
    * The collector will run once to populate the database and then exit.
    * The viewer will start and remain running.

3.  **Access the Web UI:**
    Open your web browser and navigate to **[http://localhost:5000](http://localhost:5000)**.

### Usage

-   Use the left sidebar to search and filter through the collected rules.
-   Click on any rule in the list to view its complete details in the main content area.
-   To re-run the collector and fetch updated rules, you can simply run: `docker-compose up -d collector`

To stop the application, run:
```bash
docker-compose down
