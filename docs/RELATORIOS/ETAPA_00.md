# Etapa 00 — Fundação do repositório e ambiente

Data: 21/10/2026 (America/Sao_Paulo).
Status: **CONCLUÍDA** — critérios obrigatórios verificados no ambiente abaixo.
Ambiente: Windows 11 Pro 10.0.26200 x64, PowerShell 5.1.26100.9711;
AMD Ryzen 5 5625U, 6 núcleos/12 threads, 15,4 GiB RAM visível,
AMD Radeon (TM) Graphics. Sem avaliação de GPU, câmera ou inferência.
Revisão inicial: `a61716c` (`first commit`), árvore limpa antes das edições.
Nenhum commit, push ou deploy realizado.

## Resultado entregue

Monorepo pnpm com `apps/web`, `apps/api`, `packages/contracts` e projeto uv separado
em `services/edge`. Next.js exibe uma página mínima em português, com indicação
explícita de que nenhuma fonte de vídeo está em execução. NestJS ESM serve
`GET /v1/health/live` com HTTP 200 e `{"status":"ok"}`. O Next encaminha
`/api/health/live` para a API e a mesma resposta foi verificada.

PostgreSQL 17.11 em Docker Compose com healthcheck, volume `radar_postgres_data`,
senha aleatória privada e publicação somente em loopback. Nesta máquina utiliza
`127.0.0.1:15432`; a instalação PostgreSQL já existente em 5432 foi preservada.
Conexão TCP autenticada e sobrevivência de um registro após remover/recriar o
container foram comprovadas. A tabela sintética de verificação foi removida.

MediaPipe, OpenCV e `mediapipe.tasks.python.vision.PoseLandmarker` importaram no
Python 3.12.15 nativo. A CLI `radar-edge env` verifica imports, versões, fornecedor
único de cv2 e backends compilados. Não carrega modelo nem abre câmera.

## Arquivos e decisões

Inventário inicial: 26 arquivos versionados, apenas `AGENTS.md`, `README.md`,
`docs/` e `etapas/`. Não existiam módulos de software; não havia alterações do fundador.

| Área / arquivos | Alteração |
| --- | --- |
| `package.json`, `pnpm-workspace.yaml`, `pnpm-lock.yaml`, `.npmrc`, `.node-version`, `tsconfig.base.json` | Workspace privado, Node 24, pnpm 10, versões exatas, TypeScript strict; Python fora do workspace |
| `eslint.config.mjs`, `.prettierrc.json`, `.prettierignore` | Lint e formatter reais, preservando a formatação dos documentos originais |
| `apps/web/` | Next 16/React 19/Tailwind 4; página mínima; rewrite local validado; env de exemplo sem segredo e telemetria Next desabilitada |
| `apps/api/` | Nest 11 ESM/NodeNext; liveness; logs JSON; validação de host e porta; scripts dev/build/start |
| `packages/contracts/` | Pacote inicial com tipo da resposta de liveness; schemas e validação entre linguagens ficam na 02 |
| `services/edge/`, `.python-version` | Python 3.12.15, pyproject/uv.lock, pacote instalável e CLI de ambiente; Ruff; build de sdist/wheel verificado |
| `infra/compose.yaml`, `.env.example` | PostgreSQL 17.11, healthcheck, volume e senha privada obrigatória; porta configurável |
| `scripts/setup-env.mjs`, `scripts/activate.ps1` | Geração idempotente de configuração privada; ativação das ferramentas locais somente no terminal atual |
| `.gitignore` | Dependências, ambientes, `.local`, configurações privadas, mídia, modelos, bancos, dumps e builds ignorados; exemplos e locks permitidos |
| README central, docs de arquitetura/ambiente/decisões/status/relatórios | Estado real, comandos existentes e D15; inventário de versões/licenças |

Decisões de implementação:

- Node 22.21.1 e Python 3.13.7 encontrados inicialmente não atendiam às famílias
  escolhidas. Foram preservados. Node 24.22.1 portátil, pnpm 10.34.7 e uv 0.13.4
  estão em `.local/tools`; uv instalou Python 3.12.15 sem alterar o Python padrão.
- Nenhuma alteração global de PATH, firewall ou permissões de webcam foi feita.
  O Docker Desktop instalado foi iniciado por `Start-Process ... -WindowStyle Hidden`.
- D15 registra `POSTGRES_PORT=15432` no `.env` privado desta máquina. O exemplo
  mantém 5432 como padrão; a porta interna continua 5432. Não foi interrompido o
  PostgreSQL preexistente (processo `postgres`, PID 7000 durante o diagnóstico).
