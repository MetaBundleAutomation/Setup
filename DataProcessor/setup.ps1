# DataProcessor Setup Script
# This script helps set up the DataProcessor environment

# Create logs directory if it doesn't exist
if (-not (Test-Path -Path ".\logs")) {
    New-Item -Path ".\logs" -ItemType Directory
    Write-Host "Created logs directory" -ForegroundColor Green
}

# Create .env file from example if it doesn't exist
if (-not (Test-Path -Path ".\.env")) {
    Copy-Item -Path ".\.env.example" -Destination ".\.env"
    Write-Host "Created .env file from .env.example" -ForegroundColor Green
    
    # Check if environment variables are set
    $apiKey = [System.Environment]::GetEnvironmentVariable("GOOGLE_SEARCH_API_KEY", "User")
    $engineId = [System.Environment]::GetEnvironmentVariable("GOOGLE_SEARCH_ENGINE_ID", "User")
    
    if ([string]::IsNullOrEmpty($apiKey) -or [string]::IsNullOrEmpty($engineId)) {
        Write-Host "WARNING: One or more required environment variables are not set" -ForegroundColor Yellow
        Write-Host "Please set the following environment variables or update the .env file manually:" -ForegroundColor Yellow
        Write-Host "  GOOGLE_SEARCH_API_KEY" -ForegroundColor Yellow
        Write-Host "  GOOGLE_SEARCH_ENGINE_ID" -ForegroundColor Yellow
        
        $setNow = Read-Host "Would you like to set these environment variables now? (y/n)"
        if ($setNow -eq "y") {
            $newApiKey = Read-Host "Enter your Google Search API Key"
            $newEngineId = Read-Host "Enter your Google Search Engine ID"
            
            [System.Environment]::SetEnvironmentVariable("GOOGLE_SEARCH_API_KEY", $newApiKey, "User")
            [System.Environment]::SetEnvironmentVariable("GOOGLE_SEARCH_ENGINE_ID", $newEngineId, "User")
            
            Write-Host "Environment variables set successfully" -ForegroundColor Green
        }
    } else {
        Write-Host "Environment variables already configured" -ForegroundColor Green
    }
} else {
    Write-Host ".env file already exists" -ForegroundColor Green
}

# Install Python dependencies
Write-Host "Installing Python dependencies..." -ForegroundColor Cyan
pip install -r requirements.txt

Write-Host "`nSetup complete!" -ForegroundColor Green
Write-Host "You can now run the DataProcessor with: python src\main.py"
