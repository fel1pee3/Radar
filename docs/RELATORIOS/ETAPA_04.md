# Etapa 04 — Visão computacional em arquivo

Data: 21/10/2026. Status: **CONCLUÍDA** no escopo de visão em arquivo.
Base: main, `0a528d4`, árvore inicialmente limpa. Sem commit, push ou deploy.
Ambiente: Windows 11 Pro 10.0.26200 x64, PowerShell 5.1; Ryzen 5 5625U,
6 núcleos/12 threads,15,4 GiB RAM. Python 3.12.15 nativo/uv 0.13.4,
MediaPipe 1.1.1, único opencv-contrib-python 5.0.0.93/cv2 5.0.0.

## Resultado entregue

Pipeline FILE real, sequencial e local: decode FFmpeg → orientação → resize
proporcional até640px de largura → amostragem por mídia → Tasks VIDEO/CPU →
observações corporais estruturadas → prévia opcional e relatório privado.
Até duas poses e máscaras desligadas. Configuração, fonte, estimador,
observação, calibração, janela e medições ficam em módulos separados.

`env` mantém o diagnóstico de imports. `model-fetch` obtém o bundle oficial
fixado por hash. `doctor` abre o primeiro frame e executa o modelo; `calibrate`
oferece escolha gráfica ou pontos manuais confirmados; `run` exige ROI compatível.
A configuração privada começa sem autorização presumida de vídeo pessoal.

Comprovado: modelo real carregado e executado sobre arquivo sintético sem pessoa
e sobre um arquivo autorizado com pessoa, decode/amostragem, ausência de pose,
replay equivalente, janela real e encerramento. O fundador selecionou o piso na
GUI, pressionou Enter e confirmou que o esqueleto acompanha o corpo e o contorno
corresponde ao piso. Os três replays reais terminaram normalmente, com 89
observações cada. A etapa ficou inicialmente parcial por falta do vídeo; o
fundador depois o forneceu na pasta reservada do projeto. Não se pesquisaram
pastas pessoais nem se enviaram frames ao chat para inspeção pelo agente.

Não há motor temporal, decisão de queda, incidentes, HTTP de ingestão, heartbeat,
webcam, RTSP, outbox, snapshot ou streaming web nesta implementação. API, web,
PostgreSQL da demo em15432 e outro servidor5432 permaneceram preservados.

## Arquivos e decisões

| Área | Arquivos/decisões |
| --- | --- |
| Configuração | services/edge/edge.example.yaml e radar_edge/config.py; YAML safe_load, validação Pydantic fechada, autorização explícita, tipo FILE apenas, saídas/modelo/calibração privados |
| Fonte/tempo | source.py: FileSource/FrameSource, Frame/Geometry, MediaClock, MediaSampler; PTS da mídia, fallback índice/FPS válido e registrado; rotação metadata/override; pixels quadrados |
| Modelo | model.py: URL, ID e hash imutáveis; download explícito; arquivo divergente não carrega; estimator.py: interface PoseEstimator e adapter Tasks real CPU/VIDEO |
| Observações | observations.py: run/frame/tempo/dimensões/poses/qualidade/modelo/calibração; corpo11–32; ausente/não finito vira null, nunca coordenada zero |
| Calibração | calibration.py: polígono simples normalizado,3–32 pontos, área técnica mínima; seleção confirmada; ID/versão, geometria/câmera/instante; revisões privadas sem imagem |
| Prévia | preview.py: pose suficiente para desenho, ROI e legenda REPLAY/sem classificação; janela opcional, Q/Esc/fechar, cleanup |
| Pipeline/medidas | pipeline.py, metrics.py, errors.py, cli.py; agregados limitados e JSON/JSONL privados; erro explícito sem traceback/caminho pessoal; contadores de processo Windows |
| Ambiente | pyproject.toml/uv.lock; PyYAML 6.0.3 novo, NumPy 2.5.4 já existente agora direto;42 pacotes, sem trocar família de visão ou fornecedor cv2 |
| Testes | conftest.py, test_video_source.py, test_calibration.py, test_pose_pipeline.py; contratos Python anteriores preservados |
| Documentação | README central/edge, STATUS, ambiente/comandos, decisõesD27–D30, inventário, roteiro 04 e este relatório |

