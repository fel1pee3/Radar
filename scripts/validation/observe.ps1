param([string]$Config = '.local/etapa08/webcam.yaml')
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '../activate.ps1')
$taskRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
Set-Location -LiteralPath $taskRoot
if ($Config -notmatch '^\.local/[A-Za-z0-9_./-]+\.yaml$' -or $Config.Contains('..')) { throw 'Use caminho relativo simples dentro de .local.' }
if (-not (Test-Path -LiteralPath $Config)) { throw 'Prepare a configuracao privada antes de iniciar.' }
$taskCameraId = (& uv run --project services/edge --frozen python -c 'import sys; from radar_edge.config import load_config; print(load_config(sys.argv[1]).cameraId)' $Config).Trim()
if ($LASTEXITCODE -ne 0 -or $taskCameraId -notmatch '^[0-9a-f-]{36}$') { throw 'Configuracao invalida.' }
$taskStatusPath = Join-Path $taskRoot ".local/edge-control/$taskCameraId-status.json"
$taskStartUtc = [DateTime]::UtcNow
$taskId = [guid]::NewGuid().ToString()
$taskDirectory = Join-Path $taskRoot ".local/etapa08/continuous-$taskId"
New-Item -ItemType Directory -Path $taskDirectory | Out-Null
$taskProcess = Start-Process -FilePath (Get-Command uv).Source -ArgumentList @('run', '--project', 'services/edge', '--frozen', 'radar-edge', 'run', '--config', $Config, '--preview') -PassThru -WindowStyle Hidden -RedirectStandardOutput (Join-Path $taskDirectory 'worker.json') -RedirectStandardError (Join-Path $taskDirectory 'worker-errors.log')
$taskWatch = [Diagnostics.Stopwatch]::StartNew()
$taskWriter = [System.IO.StreamWriter]::new((Join-Path $taskDirectory 'resources.jsonl'), $false, [System.Text.UTF8Encoding]::new($false))
Write-Host 'Observacao iniciada. Nenhum video e gravado. Q/Esc na previa encerra.'
Write-Host 'Este comando mede recursos; nao confirma sozinho postura, cobertura ou revisao humana.'
try {
    do {
        $taskAll = @(Get-CimInstance Win32_Process)
        $taskIds = [System.Collections.Generic.HashSet[uint32]]::new()
        [void]$taskIds.Add([uint32]$taskProcess.Id)
        do {
            $taskAdded = $false
            foreach ($taskItem in $taskAll) {
                if ($taskIds.Contains([uint32]$taskItem.ParentProcessId) -and -not $taskIds.Contains([uint32]$taskItem.ProcessId)) {
                    [void]$taskIds.Add([uint32]$taskItem.ProcessId)
                    $taskAdded = $true
                }
            }
        } while ($taskAdded)
        $taskMembers = @($taskAll | Where-Object { $taskIds.Contains([uint32]$_.ProcessId) })
        $taskCpu = ($taskMembers | ForEach-Object { ([double]$_.KernelModeTime + [double]$_.UserModeTime) / 10000000 } | Measure-Object -Sum).Sum
        $taskMemory = ($taskMembers | ForEach-Object { [double]$_.WorkingSetSize } | Measure-Object -Sum).Sum
        $taskStatus = $null
        try {
            $taskStatusFile = Get-Item -LiteralPath $taskStatusPath
            if ($taskStatusFile.LastWriteTimeUtc -ge $taskStartUtc) {
                # Keep the read handle short-lived; the worker retries Windows rename conflicts.
                $taskStream = [System.IO.File]::Open($taskStatusPath, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, ([System.IO.FileShare]::ReadWrite -bor [System.IO.FileShare]::Delete))
                try {
                    $taskReader = [System.IO.StreamReader]::new($taskStream, [System.Text.Encoding]::UTF8, $true)
                    try { $taskStatusText = $taskReader.ReadToEnd() }
                    finally { $taskReader.Dispose() }
                } finally { $taskStream.Dispose() }
                $taskStatus = $taskStatusText | ConvertFrom-Json
            }
        } catch { $taskStatus = $null }
        $taskWriter.WriteLine((@{ elapsedSeconds = $taskWatch.Elapsed.TotalSeconds; utc = [DateTime]::UtcNow.ToString('o'); processCount = $taskMembers.Count; cpuSecondsLivingTree = $taskCpu; workingSetBytesSum = $taskMemory; workerStatus = $taskStatus; statusAgeSeconds = $(if ($null -ne $taskStatus) { ([DateTime]::UtcNow - $taskStatusFile.LastWriteTimeUtc).TotalSeconds } else { $null }); method = 'Win32_Process; uv and living descendants; CPU cumulative and memory sum. Shared pages can count twice; exited children can disappear from cumulative CPU. Status sampled at about 1 second; null/stale is unobserved.' } | ConvertTo-Json -Compress -Depth 10))
        $taskWriter.Flush()
        Start-Sleep -Seconds 1
        $taskProcess.Refresh()
    } while (-not $taskProcess.HasExited)
} finally {
    $taskWriter.Dispose()
    Write-Host "Medicoes privadas em $taskDirectory"
}
if ($taskProcess.ExitCode -ne 0) { throw 'Worker encerrou com erro; confira worker-errors.log e o relatorio.' }
