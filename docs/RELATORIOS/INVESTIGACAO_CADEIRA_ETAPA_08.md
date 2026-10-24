# Investigação da pose na cadeira — etapa 08

Atualização de 23/10: [adaptador integrado e comparação nativa](INTEGRACAO_RTMO_ETAPA_08.md)
entregues depois desta pesquisa. RTMO agora é uma opção explícita no worker;
configurações antigas seguem Full/Lite. A qualidade da percepção e os gates finais
continuam parciais. O texto abaixo preserva o resultado da investigação anterior.

22/10/2026, America/Sao_Paulo. **Pesquisa executada; integração e etapa parciais.**
Sem alterações adicionais ao código operacional, dependências ou contratos.
Sem commit, push, treinamento, envio de vídeos ou captura de webcam.

## Problema e resultado

No `sentar-cadeira2.mp4`, GMDCSA24 Subject 1/ADL/13.mp4, o MediaPipe Full
posiciona parte dos pontos da perna junto ao pé traseiro da cadeira ao sentar
de lado. Há uma única pose detectada; não é um segundo esqueleto detectado como
outra pessoa. A confiança técnica do modelo não comprova a posição da articulação.
O teste temporal anterior terminou sem alerta, mas isso não corrige a pose.

Dois experimentos foram executados:

1. Máscara corporal do próprio Full: **insuficiente**. A máscara também inclui
   parte da cadeira. Rejeitar pontos fora dela não remove consistentemente o erro.
2. RTMO-s, outra família pré-treinada: **melhora visual localizada confirmada pelo
   fundador**. Na comparação lado a lado, as pernas deixam de ir para o pé traseiro
   da cadeira. Não equivale a precisão articular medida ou eficácia geral.

O worker atual continua com Full. Não foi inserido score RTMO no lugar de
visibility/presence nem alterado o motor para obter verde. A correção operacional
continua pendente de integração e validação; abrir a comparação não troca o modelo
usado pelos comandos normais do projeto.

## Experimento da máscara

Script privado `.local/etapa08/test-chair-mask.py`; saída
`.local/etapa08/chair-mask-4ba76e88-0d8e-4f22-8081-504ece342ad8/`.
Full CPU/VIDEO, duas poses, 5 Hz, segmentação habilitada somente na pesquisa.
Seis clipes, 210 inferências. Para cada ponto essencial, o teste consulta o máximo
da máscara em região de até 5 × 5 pixels, com limiar 0,5. É diagnóstico, sem
aplicação do filtro no produto ou teste de regressão desse filtro.

No segundo vídeo da cadeira, sete das 32 amostras têm ao menos um ponto de
confiança suficiente sem suporte nesse teste de máscara. Entretanto, a região
errada continua coberta em outras amostras. Inspeção da máscara aos 4000 ms
mostra a extensão sobre a cadeira. A máscara compartilha erros com a pose;
não é uma confirmação independente de localização corporal.

Fonte primária: [opção de segmentação do Pose Landmarker Python](https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker/python).

## Ambiente separado e artefato RTMO

Projeto privado `.local/etapa08/pose-alt/`, com pyproject.toml, uv.lock e .venv.
Python 3.12.15, RTMLib 0.0.16, ONNX Runtime 1.23.2, NumPy 2.5.4,
opencv-contrib-python 5.0.0.93. CPU no Ryzen 5 5625U da bancada.
RTMLib declara tanto opencv-python quanto opencv-contrib-python. O projeto de
pesquisa usa override `opencv-python; sys_platform == 'nonexistent'`, preservando
um único fornecedor cv2, contrib. Importação/inferência reais e auditoria das
distribuições passaram. Esse override é uma decisão explícita do ambiente de
pesquisa; não foi aplicado ao projeto services/edge.

Modelo RTMO-s body7, 640 × 640, backend ONNX Runtime CPU, NMS 0,45 e limiar de
detecção 0,7 do wrapper. Para o desenho, pontos corporais com score ≥ 0,5;
esse score não é declarado como visibilidade física ou presence do MediaPipe.
Não foram treinados pesos. Artefatos permanecem privados.

