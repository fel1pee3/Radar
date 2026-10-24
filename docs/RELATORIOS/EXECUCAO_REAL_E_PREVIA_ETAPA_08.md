# Execução cadenciada e prévia estabilizada — etapa 08

## Verificação geral final desta rodada

`pnpm.cmd demo:verify` exit 0, 14 tarefas aprovadas: frozen JS/Python,
lint/tipos/build, edge-lint/imports, 100 contratos TS, quatro testes do simulador,
317 testes Python sem skip, 155 API, 20 E2E, backup/restore e instalação limpa.
Código avaliado: HEAD 68ac3d60418ecc6b272990f6c48a14c62918ed13, árvore alterada,
179 arquivos, SHA-256
`a2b76fa33449fac7a438efa10e5470580b6310a6b12530d62bf33790b8aeb991`.
Evidência em `.local/etapa08/engineering.json`; rodada anterior preservada em
`engineering-before-stabilization-<id>.json`. Imports gerados de next-env.d.ts
restaurados ao estado anterior após o build.

Também executados `pnpm.cmd demo:check --engineering` (exit 0),
`pnpm.cmd demo:check` (exit 2 esperado por gates manuais) e `git diff --check`
(exit 0). O check mantém lista manual genérica: LIVE/revisão e offline já
comprovados seguem no STATUS, sem exigir repetir essas provas. A etapa continua
parcial por percepção delimitada, 30 min contínuos e apresentação.

Preparado helper privado `.local/etapa08/preview-stable-worker.ps1`, sintaxe
PowerShell validada. Lançado começando pausado no mesmo arquivo autorizado,
sem webcam/eventos/HTTP, pela CLI normal com `--preview-paused`. Logs em
`.local/etapa08/stabilized-worker-check/viewer.log` e `viewer-errors.log`;
lançamento em `.local/etapa08/stabilized-worker-preview-launch.json`.
Conferência concluída: fundador respondeu “Acompanha bem; movimento aceitável”.
Report `results/5f15051f-41e4-4144-a417-c1fe8207e7f2/report.json` terminou
ok/ENDED: 187 quadros decodificados, 32 análises válidas, zero ausência/erro,
inferência média 100,41 ms. Sem eventos, HTTP ou quadros salvos. Tempo total
1136,53 s inclui 1129,76 s pausados; não interpretar como FPS do modelo ou
ensaio contínuo. Confirmação e hashes em `stabilized-worker-check/human-review.json`.
Essa conferência durante inferência é separada das prévias já geradas e não
precisa ser repetida para validar o mesmo arquivo.

Para reproduzir, sem nova calibração ou credencial:

```powershell
. ./scripts/activate.ps1
uv run --offline --project services/edge --frozen radar-edge run --config .local/etapa08/stabilized-worker-check/config.yaml --preview-paused
```

Espaço inicia; Q/Esc encerra. Fonte FILE, sem comprovação física de webcam.

23/10/2026. Etapa 08 **PARCIAL**. Continuação da
[comparação quadro a quadro](QUADRO_A_QUADRO_ETAPA_08.md). Sem webcam, commit,
push, deploy, treinamento, dependência nova ou alteração dos dados originais.

## Medição com inferência durante a execução

Arquivo FILE publicado no ritmo dos timestamps de mídia por thread, slot único
e consumidor da imagem mais recente. Sem fila crescente de imagens antigas.
Modelo RTMO-s CPU/quatro threads, mesma qualidade e filtro visual conferido.

| Ensaio | Análises/publicações | Desenhos/s de relógio | Idade média/P95 ao concluir desenho ou submissão GUI (ms) |
| --- | --- | --- | --- |
| Cadeira 2, alvo 5 Hz, sem janela | 33/187 | 5,00 | 159,34 / 186,61 |
| Cadeira 2, capacidade, sem janela A | 47/187 | 7,22 | 166,35 / 202,41 |
| Piso 07, capacidade, sem janela | 39/153 | 7,40 | 161,29 / 199,79 |
| Histórico 07, capacidade, sem janela | 67/269 | 7,30 | 162,09 / 198,76 |
| Cadeira 2, capacidade, sem janela B | 47/187 | 7,36 | 160,95 / 215,52 |
| Cadeira 2, capacidade, janela nativa | 34/187 | 5,21 | 213,87 / 252,11 |