Não houve migração, alteração de API/painel/simulador ou pnpm-lock. Pesos, vídeos,
configurações e resultados ficam ignorados. Observações detalhadas opt-in, no
máximo1000/10 MiB no exemplo (configuração limitada a10000/50 MiB). Atingir limite
marca truncamento e continua a inferência. Sem buffers contínuos ilimitados.

Decisões técnicas relevantes:

- PTS é normalizado para início relativo da mídia e deve crescer em ms. Se
  indisponível/repetido, fallback permanente índice/FPS somente quando válido e
  permitido; não voltar ao relógio anterior nem fabricar continuidade somando1ms.
  Fallback que ficaria atrás do último PTS interrompe com erro. Isso pode exigir
  converter arquivo VFR/metadata defeituosa; não oferece precisão fictícia.
- Decode sequencial também lê os frames pulados por amostragem. Falha anterior
  à contagem declarada é DECODE_ERROR; contagem desconhecida é END_UNVERIFIED,
  não EOF declarado como sucesso. Metadados inconsistentes podem dar falso erro;
  a API OpenCV não permite provar toda forma de corrupção no último frame.
- Rotação automática do decoder é desativada antes de aplicar metadata/override,
  evitando rotação dupla. Resize não amplia fontes menores; não corta ROI.
- Mudança de câmera/orientação/proporção bloqueia execução. Escala com mesma
  proporção reutiliza coordenadas; deslocamento físico/enquadramento não é detectado.
- Qualidade distingue NO_POSE, MULTIPLE_POSES, LOW_CONFIDENCE e ONE_VALID_POSE.
  DARK_FRAME é diagnóstico instantâneo, não a política temporal LOW_LIGHT da 05.
  Não existe probabilidade de emergência nesses valores de qualidade.
- Velocidade do replay altera somente espera de apresentação. Não descarta
  observações para acompanhar o relógio de parede. Throughput não é sampling FPS.

## Modelo, termos e material

