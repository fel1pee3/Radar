# Validação manual — etapa 02

Execute na raiz, em PowerShell. Este roteiro usa chamadas HTTP com dados
**SIMULATED**. Não abre câmera, executa IA ou envia mensagem externa. A interface
continua mínima; os endpoints `/api/...` retornam JSON e não são telas de login.

## Preparação

```powershell
. ./scripts/activate.ps1
pnpm.cmd install --frozen-lockfile
uv sync --project services/edge --frozen
pnpm.cmd setup:env
pnpm.cmd infra:up
pnpm.cmd db:generate
pnpm.cmd db:migrate
```

Use o proprietário já existente; `setup:owner` só é necessário numa instalação
nova. O PostgreSQL do projeto fica em `127.0.0.1:15432`. Não utilize a porta 5432,
reset, limpeza do banco ou `down -v`.

Em dois terminais separados, ative as ferramentas **em cada terminal**:

```powershell
. ./scripts/activate.ps1
pnpm.cmd dev:api
```

```powershell
. ./scripts/activate.ps1
pnpm.cmd dev:web
```

No terceiro terminal, na raiz:

```powershell
$radarBase = 'http://127.0.0.1:3000/api'
$radarOrigin = @{ Origin = 'http://127.0.0.1:3000' }
Invoke-RestMethod "$radarBase/health/ready"
$radarEmail = Read-Host 'E-mail do proprietario'
$radarSecurePassword = Read-Host 'Senha' -AsSecureString
$radarPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($radarSecurePassword)
try {
    $radarLoginBody = @{
        email = $radarEmail
        password = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($radarPointer)
    } | ConvertTo-Json -Compress
    $radarIdentity = Invoke-RestMethod "$radarBase/auth/login" -Method Post -Headers $radarOrigin -ContentType 'application/json' -Body $radarLoginBody -SessionVariable radarSession
    $radarIdentity | Select-Object id, tenantId, role
} finally {
    $radarLoginBody = $null
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($radarPointer)
    $radarSecurePassword.Dispose()
}
```

Esperado: readiness `status: ok`, login 200 e `role: OWNER`. Não imprima cookies,
senha ou o objeto que contém a credencial de worker. Os próximos blocos usam
essa sessão e são também exercitados pelo teste HTTP/PowerShell isolado.

<!-- smoke:begin -->

## Câmera lógica e credencial exclusiva deste teste

Não reutilize uma câmera que já possua worker: emitir credencial rotaciona a
anterior. Este bloco cria uma câmera lógica nova; nenhum hardware é acessado.

```powershell
$ErrorActionPreference = 'Stop'
$radarSites = Invoke-RestMethod "$radarBase/sites" -WebSession $radarSession
$radarCameraBody = @{ siteId = $radarSites.items[0].id; name = 'Teste HTTP etapa 02'; type = 'FILE' } | ConvertTo-Json
$radarCamera = Invoke-RestMethod "$radarBase/cameras" -Method Post -Headers $radarOrigin -WebSession $radarSession -ContentType 'application/json' -Body $radarCameraBody
$radarCredential = Invoke-RestMethod "$radarBase/cameras/$($radarCamera.id)/device-credentials" -Method Post -Headers $radarOrigin -WebSession $radarSession -ContentType 'application/json' -Body '{}'
$radarWorkerHeaders = @{ Authorization = "Bearer $($radarCredential.token)" }
$radarCamera | Select-Object id, name, type
```

## Evento SIMULATED e reenvio idêntico

