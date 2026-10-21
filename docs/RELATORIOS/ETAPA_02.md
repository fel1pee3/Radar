# Etapa 02 — Eventos, incidentes e contratos

Data: 21/10/2026.
Status: **CONCLUÍDA**.
Ambiente: Windows 11 Pro 10.0.26200 x64; PowerShell 5.1.26100.9711;
AMD Ryzen 5 5625U, 6 núcleos/12 threads, 15,4 GiB de RAM. Node 24.22.1,
pnpm 10.34.7, Python 3.12.15, uv 0.13.4; Docker Engine 29.1.3/Compose 5.0.1,
PostgreSQL 17.11. Nenhuma câmera aberta, modelo carregado ou inferência executada.
Base local: `f43dacb`, branch `main`. Árvore limpa no início; alterações desta
etapa permanecem sem commit/push/deploy, conforme solicitado.

## Resultado entregue

Um evento autenticado de worker gera, após commit, um recibo, um incidente OPEN,
auditoria e intenção de aviso persistida. Reenvios, inclusive concorrentes,
retornam o mesmo incidente; conflitos não modificam o original. O executor Nest
registra um aviso no canal SIMULATED, sem comunicação externa, e retoma pendências
na inicialização. Usuários OWNER/OPERATOR consultam incidentes e executam ações
auditadas com idempotência e controle de versão.

Heartbeat tem sequência, lease de 15 segundos e proteção contra regressão de run.
Saúde é calculada na leitura pelo horário de recepção do servidor e inclui idade
e stale. Modo da fonte, classe de entrega, estado operacional, revisão humana e
desfecho permanecem campos distintos.

JSON Schemas, tipos TS gerados, exemplos e validação Python compartilham a mesma
fonte de dados. Os exemplos são sintéticos. O roteiro PowerShell publicado foi
executado por HTTP real em ambiente exclusivo de testes.

## Arquivos e decisões

| Área | Arquivos e finalidade |
| --- | --- |
| Contratos | `packages/contracts/src/schemas/*.json`, `src/generated/*.ts`, `src/validation.ts`, `src/index.ts`; `fixtures/cases.json`, `fixtures/event-simulated.json`, `scripts/generate-types.mjs` e `test/fixtures.test.mjs` |
| Python | `services/edge/src/radar_edge/contracts.py`, `tests/test_contracts.py`, `pyproject.toml` e `uv.lock`; apenas validação/diagnóstico |
| Banco | `apps/api/prisma/schema.prisma` e `migrations/20261021000200_events_incidents/migration.sql`; migração inicial preservada |
| API | Novos `event-support.ts`, `ingest.ts`, `heartbeat.ts`, `incidents.ts`, `notifications.ts`; integração em `app.module.ts`, `application.ts`, `catalog.ts`; exportação do tipo DeviceRequest em `devices.ts` e tipo numérico explícito para limit em `dto.ts` |
| Testes/scripts | `apps/api/test/events.test.mjs`, atualização da expectativa de migrações em `access.test.mjs`, ordem explícita em `scripts/test-api.mjs`; scripts em manifests e globals do ESLint |
| Documentação | `README.md`, `docs/03_CONTRATOS_E_DADOS.md`, `08_AMBIENTE_E_COMANDOS.md`, `09_DECISOES_E_FUTURO.md`, `OPENAPI.json`, `STATUS.md`, `VALIDACAO_MANUAL_ETAPA_02.md`, índice de relatórios, inventário e este relatório |
| Locks | `pnpm-lock.yaml`, `services/edge/uv.lock`; versões anteriores preservadas |

A migração é aditiva: cria EventReceipt, Incident, IncidentAction,
NotificationIntent, NotificationDelivery, CameraRun e enums; amplia Camera e
AuditEntry. Unicidades protegem `(deviceId,eventId)`, `(cameraId,episodeId)`,
`(tenantId,actionId)` e entrega/intenção por incidente. FKs compostas impedem
relações entre tenants. Índices atendem listas, auditoria e intenções pendentes.
Não houve reset, `db push`, parada/limpeza do banco da demonstração ou acesso ao
PostgreSQL preexistente da porta 5432.

Recibos mantêm payload anulável, hash, chave e expiredAt; relação com incidente
pode ser anulada explicitamente na purga futura. Payload de ação e sinais/pose/
versões de incidente também permitem redação. FKs RESTRICT exigem purga explícita,
evitando apagar chaves de deduplicação por cascata. Não há rotina de retenção
automática nesta etapa.

Decisões registradas como D19–D22 em [09](../09_DECISOES_E_FUTURO.md):

