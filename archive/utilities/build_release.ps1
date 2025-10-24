# UDS3 v1.4.0 Release Build Script
# Purpose: Build and package UDS3 for distribution

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "UDS3 v1.4.0 Release Build" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if we're in the correct directory
if (-not (Test-Path "pyproject.toml")) {
    Write-Host "❌ Error: pyproject.toml not found!" -ForegroundColor Red
    Write-Host "Please run this script from the UDS3 root directory" -ForegroundColor Yellow
    exit 1
}

# Clean previous builds
Write-Host "🧹 Cleaning previous builds..." -ForegroundColor Yellow
if (Test-Path "dist") { Remove-Item -Recurse -Force dist }
if (Test-Path "build") { Remove-Item -Recurse -Force build }
if (Test-Path "*.egg-info") { Remove-Item -Recurse -Force *.egg-info }
Write-Host "✅ Clean complete" -ForegroundColor Green
Write-Host ""

# Upgrade build tools
Write-Host "📦 Upgrading build tools..." -ForegroundColor Yellow
python -m pip install --upgrade pip setuptools wheel build
Write-Host "✅ Build tools upgraded" -ForegroundColor Green
Write-Host ""

# Build package
Write-Host "🔨 Building UDS3 package..." -ForegroundColor Yellow
python -m build
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Build failed!" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Build successful" -ForegroundColor Green
Write-Host ""

# List built files
Write-Host "📁 Built files:" -ForegroundColor Cyan
Get-ChildItem dist | ForEach-Object {
    $size = "{0:N2} KB" -f ($_.Length / 1KB)
    Write-Host "  - $($_.Name) ($size)" -ForegroundColor White
}
Write-Host ""

# Verify package contents
Write-Host "🔍 Verifying package contents..." -ForegroundColor Yellow
$tarball = Get-ChildItem dist/*.tar.gz | Select-Object -First 1
if ($tarball) {
    Write-Host "  Checking $($tarball.Name)..." -ForegroundColor Gray
    # Note: tar is available in Windows 10+ by default
    tar -tzf $tarball.FullName | Select-String -Pattern "uds3|search" | ForEach-Object {
        Write-Host "    $_" -ForegroundColor DarkGray
    }
}
Write-Host "✅ Package verification complete" -ForegroundColor Green
Write-Host ""

# Test installation in virtual environment (optional)
Write-Host "🧪 Test installation (optional)..." -ForegroundColor Yellow
Write-Host "To test the package, run:" -ForegroundColor Cyan
Write-Host "  python -m venv test_env" -ForegroundColor White
Write-Host "  .\test_env\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "  pip install dist\uds3-1.4.0-py3-none-any.whl" -ForegroundColor White
Write-Host "  python -c 'from uds3 import __version__; print(__version__)'" -ForegroundColor White
Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✅ UDS3 v1.4.0 Build Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Test installation (see commands above)" -ForegroundColor White
Write-Host "2. Create git tag: git tag v1.4.0" -ForegroundColor White
Write-Host "3. Push tag: git push origin v1.4.0" -ForegroundColor White
Write-Host "4. Create GitHub release with dist/ files" -ForegroundColor White
Write-Host ""
