param([ValidateSet('owner', 'operator')][string]$Mode = 'owner')
$radarEmail = Read-Host 'E-mail da conta'
$radarSecret = Read-Host 'Senha (12 a 128 caracteres; nao sera exibida)' -AsSecureString
$radarConfirm = Read-Host 'Repita a senha' -AsSecureString
$radarPointer = [IntPtr]::Zero
$radarConfirmPointer = [IntPtr]::Zero
$radarEmailKey = if ($Mode -eq 'owner') { 'BOOTSTRAP_EMAIL' } else { 'OPERATOR_EMAIL' }
$radarPasswordKey = if ($Mode -eq 'owner') { 'BOOTSTRAP_PASSWORD' } else { 'OPERATOR_PASSWORD' }
$radarPreviousEmail = [Environment]::GetEnvironmentVariable($radarEmailKey, 'Process')
$radarPreviousPassword = [Environment]::GetEnvironmentVariable($radarPasswordKey, 'Process')
try {
    $radarPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($radarSecret)
    $radarConfirmPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($radarConfirm)
    $radarPlain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($radarPointer)
    if ($radarPlain -cne [Runtime.InteropServices.Marshal]::PtrToStringBSTR($radarConfirmPointer)) { throw 'Senhas diferentes.' }
    if ($radarPlain.Length -lt 12 -or $radarPlain.Length -gt 128) { throw 'Use entre 12 e 128 caracteres.' }
    [Environment]::SetEnvironmentVariable($radarEmailKey, $radarEmail, 'Process')
    [Environment]::SetEnvironmentVariable($radarPasswordKey, $radarPlain, 'Process')
    if ($Mode -eq 'owner') { & pnpm.cmd db:seed } else { & pnpm.cmd user:operator-env }
    if ($LASTEXITCODE -ne 0) { throw 'Provisionamento falhou. Verifique a configuracao e o banco.' }
} finally {
    [Environment]::SetEnvironmentVariable($radarEmailKey, $radarPreviousEmail, 'Process')
    [Environment]::SetEnvironmentVariable($radarPasswordKey, $radarPreviousPassword, 'Process')
    $radarPlain = $null
    if ($radarPointer -ne [IntPtr]::Zero) { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($radarPointer) }
    if ($radarConfirmPointer -ne [IntPtr]::Zero) { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($radarConfirmPointer) }
    $radarSecret.Dispose()
    $radarConfirm.Dispose()
}