- [Catálogo oficial RTMO/MMPose](https://github.com/open-mmlab/mmpose/blob/main/projects/rtmo/README.md).
- [Wrapper RTMLib RTMO](https://github.com/Tau-J/rtmlib/blob/main/rtmlib/tools/pose_estimation/rtmo.py).
- [Pacote RTMLib 0.0.16](https://pypi.org/project/rtmlib/0.0.16/) e [ONNX Runtime 1.23.2](https://pypi.org/project/onnxruntime/1.23.2/).
- [ZIP oficial](https://download.openmmlab.com/mmpose/v1/projects/rtmo/onnx_sdk/rtmo-s_8xb32-600e_body7-640x640-dac2bf74_20231211.zip): 36.442.532 bytes,
  SHA-256 `3da7ad88b209f9da8be87ba5c325610639af04de3b5c8a96649b98cd9e2848a2`.
- `end2end.onnx`: 39.617.685 bytes,
  SHA-256 `d0703d40d19f3921da51ae725402d5fdae4d2478c7442072d3101bd396f370d8`.

Os hashes são calculados localmente, não uma verificação contra full digest
publicado. O preparo limita tamanho, seleciona somente o único ONNX do ZIP e
escreve em caminho privado fixo, sem extrair caminhos arbitrários. O runner
confere o digest local antes de carregar. Código
[RTMLib](https://github.com/Tau-J/rtmlib/blob/main/LICENSE) e
[MMPose](https://github.com/open-mmlab/mmpose/blob/main/LICENSE) declara Apache 2.0.
O ZIP não inclui LICENSE: contém deploy.json, detail.json, pipeline.json e ONNX.
Licença específica dos pesos e adequação de uso precisam de revisão antes de
incorporar ou redistribuir; licença de código não foi apresentada como licença
automática do artefato ou de seus datasets de treinamento.

## Método e medidas reais

O exportador usou o FileSource e o MediaSampler reais do Radar para produzir
quadros PNG a 5 Hz, largura máxima 640 e relógio de mídia. Mesmos seis clipes
da pesquisa de máscara: os dois de sentar, os três perdidos já revisados e o
positivo histórico `piso-f-07`. São materiais CALIBRATION/diagnóstico, sem
independência para selecionar modelo e depois alegar avaliação final.

210 inferências em seis clipes, sem motor temporal, outbox ou HTTP. Resultados
corporais exportados excluem os cinco pontos faciais COCO; conservam somente
índices 5–16. Não há associação de identidade ou reconhecimento facial.
As imagens de comparação permanecem privadas.

| Caso | Amostras | Amostras com uma pose desenhável | Inferência média (ms) |
| --- | ---: | ---: | ---: |
| sentar-cadeira1 | 47 | 47 | 125,04 |
| sentar-cadeira2 | 32 | 32 | 124,13 |
| novo 03.mp4 revisado | 30 | 30 | 137,24 |
| novo 05.mp4 revisado | 30 | 28 | 125,82 |
| novo 07.mp4 revisado | 26 | 22 | 122,40 |
| positivo histórico piso-f-07 | 45 | 45 | 125,31 |

“Pose desenhável” aqui significa saída do wrapper com ao menos um ponto corporal
com score > 0,5; não significa corpo completo, qualidade aprovada ou pessoa no
chão. Algumas amostras do 05/07 não têm pose desenhável. Não foram contadas
detecções temporais, perdas ou falsos alertas do RTMO.

Média global 126,49 ms; P95 152,15 ms; máximo 225,87 ms; duas amostras acima de
200 ms. Parede dos seis loops 28,61 s; CPU acumulada 167,75 s, incluindo trabalho
concorrente nas threads do runtime. Loops também decodificam PNG e gravam desenhos;
não representam taxa de captura LIVE. RAM, autonomia, aquecimento e webcam
contínua não foram medidos neste experimento. A média não garante cumprir toda
janela de 200 ms sob carga com API/web e captura simultâneas.

No segundo vídeo da cadeira, comparação com o log Full original mostrou pixels
SHA-256 e timestamps idênticos em 32/32 amostras; Full médio 27,63 ms nesse log,
RTMO 124,13 ms no novo ensaio. São execuções separadas, não benchmark simultâneo.
Aos 4000 ms, o desenho Full aponta a perna junto ao pé traseiro da cadeira;
RTMO mantém as pernas na região corporal. Ambos os painéis usam o mesmo piso
confirmado. Prévia abre pausada e permite tocar/pausar/repetir. O fundador
assistiu e confirmou explicitamente a melhora à direita. Não confirmou os outros
cinco clipes nessa prévia nem forneceu marcações de articulações como ground truth.
Articulações encobertas continuam estimativas; scores altos não as tornam visíveis.

## Comandos executados e reprodução nesta bancada

Scripts e dados deste diagnóstico são privados; os comandos abaixo dependem
deles, não são oferecidos como comandos do worker em checkout novo.

```powershell
. ./scripts/activate.ps1
uv sync --project .local/etapa08/pose-alt --python 3.12
uv run --project .local/etapa08/pose-alt --frozen python .local/etapa08/pose-alt/prepare.py
uv run --project services/edge --frozen python .local/etapa08/export-pose-cases.py
uv run --project services/edge --frozen python .local/etapa08/export-pose-frames.py
uv run --project .local/etapa08/pose-alt --frozen python .local/etapa08/pose-alt/compare.py
uv run --project .local/etapa08/pose-alt --frozen python .local/etapa08/pose-alt/audit.py
pnpm.cmd demo:check --engineering
git diff --check
```

Todos retornaram 0. A preparação obtém somente o modelo oficial; não envia vídeos.
Auditoria verificou seis hashes de vídeo, arquivos, 32 comparações exatas de pixels,
timestamps, ausência de pontos faciais nos resultados exportados e único cv2.
Execução da máscara via uv no ambiente edge também retornou 0, antes da comparação
RTMO. Os resultados da máscara são descritos acima, sem aprovação do filtro.

Verificações posteriores: py_compile dos quatro scripts RTMO retornou 0;
git check-ignore confirmou projeto/lock/peso/revisão privados; git diff --check
retornou 0, com avisos já existentes de CRLF/LF. `pnpm.cmd demo:check` sem a opção
engineering manteve releaseReady=false e os cinco gates manuais pendentes;
o filho check.mjs indicou código 2, reportado pelo pnpm como ELIFECYCLE, e o
comando PowerShell envolvente terminou 1. Isso não foi registrado como aprovação.
A suíte completa não foi repetida: nenhuma alteração adicional de engenharia
foi feita, e demo:check --engineering validou o fingerprint já verificado.

A prévia foi lançada com Start-Process/uv, WindowStyle Hidden e logs privados;
janela real conferida pelo título antes de solicitar revisão. Comando equivalente
para abrir novamente (Espaço toca/pausa; R repete; Q/Esc fecha):

```powershell
. ./scripts/activate.ps1
uv run --project .local/etapa08/pose-alt --frozen python .local/etapa08/pose-alt/preview-chair.py
```

Artefatos: model-record.json, cases-frames.json, rtmo-s-results/*.json e
audit-human-review.json, sob `.local/etapa08/pose-alt/`. Máscara com ponteiro em
`.local/etapa08/chair-mask-latest.json`. Projeto Python/lock/modelos/resultados
privados ignorados pelo Git. Nenhum segredo foi incluído neste relatório.

## O que falta para uma correção no produto

1. Especificar a qualidade por backend: os gates atuais requerem visibility e
   presence, e o evento v1 documenta pontos MediaPipe com visibility. Não copiar
   score RTMO para esses campos, preencher invisíveis ou anunciar que os gates
   atuais aprovaram esse modelo. Definir adaptação/versionamento de contrato e
   política com ausência/oclusão explícitas antes de integrar.
2. Verificar termos do artefato e compatibilidade do runtime no worker, mantendo
   modelo fixado por SHA, único cv2, obtenção explícita, suporte offline e erros
   de inferência visíveis. Esta pesquisa não instala RTMO no worker.
3. Implementar o adaptador e repetir negativos, positivos e regressão temporal,
   ambiguidade de pessoas, perda de pose, limites e CPU/RAM. Comparar todos os
   casos conhecidos; não concluir pelas imagens de contato ou por este
   único confundidor visualmente melhor.
4. Congelar a versão escolhida e medir cenas novas independentes; executar as
   provas LIVE/30 min, offline e apresentação ainda pendentes da etapa 08.

A melhora visual foi comprovada somente no recorte descrito. O item da cadeira
no worker operacional e a liberação da etapa 08 permanecem **pendentes**.
