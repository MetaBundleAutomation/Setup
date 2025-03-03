# MetaBundle Setup Script
# This script guides users through setting up the MetaBundle infrastructure and dashboard

# Function to display colored text
function Write-ColorText {
    param (
        [Parameter(Mandatory = $false)]
        [string]$Text = "",
        
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

# Function to set environment variables at both process and machine level
function Set-GlobalEnvironmentVariable {
    param (
        [Parameter(Mandatory = $true)]
        [string]$Name,
        
        [Parameter(Mandatory = $true)]
        [string]$Value
    )
    
    # Set for current process
    [Environment]::SetEnvironmentVariable($Name, $Value, [EnvironmentVariableTarget]::Process)
    
    # Set for machine (requires admin privileges)
    try {
        [Environment]::SetEnvironmentVariable($Name, $Value, [EnvironmentVariableTarget]::Machine)
        Write-ColorText "Set global environment variable: $Name" -ForegroundColor "Green"
    } catch {
        Write-ColorText "Warning: Could not set machine-level environment variable $Name. Running as administrator may be required." -ForegroundColor "Yellow"
        # Still set it for the user level as fallback
        [Environment]::SetEnvironmentVariable($Name, $Value, [EnvironmentVariableTarget]::User)
        Write-ColorText "Set user-level environment variable: $Name" -ForegroundColor "Green"
    }
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

# Get GitHub token from environment variable or ask user
$defaultGithubToken = if ($env:GITHUB_TOKEN) { $env:GITHUB_TOKEN } else { "" }
$githubToken = Get-ValidatedInput -Prompt "Enter your GitHub Personal Access Token" -Default $defaultGithubToken -Validator {
    param($token)
    return $token -ne ""
} -ErrorMessage "GitHub token cannot be empty."

# Get GitHub organization from environment variable or ask user
$defaultGithubOrg = if ($env:GITHUB_ORG) { $env:GITHUB_ORG } else { "MetaBundleAutomation" }
$githubOrg = Get-ValidatedInput -Prompt "Enter your GitHub organization name" -Default $defaultGithubOrg -Validator {
    param($org)
    return $org -ne ""
} -ErrorMessage "GitHub organization cannot be empty."

Write-ColorText "GitHub Token: $('*' * [Math]::Min($githubToken.Length, 10))..." -ForegroundColor "Yellow"
Write-ColorText "GitHub Organization: $githubOrg" -ForegroundColor "Yellow"
Write-ColorText ""

# Step 3: Docker Configuration
Write-ColorText "Step 3: Docker Configuration..." -ForegroundColor "Green"

# Get repository base directory from environment variable or ask user
$defaultRepoBaseDir = if ($env:REPO_BASE_DIR) { $env:REPO_BASE_DIR } else { "C:/repos/metabundle_repos" }
$repoBaseDir = Get-ValidatedInput -Prompt "Enter the repository base directory" -Default $defaultRepoBaseDir -Validator {
    param($dir)
    return $dir -ne ""
} -ErrorMessage "Repository base directory cannot be empty."

# Create the repository base directory if it doesn't exist
Ensure-Directory -Path $repoBaseDir

Write-ColorText "Repository Base Directory: $repoBaseDir" -ForegroundColor "Yellow"
Write-ColorText ""

# Step 4: API Configuration
Write-ColorText "Step 4: API Configuration..." -ForegroundColor "Green"

# Get API port from environment variable or ask user
$defaultApiPort = if ($env:API_PORT) { $env:API_PORT } else { "8000" }
$apiPort = Get-ValidatedInput -Prompt "Enter the API port" -Default $defaultApiPort -Validator {
    param($userInput)
    if ($userInput -match "^\d+$" -and [int]$userInput -gt 0 -and [int]$userInput -lt 65536) {
        return $true
    }
    return $false
} -ErrorMessage "Please enter a valid port number between 1 and 65535."

# Get WebSocket port from environment variable or ask user
$defaultWebsocketPort = if ($env:WEBSOCKET_PORT) { $env:WEBSOCKET_PORT } else { "8001" }
$websocketPort = Get-ValidatedInput -Prompt "Enter the WebSocket port" -Default $defaultWebsocketPort -Validator {
    param($userInput)
    if ($userInput -match "^\d+$" -and [int]$userInput -gt 0 -and [int]$userInput -lt 65536) {
        return $true
    }
    return $false
} -ErrorMessage "Please enter a valid port number between 1 and 65535."

Write-ColorText "API Port: $apiPort" -ForegroundColor "Yellow"
Write-ColorText "WebSocket Port: $websocketPort" -ForegroundColor "Yellow"
Write-ColorText ""

# Step 5: Environment Configuration
Write-ColorText "Step 5: Environment Configuration..." -ForegroundColor "Green"

# Get environment setting from environment variable or ask user
$defaultEnvironment = if ($env:ENVIRONMENT) { $env:ENVIRONMENT } else { "development" }
$environment = Get-ValidatedInput -Prompt "Enter the environment (development/production)" -Default $defaultEnvironment -Validator {
    param($env)
    return $env -eq "development" -or $env -eq "production"
} -ErrorMessage "Environment must be either 'development' or 'production'."

# Get test mode setting from environment variable or ask user
$defaultTestMode = if ($env:METABUNDLE_TEST_MODE) { $env:METABUNDLE_TEST_MODE.ToLower() } else { "false" }
$testMode = Get-ValidatedInput -Prompt "Run in test mode? (true/false)" -Default $defaultTestMode -Validator {
    param($mode)
    return $mode -eq "true" -or $mode -eq "false"
} -ErrorMessage "Test mode must be either 'true' or 'false'."

Write-ColorText "Environment: $environment" -ForegroundColor "Yellow"
Write-ColorText "Test Mode: $testMode" -ForegroundColor "Yellow"
Write-ColorText ""

# Step 6: Create Environment Files
Write-ColorText "Step 6: Setting environment variables..." -ForegroundColor "Green"

# Set global environment variables
Write-ColorText "The following environment variables will be set:" -ForegroundColor "Yellow"
Write-ColorText "GitHub Token: [Secured]" -ForegroundColor "Yellow"
Write-ColorText "GitHub Organization: $githubOrg" -ForegroundColor "Yellow"
Write-ColorText "Repository Base Directory: $repoBaseDir" -ForegroundColor "Yellow"
Write-ColorText "API Port: $apiPort" -ForegroundColor "Yellow"
Write-ColorText "WebSocket Port: $websocketPort" -ForegroundColor "Yellow"
Write-ColorText "Environment: $environment" -ForegroundColor "Yellow"
Write-ColorText "Test Mode: $testMode" -ForegroundColor "Yellow"
Write-ColorText ""

# Check if we're in the test environment and adjust ports to avoid conflicts
if ($infrastructurePath -like "*MetaBundleTest*") {
    # Use different ports for the test environment
    $apiPort = "9080"
    $websocketPort = "9081"
    
    # Update the global environment variables for the test environment
    Write-ColorText "Test environment detected, adjusting ports:" -ForegroundColor "Yellow"
    Write-ColorText "API Port: $apiPort" -ForegroundColor "Yellow"
    Write-ColorText "WebSocket Port: $websocketPort" -ForegroundColor "Yellow"
    Write-ColorText ""
}

# Set global environment variables
Write-ColorText "Setting global environment variables..." -ForegroundColor "Green"
Set-GlobalEnvironmentVariable -Name "GITHUB_TOKEN" -Value $githubToken
Set-GlobalEnvironmentVariable -Name "GITHUB_ORG" -Value $githubOrg
Set-GlobalEnvironmentVariable -Name "REPO_BASE_DIR" -Value $repoBaseDir
Set-GlobalEnvironmentVariable -Name "API_PORT" -Value $apiPort
Set-GlobalEnvironmentVariable -Name "WEBSOCKET_PORT" -Value $websocketPort
Set-GlobalEnvironmentVariable -Name "ENVIRONMENT" -Value $environment
Set-GlobalEnvironmentVariable -Name "METABUNDLE_TEST_MODE" -Value $testMode

# Step 7: Dashboard Configuration
Write-ColorText "Step 7: Dashboard Configuration..." -ForegroundColor "Green"

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

# Step 8: Create .env files
Write-ColorText "Step 8: Creating backup .env files for development environments..." -ForegroundColor "Green"

# Create backup .env files for development without setup script
# These are only used as fallbacks if the environment variables are not set
Write-ColorText "Creating backup .env files for development environments..." -ForegroundColor "Yellow"

# Create Infrastructure .env file (as backup only)
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
# Set to true to run in test mode (no Docker required)
METABUNDLE_TEST_MODE=$testMode

# Note: This file is only used as a fallback if the system environment variables are not set
# The primary configuration comes from the system environment variables set by setup.ps1
"@

$infrastructureEnvPath = Join-Path -Path $infrastructurePath -ChildPath ".env"
$infrastructureEnvContent | Out-File -FilePath $infrastructureEnvPath -Encoding utf8
Write-ColorText "Created Infrastructure backup .env file at: $infrastructureEnvPath" -ForegroundColor "Yellow"

# Create .env file for Dashboard (as backup only)
$dashboardEnvContent = @"
# Dashboard Configuration
INFRASTRUCTURE_API_URL=$infrastructureApiUrl
DEBUG_MODE=$debugMode
SECRET_KEY=$secretKey

# Note: This file is only used as a fallback if the system environment variables are not set
# The primary configuration comes from the system environment variables set by setup.ps1
"@

if ($infrastructurePath -like "*MetaBundleTest*") {
    # Add host binding to avoid socket permission issues
    $dashboardEnvContent += "`nFLASK_RUN_HOST=127.0.0.1"
}

$dashboardEnvPath = Join-Path -Path $dashboardPath -ChildPath ".env"
Set-Content -Path $dashboardEnvPath -Value $dashboardEnvContent
Write-ColorText "Created Dashboard backup .env file at: $dashboardEnvPath" -ForegroundColor "Yellow"
Write-ColorText ""

# Step 9: Summary and Next Steps
Write-ColorText "Step 9: Setup Complete!" -ForegroundColor "Green"
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
    param($userInput)
    $userInput = "$userInput".Trim().ToLower()
    if ($userInput -eq "yes" -or $userInput -eq "no" -or $userInput -eq "y" -or $userInput -eq "n") {
        return $true
    }
    return $false
} -ErrorMessage "Please enter 'yes', 'no', 'y', or 'n'."

# Convert y/n to yes/no for consistency
if ($startServices -eq "y") {
    $startServices = "yes"
} elseif ($startServices -eq "n") {
    $startServices = "no"
}

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
