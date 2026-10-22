param(
    [Parameter(Mandatory = $true)][Guid]$CameraId,
    [string]$OutputFile = '.local/webcam-device.json',
    [switch]$FromClipboard,
    [ValidateRange(1, 300)][int]$ClipboardTimeoutSeconds = 120
)
$ErrorActionPreference = 'Stop'
$privateRoot = [IO.Path]::GetFullPath((Join-Path (Get-Location) '.local'))
$targetPath = if ([IO.Path]::IsPathRooted($OutputFile)) {
    [IO.Path]::GetFullPath($OutputFile)
} else {
    [IO.Path]::GetFullPath((Join-Path (Get-Location) $OutputFile))
}
if (-not $targetPath.StartsWith($privateRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Use um arquivo dentro de .local.'
}
if (Test-Path -LiteralPath $targetPath) {
    throw 'Arquivo existente preservado. Use outro destino ou revise a configuracao local.'
}
$tokenPointer = [IntPtr]::Zero
try {
    if ($FromClipboard) {
        Write-Host 'Agora volte ao painel e clique em Copiar na credencial desta camera.'
        Write-Host 'Nao precisa colar nem apertar Enter. Aguardando o token por ate 2 minutos...'
        $clipboardDeadline = [DateTime]::UtcNow.AddSeconds($ClipboardTimeoutSeconds)
        do {
            try { $workerToken = ([string](Get-Clipboard -Raw -ErrorAction Stop)).Trim() }
            catch { $workerToken = '' }
            if ($workerToken -cmatch '^dev_[A-Za-z0-9_-]{43}$') { break }
            Start-Sleep -Milliseconds 200
        } while ([DateTime]::UtcNow -lt $clipboardDeadline)
    } else {
        $secureToken = Read-Host 'Cole a credencial de worker desta camera (entrada oculta)' -AsSecureString
        $tokenPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureToken)
        $workerToken = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($tokenPointer)
    }
    if ($workerToken -cnotmatch '^dev_[A-Za-z0-9_-]{43}$') {
        throw 'A area de transferencia ou entrada nao contem uma credencial valida. Nenhum arquivo foi salvo. Copie somente o token pelo botao Copiar do painel.'
    }
    $privateConfig = @{ apiUrl = 'http://127.0.0.1:3001/v1'; cameraId = $CameraId.ToString(); deviceToken = $workerToken }
    [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($targetPath)) | Out-Null
    [IO.File]::WriteAllText($targetPath, ($privateConfig | ConvertTo-Json), (New-Object Text.UTF8Encoding($false)))
    Write-Output 'status: ok; credencial salva no arquivo privado, sem exibir o token.'
} finally {
    if ($tokenPointer -ne [IntPtr]::Zero) { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($tokenPointer) }
    $workerToken = $null
    $privateConfig = $null
}
