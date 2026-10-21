# Ambiente, configuração e comandos previstos

[Voltar ao README central](../README.md)

**Etapas 00–03 implementadas em 21/10/2026.** Consulte o [status](STATUS.md), o [relatório 03](RELATORIOS/ETAPA_03.md) e o [roteiro de apresentação](VALIDACAO_MANUAL_ETAPA_03.md). Comandos de 04 em diante continuam previstos e não devem ser executados antes da etapa correspondente. O proprietário existente é preservado; não há necessidade de repetir provisionamento para abrir o painel.

## Iniciar a fundação nesta máquina (PowerShell, raiz do repositório)

O Node 22 e Python 3.13 existentes foram preservados. Node 24.22.1, pnpm 10.34.7 e uv 0.13.4 foram preparados em `.local/tools/` (ignorado). Python 3.12.15 foi instalado pelo uv sem alterar o Python padrão. Em cada novo terminal, execute o dot-source abaixo; ele altera somente o PATH daquele terminal.

```powershell
. ./scripts/activate.ps1
node --version
pnpm.cmd --version
uv --version
pnpm.cmd install --frozen-lockfile
uv sync --project services/edge --frozen
pnpm.cmd setup:env
pnpm.cmd infra:up
pnpm.cmd infra:status
```

`pnpm` e `pnpm.cmd` referem-se ao mesmo gerenciador; `.cmd` evita problemas de política de execução do shim PowerShell. O script `activate.ps1` foi executado com sucesso sem mudar a política de execução do Windows. Se o Docker estiver parado, inicie o Docker Desktop e aguarde `docker version` mostrar Client e Server.

`setup:env` cria `.env`, `apps/api/.env` e `apps/web/.env` somente se não existirem. Gera uma senha aleatória de 32 bytes para o banco, sem imprimi-la. Na atualização da 01 complementa apenas valores novos/ausentes de DATABASE_URL, WEB_ORIGIN, NODE_ENV e ALLOW_INSECURE_LOCAL_HTTP da API; preserva valores já preenchidos e credenciais existentes. DATABASE_URL é derivada das credenciais do `.env` raiz com encoding e sem log de seu valor. O exemplo e esta máquina usam `POSTGRES_PORT=15432` (D16), pois há outro PostgreSQL em 5432. Prisma/API rejeitam a porta 5432 do host. Nunca edite o exemplo com senha real. A senha do volume existente não muda ao editar o `.env`: preserve o arquivo privado ou faça a rotação conscientemente, sem apagar o volume.

Depois da preparação, execute `pnpm.cmd db:generate`, `pnpm.cmd db:migrate` e `pnpm.cmd setup:owner`. Migração usa `prisma migrate deploy`, aplicando somente SQL versionado. O proprietário depende de e-mail/senha privados escolhidos pelo fundador; não há senha pública. Para execução não interativa, configure BOOTSTRAP_EMAIL/BOOTSTRAP_PASSWORD no `.env` privado da API e use `pnpm.cmd db:seed`. Repetir preserva senha e dados. Trocar o e-mail não cria silenciosamente outro proprietário no mesmo tenant. Para operador local, use `pnpm.cmd user:create-operator`. O tenant padrão é identificado pelo slug `demo`, configurável por BOOTSTRAP_TENANT_SLUG.

Terminal da API:

```powershell
. ./scripts/activate.ps1
pnpm.cmd dev:api
```

Terminal da web:

```powershell
. ./scripts/activate.ps1
pnpm.cmd dev:web
```

Abra `http://127.0.0.1:3000`. A etapa 03 oferece login real e painel com visão geral, incidentes, fontes, avisos locais e configuração de OWNER. Liveness só comprova o processo; readiness (`/v1/health/ready`) consulta o banco. O [roteiro da etapa 03](VALIDACAO_MANUAL_ETAPA_03.md) mostra a apresentação no navegador e o simulador; o [roteiro HTTP anterior](VALIDACAO_MANUAL_ETAPA_01.md) continua válido para diagnóstico.

Terminal de validação:

```powershell
. ./scripts/activate.ps1
Invoke-RestMethod http://127.0.0.1:3001/v1/health/live
Invoke-RestMethod http://127.0.0.1:3000/api/health/live
pnpm.cmd lint
pnpm.cmd typecheck
pnpm.cmd build
pnpm.cmd lint:edge
pnpm.cmd check:edge
uv build --project services/edge
docker compose --env-file .env -f infra/compose.yaml exec -T postgres pg_isready -U radar -d radar
```

