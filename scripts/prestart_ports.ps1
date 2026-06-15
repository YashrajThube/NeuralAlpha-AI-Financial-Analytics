Param(
  [int[]]$Ports = @(8000, 5173)
)

$stopped = @()

foreach ($port in $Ports) {
  $listeners = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
  foreach ($listener in $listeners) {
    $owningProcess = $listener.OwningProcess
    if ($owningProcess -and $owningProcess -ne 0) {
      try {
        Stop-Process -Id $owningProcess -Force -ErrorAction Stop
        $stopped += [PSCustomObject]@{ Port = $port; ProcessId = $owningProcess; Status = 'stopped' }
      } catch {
        $stopped += [PSCustomObject]@{ Port = $port; ProcessId = $owningProcess; Status = 'failed' }
      }
    }
  }
}

Start-Sleep -Milliseconds 250

$inUseAfter = @()
foreach ($port in $Ports) {
  $listeners = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
  if ($listeners) {
    $inUseAfter += $port
  }
}

[PSCustomObject]@{
  PortsChecked = $Ports
  ProcessesStopped = $stopped
  PortsStillInUse = $inUseAfter
} | ConvertTo-Json -Depth 5
