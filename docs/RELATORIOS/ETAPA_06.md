# Etapa 06 — Webcam, disponibilidade e recuperação

Data: 21–22/10/2026, America/Sao_Paulo.
Status: **CONCLUÍDA no escopo da bancada** — piso próprio, inferência contínua,
pausa, retomada e encerramento no painel confirmados pelo fundador em 22/10.
Pose falsa na estante, fluidez e evento LIVE positivo permanecem para validação
e melhorias do MVP, sem prometer eficácia não medida.
Ambiente: Windows 11 Pro 10.0.26200 x64; PowerShell 5.1; Ryzen 5 5625U,
6 núcleos/12 threads, 15,4 GiB RAM; Python 3.12.15, uv 0.13.4,
Node 24.22.1, pnpm 10.34.7; MediaPipe 1.1.1,
único fornecedor cv2 opencv-contrib-python 5.0.0.93.
Base: main `27801425f274cc9412e8e52d7affb8e8c0d1f472`, etapa 05.
Commit/push autorizados pelo fundador após a validação em 22/10/2026; sem deploy.

## Resultado entregue

Adaptador nativo WEBCAM, diagnóstico/probe, captura isolada, frames mais recentes,
modelo Full explícito, calibração própria, controles locais e saúde atual.
Heartbeat e entrega HTTP independem da inferência e um do outro. SQLite mantém
eventos, episódio ativo e diagnósticos; limites interrompem novas inferências
antes de emitir evento sem espaço. A API e o painel existentes foram reutilizados.

Captura física e inferência em um frame passaram inicialmente. Pausar liberou o driver;
retomar abriu o mesmo índice com frame novo e relógio crescente. Isso não prova
pose adequada, postura no chão nem incidente LIVE. O fundador inicialmente não
conseguia mostrar o chão; depois confirmou a prévia/enquadramento. Ainda falta
calibração e validação contínua naquele momento. Em 22/10, calibração v1 e sessão
contínua com pose no corpo foram confirmadas; detalhes abaixo. Em seguida, o
fundador conferiu pausa, retomada e encerramento no painel. Os critérios da 06
foram atendidos no ambiente de bancada, com os limites descritos neste relatório.

## Sessão física contínua de 22/10/2026

Relatório privado `619d6049-3270-4c54-8923-978bbe814eb9`, run
`04f31858-98d6-4705-8bf4-1a6c53afbce3`. Calibração v1 da câmera WEBCAM/índice 0,
sete pontos, salva às 11:11:21 no fuso America/Sao_Paulo; metadata validada por
load_calibration. O fundador conferiu piso e esqueleto no corpo.

| Medida | Resultado |
| --- | --- |
| Modo/modelo | LIVE, Full fixado, CPU/VIDEO, 640×480/DSHOW |
| Duração total do relatório | 83,72 s, incluindo setup e encerramento |
| Frames adquiridos/consumidos/substituídos | 2.116 / 385 / 1.731; consumo do mais recente, sem fila de atraso |
| Análises | 384; vazão global 4,59 análises/s, não FPS instantâneo de captura |
| Inferência média/mínima/máxima | 25,34 / 11,81 / 40,58 ms |
| Qualidade de pose por observação | 122 ONE_VALID_POSE, 175 LOW_CONFIDENCE, 70 NO_POSE, 17 MULTIPLE_POSES |
| Elegibilidade temporal | 11.046 ms elegíveis em 79.250 ms observados, conforme agregação do motor |
| Candidatos/eventos | 0 / 0; outbox sem itens na consulta SQLite somente leitura |
| Heartbeat final | ACCEPTED, ENDED; 39 sequências na sessão |
| Encerramento | status ok, sem erro registrado |
| CPU/RAM do processo principal | CPU média 23,33% de um núcleo lógico; pico 233.713.664 bytes; exclui filho de captura |

