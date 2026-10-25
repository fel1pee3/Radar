# Evolução do detector — incremento 01

Data: 24/10/2026. Estado: **PARCIAL**, sem aprovação de MVP funcional.
Escopo autorizado em [plano e critérios](../EVOLUCAO_DO_DETECTOR.md), preservando
08/D50/D51. Baseline 0778e02, árvore limpa antes de iniciar; RTMO-s mantido.

## Entregas e verificações desta rodada

- Inventário de 41 vídeos, arquivo do código e cópias de configurações/pisos com
  hashes em `.local/detector-evolution/baseline-0778e02/baseline.json`.
- Exportador de decisões limitado, com retenção, quota, exclusividade por raiz
  e status de captura. Integrado aos caminhos FILE/LIVE e EventRuntime.
- Diagnóstico lê observações reais; não muda os sinais/decisões da baseline.
- Retomada preserva evento se gravação diagnóstica falhar depois do checkpoint.

| Comando realmente executado | Resultado | Alcance |
| --- | --- | --- |
| `git status --short`; `git log -1` | Árvore limpa, 0778e02 | Não presumiu que o commit antigo ainda era a baseline |
| `uv run --offline --project services/edge --frozen python .local/prepare-detector-baseline.py` | Exit 0; 41 vídeos, hashes/configs/modelo arquivados | Sem câmera, cópia local fora do Git |
| Ruff check/format nos arquivos alterados | Formatação/imports corrigidos; rechecagem aprovada | Sem nova dependência |
| `uv run --offline --project services/edge --frozen pytest services/edge/tests/test_decision_trace.py services/edge/tests/test_live_health.py services/edge/tests/test_temporal_pipeline.py -q` | 22 passed | Limites/privacidade/reset/retomada/FILE e adaptador LIVE sintéticos; não câmera física |
| `uv run --offline --project services/edge --frozen python .local/detector-evolution/run-baseline-traces.py` | Exit 0; 3/4 alvos reproduzidos, perda S9 preservada | Inferência RTMO real nos 12 CAUCAFall, novas filas e traces, sem HTTP/webcam |

## Continuidade executada

Comparação e integração foram executadas depois desta instrumentação inicial.
O [incremento 02](EVOLUCAO_DETECTOR_02.md) registra classificador, histerese,
reprodução das perdas, resultados reais, comandos e pendências. CAUCAFall passa
a desenvolvimento/seleção da nova versão; avaliação histórica preservada.