- Draft-07 compartilhado com Ajv/jsonschema; tipos gerados e validação de calendário,
  finitude e índices únicos de pose. Limites concretos estão em [03](../03_CONTRATOS_E_DADOS.md).
- Hash SHA-256 de JSON com chaves ordenadas recursivamente; não se declara RFC 8785.
  Episódio equivalente inclui todos os campos exceto eventId, inclusive runId.
  ActionId único por tenant inclui o incidente no hash e preserva resultado original.
- Bloqueio da câmera para ingestão/heartbeat; advisory lock de actionId e bloqueio
  de incidente para ações. Restrições no banco complementam os locks.
- CameraRun guarda somente IDs/horários de runs aposentados; não há histórico de
  payloads de heartbeat. ENDED fecha o run. PAUSED/SOURCE_ENDED persistidos sempre
  expõem idade/stale, sem afirmar que o processo continua ligado.
- Executor com polling de um segundo, recuperação na inicialização e SKIP LOCKED.
  Entrega, auditoria e status são atômicos. Falha deixa PENDING para retry; não há
  backoff exponencial. attempts conta processamentos com commit.
- OpenAPI declara 3.1 para incorporar os schemas com const/condições; bearerFormat
  foi corrigido de JWT para opaque. O tipo de limit passou a Number no OpenAPI.
- API gera contratos/client no prebuild/dev/typecheck, evitando depender de saídas
  antigas. Testes de acesso executam antes dos novos, preservando sua verificação
  de banco vazio. A expectativa passou de uma para duas migrações concluídas.

Dependências diretas novas, fixadas: Ajv 8.20.0, ajv-formats 3.0.1,
json-schema-to-typescript 16.0.0 (dev), jsonschema 4.26.0 e pytest 9.1.1 (dev).
Metadados oficiais e termos declarados constam no
[inventário](DEPENDENCIAS_E_MODELOS.md). Nenhuma família anterior foi trocada;
opencv-contrib-python segue como único fornecedor de cv2. Ambiente Python com
41 pacotes após as adições.

## Verificações reais

Comandos abaixo foram executados na raiz, salvo os encapsulados por `--filter`.
Inspeções de leitura foram agrupadas; comandos de reprodução na seção seguinte
podem incluir preparação não necessária num ambiente já iniciado.

