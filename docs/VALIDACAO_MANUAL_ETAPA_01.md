# Validação manual — etapa 01

Execute na raiz do repositório, em PowerShell. Não cole senha, token ou corpo de
requisição autenticada em chats, screenshots ou relatórios. Os comandos abaixo
mantêm os segredos em variáveis locais, sem imprimi-los ou salvá-los em histórico.
Não há tela de login nesta etapa.

## Preparação

```powershell
. ./scripts/activate.ps1
pnpm.cmd install --frozen-lockfile
pnpm.cmd setup:env
pnpm.cmd infra:up
pnpm.cmd db:generate
pnpm.cmd db:migrate
pnpm.cmd setup:owner
```

`setup:owner` solicita e-mail e senha duas vezes (12–128 caracteres) sem exibi-la.
Usa variáveis privadas somente no processo de provisionamento. Não grava a senha
no arquivo `.env`. É possível, alternativamente, preencher `BOOTSTRAP_EMAIL` e
`BOOTSTRAP_PASSWORD` no `apps/api/.env` ignorado e executar `pnpm.cmd db:seed`.
Nunca preencher o `.env.example` com segredo real.

Esperado: migração aplicada ou nenhuma migração pendente; provisionamento com
`status: ok`, IDs e `created: true` na primeira criação. Repetir com o mesmo e-mail
retorna `created: false` e preserva a senha e os registros existentes, mesmo que
uma senha diferente seja fornecida. Não é um comando de reset de senha.

O banco do projeto é `127.0.0.1:15432`. Não usar o PostgreSQL existente em 5432.
Nunca executar reset, `db push`, limpeza ou `down -v` no banco da demonstração.

Em dois terminais separados (ative as ferramentas **em cada terminal**):

```powershell
. ./scripts/activate.ps1
pnpm.cmd dev:api
```

```powershell
. ./scripts/activate.ps1
pnpm.cmd dev:web
```

## Saúde e contrato

```powershell
Invoke-RestMethod http://127.0.0.1:3001/v1/health/live
Invoke-RestMethod http://127.0.0.1:3001/v1/health/ready
Invoke-RestMethod http://127.0.0.1:3000/api/health/ready
$radarOpenApi = Invoke-RestMethod http://127.0.0.1:3001/v1/openapi.json
$radarOpenApi.info
```

Esperado: três respostas `status: ok`; OpenAPI com versão 0.1.0.
O arquivo [OPENAPI.json](OPENAPI.json) é gerado por `pnpm.cmd openapi:generate`.
Liveness independe do banco; readiness executa `SELECT 1` de verdade.

## Login pelo proxy da web, sem expor a senha

No terminal de validação:

```powershell
$radarBase = 'http://127.0.0.1:3000/api'
$radarOrigin = @{ Origin = 'http://127.0.0.1:3000' }
$radarEmail = Read-Host 'E-mail do proprietario'
$radarSecurePassword = Read-Host 'Senha' -AsSecureString
$radarPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($radarSecurePassword)
try {
    $radarBody = @{
        email = $radarEmail
        password = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($radarPointer)
    } | ConvertTo-Json -Compress
    $radarUser = Invoke-RestMethod "$radarBase/auth/login" -Method Post -Headers $radarOrigin -ContentType 'application/json' -Body $radarBody -SessionVariable radarSession
    $radarUser | Select-Object id, tenantId, role, expiresAt
} finally {
    $radarBody = $null
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($radarPointer)
    $radarSecurePassword.Dispose()
}
Invoke-RestMethod "$radarBase/auth/me" -WebSession $radarSession
```

Esperado: login HTTP 200 com `role: OWNER`; `/auth/me` retorna a identidade.
O token humano vem apenas no cookie `radar_session`, HttpOnly, SameSite=Lax,
Path=/, duração de oito horas. Não imprima a coleção de cookies. A exceção ao
Secure exige `NODE_ENV=development`, `ALLOW_INSECURE_LOCAL_HTTP=true`, API em
loopback e Origin HTTP da web em 127.0.0.1. Fora disso o cookie é Secure, a origem
precisa ser HTTPS e esta bancada não implementa exposição remota/TLS por conta própria.

Senha incorreta ou usuário inexistente: HTTP 401 com mensagem idêntica. Para
repetir o bloco de login, informe uma senha incorreta **localmente**; não escreva
a senha real como literal de comando. Há limite em memória de 10 tentativas por
e-mail e 60 por IP em cinco minutos; não usar essa checagem para bloquear sua conta.

## Leitura e configuração

```powershell
$radarSites = Invoke-RestMethod "$radarBase/sites" -WebSession $radarSession
$radarSites.items | Select-Object id, name, timezone
$radarSiteId = $radarSites.items[0].id
$radarCameraBody = @{
    siteId = $radarSiteId
    name = 'Camera de bancada'
    type = 'WEBCAM'
    expectedRunning = $false
} | ConvertTo-Json
$radarCamera = Invoke-RestMethod "$radarBase/cameras" -Method Post -Headers $radarOrigin -WebSession $radarSession -ContentType 'application/json' -Body $radarCameraBody
$radarCamera | Select-Object id, siteId, name, type, expectedRunning, device
Invoke-RestMethod "$radarBase/cameras?limit=20" -WebSession $radarSession
```

Esperado: câmera criada com HTTP 201 e Device estável. A criação é explícita e
permanece no banco; repetir o comando cria outra câmera. Nenhum dispositivo físico
é aberto. Tipos aceitos: FILE, WEBCAM, RTSP; tipo não comprova compatibilidade.
Não existe campo para URI, senha de câmera ou token de captura. Campos desconhecidos
(inclusive `tenantId`) são rejeitados com HTTP 400.