```powershell
$radarEvent = Get-Content packages/contracts/fixtures/event-simulated.json -Raw | ConvertFrom-Json
$radarEvent.eventId = [guid]::NewGuid().ToString()
$radarEvent.episodeId = [guid]::NewGuid().ToString()
$radarEvent.runId = [guid]::NewGuid().ToString()
$radarEvent.cameraId = $radarCamera.id
$radarEvent.detectedAt = [DateTime]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ss.fff'Z'")
$radarEvent.occurredAt = [DateTime]::UtcNow.AddSeconds(-2).ToString("yyyy-MM-ddTHH:mm:ss.fff'Z'")
$radarEventBody = $radarEvent | ConvertTo-Json -Depth 10 -Compress
$radarFirstHttp = Invoke-WebRequest "$radarBase/edge/events" -UseBasicParsing -Method Post -Headers $radarWorkerHeaders -ContentType 'application/json' -Body $radarEventBody
$radarFirst = $radarFirstHttp.Content | ConvertFrom-Json
if ($radarFirstHttp.StatusCode -ne 201 -or $radarFirst.duplicate -or $radarFirst.deliveryClass -ne 'TEST') { throw 'Evento novo divergente do contrato.' }
1..10 | ForEach-Object {
    $radarRepeatHttp = Invoke-WebRequest "$radarBase/edge/events" -UseBasicParsing -Method Post -Headers $radarWorkerHeaders -ContentType 'application/json' -Body $radarEventBody
    $radarRepeat = $radarRepeatHttp.Content | ConvertFrom-Json
    if ($radarRepeatHttp.StatusCode -ne 200 -or -not $radarRepeat.duplicate -or $radarRepeat.incidentId -ne $radarFirst.incidentId) { throw 'Reenvio divergente do contrato.' }
}
$radarIncidentId = $radarFirst.incidentId
$radarIncident = Invoke-RestMethod "$radarBase/incidents/$radarIncidentId" -WebSession $radarSession
if ($radarIncident.status -ne 'OPEN' -or $radarIncident.version -ne 1) { throw 'Incidente inicial divergente.' }
$radarIncident | Select-Object id, mode, kind, deliveryClass, status, review, version
```

Esperado: primeira resposta 201; dez reenvios 200 com o mesmo incidente, sem
nova urgência. `mode: SIMULATED`, `deliveryClass: TEST`, `status: OPEN`, versão 1.

## Ações, revisão e resultado idempotente

```powershell
$radarRecognizeBody = @{ actionId = [guid]::NewGuid().ToString(); expectedVersion = 1; action = 'RECOGNIZE' } | ConvertTo-Json -Compress
$radarRecognized = Invoke-RestMethod "$radarBase/incidents/$radarIncidentId/actions" -Method Post -Headers $radarOrigin -WebSession $radarSession -ContentType 'application/json' -Body $radarRecognizeBody
if ($radarRecognized.status -ne 'ACKNOWLEDGED' -or $radarRecognized.version -ne 2) { throw 'Reconhecimento divergente.' }
$radarStartBody = @{ actionId = [guid]::NewGuid().ToString(); expectedVersion = 2; action = 'START_RESPONSE' } | ConvertTo-Json -Compress
$radarStarted = Invoke-RestMethod "$radarBase/incidents/$radarIncidentId/actions" -Method Post -Headers $radarOrigin -WebSession $radarSession -ContentType 'application/json' -Body $radarStartBody
if ($radarStarted.status -ne 'IN_PROGRESS' -or $radarStarted.version -ne 3) { throw 'Atendimento registrado divergente.' }
$radarResolveBody = @{ actionId = [guid]::NewGuid().ToString(); expectedVersion = 3; action = 'RESOLVE'; review = 'PERSON_ON_FLOOR_CONFIRMED'; outcome = 'TEST_COMPLETED' } | ConvertTo-Json -Compress
$radarResolved = Invoke-RestMethod "$radarBase/incidents/$radarIncidentId/actions" -Method Post -Headers $radarOrigin -WebSession $radarSession -ContentType 'application/json' -Body $radarResolveBody
$radarOriginalAgain = Invoke-RestMethod "$radarBase/incidents/$radarIncidentId/actions" -Method Post -Headers $radarOrigin -WebSession $radarSession -ContentType 'application/json' -Body $radarRecognizeBody
if ($radarOriginalAgain.version -ne 2 -or $radarOriginalAgain.status -ne 'ACKNOWLEDGED') { throw 'Ação repetida perdeu o resultado original.' }
$radarNoteBody = @{ actionId = [guid]::NewGuid().ToString(); expectedVersion = 4; action = 'ADD_NOTE'; note = 'Teste HTTP sintético concluído.' } | ConvertTo-Json -Compress
$radarNoted = Invoke-RestMethod "$radarBase/incidents/$radarIncidentId/actions" -Method Post -Headers $radarOrigin -WebSession $radarSession -ContentType 'application/json; charset=utf-8' -Body ([Text.Encoding]::UTF8.GetBytes($radarNoteBody))
$radarFinal = Invoke-RestMethod "$radarBase/incidents/$radarIncidentId" -WebSession $radarSession
if ($radarFinal.status -ne 'RESOLVED' -or $radarFinal.version -ne 5 -or $radarFinal.outcome -ne 'TEST_COMPLETED') { throw 'Estado final divergente.' }
$radarFinal | Select-Object id, kind, status, review, outcome, version
```

