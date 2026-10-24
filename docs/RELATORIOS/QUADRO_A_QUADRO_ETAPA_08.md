# Pose quadro a quadro e desempenho — etapa 08

**Atualização posterior:** candidato agora integrado como opção da prévia,
desligada por padrão, após ensaio cadenciado e regressão. Este relatório preserva
a pesquisa anterior. Ver [execução real e integração](EXECUCAO_REAL_E_PREVIA_ETAPA_08.md).

23/10/2026. **Investigação executada; etapa 08 PARCIAL.** Preferência do fundador:
priorizar acompanhamento corporal, alinhamento, continuidade e fluidez, com
medição de falhas e custo antes de adotar mudanças. Registrada em D48.

## Método e resultado

Executado RTMO-s real em todos os 1236 quadros de seis vídeos CALIBRATION já
utilizados, sem fluxo óptico ou preenchimento de pontos. Mesmos pixels, piso,
geometria e limiar articular 0,5. As 210 imagens comuns com a baseline de cerca
de 5 Hz coincidiram por hash, tempo e calibração; coordenadas RTMO-s reproduzidas
com diferença máxima de 0 px. Observações anteriores conservaram seus hashes.
Os ensaios não são avaliação independente nem demonstram precisão anatômica.

| Caso | Quadros | RTMO-s: 12 pontos | RTMO-s: 8 essenciais | RTMO-s: sem pontos | RTMO-t: 12 pontos | RTMO-t: sem pontos |
| --- | --- | --- | --- | --- | --- | --- |
| chair02 | 187 | 187 | 187 | 0 | 178 | 9 |
| chair01 | 277 | 276 | 276 | 1 | 258 | 19 |
| floor03 | 176 | 162 | 172 | 4 | 134 | 24 |
| floor05 | 174 | 157 | 163 | 11 | 150 | 0 |
| floor07 | 153 | 144 | 144 | 9 | 131 | 22 |
| legacy07 | 269 | 265 | 265 | 4 | 177 | 86 |
| Total | 1236 | 1191 | 1207 | 29 | 1028 | 160 |

Na cadeira 2, o fluxo anterior perdia pontos em 74/155 quadros intermediários;
agora há 12 pontos em 187/187 quadros com inferência direta. Localiza uma fonte
de perda na comparação anterior, sem comprovar posição correta das articulações.
Outras cenas ainda têm perdas no próprio modelo. Não se prolongou uma pose
antiga para disfarçar ausência atual.

RTMO-s: 142,90 s de inferência e 158,50 s de processamento completo nos seis
arquivos. Médias por clipe 112,80–117,76 ms; processamento completo 7,66–8,03
quadros/s. Cadeira 2: 24,27 s para processar 187 quadros/6,272 s observados.
O total inclui abertura/verificação do modelo, decode, desenho e encode; exclui
preparação inicial de configuração/observações. **Vídeo pré-processado não é
30 FPS de webcam.**

## CPU e variante menor

