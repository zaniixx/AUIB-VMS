<#
PowerShell helper to render PlantUML diagrams locally without Docker.
Usage:
  powershell -ExecutionPolicy Bypass -File .\tools\render_plantuml.ps1
  or
  .\tools\render_plantuml.ps1

This script will:
- Verify Java is installed
- Optionally download plantuml.jar into docs/diagrams if missing
- Warn if Graphviz (`dot`) is missing (recommended)
- Render all .puml files in docs/diagrams to SVG
#>

param(
    [switch]$ForceDownload
)

function Write-Ok($msg) { Write-Host "[OK]  $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err($msg) { Write-Host "[ERR]  $msg" -ForegroundColor Red }

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..')
$diagramsDir = Join-Path $repoRoot 'docs\diagrams'
$jarPath = Join-Path $diagramsDir 'plantuml.jar'

# Check Java
$java = Get-Command java -ErrorAction SilentlyContinue
if (-not $java) {
    Write-Err "Java not found. Please install Java (OpenJDK or Oracle) and ensure 'java' is on PATH."
    exit 1
}
Write-Ok "Java detected at $($java.Source)"

# Ensure diagrams dir exists
if (-not (Test-Path $diagramsDir)) {
    Write-Err "Diagrams directory not found: $diagramsDir"
    exit 1
}

# Download plantuml.jar if missing or forced
if (-not (Test-Path $jarPath) -or $ForceDownload) {
    Write-Host "plantuml.jar not found or force download requested. Downloading..."
    # Try a list of known hosts for plantuml.jar (GitHub releases and SourceForge mirrors)
    $urls = @(
        'https://github.com/plantuml/plantuml/releases/latest/download/plantuml.jar',
        'https://downloads.sourceforge.net/project/plantuml/plantuml.jar',
        'https://sourceforge.net/projects/plantuml/files/latest/download'
    )
    $downloaded = $false
    foreach ($u in $urls) {
        try {
            Write-Host "Attempting download from $u"
            Invoke-WebRequest -Uri $u -OutFile $jarPath -UseBasicParsing -ErrorAction Stop
            Write-Ok "Downloaded plantuml.jar to $jarPath from $u"
            $downloaded = $true
            break
        } catch {
            Write-Warn ("Failed to download from " + $u + ": " + $_.Exception.Message)
        }
    }
    if (-not $downloaded) {
        Write-Err "Failed to download plantuml.jar from known mirrors. Please download manually and place it at $jarPath"
        exit 1
    }
} else {
    Write-Ok "Found plantuml.jar at $jarPath"
}

# Check for Graphviz (dot)
$dot = Get-Command dot -ErrorAction SilentlyContinue
if (-not $dot) {
    Write-Warn "Graphviz 'dot' executable not found. Some diagrams (class relations, complex sequences) may not render correctly."
    Write-Warn "Install Graphviz and ensure 'dot' is on PATH: https://graphviz.org/download/"
} else {
    Write-Ok "Graphviz detected at $($dot.Source)"
}

# Run renderer
Push-Location $diagramsDir
try {
    Write-Host "Rendering .puml files to SVG in $diagramsDir"
    & java -jar $jarPath -tsvg *.puml
    if ($LASTEXITCODE -eq 0) {
        Write-Ok "Rendered PlantUML files successfully. SVG files are next to their .puml sources."
    } else {
        Write-Warn "PlantUML exited with code $LASTEXITCODE. Check output above for errors."
    }
} finally {
    Pop-Location
}

exit 0