O fundador relatou esqueleto numa estante quando saiu do enquadramento. É falso
reconhecimento visual observado, sem gravação/anotação temporal que permita
separar os intervalos humanos/objeto nos agregados. Zero eventos não demonstra
que toda pose de estante foi rejeitada por confiança, nem que objetos não poderão
gerar falsos alertas em outras condições. Registrar ensaio negativo delimitado
antes de afirmar melhoria; não elevar/reduzir gates arbitrariamente.

A prévia atual desenha junto com as análises (alvo 5 Hz), o que limita a fluidez
mesmo com captura mais rápida. Não houve suavização/reutilização artificial de
poses nem alteração de modelo/política para melhorar aparência ou números.

O fundador confirmou que ainda não conferiu pause/resume no painel. A revisão
do controle encontrou espera sobre Event de captura já sinalizado durante pausa,
com risco de busy loop, e ausência de processamento da GUI quando não há frame.
LIVE agora usa espera limitada independente da captura e poll não bloqueante;
Espaço/Q e comandos de terminal funcionam durante pausa sem reabrir câmera para
encerrar. FILE mantém a pausa bloqueante e o relógio de mídia. Duas regressões
novas verificam GUI e pipeline com adaptador sintético/SQLite real. A fixture
inicial não incluía geometry/exhausted e foi completada; não era evidência física.
Suíte completa: 242 testes Python aprovados em 12,06 s, GUI sintética habilitada;
Ruff check/format aprovados. Modelo e gates preservados. O limite privado para a
próxima sessão guiada passou de 120 para 600 s, sem mudar fonte ou fingerprint
da decisão; exemplo público continua 120 s. Nenhum teste físico novo foi aberto
pela IA nessa revisão.

## Arquivos e decisões

Atualização posterior da validação de controles: fundador confirmou LIVE e
depois Pausada no painel. O registro da sessão anterior estava desatualizado e
sem processo ativo; não foi tratado como worker ainda em execução. A IA iniciou
uma sessão nova (`61ab8be4-f511-4f9f-bef7-ed42c67a4c90`) com a mesma câmera,
calibração/modelo e sem gravar imagens. `control --action pause` resultou em
PAUSED atual confirmado no status local e no banco; `control --action resume`
resultou em RUNNING, mesma sessão, sequence 18 e frame com idade 15 ms na consulta.
Heartbeat aceito; servidor mostrou DEGRADED/LOW_LIGHT, sem mascarar a baixa luz.
Comandos feitos pela IA para reduzir a interação manual; fundador confirmou
imagem em movimento e saída de Pausada após resume. Depois de `control --action
stop`, confirmou fechamento da janela e Fonte encerrada no painel. Metadados em
`.local/etapa06/guided-controls-observations.jsonl`; log privado do processo.

Relatório final dessa sessão: `3285821f-f067-42b3-84fb-fe2d21a831cf`, 981 análises
em 231,23 s totais (inclui pausa), inferência média 20,82 ms, zero candidatos e
eventos, sem erro. Os estados de pose foram 525 NO_POSE, 449 LOW_CONFIDENCE e sete
MULTIPLE_POSES: sessão de controles perto do teclado, não prova de boa pose corporal.
Heartbeat final ENDED aceito, servidor SOURCE_ENDED, processo retornou exit 0.
O lock da bancada foi adquirido/liberado depois do término sem abrir a câmera,
confirmando ausência de outro detentor. O fundador confirmou os estados visuais;
a sessão anterior de 384 análises é a evidência de pose no corpo.

Verificação adicional de falha de captura com buffers compartilhados reais e
driver/processo sintéticos confirmou descarte do slot anterior, índice/timestamp
crescentes após recuperação e teto de duas reconexões sem loop infinito. Não
foi apresentada como interrupção física de dispositivo. Suíte final: **243 testes
Python aprovados em 15,28 s**, Ruff check/format aprovados.

