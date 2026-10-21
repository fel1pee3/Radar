# Etapa 01 — Domínio, banco e acesso

Data: 21/10/2026, America/Sao_Paulo.
Status: **CONCLUÍDA** — implementação, verificações automatizadas e
provisionamento do proprietário real confirmados.
Ambiente: Windows 11 Pro x64, Ryzen 5 5625U, 15,4 GiB RAM visível;
Node 24.22.1, pnpm 10.34.7, Nest 11.2.7, PostgreSQL 17.11;
Docker Engine 29.1.3, Compose 5.0.1. Python/visão preservados, sem execução nesta etapa.
Revisão inicial: `1d35e36`, main limpa na inspeção. Sem commit, push ou deploy nesta solicitação.

## Resultado entregue

API NestJS ESM integrada ao PostgreSQL via Prisma 7.10.1, client gerado em output
explícito, adapter-pg e pg com pool/timeouts. Migração versionada
`20261021000100_initial_access` aplicada em banco vazio exclusivo de teste e no
banco de demonstração em 127.0.0.1:15432. Segunda execução não encontrou pendências.
Nenhum comando `db push`, reset ou limpeza foi executado na demonstração.

Domínio: Tenant, User, Session, Site, Camera, Device e DeviceCredential; mais
AuditEntry mínimo para autenticação/provisionamento/configuração/credenciais.
FKs compostas conferem tenant em sessão/usuário, câmera/local, device/câmera,
credencial/device e ator de auditoria/usuário. Há unicidade de um Device por câmera.

Login/logout/me reais, Argon2id, sessões opacas de oito horas com hash, revogação,
cookie HttpOnly/Lax/Path=/ e exceção HTTP explícita de desenvolvimento em loopback.
Validação de Origin cobre login e mutações com sessão; limiter local e corpo JSON
limitado. Papéis OWNER/OPERATOR com leituras autenticadas e configuração somente OWNER.

Worker usa bearer separado da sessão, token aleatório mostrado uma vez e hash no
banco. Rotação serializa atualização do Device, revoga anteriores e incrementa
versão sem trocar identidade. `GET /edge/me` comprova autenticação/escopo sem
antecipar ingestão de eventos/heartbeat. Readiness consulta o banco de verdade;
liveness mantém resposta independente do banco.

O seed é idempotente, preserva senha/IDs/dados editados e rejeita criar outro
proprietário no mesmo tenant ao mudar o e-mail. CLI de operador explícita, sem
cadastro público. Há prompts locais mascarados e alternativa por configuração
privada. O fundador executou o provisionamento local após ser orientado a não
enviar a senha pelo chat. A consulta final confirmou um proprietário ativo e um
registro OWNER_BOOTSTRAPPED, usando apenas contagens, sem ler senha ou hash da
conta real. As contagens anteriores eram zero; nenhuma senha foi inventada.

## Arquivos e decisões

| Área | Arquivos / alteração |
| --- | --- |
| Prisma | `apps/api/prisma/schema.prisma`, `prisma.config.ts`, `prisma/migrations/20261021000100_initial_access/migration.sql`, `migration_lock.toml`; oito tabelas, enums, índices e FKs compostas |
| API | `src/database.ts`, `config.ts`, `application.ts`, `app.module.ts`, `main.ts`, `health.controller.ts`; configuração validada, pool, factory para runtime/testes, readiness e OpenAPI |
| Identidade | `src/identity.ts`, `security.ts`, `dto.ts`, `errors.ts`; sessão/bearer separados, guards, Argon2id, DTOs, erros/logs sem stack ou entrada sensível |
| Configuração / worker | `src/catalog.ts`, `pagination.ts`, `devices.ts`; CRUD mínimo, paginação, emissão/rotação/revogação e diagnóstico |
| Provisionamento | `src/bootstrap.ts`, `cli.ts`, `scripts/setup-user.ps1`; seed, operador local, OpenAPI e senha por ambiente do processo, nunca argumento literal |
| Ambiente / scripts | `scripts/setup-env.mjs`, `scripts/test-api.mjs`, manifests/lock, workspace, exemplos, `.gitignore`/lint/formatter; atualização aditiva da configuração e teste isolado |
| Testes | `apps/api/test/access.test.mjs`, `jest.config.mjs`; 19 testes com HTTP e PostgreSQL reais, sem mocks de persistência/auth |
| Documentação | `docs/OPENAPI.json`, `VALIDACAO_MANUAL_ETAPA_01.md`, STATUS, ambiente, arquitetura, contratos, segurança, decisões, inventário e README |

Decisões registradas: D16 padroniza 15432 e bloqueia 5432 do host para evitar o
PostgreSQL preexistente; D17 define e-mail globalmente único normalizado e bootstrap
de um proprietário; D18 explicita os endpoints de detalhe/alteração de local e
diagnóstico de worker. Tipos FILE/WEBCAM/RTSP seguem o source.kind já documentado.
Não há URI, senha de câmera, campos arbitrários de tenant nem falso status online.

