# MetaBundle Setup Repository

This repository contains the setup scripts and Docker configuration for the MetaBundle system.

## Repository Structure

- **Setup/**: Contains all setup scripts, Docker management scripts, and configuration templates
- **docker-compose.yml**: Docker Compose configuration for running MetaBundle components

## Quick Start

1. Clone this repository
2. Run the setup wizard:
   ```
   powershell -ExecutionPolicy Bypass -File ".\Setup\setup.ps1"
   ```
3. Start the Docker containers:
   ```
   powershell -ExecutionPolicy Bypass -File ".\Setup\run-docker-with-env.ps1"
   ```
4. Access the Dashboard at http://localhost:5001

## Docker Commands

- Start containers: `powershell -ExecutionPolicy Bypass -File ".\Setup\run-docker-with-env.ps1"`
- Rebuild containers: `powershell -ExecutionPolicy Bypass -File ".\Setup\run-docker-with-env.ps1" -Rebuild`
- Stop containers: `powershell -ExecutionPolicy Bypass -File ".\Setup\stop-docker.ps1"`
- View logs: `docker-compose logs -f`

## Documentation

For detailed documentation, see [Setup/README.md](Setup/README.md).
