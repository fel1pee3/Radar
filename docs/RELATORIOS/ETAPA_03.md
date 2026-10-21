# Etapa 03 — Painel e primeira demonstração

Data: 21/10/2026.
Status: **CONCLUÍDA**.
Ambiente: Windows 11 Pro 10.0.26200 x64, PowerShell 5.1.26100.9711;
Ryzen 5 5625U, 6 núcleos/12 threads, 15,4 GiB RAM; Node 24.22.1, pnpm 10.34.7,
Python 3.12.15, uv 0.13.4. Docker 29.1.3/Compose 5.0.1, PostgreSQL 17.11 preservados.
Base: `4892ad7`, branch main, árvore inicialmente limpa. Sem commit/push/deploy.
Navegador de testes: Chromium/Chrome for Testing 156.0.8078.4, revisão 1248,
Playwright 1.64.1; desktop 1440×1000 e viewport móvel 390×844.

## Resultado entregue

Fluxo real: login → fontes → simulador bearer → incidente no painel → sinais e
pose sintética → reconhecimento/revisão/atendimento registrado/desfecho → histórico
e aviso SIMULATED. Recarregar preserva os dados no PostgreSQL. A identidade visual
é consistente e responsiva, com navegação, estados vazios/carregando/erro,
banner de MVP de demonstração e indicação dos modos Simulado/Reprodução/Ao vivo.
Nenhum contador global é calculado a partir de uma página parcial.

A configuração permite ao OWNER criar locais, criar/editar câmeras lógicas,
emitir/rotacionar credenciais mediante confirmação, copiar/ocultar o token único
e revogar por ID após recarga. OPERATOR consulta/revisa sem configurar. URI e
senha de câmera permanecem fora da interface.

Polling sequencial por recurso, com intervalo mínimo de 2 s após a consulta,
cancelamento/cleanup e pausa por visibilidade. Falha mantém os dados anteriores
com indicação de desatualização; fonte que era ativa passa a indicar estado não
atualizado quando a consulta falha. Ausência de heartbeat não parece conexão.
Rascunho/tentativa ficam em memória. Expiração oculta dados e permite retomar
com a mesma conta. Logout/troca de conta desmonta o estado. Não há armazenamento
de senha, bearer ou sessão em localStorage.

## Arquivos e decisões

| Área | Arquivos principais |
| --- | --- |
| Rotas | `apps/web/app/login`, `app/(panel)/{page,layout}`, `incidentes`, `incidentes/[id]`, `fontes`, `avisos`, `configuracao`; substituem a página mínima |
| UI | `apps/web/components/{session,shell,ui,views,detail,configuration,pose}.tsx`, `app/globals.css`, `app/layout.tsx` |
| Integração | `apps/web/lib/{api,polling,models}.ts`; tipos de eventos/ações de @radar/contracts |
| API | `apps/api/src/devices.ts`: apenas GET paginado de metadados das credenciais, com guards existentes |
| Simulador | `scripts/demo/simulate.mjs`, `config.example.json`; configuração privada em .local |
| E2E | `tests/e2e/{run,playwright.config,panel.spec}.mjs`; banco/API/web próprios, capturas privadas |
| Ambiente | Manifests, pnpm-lock, ignores/ESLint; Next com build/config TS de testes separados |
| Documentação | README, contratos, comandos, decisões, inventário, OpenAPI, STATUS, roteiro manual03 e este relatório |

Nenhuma migração foi necessária. As duas anteriores foram reaplicadas em bancos
vazios exclusivos, sem mudar schema ou resetar a demonstração. A API retorna
somente id/deviceId/version/createdAt/revokedAt na nova listagem; nunca token/hash.
Isso resolve a revogação pela UI depois de recarregar, preservando tenant/RBAC.

Decisões D23–D26 registradas em [09](../09_DECISOES_E_FUTURO.md):

- Sessão por cookie HttpOnly/proxy, fetch no-store e conteúdo autenticado carregado
  no cliente. HTML estático não contém dados privados de usuário.
- actionId/corpo estáveis por tentativa; falha transitória oferece retry idempotente.
  409 recarrega o estado e exige nova intenção explícita, sem submissão automática.
- Pose SVG usa apenas os pontos corporais presentes, com conexão dos índices
  existentes e visibilidade ≥ 0,5. Ausência é explícita. SIMULATED é evidência sintética.
- Simulador Node usa câmera/credencial dedicadas, UUIDs/UTC, somente SIMULATED,
  pose sintética, heartbeat de 5 s e ENDED no término normal. Não usa senha humana,
  banco diretamente, câmera, modelo ou produtor Python.
- E2E usa portas efêmeras, container/volume próprios e build `.next-e2e`, com
  configuração TS temporária ignorada. next-env.d.ts é restaurado ao final.

