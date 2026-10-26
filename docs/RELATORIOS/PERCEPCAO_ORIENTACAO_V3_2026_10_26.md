# Perdas de percepção — referência V3 e recuperação de orientação

**Complemento posterior:** o fundador executou a sessão física em 26/10.
[Auditoria do ensaio](ENSAIO_WEBCAM_ORIENTACAO_2026_10_26.md): quatro entregas,
limitações de cobertura/cadência, três janelas positivas sem alerta, tempos
posturais inconclusivos e revisão humana pendente. Aceite não aprovado. O texto
abaixo preserva os resultados e o estado anteriores a esse ensaio.

26/10/2026. Continuação da investigação iniciada em 25/10.
**PARCIAL: ganho reproduzido em arquivo; novo ensaio físico não executado.**
Não aprova o MVP completo, uso assistencial ou reconhecimento geral de quedas.

## Objetivo e referência preservada

Demonstrar pessoa permanecendo deitada no chão, incidente e revisão humana,
com câmera fixa e uma pessoa no cômodo configurado. PERSON_ON_FLOOR é o alvo
postural. POSSIBLE_FALL exige transição observada; yoga não comprova queda,
desmaio, acidente ou necessidade de socorro. Percepção insuficiente é abstenção.

Árvore inicialmente limpa em `eaa845a060db680d679b4563a42a984e3fcc05d2`.
Referência de 197 arquivos de fonte:
`27aa36e4c2d0b13c9a0fc3b00d900db67ab25da6bd3ece59393620bfe2bdf467`.
ZIP de Git, configurações efetivas, políticas expandidas, calibrações, hashes,
traces e resultados preservados antes de alterar o detector. A referência na
regressão foi executada importando esse código extraído, e não o adaptador novo
com apenas um nome antigo. Ponteiro privado:
`.local/detector-evolution/perception-current.json`, diretório
`perception-dce2d01b-278b-4029-a405-974ffb0d00e9`.

Identidades mantidas:

| Item | Identidade |
| --- | --- |
| Estimador | RTMO-s ONNX, CPU, quatro threads intra / uma inter |
| Pesos RTMO | `d0703d40d19f3921da51ae725402d5fdae4d2478c7442072d3101bd396f370d8` |
| Classificador | MULTICLASS_BODY_V3, signed-body-mlp-v3-dev01 |
| Artefato | `40d01401851f24cd8c815557970f0dcf42877707afbba38d521ebfa87bd5bd19` |
| Política de referência | floor-rtmo-score-posture-multiclass-v3-dynamics01-adaptive2 |
| Recuperação de referência | RTMO_ADAPTIVE_V2 |
| Política candidata | floor-rtmo-score-posture-multiclass-v3-dynamics01-adaptive3 |
| Recuperação candidata | RTMO_ADAPTIVE_V3, opt-in; padrão continua NONE |
| Aceitação de pessoa / articulação | detecção >0,7 / score nativo ≥0,5 |
| Classificação | score ≥0,65 e margem ≥0,15; desconhecido continua possível |
| Persistência / cobertura / prazo | 2000 ms / ≥80% / 5000 ms desde início anotado |
| Lacuna / rearme / reset negativo | 500 ms / 3000 ms / 600 ms |

O contexto continua sendo região 2D confirmada do quadril e exclusões existentes;
não mede altura ou contato físico. Polígonos não foram redesenhados nesta rodada.
Nenhum treino, download de modelo, alteração de dependência/lockfile ou upload.
Os dois vídeos de yoga passam explicitamente a **desenvolvimento/regressão**,
pois orientaram a correção; não são reserva final. Procedência e restrições de
licença continuam no [relatório anterior](TESTE_DOIS_VIDEOS_YOGA_V3_2026_10_25.md).