Finalização da configuração de uso: diagnóstico usou reconnectAttempts=0. Para
as próximas execuções, `.local/edge-webcam.yaml` passou a três tentativas, com a
mesma câmera/modelo/piso e limite de 600 s. O YAML anterior ficou em
`.local/edge-webcam-validation-20261022.yaml`; SQLite de validação preservado.
Como o fingerprint conservador inclui a política operacional da fonte, a
configuração normal usa `.local/edge-webcam/outbox-live.sqlite`, sem reescrever
execuções antigas. Consulta anterior confirmou zero pendências. EventRuntime
aceitou o fingerprint novo em verificação local sem câmera/HTTP, com fila vazia.
Nenhum histórico, episódio ativo ou evento pendente foi apagado.

- `services/edge/src/radar_edge/webcam.py`: processo spawn, slot compartilhado
  de 3.932.160 bytes, índice/backend explícitos, aquisição monotônica, descarte de
  frames antigos, lock de bancada, reconexão limitada, timeout e liberação.
- `live.py`, `health.py`: pipeline LIVE, status privado, pausa/retomada/reconnect,
  heartbeat atual de 5 s/mudanças, conflito de run e transporte independente.
- `config.py`, `cli.py`, `calibration.py`, `observations.py`, `preview.py`:
  configuração FILE/WEBCAM, CLI, piso por câmera/índice/geometria e rótulo LIVE.
- `event_runtime.py`, `pipeline.py`: sessão nova versus execução SQLite retomada,
  episódio ativo preservado, entrega assíncrona e heartbeat também no FILE com
  eventos habilitados. Relatório de FILE mantém o ID persistente e acrescenta
  `captureRunId`. Eventos já gravados não são reescritos.
- `delivery.py`, `outbox.py`: ACK por modo, jitter/Retry-After, erros permanentes,
  AUTH_BLOCKED, limite por itens/bytes e limpeza restrita de confirmados antigos.
- `scripts/setup-worker.ps1`: preparação privada sem digitar token; modo clipboard
  automático testado com conteúdo fictício, sem consultar clipboard real da IA.
- `services/edge/webcam.example.yaml`, `edge.example.yaml`: configuração pública
  sem segredos, defaults de timeout/limites alinhados à arquitetura.
- `apps/api/test/resilience.test.mjs`, `scripts/test-api.mjs`,
  `services/edge/tests/resilience_api_probe.py`, `test_webcam.py`,
  `test_live_health.py`: regressão e falhas controladas em recursos exclusivos.
- Documentos de arquitetura/operação, decisões D35–D38, status e
  [roteiro manual](../VALIDACAO_MANUAL_ETAPA_06.md).

Sem dependências, lockfiles, contratos públicos ou migrações novos. Proprietário,
catálogo anterior, serviço 5432, PostgreSQL 15432, calibrações FILE e outboxes
anteriores preservados. Somente a credencial da câmera escolhida foi emitida pelo
fundador no painel; testes de revogação usaram credenciais sintéticas dedicadas.

Full: `pose-landmarker-full-float16-v1`, CPU/VIDEO, até duas poses,
9.398.198 bytes; SHA-256
`5134a3aad27a58b93da0088d431f366da362b44e3ccfbe3462b3827a839011b1`.
Política floor-v0.1 e gates preservados; Lite continua disponível nos arquivos.

