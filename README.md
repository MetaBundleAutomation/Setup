# MetaBundle Setup Repository

This repository provides an automated setup process for the MetaBundle infrastructure and dashboard.

## Overview

MetaBundle consists of two main components:

1. **Infrastructure Backend**: Manages GitHub repositories and Docker containers
2. **Dashboard Frontend**: Provides a user interface to monitor and manage the infrastructure

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

## Environment Variables

MetaBundle uses a centralized approach to environment variable management where system environment variables set by the setup.ps1 script are the primary source of configuration, with .env files used only as fallbacks.

## Documentation

For detailed documentation, see [Setup/README.md](Setup/README.md).