Fonte entregue: **200 arquivos**, SHA
`4fab1f96dc5d29d71d9210e4c956143bcdbeda36a7ed583609d89e8b4b36f7f5`.
ZIP privado `candidate-final-source.zip`, SHA
`020fe75187a228175769b59d1928588e53703d9aff534f4857f0e517c4b12722`;
manifesto `final-source-freeze.json`. HEAD permanece o da referência, com alterações
locais identificadas e sem commit. O ZIP inclui código/testes/manifests, sem mídia,
pesos, credenciais ou diagnósticos privados.

Arquivos executáveis alterados: `services/edge/src/radar_edge/rtmo.py` e `config.py`
(recuperação opt-in); `observations.py`, `pipeline.py`, `decision_trace.py`
(tentativas e cronologia); `live.py`, `webcam.py`, `metrics.py`, `event_runtime.py`
(idades e custo LIVE). Testes novos: `test_rtmo_orientation_recovery.py` e
`test_live_timing.py`. `scripts/validation/physical-session.py` prepara marcadores
humanos separados do detector. STATUS, roteiro de uso, decisões, índice de relatórios
e README foram atualizados; CSVs públicos contêm somente resultados derivados.

Hashes dos vídeos, recalculados antes e após os testes:

- Casa: `f6f18ba27740284bf8fbf6c59eab52c8417ee0f1091b30e81fce76800963487c`.
- Sala: `d6317f319558a04f40f1af7a53df9bd42037a63736a950388ae23fa44bdd4935`.

## Reprodução e causa investigada

V3 reproduzido antes da mudança: casa, 125 análises, PERSON_ON_FLOOR em
2002 ms e cobertura 100%; sala, 80 análises, evento em 4000 ms, cobertura
12600/15800 ms = 79,746835443%. Um evento por arquivo, sem POSSIBLE_FALL.
Configurações e artefatos coincidem com os do relato anterior. A reprodução
com diagnósticos por tentativa não alterou esses resultados.

Na sala, todas as **69 poses aceitas** têm oito essenciais suficientes, classe
LYING e contexto aceito. Não há descarte adicional de classe ou piso nesses
69 casos. Original resolve 47; o recorte da proposta recupera outros 22.
Nas 11 restantes, todas as tentativas ficam abaixo de 0,7 no gate de pessoa.
A perda acontece **antes da aceitação da pose e da classificação corporal**.

O RTMO é um estimador conjunto de pessoa/pose: proposta abaixo do limiar não é
localização aceita por um detector independente. Portanto, a descrição exata é
“proposta rejeitada; nenhuma pose aceita”, e não prova de ambiente vazio, nem
prova isolada de que a rede não calculou articulações. O trace também distingue
pessoa aceita com pose insuficiente, postura incerta, rejeição de contexto e
observação elegível. As categorias intermediárias não ocorreram nesses 11 casos.

As 80 análises estão na [linha do tempo V3](DADOS/PERCEPCAO_SALA_V3.csv):
timestamp, scores de cada tentativa, pose/essenciais, classe, contexto, estado,
temporizadores, emissão, custo e motivo de descarte. O JSON privado
`reference/yoga2-02/timeline.json` contém também os oito pontos e suas qualidades,
dimensões/propostas de cada tentativa e estados completos antes/depois. Não há
frame ou vídeo bruto no CSV público.

| Ausências, ms | Amostras | Intervalo conservador entre observações válidas |
| --- | ---: | --- |
| 1400, 1600, 1800 | 3 | 1200–2000, 800 ms |
| 2200 | 1 | 2000–2400, 400 ms |
| 7400, 7600, 7800 | 3 | 7200–8000, 800 ms |
| 8800, 9000, 9200 | 3 | 8600–9400, 800 ms |
| 9800 | 1 | 9600–10000, 400 ms |

São cinco grupos, não uma interrupção única. A maior sequência tem três análises
ausentes: 400 ms entre o primeiro e o último timestamp ausente, três células de
200 ms, e **800 ms entre as poses válidas que a delimitam**. Não confundir essas
três formas de expressar a lacuna. A tabela não afirma conhecer o estado de cada
frame intermediário não analisado.