Listagens retornam `{items, nextCursor}` com limite padrão 20/máximo 100, ordenadas
por `(createdAt,id)`. Para continuar, envie `cursor=<nextCursor>`. Leituras e alterações
com IDs de outro tenant retornam 404, sem revelar a existência do registro.

Alteração somente OWNER:

```powershell
$radarPatch = @{ expectedRunning = $false; name = 'Camera configurada' } | ConvertTo-Json
Invoke-RestMethod "$radarBase/cameras/$($radarCamera.id)" -Method Patch -Headers $radarOrigin -WebSession $radarSession -ContentType 'application/json' -Body $radarPatch
```

Esperado: HTTP 200. Isso altera apenas configuração; não anuncia captura online.

## Token do worker: emissão única, rotação e revogação

```powershell
$radarIssued = Invoke-RestMethod "$radarBase/cameras/$($radarCamera.id)/device-credentials" -Method Post -Headers $radarOrigin -WebSession $radarSession -ContentType 'application/json' -Body '{}'
$radarIssued | Select-Object id, deviceId, cameraId, version
$radarBearer = @{ Authorization = "Bearer $($radarIssued.token)" }
Invoke-RestMethod "$radarBase/edge/me" -Headers $radarBearer

$radarRotated = Invoke-RestMethod "$radarBase/cameras/$($radarCamera.id)/device-credentials" -Method Post -Headers $radarOrigin -WebSession $radarSession -ContentType 'application/json' -Body '{}'
$radarRotated | Select-Object id, deviceId, cameraId, version
```

O segredo fica nas variáveis `$radarIssued.token` e `$radarRotated.token`, nunca
imprima os objetos completos. Esperado: `deviceId` igual e versão incrementada.
O bearer antigo passa a dar HTTP 401. O novo funciona em `/edge/me`, diagnóstico
de escopo sem ingestão ou heartbeat. Não há endpoint de leitura posterior do token.

```powershell
try {
    Invoke-RestMethod "$radarBase/edge/me" -Headers $radarBearer
    throw 'O bearer anterior deveria estar revogado.'
} catch {
    if ($_.Exception.Response -and [int]$_.Exception.Response.StatusCode -eq 401) {
        Write-Host 'Bearer anterior rejeitado: 401'
    } else { throw }
}
$radarBearer = @{ Authorization = "Bearer $($radarRotated.token)" }
Invoke-RestMethod "$radarBase/edge/me" -Headers $radarBearer
Invoke-RestMethod "$radarBase/device-credentials/$($radarRotated.id)" -Method Delete -Headers $radarOrigin -WebSession $radarSession
```

Esperado: diagnóstico do novo bearer HTTP 200; DELETE HTTP 204. Depois da revogação,
o novo bearer também deve retornar 401 usando o mesmo bloco `try/catch`.
Sessão humana não autentica `/edge/me`; bearer não autentica `/sites` ou `/auth/me`.

## Origin externa, logout e operador

```powershell
try {
    Invoke-RestMethod "$radarBase/auth/logout" -Method Post -Headers @{ Origin = 'https://externo.example' } -WebSession $radarSession
    throw 'A origem externa deveria ser rejeitada.'
} catch {
    if ($_.Exception.Response -and [int]$_.Exception.Response.StatusCode -eq 403) {
        Write-Host 'Origem externa rejeitada: 403'
    } else { throw }
}
Invoke-RestMethod "$radarBase/auth/logout" -Method Post -Headers $radarOrigin -WebSession $radarSession
```

Esperado: tentativa externa 403 e logout correto 204. `/auth/me` depois disso deve
retornar 401. Ausência de Origin também é rejeitada em login e mutações com sessão.

Para criar operador localmente, execute `pnpm.cmd user:create-operator`; o comando
solicita credenciais sem exibir senha e usa o mesmo tenant de bootstrap. Refaça
o login com esse operador: leitura de locais/câmeras retorna 200; criação/alteração
e emissão/revogação de credencial retornam 403. Não há gestão pública de equipe.

## Falhas, isolamento e regressões automatizadas

```powershell
pnpm.cmd test:api
pnpm.cmd lint
pnpm.cmd typecheck
pnpm.cmd build
```

`test:api` cria outro container PostgreSQL 17.11, banco `radar_test_<id>`, porta
local temporária fixa durante a suíte e volume anônimo exclusivo. Os testes aplicam
migração em banco vazio e testam seed repetido, sessões, limites, Origin, papéis,
dois tenants artificiais, FKs compostas, rotação concorrente, logs, OpenAPI e
parada/retomada **somente desse container**. Ao final ele e seu volume são removidos,
mesmo em falha. Nunca usa o volume ou limpa o banco de demonstração. Em interrupção
abrupta, inspecione containers `radar-test-*` antes de remover apenas o teste abandonado.

Não pare o banco real da demonstração para testar readiness: a suíte já verifica
503 na indisponibilidade, liveness 200 e retorno a 200 após restauração isolada.
Expiração de sessão é testada com um registro sintético vencido, sem esperar oito horas.

Para encerrar web/API: Ctrl+C em seus terminais. Para o banco da demonstração:
`pnpm.cmd infra:down`, sem excluir volume. Limpe as variáveis contendo tokens ao
terminar (`$radarIssued=$null; $radarRotated=$null; $radarBearer=$null; $radarSession=$null`).