Dependência nova: @playwright/test 1.64.1, exata e somente dev, com árvore no lock.
Web importa os tipos do workspace contracts. Versões anteriores, Python e
fornecedor único de cv2 preservados. Fontes/licenças no [inventário](DEPENDENCIAS_E_MODELOS.md).

## Verificações reais

| Comando/ação executada | Resultado observado | Evidência/limitação |
| --- | --- | --- |
| Leitura do prompt/AGENTS/README/STATUS, relatórios01/02, etapa03 e referências; `rg --files`, `git status --short --branch` | Código e documentos inspecionados; base limpa em4892ad7 | API existente reutilizada |
| Get-CimInstance de SO/CPU; versões Node/pnpm/uv; docker ps e portas em escuta | Ambiente acima; demo saudável em15432, servidor5432 preservado | Inicialmente não havia API/web da demo rodando; nenhum processo do fundador foi parado |
| `. ./scripts/activate.ps1` | Ferramentas disponíveis no shell | Necessário em cada novo terminal |
| `pnpm.cmd view @playwright/test version engines license` | 1.64.1, Node>=20, Apache-2.0 | Metadados oficiais; sem atualização de framework |
| `pnpm.cmd add -Dw @playwright/test@1.64.1`; `pnpm.cmd --filter @radar/web add @radar/contracts@workspace:*` | Dependências/lock atualizados | Novidade externa somente de desenvolvimento |
| `pnpm.cmd exec playwright install chromium` | Chromium 156/revisão 1248 instalado | Binários/cache fora do Git; instalador removeu revisões que considerou não usadas |
| `pnpm.cmd install --frozen-lockfile` | Lock consistente; instalação aprovada | Avisos anteriores de scripts Scarf/Parcel bloqueados permaneceram |
| `pnpm.cmd test:e2e` | **16/16 aprovados**, oito cenários em desktop e móvel | PostgreSQL/API/web reais e exclusivos; recursos removidos ao final |
| CLI demo:simulate executada pela suíte com arquivo privado UTF-8/BOM | 1 resposta201 e 10 respostas200; um recibo/incidente/intenção/aviso; pose sintética e ENDED | Heartbeat periódico comprovado pela sequence ≥ 2; modo sempre SIMULATED; saída sem token/senha sintéticos |
| `pnpm.cmd test:e2e --grep 'conflito real|polling pausa' --project desktop` | Execução focada final:2/2 aprovados | Usada para resolver os problemas descritos abaixo |
| `pnpm.cmd test:e2e --grep 'polling pausa'` | 2/2 aprovados, desktop/móvel | Capturas da visão geral esperam os seis registros antes de fotografar |
| `pnpm.cmd test:api` | **19+104=123 testes aprovados** | Migrações vazias, RBAC, idempotência, transações, heartbeat e logs anteriores preservados |
| `pnpm.cmd test:contracts` | **87 TS +87 Python aprovados** | Mesmos exemplos e caso não finito |
| `pnpm.cmd lint`, `pnpm.cmd typecheck`, `pnpm.cmd build` | Aprovados nos projetos | ESLint inclui simulador/E2E; build normal e de testes verificados |
| `pnpm.cmd lint:edge`, `pnpm.cmd check:edge` | Ruff aprovado; imports reais MediaPipe/OpenCV/Tasks aprovados | Nenhum modelo/câmera/inferência executados |
| `pnpm.cmd openapi:generate`; conferência do JSON | OpenAPI atualizado com GET de metadados | Sem alteração dos envelopes de ingestão/ação |
| Inspeção visual de screenshots pelo agente | Detalhe desktop/móvel e visão geral desktop revisados; legibilidade, pose e identificação da simulação conferidas | Capturas sintéticas em .local/etapa03/results e visual-reviewed; não são imagem de câmera |
| Verificador privado da02: `node --env-file-if-exists=apps/api/.env .local/etapa02/preserve-demo.mjs after` | Mesmo OWNER ativo, local, duas câmeras e zero credenciais anteriores | Nenhum e-mail/senha/hash pessoal consultado; demonstração sem incidentes inseridos pelos testes |
| `git diff --check`, revisão de caminhos/ignores/segredos e docker ps final | Sem whitespace inválido ou artefatos privados versionáveis; só container da demo mantido | Sem commit/push/deploy |

## Critérios da etapa