As duas consultas HTTP retornam `status: ok`. `check:edge` equivale a `uv run --project services/edge --frozen radar-edge env`: importa MediaPipe/OpenCV/Tasks reais, mas não abre câmera, baixa modelo nem executa inferência. `lint` inclui ESLint e Prettier nos arquivos novos de código/configuração; `lint:edge` aplica Ruff. `typecheck`/`build` percorrem os três pacotes TypeScript. O projeto Python tem lock e build próprios, fora do workspace pnpm.

Após o build, também é possível executar `pnpm.cmd --filter @radar/api start` e `pnpm.cmd --filter @radar/web start` em terminais separados, com os processos de desenvolvimento parados. `Ctrl+C` encerra web/API. `pnpm.cmd infra:down` encerra o banco preservando `radar_postgres_data`; `pnpm.cmd infra:up` o recupera.

### Recriar as ferramentas em outra instalação Windows

Instale Node **24.22.1** de [nodejs.org](https://nodejs.org/dist/v24.22.1/) e confira o SHA-256 do artefato com o `SHASUMS256.txt` oficial. Com esse Node no PATH e Python disponível apenas para bootstrap, os comandos usados para preparar os outros gerenciadores locais foram:

```powershell
python -m pip install --target .local/tools/uv uv==0.13.4
npm.cmd install --prefix .local/tools/pnpm --no-package-lock --ignore-scripts pnpm@10.34.7
.local/tools/uv/bin/uv.exe python install 3.12.15 --no-bin
. ./scripts/activate.ps1
```

O uso de npm/pip acima é limitado ao bootstrap dos gerenciadores. As dependências do software usam exclusivamente pnpm/uv e os locks versionados. O Node portátil desta máquina está em `.local/tools/node-v24.22.1-win-x64`; o script aceita também a mesma versão instalada no PATH. Não versionar essas ferramentas. Para outros sistemas, instale as mesmas versões conforme as fontes oficiais e execute os comandos pnpm/uv; esses sistemas não foram testados aqui.

## Pré-requisitos

Git, VS Code, Node.js 24 LTS, pnpm 10, Python 3.12, uv e Docker com Compose. Preferir ambiente nativo do SO para webcam. Primeiro verificar os programas presentes; não reinstalar tudo ou alterar configurações globais sem necessidade.

Não há GPU, conta AWS, OpenAI API, servidor público, cartão de crédito ou assinatura obrigatória. Instalação de pacotes/modelo requer internet inicialmente. O consumo de memória e a capacidade de uma câmera serão medidos; não há especificação inventada para o notebook do fundador.

| Comando de diagnóstico | Uso |
| --- | --- |
| `node --version` / `pnpm --version` | Conferir runtime JS e gerenciador |
| `python --version` / `uv --version` | Conferir runtime e ambiente Python |
| `docker version` / `docker compose version` | Conferir daemon e Compose |
| `git status --short` | Preservar alterações antes de editar |

## Variáveis e arquivos privados

O bootstrap deve gerar `.env.example` sem segredos e orientar cópia local. Validar variáveis na inicialização e falhar com erro compreensível, sem imprimir valores sensíveis.

| Variável/conceito | Onde | Observação |
| --- | --- | --- |
| `DATABASE_URL` | API/migrações | PostgreSQL local com senha particular |
| `POSTGRES_USER`, `POSTGRES_DB`, `POSTGRES_PASSWORD`, `POSTGRES_PORT` | Compose; `.env` raiz | Senha privada obrigatória; porta publicada apenas em `127.0.0.1`; padrão 15432 na etapa 01 |
| `API_HOST`, `API_PORT` | API | `127.0.0.1`, `3001` |
| `WEB_ORIGIN` | API | `http://127.0.0.1:3000` |
| `API_INTERNAL_URL` | Web server | `http://127.0.0.1:3001/v1`; não vazar segredos ao client |
| `BOOTSTRAP_EMAIL`, `BOOTSTRAP_PASSWORD` | Setup local | Conta proprietária; não embutir no código |
| `EDGE_API_URL` | Worker/simulador | Endpoint da API local |
| `EDGE_DEVICE_TOKEN` | Worker/simulador | Credencial individual emitida pelo backend |
| `EDGE_CAMERA_ID` | Worker | Registro de câmera autorizado |
| `EDGE_SOURCE_URI` | Worker | Somente para RTSP; nunca em log/argumento CLI |
| `EDGE_MODEL_PATH` | Worker | Bundle obtido de fonte oficial e hash verificado |
| `EVIDENCE_MODE` | Worker | `skeleton` por padrão; `none`/`snapshot` explícitos |
| `LOCAL_DATA_DIR` | API/worker | Raiz privada `.local/` e subdiretórios separados |
| `METADATA_RETENTION_ENABLED` | API | `false` por padrão; proprietário habilita conscientemente a purga de metadados de 30 dias |

Nunca prefixar segredo com `NEXT_PUBLIC_`. Não definir nome de variável de tarefa que substitua `HOME` ou outros diretórios de sistema.

## Comandos que a implementação deve oferecer

Executados a partir da raiz do repositório. Scripts pnpm encapsulam caminhos para reduzir diferenças entre PowerShell e bash; evitar scripts que só funcionem com sintaxe Unix sem documentação.

| Comando-alvo | Introduzido | Efeito esperado |
| --- | --- | --- |
| `pnpm install --frozen-lockfile` | 00, após lock inicial | Instala JS reproduzivelmente |
| `pnpm setup:env` | 00 | Cria configuração privada e senha aleatória sem sobrescrever arquivos |
| `pnpm infra:up` | 00 | Sobe somente PostgreSQL em loopback |
| `pnpm infra:down` | 00 | Para infraestrutura sem excluir volume |
| `pnpm dev:api` / `pnpm dev:web` | 00 | Inicia API e interface em terminais separados |
| `pnpm lint` / `pnpm typecheck` / `pnpm build` | 00 | Verificações JS reais |
| `uv sync --project services/edge --frozen` | 00 | Instala Python pelo lock |
| `pnpm lint:edge` / `pnpm check:edge` | 00 | Ruff e imports reais de visão, sem modelo/câmera |
| `pnpm db:generate` / `pnpm db:migrate` | 01 | Gera client e aplica migrações versionadas |
| `pnpm db:seed` | 01 | Cria dados locais idempotentes sem apagar dados |
| `pnpm setup:owner` / `pnpm user:create-operator` | 01 | Provisionamento local com senha mascarada; sem cadastro público |
| `pnpm openapi:generate` | 01 | Gera docs/OPENAPI.json a partir dos endpoints/DTOs |
| `pnpm test:api` | 01 | Integração real em container/banco/volume exclusivos e descartáveis; não limpa o banco da demo |
| `pnpm test:contracts` | 02 | Testes de contratos entre linguagens |
| `pnpm contracts:generate` | 02 | Regenera tipos TypeScript dos JSON Schemas; `test:contracts` confere sua consistência |
| `pnpm demo:simulate` | 03 | Envia evento artificial rotulado, via API autenticada |
| `pnpm test:demo` | 03 | Testa falhas de transporte do simulador em servidor HTTP sintético exclusivo |
| `pnpm test:e2e` | 03 | Fluxo de navegador em ambiente de teste |
| `pnpm test:e2e:install` | 03 | Instala Chromium compatível com Playwright fixado; executar uma vez por ambiente |
| `uv run --project services/edge radar-edge doctor` | 04 | Verifica modelo, arquivos e recursos sem expor segredos |
| `uv run --project services/edge radar-edge calibrate --config .local/edge.yaml` | 04 | Assistente local para delimitar piso |
| `uv run --project services/edge radar-edge run --config .local/edge.yaml` | 04/05 | Arquivo/poses; após 05, emissão real de candidatos |
| `uv run --project services/edge pytest` | 05 | Testes de regras, contrato e persistência |
| `uv run --project services/edge radar-edge evaluate --manifest .local/evaluation.json` | 05/08 | Replay e métricas em relatório privado |
| `uv run --project services/edge radar-edge reset-episode --config .local/edge.yaml --reason scene_reset` | 05 | Reset local explícito, com worker de captura parado e auditoria; não encerra incidente humano |
| `uv run --project services/edge radar-edge probe --config .local/edge.yaml` | 06/09 | Verifica fonte configurada, sem detectar incidente |
| `pnpm demo:check` | 08 | Checa pré-requisitos e consistência sem fabricar resultados |

Definir no Python a descoberta de testes de modo que o comando a partir da raiz funcione; o argumento `--project` do uv seleciona o projeto, não garante sozinho o diretório de trabalho de toda ferramenta. Não esconder falha com `|| true` ou placeholder que sempre retorna sucesso.

O primeiro `pnpm install`/`uv sync` da etapa 00 resolve e cria os locks; os comandos frozen passam a ser usados depois. A CLI `calibrate` precisa de interação do fundador quando não houver ambiente gráfico. Pode oferecer edição manual de pontos validados como alternativa, sem supor que a IA viu o vídeo.

Na 03, `pnpm.cmd demo:simulate` lê `.local/demo.json`; o exemplo sem segredo é
`scripts/demo/config.example.json`. Use câmera/credencial exclusivas de demonstração,
modo SIMULATED, pose sintética e heartbeat enquanto a execução estiver ativa.
`r` e Enter reenviam o mesmo evento; `q` e Enter ou o prazo encerram com ENDED.
`--config .local/demo.json --once` faz uma execução curta. Não há inserção direta
de incidentes no banco, login humano no simulador, captura ou inferência.
Inicie a API antes: `dev:api` já compila os contratos. O simulador não os recompila,
evitando reiniciar o processo observado pelo Node durante os envios. Há até quatro
tentativas para conexão/timeout/HTTP 502/503/504, com o mesmo envelope; falhas
permanentes continuam encerrando com código não zero. `test:demo` exige os mesmos
contratos compilados e usa somente servidor e credenciais sintéticos locais.

`pnpm.cmd test:e2e` cria container `radar-e2e-<id>`, banco/volume próprios e três
portas efêmeras, aplica as migrações e inicia seus processos de API e web. O build
da web usa `.next-e2e` e configuração TS gerada/ignorada; `next-env.d.ts` é restaurado
ao final. Os processos e configurações privados da demonstração ficam preservados.
O teste de falha para/reinicia somente esse container. Screenshots/diagnósticos
sintéticos ficam em `.local/etapa03/results`. Suíte completa: desktop 1440×1000 e
viewport móvel 390×844, Chromium. Exemplo de investigação focada:
`pnpm.cmd test:e2e --grep 'polling pausa' --project desktop`.

Na etapa 02, `pnpm.cmd test:api` aplica as duas migrações num banco exclusivo vazio, executa primeiro os 19 testes de acesso e depois os testes de eventos/incidentes, incluindo o roteiro PowerShell por HTTP real. A ordem preserva o teste anterior de banco vazio. Não execute o comando interno `test:integration` contra a demonstração: a suíte exige o identificador do container exclusivo. A validação de tipos da API gera contratos/client necessários para não depender de um build antigo. O [roteiro manual 02](VALIDACAO_MANUAL_ETAPA_02.md) permite validar o fluxo com a conta local existente. Ative `. ./scripts/activate.ps1` em cada terminal antes de usar `pnpm.cmd`.

## Sequência final de execução prevista

1. Instalar dependências e preparar `.env`/configuração privada.
2. Subir PostgreSQL; gerar client, aplicar migrações e seed idempotente.
3. Iniciar API e web; fazer login.
4. Cadastrar câmera e obter credencial de worker.
5. Obter modelo, verificar hash/licença e executar diagnóstico.
6. Selecionar fonte, calibrar e iniciar worker em outro terminal.
7. Demonstrar, revisar incidente e consultar relatório.
8. Parar worker e serviços de forma limpa, preservando banco/outbox.

Sem `docker compose down -v`, reset de banco, exclusão de `.local` ou regravação de vídeo como parte do fluxo normal. Testes usam banco dedicado claramente identificado; nunca apontar rotina de limpeza ao banco da demo.

## Falhas comuns a documentar durante a implementação

Webcam ocupada ou sem permissão; caminhos Windows; versão Python sem wheel; múltiplas distribuições `cv2`; falha de decoder; prisma generate ausente; ESM inconsistente; cookie/origin divergentes; banco indisponível; ROI inválida após rotação; token revogado; fim normal de arquivo. Solucionar a causa concreta e registrar o comando real, sem inventar uma compatibilidade universal.
