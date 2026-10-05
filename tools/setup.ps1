# Builds / repairs the portable runtime inside the app folder:
#   runtime\          private Python (embeddable distribution) + all packages
# Nothing is installed system-wide and no admin rights are needed.
param(
    [string]$PythonVersion = "3.13.16",
    [string]$Requirements = "requirements.txt",
    [string[]]$Packages = @()
)
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$Root = Split-Path -Parent $PSScriptRoot
$Rt = Join-Path $Root "runtime"
$Py = Join-Path $Rt "python.exe"
$Tmp = Join-Path $Rt "_tmp"
New-Item -ItemType Directory -Force $Tmp | Out-Null
$env:TEMP = $Tmp; $env:TMP = $Tmp
$env:PIP_DISABLE_PIP_VERSION_CHECK = "1"
$env:PYTHONNOUSERSITE = "1"

function Step($msg) { Write-Host ""; Write-Host "==> $msg" -ForegroundColor Cyan }

if (-not (Test-Path $Py)) {
    Step "Downloading portable Python $PythonVersion"
    $zip = Join-Path $Tmp "python.zip"
    $url = "https://www.python.org/ftp/python/$PythonVersion/python-$PythonVersion-embed-amd64.zip"
    Invoke-WebRequest -Uri $url -OutFile $zip -UseBasicParsing
    Expand-Archive -Path $zip -DestinationPath $Rt -Force
    Remove-Item $zip
    # Enable site-packages and let Python see the app folder.
    $pth = Get-ChildItem $Rt -Filter "python*._pth" | Select-Object -First 1
    $zipName = (Get-ChildItem $Rt -Filter "python*.zip" | Select-Object -First 1).Name
    Set-Content -Path $pth.FullName -Encoding ascii -Value @($zipName, ".", "Lib\site-packages", "..", "import site")
}

if (-not (Test-Path (Join-Path $Rt "Lib\site-packages\pip"))) {
    Step "Installing pip"
    $gp = Join-Path $Tmp "get-pip.py"
    Invoke-WebRequest -Uri "https://bootstrap.pypa.io/get-pip.py" -OutFile $gp -UseBasicParsing
    & $Py $gp --no-warn-script-location
    if ($LASTEXITCODE -ne 0) { throw "pip installation failed" }
}

$Packages = @($Packages | ForEach-Object { $_ -split "," } | Where-Object { $_ })
if ($Packages.Count -gt 0) {
    Step "Installing $($Packages -join ', ')"
    & $Py -m pip install --no-warn-script-location @Packages
} else {
    Step "Installing app packages (first time takes a few minutes)"
    & $Py -m pip install --no-warn-script-location -r (Join-Path $Root $Requirements)
}
if ($LASTEXITCODE -ne 0) { throw "Package installation failed (see messages above)" }

Remove-Item -Recurse -Force $Tmp -ErrorAction SilentlyContinue
Step "Done. Start the app with Dizcord.bat"
