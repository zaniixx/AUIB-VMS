param(
    [switch]$Install = $false,
    [switch]$Seed = $false
)

# A simple setup script for Windows PowerShell
# Usage examples:
#  1) Create venv and install requirements: .\setup.ps1 -Install
#  2) Create venv, install, and seed DB: .\setup.ps1 -Install -Seed
#  3) Dry-run (no installs): .\setup.ps1

$cwd = Split-Path -Parent $MyInvocation.MyCommand.Definition
Write-Host "Working in $cwd"

$venvPath = Join-Path $cwd '.venv'
if (-not (Test-Path $venvPath)) {
    Write-Host "Creating virtual environment at $venvPath"
    python -m venv $venvPath
} else {
    Write-Host "Virtual environment already exists at $venvPath"
}

$activate = Join-Path $venvPath 'Scripts\Activate.ps1'

$venvPython = Join-Path $venvPath 'Scripts\python.exe'
$venvPip = Join-Path $venvPath 'Scripts\pip.exe'

if ($Install) {
    Write-Host "Installing requirements into venv ($venvPath) ..."
    if (-not (Test-Path $venvPython)) {
        Write-Host "Warning: venv python not found at $venvPython. Ensure venv was created successfully."
    } else {
        & $venvPip install -r (Join-Path $cwd 'requirements.txt')
    }
} else {
    Write-Host "Install flag not set. Skipping pip install. Use -Install to install dependencies."
}

if ($Seed) {
    Write-Host "Seeding database (imports vms.create_app and runs seed)."
    $env:PYTHONPATH = $cwd
    $temp = Join-Path $env:TEMP "vms_seed_$(Get-Random).py"
    $py = @'
from vms import create_app
app = create_app()
with app.app_context():
    from vms.models import seed_sample_users
    seed_sample_users()
    print('Seeded sample users')
'@
    Set-Content -Path $temp -Value $py -NoNewline
    try {
        if (Test-Path $venvPython) {
            & $venvPython $temp
        } else {
            python $temp
        }
    } finally {
        Remove-Item $temp -ErrorAction SilentlyContinue
    }
} else {
    Write-Host "Seed flag not set. Skipping DB seed. Use -Seed to seed demo users."
}

Write-Host 'Setup script finished. To activate the venv: `. .\.venv\Scripts\Activate.ps1`'
