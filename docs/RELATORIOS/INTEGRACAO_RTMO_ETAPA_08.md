# Integração RTMO e comparação nativa — etapa 08

23/10/2026, America/Sao_Paulo. **Etapa PARCIAL; candidato experimental.**
Continuação da [investigação da cadeira](INVESTIGACAO_CADEIRA_ETAPA_08.md).
Não houve commit/push/deploy, treinamento ou captura de webcam nesta continuação.

## Entrega concreta

RTMO-s integrado à interface de estimador usada pelo pipeline real FILE e LIVE.
ONNX Runtime 1.23.2 fixado no uv.lock do worker; MediaPipe 1.1.1 e o único
opencv-contrib-python 5.0.0.93 preservados. RTMLib não é dependência do produto.
O adaptador implementa preparo BGR/top-left letterbox 640, CPU com quatro threads
intra-op/uma inter-op, limiar de detecção 0,7 e NMS 0,45 para duplicatas.
Pessoas distintas são preservadas; múltiplas poses impedem classificar.
Erro de carregamento, saída inválida ou inferência vira erro explícito, sem
converter falha em NO_POSE. Não há obtenção automática de modelo ao executar.

Variantes Full/Lite e defaults anteriores preservados. A seleção RTMO exige
variant/path explícitos e política `floor-rtmo-score-*` com
`qualitySource=RTMO_KEYPOINT_SCORE`. O score é transportado como confidence,
sem inventar visibility, presence, profundidade, face, dedos ou pontos ausentes.
São doze pontos anatômicos; todos os oito essenciais continuam obrigatórios.
Geometria, persistência, qualidade temporal, rearmamento e idempotência continuam
com os valores da baseline. Não foi introduzida margem de piso para forçar alertas.
Policy/model incompatíveis são recusados, e o limiar usado faz parte do fingerprint.
Serialização de política/fingerprint antigos Full/Lite preservados por teste.

Schema compartilhado v1 recebe variante aditiva restrita ao ID RTMO fixado,
índices corporais correspondentes e família de política. Score misturado com
visibility, modelo desconhecido ou política antiga é rejeitado. Envelopes antigos
continuam válidos no conjunto atualizado. API e banco conservam o JSON explícito;
painel e prévia distinguem score de visibilidade. Não há migração SQL necessária.
API/web/contracts/Python devem ser atualizados juntos; não publicar como formato
compatível com leitores antigos sem atualização. Decisões D46/D47 registradas.

## Fonte, integridade e termos

Registro do modelo: `rtmo-s-body7-640x640-20231211-onnx-v1`,
`.local/models/rtmo_s_body7_640.onnx`. O comando model-fetch real foi executado
e verificou ZIP e ONNX; os hashes completos estão no relatório de investigação
e em model.py. Limite de 20 MiB dos bundles MediaPipe preservado; somente o novo
ZIP/ONNX usa limite de 64 MiB. ZIP é verificado antes de ler o único ONNX, sem
extrair nomes de arquivo arbitrários. Falhas removem arquivos temporários.
Testes cobrem ZIP com nome tentando sair do diretório e hash inválido.