Consultadas fontes primárias: [threads no ONNX Runtime](https://onnxruntime.ai/docs/performance/tune-performance/threading.html)
e [catálogo RTMO dos autores](https://raw.githubusercontent.com/open-mmlab/mmpose/main/projects/rtmo/README.md).
Mantidos Ryzen 5 5625U, CPUExecutionProvider, dependências/locks e único cv2.

Ensaio de threads em 13 imagens da cadeira 2, ordem 4/2/1/1/2/4: 78 inferências
medidas e seis de aquecimento excluídas, carregamento separado. Médias com quatro
threads: 110,73/110,79 ms; duas: 175,49/162,83 ms; uma: 286,29/273,93 ms.
Coordenadas/scores iguais nas imagens repetidas. CPU aproximadamente 98–401% de
um núcleo, sem medir o notebook inteiro. Pico cumulativo de working set do processo
222826496 bytes. Serviços existentes preservados; ensaio curto, não LIVE.
Quatro threads continuaram melhores entre as configurações testadas.

RTMO-t foi baixado explicitamente do catálogo oficial, apenas para pesquisa
privada. Entrada real ONNX [batch,3,416,416], dets/keypoints; letterbox 416,
quatro threads, mesmos limiares de detecção/NMS/score e mapeamento corporal.
Não instalado no registro de modelos ou contratos do produto.

- URL: `https://download.openmmlab.com/mmpose/v1/projects/rtmo/onnx_sdk/rtmo-t_8xb32-600e_body7-416x416-f48f75cb_20231219.zip`.
- ZIP: 25248869 bytes; SHA-256 `6c71dea1d9d948917f2c562d58c881e4a11d7c8ce335d2920bcaa73d75e7c898`.
- ONNX: 27342008 bytes; SHA-256 `20aad6e2e42359cac1c5b4a0b2da00e29bfe91a72a782fdcf287d273a04c1b24`.
- Mesmas lacunas sobre licença específica dos pesos já registradas para RTMO-s;
  arquivo privado, sem treinamento ou redistribuição.

RTMO-t teve 1075/1236 quadros com oito pontos essenciais. No floor05 melhorou
essa disponibilidade de 163 para 174, mas perdeu mais poses no conjunto e nas
cadeiras. Inferência média por clipe 31,85–35,59 ms; processamento completo
21,22–23,46 quadros/s. Somados 43,08 s de inferência/56,97 s de processamento.
Mais rápido, sem melhora consistente de percepção: **não adotado**. Diferenças
de coordenadas entre modelos não foram tratadas como erro em relação à verdade.

## Decisões temporais preservadas

Reaplicados QualityGate, extract_features e TemporalEngine puros, sem SQLite,
envelope ou HTTP. RTMO-s nos mesmos 210 quadros reproduziu integralmente a
baseline. Duas cadeiras sem candidato/emissão; três perdas no piso continuaram
sem emissão em todas as variantes.

No legacy07, baseline de 5 Hz: POSSIBLE_FALL aos 4224 ms. RTMO-s em todos os
quadros: PERSON_ON_FLOOR aos 3888 ms, sem descida rápida confirmada no início
candidato mais cedo. RTMO-t: PERSON_ON_FLOOR aos 8992 ms em todos os quadros ou
7408 ms nos quadros da baseline. São reaplicações em memória, **não novos
incidentes**. Não há anotação independente para afirmar qual classe é correta.
Elevar frequência de inferência e alimentar o motor com tudo não é mudança
somente visual. Uma prévia mais rápida exige preservar/validar decisões
separadamente. Frequência operacional, política, pisos e gates preservados.

## Execução, verificações e reprodução

Comandos realmente executados, todos exit 0:

```powershell
. ./scripts/activate.ps1
uv run --offline --project services/edge --frozen python .local/etapa08/framewise-pose-check.py
uv run --offline --project services/edge --frozen python .local/etapa08/benchmark-rtmo-threads.py
uv run --offline --project services/edge --frozen python .local/etapa08/fetch-rtmo-t-research.py
uv run --offline --project services/edge --frozen python .local/etapa08/framewise-pose-check.py --research-model rtmo-t
uv run --offline --project services/edge --frozen python .local/etapa08/framewise-temporal-audit.py
uv run --offline --project services/edge --frozen pytest services/edge/tests/test_rtmo.py services/edge/tests/test_temporal.py services/edge/tests/test_visual_tracking.py services/edge/tests/test_preview_comparison.py -q
pnpm.cmd demo:check --engineering
```

39 testes direcionados passaram em 0,88 s. Engenharia reconhecida para o mesmo
código operacional (fingerprint 7927d913436cd52cc7cbcf330ec01a845f31cf8e79cd58b5a5d931810d2a142f,
177 arquivos); a rodada completa anterior de 302 testes não foi repetida nem
apresentada como nova execução. demo:check ainda lista gates manuais de forma
genérica; LIVE/revisão e offline já comprovados permanecem registrados no STATUS.
Etapa continua parcial por percepção delimitada, 30 min contínuos e apresentação.

Fetch acessou somente a origem pública dos pesos: uv --offline impede resolução
online de dependências, mas não bloqueia esse download explícito do script.
É separado da prova offline da demo; nenhum vídeo foi enviado. Nenhuma câmera,
dependência operacional, treino, banco original, configuração ativa, commit ou
deploy foi alterado.

As 12 comparações MP4 foram reabertas e decodificadas até o fim, com contagens
187/277/176/174/153/269 em ambos os modelos. Agente inspecionou três quadros
(chair02, legacy07, floor07); não equivale a anotação completa de precisão.

Artefatos privados em .local/etapa08:

- `framewise-pose-cd41f974-1210-4dbd-aaa9-d32dca1a0bb1/`: RTMO-s, observações,
  resumos, seis comparações e video-check.json.
- `framewise-rtmo-t-1b684a23-8fe8-4968-8f67-f96f2b055734/`: RTMO-t, mesmos formatos.
- `rtmo-thread-benchmark-6a4655dd-a781-4d1d-9968-1da8feb3e922/summary.json`.
- `rtmo-t-research-efad6c2f-8687-44ac-ab48-80fdf045f466/`: ZIP/ONNX/manifesto.
- `framewise-temporal-14604856-55e0-4b4f-bb21-a99535a04f44/summary.json`.

Comparação da cadeira 2 aberta pelo agente, começando pausada, na janela
`Radar - pose real por quadro - REPLAY`. Esquerda RTMO-s nas análises anteriores;
direita RTMO-s real em cada quadro, verde, sem fluxo óptico. Abertura e ausência
de erros verificadas. O fundador confirmou que permanece visível, acompanha bem
melhor o corpo e tem fluidez; relatou tremor mesmo quando a pessoa está parada.
Confirmação desta cena pré-processada, sem comprovar FPS LIVE ou eficácia.
Logs no diretório RTMO-s; lançamento em framewise-preview-launch.json.

```powershell
. ./scripts/activate.ps1
powershell -NoProfile -File .local/etapa08/preview-framewise.ps1
```

Espaço reproduz/pausa, R repete, Q/Esc fecha. Outros casos pelo argumento -Case.
Fundador já confirmou melhor acompanhamento nessa comparação; permanece o
tremor investigado abaixo. O vídeo é pré-processado, sem medir FPS LIVE. Nenhum candidato ativado
automaticamente e nenhuma correção integral ou eficácia alegada.

## Estabilização visual após a conferência humana

Para investigar o tremor, implementado experimento privado de filtro passa-baixa
adaptativo, inspirado no [1 Euro dos autores](https://gery.casiez.net/1euro/).
Implementação própria vetorial 2D, coordenadas normalizadas pela maior dimensão
e timestamps de mídia: mínimo 1,5 Hz, beta 30, derivada 1 Hz, afastamento máximo
de 8 px da posição atual. A velocidade altera a suavização. Não cria confiança,
articulação ausente ou dado para o detector; pode introduzir atraso e conservar
erro anatômico do modelo. Verde: bruto; ciano: desenho filtrado.

Somente pontos aceitos no quadro atual são desenhados. Ausência, score baixo,
múltiplas poses e ponto fora do quadro removem histórico. Troca de fonte/run/
modelo/calibração/geometria, tempo regressivo ou lacuna acima de 250 ms reiniciam
o filtro. Sem extrapolação ou associação de pessoas.

Posição sintética conhecida: 300 amostras/30 Hz, ruído de 2 px, primeiras 30
excluídas da medida. Desvio-padrão bruto 1,9468 px; filtrado 0,9931 px. Degrau
de 30 px: erro 8 px em 33 ms e 2,6437 px em 67 ms. Não mede precisão corporal
ou atraso total LIVE. Primeira tentativa beta 20: 10 testes passaram e um falhou
(3,2553 px em 67 ms, limite 3 px). Beta elevado para 30 para responder mais
rápido, sem mudar o limite do teste: 11/11 passaram em 0,51 s. Resultado inicial
preservado em synthetic.json, sem declarar sucesso daquela tentativa.

Comparados seis vídeos/1236 quadros já inferidos, sem nova inferência/câmera/HTTP:
mesmos índices de pontos em cada quadro, nenhum ponto rejeitado preenchido,
arquivos brutos com SHA-256 preservados. As 29 ausências continuam ausentes.
Ajuste máximo 8 px mais arredondamento; cadeira 2 máximo 6,3154 px. Tempo médio
0,30–0,45 ms por quadro (médias por clipe), somente filtro. Não elimina o custo de inferência do
RTMO-s ou comprova FPS LIVE. Sem adoção no worker ou mudança de alertas.

Comandos adicionais realmente executados:

```powershell
uv run --offline --project services/edge --frozen pytest .local/etapa08/test_visual_smoothing_research.py -q
uv run --offline --project services/edge --frozen python .local/etapa08/render-visual-smoothing.py
powershell -NoProfile -File .local/etapa08/preview-stabilization.ps1
```

Pytest teve a falha inicial acima, depois exit 0; renderização exit 0. Helper
lançado por PowerShell oculto; janela nativa `Radar - estabilizacao visual - REPLAY`
começa pausada. Logs/vídeos em
`.local/etapa08/visual-smoothing-a13288bc-37b3-45ff-9087-2ca2ecd33b05/`.
Esquerda: bruto por quadro; direita: mesmos pontos filtrados. Espaço reproduz,
R repete, Q/Esc fecha. Conferência humana solicitada e posteriormente respondida
conforme registro abaixo.

As seis comparações estabilizadas foram reabertas e decodificadas integralmente,
somando 1236 quadros, com contagens iguais às originais. `git diff --check`
retornou 0; modelos, mídia e experimentos privados conferidos como ignorados.
Nenhuma nova revisão geral do código operacional foi necessária nesta rodada.

### Retorno do fundador sobre a estabilização

Em 23/10, o fundador confirmou que o esqueleto acompanha bem o corpo nesta
cena, com boa fluidez, sem partes sumindo e com menos tremor. Ainda percebe
pequenas oscilações ao observar com atenção. Não relatou atraso; isso não é
medição de latência. Registro privado em `human-review.json` no diretório da
comparação. A revisão dessa versão da cadeira 2 está feita.

Manter os parâmetros medidos como candidato. Não ajustar repetidamente só para
eliminar visualmente todo tremor nessa mesma cena, sem avaliar atraso e outras
posturas. Essa confirmação é de replay pré-processado; não demonstra precisão
independente, fluidez na webcam ou desempenho em outras cenas. Próximo trabalho
técnico: medir execução na velocidade real, separando custo de inferência,
estabilização e exibição, antes de qualquer adoção operacional. Sem abrir a
webcam automaticamente. Etapa 08 permanece parcial.