- `opencv-contrib-python==5.0.0.93` é o único fornecedor de cv2: atende à dependência
  declarada do MediaPipe 1.1.1 e mantém GUI para a futura prévia local. Wheels Windows
  x64 e imports da combinação foram verificados antes de considerá-la pronta.
- O comando `env` é apenas diagnóstico de bibliotecas. `doctor` e execução do
  worker permanecem para as etapas previstas. Pydantic e HTTPX estão instalados,
  mas não há captura, HTTP de ingestão, detector ou outbox implementados.
- Prisma 7, esquema/migrações, login, readiness e domínio ficam na etapa 01;
  nenhum adaptador de banco simulado foi acrescentado à API.
- ESLint 9.39.5 sinaliza fim de suporte no npm, mas os plugins React/a11y publicados
  não declaram ESLint 10. Foi mantida a família compatível, com lint aprovado e
  aviso registrado no [inventário](DEPENDENCIAS_E_MODELOS.md).
- `agentRules: false` usa uma opção documentada no pacote Next instalado e evita
  gerar outro `AGENTS.md` automaticamente. O arquivo gerado durante o primeiro
  `next dev` foi removido pelo próprio Next após configurar essa opção.

## Verificações reais

Os comandos abaixo foram efetivamente executados. Consultas de registros oficiais
por scripts Python (`python -`), npm e navegador serviram para selecionar versões
estáveis, verificar engines/peers/wheels e registrar licenças; não substituem os testes locais.

