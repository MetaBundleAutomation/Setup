param (
    [switch]$Rebuild = $false
)

Write-Host "MetaBundle Server Docker Setup with Environment Variables" -ForegroundColor Cyan
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is installed
try {
    $dockerVersion = docker --version
    Write-Host "Docker detected: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "Error: Docker is not installed or not in PATH. Please install Docker Desktop." -ForegroundColor Red
    exit 1
}

# Check if setup.ps1 has been run
Write-Host "Checking for environment variables..." -ForegroundColor Cyan
Write-Host "Note: Environment variables should be set by running .\Setup\run-setup.bat first" -ForegroundColor Yellow
Write-Host ""

# Get environment variables with fallbacks
$apiPort = [Environment]::GetEnvironmentVariable("API_PORT", "Machine")
if (-not $apiPort) { $apiPort = "9090" }

$websocketPort = [Environment]::GetEnvironmentVariable("WEBSOCKET_PORT", "Machine")
if (-not $websocketPort) { $websocketPort = "9091" }

$githubToken = [Environment]::GetEnvironmentVariable("GITHUB_TOKEN", "Machine")
if (-not $githubToken) { $githubToken = "" }

$githubOrg = [Environment]::GetEnvironmentVariable("GITHUB_ORG", "Machine")
if (-not $githubOrg) { $githubOrg = "MetaBundle" }

$repoBaseDir = [Environment]::GetEnvironmentVariable("REPO_BASE_DIR", "Machine")
if (-not $repoBaseDir) { $repoBaseDir = "/repos" }

$environment = [Environment]::GetEnvironmentVariable("ENVIRONMENT", "Machine")
if (-not $environment) { $environment = "development" }

$testMode = [Environment]::GetEnvironmentVariable("METABUNDLE_TEST_MODE", "Machine")
if (-not $testMode) { $testMode = "true" }

$debugMode = [Environment]::GetEnvironmentVariable("DEBUG_MODE", "Machine")
if (-not $debugMode) { $debugMode = "true" }

$secretKey = [Environment]::GetEnvironmentVariable("SECRET_KEY", "Machine")
if (-not $secretKey) { $secretKey = "dev_key_replace_in_production" }

$flaskRunPort = [Environment]::GetEnvironmentVariable("FLASK_RUN_PORT", "Machine")
if (-not $flaskRunPort) { $flaskRunPort = "5000" }

Write-Host ""
Write-Host "Building and starting MetaBundle services with environment variables..." -ForegroundColor Cyan

Write-Host "Using the following environment variables:" -ForegroundColor Green
Write-Host "  - API_PORT: $apiPort" -ForegroundColor Green
Write-Host "  - WEBSOCKET_PORT: $websocketPort" -ForegroundColor Green
Write-Host "  - GITHUB_ORG: $githubOrg" -ForegroundColor Green
Write-Host "  - ENVIRONMENT: $environment" -ForegroundColor Green
Write-Host "  - METABUNDLE_TEST_MODE: $testMode" -ForegroundColor Green
Write-Host "  - DEBUG_MODE: $debugMode" -ForegroundColor Green
Write-Host "  - FLASK_RUN_PORT: $flaskRunPort" -ForegroundColor Green
Write-Host ""

# Build and start containers
if ($Rebuild) {
    Write-Host "Rebuilding all containers..." -ForegroundColor Yellow
    docker-compose build --no-cache
}

# Set environment variables for docker-compose
$env:API_PORT = $apiPort
$env:WEBSOCKET_PORT = $websocketPort
$env:GITHUB_TOKEN = $githubToken
$env:GITHUB_ORG = $githubOrg
$env:REPO_BASE_DIR = $repoBaseDir
$env:ENVIRONMENT = $environment
$env:METABUNDLE_TEST_MODE = $testMode
$env:DEBUG_MODE = $debugMode
$env:SECRET_KEY = $secretKey
$env:FLASK_RUN_PORT = $flaskRunPort

docker-compose up -d

Write-Host ""
Write-Host "MetaBundle services are running!" -ForegroundColor Green
Write-Host "- Infrastructure API: http://localhost:$apiPort" -ForegroundColor Cyan
Write-Host "- Dashboard: http://localhost:5001" -ForegroundColor Cyan
Write-Host ""
Write-Host "To view logs, run: docker-compose logs -f" -ForegroundColor Yellow
Write-Host "To stop services, run: .\stop-docker.ps1" -ForegroundColor Yellow
