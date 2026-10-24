# Sessão física de 10 minutos — etapa 08

Data: 24/10/2026, America/Sao_Paulo.
Resultado: **continuidade e encerramento verificados no escopo nominal D51**.
Não comprova o ensaio original de 30 min ou eficácia geral do detector.

## Execução e identidade

Comando executado pelo fundador, após resolver o conflito de calibração:

```powershell
. ./scripts/activate.ps1
powershell -NoProfile -File scripts/validation/observe.ps1 -Config .local/etapa08/webcam-10min.yaml
```

Worker LIVE `9c560226-183a-45ea-abc6-6e4fde5b9c65`, execução SQLite
`afcd95b9-3a38-44b1-835b-b651614ba670`, diagnóstico
`3192ea80-c6f9-4a4d-bb25-6cb9f65c0acc`. Monitor privado:
`.local/etapa08/continuous-4d4357f7-8ff9-450b-9922-9f2560823b29/`.
Contém worker.json, worker-errors.log vazio, resources.jsonl, audit.json e
human-review.json. Relatório original em
`.local/etapa08/webcam-10min-preparation-302fa34d-22d5-40d8-859b-e1884a09a5d6/results/3192ea80-c6f9-4a4d-bb25-6cb9f65c0acc/report.json`.
Auditoria comparou os dois relatórios como JSON e verificou o checkpoint SQLite.

Mesma fonte webcam 0/DSHOW, 640×480, RTMO-s experimental CPU, política
floor-rtmo-score-v0.1, estabilização visual ligada e piso
ab0094ef-eee7-478b-8304-bf96139c0d48-v3. Fonte de 179 arquivos SHA-256
`a2b76fa33449fac7a438efa10e5470580b6310a6b12530d62bf33790b8aeb991`,
sem alteração de modelo/gates durante o ensaio. Modelo SHA-256
`d0703d40d19f3921da51ae725402d5fdae4d2478c7442072d3101bd396f370d8`.

## Medições e denominadores

| Medida | Resultado | Método/limite |
| --- | --- | --- |
| Tempo total do worker | 600,660 s | Inclui abertura/modelo/limpeza; atende limite nominal 600 s de D51 |
| Intervalo entre primeira e última análise | 597,453 s | Timestamps monotônicos 641–598094 ms; não são 600 s de imagens úteis |
| Intervalos elegíveis | 576,986 s | Ambos os extremos elegíveis, conforme soma conservadora do motor |
| Intervalos inelegíveis | 20,467 s | Observado menos elegível; não comprova ausência de ocorrência |
| Tempo fora do intervalo de análises | 3,207 s | Diferença para wall time; sem contador que separe exatamente aquecimento, caudas e limpeza |
| Análises | 2799 | 2726 ONE_VALID_POSE, 54 LOW_CONFIDENCE, 19 NO_POSE; zero múltiplas poses |
| Cadência de análise | 4,68/s no intervalo observado | 4,66/s por tempo total; alvo configurado 5/s |
| Inferência por análise | Média 119,96 ms; 103,34–194,76 ms | Tempo do estimador CPU, sem inferir FPS de exibição de vídeo |
| Aquisição da câmera | 17854 imagens | 29,72 imagens/s por tempo total do worker, incluindo setup/limpeza; não FPS instantâneo do driver |
| Imagens consumidas/sobrescritas no slot | 2800 / 15054 | Inclui primeira imagem de configuração; slot mantém a imagem recente, não uma fila de vídeo |
| Reconexões / erro de captura | 0 / nenhum reportado | Monitor não observou captura PAUSED/ERROR; amostragem pode perder transições curtas |
| Eventos / candidatos / pendências | 0 / 0 / 0 | SQLite e relatório coerentes; sem imagens JPEG ou vídeo gravado |
| CPU do worker | 1572,766 CPU-s; 261,84% de um núcleo lógico | Equivale a cerca de 2,62 núcleos durante o processo; não uso global do computador |
| Pico de memória do worker | 235945984 bytes, cerca de 225 MiB | Peak working set do processo Windows, inclui threads nativas |
| Pico de memória somada dos processos monitorados | 350007296 bytes, cerca de 334 MiB | Pode contar páginas compartilhadas mais de uma vez |