| Comando/ação | Resultado observado | Evidência/limitação |
| --- | --- | --- |
| `Get-Location`, `git status --short`, `git status --porcelain=v1`, `git log -1 --format='%h %s'`, `rg --files`, leituras `Get-Content ... -Encoding UTF8` | Raiz correta, árvore limpa e documentação localizada/lida antes de editar | 26 arquivos originais; nenhum software presumido |
| `$PSVersionTable`; `Get-CimInstance Win32_OperatingSystem`, `Win32_Processor`, `Win32_VideoController`; `Get-Command ...` | SO/hardware acima; pnpm e uv ausentes do PATH inicial | GPU apenas identificada; nenhuma câmera consultada |
| `node --version`, `npm.cmd --version`, `corepack.cmd --version`, `python --version`, `py --list-paths`, `git --version` | Inicialmente Node 22.21.1, npm 10.9.4, Corepack 0.34.0, Python 3.13.7, Git 2.50.1.windows.1 | Instalações anteriores preservadas |
| `docker version`, `docker compose version` | Inicialmente daemon indisponível; após iniciar Desktop: Engine 29.1.3 e Compose 5.0.1 | Desktop 4.57.0 já instalado |
| `python -m pip install --target .local/tools/uv uv==0.13.4` | Instalação local aprovada | pip somente para bootstrap do uv |
| Script `python -` de download Node 24.22.1 e SHA-256 | ZIP oficial obtido e hash calculado igual ao checksum oficial | Hash no inventário; extraído em `.local/tools` |
| `npm.cmd install --prefix .local/tools/pnpm --no-package-lock --ignore-scripts pnpm@10.34.7` | Bootstrap local aprovado | npm somente para instalar o gerenciador |
| `.local/tools/uv/bin/uv.exe python install 3.12 --no-bin` | Instalou CPython 3.12.15 | Patch fixado nos dois `.python-version` |
| `. ./scripts/activate.ps1`; `node --version`; `pnpm.cmd --version`; `uv --version` | 24.22.1 / 10.34.7 / 0.13.4 | PATH somente do processo PowerShell atual |
| `npm.cmd view ...` e scripts de leitura de nodejs.org, registro npm, PyPI e Docker Hub | Patches estáveis, engines, peers e wheels conferidos | Lista exata de dependências no inventário e nos manifests; sem tags latest |
| `pnpm.cmd install` | Instalou quatro projetos de workspace e gerou lock | Aviso de ESLint 9 documentado; sem conflito de peers observado |
| `pnpm.cmd install --frozen-lockfile` | Aprovado | Lock preservado, sem nova resolução |
| Instalação com `pnpm --dir .local/lock-repro install --frozen-lockfile` via Node local | Aprovada em diretório vazio com cópias dos manifests/lock | 444 pacotes, reutilizados do cache; sem dependência de node_modules anterior |
| `uv sync --project services/edge` e `uv sync --project services/edge --frozen` | Aprovados; 31 pacotes, uv.lock criado/preservado | `.venv` nativo Windows |
| `UV_PROJECT_ENVIRONMENT=.local/edge-repro` seguido de sync frozen e CLI env | Aprovados em outro ambiente virtual vazio | Imports reais passaram novamente; variável definida somente no processo desse teste |
| `pnpm.cmd setup:env`; repetição por `node scripts/setup-env.mjs` | Criou três arquivos privados e preservou todos na segunda execução | SHA-256 antes/depois iguais; senha nunca impressa |
| `pnpm.cmd infra:up` | Primeira execução falhou no bind 5432; após D15, saudável em 15432 | Sem alterar o serviço PostgreSQL anterior |
| `Get-NetTCPConnection -LocalPort 5432`; `netsh interface ipv4 show excludedportrange protocol=tcp`; `Get-Process -Id 7000` | Porta 5432 ocupada por postgres; não era exclusão de porta do sistema | Motivou configuração local, sem alterar firewall |
| `docker compose --env-file .env -f infra/compose.yaml config --quiet`; `pnpm.cmd infra:status` | Configuração válida e container healthy | Somente 127.0.0.1:15432 publicado |
| `python .local/verify-postgres.py "SELECT version(), current_database(), inet_server_port();"` (mesma consulta primeiro via stdin) | PostgreSQL 17.11, banco radar, porta interna 5432 | psql nativo existente, conexão TCP em 127.0.0.1:15432 e senha por ambiente privado |
| `CREATE TABLE stage00_persistence_probe ...; INSERT ...`; `pnpm.cmd infra:down`; `pnpm.cmd infra:up`; `SELECT ...; DROP TABLE ...` via script psql privado | Valor `etapa00` permaneceu após recriação do container; tabela removida | Verificação real do volume; nenhuma tabela de domínio criada |
| `pnpm.cmd format`; `pnpm.cmd lint` | Aprovados, última execução sem avisos de lint | ESLint nos três pacotes/scripts e Prettier |
| `pnpm.cmd typecheck` | Aprovado nos três pacotes | Inclui `next typegen`; TS strict e API NodeNext |
| `pnpm.cmd build` | Aprovado nos três pacotes | Next 16.4.2/Turbopack compilou; API compilou para ESM |
| `uv run --project services/edge --frozen ruff check services/edge`; `uv run --project services/edge --frozen ruff format --check services/edge`; `pnpm.cmd lint:edge` | Aprovados após corrigir duas linhas longas | Três arquivos Python formatados |
| `uv build --project services/edge` | sdist e wheel gerados com sucesso | Artefatos locais em `services/edge/dist/`, ignorados |
| `uv run --project services/edge --frozen radar-edge env`; `pnpm.cmd check:edge` | status ok; MediaPipe 1.1.1, cv2 5.0.0, PoseLandmarker importado | Um fornecedor cv2; WIN32UI, FFmpeg, DirectShow e Media Foundation compilados; não comprova dispositivo/decoder |
| `pnpm.cmd dev:api`; `pnpm.cmd dev:web` | API e web iniciaram em loopback; watchers funcionaram após correção | Emissão de logs JSON da API e compilação incremental observadas |
| `Invoke-WebRequest -UseBasicParsing ...` e scripts HTTP `python -` | Página HTTP 200; API e proxy HTTP 200 com `{"status":"ok"}` | Título, lang pt-BR e rótulo de ausência de vídeo conferidos |
| Edge `--headless --disable-gpu --no-first-run --no-default-browser-check --user-data-dir=... --screenshot=... --window-size=1280,900 --timeout=10000 http://127.0.0.1:3000` | Captura de tela produzida e inspecionada | Página renderizada sem erro; imagem em `.local/etapa00-web.png`, ignorada |
| `pnpm.cmd --filter @radar/api start`; `pnpm.cmd --filter @radar/web start` | Processos do build iniciaram em loopback | HTTP conferido também com execução do build |
| Scripts Python de subprocessos com API_HOST/PORT inválidos, API_INTERNAL_URL inválida e POSTGRES_PASSWORD vazio | Saída de erro não zero em todos; URL inválida não apareceu no erro | Não alteraram os arquivos privados nem as variáveis globais |
| `git check-ignore ...`, inspeção dos candidatos com `git ls-files --cached --others --exclude-standard -z`, `git diff --check` | Privados/builds ignorados; senha gerada ausente dos candidatos; diff sem erro de espaços | Não foi feito git add/commit/push |

## Critérios da etapa