Fontes técnicas consultadas: os timeouts de leitura/abertura do OpenCV são
documentados para FFmpeg/GStreamer; isso não garante timeout no DSHOW. Essa
limitação fundamenta o processo isolado. [OpenCV 5 — flags de vídeo](https://docs.opencv.org/5.0/main_modules/videoio_flags_base.html).
Spawn e substituição do IPC após término forçado seguem os cuidados descritos
em [Python 3.12 — multiprocessing](https://docs.python.org/3.12/library/multiprocessing.html).

## Verificações reais

Comandos executados na raiz, com `. ./scripts/activate.ps1` em cada terminal e
`PYTHONIOENCODING=utf-8` para o Python. Logs/resultados privados em `.local/etapa06`.

| Comando/ação | Resultado observado | Evidência/limitação |
| --- | --- | --- |
| Inventário com git status, rg e leitura dos documentos/código | Base limpa no início; trabalho da 06 preservado durante retomadas | Nenhum reset/checkout destrutivo |
| `radar-edge probe --config .local/edge-webcam.yaml --seconds 5` via uv frozen | Primeiro ensaio físico: 56 aquisições, 54 consumidas, 2 substituídas; taxa de consumo 10,437 FPS | Sem inferência; nome antigo da métrica corrigido para separar aquisição/consumo |
| `radar-edge doctor --config .local/edge-webcam.yaml` via uv frozen | Câmera física 640×480, Full carregado e executado, 11,9295 ms de inferência, zero poses | Um frame; sem piso; não demonstra detecção de pessoa |
| `uv run --project services/edge --frozen python .local/etapa06/physical-adapter.py` | Probe final: 51 frames em 5 s, aquisição e consumo 10,0 FPS; 0 substituídos; pausa liberou driver, retomada gerou índice e timestamp maiores | Índice 0 escolhido pelo fundador, DSHOW; sem modelo/gravação nesse ensaio |
| `uv run --project services/edge --frozen python .local/etapa06/abrupt-orchestrator.py` | Processo físico com heartbeat encerrado abruptamente; filho de captura saiu em até 4 s, webcam reaberta; após 16 s sem heartbeat, servidor OFFLINE | Somente processo próprio, PID/ancestralidade verificados; sem inferência/piso; não é conferência visual do painel |
| Inventário CIM do Windows | Positivo Theia Camera com status OK; Camera DFU Device também listado | Nome não foi associado visualmente à imagem pelo fundador |
| `setup-worker.ps1 ... -FromClipboard`, pelo fundador | Salvamento privado confirmado, sem digitação de token | A primeira versão exigia Enter e foi simplificada após dificuldade real |
| GET `/v1/edge/me` via HTTPX lendo somente o arquivo privado | HTTP 200, câmera `5be84234-7b00-4e87-85e8-b0e68f7c2a6d` | Nenhum segredo incluído na saída do teste |
| `uv run --project services/edge --frozen radar-edge run --config .local/edge-webcam.yaml --no-preview` | Exit 1 esperado: CALIBRATION_REQUIRED, 0 análises; heartbeat ERROR aceito | Sem fingir piso calibrado; relatório `6364af47-3587-4173-b144-f2e96f6267ab` |
| `node --env-file=apps/api/.env .local/etapa06/health-check.mjs` | Consulta somente de leitura confirmou heartbeat LIVE/ERROR/CALIBRATION_REQUIRED persistido; função de saúde dá DEGRADED no recebimento e OFFLINE na consulta posterior | Estado calculado pelo código real do servidor; não é conferência visual do painel |
| Testes PowerShell do setup com Get-Clipboard fictício | Aguarda mudança, salva token fictício válido, rejeita texto errado sem arquivo | Clipboard real não acessado pela IA; ParseFile também passou |
| `pnpm.cmd test:api` | 125 testes aprovados: 19 acesso, 104 eventos, 1 replay Python e 1 cenário de resiliência com várias falhas | PostgreSQL/API/tenant/câmera/token/outboxes exclusivos, containers removidos ao final |
| `uv run --project services/edge --frozen pytest services/edge/tests -q` com `RADAR_TEST_GUI=1` | **240 aprovados** na rodada final (14,15 s), incluindo janela sintética; nenhuma omissão | Antes: 236 + 1 omitido, depois 237/239; acrescentados testes de lock e FPS por tempo de cena no replay |
| `pytest .../test_webcam.py .../test_live_health.py -q` via uv frozen | Capture slots, idade, repetição, driver, lock, saúde, capacidade, ACK e HTTP bloqueado aprovados | Fixtures sintéticas, sem alegar câmera física por esses testes |
| `pnpm.cmd test:contracts` | 87 TS + 87 Python aprovados | Contratos gerados preservados |
| `pnpm.cmd typecheck` | Web/API/contracts aprovados | Sem mudança de schema público |
| `pnpm.cmd build` | Web/API/contracts aprovados | Build não substitui validação física |
| `pnpm.cmd lint:edge` | Ruff check/format aprovados | Sem novos fornecedores cv2 |
| `pnpm.cmd lint` | ESLint e Prettier aprovados na rodada final | Aviso inicial de formatação corrigido no harness |
| `git diff --check` e `git check-ignore` dos arquivos privados | Sem whitespace inválido; credencial/YAML/SQLite ignorados pelo Git | Nenhum arquivo privado preparado para versionamento |
| `pytest services/edge/tests/test_pose_pipeline.py::test_portrait_display_and_clicks_keep_normalized_calibration services/edge/tests/test_preview.py -q` via uv frozen, após esclarecer a janela parada | 18 aprovados; Ruff check/format e diff check também passaram | Somente título/mensagem e roteiro alterados; não abriu outra webcam nem calibrou o piso |
| `radar-edge run --config .local/edge-webcam.yaml --preview` e `control --action pause/resume/stop`, via uv frozen | Sessão guiada física de 981 análises, PAUSED → RUNNING com frame novo → ENDED; exit 0, API confirmou SOURCE_ENDED | Fundador confirmou pausa, imagem retomada e fechamento/Fonte encerrada; nenhuma imagem gravada |
| `uv run --project services/edge --frozen pytest services/edge/tests -q`, RADAR_TEST_GUI=1, após teste de recuperação | 243 aprovados, nenhuma omissão; `pnpm.cmd lint:edge` aprovado | Recuperação do adaptador e limites de reconexão injetados; não confundir com hardware |
| Consulta de status/relatórios, SQLite somente leitura, lock de bancada e EventRuntime local | Estados/encerramento conferidos, lock livre, nenhuma pendência na fila, configuração normal aceita | Só metadados; não abriu outra câmera nem enviou HTTP nessa validação de configuração |
| Auditoria final do Git e segredo privado | 29 arquivos alterados/novos versionáveis examinados sem encontrar o token real; YAML, credencial, piso, SQLite e backup privado ignorados | Comparação local sem exibir o segredo; `pnpm.cmd lint` e `git diff --check` finais aprovados |

As primeiras rodadas encontraram e corrigiram: compatibilidade de configurações
FILE antigas sem kind explícito, fixture Prisma com tenantId redundante em
Device aninhado, relógio de retry do harness que não avançava entre processos,
path absoluto no script de credencial e formatação de `scripts/test-api.mjs`.
O teste não foi reduzido para passar. Os failures de credencial mostrados pelo
fundador eram locais ao clipboard; a API só foi validada após o salvamento.
O primeiro orquestrador físico de morte abrupta recusou agir porque o redirector
do Python no Windows tinha PID diferente do interpretador. A segunda tentativa
verificou a relação pai/filho e o caminho do processo próprio antes de encerrá-lo;
nenhum processo foi selecionado apenas pelo nome.

## Critérios da etapa

| Critério | Verificado / pendente | Evidência |
| --- | --- | --- |
| Webcam real aberta/liberada, backend/resolução/FPS | Verificado | Probe físico e pausa/retomada; DSHOW, 640×480, 10,0 FPS medidos |
| Inferência Full em câmera real | Verificado na sessão de 22/10 | 384 análises, pose no corpo conferida; falso reconhecimento visual de estante relatado; não é eficácia certificada |
| Calibração própria e conferência da prévia | Verificado | WEBCAM v1/índice 0, sete pontos; piso e corpo conferidos pelo fundador; nenhuma calibração FILE aplicada |
| Frames limitados, novos, idade e reconexão | Verificado no adaptador/controlado | Slot único, rejeição de frame velho/repetido, término limitado, novo IPC |
| Heartbeat sem esperar inferência/entrega | Verificado controlado | POST de evento bloqueado enquanto heartbeat avança e marca LOW_FPS/FRAME_TIMEOUT |
| API fora/restart/retorno e ACK perdido | Verificado real em recursos sintéticos | Novo processo Python conserva payload/eventId, um incidente por episódio |
| Revogação, erro permanente, relógio/atraso | Verificado real em recursos sintéticos | AUTH_BLOCKED/retomada explícita; PERMANENT_ERROR sem retry; DELAYED/CLOCK_UNCERTAIN sem urgência |
| Lease/conflito/PAUSED/SOURCE_ENDED/OFFLINE | Verificado nos escopos descritos | Lease/conflito e expiração controlados na API; pausa/retomada/fim físicos e visuais confirmados pelo fundador; baixa luz indicada pelo servidor |
| Morte abrupta com driver/heartbeat | Verificado físico no adaptador/servidor | Processo próprio interrompido, filho saiu, webcam reabriu e servidor OFFLINE; sem inferência nesse ensaio; não houve conferência visual de OFFLINE pelo fundador |
| Retomada e encerramento no painel | Verificado físico/visual | Fundador confirmou imagem retomada, saída de Pausada, fechamento da janela e Fonte encerrada |
| Limite local e preservação de pendentes | Verificado controlado | Capacidade antes de decisão, reserva e limpeza só de confirmados/episódios inativos |
| Evento LIVE positivo por visão (validação final) | Não observado | Pendência prevista para etapa 08, conforme prompt da 06; não substituir por fixture/REPLAY |

## Como reproduzir

Siga o [roteiro PowerShell completo](../VALIDACAO_MANUAL_ETAPA_06.md). A configuração
privada desta bancada é `.local/edge-webcam.yaml`, câmera WEBCAM com ID começando
em `5be84234`, índice 0/DSHOW e `.local/webcam-device.json` já autenticado.

Quando houver piso visível e câmera estável:

```powershell
. ./scripts/activate.ps1
uv run --project services/edge --frozen radar-edge calibrate --config .local/edge-webcam.yaml --frame-ms 0
```

Essa janela usa uma imagem parada. Marque somente o piso (pelo menos três pontos
em ordem) e Enter. Somente após salvar com sucesso, execute separadamente:

```powershell
uv run --project services/edge --frozen radar-edge run --config .local/edge-webcam.yaml --preview
```

Confira corpo,
piso e modo LIVE localmente; abra `/fontes`. Use outro terminal ativado para
control pause/resume/reconnect/stop, conforme o roteiro. Nenhuma queda deve ser
provocada. O YAML privado foi ampliado para 600 s em 22/10 (antes 120 s), para
dar tempo ao teste guiado de controles. Os ensaios de diagnóstico usaram zero
reconexões; configuração normal final e exemplo/default permitem três. YAML e
SQLite de diagnóstico preservados; a outbox normal agora é outbox-live.sqlite.

## Falhas, limites e pendências

Uso manual posterior: o fundador abriu calibrate esperando vídeo ao vivo e
interpretou o frame parado como travamento. A janela de seleção usa um frame
estático por definição; a imagem enviada mostrava o chão fora do enquadramento.
Título/terminal agora explicam IMAGEM PARADA e cancelamento, e o roteiro separa
probe ao vivo, calibração e run em comandos individuais. Não há nova calibração
nem evidência de inferência física contínua por essa interação.

Em seguida, a prévia probe apareceu preta. Uma tentativa diagnóstica de medir
somente estatísticas dos pixels retornou WORKER_LOCKED porque a prévia do fundador
ainda ocupava a câmera; seu processo foi preservado. O fundador confirmou que a
tampinha de privacidade estava fechada. Não foi identificada falha de renderização
por essa ocorrência e não houve alteração de backend/permissões. Falta conferir
visualmente a imagem com a tampa aberta e preparar o enquadramento/piso; isso
não comprova calibração, pose contínua ou evento LIVE.

Após esclarecer que o teste inicial é feito em pé, sem falar no chat durante
a execução, o fundador respondeu que o enquadramento deu certo. Isso registra
a conferência da prévia em movimento; probe não carrega modelo. A calibração
da webcam e a conferência integrada de pose/painel ainda não foram concluídas.

Na tentativa seguinte pela IA, `uv run --project services/edge --frozen radar-edge
calibrate --config .local/edge-webcam.yaml --frame-ms 0` retornou
`CONFIG_OR_ENVIRONMENT_ERROR`, error_type ValueError, antes de uma marcação
confirmada. A causa não foi identificada. Consulta posterior confirmou ausência
de `.local/calibration-webcam.json` e nenhum processo de calibração/captura em
execução. Essa falha precisa ser investigada; não foi tratada como calibração
salva nem atribuída à tampa ou à imagem estática sem evidência.

As pendências iniciais de calibração, sessão física contínua e controles no painel
foram atendidas em 22/10, com confirmação do fundador. Nenhuma verificação
obrigatória da 06 pendente no escopo do prompt. Para a avaliação final, falta
ensaio negativo delimitado para investigar a estante; não declarar rejeição garantida.
Morte abrupta/liberação/expiração foram testadas no adaptador físico com heartbeat,
sem inferência naquele ensaio. A sessão contínua posterior tem as medidas acima;
evento LIVE positivo ainda não foi observado. Um frame no doctor não certificava 5 Hz.
O inventário da câmera não comprova orientação/enquadramento visual.

Flags de congelamento (pixels idênticos por 10 s) e baixa luz (luminância abaixo
de 25 por 2 s) são heurísticas. Cena imóvel e bloqueio de lente podem se parecer;
nenhuma pose detectada não comprova ausência de pessoas. Limitações de perspectiva
do detector 2D e gate de múltiplas poses continuam. CPU/RAM do processo principal
não incluem o filho de captura; não foram apresentadas como consumo total.

O fundador colou a credencial no terminal/chat após ela já estar salva. Não foi
copiada para arquivos públicos, logs ou este relatório. Recomenda-se rotacioná-la
no painel e salvar outro arquivo privado antes de reutilização fora deste ensaio;
nenhuma rotação/revogação de sua credencial foi feita automaticamente.

Por crescimento do histórico técnico, SQLite pode atingir o teto mesmo com
payloads confirmados removidos; o comportamento é falhar fechado, sem VACUUM ou
purga de pendentes automática. Retenção global e snapshots continuam na etapa 07.
Ausência total de tráfego nativo do SDK não foi comprovada; a ressalva D30 permanece.

## Próxima etapa elegível

Registro histórico da retomada, antes da validação física de 22/10/2026:
inventário de leitura confirmou .envs, node_modules,
ambiente Python, YAML da webcam e arquivo privado da credencial existentes;
calibração da webcam continua ausente. `docker info --format '{{.ServerVersion}}'`
respondeu 29.1.3. Consultas HTTP de até 3 s à API `/v1/health/live` e ao painel
retornaram indisponibilidade. Essas verificações não iniciaram serviços nem
reexecutaram os testes de 21/10. O roteiro manual ganhou sequência após reboot,
com terminais separados e resultados esperados; erro de calibração permanece
pendente. `git diff --check` verificou a alteração documental.

**Etapa 07 elegível somente com nova solicitação do fundador.** A 06 foi encerrada
após suas confirmações visuais e as verificações descritas. O relato de estante
continua como limitação observada; zero eventos nestes ensaios não o resolve.
Evento LIVE positivo e eficácia/negativos anotados permanecem para a validação
final da etapa 08. Não implementar 07/08 automaticamente.
