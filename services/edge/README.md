# Worker local — visão em arquivo

Etapa 05: motor temporal, SQLite/checkpoint, entrega local e evaluate disponíveis.
Validação **concluída para a bancada**: após os resultados negativos com Lite,
Full produziu um evento real em piso-f-07, entregue à API e conferido pelo
fundador no painel como REPLAY/TEST. Outros enquadramentos continuam falhando;
não há promessa de eficácia geral. Veja o
[roteiro 05](../../docs/VALIDACAO_MANUAL_ETAPA_05.md) e o
[relatório 05](../../docs/RELATORIOS/ETAPA_05.md).

`events.enabled` é false por padrão para preservar o uso de poses da 04. Na cópia
privada habilite events, escolha outbox dedicada e habilite delivery somente com
credencial da câmera. EVIDENCE_MODE aceita none/skeleton; sem imagem ou pontos
faciais. Modelos, vídeos, SQLite e tokens permanecem em .local ignorado.

```powershell
. ./scripts/activate.ps1
uv run --project services/edge --frozen radar-edge run --config .local/edge-events.yaml --no-preview
uv run --project services/edge --frozen radar-edge outbox-status --config .local/edge-events.yaml
uv run --project services/edge --frozen radar-edge deliver --config .local/edge-events.yaml
uv run --project services/edge --frozen radar-edge evaluate --manifest .local/evaluation.json
```

Run repete somente a partir do checkpoint; EOF não reanalisa. Reset local exige
worker parado e motivo com `reset-episode --config ... --reason scene_reset`;
preserva histórico/pendências e não fecha o incidente humano. Evaluate sempre cria
outbox isolada sem entrega HTTP. Formato em evaluation.example.json.

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

Lite é o padrão preservado. Full é uma seleção explícita validada na etapa 05:

```powershell
uv run --project services/edge --frozen radar-edge model-fetch --variant full
uv run --project services/edge --frozen radar-edge run --config .local/edge-piso-f-07-full.yaml --poses-only --preview-paused --replay-speed 0.5
```

Na configuração privada use model.variant=full e
model.path=.local/models/pose_landmarker_full.task. IDs/hashes corretos aparecem
no relatório/evento e identificam a execução; Full não retoma histórico Lite.
A prévia pode começar pausada, com Espaço para iniciar/pausar/retomar e Q/Esc para
sair. Pontos verdes exigem presença e visibilidade suficientes; não são uma
classificação de piso. Diagnósticos por articulação são apenas contagens agregadas.

Copie `edge.example.yaml` para `.local/edge.yaml` sem sobrescrever configuração
existente. Informe caminho local autorizado, UUID da câmera lógica e
`source.authorized: true` somente quando tiver autorização. Caminhos relativos
são resolvidos a partir da raiz, inclusive quando se usa `uv --project`.
O percurso de poses da 04 não precisa de bearer nem chama a API. Na 05, a entrega
de eventos é explícita e referencia credencial privada, sem senha humana.

```powershell
uv run --project services/edge --frozen radar-edge doctor --config .local/edge.yaml
uv run --project services/edge --frozen radar-edge calibrate --config .local/edge.yaml --frame-ms 0
uv run --project services/edge --frozen radar-edge run --config .local/edge.yaml --preview --replay-speed 1
uv run --project services/edge --frozen radar-edge run --config .local/edge.yaml --no-preview
```

O diagnóstico `doctor` abre/decodifica o primeiro frame e executa o modelo real;
`calibration: MISSING` permite preparar a calibração, não autoriza rodar sem ROI.
`run` exige calibração compatível e produz poses REPLAY; events.enabled habilita
o motor e delivery.enabled habilita entrega de incidentes. Sem essas opções,
mantém o percurso de poses da 04. Não emite heartbeat nesta etapa; janela local,
sem streaming web.

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