A primeira suspeita começa em 0 ms. Em 1800 ms, passaram 600 ms desde a última
candidata em 1200 ms, excedendo 500 ms: o motor limpa a suspeita. Reinicia em
2000 ms; a ausência em 2200 ms reduz a cobertura da janela. Em 4000 ms, os
1600 ms positivos da janela de 2000 ms atingem exatamente 80%, permitindo a
emissão. A perda inicial explica os 2 s adicionais de latência. Não foi preciso
alterar temporizadores para corrigir esse arquivo.

## Duas hipóteses e comparação controlada

**H1 — recorte muito estreito no eixo curto.** Propostas do recorte extrapolavam
sua própria altura. Testada margem de 25% do lado maior nos dois eixos, nos
mesmos frames, sem alterar scores/piso. Recuperou apenas **1/11** ausências.
Não é evidência suficiente para atribuir todas as perdas ao truncamento;
essa mudança não foi incorporada.

**H2 — sensibilidade à orientação não coberta pela inversão de 180°.** Nos mesmos
80 frames completos, com mesmos pesos e limiares: rotação de 90° produziu zero
poses com oito essenciais; 270° produziu **80/80**, incluindo as 11 ausências.
Nessas 11, score de pessoa entre **0,8193909 e 0,9455924**, com oito essenciais
reais ≥0,5. As tentativas antigas chegavam no máximo a aproximadamente
0,493–0,698 nesses instantes. Isto sustenta uma causa reproduzível de sensibilidade
à orientação **neste material**. Não isola iluminação, distância ou roupa como
causas, nem explica automaticamente as perdas da webcam do fundador.

Não houve busca indiscriminada de parâmetros ou treino nesses arquivos.
Todos os frames aceitos anteriormente também entraram na análise.

## Correção e limite de custo

O candidato mantém original e recorte existentes. Se continuam sem pose, uma
proposta **do frame atual**, horizontal, com os oito essenciais nativos suficientes,
permite tentar 270° e depois 90°. A proposta ≥0,3 serve apenas para decidir trabalho;
nenhuma pessoa é aceita por esse score. Cada nova pose exige detecção >0,7 e os
oito essenciais. Múltiplas pessoas são preservadas como ambiguidade. Se as novas
tentativas falham, seguem inversão/recorte central existentes.

Coordenadas de pontos e caixas são restauradas para a imagem original, incluindo
correção de pixel em imagens não quadradas. Índices anatômicos e scores não são
trocados. Não há interpolação, preenchimento de pontos, reaproveitamento de pose
anterior ou mudança do timestamp. O desenho estabilizado continua apenas visual.
O motor, seus limites de interrupção, histerese e deduplicação não foram alterados.

A primeira implementação acionava rotações apenas pela proposta horizontal.
Preservada em `iteration1/`: no controle vazio intake16-15, aumentou de quatro
para seis inferências por análise, com médias medidas 547,932 → 790,398 ms.
Esse custo adverso não foi removido do histórico.

Inspeção das saídas nativas atuais: a proposta falsa desse vazio tem somente
sete essenciais ≥0,5 em 39/39 análises; a sala tem oito em 80/80. Acrescentado
o gate conservador dos **oito essenciais**, reutilizando o critério existente,
sem criar novo limiar ajustado ao vídeo. Isso limita o custo; não aceita a proposta
como pessoa e não a classifica. Quando não satisfeita, preserva a recuperação V3
anterior, inclusive sua incerteza. A regressão inteira foi repetida após o ajuste.
Teto de tentativas continua explícito: até seis, sem loop ou paralelismo novo.

## Resultados em arquivo

Referência e candidato final: **34 execuções completas cada**, mais dois controles
históricos de cadeira em cada versão: **36 por versão, 72 execuções comparativas**.
Além disso houve a reprodução inicial, experimentos controlados de recuperação,
primeira implementação e medições de custo, separados nos registros privados.
Todos os alvos/controles permaneceram nos denominadores.

