# Test script for the MetaBundle setup
Write-Host "Testing MetaBundle Setup Script..." -ForegroundColor Cyan

# Check if setup.ps1 exists
if (Test-Path -Path ".\setup.ps1") {
    Write-Host " setup.ps1 found" -ForegroundColor Green
} else {
    Write-Host " setup.ps1 not found" -ForegroundColor Red
    exit 1
}

# Check if run-setup.bat exists
if (Test-Path -Path ".\run-setup.bat") {
    Write-Host " run-setup.bat found" -ForegroundColor Green
} else {
    Write-Host " run-setup.bat not found" -ForegroundColor Red
    exit 1
}

# Check if example env files exist
if (Test-Path -Path ".\infrastructure.env.example") {
    Write-Host " infrastructure.env.example found" -ForegroundColor Green
} else {
    Write-Host " infrastructure.env.example not found" -ForegroundColor Red
    exit 1
}

if (Test-Path -Path ".\dashboard.env.example") {
    Write-Host " dashboard.env.example found" -ForegroundColor Green
} else {
    Write-Host " dashboard.env.example not found" -ForegroundColor Red
    exit 1
}

# Check if README.md exists
if (Test-Path -Path ".\README.md") {
    Write-Host " README.md found" -ForegroundColor Green
} else {
    Write-Host " README.md not found" -ForegroundColor Red
    exit 1
}

# Check if Infrastructure and Dashboard directories exist
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$parentPath = Split-Path -Parent $scriptPath
$infrastructurePath = Join-Path -Path $parentPath -ChildPath "Infrastructure"
$dashboardPath = Join-Path -Path $parentPath -ChildPath "Dashboard"

if (Test-Path -Path $infrastructurePath) {
    Write-Host " Infrastructure directory found at: $infrastructurePath" -ForegroundColor Green
} else {
    Write-Host " Infrastructure directory not found at: $infrastructurePath" -ForegroundColor Red
    exit 1
}

if (Test-Path -Path $dashboardPath) {
    Write-Host " Dashboard directory found at: $dashboardPath" -ForegroundColor Green
} else {
    Write-Host " Dashboard directory not found at: $dashboardPath" -ForegroundColor Red
    exit 1
}

Write-Host "All required files and directories are present." -ForegroundColor Green
Write-Host "Setup script is ready to use." -ForegroundColor Cyan
Write-Host ""
Write-Host "To run the setup wizard, use one of the following methods:" -ForegroundColor Yellow
Write-Host "1. Double-click on run-setup.bat" -ForegroundColor White
Write-Host "2. Run 'powershell -ExecutionPolicy Bypass -File setup.ps1' in a command prompt" -ForegroundColor White
Write-Host ""

# Define the base directory
$baseDir = "C:\Repos\MetaBundleTest"

# Define a placeholder token - in real usage, use a secure environment variable
$githubToken = "YOUR_GITHUB_TOKEN_HERE"

# Run setup.ps1 directly with arguments
Write-Host "Running setup.ps1 with command line arguments..." -ForegroundColor Yellow

# Run setup.ps1 with arguments
powershell -ExecutionPolicy Bypass -File "$PSScriptRoot\setup.ps1" -NonInteractive -GitHubToken $githubToken -GitHubOrg "MetaBundleAutomation" -CloneRepos "yes" -Environment "development" -TestMode "false" -BaseDirectory $baseDir -ApiDomain "api.metabundle.yourdomain.com" -DashboardDomain "dashboard.metabundle.yourdomain.com"

Write-Host ""
Write-Host "Test completed!" -ForegroundColor Cyan