Monitor: 537 amostras de 12:30:18,692 a 12:40:19,427 locais; maior intervalo
entre amostras 1,197 s. Três amostras iniciais sem status, depois 534 RUNNING,
mesmo runId e heartbeat ACCEPTED em todas. Maior idade do status 1,138 s.
Uma amostra WARMING_UP com FRAME_TIMEOUT aos 3,866 s e imagem de 15 ms de idade;
LiveHealth inicializa assim antes da primeira análise. Não tratar essa marca
isolada de aquecimento como desconexão física; zero reconexões e sem erro final.
Zero retries de escrita de status.

Estado final do worker e heartbeat: ENDED; ACK final ACCEPTED. O campo
source.captureState=RUNNING é o último snapshot de metadados do capturador,
não a situação final da sessão. Fundador confirmou fechamento automático e
“Fonte encerrada” no painel. PRAGMA integrity_check da fila retornou ok;
checkpoint 17853/598094 ms, histórico anterior aposentado e reset preservados.

## Conferência humana e trecho no chão sem alerta

Fundador relatou principalmente ficar sentado em uma rede, também deitar na
rede, fazer polichinelos e deitar brevemente no chão para testar. Avaliou o
acompanhamento como bom, com poucas ausências do esqueleto, mas poucos FPS.
A prévia atual é atualizada junto das análises, perto de 4,7 vezes/s nesta sessão;
não atribuir a baixa cadência automaticamente à webcam, cuja aquisição foi maior.

Sobre o chão: informou **menos de 10 s**, com o corpo enquadrado. Não foram
confirmados o instante, a duração exata, uma janela elegível contínua de pelo
menos 2 s ou o quadril dentro do polígono. Zero eventos/candidatos no ensaio.
Registrar **possível perda, inconclusiva com a anotação disponível**; não
afirmar que o detector acertou ou atribuir causa a piso, pose ou duração sem
prova. Corpo enquadrado não confirma quadril dentro da ROI ou gates de geometria.

O LIVE atual salva métricas agregadas, não JSONL por observação, mesmo com
exportObservations configurado. Sem vídeo ou observações individuais não há
reconstrução retrospectiva exata desse trecho nem de cada uma das lacunas de
pose. Os 20,467 s inelegíveis não podem ser atribuídos ao chão por suposição.
Não publicar taxa de falso alerta/hora ou recall desta sessão mista sem
anotação temporal completa. Não solicitada repetição física para maquiar esse
resultado. O percurso LIVE positivo/revisado anterior permanece comprovado no
incidente 4e6f8c4b…; esta sessão não acrescentou outro positivo.

## Verificações realmente executadas após a sessão

| Comando/ação | Resultado |
| --- | --- |
| Leitura de worker.json/report.json/resources.jsonl e inventário de processos | Encerramento normal; nenhum worker de câmera ativo |
| `uv run --offline --project services/edge --frozen python .local/etapa08/audit-completed-webcam-10min.py` | Exit 0; relatórios coerentes, duração/saúde/recursos e SQLite auditados sem abrir câmera |
| `uv run --offline --project services/edge --frozen python .local/etapa08/record-completed-webcam-10min-review.py` | Exit 0; respostas reais vinculadas ao hash da auditoria, sem inventar ROI/tempo exato |
| `node .local/etapa08/verify-cauca-source.mjs` | Exit 0, código a2b76fa3… preservado |
| `pnpm.cmd demo:check --engineering` | Exit 0, evidência da engenharia ainda corresponde ao código atual |
| `git -c core.safecrlf=false diff --check` | Exit 0 após consolidar os relatórios |

Código não alterado; a suíte completa anterior continua identificando este
candidato. Não repetir dezenas de testes ou a webcam só para aumentar contagem.
Scripts privados de auditoria e todos os dados pessoais permanecem fora do Git.

## Decisão de alcance

Continuidade, medição, encerramento e conferência humana de D51 atendidos.
Etapa 08 encerrada **no escopo revisado da demonstração experimental de bancada**,
com matriz/relatório final; não é aprovação geral de segurança. O requisito
original de 30 min não foi comprovado. Falha histórica aos 27min45s, perda
CAUCAFall, perdas históricas, possíveis poses em objetos e este trecho sem
alerta continuam registrados. Apresentação formal dispensada por D50.
Não avançar automaticamente à etapa 09, publicar, vender ou monitorar terceiros.
