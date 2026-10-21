# Execute com dot-source: . ./scripts/activate.ps1
# Usa as ferramentas locais preparadas nesta máquina, sem alterar o PATH global.
$radarToolRoot = Join-Path $PSScriptRoot '../.local/tools'
$radarToolPaths = @(
    (Join-Path $radarToolRoot 'node-v24.22.1-win-x64'),
    (Join-Path $radarToolRoot 'pnpm/node_modules/.bin'),
    (Join-Path $radarToolRoot 'uv/bin')
)
foreach ($radarToolPath in $radarToolPaths) {
    if (Test-Path -LiteralPath $radarToolPath) {
        $env:PATH = "$radarToolPath;$env:PATH"
    }
}
if ((node --version) -ne 'v24.22.1') { throw 'Instale Node 24.22.1; veja docs/08_AMBIENTE_E_COMANDOS.md.' }
if ((pnpm.cmd --version) -ne '10.34.7') { throw 'Instale pnpm 10.34.7.' }
if ((uv --version) -notmatch '^uv 0\.13\.4\b') { throw 'Instale uv 0.13.4.' }
Write-Host 'Ferramentas do Radar disponiveis neste terminal.'
