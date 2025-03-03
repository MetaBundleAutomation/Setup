# MetaBundle Production Deployment Guide

This guide provides instructions for deploying MetaBundle to a production server with custom domain names.

## Prerequisites

1. A server with Docker and Docker Compose installed
2. Domain names configured with DNS records pointing to your server
3. Ports 80 and 443 open on your server firewall

## Deployment Steps

### 1. Clone the Repository

```bash
git clone https://github.com/MetaBundleAutomation/Setup.git metabundle
cd metabundle
```

### 2. Configure Environment Variables

Run the setup script with your domain information:

```powershell
powershell -ExecutionPolicy Bypass -File ".\Setup\setup.ps1" -NonInteractive `
  -GitHubToken "your-github-token" `
  -GitHubOrg "your-github-org" `
  -CloneRepos "yes" `
  -Environment "production" `
  -TestMode "false" `
  -BaseDirectory "/path/to/your/repo/directory" `
  -ApiDomain "api.metabundle.yourdomain.com" `
  -DashboardDomain "dashboard.metabundle.yourdomain.com"
```

### 3. Start the Docker Containers

```powershell
cd ".\Setup"
powershell -ExecutionPolicy Bypass -File ".\run-docker.ps1"
```

The system will automatically:
- Set up an Nginx reverse proxy
- Configure SSL certificates using Let's Encrypt
- Route traffic to the appropriate containers based on domain names

### 4. Verify the Deployment

After the containers are running, verify that your services are accessible:

- Dashboard: https://dashboard.metabundle.yourdomain.com
- API: https://api.metabundle.yourdomain.com

## Troubleshooting

### SSL Certificate Issues

If you encounter SSL certificate issues:

1. Check that your domains are correctly pointing to your server
2. Verify that ports 80 and 443 are open
3. Check the Let's Encrypt container logs:
   ```
   docker logs letsencrypt-companion
   ```

### API Connection Issues

If the Dashboard cannot connect to the API:

1. Check that both containers are running:
   ```
   docker ps
   ```
2. Verify the API URL configuration in the Dashboard environment variables
3. Check the container logs:
   ```
   docker logs metabundle-infrastructure-api
   docker logs metabundle-dashboard
   ```

## Maintenance

### Updating the Application

To update to a new version:

1. Pull the latest changes:
   ```
   git pull
   ```
2. Rebuild and restart the containers:
   ```
   cd ".\Setup"
   powershell -ExecutionPolicy Bypass -File ".\run-docker.ps1" -Rebuild
   ```

### Backup

Regularly backup your environment variables and any custom configurations:

1. Environment files:
   ```
   cp .env .env.backup
   ```
2. Nginx configurations and SSL certificates:
   ```
   cp -r nginx nginx.backup
   ```
