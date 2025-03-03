param (
    [switch]$Rebuild = $false
)

Write-Host "MetaBundle Server Docker Setup" -ForegroundColor Cyan
Write-Host "=============================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is installed
try {
    $dockerVersion = docker --version
    Write-Host "Docker detected: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "Error: Docker is not installed or not in PATH. Please install Docker Desktop." -ForegroundColor Red
    exit 1
}

# Check if docker-compose is available
try {
    $composeVersion = docker-compose --version
    Write-Host "Docker Compose detected: $composeVersion" -ForegroundColor Green
} catch {
    Write-Host "Docker Compose is part of Docker Desktop. Continuing..." -ForegroundColor Yellow
}

# Check if setup.ps1 has been run by looking for environment variables
$githubToken = [Environment]::GetEnvironmentVariable("GITHUB_TOKEN", "Machine")
if (-not $githubToken) {
    Write-Host "Warning: GITHUB_TOKEN environment variable not found." -ForegroundColor Yellow
    Write-Host "Have you run the setup script? If not, please run:" -ForegroundColor Yellow
    Write-Host ".\run-setup.bat" -ForegroundColor Yellow
    Write-Host ""
    $continue = Read-Host "Continue anyway? (y/n)"
    if ($continue -ne "y") {
        exit 0
    }
}

# Check for domain configuration
$apiDomain = [Environment]::GetEnvironmentVariable("API_DOMAIN", "Machine")
$dashboardDomain = [Environment]::GetEnvironmentVariable("DASHBOARD_DOMAIN", "Machine")

$usingDomains = ($apiDomain -ne $null -and $apiDomain -ne "localhost" -and 
                $dashboardDomain -ne $null -and $dashboardDomain -ne "localhost")

if ($usingDomains) {
    Write-Host ""
    Write-Host "Domain Configuration Detected:" -ForegroundColor Cyan
    Write-Host "- API Domain: $apiDomain" -ForegroundColor Yellow
    Write-Host "- Dashboard Domain: $dashboardDomain" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Ensure your DNS records are properly configured to point to this server." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Building and starting MetaBundle services..." -ForegroundColor Cyan

# Build and start containers
if ($Rebuild) {
    Write-Host "Rebuilding all containers..." -ForegroundColor Yellow
    docker-compose build --no-cache
}

docker-compose up -d

# Get the API port from environment or use default
$apiPort = [Environment]::GetEnvironmentVariable("API_PORT", "Machine")
if (-not $apiPort) { $apiPort = "9090" }

Write-Host ""
Write-Host "MetaBundle services are running!" -ForegroundColor Green

if ($usingDomains) {
    Write-Host "- Infrastructure API: https://$apiDomain" -ForegroundColor Cyan
    Write-Host "- Dashboard: https://$dashboardDomain" -ForegroundColor Cyan
} else {
    Write-Host "- Infrastructure API: http://localhost:$apiPort" -ForegroundColor Cyan
    Write-Host "- Dashboard: http://localhost:5001" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "To view logs, run: docker-compose logs -f" -ForegroundColor Yellow
Write-Host "To stop services, run: docker-compose down" -ForegroundColor Yellow