| Comando/ação executada | Resultado observado | Evidência/limitação |
| --- | --- | --- |
| `git status --short`, `git log -1`, inventário com `rg --files` e leitura dos documentos/código/testes | Base e arquivos confirmados; sem alterações iniciais do fundador | Não foi presumida implementação só pela documentação |
| `Get-CimInstance Win32_OperatingSystem`, `Get-CimInstance Win32_Processor`; versões Node/pnpm/Python/uv/Docker/Compose | Ambiente indicado acima | Sem benchmark de GPU/visão |
| `. ./scripts/activate.ps1` | Ferramentas portáteis disponíveis em cada shell | Evita o erro anterior de pnpm.cmd em terminal sem ativação |
| `pnpm.cmd view ajv@8.20.0 version license`, `pnpm.cmd view ajv-formats@3.0.1 version license`, `pnpm.cmd view json-schema-to-typescript@16.0.0 version license`; metadados PyPI | Versões exatas e licenças declaradas consultadas | Não é auditoria integral de transitivos |
| `pnpm.cmd install --frozen-lockfile` | Lock consistente; instalação concluída | Avisos de scripts @scarf/scarf e @parcel/watcher bloqueados já documentados na 01 |
| `uv sync --project services/edge --frozen` | Ambiente sincronizado pelo lock | Atualização de metadados do pacote local recompilou seu editable, sem trocar dependências de visão |
| `pnpm.cmd --filter @radar/api exec prisma format`, `pnpm.cmd --filter @radar/api exec prisma generate`, `pnpm.cmd --filter @radar/api exec tsc --noEmit` | Schema/client e tipos aprovados após correções | Prisma 7.10.1 preservado |
| `pnpm.cmd --filter @radar/api exec prisma migrate diff --from-schema ../../.local/etapa02/schema-before.prisma --to-schema prisma/schema.prisma --script --output prisma/migrations/20261021000200_events_incidents/migration.sql` | SQL aditivo gerado e inspecionado | Cópia anterior obtida de HEAD sem BOM; artefato temporário ignorado |
| `pnpm.cmd contracts:generate` e `pnpm.cmd test:contracts` | Tipos coerentes com schemas; **87 TS + 87 Python aprovados** | 86 exemplos compartilhados e um caso adicional não finito em cada linguagem |
| `pnpm.cmd test:api` | **19 testes anteriores + 104 novos aprovados** | Duas migrações em PostgreSQL 17.11 vazio exclusivo; recursos removidos ao final |
| Blocos HTTP do roteiro PowerShell executados pelo teste de integração | Evento 201; dez reenvios 200; ações/resultado original, auditoria e um aviso SIMULATED | Nest escutando em porta efêmera real; PowerShell 5.1; credenciais sintéticas em env/sessão privada, sem impressão de token |
| `pnpm.cmd lint` | ESLint e Prettier aprovados | Sem reduzir regras para passar |
| `pnpm.cmd build` | Contratos, NestJS e Next.js compilados | Web continua mínima, sem UI de incidentes |
| `pnpm.cmd typecheck` | Todos os projetos aprovados | Sem depender de contratos/client antigos |
| `pnpm.cmd lint:edge` | Ruff check/format aprovados | Python limitado a contratos/diagnóstico |
| `pnpm.cmd check:edge` | Imports reais MediaPipe 1.1.1, cv2 5.0.0 e PoseLandmarker aprovados; somente opencv-contrib-python fornece cv2 | model_loaded=false, camera_opened=false, inference_executed=false |
| `pnpm.cmd db:migrate`, `pnpm.cmd --filter @radar/api exec prisma migrate status` | Migração 02 aplicada em radar:15432; banco atualizado | Migração 01 preservada; nenhum reset ou seed novo na demo |
| Verificador local `.local/etapa02/preserve-demo.mjs before/after` com Node e env privado | Um usuário/OWNER ativo, um local, duas câmeras, zero credenciais; IDs/estado anteriores preservados | Não leu e-mail, senha ou passwordHash; script/snapshot temporários fora do Git |
| `docker inspect --format '{{json .Mounts}}' radar-postgres-1` antes/depois | Mesmo volume `radar_postgres_data` | Apenas leitura de mounts, sem inspecionar environment privado |
| `pnpm.cmd openapi:generate` | `docs/OPENAPI.json` regenerado com endpoints e três schemas | Disponível também em `/v1/openapi.json` |
| `Invoke-WebRequest` em 3001 `/v1/health/live`, `/v1/health/ready`, 3000 `/api/health/ready` e `/` | HTTP 200 nos quatro; health status ok | Processos existentes preservados; sem login com senha pessoal |
| `Get-NetTCPConnection -State Listen -LocalPort 5432,15432,3000,3001`, `docker ps` | Demo em loopback15432; PostgreSQL preexistente continuou escutando5432 | Sem conexão ou alteração ao banco5432 |
| `git diff --check` e revisão final de arquivos/artefatos | Sem erro de whitespace; sem configurações privadas ou mídia no conjunto versionável | Sem commit/push/deploy |

## Critérios da etapa

| Critério | Situação | Evidência |
| --- | --- | --- |
| Regressão anterior | VERIFICADO | 19/19, incluindo seed, RBAC, rotação, perda/retomada do banco e logs |
| Compatibilidade TS/API/Python | VERIFICADO | Mesmos 86 exemplos; 87 testes por linguagem; ContractPipe da API exercitado nos mesmos exemplos, inválidos também por HTTP |
| Reenvio dez vezes concorrente/sequencial | VERIFICADO | Uma resposta 201, demais 200; um incidente/recibo/intenção/entrega; dez eventIds equivalentes também serializados |
| Hash canônico e conflitos | VERIFICADO | Ordem de chaves alterada aceita; kind/runId/modo/sinais conflitantes recusados, original inalterado |
| Atomicidade | VERIFICADO | Triggers que lançam exceção no PostgreSQL exclusivo comprovam rollback de criação, ação e aviso/auditoria; retry posterior passa |
| Atualidade | VERIFICADO | TEST, CURRENT, DELAYED, CLOCK_UNCERTAIN; fronteiras 30 s/120 s/30 dias/24 h; timestamps originais, reenvio após31 dias e tombstone410 |
| Ações humanas | VERIFICADO | Seis ações; estados finais; notas e revisão/desfecho separados; dez ações iguais concorrentes, versão desatualizada, actionId conflitante e resultado original após avanço |
| Segurança/tenant/câmera | VERIFICADO | Dois tenants; outra câmera do mesmo tenant; sessão/bearer separados; Origin/RBAC; credencial revogada; FKs compostas/uniquidades diretamente no banco |
| Paginação/filtros/auditoria | VERIFICADO | Cursor com timestamps iguais sem repetição; filtros e intervalo; histórico de notas/versões e scoping |
| Heartbeat | VERIFICADO | Relógio injetado; sequência antiga sem renovar lease; fronteira15000ms, conflito/troca, run aposentado, cinco estados, pausa/fim stale, sentAt não controla saúde, evento não altera run |
| Aviso durável e retomável | VERIFICADO | Nova instância Nest lê intenção pendente; concorrência de executores; rollback de entrega/auditoria; repetição após marcar PENDING não duplica entrega |
| Logs sem segredos | VERIFICADO | Senhas/cookies/tokens/hashes de credenciais sintéticos ausentes de logs/auditoria; nota de teste não aparece no log técnico; saída PowerShell sem segredos |
| Ambiente e ferramentas | VERIFICADO | Frozen locks, lint, typecheck, build, Ruff e imports reais aprovados |
| Preservação local | VERIFICADO | Migração aditiva; OWNER/cadastros/volume preservados; porta5432 intocada |

