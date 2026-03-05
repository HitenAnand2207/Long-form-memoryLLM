param(
    [string]$OutputDirectory = "."
)

# Create submission zip file excluding virtual environments and caches
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$zipFileName = "long-form-memory_submission_$timestamp.zip"
$zipFilePath = Join-Path -Path (Resolve-Path $OutputDirectory) -ChildPath $zipFileName
$tempDir = Join-Path -Path $env:TEMP -ChildPath "temp_submission_$timestamp"

Write-Host "Creating submission package..." -ForegroundColor Cyan
Write-Host "Zip file: $zipFilePath" -ForegroundColor Green

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
    "create_submission_zip.ps1",
    ".gitignore"
)

$excludeDirectories = @("__pycache__", ".pytest_cache", ".venv", "venv", ".git")

New-Item -ItemType Directory -Path $tempDir -Force | Out-Null

try {
    # Copy files to temp directory
    foreach ($item in $includeItems) {
        if (-not (Test-Path $item)) {
            Write-Host "Skipping missing item: $item" -ForegroundColor DarkYellow
            continue
        }

        Write-Host "Adding: $item" -ForegroundColor Yellow
        $srcItem = Get-Item $item

        if ($srcItem -is [System.IO.DirectoryInfo]) {
            Copy-Item -Path $item -Destination $tempDir -Recurse -Force
        } else {
            Copy-Item -Path $item -Destination $tempDir -Force
        }
    }

    # Remove excluded directories from copied content
    foreach ($excludedName in $excludeDirectories) {
        Get-ChildItem -Path $tempDir -Recurse -Directory -Force |
            Where-Object { $_.Name -eq $excludedName } |
            Remove-Item -Recurse -Force
    }

    # Create data directory structure (empty, for documentation)
    Write-Host "Creating data directory structure..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path (Join-Path $tempDir "data\embeddings") -Force | Out-Null
    "# This directory is auto-created on first run" | Out-File -FilePath (Join-Path $tempDir "data\README.txt") -Encoding UTF8

    # Compress to zip
    Write-Host "Compressing files..." -ForegroundColor Cyan
    if (Test-Path $zipFilePath) {
        Remove-Item -Path $zipFilePath -Force
    }
    Compress-Archive -Path (Join-Path $tempDir "*") -DestinationPath $zipFilePath -Force
}
finally {
    if (Test-Path $tempDir) {
        Remove-Item -Path $tempDir -Recurse -Force
    }
}

# Check file size
$zipSize = (Get-Item $zipFilePath).Length
$zipSizeMB = [math]::Round($zipSize / 1MB, 2)

Write-Host ""
Write-Host "Zip file created successfully!" -ForegroundColor Green
Write-Host "Location: $zipFilePath" -ForegroundColor Green
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