| Critério | Verificado / pendente | Evidência |
| --- | --- | --- |
| Instalação JS/Python reproduzível pelos locks | Verificado | Frozen no ambiente principal e em diretórios vazios |
| Web abre; API responde; PostgreSQL saudável | Verificado | HTTP 200, Edge renderizado, Compose healthy, TCP autenticado |
| Build/lint/typecheck; imports reais de visão | Verificado | Três pacotes TS, Ruff e env com imports reais |
| Sem senha pública, mídia pessoal ou modelo no Git | Verificado | Exemplos sem senha, geração privada e checagens de ignore/valor privado |
| Status e relatório refletem situação real | Verificado | Este relatório, STATUS e inventário atualizados |

## Como reproduzir

Na raiz do repositório, em PowerShell nesta máquina:

```powershell
. ./scripts/activate.ps1
pnpm.cmd install --frozen-lockfile
uv sync --project services/edge --frozen
pnpm.cmd setup:env
pnpm.cmd infra:up
pnpm.cmd infra:status
pnpm.cmd check:edge
```

Em dois terminais separados, cada um com `. ./scripts/activate.ps1`:

```powershell
pnpm.cmd dev:api
```

```powershell
pnpm.cmd dev:web
```

Abra `http://127.0.0.1:3000` e, em outro terminal ativado:

```powershell
Invoke-RestMethod http://127.0.0.1:3001/v1/health/live
Invoke-RestMethod http://127.0.0.1:3000/api/health/live
pnpm.cmd lint
pnpm.cmd typecheck
pnpm.cmd build
pnpm.cmd lint:edge
uv build --project services/edge
docker compose --env-file .env -f infra/compose.yaml exec -T postgres pg_isready -U radar -d radar
```

Para testar login TCP do banco com o psql já existente nesta máquina:

```powershell
& 'C:\Program Files\PostgreSQL\17\bin\psql.exe' -X -h 127.0.0.1 -p 15432 -U radar -d radar -W -c 'SELECT version(), current_database();'
```

Esse comando solicita a senha privada de `POSTGRES_PASSWORD` do `.env` raiz.
Não coloque a senha no argumento nem em relatório. Scripts auxiliares de verificação
e ferramentas sob `.local/` são locais, não são requisitos ocultos do software.
Em outro checkout é necessário instalar as ferramentas; há instruções e versões em
[ambiente e comandos](../08_AMBIENTE_E_COMANDOS.md).

`Ctrl+C` para web/API e `pnpm.cmd infra:down` para o banco, sem `-v`.
Ao final desta execução, web/API foram encerrados e `infra:down` executado;
o volume `radar_postgres_data` permaneceu disponível. Docker Desktop permaneceu
iniciado. Os comandos acima iniciam novamente os processos do projeto.
Durante o desenvolvimento, uma compilação de `build` pode provocar um reinício
normal do watcher da API por atualizar `dist`; não é execução adicional de domínio.

## Falhas, limites e pendências

- Daemon Docker parado: corrigido iniciando a instalação existente.
- Bind 5432 falhou: corrigido com porta local 15432, mantendo o banco existente.
- Primeira abordagem de dev API compilava dentro do processo vigiado e causou
  ciclo de reinícios: substituída por `tsc --watch` e `node --watch` coordenados por
  concurrently. Inicialização, resposta HTTP e recompilação foram verificadas.
- Aviso de export anônimo na configuração PostCSS e duas linhas Ruff longas:
  corrigidos; últimas execuções sem esses avisos/erros.
- Uma comparação textual enviada ao Python por pipe PowerShell teve problema de
  codificação dos acentos; repetida com escapes Unicode, passou. A página renderizada
  no navegador confirmou os acentos corretos. Não foi um defeito da página.
- ESLint 9: aviso de fim de suporte permanece como limitação de manutenção da
  combinação de plugins, sem erro de lint ou conflito de instalação.
- Somente Windows x64 foi testado. Sem medição de FPS, uso de CPU sob inferência,
  suporte de câmera, reprodução de vídeo ou eficácia de detector nesta etapa.
- Nenhum modelo, vídeo ou dataset obtido. Licenças/avisos iniciais estão inventariados;
  termos de modelo e auditoria de redistribuição de binários/codecs são trabalho
  futuro, antes de obter/empacotar esses artefatos.
- Nenhuma verificação obrigatória da etapa 00 ficou pendente. Não é necessário
  fornecer credenciais ou autorizar hardware para reproduzir a fundação atual.

## Próxima etapa elegível

Etapa 01 — domínio, banco e acesso — somente com solicitação do fundador.
Etapas 01–09 permanecem não iniciadas. Esta entrega não demonstra detecção,
webcam, autenticação ou ingestão de incidentes.
