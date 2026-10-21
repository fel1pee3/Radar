# Worker local — visão em arquivo

Execute na raiz do repositório, PowerShell:

```powershell
. ./scripts/activate.ps1
uv sync --project services/edge --frozen
uv run --project services/edge --frozen radar-edge env
uv run --project services/edge --frozen radar-edge model-fetch
```

`env` preserva o diagnóstico de imports, sem abrir arquivo, câmera ou modelo.
`model-fetch` é o único comando que baixa o modelo; verifica SHA-256 e não
sobrescreve um arquivo existente divergente. Pesos ficam em `.local/models`.

Copie `edge.example.yaml` para `.local/edge.yaml` sem sobrescrever configuração
existente. Informe caminho local autorizado, UUID da câmera lógica e
`source.authorized: true` somente quando tiver autorização. Caminhos relativos
são resolvidos a partir da raiz, inclusive quando se usa `uv --project`.
Não há bearer, senha humana nem chamada à API nesta etapa.

```powershell
uv run --project services/edge --frozen radar-edge doctor --config .local/edge.yaml
uv run --project services/edge --frozen radar-edge calibrate --config .local/edge.yaml --frame-ms 0
uv run --project services/edge --frozen radar-edge run --config .local/edge.yaml --preview --replay-speed 1
uv run --project services/edge --frozen radar-edge run --config .local/edge.yaml --no-preview
```

O diagnóstico `doctor` abre/decodifica o primeiro frame e executa o modelo real;
`calibration: MISSING` permite preparar a calibração, não autoriza rodar sem ROI.
`run` exige calibração compatível e produz poses REPLAY, sem classificar quedas
ou emitir incidentes/heartbeat. A janela é local, sem streaming web.

Modelo Tasks Lite float16/v1, CPU, VIDEO, duas poses e sem máscara. Mantém
proporção, largura máxima 640, rotação explícita e amostragem por timestamp da
mídia. `replaySpeed: 0` não impõe espera; 1/2 tentam ritmo original/2× sem pular
observações para compensar lentidão. A duração da cena nunca usa o relógio do CPU.

O fallback índice/FPS supõe CFR e aparece no relatório; pode ser desabilitado.
Falha de leitura antes da contagem esperada é erro de decodificação; ausência de
contagem não permite afirmar EOF normal e gera END_UNVERIFIED. Não há recuperação
silenciosa pulando frames corrompidos. Pixels anamórficos exigem normalização prévia.

Resumo privado: `.local/results/edge/<runId>/report.json`. Observações completas
somente com `--export-observations` ou configuração explícita, com limites de
quantidade/bytes. Somente índices corporais 11–32 são retidos; valores ausentes
ficam null. Não salvar frames/snapshot é o padrão. Limite de exportação não
interrompe inferência; o relatório informa truncamento.

```powershell
uv run --project services/edge --frozen pytest services/edge/tests -q
$env:RADAR_TEST_GUI = '1'
uv run --project services/edge --frozen pytest services/edge/tests -q
Remove-Item Env:RADAR_TEST_GUI
pnpm.cmd lint:edge
uv build --project services/edge
```

O teste GUI explícito abre e fecha uma janela com vídeo sintético. Testes com
modelo real exigem `model-fetch`; sem o artefato aparecem como skipped, não como
inferência aprovada. Só `opencv-contrib-python` fornece cv2; não instalar outro
OpenCV/headless junto dele. PyYAML usa safe_load; configuração rejeita campos
desconhecidos. NumPy existente foi fixado também como dependência direta.

Veja o [roteiro detalhado](../../docs/VALIDACAO_MANUAL_ETAPA_04.md), o
[relatório](../../docs/RELATORIOS/ETAPA_04.md) e o
[inventário/termos do modelo e biblioteca](../../docs/RELATORIOS/DEPENDENCIAS_E_MODELOS.md).
