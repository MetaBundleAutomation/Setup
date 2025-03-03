# Initialize a new Git repository for the Setup components

Write-Host "Initializing new Git repository for MetaBundle Setup..." -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host ""

# Check if git is installed
try {
    $gitVersion = git --version
    Write-Host "Git detected: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "Error: Git is not installed or not in PATH. Please install Git." -ForegroundColor Red
    exit 1
}

# Initialize git repository
Write-Host "Initializing Git repository..." -ForegroundColor Yellow
git init

# Add all setup files
Write-Host "Adding setup files to repository..." -ForegroundColor Yellow
git add .gitignore
git add .gitattributes
git add README.md
git add docker-compose.yml
git add run-docker-with-env.ps1
git add run-docker.ps1
git add stop-docker.ps1
git add run-setup.bat
git add Setup/

# Commit the changes
Write-Host "Committing initial setup files..." -ForegroundColor Yellow
git commit -m "Initial commit of MetaBundle Setup repository"

Write-Host ""
Write-Host "Git repository initialized successfully!" -ForegroundColor Green
Write-Host "You can now push this repository to your Git server." -ForegroundColor Cyan
Write-Host ""
Write-Host "Example commands:" -ForegroundColor Yellow
Write-Host "git remote add origin https://github.com/yourusername/metabundle-setup.git" -ForegroundColor Yellow
Write-Host "git push -u origin main" -ForegroundColor Yellow
Write-Host ""
