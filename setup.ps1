# MetaBundle Setup Script
# This script guides users through setting up the MetaBundle infrastructure and dashboard

# Function to display colored text
function Write-ColorText {
    param (
        [Parameter(Mandatory = $true)]
        [string]$Text,
        
        [Parameter(Mandatory = $false)]
        [string]$ForegroundColor = "White"
    )
    
    Write-Host $Text -ForegroundColor $ForegroundColor
}

# Function to create a directory if it doesn't exist
function Ensure-Directory {
    param (
        [Parameter(Mandatory = $true)]
        [string]$Path
    )
    
    if (-not (Test-Path -Path $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
        Write-ColorText "Created directory: $Path" -ForegroundColor "Yellow"
    }
}

# Function to get user input with validation
function Get-ValidatedInput {
    param (
        [Parameter(Mandatory = $true)]
        [string]$Prompt,
        
        [Parameter(Mandatory = $false)]
        [string]$Default = "",
        
        [Parameter(Mandatory = $false)]
        [scriptblock]$Validator = { $true },
        
        [Parameter(Mandatory = $false)]
        [string]$ErrorMessage = "Invalid input. Please try again."
    )
    
    $promptText = $Prompt
    if ($Default -ne "") {
        $promptText += " (default: $Default)"
    }
    $promptText += ": "
    
    while ($true) {
        $input = Read-Host -Prompt $promptText
        
        if ($input -eq "" -and $Default -ne "") {
            $input = $Default
        }
        
        if (& $Validator $input) {
            return $input
        }
        
        Write-ColorText $ErrorMessage -ForegroundColor "Red"
    }
}

# Function to generate a random secret key
function Get-RandomSecretKey {
    $bytes = New-Object Byte[] 32
    $rand = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    $rand.GetBytes($bytes)
    $rand.Dispose()
    return [Convert]::ToBase64String($bytes)
}

# Clear the console and display welcome message
Clear-Host
Write-ColorText "===============================================" -ForegroundColor "Cyan"
Write-ColorText "       MetaBundle Setup Wizard" -ForegroundColor "Cyan"
Write-ColorText "===============================================" -ForegroundColor "Cyan"
Write-ColorText "This wizard will guide you through setting up the MetaBundle infrastructure and dashboard." -ForegroundColor "White"
Write-ColorText "You will need to provide some information to configure the environment." -ForegroundColor "White"
Write-ColorText ""

# Step 1: Locate the Infrastructure and Dashboard directories
Write-ColorText "Step 1: Locating Infrastructure and Dashboard directories..." -ForegroundColor "Green"

# Define default paths
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$parentPath = Split-Path -Parent $scriptPath
$defaultInfrastructurePath = Join-Path -Path $parentPath -ChildPath "Infrastructure"
$defaultDashboardPath = Join-Path -Path $parentPath -ChildPath "Dashboard"

# Ask for Infrastructure path
$infrastructurePath = Get-ValidatedInput -Prompt "Enter the path to the Infrastructure directory" -Default $defaultInfrastructurePath -Validator {
    param($path)
    if (-not (Test-Path -Path $path)) {
        return $false
    }
    return $true
} -ErrorMessage "Directory does not exist. Please enter a valid path."

# Ask for Dashboard path
$dashboardPath = Get-ValidatedInput -Prompt "Enter the path to the Dashboard directory" -Default $defaultDashboardPath -Validator {
    param($path)
    if (-not (Test-Path -Path $path)) {
        return $false
    }
    return $true
} -ErrorMessage "Directory does not exist. Please enter a valid path."

Write-ColorText "Infrastructure directory: $infrastructurePath" -ForegroundColor "Yellow"
Write-ColorText "Dashboard directory: $dashboardPath" -ForegroundColor "Yellow"
Write-ColorText ""

# Step 2: GitHub Configuration
Write-ColorText "Step 2: GitHub Configuration..." -ForegroundColor "Green"
Write-ColorText "You need a GitHub Personal Access Token with 'repo' and 'read:org' permissions." -ForegroundColor "White"
Write-ColorText "If you don't have one, create it at: https://github.com/settings/tokens" -ForegroundColor "White"

$githubToken = Get-ValidatedInput -Prompt "Enter your GitHub Personal Access Token" -Validator {
    param($token)
    if ($token -eq "") {
        return $false
    }
    return $true
} -ErrorMessage "GitHub token cannot be empty."

$githubOrg = Get-ValidatedInput -Prompt "Enter your GitHub Organization name" -Default "MetaBundleAutomation"

Write-ColorText "GitHub Token: [Hidden for security]" -ForegroundColor "Yellow"
Write-ColorText "GitHub Organization: $githubOrg" -ForegroundColor "Yellow"
Write-ColorText ""

# Step 3: Docker Configuration
Write-ColorText "Step 3: Docker Configuration..." -ForegroundColor "Green"

$repoBaseDir = Get-ValidatedInput -Prompt "Enter the base directory for repositories" -Default "C:/repos/metabundle_repos"

# Create the repository base directory if it doesn't exist
Ensure-Directory -Path $repoBaseDir

Write-ColorText "Repository Base Directory: $repoBaseDir" -ForegroundColor "Yellow"
Write-ColorText ""

# Step 4: API Configuration
Write-ColorText "Step 4: API Configuration..." -ForegroundColor "Green"

$apiPort = Get-ValidatedInput -Prompt "Enter the API port" -Default "8080" -Validator {
    param($port)
    if ($port -match "^\d+$" -and [int]$port -gt 0 -and [int]$port -lt 65536) {
        return $true
    }
    return $false
} -ErrorMessage "Port must be a number between 1 and 65535."

$websocketPort = Get-ValidatedInput -Prompt "Enter the WebSocket port" -Default "8081" -Validator {
    param($port)
    if ($port -match "^\d+$" -and [int]$port -gt 0 -and [int]$port -lt 65536) {
        return $true
    }
    return $false
} -ErrorMessage "Port must be a number between 1 and 65535."

Write-ColorText "API Port: $apiPort" -ForegroundColor "Yellow"
Write-ColorText "WebSocket Port: $websocketPort" -ForegroundColor "Yellow"
Write-ColorText ""

# Step 5: Environment Configuration
Write-ColorText "Step 5: Environment Configuration..." -ForegroundColor "Green"

$environment = Get-ValidatedInput -Prompt "Enter the environment (development, production)" -Default "development" -Validator {
    param($env)
    if ($env -eq "development" -or $env -eq "production") {
        return $true
    }
    return $false
} -ErrorMessage "Environment must be either 'development' or 'production'."

$testMode = Get-ValidatedInput -Prompt "Run in test mode? (true/false)" -Default "true" -Validator {
    param($mode)
    if ($mode -eq "true" -or $mode -eq "false") {
        return $true
    }
    return $false
} -ErrorMessage "Test mode must be either 'true' or 'false'."

Write-ColorText "Environment: $environment" -ForegroundColor "Yellow"
Write-ColorText "Test Mode: $testMode" -ForegroundColor "Yellow"
Write-ColorText ""

# Step 6: Dashboard Configuration
Write-ColorText "Step 6: Dashboard Configuration..." -ForegroundColor "Green"

$infrastructureApiUrl = "http://localhost:$apiPort"
$debugMode = Get-ValidatedInput -Prompt "Run Dashboard in debug mode? (true/false)" -Default "true" -Validator {
    param($mode)
    if ($mode -eq "true" -or $mode -eq "false") {
        return $true
    }
    return $false
} -ErrorMessage "Debug mode must be either 'true' or 'false'."

$secretKey = Get-RandomSecretKey
Write-ColorText "Infrastructure API URL: $infrastructureApiUrl" -ForegroundColor "Yellow"
Write-ColorText "Debug Mode: $debugMode" -ForegroundColor "Yellow"
Write-ColorText "Secret Key: [Generated]" -ForegroundColor "Yellow"
Write-ColorText ""

# Step 7: Create .env files
Write-ColorText "Step 7: Creating .env files..." -ForegroundColor "Green"

# Create Infrastructure .env file
$infrastructureEnvContent = @"
# GitHub Configuration
GITHUB_TOKEN=$githubToken
GITHUB_ORG=$githubOrg

# Docker Configuration
REPO_BASE_DIR=$repoBaseDir

# API Configuration
API_PORT=$apiPort
WEBSOCKET_PORT=$websocketPort

# Environment
ENVIRONMENT=$environment
METABUNDLE_TEST_MODE=$testMode
"@

$infrastructureEnvPath = Join-Path -Path $infrastructurePath -ChildPath ".env"
$infrastructureEnvContent | Out-File -FilePath $infrastructureEnvPath -Encoding utf8
Write-ColorText "Created Infrastructure .env file at: $infrastructureEnvPath" -ForegroundColor "Yellow"

# Create Dashboard .env file
$dashboardEnvContent = @"
# Dashboard Configuration
INFRASTRUCTURE_API_URL=$infrastructureApiUrl
DEBUG_MODE=$debugMode
SECRET_KEY=$secretKey
"@

$dashboardEnvPath = Join-Path -Path $dashboardPath -ChildPath ".env"
$dashboardEnvContent | Out-File -FilePath $dashboardEnvPath -Encoding utf8
Write-ColorText "Created Dashboard .env file at: $dashboardEnvPath" -ForegroundColor "Yellow"
Write-ColorText ""

# Step 8: Summary and Next Steps
Write-ColorText "Step 8: Setup Complete!" -ForegroundColor "Green"
Write-ColorText "Configuration files have been created successfully." -ForegroundColor "White"
Write-ColorText ""
Write-ColorText "Next Steps:" -ForegroundColor "Cyan"
Write-ColorText "1. Start the Infrastructure Backend:" -ForegroundColor "White"
Write-ColorText "   cd '$infrastructurePath'" -ForegroundColor "Yellow"
Write-ColorText "   .\start-backend.ps1 -TestMode" -ForegroundColor "Yellow"
Write-ColorText ""
Write-ColorText "2. Start the Dashboard Frontend:" -ForegroundColor "White"
Write-ColorText "   cd '$dashboardPath'" -ForegroundColor "Yellow"
Write-ColorText "   python src/app.py" -ForegroundColor "Yellow"
Write-ColorText ""
Write-ColorText "3. Access the Dashboard:" -ForegroundColor "White"
Write-ColorText "   http://localhost:5050" -ForegroundColor "Yellow"
Write-ColorText ""
Write-ColorText "Thank you for setting up MetaBundle!" -ForegroundColor "Cyan"
Write-ColorText "===============================================" -ForegroundColor "Cyan"

# Ask if user wants to start the services now
$startServices = Get-ValidatedInput -Prompt "Do you want to start the services now? (yes/no)" -Default "yes" -Validator {
    param($input)
    if ($input -eq "yes" -or $input -eq "no") {
        return $true
    }
    return $false
} -ErrorMessage "Please enter 'yes' or 'no'."

if ($startServices -eq "yes") {
    Write-ColorText "Starting Infrastructure Backend..." -ForegroundColor "Green"
    $currentLocation = Get-Location
    Set-Location -Path $infrastructurePath
    Start-Process powershell -ArgumentList "-NoExit", "-Command", ".\start-backend.ps1 -TestMode"
    
    Write-ColorText "Starting Dashboard Frontend..." -ForegroundColor "Green"
    Set-Location -Path $dashboardPath
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "python src/app.py"
    
    # Open the dashboard in the default browser
    Start-Process "http://localhost:5050"
    
    Set-Location -Path $currentLocation
    Write-ColorText "Services started! The dashboard should open in your browser." -ForegroundColor "Green"
}

Write-ColorText "Setup script completed." -ForegroundColor "Cyan"