Fontes primárias: [catálogo oficial](https://github.com/open-mmlab/mmpose/blob/main/projects/rtmo/README.md),
[licença do código MMPose](https://github.com/open-mmlab/mmpose/blob/main/LICENSE),
[exceções de algoritmos](https://github.com/open-mmlab/mmpose/blob/main/LICENSES.md)
e [ONNX Runtime](https://github.com/microsoft/onnxruntime/blob/main/LICENSE).
Código MMPose Apache 2.0, ONNX Runtime MIT. A lista de exceções consultada não
lista RTMO; o ZIP não traz LICENSE específica. **Não foi comprovada liberação
comercial por artefato ou por todos os datasets body7.** Candidato delimitado
à bancada experimental, com pesos privados, sem redistribuição/treinamento.
Não registrar essa incerteza como licença comercial aprovada ou proibição constatada.

## Comparação real executada

20 vídeos únicos, duas execuções por vídeo: Full e RTMO, 40 pipelines completos.
Inclui 14 casos de calibração já usados na comparação Heavy, três perdas com piso
v2 confirmado, os dois de sentar e o positivo histórico `piso-f-07` recuperado por
hash. Inferência real, extração de features, motor temporal e SQLite em cada
execução. Nenhum HTTP, JPEG ou escrita no banco original. Câmeras/filas/calibrações
de teste dedicadas; coordenadas do piso preservadas. Conferência dos hashes de
sequência decodificada passou nos 20 pares. São CALIBRATION/diagnóstico, não
avaliação independente ou prova de webcam. Pisos/anotações dos 14 antigos ainda
não têm revisão humana integral.

| Medida | Full | RTMO-s |
| --- | ---: | ---: |
| Inferências | 776 | 776 |
| Eventos | 8 | 12 |
| PERSON_ON_FLOOR | 8 | 8 |
| POSSIBLE_FALL | 0 | 4 |
| Inferência média ponderada (ms) | 28,94 | 121,36 |
| Parede acumulada dos pipelines (s) | 47,34 | 120,04 |
| CPU acumulada dos pipelines (s) | 79,00 | 487,00 |

RTMO mede preparo/inferência/NMS; a medição interna MediaPipe cobre a chamada
de inferência após conversão RGB. Parede do pipeline inclui preparação, decodificação,
persistência e cleanup. CPU inclui threads nativas e pode superar tempo de parede.
Memória dos relatórios é pico de vida de um único processo compartilhado pelas
40 execuções; não comparar como se fossem picos independentes por modelo.
Essas medidas FILE não comprovam 5 Hz estáveis em webcam com API/web simultâneas.

Antes da escolha de quatro threads, um ensaio com 14 inferências medidas após
três de aquecimento por configuração encontrou médias 149,94/105,64/101,36 ms em
2/4/6 threads. Quatro escolhidas por pequeno ganho adicional com seis e aumento
de CPU. Dados em `.local/etapa08/rtmo-thread-benchmark.json`; não são teste LIVE.

| Caso | Eventos Full | Eventos RTMO |
| --- | ---: | ---: |
| sentar-cadeira1 | 0 | 0 |
| sentar-cadeira2 | 0 | 0 |
| novo 03.mp4 / intake08-02, piso v2 | 0 | 0 |
| novo 05.mp4 / intake08-05, piso v2 | 0 | 0 |
| novo 07.mp4 / intake08-08, piso v2 | 0 | 0 |
| positivo histórico piso-f-07 | 1 | 1 |
| intake08-01 | 1 | 1 |
| intake08-03 | 0 | 0 |
| intake08-06 | 1 | 1 |
| intake08-09, fonte ADL | 0 | 1 |
| intake08-11, fonte ADL | 0 | 1 |
| intake08-12 | 0 | 1 |
| intake08-13 | 1 | 1 |
| intake08-14 | 0 | 0 |
| intake08-16 | 1 | 1 |
| intake08-17 | 1 | 1 |
| intake08-18 | 1 | 1 |
| intake08-19 | 0 | 1 |
| intake08-20 | 0 | 0 |
| intake08-21 | 1 | 1 |

Os oito casos com emissão Full continuam com emissão RTMO, com horários/tipos
que podem diferir. Quatro casos adicionais não são automaticamente quatro acertos.
Nos dois ADL, a inspeção de quadros mostra posturas voluntárias no piso em partes
dos vídeos; a categoria ADL não significa ausência de pessoa no chão. Faltam
anotações humanas completas de postura/necessidade de ajuda para avaliar os
alertas. Não estimar precisão, recall, queda real ou necessidade de assistência.
POSSIBLE_FALL significa trajetória observada pela regra, sem autenticar acidente.

**As três perdas persistem.** Houve recuperação de qualidade articular, porém o
quadril estimado ficou fora da ROI nos trechos deitados. Desenhos diagnósticos
com centro do quadril e contorno preservado registram o motivo; não houve nova
marcação automática nem ampliação para parede/móveis. Isso limita a regra
geométrica/projeção, além dos erros de pose do Full. Não declarar solução geral.

No segundo vídeo da cadeira, auditou-se também a equivalência com a pesquisa
assistida pelo fundador: 32 timestamps, uma pose em cada, erro máximo de
coordenadas 0,0000153 pixel entre adaptador integrado e saída RTMLib de referência.
Essa equivalência preserva a melhora visual confirmada; não é ground truth
anatômico nem prova de estabilidade em qualquer móvel/pessoa.

## Arquivos alterados

- Worker: rtmo.py, estimator.py, model.py, config.py, observations.py, features.py,
  policy.py, metrics.py, preview.py, pipeline.py, live.py, event_runtime.py e cli.py.
- Ambiente: services/edge/pyproject.toml, uv.lock e rtmo.example.yaml.
- Contrato/painel: schema event-v1, tipos gerados, fixtures compartilhadas e pose.tsx.
- Testes: test_rtmo.py, adaptação do ponto de injeção do estimador nos testes
  existentes, teste de limite por artefato e testes API/E2E da nova variante.
- Documentos: contrato, motor, ambiente, fontes, decisões, STATUS e relatórios.

## Comandos executados e artefatos

```powershell
. ./scripts/activate.ps1
uv sync --project services/edge
uv run --project services/edge --frozen radar-edge env
uv run --project services/edge --frozen radar-edge model-fetch --variant rtmo-s
pnpm.cmd --filter @radar/contracts types:generate
pnpm.cmd --filter @radar/contracts test
uv run --project services/edge --frozen ruff check services/edge
uv run --project services/edge --frozen ruff format --check services/edge
uv run --project services/edge --frozen pytest -q services/edge/tests/test_rtmo.py services/edge/tests/test_metrics.py services/edge/tests/test_preview.py
pnpm.cmd typecheck
uv run --project services/edge --frozen python .local/etapa08/rtmo-thread-benchmark.py
uv run --project services/edge --frozen python .local/etapa08/run-integrated-rtmo.py
uv run --project services/edge --frozen python .local/etapa08/audit-integrated-rtmo.py
uv run --project services/edge --frozen python .local/etapa08/inspect-integrated-rtmo.py
```

Os comandos corrigidos acima passaram. Primeiro teste do schema falhou em
strictTypes do AJV; tipos explícitos adicionados sem afrouxar validação. Primeiro
pytest geral encontrou teste antigo de limite global; limite MediaPipe de 20 MiB
foi preservado, e o teste de download passou a injetar limite do artefato. Após
correções, testes dirigidos do adaptador/metrics/prévia: 29 passaram. A primeira
execução geral anterior às correções teve 264 aprovados, uma falha e um skip de GUI;
não foi registrada como aprovação final.

Verificação geral final: `pnpm.cmd demo:verify`, exit 0, 14 jobs aprovados.
283 testes Python, 155 API, 100 contratos TS, 20 E2E desktop/mobile e quatro
testes do simulador. Os 100 contratos Python estão incluídos nos 283. Inclui
lint, tipos, build, locks frozen, importações reais, backup/restore isolado e
instalação limpa. Fingerprint
`17d8cfcf12dce20fa271de96819f70a46af903390a875348646fa3aa10ae04e0`,
171 arquivos. `pnpm.cmd demo:check --engineering` retornou 0, releaseReady=false
por gates manuais. A primeira tentativa geral falhou na preparação do Docker
da API porque o Desktop estava fechado; nenhuma suíte API tinha executado nessa
tentativa. Docker Desktop iniciado com WindowStyle Hidden, daemon 29.1.3 voltou
a responder e a verificação geral completa passou. Tentativas anteriores/logs
arquivados em .local; banco original não foi usado como banco de teste.

Checagem final deve ser invocada pelo comando pnpm documentado: a tentativa
direta `node scripts/validation/check.mjs` retornou 1 porque faltou contexto
npm_execpath para conferir pnpm, embora o fingerprint tenha sido aprovado.
Repetida por `pnpm.cmd demo:check`: pré-requisitos/engenharia aprovados,
LASTEXITCODE capturado explicitamente como 2 por gates manuais, com ELIFECYCLE
indicando esse código esperado.
`pnpm.cmd demo:check --engineering` novamente retornou 0. Não é liberação final.

Auditoria adicional abriu as 40 filas nativas em modo somente leitura e exportou
os 20 envelopes reais (oito Full/doze RTMO) para artefato privado. Todos passaram
em Python e TS/AJV, sem enviar à API. Comandos executados, exit 0:

```powershell
uv run --project services/edge --frozen python .local/etapa08/export-native-events.py
node .local/etapa08/validate-native-events.mjs
pnpm.cmd demo:verify
pnpm.cmd demo:check --engineering
```

Hipótese geométrica adicional, somente em pesquisa privada: usar seis dos oito
pontos essenciais dentro da ROI, preservando qualidade/ângulo/bbox/tempo, foi
reaplicado às observações nativas salvas com o motor puro. Recuperou o 03 aos
5616 ms, mas não o 05/07; dois vídeos de sentar continuaram sem emissão.
Não é solução comprovada e não foi integrada nem usada para alterar os resultados
nativos. Sem inferência nova, outbox ou HTTP. Comando real exit 0:
`uv run --project services/edge --frozen python .local/etapa08/research-floor-overlap.py`.
Resultado research-floor-overlap.json junto da comparação. Não reduzir limiar
até disparar nem contar esse diagnóstico como avaliação independente.

Comparação final retornou exit 0, com redirecionamento e código nativo capturado.
Artefatos privados:
`.local/etapa08/integrated-rtmo-1be8862c-1548-42fc-9222-28cc1bc5d476/`;
summary.json, audit.json, configs, relatórios, observações e filas próprias.
Logs integrated-rtmo-final.log/integrated-rtmo-final-errors.log. Avisos nativos
MediaPipe de feedback tensors permanecem no stderr; os 40 relatórios têm code 0.
Primeira comparação de seis clipes preservada em integrated-rtmo-a84804e2-*;
usava duas threads e não substitui as medidas finais. Nenhum peso/vídeo/segredo no Git.

## O que continua faltando

Preparação do próximo ensaio: executado
`uv run --project services/edge --frozen python .local/etapa08/prepare-rtmo-webcam.py`,
exit 0. Criou `.local/etapa08/webcam-rtmo.yaml` sem alterar original, abrir câmera
ou ler/exibir token. Reutiliza referência privada de credencial, índice 0 e câmera
lógica originais; cópia de calibração, outbox/resultados dedicados, 90 s, sem JPEG.
Configuração preparada não significa teste físico ou API já em execução. Aguardar
resposta sobre posicionamento; não iniciar captura por falta de resposta.

Integração funcional não é aprovação da percepção. Faltam validação independente
anotada, tratamento/registro dos limites de piso/projeção, prova LIVE positiva
com revisão, webcam 30 min, execução offline e apresentação pelo fundador.
O RTMO não foi ativado nas configurações operacionais existentes. O exemplo é
opt-in e seus eventos/delivery/autorização começam desligados. Não iniciar etapa 09.
