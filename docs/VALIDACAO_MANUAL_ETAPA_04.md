# Validação manual — etapa 04

Objetivo: arquivo → poses reais → prévia e medidas locais. Não cria incidente,
não classifica queda, não abre webcam e não transmite vídeo ao painel.
**Situação da validação real:** concluída em 21/10/2026 no arquivo `bancada-01`.
O fundador selecionou o piso e confirmou o alinhamento da pose e da região na
prévia. Três execuções completas mantiveram as mesmas 89 amostras da mídia.
O caminho real já está configurado em `.local/edge.yaml` nesta máquina; não é
necessário renomear o arquivo ou repetir a calibração para reproduzir o teste.
Resultados automatizados e limites estão no [relatório 04](RELATORIOS/ETAPA_04.md).

## Preparar

Na raiz, PowerShell:

```powershell
. ./scripts/activate.ps1
uv sync --project services/edge --frozen
uv run --project services/edge --frozen radar-edge env
uv run --project services/edge --frozen radar-edge model-fetch
New-Item -ItemType Directory -Force .local/videos | Out-Null
if (-not (Test-Path -LiteralPath .local/edge.yaml)) {
    Copy-Item -LiteralPath services/edge/edge.example.yaml -Destination .local/edge.yaml
}
notepad .local/edge.yaml
```

O bundle é oficial e fixado na versão1, não latest. Esperado:
`pose-landmarker-lite-float16-v1`, 5.777.746 bytes,
SHA-256 `59929e1d1ee95287735ddd833b19cf4ac46d29bc7afddbbf6753c459690d574a`.
Um modelo divergente não é carregado nem sobrescrito automaticamente.

Grave 10–20 s autorizados, câmera parada, piso e pessoa inteira visíveis, boa luz.
Parar ou caminhar basta; não provoque queda. Transfira localmente para
`.local/videos/teste.mp4`. Não cole vídeo ou token no chat. O Radar não precisa do
token da câmera para esta etapa. Não procura vídeos em pastas pessoais.

No YAML, use o UUID da câmera lógica FILE e os campos:

```yaml
source:
  kind: FILE
  path: .local/videos/teste.mp4
  videoId: bancada-01
  authorized: true
  rotation: AUTO
  allowTimestampFallback: true
```

`authorized: true` é a sua declaração para esse arquivo. Não autoriza publicação,
treinamento ou reaproveitamento de mídia de terceiros. Mantenha os demais campos
do exemplo. Para caminho absoluto Windows, prefira barras `/` ou string YAML
entre aspas simples. Modelo, calibração, exportações e relatórios exigem `.local`.
O arquivo de entrada pode ficar em outro caminho local explicitamente informado.

Registre privadamente autorização, retenção, `videoId`, hash, pseudônimo da pessoa,
sessão, ambiente e finalidade CALIBRATION/EVALUATION, conforme
[validação](07_VALIDACAO_E_DEMO.md). O hash calculado aparece no diagnóstico e
no relatório; nenhum nome civil ou caminho do vídeo é necessário no relatório Git.

## Diagnóstico real

```powershell
uv run --project services/edge --frozen radar-edge doctor --config .local/edge.yaml
```

Esperado: `status: ok`, `mode: REPLAY`, `modelLoaded: true` e
`inferenceExecuted: true`; dimensões/FPS/contagem da fonte e hash. `poseCount: 0`
no primeiro frame não comprova ausência de pessoa no vídeo inteiro. Se o piso
ainda não estiver marcado, `calibration: MISSING` é esperado neste diagnóstico.

Erros FILE_MISSING/FILE_INVALID/DECODE_ERROR não são “nenhuma pessoa”. Corrija o
arquivo/codec antes de continuar. Doctor só decodifica o primeiro frame; a leitura
completa é verificada por run.

## Marcar o piso

Escolha um instante em milissegundos com a região do piso visível. Exemplo: 1000
significa um segundo de mídia, não um segundo após abrir a janela.

```powershell
uv run --project services/edge --frozen radar-edge calibrate --config .local/edge.yaml --frame-ms 1000
```

Na janela local:

1. Clique em pelo menos três vértices contornando apenas o piso utilizável.
2. Exclua cama, sofá e partes ocultas; o software não sabe qual superfície é piso.
3. Botão direito desfaz o último ponto; C limpa; Q/Esc cancela preservando a calibração.
4. Enter valida e salva os metadados em `.local/calibration.json`.

Pontos são normalizados, sem cruzar arestas, distintos e com área mínima técnica
de 0,0001 da imagem. Essa área mínima não certifica uma região de piso adequada.
Cada nova calibração incrementa a versão e arquiva a anterior privadamente.
O frame não é salvo. Trocar proporção, orientação ou cameraId exige recalibração.
Vídeo vertical é reduzido somente na exibição para caber na janela do notebook;
os cliques são normalizados nessa imagem completa, sem alterar a geometria usada
pela inferência ou recortar o piso.
Mudança de escala na mesma proporção pode reutilizar os pontos; deslocamento
físico da câmera não é detectado automaticamente.

Sem GUI, escolha pontos normalizados sobre esse mesmo frame em um visualizador
local, salve a lista JSON em `.local/floor-points.json` e confirme explicitamente:

```powershell
uv run --project services/edge --frozen radar-edge calibrate --config .local/edge.yaml --frame-ms 1000 --points .local/floor-points.json --confirm-floor
```