Esperado: versões 2, 3 e 4 nas três transições. O reenvio do reconhecimento
continua retornando a versão 2 original. Nota final gera versão 5 sem reabrir.
Isso registra um teste, não atendimento real ou diagnóstico de queda.

## Auditoria e exatamente um aviso local

```powershell
$radarAudit = Invoke-RestMethod "$radarBase/audit?incidentId=$radarIncidentId&limit=100" -WebSession $radarSession
$radarActionAudit = @($radarAudit.items | Where-Object { $null -ne $_.incidentAction })
if ($radarActionAudit.Count -ne 4) { throw 'Auditoria repetiu ou perdeu ação.' }
$radarAudit.items | Select-Object action, fromVersion, toVersion, createdAt
function Get-RadarNotifications {
    $radarCursor = $null
    do {
        $radarPath = "$radarBase/notifications?limit=100"
        if ($radarCursor) { $radarPath += '&cursor=' + [Uri]::EscapeDataString($radarCursor) }
        $radarPage = Invoke-RestMethod $radarPath -WebSession $radarSession
        $radarPage.items
        $radarCursor = $radarPage.nextCursor
    } while ($radarCursor)
}
$radarFound = @()
for ($radarAttempt = 0; $radarAttempt -lt 25; $radarAttempt++) {
    $radarFound = @(Get-RadarNotifications | Where-Object { $_.intent.incidentId -eq $radarIncidentId })
    if ($radarFound.Count -gt 0) { break }
    Start-Sleep -Milliseconds 200
}
if ($radarFound.Count -ne 1 -or $radarFound[0].channel -ne 'SIMULATED' -or $radarFound[0].urgent) { throw 'Aviso local ausente, duplicado ou urgente indevidamente.' }
$radarFound | Select-Object channel, urgent, message, createdAt
Invoke-RestMethod "$radarBase/device-credentials/$($radarCredential.id)" -Method Delete -Headers $radarOrigin -WebSession $radarSession | Out-Null
$radarWorkerHeaders = $null
$radarCredential = $null
Write-Output 'Validação HTTP da etapa 02: ok.'
```

<!-- smoke:end -->

Esperado: quatro ações auditadas e um aviso `SIMULATED`, `urgent: false`.
A credencial exclusiva é revogada ao final; os registros de teste ficam visíveis
e identificados no banco. Se interromper o roteiro antes da revogação, execute
o `DELETE` enquanto `$radarCredential` ainda estiver disponível. Não imprima o token.

## Verificação automatizada completa

```powershell
. ./scripts/activate.ps1
pnpm.cmd test:contracts
pnpm.cmd test:api
pnpm.cmd lint
pnpm.cmd typecheck
pnpm.cmd build
pnpm.cmd lint:edge
pnpm.cmd check:edge
```

`test:api` cria seu próprio container/banco/volume, aplica as duas migrações,
executa primeiro os testes anteriores e depois os da etapa 02, removendo apenas
o recurso exclusivo de testes. Concorrência, 409/410/422, rollback, isolamento e
heartbeat com relógio controlado são conferidos nessa suíte. Nenhuma câmera é
necessária. Consulte os resultados registrados no [relatório 02](RELATORIOS/ETAPA_02.md).
