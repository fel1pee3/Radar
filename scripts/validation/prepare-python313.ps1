# Official PSF runtime, installed only under this workspace's .local.
# No policy, PATH, registry or original Python environment is changed.
# Runtime ZIP is the normal Python Install Manager package, not the embeddable ZIP.
# https://www.python.org/ftp/python/3.13.17/windows-3.13.17.json
# https://www.python.org/downloads/release/python-31317/
[CmdletBinding()]
param(
    [string]$Output = '',
    [string]$ExistingRuntime = '',
    [switch]$SkipSync
)
$ErrorActionPreference = 'Stop'
if ($env:UV_PROJECT_ENVIRONMENT) { throw 'UV_PROJECT_ENVIRONMENT definido: preserve esse ambiente e remova a variavel somente deste terminal antes da preparacao isolada.' }
$setupRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$setupVersion = '3.13.17'
$setupManifestUrl = 'https://www.python.org/ftp/python/3.13.17/windows-3.13.17.json'
$setupArchiveUrl = 'https://www.python.org/ftp/python/3.13.17/python-3.13.17-amd64.zip'
$setupArchiveHash = 'b26ca4b4ee51e157836049934d2b8eabd55939be296f3130254251b6df96ec2f'
$setupBinaryHashes = @{
    'python.exe' = '7c2fc2b303a4ee3cc14cc17b47bc6e8bca98c78792edd123b846a560da44b203'
    'python313.dll' = '26026530507a7389e7892ce130e7c1753b32a2df03ec3721d45ad8c1705d40eb'
}
function Resolve-SetupPath([string]$Path, [int]$Depth = 0) {
    if ($Depth -gt 16) { throw 'Limite de resolucao de links atingido.' }
    $full = [IO.Path]::GetFullPath($Path)
    $rootPart = [IO.Path]::GetPathRoot($full)
    $pieces = @($full.Substring($rootPart.Length) -split '[\\/]')
    $cursor = $rootPart
    for ($i = 0; $i -lt $pieces.Count; $i++) {
        if (-not $pieces[$i]) { continue }
        $cursor = Join-Path $cursor $pieces[$i]
        if (Test-Path -LiteralPath $cursor) {
            $item = Get-Item -LiteralPath $cursor -Force
            if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                $targets = @($item.Target)
                if ($targets.Count -eq 0 -or -not $targets[0]) { throw 'Link sem destino observavel.' }
                $target = [string]$targets[0]
                if ($target.StartsWith('\\?\')) { $target = $target.Substring(4) }
                if (-not [IO.Path]::IsPathRooted($target)) { $target = Join-Path (Split-Path -Parent $cursor) $target }
                for ($j = $i + 1; $j -lt $pieces.Count; $j++) {
                    if ($pieces[$j]) { $target = Join-Path $target $pieces[$j] }
                }
                return Resolve-SetupPath $target ($Depth + 1)
            }
        }
    }
    return $full
}
function Get-SetupLocalPath([string]$Path) {
    $full = if ([IO.Path]::IsPathRooted($Path)) { [IO.Path]::GetFullPath($Path) } else { [IO.Path]::GetFullPath((Join-Path $setupRoot $Path)) }
    $resolved = Resolve-SetupPath $full
    $rootResolved = (Resolve-SetupPath $setupRoot).TrimEnd('\', '/')
    if (-not $resolved.StartsWith(($rootResolved + '\.local\'), [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Use somente destino resolvido dentro de workspace/.local.'
    }
    return $full
}
function Save-SetupReceipt {
    [IO.File]::WriteAllText((Join-Path $setupOutput 'preparation.json'), ($setupReceipt | ConvertTo-Json -Depth 12), [Text.UTF8Encoding]::new($false))
}
if (-not $Output) { $Output = '.local/python313-preparation-' + [guid]::NewGuid().ToString() }
$setupOutput = Get-SetupLocalPath $Output
if (Test-Path -LiteralPath $setupOutput) { throw 'Destino existente preservado. Use uma pasta nova.' }
New-Item -ItemType Directory -Path $setupOutput | Out-Null
$setupReceipt = @{
    schemaVersion = 1; createdAtUtc = [datetime]::UtcNow.ToString('o')
    version = $setupVersion; status = 'PREPARING'; output = $setupOutput
    manifestUrl = $setupManifestUrl; archiveUrl = $setupArchiveUrl; archiveSha256 = $setupArchiveHash
    usedExistingRuntime = [bool]$ExistingRuntime; skippedSync = [bool]$SkipSync
    policiesModified = $false; globalPathModified = $false; registryModified = $false
    originalEnvironmentsReplaced = $false; webcamOpened = $false; inferenceExecuted = $false
    patchLimitation = '3.13.18 is newer and source-only. 3.13.17 is the verified official Windows binary candidate, not the newest security patch.'
}
Save-SetupReceipt
try {
    if ($ExistingRuntime) {
        $setupRuntime = Get-SetupLocalPath $ExistingRuntime
        if (-not (Test-Path -LiteralPath $setupRuntime -PathType Container)) { throw 'Runtime existente nao encontrado.' }
    } else {
        $setupManifestPath = Join-Path $setupOutput 'windows-3.13.17.json'
        Invoke-WebRequest -Uri $setupManifestUrl -OutFile $setupManifestPath -UseBasicParsing -TimeoutSec 120
        $setupManifest = [IO.File]::ReadAllText($setupManifestPath) | ConvertFrom-Json
        $setupPackage = @($setupManifest.versions | Where-Object { $_.id -eq 'pythoncore-3.13-64' })
        if ($setupPackage.Count -ne 1 -or $setupPackage[0].url -ne $setupArchiveUrl -or $setupPackage[0].hash.sha256 -ne $setupArchiveHash) {
            throw 'Manifesto oficial divergiu da distribuicao fixada. Nao executar.'
        }
        $setupArchive = Join-Path $setupOutput 'python-3.13.17-amd64.zip'
        Invoke-WebRequest -Uri $setupArchiveUrl -OutFile $setupArchive -UseBasicParsing -TimeoutSec 180
        if ((Get-FileHash -LiteralPath $setupArchive -Algorithm SHA256).Hash.ToLowerInvariant() -ne $setupArchiveHash) {
            throw 'SHA-256 do ZIP divergiu. Nao executar.'
        }
        $setupRuntime = Join-Path $setupOutput 'runtime'
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        $setupZip = [IO.Compression.ZipFile]::OpenRead($setupArchive)
        try {
            $setupRuntimePrefix = [IO.Path]::GetFullPath($setupRuntime).TrimEnd('\', '/') + '\'
            foreach ($setupEntry in $setupZip.Entries) {
                $setupEntryPath = [IO.Path]::GetFullPath((Join-Path $setupRuntime $setupEntry.FullName))
                if (-not $setupEntryPath.StartsWith($setupRuntimePrefix, [StringComparison]::OrdinalIgnoreCase)) {
                    throw 'Entrada ZIP fora do destino privado. Nao extrair.'
                }
            }
        } finally { $setupZip.Dispose() }
        Expand-Archive -LiteralPath $setupArchive -DestinationPath $setupRuntime
    }
    $setupSignatures = @()
    foreach ($setupName in @('python.exe', 'python313.dll')) {
        $setupFile = Join-Path $setupRuntime $setupName
        if (-not (Test-Path -LiteralPath $setupFile -PathType Leaf)) { throw "Arquivo ausente: $setupName" }
        [void](Get-SetupLocalPath $setupFile)
        $setupHash = (Get-FileHash -LiteralPath $setupFile -Algorithm SHA256).Hash.ToLowerInvariant()
        $setupSignature = Get-AuthenticodeSignature -LiteralPath $setupFile
        $setupInfo = [Diagnostics.FileVersionInfo]::GetVersionInfo($setupFile)
        if ($setupHash -ne $setupBinaryHashes[$setupName] -or $setupInfo.FileVersion -ne $setupVersion -or
            $setupSignature.Status -ne 'Valid' -or $setupSignature.SignerCertificate.Subject -notmatch '(^|, )O=Python Software Foundation(,|$)') {
            throw "Bytes, versao ou assinatura PSF nao correspondem ao runtime fixado: $setupName"
        }
        $setupSignatures += @{
            path = $setupFile; sha256 = $setupHash; fileVersion = $setupInfo.FileVersion
            signatureStatus = [string]$setupSignature.Status; signer = $setupSignature.SignerCertificate.Subject
            thumbprint = $setupSignature.SignerCertificate.Thumbprint
        }
    }
    $setupPython = Join-Path $setupRuntime 'python.exe'
    $setupReceipt.runtime = $setupRuntime
    $setupReceipt.python = $setupPython
    $setupReceipt.signatures = $setupSignatures
    $setupReceipt.status = 'SIGNATURES_VERIFIED'
    Save-SetupReceipt
    # First execution occurs only after hashes, version and PSF signatures are checked.
    $setupVersionText = & $setupPython -I -c 'import json,sys; print(json.dumps(dict(version=sys.version,executable=sys.executable,prefix=sys.prefix)))'
    $setupReceipt.executionExitCode = $LASTEXITCODE
    if ($LASTEXITCODE -ne 0) { throw ('Execucao isolada falhou, exit=' + $LASTEXITCODE + '. Confira o diagnostico antes de atribuir a causa ao Windows.') }
    $setupReceipt.execution = $setupVersionText | ConvertFrom-Json
    $setupReceipt.sync = @()
    if (-not $SkipSync) {
        $setupUv = Join-Path $setupRoot '.local/tools/uv/bin/uv.exe'
        if (-not (Test-Path -LiteralPath $setupUv)) { throw 'uv local ausente; leia scripts/activate.ps1.' }
        if ((& $setupUv --version) -notmatch '^uv 0\.13\.4\b') { throw 'Use uv 0.13.4 fixado.' }
        foreach ($setupProject in @('experiments/python313-cpu', 'experiments/python313-directml')) {
            $setupProjectPath = Join-Path $setupRoot $setupProject
            $setupVenvCfg = Join-Path $setupProjectPath '.venv/pyvenv.cfg'
            if (Test-Path -LiteralPath $setupVenvCfg) {
                $setupHomeLine = @([IO.File]::ReadAllLines($setupVenvCfg) | Where-Object { $_ -match '^home\s*=' })
                if ($setupHomeLine.Count -ne 1) { throw "Ambiente existente sem home inequivoco: $setupProject" }
                $setupHome = ($setupHomeLine[0] -replace '^home\s*=\s*', '').Trim()
                if (-not (Resolve-SetupPath $setupHome).Equals((Resolve-SetupPath $setupRuntime), [StringComparison]::OrdinalIgnoreCase)) {
                    throw "Ambiente existente aponta a outro runtime e foi preservado: $setupProject. Use -ExistingRuntime com o runtime correspondente."
                }
            }
            $setupLog = Join-Path $setupOutput (($setupProject -replace '[/\\]', '-') + '.log')
            # uv writes progress to stderr even when successful. Redirect through
            # Process APIs so Windows PowerShell does not turn it into a terminating
            # NativeCommandError. The real exit code still controls success.
            $setupStart = New-Object Diagnostics.ProcessStartInfo
            $setupStart.FileName = $setupUv
            $setupStart.Arguments = 'sync --project "' + $setupProjectPath + '" --python "' + $setupPython + '" --frozen --no-python-downloads'
            $setupStart.UseShellExecute = $false
            $setupStart.CreateNoWindow = $true
            $setupStart.RedirectStandardOutput = $true
            $setupStart.RedirectStandardError = $true
            $setupChild = [Diagnostics.Process]::Start($setupStart)
            try {
                $setupStdout = $setupChild.StandardOutput.ReadToEndAsync()
                $setupStderr = $setupChild.StandardError.ReadToEndAsync()
                $setupChild.WaitForExit()
                $setupCode = $setupChild.ExitCode
                [IO.File]::WriteAllText($setupLog, ($setupStdout.GetAwaiter().GetResult() + $setupStderr.GetAwaiter().GetResult()), [Text.UTF8Encoding]::new($false))
            } finally { $setupChild.Dispose() }
            $setupReceipt.sync += @{ project = $setupProject; exitCode = $setupCode; log = $setupLog }
            Save-SetupReceipt
            if ($setupCode -ne 0) { throw "Falha no sync isolado: $setupProject. Confira o log." }
        }
    }
    $setupReceipt.status = if ($SkipSync) { 'RUNTIME_VERIFIED_SYNC_SKIPPED' } else { 'ISOLATED_ENVIRONMENTS_PREPARED' }
    Save-SetupReceipt
    Write-Output (@{ status = $setupReceipt.status; python = $setupPython; receipt = (Join-Path $setupOutput 'preparation.json'); webcamOpened = $false; policiesModified = $false } | ConvertTo-Json -Compress)
} catch {
    $setupReceipt.status = 'ERROR'
    $setupReceipt.error = $_.Exception.Message
    Save-SetupReceipt
    throw
}