| Grupo | V3 de referência | Candidato final |
| --- | --- | --- |
| Casa, já no chão | 2002 ms; 100% | 2002 ms; 100% |
| Sala, já no chão | 4000 ms; 79,7468%, parcial | 2000 ms; 100% |
| Seis alvos dos 16 | 6/6 em 2000 ms | 6/6 em 2000 ms |
| Dez negativos dos 16 | zero alertas; dez PASS | igual |
| Quatro CAUCA | quatro alertas; só um POSSIBLE_FALL | igual em tipos de evento |
| CAUCA-04 | 4000 ms desde alvo; cobertura 80,7692% | 2600 ms; 92,3077% |
| Oito ADL CAUCA | zero alertas; sete PASS, um inconclusivo | igual |
| Três perdas históricas | floor03/05/07 sem alerta | continuam sem alerta |
| Deitar voluntariamente, controle antigo | sem alerta | continua perdido |
| Duas cadeiras antigas | zero alertas; uma PASS e uma inconclusiva | igual |
| Duplicações / alertas nos negativos | zero / zero | zero / zero |

Os 20 controles negativos somam 18 PASS e dois inconclusivos: cauca-10 com
65,2778% e chair08-01 com 65,1042% de cobertura. Silêncio não aprova esses dois.
Chair08-02 teve 100%; o relato anterior de esqueleto melhor não substitui esses
resultados decisórios. Nenhuma regressão de aceite nos casos que passavam.

As quatro perdas positivas antigas continuam abertas, principalmente por contexto
e observação; não foram corrigidas expandindo polígonos. O reconhecimento de
transição permanece em 1/4 dos CAUCA encenados. Não calcular recall geral juntando
onsets provisórios, diferentes contextos, pessoas e dados usados no desenvolvimento.

[Comparação individual](DADOS/COMPARACAO_PERCEPCAO.csv) e traces privados incluem
cobertura, latência, classes, motivos e cada fonte por SHA. Os relatórios anteriores
continuam intactos, incluindo o resultado original 2/6 dos 16 e o teste físico V3
insatisfatório de um alerta para três tentativas.

## Fórmulas, denominadores e relógios

- Disponibilidade de pose: análises com pose aceita / todas as análises. Sala V3:
  69/80 = **86,25%**; candidato: 80/80. Não comprova qualidade automaticamente.
- Observações elegíveis: classificação/contexto/qualidade aceitos / todas as
  análises. Na sala, também 69/80 no V3 e 80/80 no candidato; em outros arquivos
  pode haver pose e classificação incerta ou rejeição de contexto.
- Tempo observado: último timestamp menos primeiro. Sala: 15800 ms, 79
  intervalos de 200 ms. Conteúdo: 16000 ms, com cauda não amostrada de 200 ms.
  Casa: 25025,025 ms de conteúdo, 24825 ms observados; cauda 200,025 ms.
- Cobertura temporal: soma de intervalos com **ambos os extremos elegíveis** e
  delta ≤500 ms, dividida por todo o tempo observado. V3: 63/79 intervalos,
  **12600/15800 = 79,746835443%**. As 11 ausências invalidam 16 intervalos,
  totalizando 3200 ms inconclusivos. Não há outro descarte oculto nesse caso.
- Candidato na sala: 79/79 intervalos, 15800/15800 = 100%. Cauda continua
  separada; não inventar observação dos últimos 200 ms. Nenhuma correção da
  fórmula foi necessária e ambos foram medidos pelo mesmo método.
- Latência: timestamp da emissão menos início humano/anotado, **0 ms** nos dois
  vídeos já deitados; o instante real anterior ao arquivo é desconhecido. Não
  substituir por primeira pose elegível. Latência de mídia é diferente de parede.
- Negativo com pessoa: exige cobertura decisória ≥80%. Vazio confirmado por
  humano: usa disponibilidade temporal de captura, sem inferir vazio de NO_POSE.
