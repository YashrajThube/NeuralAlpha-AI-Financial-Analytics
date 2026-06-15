param(
    [string]$MySqlServiceName = "MySQL80",
    [string]$MySqlBin = "C:\Program Files\MySQL\MySQL Server 8.0\bin",
    [string]$MySqlIni = "C:\ProgramData\MySQL\MySQL Server 8.0\my.ini",
    [string]$DbName = "neuralalpha",
    [string]$AppUser = "neuralalpha",
    [string]$AppPassword = "neuralalpha"
)

$ErrorActionPreference = "Stop"

if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw "Run this script in an elevated PowerShell (Run as Administrator)."
}

$mysqlExe = Join-Path $MySqlBin "mysql.exe"
$mysqldExe = Join-Path $MySqlBin "mysqld.exe"
if (-not (Test-Path $mysqlExe)) { throw "mysql.exe not found at $mysqlExe" }
if (-not (Test-Path $mysqldExe)) { throw "mysqld.exe not found at $mysqldExe" }
if (-not (Test-Path $MySqlIni)) { throw "my.ini not found at $MySqlIni" }

$resetSqlPath = Join-Path $env:TEMP "neuralalpha_mysql_reset.sql"
@"
CREATE DATABASE IF NOT EXISTS $DbName;
CREATE USER IF NOT EXISTS '$AppUser'@'localhost' IDENTIFIED BY '$AppPassword';
ALTER USER '$AppUser'@'localhost' IDENTIFIED BY '$AppPassword';
GRANT ALL PRIVILEGES ON $DbName.* TO '$AppUser'@'localhost';
FLUSH PRIVILEGES;
"@ | Set-Content -Path $resetSqlPath -Encoding ASCII

Write-Host "Stopping service $MySqlServiceName ..."
Stop-Service -Name $MySqlServiceName -Force

Write-Host "Starting mysqld with one-time init-file ..."
$proc = Start-Process -FilePath $mysqldExe -ArgumentList @(
    "--defaults-file=$MySqlIni",
    "--init-file=$resetSqlPath",
    "--console"
) -PassThru -WindowStyle Hidden

Start-Sleep -Seconds 5
if (-not $proc.HasExited) {
    Write-Host "Stopping temporary mysqld process ..."
    Stop-Process -Id $proc.Id -Force
}

Write-Host "Starting service $MySqlServiceName ..."
Start-Service -Name $MySqlServiceName

Write-Host "Verifying app login ..."
& $mysqlExe -h localhost -P 3306 -u$AppUser -p$AppPassword -e "SELECT USER(), CURRENT_USER(); SHOW DATABASES LIKE '$DbName';"

Write-Host "MySQL app user repair completed."