Formato: lista de pares `[x,y]` entre 0 e 1. Não copie os pontos dos testes sintéticos
para um vídeo pessoal. `--confirm-floor` declara que você escolheu a região sobre
aquele frame. Sem confirmação ou geometria válida, nada é gravado.

## Executar com prévia e sem prévia

```powershell
uv run --project services/edge --frozen radar-edge run --config .local/edge.yaml --preview --replay-speed 1
uv run --project services/edge --frozen radar-edge run --config .local/edge.yaml --no-preview
```

A janela mostra imagem processada, ROI, pontos corporais suficientes para desenho,
timestamp, número de poses, estado de qualidade e duração da inferência. A legenda
REPLAY e a ausência de classificação de queda são explícitas. Q/Esc ou fechar a
janela produz STOPPED_REQUEST; Ctrl+C gera INTERRUPTED/exit130. O prazo do vídeo
com contagem confirmada termina em ENDED/exit0. `--max-observations 5` termina
antecipadamente com STOPPED_LIMIT. Falha de arquivo/modelo termina em ERROR/exit1.

O resumo informa o caminho do relatório JSON privado. `maxWidth` inicia em640 e
não amplia fonte menor. Máscaras desativadas; até duas poses; CPU; modo VIDEO.
Pontos faciais e worldLandmarks não são exportados. NO_POSE, LOW_CONFIDENCE e
MULTIPLE_POSES são resultados distintos, sem transformar pontos ausentes em zero.
NO_POSE não comprova que não havia pessoa na cena; uma pose não exclui outra oculta.

## Conferir tempo e medições

```powershell
uv run --project services/edge --frozen radar-edge run --config .local/edge.yaml --no-preview --replay-speed 0
uv run --project services/edge --frozen radar-edge run --config .local/edge.yaml --no-preview --replay-speed 2
```

Compare `mediaSequenceSha256`, frames analisados e primeiro/último timestamp dos
dois relatórios. A mesma mídia/configuração mantém a sequência mesmo quando o
tempo de processamento muda. A velocidade2 tenta ritmo2×, mas não promete que o
computador alcance esse ritmo; nenhuma observação é descartada para compensar.

- `targetAnalysisFps`: alvo na mídia; `analysisSamplesPerMediaSecond`: inverso do
  intervalo médio entre amostras, `(N−1)/(último−primeiro em segundos)`, null com
  menos de duas observações. Não é throughput do computador.
- `analyzedFramesPerWallSecond`: observações divididas pelo tempo de relógio da
  execução, incluindo carga do modelo/hash/decodificação/espera/GUI/cleanup.
  Inicialização do Python/imports anteriores ao pipeline e escrita final do JSON
  ficam fora desse intervalo. Arquivos muito curtos amplificam o custo de setup.
- Inferência min/média/máxima: apenas detect_for_video síncrono, medida por
  perf_counter. Não inclui conversão RGB e desenho.
- CPU: process_time/perf_counter; 100% significa um CPU lógico, incluindo threads
  nativas. Não é uso total do computador. RAM: pico do working set do processo
  inteiro via GetProcessMemoryInfo no Windows, não memória exclusiva da inferência.
- Fallback INDEX_FPS supõe FPS constante e aparece em warnings. Não é precisão
  temporal garantida de vídeo VFR. Para proibi-lo use allowTimestampFallback:false.
- Decoder OpenCV não diferencia sozinho qualquer corrupção de EOF. Leitura
  interrompida antes da contagem declarada dá erro; contagem ausente resulta em
  END_UNVERIFIED. Metadados incorretos podem exigir conversão do vídeo.

Não use o resultado do vídeo sintético sem pessoas como benchmark de pose humana.
Ainda não se mede eficácia/queda e não se garante tempo real.

## Diagnósticos opcionais e privacidade

```powershell
uv run --project services/edge --frozen radar-edge run --config .local/edge.yaml --no-preview --export-observations
```

Por padrão apenas resumo, sem sequência detalhada. O opt-in acima grava JSONL
privado limitado a1000 observações ou10MiB no exemplo. Exceder um limite marca
`truncated: true`; inferência continua, sem aumentar arquivo indefinidamente.
Não compartilhe poses/vídeos pessoais; nenhum frame é gravado por esses comandos.

O [aviso do fornecedor](https://developers.google.com/edge/mediapipe/solutions/tasks#mediapipe_tasks_privacy_notice)
declara processamento dos inputs no dispositivo e coleta de métricas de uso do
SDK. Não foi comprovada ausência de tráfego nativo na versão instalada, nem foi
encontrado opt-out na API Python inspecionada. Ausência de HTTP no pipeline Radar
não comprova ausência de telemetria de terceiros. Validação estritamente sem
tráfego requer execução em ambiente com saída de rede isolada, ainda pendente;
não houve alteração de firewall/rede nesta etapa. Downloads de preparo são explícitos.

## Regressões automatizadas

```powershell
uv run --project services/edge --frozen pytest services/edge/tests -q
$env:RADAR_TEST_GUI = '1'
uv run --project services/edge --frozen pytest services/edge/tests -q
Remove-Item Env:RADAR_TEST_GUI
pnpm.cmd lint:edge
pnpm.cmd check:edge
uv build --project services/edge
```

O teste gráfico requer sessão desktop e abre uma janela sintética breve. Teste
de adaptador ou vídeo sem pessoa não substitui validar landmarks numa pessoa.
Não é necessário iniciar API/banco/web para esses comandos da 04. A validação
real e o status já foram atualizados; a etapa 05 exige uma nova solicitação.