- Parede/CPU: perf_counter/process_time; inferência inclui tentativas e conversões;
  classificação, decodificação e prévia têm medidas separadas. FILE usa tempo da
  mídia; LIVE usa aquisição monotônica, com origem e offset registrados.

## Webcam: instrumentação e o que ainda não foi medido

### Custo medido e variabilidade

Os lotes de correção/regressão tiveram execuções simultâneas e outras verificações
em andamento. Não se usa a diferença de suas somas de parede como ganho de
velocidade. Foi feita medição adicional sequencial referência/candidato; após o
reinício do PC, a primeira repetição coincidiu com a subida do Docker. Essa
repetição está preservada em `*-final-cost-comparison.json`, com a interferência
identificada. Sala e vazio foram repetidos com os serviços já iniciados, sem outro
runner de inferência concorrente: `*-final-steady-cost-comparison.json`.

| Arquivo / versão | Análises | Inferência média / máxima | Parede | CPU-s | Pico de processo |
| --- | ---: | --- | ---: | ---: | ---: |
| Sala / V3 | 80 | 309,139 / 792,556 ms | 26,309 s | 98,750 | 242,20 MiB |
| Sala / candidato | 80 | 299,164 / 624,704 ms | 25,357 s | 95,063 | 239,09 MiB |
| Vazio intake16-15 / V3 | 39 | 764,174 / 809,720 ms | 31,240 s | 119,469 | 263,21 MiB |
| Vazio intake16-15 / candidato | 39 | 740,049 / 785,967 ms | 30,412 s | 120,766 | 266,93 MiB |

Na sala: 16 s de conteúdo e 15,8 s observados; no vazio: 7,760 s de conteúdo
e 7,6 s observados. Tempos de leitura/decodificação da sala: 167,04 /
165,97 ms totais; vazio: 778,56 / 760,77 ms. Prévia desabilitada nessa medição;
classificação e persistência não são confundidas com inferência. Pico de memória
é de vida do processo, não amostragem exclusiva da cena.

Casa usa somente inferência original em ambas as versões: 125 chamadas, cobertura
100%, latência 2002 ms. Na repetição de quatro casos, médias 172,957 / 158,594 ms,
paredes 25,371 / 23,010 s, CPU 99,188 / 92,969 s, sem diferença de algoritmo nesse
percurso. Isso evidencia variação da máquina, não ganho causal pelo candidato.
O alvo intake16-03, de orientação oposta, manteve latência 2000 ms e médias
510,576 / 509,046 ms naquela repetição; paredes 39,732 / 39,859 s.

O dado estrutural verificável é mais restrito: na sala, V3 fez **135 inferências**
nas 80 análises, candidato **124** (47 originais, 22 com um recorte adicional e
11 com recorte + rotação). O gate final restaurou quatro tentativas por análise
no vazio, em vez das seis da primeira implementação. A CPU do vazio não melhorou
de forma demonstrada. Não apresentar diferenças pequenas de uma rodada como
benchmark rigoroso ou porcentagem garantida de aceleração.

**Ainda há frames acima de 500 ms e custo alto no vazio em ambas as versões.**
O candidato não foi aprovado para 5 análises/s ao vivo; a recuperação pode causar
lacunas maiores que a tolerância temporal. Não foram reduzidos resolução,
limiares, requisitos ou alterado o relógio para esconder isso. O próximo ensaio
medirá aquisição recente, idade na decisão, cadência e elegibilidade efetiva.

Captura existente inspecionada e testada: processo nativo e **um único slot do
frame mais recente**, sem fila FIFO. Sobrescrita é descarte deliberado de frames
intermediários, não erro de captura. Testes de slot recente, frame velho,
reconexão, pausa, limite de tentativas e encerramento passaram. Não foi encontrado
defeito comprovado de crescimento do buffer que justificasse reescrever a captura.

