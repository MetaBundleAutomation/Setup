Write-Host "Stopping MetaBundle Docker services..." -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Check if containers are running
$containers = docker ps --filter "name=metabundle" --format "{{.Names}}"
if (-not $containers) {
    Write-Host "No MetaBundle containers are currently running." -ForegroundColor Yellow
    exit 0
}

Write-Host "Stopping the following containers:" -ForegroundColor Yellow
foreach ($container in $containers -split "`n") {
    if ($container) {
        Write-Host "- $container" -ForegroundColor Yellow
    }
}
Write-Host ""

# Stop the containers
docker-compose down

Write-Host ""
Write-Host "All MetaBundle services have been stopped." -ForegroundColor Green
Write-Host "To start them again, run: .\run-docker-with-env.ps1" -ForegroundColor Cyan
