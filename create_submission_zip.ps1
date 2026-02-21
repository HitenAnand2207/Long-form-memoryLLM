# Create submission zip file excluding venv and other unnecessary files
$ErrorActionPreference = "Stop"

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$zipFileName = "long-form-memory_submission_$timestamp.zip"
$tempDir = "temp_submission_$timestamp"

Write-Host "Creating submission package..." -ForegroundColor Cyan
Write-Host "Zip file: $zipFileName" -ForegroundColor Green

# Create temporary directory
New-Item -ItemType Directory -Path $tempDir -Force | Out-Null

# Define files and directories to include
$includeItems = @(
    "src",
    "tests",
    "diagnose.py",
    "QUICKSTART.md",
    "README.md",
    "requirements-minimal.txt",
    "requirements.txt",
    "setup.bat",
    "setup.sh",
    "web_interface.html",
    ".gitignore"
)

# Copy files to temp directory
foreach ($item in $includeItems) {
    if (Test-Path $item) {
        Write-Host "Adding: $item" -ForegroundColor Yellow
        if ((Get-Item $item) -is [System.IO.DirectoryInfo]) {
            # Copy directory, excluding __pycache__
            Copy-Item -Path $item -Destination $tempDir -Recurse -Force -Exclude "__pycache__"
            # Remove any __pycache__ directories that were copied
            Get-ChildItem -Path "$tempDir\$item" -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
        } else {
            # Copy file
            Copy-Item -Path $item -Destination $tempDir -Force
        }
    }
}

# Create data directory structure (empty, for documentation)
Write-Host "Creating data directory structure..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path "$tempDir\data\embeddings" -Force | Out-Null
"# This directory is auto-created on first run" | Out-File -FilePath "$tempDir\data\README.txt" -Encoding UTF8

# Compress to zip
Write-Host "Compressing files..." -ForegroundColor Cyan
Compress-Archive -Path "$tempDir\*" -DestinationPath $zipFileName -Force

# Clean up temp directory
Remove-Item -Path $tempDir -Recurse -Force

# Check file size
$zipSize = (Get-Item $zipFileName).Length
$zipSizeMB = [math]::Round($zipSize / 1MB, 2)

Write-Host ""
Write-Host "Zip file created successfully!" -ForegroundColor Green
Write-Host "Location: $(Get-Location)\$zipFileName" -ForegroundColor Green
Write-Host "Size: $zipSizeMB MB" -ForegroundColor Green

if ($zipSizeMB -gt 50) {
    Write-Host ""
    Write-Host "WARNING: File size exceeds 50 MB limit!" -ForegroundColor Red
} else {
    Write-Host ""
    Write-Host "File size is within 50 MB limit" -ForegroundColor Green
}

Write-Host ""
Write-Host "Zip file ready for submission!" -ForegroundColor Cyan