Acrescentados diagnósticos mínimos por tentativa: dimensão de entrada, score
máximo, scores aceitos, contagem de pose/essenciais e custo. Sem imagem ou
coordenadas adicionais. LIVE registra idade do frame no início da inferência,
após a inferência e na conclusão da decisão/checkpoint; idade usa monotônico.
Relatório distingue frames adquiridos/consumidos/sobrescritos, capacidade do
buffer, análises aceitas e tentativas descartadas por idade >2000 ms. O agregado
de todas as tentativas conserva o pior custo/idade, inclusive as descartadas.
Os contadores históricos de aquisição/sobrescrita refletem o último snapshot
consumido; não contabilizam como total exato os frames posteriores a esse consumo
durante a última inferência/encerramento. Isso não é contagem de erros de captura.
O buffer interno do driver não foi medido. A idade monotônica do frame efetivamente
analisado é registrada separadamente, sem inferi-la desses contadores.
Não aumentar paralelismo, reduzir resolução ou confundir frames capturados com
análises/segundo. Perda de pose não comprova ambiente vazio.

**Nenhuma webcam foi aberta nesta rodada.** As métricas LIVE novas ainda não
foram medidas no equipamento físico. Arquivo processado rapidamente não aprova
cadência ao vivo; tentativas de recuperação podem superar 500 ms e fragmentar
evidência. O ensaio anterior de três tentativas continua insatisfatório e não
tem vídeo/anotação suficiente para atribuir aquelas perdas a esta causa.

## Integração e roteiro pendente

Fluxo técnico com 12 envelopes nativos reais de FILE: contrato, HTTP, API,
PostgreSQL isolado, incidente, aviso local e reenvio idempotente. Revisão técnica
automatizada é distinguida de revisão humana. Painel teve 20 E2E desktop/móvel,
incluindo pose RTMO, permissões, persistência da revisão, avisos e falhas de rede.
Isso não é conferência física do fundador nem latência medida de exibição LIVE.

Uma sessão nova foi preparada com índice 0/DSHOW, 640×480, limite fixo de
720 s, sem gravação/JPEG. Base, credencial e calibração anteriores preservadas;
há cópia privada idêntica do piso para não sobrescrever a original numa remarcação.
`--check` passou sem abrir fonte/banco. A janela de marcação física só inicia
quando o fundador executar `--start`, após confirmar disponibilidade. Seu uso real
e os marcadores ainda precisam ser exercitados no ensaio.