Prisma/config/client/adapter usam a família 7 estável, sem adotar 8 RC. Node, Nest,
Next, React, pnpm e Python mantiveram as versões fixadas. Gerados do Prisma ficam
ignorados; SQL de migração é exceção explícita à regra geral de ignorar dumps SQL.
Nenhum teste utilizou o banco/volume da demonstração para limpeza ou parada.

## Verificações reais

| Comando/ação executado | Resultado observado | Evidência/limitação |
| --- | --- | --- |
| `git status --short`, `rg --files`, leituras UTF-8 dos documentos e código | Árvore limpa inicialmente; fundação e ferramentas existentes confirmadas | Inventário antes de editar; leitura do prompt anexado |
| `. ./scripts/activate.ps1`, `node --version`, `pnpm.cmd --version`, `docker version --format '{{.Server.Version}}'`, `pnpm.cmd infra:status`, `Get-NetTCPConnection ...` | Node 24.22.1/pnpm 10.34.7/Engine 29.1.3; banco saudável em 15432; API/web já ativas | Não interrompidos os processos do fundador nem PostgreSQL externo |
| Consultas de metadados oficiais npm e documentação Prisma/Nest/Argon2 | Versões estáveis/engines/peers/licenças conferidos | Versões e fontes no inventário; sem tags latest |
| `pnpm.cmd --filter @radar/api add ...` e `add -D ...` | Dependências instaladas e lock atualizado | Native argon2 carregou; scripts scarf/parcel não aprovados |
| `pnpm.cmd setup:env` | Complementou somente configuração ausente da API; DSN derivada do `.env` raiz | Sem imprimir senha, sem substituir valores preenchidos; validação de idempotência ao final |
| `pnpm.cmd db:generate` | Client 7.10.1 gerado em `src/generated/prisma` | Primeiro schema apontou unicidade composta ausente em Device/camera; corrigida e geração passou |
| `pnpm.cmd --filter @radar/api exec tsc --noEmit` | Aprovado | ESM/NodeNext, imports com extensão .js |
| `pnpm.cmd --filter @radar/api exec prisma format` | Schema formatado | Gerador prisma-client, datasource sem URL no schema |
| `pnpm.cmd --filter @radar/api exec prisma migrate diff --from-empty --to-schema prisma/schema.prisma --script --output prisma/migrations/20261021000100_initial_access/migration.sql` | Migração SQL real gerada e inspecionada | Somente criação de schema/enums/tabelas/índices/FKs; sem reset ou db push |
| `pnpm.cmd test:api`, primeira execução | 16 passaram, dois falharam após reinício do container de teste | Porta automática e dados tmpfs não eram adequados à restauração; corrigida a infraestrutura sem reduzir testes |
| `pnpm.cmd test:api`, após correção | 18/18 aprovados | Container exclusivo com porta estável e volume anônimo próprio, removidos no finally |
| `pnpm.cmd test:api`, com teste de CLI e regra de bootstrap adicional | 19/19 aprovados | Migração em banco vazio, seed, sessão, Origin, limiter, papéis, dois tenants, FKs diretas, concorrência, revogação, parada/retomada e logs |
| `pnpm.cmd db:migrate` duas vezes; `pnpm.cmd --filter @radar/api exec prisma migrate status` | Primeira aplicou migração na demo; segunda sem pendências; schema atualizado | Banco `radar` em 127.0.0.1:15432; volume preservado |
| `Invoke-RestMethod` em `/v1/health/live`, `/v1/health/ready` e web `/api/health/ready` | Todos retornaram `status: ok` | Processos reais já abertos pelo fundador; proxy da web preservado |
| `pnpm.cmd openapi:generate` | `docs/OPENAPI.json` gerado da aplicação | JSON servido em /v1/openapi.json; sem UI extra |
| `pnpm.cmd install --frozen-lockfile` | Aprovado, sem nova resolução | Locks preservados após instalação |
| `pnpm.cmd format`, `pnpm.cmd lint`, `pnpm.cmd typecheck`, `pnpm.cmd build` | Aprovados no workspace | Inclui web/contratos preservados e API com prebuild Prisma |
| Parser PowerShell `Language.Parser.ParseFile` em `scripts/setup-user.ps1` | Sintaxe válida | Teste CLI não interativo real também coberto; senha do fundador não foi recebida no chat |
| Consultas locais Prisma somente de contagem de OWNER/registro OWNER_BOOTSTRAPPED | Inicialmente 0/0; consulta final 1/1 após execução local do fundador | Proprietário real confirmado; nenhum e-mail, senha ou hash dessa conta incluído em saída/relatório |
| Script Node de SHA-256 dos três `.env`, execução de `scripts/setup-env.mjs` e comparação | Arquivos privados idênticos antes/depois da repetição | Confirma idempotência após atualização aditiva inicial, sem imprimir valores privados |
| Script de verificação dos 92 candidatos obtidos por `git ls-files --cached --others --exclude-standard -z`, `git check-ignore ...`, `git diff --check` | Nenhuma credencial privada detectada nos candidatos; gerados/ambientes ignorados, migração SQL incluída; diff sem erros de espaço | Comparação sem imprimir os valores privados; sem git add/commit/push |
| `docker ps --format ...`, `Get-NetTCPConnection -State Listen -LocalPort 5432,15432,3000,3001` | Somente container da demo permaneceu; healthy em 15432; web/API em loopback; PostgreSQL preexistente preservado em 5432 | Recursos exclusivos de testes foram removidos, nenhum reset/limpeza da demo |