| Critério | Situação | Evidência |
| --- | --- | --- |
| Fluxo completo real e persistente | VERIFICADO | CLI→API→Postgres→lista/detalhe→quatro ações→reload→histórico/aviso, nos dois viewports |
| Login, proteção e logout | VERIFICADO | Cookie HttpOnly, /auth/me, cache no-store, Origin, retorno à proteção após logout e troca de papel |
| Sinais, pose, modo e ausência de evidência | VERIFICADO | SVG de pose sintética; modo/classe explícitos; eventos sem pose também exercitados |
| Permissões e configuração | VERIFICADO | OWNER cria local/câmera, edita, emite/oculta/revoga; OPERATOR revisa e é bloqueado na configuração/credenciais; outro tenant404 |
| Ações concorrentes e retry | VERIFICADO | Ação concorrente real provoca409; texto mantido; preparar não grava; resposta perdida após commit é reenviada com mesmo actionId e só um registro |
| Simulador idempotente | VERIFICADO | Dez reenvios do envelope original sem duplicar recibo/incidente/aviso; heartbeat e ENDED |
| API indisponível e sessão expirada | VERIFICADO | Somente banco de testes parado/iniciado; dado anterior/nota preservados, ações suspensas, retomada e login da mesma conta recuperam texto |
| Fonte sem heartbeat/erro de consulta | VERIFICADO | Cadastro não fica online; falha da API substitui aparência saudável por Estado não atualizado e último estado conhecido |
| Polling e navegação | VERIFICADO | Consulta de 3 s não sobrepõe outra; aba oculta pausa e volta retoma; paginação21 registros em20+1 e filtros/URL preservados |
| Responsividade e visualização | VERIFICADO | Interações em 1440×1000 e 390×844, sem overflow horizontal da página; capturas inspecionadas |
| Regressões e documentação | VERIFICADO | 123 API, 87 + 87 contratos, lint/typecheck/build; STATUS, roteiro e este relatório |

## Como reproduzir

Siga o [roteiro manual](../VALIDACAO_MANUAL_ETAPA_03.md). Na raiz:

```powershell
. ./scripts/activate.ps1
pnpm.cmd install --frozen-lockfile
pnpm.cmd setup:env
pnpm.cmd infra:up
pnpm.cmd db:generate
pnpm.cmd db:migrate
pnpm.cmd test:e2e:install
pnpm.cmd test:e2e
```

Em terminais separados, ativados individualmente: `pnpm.cmd dev:api` e
`pnpm.cmd dev:web`. Abra http://127.0.0.1:3000 e entre com o proprietário existente.
Na configuração, prepare uma câmera FILE exclusiva e sua credencial; copie o
exemplo para `.local/demo.json` e preencha somente o arquivo privado.
Execute `pnpm.cmd demo:simulate` em um terceiro terminal. O roteiro detalha a
apresentação, ações, histórico, avisos e revogação. Não há segredo padrão público.

## Falhas, limites e pendências

Problemas encontrados e corrigidos:

- Tipos de rotas de uma página antiga permaneciam no cache dev; geração dos tipos
  atuais e separação de saída/configuração E2E resolveram sem apagar dados do
  projeto. A tentativa de limpar cache foi bloqueada pelo ambiente e não foi executada.
- Lint recusou leitura de ref durante render; estado visual de retry passou a
  usar state, mantendo ref somente para o corpo/identidade da tentativa.
- Primeiro build E2E herdava NODE_ENV=development, incompatível com o build
  de produção do Next, causando erro de prerender/useContext. Ambiente da web
  separado do da API local; builds seguintes passaram.
- Localizadores iniciais de selects e legenda exigiam texto incorreto/exato;
  passaram a usar papéis acessíveis e legenda real. Nota recebeu nome acessível
  estável, independente do contador de caracteres.
- Catálogo carregado depois do formulário apagava a seleção inicial da câmera;
  filtro passou a controlado, preservando URL/contexto.
- Ao trocar o botão de preparar pelo de enviar no mesmo formulário, o clique
  podia iniciar submit nativo. preventDefault e identidades distintas dos botões
  impedem envio; teste verifica ausência de ação até novo clique explícito.
- Retry de uma ação já confirmada remotamente precisa continuar disponível mesmo
  quando o estado atual já não permite aquela transição. A UI mantém o corpo/ID
  original para a API retornar o snapshot anterior.
- Uma consulta que falha não pode deixar o badge de fonte verde. Overview e
  fontes agora exibem Estado não atualizado, com último estado conhecido.

**Nenhum critério obrigatório pendente ou bloqueado.** A validação foi feita com
usuários/credenciais sintéticos, incluindo inspeção visual das capturas. Não foi
solicitada ou utilizada a senha pessoal do fundador. A preparação de câmera/token
na demonstração do fundador é uma ação local descrita no roteiro, não um bloqueio
da implementação testada.

