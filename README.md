# MetaBundle Setup Guide

This repository provides an automated setup process for the MetaBundle infrastructure and dashboard.

## Overview

MetaBundle consists of two main components:

1. **Infrastructure Backend**: Manages GitHub repositories and Docker containers
2. **Dashboard Frontend**: Provides a user interface to monitor and manage the infrastructure

## Quick Start

The easiest way to set up MetaBundle is to use our automated setup wizard:

1. Clone this repository
2. Run `run-setup.bat` (Windows) or `setup.ps1` (PowerShell)
3. Follow the on-screen instructions

The setup wizard will:
- Guide you through configuring all necessary environment variables
- Create the required `.env` files in both the Infrastructure and Dashboard directories
- Offer to start the services for you

## Prerequisites

- Windows with PowerShell 5.1 or later
- Python 3.8 or higher
- Git
- Docker (optional, can run in test mode without Docker)
- GitHub account with access to your organization
- GitHub Personal Access Token with repo permissions

## Manual Setup

If you prefer to set up MetaBundle manually, follow these steps:

### 1. Generate GitHub Personal Access Token

1. Go to your GitHub account settings: https://github.com/settings/tokens
2. Click "Generate new token" (classic)
3. Give it a descriptive name like "MetaBundle Access"
4. Select the following scopes:
   - `repo` (Full control of private repositories)
   - `read:org` (Read organization information)
5. Click "Generate token"
6. Copy the token (you won't be able to see it again)

### 2. Configure Environment Variables

#### Infrastructure Backend

Create a `.env` file in the Infrastructure directory using the template in `infrastructure.env.example`.

#### Dashboard Frontend

Create a `.env` file in the Dashboard directory using the template in `dashboard.env.example`.

### 3. Start the Services

Follow the instructions in the "Next Steps" section after running the setup wizard.

## Configuration Reference

### Infrastructure Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| GITHUB_TOKEN | GitHub Personal Access Token | (Required) |
| GITHUB_ORG | GitHub Organization name | MetaBundleAutomation |
| REPO_BASE_DIR | Base directory for repositories | C:/repos/metabundle_repos |
| API_PORT | Port for the Infrastructure API | 8080 |
| WEBSOCKET_PORT | Port for WebSocket connections | 8081 |
| ENVIRONMENT | Environment (development/production) | development |
| METABUNDLE_TEST_MODE | Run in test mode without Docker | false |

### Dashboard Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| INFRASTRUCTURE_API_URL | URL of the Infrastructure API | http://localhost:8080 |
| DEBUG_MODE | Run in debug mode | true |
| SECRET_KEY | Secret key for session security | (Generated) |

## Troubleshooting

### Backend API Connection Issues

If the Dashboard cannot connect to the Backend API:

1. Verify that the Backend API is running
2. Check that the `INFRASTRUCTURE_API_URL` in the Dashboard's `.env` file is correct
3. Ensure there are no firewall issues blocking the connection

### GitHub API Authentication Issues

If you see GitHub API authentication errors:

1. Verify that your GitHub token is valid
2. Check that the token has the required permissions
3. Ensure the token is correctly set in the `.env` file

### Port Conflicts

If you encounter port conflicts:

1. Run the setup wizard again and specify different ports
2. Or manually update the ports in both `.env` files

## Support

If you encounter any issues not covered in this guide, please open an issue in this repository or contact the MetaBundle team.