Os testes usam dados/e-mails/senhas sintéticos gerados localmente. As credenciais
do banco de testes são aleatórias e passam via ambiente, sem aparecer na linha de
comando. A suíte não exporta dumps ou logs com payloads e remove seus próprios
recursos; nomes/portas mudam a cada execução. A leitura de logs usa segredos-sentinela,
tokens emitidos, hashes e URI fictícia para verificar ausência de vazamentos.

## Critérios da etapa

| Critério | Situação | Evidência |
| --- | --- | --- |
| Prisma 7, migração em banco vazio e migração da demo | Verificado | Migrate deploy real nos dois bancos; status sem pendências |
| Seed repetido não duplica/apaga/sobrescreve senha | Verificado | Integração de função e CLI reais, preservando IDs/hash/site editado e rejeitando troca de escopo/e-mail |
| Login/logout/expiração/credencial inválida/Origin | Verificado | HTTP real, sessões persistidas e expiração sintética no banco exclusivo |
| OWNER/OPERATOR e isolamento entre tenants | Verificado | Leituras/alterações/referências HTTP e cinco relações cruzadas bloqueadas por FK no PostgreSQL |
| Worker: emissão única, rotação, revogação, Device estável | Verificado | Tokens armazenados como hash; rotação concorrente; token anterior 401 e bearer separado de sessão |
| Readiness indisponível e recuperação sem afetar demonstração | Verificado | Container de teste parado/iniciado; readiness 503, liveness 200, depois recuperação 200 |
| Segredos ausentes de logs/auditoria | Verificado | Sentinelas e tokens/hashes emitidos comparados aos registros capturados |
| Build/lint/typecheck e OpenAPI | Verificado | Comandos reais e contrato gerado |
| Proprietário real da demonstração criado com credenciais do fundador | Verificado | Execução local de setup:owner; consulta final de contagem confirmou OWNER ativo e auditoria, sem receber senha no chat |
| Documentação de estado e reprodução | Verificado | Este relatório, STATUS, inventário e roteiro manual |

## Como reproduzir

Na raiz, em PowerShell:

```powershell
. ./scripts/activate.ps1
pnpm.cmd install --frozen-lockfile
pnpm.cmd setup:env
pnpm.cmd infra:up
pnpm.cmd db:generate
pnpm.cmd db:migrate
pnpm.cmd setup:owner
pnpm.cmd test:api
pnpm.cmd lint
pnpm.cmd typecheck
pnpm.cmd build
```

Em terminais separados, cada um ativado: `pnpm.cmd dev:api` e `pnpm.cmd dev:web`.
Não é necessário iniciar o processo da API da demonstração para `test:api`; a suíte
abre sua própria API compilada em porta efêmera de loopback.

Use o [roteiro manual PowerShell](../VALIDACAO_MANUAL_ETAPA_01.md) para login pelo
proxy, sessão sem exposição da senha, configuração, token em variável privada,
rotação/revogação, Origin externa, logout e operador. Esperados: login/me/leitura
200, criação 201, logout/revogação 204, inválido/expirado/revogado 401, Origin ou
papel proibidos 403, recurso de outro tenant 404, limitação de login 429 e readiness
503 durante indisponibilidade do banco exclusivo.

## Falhas, limites e pendências

- Falhas iniciais de unicidade do schema e restauração do container de testes
  foram corrigidas e os mesmos requisitos foram novamente verificados.
- Limitação de login é em memória para uma instância local e reinicia com o
  processo; não é um limitador distribuído. Nenhum serviço externo foi adicionado.
- Exceção HTTP vale somente na bancada de desenvolvimento em loopback. Não houve
  implementação/teste de TLS remoto, SaaS, cadastro público ou recuperação de senha.
- Avisos de ESLint 9/glob transitivo/VM modules do Jest permanecem documentados.
  Sem atualização silenciosa de famílias. Scripts de telemetria não foram autorizados.
- Owner real criado localmente pelo fundador. Nenhuma senha padrão, conta inventada
  ou senha recebida pelo chat foi usada. A validação dos fluxos de autenticação
  foi automatizada com usuários sintéticos em banco exclusivo; não solicitamos
  nem testamos a senha pessoal do fundador. O roteiro permite validar seu login localmente.
- Nenhuma interface completa de login, incidente, ingestão, detector, heartbeat,
  câmera física ou notificação implementada. `expectedRunning` não comprova captura.
- Os processos e volume de demonstração existentes foram preservados. Só recursos
  exclusivos de teste foram parados/removidos; a porta 5432 não foi utilizada.

## Próxima etapa elegível

Etapa 02 somente mediante nova solicitação do fundador. Nenhum critério obrigatório
da 01 pendente; a 02 não foi iniciada. Não houve commit, push ou deploy nesta etapa.