Limites: largura móvel é emulação Chromium, não aparelho físico; Firefox/Safari
não foram verificados. O caminho interativo r/q e Ctrl+C não foi exercitado
manualmente; reenvio automático e término normal por prazo foram comprovados.
Fechar/recarregar a aba perde rascunho/tentativa ainda em memória; não há outbox
de navegador. A pausa/retomada de polling foi controlada no document.hidden nos
testes, com consultas HTTP reais. Não há medição de latência/FPS/eficácia.

Captura, inferência, motor temporal, snapshot, streaming e mensagem externa
continuam ausentes. Avisos SIMULATED não representam envio nem atendimento real.
Warnings conhecidos de VM modules/NO_COLOR e scripts de dependências bloqueados
não foram ocultados nem transformados em sucesso de um teste que falhou.

## Próxima etapa elegível

04 — Visão computacional em arquivo, somente mediante nova solicitação.
Nenhuma implementação dessa etapa foi iniciada. Sem commit, push ou deploy.

## Correção após uso manual do simulador — 21/10/2026

O fundador recebeu 201, seguido de 200 com duplicate=true, e depois
DEMO_UNAVAILABLE/exit1. O incidente, pose, sinais e aviso local ficaram salvos.
Consulta somente de leitura confirmou versão1 e heartbeat RUNNING/sequence0,
sem ENDED. A API respondeu 200 em live/ready e a credencial foi aceita em edge/me,
correspondendo à câmera privada configurada; nenhum token foi impresso.

O processo filho da API em modo watch iniciou às16:44:25, imediatamente depois
da gravação às16:44:22. O comando antigo recompilava contratos importados por
essa API. Isso é compatível com reinício causado pela recompilação; não havia
captura da conexão original para atribuir sua causa com certeza. A execução
original foi **parcial**, independentemente dos testes anteriores aprovados.

Correções em package.json e scripts/demo/simulate.mjs:

- demo:simulate executa apenas a CLI; dev:api já prepara os contratos. Evita
  escrever nos módulos observados pela API durante a demonstração.
- Até quatro tentativas para conexão/timeout e HTTP502/503/504, com pausas
  de500/1000/2000ms. IDs, timestamps, sequência e corpo permanecem iguais por
  requisição, inclusive quando a resposta se perde depois de uma gravação.
- Falhas definitivas de credencial não são repetidas. Falha persistente da API
  informa API_UNAVAILABLE e exit1. ENDED só é anunciado após resposta aceita;
  falha ao encerrar informa ENDED_NOT_CONFIRMED sem ocultar o erro original.
- scripts/demo/simulate.test.mjs e test:demo exercitam exclusivamente transporte
  HTTP sintético local; não substituem o teste com PostgreSQL real. Roteiro e
  comandos foram atualizados, sem novas dependências, migração ou alteração privada.

Verificações executadas nesta correção:

| Comando/ação | Resultado |
| --- | --- |
| Get-CimInstance de processos Node; GET live/ready/edge/me; consulta Prisma somente leitura | Reinício no intervalo da falha; API/token válidos; incidente preservado, encerramento original não confirmado |
| `pnpm.cmd test:demo` | **4/4 aprovados**: falhas transitórias/resposta perdida, envelope estável, falha original preservada quando ENDED também falha, recusa403 sem retry e limite de quatro tentativas de rede |
| `pnpm.cmd exec eslint scripts/demo` | Primeira passagem encontrou no-unsafe-finally; propagação de erro movida para depois do finally; nova passagem aprovada |
| `pnpm.cmd exec prettier --write scripts/demo/simulate.mjs scripts/demo/simulate.test.mjs package.json` | Formatação aplicada |
| `pnpm.cmd exec node tests/e2e/run.mjs --grep 'simulador real' --project desktop` | Tentativa inicial recusada porque pnpm exec não fornece npm_execpath; container próprio removido |
| `$env:npm_execpath = (Resolve-Path -LiteralPath '.local/tools/pnpm/node_modules/pnpm/bin/pnpm.cjs').Path`; `node tests/e2e/run.mjs --grep 'simulador real' --project desktop` | **1/1 aprovado**, API/web/PostgreSQL exclusivos; 201+dez200, incidente/aviso únicos, heartbeat periódico/ENDED, revisão/desfecho persistidos; build web/TypeScript aprovado |

O runner foi iniciado diretamente usando os builds existentes para não recompilar
os módulos observados pela API pessoal durante o diagnóstico. O container exclusivo
foi removido ao terminar. Nenhum novo incidente foi criado na demonstração do
fundador, nenhuma credencial foi rotacionada e nenhum processo dele foi parado.
O roteiro original continua válido, com o comando corrigido; executar novamente
cria outro incidente de teste. Para continuar a revisão basta usar o já existente.

Não foram repetidas nesta correção as suítes completas de API/contratos, testes
móveis ou teclas interativas: API, contratos e interface não foram alterados.