Seis execuções até EOF: 1170 quadros publicados, 267 analisados, 903 substituídos
antes da análise, três sem pontos. Nenhum quadro futuro ou repetido consumido.
Dados brutos iguais às análises anteriores dos mesmos pixels. Na cadeira, zero
quadros sem pontos nas quatro execuções. Uma lacuna acima de 250 ms no ensaio
GUI reiniciou o filtro, respeitando seu limite. Idade máxima 262,89 ms no conjunto.
A medida termina no desenho/submissão GUI; não mede o instante físico no monitor.

Filtro: médias 0,31–0,40 ms por análise. No ensaio GUI, inferência média 177,01 ms
e desenho/GUI 11,94 ms. Ordem não contrabalanceada para isolar janela, temperatura
ou carga; não atribuir causalmente toda diferença à GUI. Pico cumulativo de
working set do processo 297635840 bytes. Carregamento e uma inferência de
aquecimento por ensaio excluídos das cadências e registrados separadamente.
Arquivo cadenciado não comprova driver, webcam física ou os 30 min obrigatórios.
**Não foram obtidos 30 FPS de inferência/exibição com esse modelo no ensaio.**

Artefatos: `.local/etapa08/paced-inference-ce0c03f2-5d5f-466e-8841-8ae3db0971be/`,
seis relatórios e traços por quadro. Três testes do slot passaram: consumidor
lento, EOF sem repetição e propagação de erro. O erro não vira fim normal.

## Integração opcional

`processing.previewStabilization: true` habilita o candidato na prévia FILE/LIVE.
Default false preserva configurações existentes. Novo módulo `visual_smoothing.py`;
preview, config e chamadas FILE/LIVE adaptados. Somente desenho em ciano é
filtrado; posição de evidência, snapshot, features, frequência de análise,
transporte e checkpoint continuam brutos. A legenda explica essa diferença.

LocalPreview filtra uma vez por observação, reaproveita o desenho durante pausa,
valida correspondência de imagem/pose e escala os pixels em vídeo vertical.
Reset em ausência/score baixo/múltiplas poses, troca de contexto, relógio ou lacuna;
sem completar articulação ausente. Não foi ativado em configurações anteriores.

Equivalência: 1236 quadros com diferença máxima de 0 px frente ao experimento
conferido pelo fundador. Teste de integração comparou dados exportados, quantidade
de eventos e fingerprint com opção ligada/desligada em fonte sintética isolada.
O teste inicial falhou por exportação diagnóstica desabilitada; corrigida a
preparação, sem reduzir critério. Ruff corrigiu importação do novo teste.
38 testes direcionados passaram. Resultado geral registrado ao final desta rodada.

CLI normal executada na cadeira autorizada: ok/ENDED, 187 quadros decodificados,
32 inferências válidas, zero ausências, 6,78 s totais, inferência média 115,31 ms,
4,72 análises/s de relógio incluindo preparação. Eventos desabilitados: sem
incidente ou HTTP. Config privada `.local/etapa08/stabilized-worker-check/config.yaml`.
Report `results/ee4bf7f0-bca1-45b9-b6db-b13fcdfa1bc6/report.json` nesse diretório.
Nenhum arquivo original de configuração/calibração/outbox foi alterado.

## Comandos realmente executados

```powershell
. ./scripts/activate.ps1
uv run --offline --project services/edge --frozen pytest .local/etapa08/test_paced_file_slot.py -q
uv run --offline --project services/edge --frozen python .local/etapa08/realtime-file-benchmark.py --gui
uv run --offline --project services/edge --frozen pytest services/edge/tests/test_visual_smoothing.py services/edge/tests/test_temporal_pipeline.py services/edge/tests/test_preview.py -q
uv run --offline --project services/edge --frozen ruff check services/edge
uv run --offline --project services/edge --frozen radar-edge run --config .local/etapa08/stabilized-worker-check/config.yaml
pnpm.cmd demo:verify
```

A melhoria integrada reduz tremor do desenho; não aumenta automaticamente FPS
ou precisão anatômica, não corrige as três perdas e não aprova o ensaio físico.
Continuidade/qualidade geral, 30 min contínuos e apresentação permanecem na matriz
de aceite. Não repetir as conferências de vídeos já respondidas como se pendentes.