Bundle:`pose-landmarker-lite-float16-v1`,5.777.746bytes,
SHA-256 `59929e1d1ee95287735ddd833b19cf4ac46d29bc7afddbbf6753c459690d574a`.
[URL oficial versionada](https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task).
O [Model Card vinculado pelo catálogo oficial](https://storage.googleapis.com/mediapipe-assets/Model%20Card%20BlazePose%20GHUM%203D.pdf)
declara Apache 2.0 para Lite/Full/Heavy; não se deduziu licença dos pesos da licença
de exemplos. Origem, avisos e limites no [inventário](DEPENDENCIAS_E_MODELOS.md).

Vídeo de infraestrutura gerado localmente, sem pessoa: `synthetic-04-infrastructure`,
SHA-256 `e396a18be5813bc10d79a776613a03a27875dfdcbc829e50d635bdbf93de3dfe`,
320×240,10fps,20frames/2s, MJPEG/AVI. Há também MP4 sintético com matriz de rotação
nos testes. Esse material comprova infraestrutura, sem representar pessoa real.

Arquivo autorizado: `bancada-01`, **4.744.892 bytes**, SHA-256
`3c361aee3f49e2e6ac2688e3afb53622ffd15451ead69874b3e0a76c9cd090c0`.
O fundador o forneceu em `.local/videos/` e pediu processamento local; o nome
original permanece privado em `.local/edge.yaml`. Origem/autoria não foram
verificadas independentemente e não há autorização presumida de redistribuição.
Manifesto privado `.local/etapa04/video-manifest-bancada-01.json` usa os pseudônimos
`participant-01`, `session-04-01`, `environment-04-01`, papel CALIBRATION. A cena
foi conferida pelo fundador quanto a pose e piso; não houve anotação de atividade
ou verdade de referência para quedas. Retenção OWNER_MANAGED, sem data automática
de exclusão configurada. Vídeo, calibração, modelo e saídas continuam ignorados.

## Comandos e verificações reais

| Comando/ação efetivamente executada | Resultado/limite |
| --- | --- |
| Leitura do anexo, AGENTS/README/STATUS/etapa 04/referências, relatórios03/inventário; git status/log, rg --files | Base limpa em 0a528d4; Python anterior só env/contratos; sem vídeo nos diretórios de teste previstos |
| `. ./scripts/activate.ps1`; Get-CimInstance SO/CPU; `uv run --project services/edge --frozen radar-edge env` | Ambiente acima; WIN32UI/FFMPEG e um fornecedor cv2; sem câmera |
| Inspeção inspect.signature/source da API MediaPipe instalada; consulta de documentação oficial Python, catálogo/model card e OpenCV | API confirmada na 1.1.1; VIDEO/detect_for_video, CPU, duas poses, masks=false; termos do modelo identificados |
| Consulta PyPI PyYAML/json; `uv add --project services/edge 'PyYAML==6.0.3'`; `uv add --project services/edge 'numpy==2.5.4'` | PyYAML 6.0.3/MIT,42 pacotes; NumPy já existente preservado; lock exato |
| Download HTTPS oficial por script Python privado, SHA-256 e inspeção ZIP; `radar-edge model-fetch` via uv frozen | Bundle/hash/tamanho acima; repetição validou o arquivo existente sem nova gravação |
| `uv run --project services/edge --frozen radar-edge model-fetch --output .local/etapa04/reproduced-lite.task` | Download novo pelo comando entregue; tamanho5.777.746 e SHA-256 idênticos ao bundle fixado; obtenção reproduzida de verdade |
| Consulta de Kaggle/model URL via web/HTTP | Endpoint Kaggle tentado retornou404/inacessível; decisão de licença baseada no Model Card oficial, não nessa consulta |
| `uv run --project services/edge --frozen ruff check services/edge --fix`; `ruff format services/edge` | Primeira passagem encontrou linhas longas/imports; corrigidos; Ruff final aprovado |
| `$env:RADAR_TEST_GUI='1'`; `uv run --project services/edge --frozen pytest services/edge/tests -q` | **139 aprovados**, incluindo 87 contratos anteriores e 52 testes novos/parametrizados; nenhum skipped nessa execução |
| `uv sync --project services/edge --frozen`; `uv build --project services/edge` |42 pacotes conferidos; sdist e wheel reais gerados em services/edge/dist ignorado |
| `pnpm.cmd lint:edge`; `pnpm.cmd check:edge` | Ruff/formatter/imports reais aprovados; env não carrega modelo nem abre câmera |
| `pnpm.cmd --filter @radar/contracts types:check`; `node --test packages/contracts/test/*.test.mjs` | Tipos coerentes e **87 TS aprovados**, sem recompilar módulos observados pela API pessoal |
| `pnpm.cmd exec prettier --write services/edge/edge.example.yaml`; `pnpm.cmd lint` | YAML formatado; ESLint monorepo/scripts/E2E e Prettier aprovados |
| Geração explícita de vídeo/configuração/pontos **sintéticos** em .local/etapa04 | Arquivos privados de infraestrutura; ROI não representa piso escolhido em vídeo de pessoa |
| `uv run --project services/edge --frozen radar-edge doctor --config .local/etapa04/synthetic.yaml` | Modelo real carregado/executado,0poses, firstInference12,40ms, fonte/hash conferidos; sem calibração ainda naquele instante |
| `uv run --project services/edge --frozen radar-edge calibrate --config .local/etapa04/synthetic.yaml --frame-ms 500 --points .local/etapa04/synthetic-points.json --confirm-floor` | Calibração sintética6424c98d…v1 criada, sem salvar frame; exercita validação/persistência, não seleção humana |
| `uv run --project services/edge --frozen radar-edge run --config .local/etapa04/synthetic.yaml --no-preview --export-observations` | ENDED/exit0,20lidos,10analisados,10pulados,10NO_POSE, JSONL limitado e relatório privado |
| Mesmo run com `--no-preview --replay-speed 2 --export-observations` | ENDED/exit0, mesma sequência/contagem/timestamps, throughput diferente conforme tabela abaixo |
| Mesmo run com `--preview --replay-speed 1 --max-observations 3` | Janela real criada/renderizada/fechada, STOPPED_LIMIT/exit0;5lidos,3analisados,2pulados; sem exportação padrão |
| Inspeção visual pelo agente de .local/etapa04/preview-synthetic.png | Imagem sintética, ROI e legenda/tempo/qualidade/inferência legíveis; não inspecionou corpo real ou seleção de piso humana |
| Inventário somente de .local/videos; ajuste privado de .local/edge.yaml, preservando os demais campos e cópia anterior em .local/etapa04/edge-before-real.yaml | Um arquivo fornecido pelo fundador; autorização local registrada; nenhuma busca fora das pastas previstas |
| `uv run --project services/edge --frozen radar-edge doctor --config .local/edge.yaml` | status ok; modelo real executado, uma pose no primeiro frame, inferência de 27,167 ms; calibração ainda ausente nesse instante |
| `uv run --project services/edge --frozen radar-edge calibrate --config .local/edge.yaml --frame-ms 1000` | exit 0; fundador marcou 9 vértices e confirmou com Enter; calibração 1140706f-b0e0-4edb-b5a1-9ad60e8e4453/v1, LOCAL_GUI/operatorConfirmed, frame 30 em 1001 ms; nenhum frame salvo |
| `uv run --project services/edge --frozen radar-edge run --config .local/edge.yaml --no-preview` | ENDED/exit 0; run 3ff93cc4-02ae-4d1e-a28e-6d99fc85e931, arquivo completo; métricas abaixo |
| `uv run --project services/edge --frozen radar-edge run --config .local/edge.yaml --no-preview --replay-speed 2` | ENDED/exit 0; run 03a3749c-d58c-42a3-99b0-dbdcabafa54e, mesma sequência de amostragem e contagens |
| `uv run --project services/edge --frozen radar-edge run --config .local/edge.yaml --preview --replay-speed 0.5` | ENDED/exit 0; run 24fadf57-2d26-4c29-b62d-b49c0eb9423e; fundador confirmou alinhamento do esqueleto e piso; janela fechada no fim |
| Comparação dos três report.json reais e listagem de seus diretórios | Mesmo hash de fonte/calibração/sequência, sem fallback temporal; cada pasta contém somente report.json, sem frames ou JSONL |
| GET locais live/ready/proxy-live e login; docker ps | Todos200; só radar-postgres-1 saudável mantido; nenhum processo/volume do fundador parado |
| Inspeção ZIP do wheel gerado; git check-ignore, diff --check e verificação local de links/segredos | Wheel17 arquivos, sem pesos/mídia/JSONL; modelos/configurações/resultados ignorados; links locais válidos;27 arquivos candidatos inspecionados sem os quatro valores privados comparados; sem erro de whitespace |

Houve uma execução intermediária com136 testes aprovados e2 falhas: import cv2
removido por lint antes de acrescentar o teste MP4; subprocess CLI em Windows
produzia CP1252 enquanto o teste esperava UTF-8. Import restabelecido e CLI passa
a emitir UTF-8 explicitamente, inclusive stderr. Depois,138/138 aprovados.
O ajuste de exibição vertical acrescentou um teste de mapeamento dos cliques
normalizados; a execução final ficou em139/139. A janela ajusta somente a imagem
de exibição para até960×720; dimensões de inferência e coordenadas normalizadas
da calibração continuam referidas à fonte processada, sem cortar o enquadramento.

Os novos testes incluem arquivos ausente/inválido, truncamento injetado, EOF
sem contagem, PTS crescentes/origem/fallback/regressão, rotação0/90/180/270 e
metadata real MP4 comparada à autorrotação do decoder, proporção, erro de
geometria, polígono inválido/cruzado/concavo, compatibilidade, revisão da calibração,
flags de qualidade com dados controlados, ausência de pose com modelo real,
modelo adulterado, erro do modelo, interrupção, fechamento de recursos,
exportação limitada e GUI real em sintético. Múltiplas pessoas foram exercitadas
apenas na lógica com observações sintéticas, não em detecção humana real.

## Medições de infraestrutura — sintético sem pessoa

| Execução | Amostras/mídia | Parede no pipeline | Throughput | Inferência média | CPU processo,1núcleo=100% | Pico working set |
| --- | --- | --- | --- | --- | --- | --- |
| Sem espera, sem GUI |10, timestamps0–1800ms |1,2603s |7,9346análises/s |11,9103ms |66,95% |182.153.216bytes |
| Ritmo2×, sem GUI |10, timestamps0–1800ms |1,9834s |5,0419análises/s |13,3688ms |44,90% |181.817.344bytes |
| GUI ritmo1×, limite 3 |3, timestamps0–400ms |1,4694s |2,0416análises/s |13,4062ms |60,61% |193.552.384bytes |

Métodos:perf_counter em torno de detect_for_video para inferência; métricas de
parede/CPU iniciam dentro de run_pipeline e terminam após cleanup, antes de gravar
o JSON. Incluem hash/carga do modelo/decode/espera/GUI, excluem imports/CLI
anteriores. process_time mede processo e threads nativas, não CPU total do host.
GetProcessMemoryInfo retorna pico do processo inteiro, não somente modelo.
Vídeo de2s amplifica setup;0pose não mede custo/qualidade de pose humana.

Taxa configurada5amostras/s de mídia, independente do throughput. As duas
execuções completas usaram exatamente índices0,2,…,18 e timestamps0,200,…,1800ms.
Digest da sequência:
`c446f8b0a698242fef03851b5dae1cd173b3deb370e4161fb3aaa059a6be44a1`.
Nenhum FPS em câmera, eficácia, latência de detector ou garantia de tempo real
foi medido/alegado. Artefatos detalhados privados em `.local/etapa04/results`.

## Medições e conferência do arquivo autorizado

Fonte 1920×1080, rotação 0°, pixels quadrados, metadado de 29,97003 fps,
530 frames e duração estimada de **17,684 s**. Processamento proporcional
640×360; Tasks Lite CPU/VIDEO, até duas poses, máscaras desativadas, visibilidade
mínima 0,5, amostragem alvo de 5 análises por segundo da mídia. O tempo PTS foi
utilizado sem fallback. Calibração v1 selecionada pelo fundador e compatível com
a câmera lógica configurada; isso não comprova conexão a uma câmera física.

| Execução completa | Parede no pipeline | Throughput | Inferência média | CPU processo, 1 núcleo=100% | Pico working set |
| --- | --- | --- | --- | --- | --- |
| Sem espera, sem prévia | 6,9568 s | 12,7933 análises/s | 25,0178 ms | 210,00% | 322.920.448 bytes |
| Ritmo 2×, sem prévia | 10,1007 s | 8,8113 análises/s | 23,6797 ms | 157,17% | 321.990.656 bytes |
| Ritmo 0,5×, com prévia | 36,6160 s | 2,4306 análises/s | 25,5870 ms | 47,45% | 336.224.256 bytes |

Os métodos e escopo de medição são os descritos acima. CPU acima de 100% é
possível porque soma threads nativas em múltiplos núcleos. Pacing e GUI aumentam
o tempo de parede; não alteram a velocidade temporal da cena nem o alvo de
amostragem. A taxa medida foi **4,9949 análises por segundo da mídia**.

Cada execução leu **530 frames**, analisou **89** e pulou **441** por amostragem.
Houve **84 ONE_VALID_POSE** e **5 LOW_CONFIDENCE/LOW_LANDMARK_QUALITY**; zero
NO_POSE e zero MULTIPLE_POSES nesse arquivo. Essas classes avaliam qualidade
técnica de observação, não acerto de detecção, identidade ou eficácia de queda.
Os timestamps analisados foram de 0 a 17.618 ms e o digest da sequência foi
idêntico nas três velocidades:
`d53fcfe0809b5bf04af3ac8e87708e3e376c9797971e6939e848e33a996cc53e`.

Relatórios privados em `.local/results/edge/<runId>/report.json`, com runIds na
tabela de comandos. Todos registraram ENDED, exportação de observações desligada,
framesSaved=false e incidentsEmitted=false. Nenhuma pose contínua foi enviada
à API. A conferência visual foi feita pelo fundador na janela local; o agente
leu apenas metadados e agregados. Não houve anotação temporal detalhada de cena.

## Critérios e limites de validação

| Critério | Estado | Evidência/ação restante |
| --- | --- | --- |
| Arquivo autorizado com poses reais de pessoa | VERIFICADO | Modelo real executou o arquivo completo em três replays; hash, autorização local, medidas e limites registrados |
| Tempo da mídia/replays em velocidades diferentes | VERIFICADO | Mesmo digest/frames/timestamps em sintético e arquivo humano, sem espera/2×/0,5× |
| ROI válida e compatibilidade | VERIFICADO | Validação/versão/escala/câmera/orientação testadas; fundador marcou o piso real em 9 pontos e confirmou Enter |
| Prévia opcional e cleanup | VERIFICADO | Janela real, com e sem preview; fundador confirmou pose/piso; fim normal liberou recursos; Q/interrupt exercitados com entrada controlada |
| Modelo/origem/hash/termos | VERIFICADO | Bundle real fixado e executado; termo de pesos no Model Card; inventário atualizado |
| Sem enviar observações/incidentes ou versionar mídia | VERIFICADO NO CÓDIGO/AUTORAL | Sem cliente de ingestão; saídas/modelo privadas; biblioteca tem ressalva de telemetria abaixo |
| Relatório, comandos, testes e versões | VERIFICADO |139 Python, 87 TS, lint/build/frozen e este relatório/roteiro/status |
| Tráfego zero do SDK em ambiente isolado (limite adicional, não critério de extração de poses) | **NÃO VERIFICADO** | Aviso nativo de métricas; não prometer isolamento sem teste próprio |

O [aviso vigente do MediaPipe](https://developers.google.com/edge/mediapipe/solutions/tasks#mediapipe_tasks_privacy_notice)
declara métricas de uso. Fonte pública com logger dummy não prova wheel sem
telemetria: DLL instalada contém strings Clearcut/play.googleapis.com. Não houve
captura de envio real nem auditoria completa; não foi encontrado opt-out na API
Python inspecionada. Inputs ficam no dispositivo conforme aviso; pipeline Radar
não faz upload. Execução estritamente sem tráfego de terceiros permanece por
validar em ambiente isolado. Não houve alteração de firewall/permissões.

Avisos nativos observados: XNNPACK CPU, feedback tensors desativados porque o
modelo não tem assinatura única e, no vídeo humano, NORM_RECT sem IMAGE_DIMENSIONS
em landmark_projection_calculator. Não foram ocultados; as execuções terminaram
e o fundador confirmou visualmente o alinhamento naquele vídeo. Isso não prova
ausência de erro geométrico em outras fontes. Não foi instalado ffmpeg CLI nem
modificado codec do usuário.

Suítes completas API/E2E da 03 não foram repetidas: não houve alteração TS/API/web.
Foram preservados contratos entre linguagens e realizadas consultas HTTP reais.
Não há pretensão de validar browser/câmera/serviço assistencial nesta etapa.

Não há critério obrigatório da etapa 04 pendente. A validação é limitada a um
arquivo, uma pessoa visível e uma seleção de piso. Múltiplas pessoas reais,
outras cenas, eficácia de queda, captura física e isolamento de rede não foram
comprovados. A retenção do vídeo é manual. Não se avançou para a etapa 05.

## Como reproduzir

Siga [VALIDACAO_MANUAL_ETAPA_04.md](../VALIDACAO_MANUAL_ETAPA_04.md):ativar/sync,
model-fetch, configurar arquivo autorizado, doctor, calibrate com seleção local,
run com/sem GUI e comparar velocidades. API/painel não são pré-requisitos da 04.
O vídeo pessoal não deve ser enviado ao chat ou incluído no Git.

Nesta máquina, o caminho autorizado e a calibração já estão preparados. Comandos
na raiz em PowerShell (calibrate só precisa ser repetido para alterar a região):

```powershell
. ./scripts/activate.ps1
uv run --project services/edge --frozen radar-edge doctor --config .local/edge.yaml
uv run --project services/edge --frozen radar-edge calibrate --config .local/edge.yaml --frame-ms 1000
uv run --project services/edge --frozen radar-edge run --config .local/edge.yaml --preview --replay-speed 0.5
uv run --project services/edge --frozen radar-edge run --config .local/edge.yaml --no-preview
uv run --project services/edge --frozen radar-edge run --config .local/edge.yaml --no-preview --replay-speed 2
```

Não é esperado aparecer incidente no painel: esta etapa produz poses e métricas
locais. Modelo e configuração privados devem ser preparados conforme o roteiro
caso se reproduza em outra máquina.

## Próxima etapa elegível

**05 — Motor temporal e eventos de visão**, somente mediante nova solicitação.
A 05 continua NÃO INICIADA. Sem commit, push ou deploy nesta entrega.