## Como reproduzir

Na raiz, PowerShell:

```powershell
. ./scripts/activate.ps1
pnpm.cmd install --frozen-lockfile
uv sync --project services/edge --frozen
pnpm.cmd setup:env
pnpm.cmd infra:up
pnpm.cmd db:generate
pnpm.cmd db:migrate
pnpm.cmd test:contracts
pnpm.cmd test:api
pnpm.cmd lint
pnpm.cmd typecheck
pnpm.cmd build
pnpm.cmd lint:edge
pnpm.cmd check:edge
```

Inicie em terminais separados, ativando em ambos:

```powershell
. ./scripts/activate.ps1
pnpm.cmd dev:api
```

```powershell
. ./scripts/activate.ps1
pnpm.cmd dev:web
```

Execute os blocos do [roteiro manual](../VALIDACAO_MANUAL_ETAPA_02.md) em um
terceiro terminal: login com senha mascarada, câmera lógica nova, credencial
privada em variável, evento SIMULATED, reenvio, consultas, ações, auditoria,
aviso único e revogação da credencial exclusiva. O proprietário atual já existe;
nada exige recriá-lo ou conhecer sua senha durante os testes automatizados.

## Falhas, limites e pendências

Falhas encontradas e corrigidas durante a implementação:

- Interop ESM/CommonJS de Ajv/ajv-formats e tipagem Json/SchemaObject: corrigidas
  importação/chamada e representação do heartbeat; OpenAPI usa cast explícito de
  schema draft-07 em documento3.1, pois Nest ainda tipa esse campo como OAS3.0.
- Prisma recusou BOM na cópia temporária do schema anterior; cópia refeita com
  bytes de `git show`, e migração gerada/aplicada com sucesso.
- Primeira suíte nova: 101/103 passaram. Dois testes faziam chamadas divergentes:
  RESOLVE com note extra (422 corretamente) e POST de revogação inexistente (404).
  Corrigidos os testes para o contrato existente, sem permitir campos ou rotas
  extras. Nova execução:103/103. Inclusão do teste PowerShell:104/104.
- Uma inspeção Docker com template contendo aspas perdeu escaping no PowerShell;
  substituída por `{{json .Mounts}}` e seleção de propriedades, sem dados privados.

**Nenhum requisito obrigatório da etapa 02 pendente ou bloqueado.** O login com
a senha pessoal do fundador não foi repetido; autenticação e roteiro passaram
com credenciais sintéticas isoladas. A migração e health/proxy foram verificados
na demonstração sem inserir incidentes artificiais nela. O roteiro fica disponível
para o fundador repetir com sua conta.

O teste de retomada cria outra instância Nest com o mesmo PostgreSQL de testes;
não simula queda do sistema operacional ou corte físico de energia. O teste de
indisponibilidade da etapa01 para/reinicia somente seu container exclusivo.
Não se mediram capacidade, latência sob carga, FPS ou eficácia de detecção.

Painel/login visual, simulador de demonstração, captura, produtor Python de
heartbeat, motor temporal, outbox SQLite, snapshot e retenção automática não
integram esta etapa. Não há evidência de câmera/IA nem envio a contatos reais.
Avisos conhecidos de VM modules do Jest e scripts de dependências bloqueados
continuam explícitos. Nenhuma dependência de sistema ou ação do fundador foi
necessária para completar as verificações obrigatórias desta etapa.

## Próxima etapa elegível

03 — Painel e primeira demonstração, somente mediante nova solicitação.
Nenhuma implementação dessa etapa foi iniciada. Não foi feito commit, push ou deploy.