O [roteiro único](../USO_DETECTOR_EXPERIMENTAL.md#ensaio-controlado-preparado-em-2610--recuperação-de-orientação)
define seis tentativas de 10 s, três orientações, 20 s em pé entre elas,
cadeira/ajoelhar/pegar objeto/caminhar/vazio/retorno, marcação humana independente,
critérios de cobertura/latência e revisão no painel. Operador ou teclado acessível
permite marcar sem mover a câmera; sem tempos confiáveis, não aprovar latência.
Não há provocação de queda, repetição automática ou extensão até obter sucesso.

## Ambiente e verificações

Windows 11 Pro 10.0.26200, Ryzen 5 5625U, 6 núcleos/12 threads, cerca de 15,4 GiB
RAM. Node 24.22.1, pnpm 10.34.7, Python 3.12.15, uv 0.13.4; ORT 1.23.2,
MediaPipe 1.1.1 e único provedor cv2 opencv-contrib-python 5.0.0.93. Nenhuma
dependência instalada. PostgreSQL 17.11 da demonstração continua em 15432;
serviço preexistente na 5432 preservado. Dados, proprietário e cadastros mantidos.

O PC reiniciou entre as sessões: Docker/API/web estavam parados na retomada.
Primeiro runner HTTP final falhou por daemon ausente, antes de criar banco.
Docker Desktop e serviços locais foram reiniciados; isso não é falha de detecção
nem foi tratado como teste aprovado. Logs e resultado da repetição foram mantidos.

| Comando realmente executado | Resultado |
| --- | --- |
| git status/log, inventário, leitura dos documentos/código/configurações | referência limpa identificada, trabalho preservado |
| node .local/detector-evolution/freeze-perception-round.mjs | ZIP/identidade da referência preservados |
| python .local/detector-evolution/reproduce-perception-reference.py | dois FILE reproduzidos; 80 tentativas da sala rastreadas |
| python .local/detector-evolution/audit-perception-timeline.py | denominadores, lacunas e CSV conferidos |
| python .local/detector-evolution/test-crop-hypothesis.py | 1/11 recuperada; H1 não incorporada |
| python .local/detector-evolution/test-quarter-turn-hypothesis.py | 80 frames × duas orientações, H2 sustentada |
| python .local/detector-evolution/compare-perception.py reference | 34 FILE com fonte V3 extraída |
| compare-perception.py candidate e candidate --final | primeira implementação e candidato final, 34 FILE cada, resultados separados |
| compare-chair-controls.py reference e candidate | quatro FILE, dois controles de cadeira por versão |
| audit-recovery-cost-gate.py | escores essenciais atuais: oito na sala; sete no controle vazio |
| run-perception-cost-pair.py | pares sequenciais e repetição após serviços estabilizados; custos e interferência preservados |
| summarize-perception.py | hashes, contratos Python e SQLite nativos auditados; comparação por caso |
| native-http-runner-perception.mjs | banco isolado; 12 eventos, 12 avisos, zero duplicações, revisão técnica |
| pytest services/edge/tests -q, RADAR_TEST_GUI=1 | **378 passaram**, incluindo janela sintética; nenhuma webcam |
| pnpm.cmd test:contracts | **104 TS e 104 Python passaram**; Python também está na suíte acima |
| pnpm.cmd test:api | **159 passaram** em banco descartável |
| pnpm.cmd test:e2e | **20 passaram** desktop/móvel; recursos isolados removidos |
| pnpm.cmd lint, typecheck, build | passaram |
| ruff check e format --check; git diff --check | verificação final registrada com a fonte entregue |
| radar-edge env; physical-session.py --check | imports reais/contexto/credencial sintaticamente válidos; fonte não aberta |
| GET /v1/health/ready, GET /login e GET /v1/edge/me com credencial privada | HTTP 200, credencial ativa e câmera correta; somente leitura |
| Inicialização/fechamento de Tk oculto | runtime gráfico disponível; não abriu webcam nem valida os marcadores físicos |

Prefixo dos comandos Python: `uv run --offline --project services/edge --frozen`.
O helper inicial de reprodução precisou trocar model_dump por asdict para Policy,
antes da inferência; leitura com sintaxe de brace do Bash foi corrigida no
PowerShell. Uma seleção pytest com `-k native` não encontrou testes (exit 5);
o teste de janela foi então executado pelo nome correto e a suíte completa com
GUI passou. Nenhum desses erros foi convertido em alegação de teste realizado.

## Estado final e reprodução

Relatórios anteriores, vídeos/pesos privados e todas as perdas mantidos.
Não houve commit, push, deploy, câmera IP ou mensagem externa.
Pendente desta rodada: **ensaio físico controlado, suas medições/avaliação e
revisão humana persistida no painel**. Depende da disponibilidade do fundador.
Reserva independente, estabilidade prolongada, operação offline do candidato
novo e reconhecimento de quedas continuam sem aprovação por esses arquivos.
Os testes offline/fluxo da etapa 08 permanecem evidências históricas delimitadas.

Para repetir a comparação privada, use o ponteiro e os helpers acima a partir da
raiz. Os runners preservam resultados existentes/checkpoints; uma nova execução
integral requer outro diretório/fila, nunca alterar eventId ou apagar falha antiga.
Materiais privados não acompanham um clone do Git.

O único próximo passo com presença é seguir o roteiro e, quando pronto, executar:

```powershell
. ./scripts/activate.ps1
uv run --offline --project services/edge --frozen python scripts/validation/physical-session.py --config .local/detector-evolution/candidate-orientation/webcam-controlled.yaml --start
```
