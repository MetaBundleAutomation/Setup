# MetaBundle Setup

This folder contains the setup scripts and configuration templates for the MetaBundle system.

## Setup Scripts

- **setup.ps1**: Main setup script that configures environment variables and prepares the system
- **test-setup.ps1**: Script to test the setup configuration
- **run-setup.bat**: Convenience batch file to run the setup script

## Environment Templates

- **dashboard.env.example**: Example environment variables for the Dashboard component
- **infrastructure.env.example**: Example environment variables for the Infrastructure API component

## Usage

The setup script should be run from the root directory using:

`
.\run-setup.bat
`

This will configure the necessary environment variables for running MetaBundle.

## Environment Variable Management

MetaBundle uses a centralized approach to environment variable management:

- Primary configuration comes from system environment variables set by the setup.ps1 script
- Local .env files are only used as fallbacks for development environments
- Docker containers use environment variables passed from the host system
