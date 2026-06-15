$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$backendRoot = Join-Path $repoRoot 'backend'
$frontendRoot = Join-Path $repoRoot 'frontend'
$pythonExe = Join-Path $repoRoot '.venv\Scripts\python.exe'

function Invoke-CommandAndCapture {
    param(
        [string]$Name,
        [string]$Command,
        [string[]]$Arguments,
        [string]$WorkingDirectory
    )

    Push-Location $WorkingDirectory
    try {
        $previousPreference = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'
        $output = & $Command @Arguments 2>&1
        $exitCode = $LASTEXITCODE
        $ErrorActionPreference = $previousPreference
        return [pscustomobject]@{
            Name = $Name
            ExitCode = $exitCode
            Output = ($output | Out-String).Trim()
            Passed = ($exitCode -eq 0)
        }
    }
    finally {
        $ErrorActionPreference = 'Stop'
        Pop-Location
    }
}

function Wait-ForUrl {
    param(
        [string]$Url,
        [int]$TimeoutSeconds = 60
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        try {
            $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 3
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 300) {
                return $true
            }
        }
        catch {
        }
    }

    return $false
}

Write-Host '==> Resetting occupied ports'
& (Join-Path $repoRoot 'scripts\prestart_ports.ps1') | Out-Null

$env:API_KEY_REQUIRED = 'false'
$env:PUBLIC_API_KEY = 'dev-full-run-key'
$env:API_KEY_ALLOWED_IPS = '127.0.0.1'
$env:ENFORCE_REAL_MODELS = 'true'
$env:MODEL_WARMUP_ON_STARTUP = 'false'

$backendOutLog = Join-Path $repoRoot 'backend-full-run.out.log'
$backendErrLog = Join-Path $repoRoot 'backend-full-run.err.log'
$frontendOutLog = Join-Path $repoRoot 'frontend-full-run.out.log'
$frontendErrLog = Join-Path $repoRoot 'frontend-full-run.err.log'
Remove-Item $backendOutLog, $backendErrLog, $frontendOutLog, $frontendErrLog -ErrorAction SilentlyContinue

Write-Host '==> Starting backend'
$backendProc = Start-Process -FilePath $pythonExe -WorkingDirectory $backendRoot -ArgumentList @('-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000') -RedirectStandardOutput $backendOutLog -RedirectStandardError $backendErrLog -PassThru

Write-Host '==> Starting frontend'
$frontendProc = Start-Process -FilePath 'npm' -WorkingDirectory $frontendRoot -ArgumentList @('run', 'dev', '--', '--host', '127.0.0.1', '--port', '5173') -RedirectStandardOutput $frontendOutLog -RedirectStandardError $frontendErrLog -PassThru

$healthOk = Wait-ForUrl -Url 'http://127.0.0.1:8000/health' -TimeoutSeconds 180
$frontendOk = Wait-ForUrl -Url 'http://127.0.0.1:5173/' -TimeoutSeconds 180

$results = @()

if ($healthOk -and $frontendOk) {
    Write-Host '==> Running deep QA'
    $results += Invoke-CommandAndCapture -Name 'deep_system_qa' -Command $pythonExe -Arguments @((Join-Path 'scripts' 'deep_system_qa.py')) -WorkingDirectory $backendRoot

    Write-Host '==> Running production validator'
    $results += Invoke-CommandAndCapture -Name 'validate_production_system' -Command $pythonExe -Arguments @((Join-Path 'scripts' 'validate_production_system.py')) -WorkingDirectory $backendRoot

    Write-Host '==> Running smoke tests'
    $results += Invoke-CommandAndCapture -Name 'smoke_test_stack' -Command $pythonExe -Arguments @((Join-Path 'scripts' 'smoke_test_stack.py')) -WorkingDirectory $backendRoot
}
else {
    $results += [pscustomobject]@{
        Name = 'startup'
        ExitCode = 1
        Passed = $false
        Output = "Backend ready: $healthOk; Frontend ready: $frontendOk"
    }
}

$passed = $results | Where-Object { $_.Passed } | Measure-Object | Select-Object -ExpandProperty Count
$failed = $results | Where-Object { -not $_.Passed } | Measure-Object | Select-Object -ExpandProperty Count

$summary = [pscustomobject]@{
    backend_pid = $backendProc.Id
    frontend_pid = $frontendProc.Id
    backend_ready = $healthOk
    frontend_ready = $frontendOk
    passed = $passed
    failed = $failed
    checks = $results
    status = if ($failed -eq 0 -and $healthOk -and $frontendOk) { 'pass' } else { 'fail' }
}

try {
    $summary | ConvertTo-Json -Depth 8
}
finally {
    if (-not $backendProc.HasExited) { Stop-Process -Id $backendProc.Id -Force -ErrorAction SilentlyContinue }
    if (-not $frontendProc.HasExited) { Stop-Process -Id $frontendProc.Id -Force -ErrorAction SilentlyContinue }
}

if (-not $healthOk) {
    Write-Host 'Backend did not become ready within the timeout. Check backend-full-run.err.log for startup errors.'
}
if (-not $frontendOk) {
    Write-Host 'Frontend did not become ready within the timeout. Check frontend-full-run.err.log for startup errors.'
}
