# Read-only Windows runtime audit. Never executes Python or changes policies.
# Official field semantics:
# https://learn.microsoft.com/en-us/windows/security/application-security/application-control/app-control-for-business/operations/appcontrol-debugging-and-troubleshooting
# https://learn.microsoft.com/en-us/windows/security/application-security/application-control/app-control-for-business/operations/inbox-appcontrol-policies
# https://learn.microsoft.com/en-us/windows/apps/develop/smart-app-control/test-your-app-with-smart-app-control
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Output,
    [datetime]$Since = [datetime]::Today,
    [Nullable[datetime]]$Until = $null,
    [string[]]$RuntimeHomes = @()
)
$ErrorActionPreference = 'Stop'
$auditRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$auditLocal = Join-Path $auditRoot '.local'

function Write-AuditText([string]$Path, [string]$Text) {
    [IO.File]::WriteAllText($Path, $Text, [Text.UTF8Encoding]::new($false))
}
function Write-AuditJson([string]$Path, $Value) {
    Write-AuditText $Path ($Value | ConvertTo-Json -Depth 20)
}
function Resolve-AuditPath([string]$Path, [int]$Depth = 0) {
    if ($Depth -gt 16) { throw 'Limite de resolucao de junctions atingido.' }
    $full = [IO.Path]::GetFullPath($Path)
    $rootPart = [IO.Path]::GetPathRoot($full)
    $pieces = @($full.Substring($rootPart.Length) -split '[\\/]')
    $cursor = $rootPart
    $links = @()
    for ($i = 0; $i -lt $pieces.Count; $i++) {
        if (-not $pieces[$i]) { continue }
        $cursor = Join-Path $cursor $pieces[$i]
        if (Test-Path -LiteralPath $cursor) {
            $item = Get-Item -LiteralPath $cursor -Force
            if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                $targets = @($item.Target)
                if ($targets.Count -eq 0 -or -not $targets[0]) {
                    throw "Reparse point sem destino observavel: $cursor"
                }
                $target = [string]$targets[0]
                if ($target.StartsWith('\\?\')) { $target = $target.Substring(4) }
                if (-not [IO.Path]::IsPathRooted($target)) {
                    $target = Join-Path (Split-Path -Parent $cursor) $target
                }
                $links += @{ path = $cursor; target = $target; linkType = [string]$item.LinkType }
                for ($j = $i + 1; $j -lt $pieces.Count; $j++) {
                    if ($pieces[$j]) { $target = Join-Path $target $pieces[$j] }
                }
                $resolved = Resolve-AuditPath $target ($Depth + 1)
                return @{ requested = $full; resolved = $resolved.resolved; links = @($links) + @($resolved.links) }
            }
        }
    }
    return @{ requested = $full; resolved = $full; links = @($links) }
}
# All output is new evidence under this workspace's .local. No existing proof is replaced.
if ([IO.Path]::IsPathRooted($Output) -or $Output -notmatch '^\.local[\\/][^\\/]+') {
    throw 'Use uma pasta NOVA relativa dentro de .local, por exemplo .local/runtime-audit-UUID.'
}
if (@($Output -split '[\\/]' | Where-Object { $_ -eq '..' }).Count -gt 0) {
    throw 'O destino nao pode conter ..'
}
$targetPath = [IO.Path]::GetFullPath((Join-Path $auditRoot $Output))
$resolvedTarget = Resolve-AuditPath $targetPath
$resolvedRoot = (Resolve-AuditPath $auditRoot).resolved.TrimEnd('\', '/')
$allowedPrefix = $resolvedRoot + '\.local\'
if (-not $resolvedTarget.resolved.StartsWith($allowedPrefix, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'O destino resolvido precisa permanecer dentro de workspace/.local.'
}
if (Test-Path -LiteralPath $targetPath) { throw 'Destino existente preservado. Use uma pasta nova.' }
$auditEnd = if ($null -eq $Until) { Get-Date } else { [datetime]$Until }
if ($Since -gt $auditEnd) { throw 'Since deve ser anterior ou igual a Until.' }
New-Item -ItemType Directory -Path $targetPath | Out-Null
$eventDirectory = Join-Path $targetPath 'events'
New-Item -ItemType Directory -Path $eventDirectory | Out-Null
$errors = [Collections.Generic.List[object]]::new()
$environments = @()
$homes = [Collections.Generic.List[string]]::new()
foreach ($project in @('services/edge', 'experiments/directml', 'experiments/python313-cpu', 'experiments/python313-directml')) {
    $cfgPath = Join-Path $auditRoot "$project/.venv/pyvenv.cfg"
    $record = @{ project = $project; configuration = $cfgPath; present = (Test-Path -LiteralPath $cfgPath) }
    if ($record.present) {
        try {
            $raw = [IO.File]::ReadAllText($cfgPath)
            $properties = @{}
            foreach ($line in ($raw -split '\r?\n')) {
                if ($line -match '^\s*([^=]+?)\s*=\s*(.*?)\s*$') { $properties[$Matches[1]] = $Matches[2] }
            }
            $record.configurationText = $raw
            $record.properties = $properties
            $record.configurationSha256 = (Get-FileHash -LiteralPath $cfgPath -Algorithm SHA256).Hash.ToLowerInvariant()
            $record.venvExecutable = Join-Path $auditRoot "$project/.venv/Scripts/python.exe"
            $homes.Add((Split-Path -Parent $record.venvExecutable))
            if ($properties.home) {
                $homePath = if ([IO.Path]::IsPathRooted($properties.home)) { $properties.home } else { Join-Path (Split-Path -Parent $cfgPath) $properties.home }
                $homes.Add($homePath)
                $record.homeResolution = Resolve-AuditPath $homePath
            }
        } catch { $record.error = $_.Exception.Message }
    }
    $environments += $record
}
foreach ($runtimeHome in $RuntimeHomes) {
    $homes.Add($(if ([IO.Path]::IsPathRooted($runtimeHome)) { $runtimeHome } else { Join-Path $auditRoot $runtimeHome }))
}
$files = @()
$seen = @{}
foreach ($homePath in @($homes | Sort-Object -Unique)) {
    $candidates = @((Join-Path $homePath 'python.exe'), (Join-Path $homePath 'pythonw.exe'))
    if (Test-Path -LiteralPath $homePath -PathType Container) {
        $candidates += @(Get-ChildItem -LiteralPath $homePath -Filter 'python3*.dll' -File | ForEach-Object { $_.FullName })
    }
    foreach ($candidate in $candidates) {
        if ($seen.ContainsKey($candidate)) { continue }
        $seen[$candidate] = $true
        $record = @{ path = $candidate; present = (Test-Path -LiteralPath $candidate -PathType Leaf) }
        if ($record.present) {
            try {
                $record.resolution = Resolve-AuditPath $candidate
                $info = [Diagnostics.FileVersionInfo]::GetVersionInfo($candidate)
                $record.version = @{ file = $info.FileVersion; product = $info.ProductVersion; company = $info.CompanyName; originalFileName = $info.OriginalFilename }
                $record.sha256 = (Get-FileHash -LiteralPath $candidate -Algorithm SHA256).Hash.ToLowerInvariant()
                $signature = Get-AuthenticodeSignature -LiteralPath $candidate
                $record.authenticode = @{
                    status = [string]$signature.Status; message = $signature.StatusMessage
                    signatureType = [string]$signature.SignatureType
                    signer = $(if ($signature.SignerCertificate) {
                        @{ subject = $signature.SignerCertificate.Subject; issuer = $signature.SignerCertificate.Issuer
                           thumbprint = $signature.SignerCertificate.Thumbprint
                           notBefore = $signature.SignerCertificate.NotBefore.ToUniversalTime().ToString('o')
                           notAfter = $signature.SignerCertificate.NotAfter.ToUniversalTime().ToString('o') }
                    } else { $null })
                }
            } catch { $record.error = $_.Exception.Message }
        }
        $files += $record
    }
}
$registry = @{ path = 'HKLM:\SYSTEM\CurrentControlSet\Control\CI\Policy'; valueName = 'VerifiedAndReputablePolicyState' }
try {
    $registry.value = (Get-ItemProperty -LiteralPath $registry.path -Name $registry.valueName).VerifiedAndReputablePolicyState
} catch { $registry.error = $_.Exception.Message }
$events = @()
try {
    $rawEvents = @(Get-WinEvent -FilterHashtable @{
        LogName = 'Microsoft-Windows-CodeIntegrity/Operational'
        Id = @(3033, 3077, 3089); StartTime = $Since; EndTime = $auditEnd
    } -ErrorAction Stop)
    $mapped = @($rawEvents | ForEach-Object {
        $eventXml = [xml]$_.ToXml()
        $fields = @{}
        $fieldIndex = 0
        foreach ($data in $eventXml.Event.EventData.Data) {
            $name = if ($data.Name) { [string]$data.Name } else { "field$fieldIndex" }
            $fields[$name] = [string]$data.'#text'
            $fieldIndex++
        }
        @{ recordId = $_.RecordId; eventId = $_.Id; utc = $_.TimeCreated.ToUniversalTime().ToString('o')
           activityId = [string]$eventXml.Event.System.Correlation.ActivityID
           fields = $fields; message = $_.Message; xml = $_.ToXml() }
    })
    $blocks = @($mapped | Where-Object {
        $_.eventId -in @(3033, 3077) -and ($_.message -match '(?i)python312\.dll' -or
            @($_.fields.Values | Where-Object { $_ -match '(?i)python312\.dll' }).Count -gt 0)
    })
    $activities = @($blocks | ForEach-Object { $_.activityId } | Where-Object { $_ } | Sort-Object -Unique)
    $events = @($mapped | Where-Object {
        $_ -in $blocks -or ($_.eventId -eq 3089 -and $_.activityId -in $activities)
    } | Sort-Object recordId)
    foreach ($record in $events) {
        Write-AuditText (Join-Path $eventDirectory "$($record.recordId)-$($record.eventId).xml") $record.xml
        $record.Remove('xml')
    }
} catch {
    # An empty time window is observable as no events, not a successful runtime test.
    $errors.Add(@{ operation = 'CodeIntegrity event read'; message = $_.Exception.Message })
}
$correlations = @($events | Where-Object { $_.eventId -in @(3033, 3077) } | ForEach-Object {
    @{ blockRecordId = $_.recordId; activityId = $_.activityId
       signatureRecordIds = @() }
})
# Build correlation lists without relying on the event message or chronological adjacency.
foreach ($correlation in $correlations) {
    $activity = $correlation.activityId
    $correlation.signatureRecordIds = @($events | Where-Object { $_.eventId -eq 3089 -and $_.activityId -eq $activity } | ForEach-Object { $_.recordId })
}
$ciTool = @{ command = 'CiTool.exe -lp -json'; readOnly = $true; available = $false }
$ciPath = Join-Path $env:windir 'System32/CiTool.exe'
if (Test-Path -LiteralPath $ciPath) {
    $ciTool.available = $true
    try {
        $stdout = Join-Path $targetPath 'citool-stdout.txt'
        $stderr = Join-Path $targetPath 'citool-stderr.txt'
        $process = Start-Process -FilePath $ciPath -ArgumentList @('-lp', '-json') -WindowStyle Hidden -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr
        if (-not $process.WaitForExit(10000)) {
            $process.Kill()
            $ciTool.error = 'Read-only inventory timed out after 10 seconds.'
        } else {
            $ciTool.exitCode = $process.ExitCode
            $ciTool.stdout = [IO.File]::ReadAllText($stdout)
            $ciTool.stderr = [IO.File]::ReadAllText($stderr)
            try {
                $ciTool.policies = $ciTool.stdout | ConvertFrom-Json
                if ($ciTool.policies.PSObject.Properties.Name -contains 'OperationResult') {
                    $ciTool.operationResult = $ciTool.policies.OperationResult
                    $ciTool.accessDenied = ($ciTool.operationResult -eq -2147024891)
                }
            } catch { $ciTool.jsonError = $_.Exception.Message }
            if ($null -eq $ciTool.exitCode) { $ciTool.exitCodeUnavailable = $true }
        }
    } catch { $ciTool.error = $_.Exception.Message }
}
$sacEvents = @($events | Where-Object {
    $_.eventId -eq 3077 -and
    ([string]$_.fields.PolicyName -eq 'VerifiedAndReputableDesktop' -or
     [string]$_.fields.PolicyGUID -eq '{0283ac0f-fff1-49ae-ada1-8a933130cad6}')
})
$assessment = @{
    pythonExecuted = $false; policyModified = $false; captureOpened = $false
    smartAppControlBlockConfirmed = ($sacEvents.Count -gt 0)
    smartAppControlEnforcedRegistry = ($registry.value -eq 1)
    managedEnterprisePolicyInferred = $false
    note = 'Unsigned is not proof of corruption. Valid signatures do not by themselves establish policy authorization. No events does not prove runtime availability.'
}
$report = @{
    schemaVersion = 1; createdAtUtc = [datetime]::UtcNow.ToString('o')
    window = @{ since = $Since.ToString('o'); until = $auditEnd.ToString('o'); timeZone = [TimeZoneInfo]::Local.Id }
    workspace = $auditRoot; output = $targetPath; outputResolution = $resolvedTarget
    script = @{ path = $PSCommandPath; sha256 = (Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant() }
    environments = @($environments); runtimes = @($files); codeIntegrityEvents = @($events)
    correlations = @($correlations); registrySmartAppControl = $registry; ciTool = $ciTool
    assessment = $assessment; errors = $errors.ToArray()
}
Write-AuditJson (Join-Path $targetPath 'audit.json') $report
Write-Output (@{ status = 'read-only audit saved'; report = (Join-Path $targetPath 'audit.json'); eventCount = $events.Count
    smartAppControlBlockConfirmed = $assessment.smartAppControlBlockConfirmed
    pythonExecuted = $false; policyModified = $false } | ConvertTo-Json -Compress)
