# Verificação da demonstração física DirectML — 28/10/2026

**Fluxo físico até painel e revisão: PARCIAL.
Critérios operacionais: NÃO ATENDIDOS pela cobertura de decisão.
Confiabilidade geral do detector: continua SEM COMPROVAÇÃO.**

Houve um evento LIVE entregue à API, um incidente e um aviso local.
A revisão humana **não está salva**: versão 1, UNREVIEWED, zero ações.
Os demais dados puderam ser verificados; a avaliação não é inteiramente inconclusiva.

Rodada somente de análise de resultados existentes. Nenhuma câmera, inferência
nova, reenvio, revisão automática, alteração do detector/parâmetros, treino,
suíte de testes, commit, push ou deploy foi executado.
Leitura de AGENTS, README, STATUS, roteiro DirectML e relatório de integração.
As alterações locais anteriores foram preservadas.

Consulta final ao banco da demonstração: **28/10/2026 às 14:10:24,895**
America/Sao_Paulo, equivalente a 17:10:24.895Z.
Transação REPEATABLE READ com READ ONLY confirmado como on.

## 1. Seleção e identificação inequívoca

Partida: `.local/directml-demo-current.json`, campo config.
Ele aponta para:

`.local/detector-evolution/directml-integration-757f4105-e1ad-46ca-8efb-995ad297eb3e/physical-demo/config.yaml`

O rótulo PREPARED no ponteiro é metadado da preparação, não um estado ao vivo.
Não foi reescrito. Os resultados LIVE abaixo comprovam a execução posterior.

Há duas tentativas nessa pasta:

| Relatório | Origem local da captura | Duração | Encerramento | Eventos desta tentativa |
| --- | --- | ---: | --- | ---: |
| 075b0e35-b841-4a24-a827-6d93063fd746 | 13:52:28,187 | 9,61 s | PREVIEW_EXIT | 0 |
| **7307ddc3-f63c-4cd4-91e5-212422305755** | **13:54:09,162** | **60,81 s** | **MAX_RUN_SECONDS** | **1** |

**A análise principal usa somente a segunda tentativa**, com 261 decisões.
Não soma as 29 decisões anteriores, o intervalo entre tentativas ou dados de
FILE/TEST. Ambas usam a mesma outbox e a mesma execução lógica persistente;
a identidade de captura é diferente.

| Camada | ID |
| --- | --- |
| Câmera WEBCAM “Camera de bancada” | 5be84234-7b00-4e87-85e8-b0e68f7c2a6d |
| Captura/heartbeat/evento, sessão analisada | 5d456564-3ae5-4ba9-9bd3-a83765b8ca4d |
| Execução lógica SQLite, retomada | 5ebdadf5-36d4-43ea-943e-b3fb26227356 |
| Relatório de diagnóstico | 7307ddc3-f63c-4cd4-91e5-212422305755 |
| Episódio | 62d08436-1f07-465c-95a9-f4b4de469173 |
| Evento | d0fe9a91-4c93-45a2-8b1b-5a01566237ee |
| Incidente na demonstração | 3f8db408-fbb1-4286-ad75-be8e9a3ce57a |
| Intenção do aviso local | 491f8c3b-2375-4c01-b1d5-cc4d113429aa |
| Entrega do aviso local | 54fece07-ad25-4476-b38c-39505f7fe353 |

Início da captura: **13:54:09,161843**, UTC 16:54:09.161843Z.
Estado final do trace: **13:55:09,969411**, UTC 16:55:09.969411Z.
Duração pelo relógio do host: **60,8085362 s**. O limite era 60 s;
a análise/liberação/envio finais explicam o tempo medido além do limite.
Não houve interrupção manual na tentativa selecionada.

Caminhos, relativos à pasta physical-demo acima:

- Relatório: `results/7307ddc3-f63c-4cd4-91e5-212422305755/report.json`.
- Trace: `results/7307ddc3-f63c-4cd4-91e5-212422305755/decisions.jsonl`.
- Outbox: `outbox.sqlite`, com WAL/SHM existentes preservados.
- Status final: `.local/edge-control/5be84234-7b00-4e87-85e8-b0e68f7c2a6d-status.json`.

## 2. Configuração e executor

Captura nativa WEBCAM 0, DSHOW, 640×480, rotação zero; 1.738 frames adquiridos,
262 consumidos incluindo o de preparação e 1.476 sobrescritos pela política
de buffer com o frame mais recente. Sobrescrita não é falha de captura.
Zero reconexões, captureState ENDED e errorCode nulo.

Executor efetivamente inicializado segundo o relatório:

- DIRECTML, onnxruntime-directml **1.23.0**, initialized=true.
- DmlExecutionProvider e CPUExecutionProvider; adaptador físico DXGI 0,
  AMD Radeon (TM) Graphics, PCI 1002:15E7, softwareAdapter=false.
- ORT_SEQUENTIAL, memory patterns desligados, batch=1, intra-op 4/inter-op 1;
  fallback automático de sessão desabilitado.
- Inicialização da sessão: 419,6 ms.
- Modelo rtmo-s-body7-640x640-20231211-onnx-v1, SHA-256
  d0703d40d19f3921da51ae725402d5fdae4d2478c7442072d3101bd396f370d8.
- REFERENCE_4_SPIN + RTMO_ADAPTIVE_V3, classificador signed-body-mlp-v3-dev01,
  mesma política adaptive3 e calibração ab0094ef-eee7-478b-8304-bf96139c0d48-v3.

O fingerprint dos parâmetros de percepção/configuração foi reconstruído sem
abrir fonte/modelo e corresponde ao persistido:
`4c1f5e30df38b4b0bc230ebc242ae9a9fb850d58d33532d7a7c9526f25338c08`.
Inclui fonte, geometria, calibração, pesos, política, classificador, qualidade,
amostragem e executor. Os valores críticos coincidem com a configuração indicada.
SHA-256 do YAML na leitura:
`52fb08c0d2c88ea6083e96325423ac7153a901a687025bb2e18be4453f0584e6`.

O worker não arquiva o YAML inteiro/hash por sessão; esse checksum é do arquivo
lido nesta auditoria. Opções não incluídas no fingerprint não recebem comprovação
retrospectiva byte a byte. O encerramento automático e os demais metadados
observados são coerentes com o limite configurado.

Profiling por operador estava desligado nesta sessão. Não há nova atribuição
nó a nó à GPU: a lista de providers não é tratada como essa prova. A inicialização
DML/AMD foi registrada e a computação GPU dos mesmos pesos/executor foi comprovada
separadamente na [integração FILE](INTEGRACAO_DIRECTML_2026_10_28.md).

## 3. Percurso do evento e recebimento

Horários abaixo em America/Sao_Paulo; originais UTC foram preservados.

| Marco persistido | Horário |
| --- | --- |
| Início da evidência contínua, amostra do evento | 13:54:34,131 |
| Amostra que confirmou PERSON_ON_FLOOR / detectedAt | 13:54:36,209 |
| Evento inserido atomicamente na outbox | 13:54:36,321 |
| API recebeu/criou o incidente e a intenção de aviso | 13:54:36,391 |
| ACK salvo como DELIVERED no SQLite | 13:54:36,424 |
| Aviso local e respectivo registro auditado | 13:54:36,933 |
| Episódio fechado no SQLite após rearme | 13:55:02,497 |
| Heartbeat ENDED recebido pela API | 13:55:09,952 |

Vinculação confirmada: o envelope local usa a captura 5d456564…, a mesma do
incidente e do heartbeat. O episódio SQLite pertence à execução lógica
5ebdadf5…, retomada da tentativa anterior. Essa identidade persistente não
transforma as duas capturas em uma única sessão de 160 s.

Resultados:

- **Uma emissão**, um evento SQLite, um episódio, um recibo da API e um incidente.
- Outbox DELIVERED, attempts=1, sem erro, ACK com mesmo eventId/incidentId e
  receivedAt idêntico ao banco. duplicate=false.
- **Não houve reenvio nesta sessão**. Logo, não se afirma que ela exercitou
  idempotência de reenvio; há apenas uma emissão e nenhum incidente duplicado.
- Uma intenção de aviso DELIVERED, attempts=1, uma entrega local e um registro
  SIMULATED_NOTIFICATION_RECORDED/RECORDED_LOCALLY.
- Evento **LIVE/CURRENT**. SIMULATED é o nome do canal de aviso local existente,
  não o modo da captura. Não houve mensagem externa.
- Zero pendentes no relatório, status, heartbeat/API e snapshot da outbox.

O detectedAt precede a inserção local em 112 ms; a API recebeu 182 ms depois
do detectedAt. Esses deltas UTC incluem etapas diferentes e não representam
latência humana ou tempo de rede puro. Não aparece o adiantamento de +282 ms
da tentativa antiga.

**A existência desses registros não comprova quando o incidente apareceu
visualmente no navegador.** Não há captura/log do navegador ou marcação humana
de primeira aparição nesta execução.

### Revisão humana: pendente, com evidência objetiva

Na consulta final: status OPEN, review **UNREVIEWED**, versão **1**,
`actions=[]`. O histórico contém somente INCIDENT_CREATED e
SIMULATED_NOTIFICATION_RECORDED, ambos sem ator humano.

Portanto, não há reconhecimento ou revisão humana salva. Isso localiza a
pendência no passo de revisão; não demonstra, por si, defeito no formulário,
tentativa de envio rejeitada ou erro do fundador. O motivo da ausência não está
registrado. Nenhuma ação foi gravada pelo assistente.

## 4. Classificações e evolução temporal

O relógio persistido é o da execução lógica, cuja origem vem da primeira
tentativa. Nesta captura, `sourceTimestampOffsetMs=100976`.
Para informar tempos desde a origem física, usa-se a conversão
`timestampMs - 100976`. Os timestamps dos eventos/traces não foram reescritos.
Essa troca de referência não remove início/fim ou trechos difíceis.

| Marco do modelo/motor | Tempo desde início físico |
| --- | ---: |
| Primeira aquisição analisada | 2,594 s |
| Primeira decisão pronta no host | 3,094 s |
| Primeiro LYING, isolado e inelegível | 19,516 s |
| Início contínuo elegível / OBSERVING → SUSPECTED | 24,969 s |
| Confirmação do evento / SUSPECTED → ACTIVE | 27,047 s |
| Decisão do evento pronta no host | 27,172 s |
| Última observação da sequência contínua LYING | 49,500 s |
| ACTIVE → REARMING, classe prevista SEATED | 50,110 s |
| Rearme concluído / OBSERVING / episódio fechado | 53,219 s |
| Última aquisição analisada | 59,875 s |
| Última decisão pronta no host | 59,985 s |

A primeira classe LYING, aos 19,516 s, foi excluída por
LYING_OUTSIDE_OBSERVED_REGION e não iniciou evidência de piso.
Depois houve SEATED/UNKNOWN previstos pelo modelo. A sequência contínua seguinte
teve **118 observações**, de 24,969 a 49,500 s: **24,531 s entre extremos**.
Foram 119 classificações LYING no total, contando a isolada.

O evento acumulou **2.078 ms de evidência**, fração válida 1,0 e 4,5 análises/s
na janela. Não houve descida rápida observada; nenhum POSSIBLE_FALL foi emitido.

**2.078 ms não são a latência após a pessoa deitar.** Não há marcação humana
independente do início real da postura. A latência humana é **inconclusiva**,
e as classes do próprio modelo não confirmam o que a pessoa realmente fez.
Sem revisão/relato específico salvo, não se aprova também a correspondência
do alerta à atividade física real nem os controles como verdadeiros negativos.

Contagens da sessão:

| Medida | Quantidade |
| --- | ---: |
| Decisões e perfis finais | 261 / 261 |
| ONE_VALID_POSE | 230 |
| LOW_CONFIDENCE | 11 |
| NO_POSE | 20 |
| BODY_OUT_OF_FRAME, flag sobreposta | 5 |
| UNKNOWN de postura | 6 |
| STANDING_OR_WALKING previsto | 56 |
| SEATED previsto | 44 |
| KNEELING_OR_CROUCHING previsto | 16 |
| LYING previsto | 119 |
| Interrupções temporais / reconexões | 0 / 0 |
| Auditorias SQLite de interrupção temporal | 0 |

As 20 observações NO_POSE ocorreram no início, entre 2,594 e 9,157 s.
Isso não prova cômodo vazio, pessoa fora do quadro ou problema de iluminação.
A causa física das inelegibilidades é **indeterminada** sem vídeo/anotação.
O rearme lógico foi comprovado, inclusive pelo episódio CLOSED no SQLite;
a atividade humana que o motivou não é certificada pela classe SEATED.

## 5. Operação e cobertura, com critérios preservados

| Medida | Média / P95 / máximo |
| --- | ---: |
| Percepção por análise, incluindo recuperações | 103,5 / 307,8 / 471,3 ms |
| Processamento total, incluindo prévia | 120,9 / 324,7 / 506,3 ms |
| Runtime/checkpoint/métricas | 5,9 / 8,8 / 15,6 ms |
| Prévia | 9,5 / 18,3 / 40,6 ms |
| Idade do frame na decisão | 130,4 / 328,0 / 500,0 ms |

261 amostras em cada série; P95 com interpolação linear.
O pico de processamento total inclui a prévia e não equivale à idade da decisão.

- 4,54 análises/s entre aquisições analisadas; **4,29/s na duração total**.
- Prévia: 4,57 atualizações de observação/s. Não é FPS do monitor/câmera.
- Heartbeat final: 4,87 análises/s na janela recente; não é média da sessão.
- 326 inferências: 230 análises com uma, 11 com duas, seis com três e 14 com quatro.
- Maior intervalo entre observações: **500 ms**, no limite permitido.
- Maior intervalo entre decisões prontas: **407 ms**.
- Zero intervalos internos acima de 500 ms; zero decisões acima de 2 s de idade.
- CPU principal: 53,99% de um processador lógico, ou 4,50% normalizado pelos 12;
  working set de pico 401,72 MiB. Não inclui toda a CPU da captura filha,
  memória do driver/GPU ou consumo elétrico.

O metadado de câmera de 30 FPS não é uma medição da fluidez da prévia.
Não há avaliação visual nova do esqueleto.

| Horizonte completo | Decisão elegível | Captura tempestiva |
| --- | ---: | ---: |
| **60 s previstos** | **47.921 ms / 79,8683%** | 57.281 ms / 95,4683% |
| **60,8085362 s executados** | **78,8064%** | 94,1989% |

Cobertura de decisão mínima: **80%**. A execução **não atende** nos dois
denominadores. Não se arredonda 79,8683% para aprovação. Usar somente os
57,281 s entre frames analisados daria uma razão diferente e não foi usado.

Intervalos sem cobertura de decisão elegível nos 60 s, em segundos:

| Início | Fim |
| ---: | ---: |
| 0,000 | 9,500 |
| 12,078 | 12,516 |
| 19,110 | 19,719 |
| 24,594 | 24,969 |
| 49,500 | 50,110 |
| 54,703 | 55,125 |
| 59,875 | 60,000 |

O primeiro intervalo inclui 2,594 s antes da primeira aquisição analisada e
6,906 s com observações inelegíveis/limites entre elas.
Os demais intervalos entre aquisições inelegíveis somam 2,454 s.
A cauda é 0,125 s no horizonte previsto e 0,9335362 s no executado.
Não se excluiu inicialização, encerramento ou o trecho inicial sem pose.
Não há dados para atribuir cada inelegibilidade a movimento, enquadramento
ou erro anatômico específico.

O auditor existente foi usado sobre os deltas e o tempo de decisão no host.
Seus campos de cabeça/cauda no relógio de episódio não servem diretamente para
LIVE retomado; os tempos físicos acima foram derivados pelo deslocamento
documentado. O numerador continua 47.921 ms, sem aumentar tolerâncias.

## 6. Encerramento e consistência final

Relatório, metadados de captura, heartbeat local, arquivo de status e
lastHeartbeat na API: **ENDED**, mesma captura 5d456564… e zero pendentes.
API: sequência 21, heartbeat recebido às 13:55:09,952.
261 decisões têm exatamente 261 perfis correspondentes, incluindo a última;
nenhum truncamento ou falha de escrita do trace.

Snapshots de heartbeat coletados em instantes diferentes têm horários e idades
ligeiramente diferentes, sem divergência de identidade/estado/pendentes.
A idade de snapshot final não substitui a idade medida na decisão.

A execução lógica SQLite continua completed=0, disponível para retomada.
Isso não significa captura aberta: a sessão física terminou e o episódio está
CLOSED. Não houve nova emissão ao rearme.

## 7. Preservação, comandos reais e reprodução

Auditoria privada nova:
`.local/detector-evolution/directml-physical-audit-abc219f8-b5f5-4e3c-b050-7f895d33311f`.

Os originais foram copiados com hashes estáveis. Como havia WAL/SHM, o trio
SQLite foi copiado antes de abrir qualquer conexão. Uma segunda cópia de
trabalho foi aberta em mode=ro e exportada para snapshot privado.
Não se usou immutable=1 no banco original ignorando o WAL.

O PostgreSQL da demonstração foi consultado duas vezes em READ ONLY/RepeatableRead,
sem HTTP, reenvio, autenticação em nome do usuário ou gravação de ação.
A consulta inicial e a final foram preservadas separadamente. Não há tokens,
senhas ou strings de conexão neste relatório.

Comandos/ações realmente executados:

| Comando/ação | Resultado |
| --- | --- |
| git status --short e leitura dos documentos/ponteiro/YAML | Alterações existentes identificadas e preservadas |
| Python via stdin: cópia/hash dos 10 arquivos de entrada | Estáveis durante a cópia |
| Python via stdin: snapshot do SQLite copiado, com WAL | Um evento entregue, um episódio fechado; sem tocar no original |
| node --env-file=apps/api/.env .../read-api.mjs <raiz> | READ ONLY on; incidente/aviso encontrados, revisão ausente |
| Mesmo comando com api-read-only-final.json | Mesmo resultado às 14:10:24,895 |
| uv run ... analyze-saved.py, análise inicial e final | IDs, cobertura, perfis, fingerprint e estados cruzados |
| git diff --check e conferência final de hashes | Sem erro; originais/software preservados |

Reanalisar as cópias já salvas, sem câmera/modelo/HTTP e em saída nova:

```powershell
. ./scripts/activate.ps1
$auditoria = ".local/detector-evolution/directml-physical-audit-abc219f8-b5f5-4e3c-b050-7f895d33311f"
$saida = "$auditoria/analysis-$([guid]::NewGuid())"
uv run --project services/edge --frozen python "$auditoria/analyze-saved.py" --root $auditoria --output $saida --api-file api-read-only-final.json
```

Para nova consulta somente leitura, em arquivo novo, sem escrever revisão:

```powershell
. ./scripts/activate.ps1
$auditoria = ".local/detector-evolution/directml-physical-audit-abc219f8-b5f5-4e3c-b050-7f895d33311f"
$consulta = "api-read-only-$([guid]::NewGuid()).json"
node --env-file=apps/api/.env "$auditoria/read-api.mjs" $auditoria $consulta
```

Nenhuma suíte foi repetida. As 493 verificações Python e 161 API da entrega
anterior não são apresentadas como comandos executados nesta auditoria.

[Intervalos de cobertura](VERIFICACAO_DEMO_DIRECTML_COBERTURA_2026_10_28.csv) ·
[Transições do motor](VERIFICACAO_DEMO_DIRECTML_TRANSICOES_2026_10_28.csv).

## 8. Conclusão e pendências

| Item | Resultado |
| --- | --- |
| Captura, inicialização DirectML, emissão, API e aviso local | **APROVADO** nos registros |
| Fluxo físico completo até revisão humana | **PARCIAL**: revisão comprovadamente ausente |
| Rearme, perfis finais e encerramento | **APROVADO** |
| Critérios operacionais agregados | **REPROVADO**: cobertura de decisão abaixo de 80% |
| Acerto físico/latência humana e confiabilidade geral | **INCONCLUSIVOS**, sem confirmação/marcação independente |

A confiabilidade geral não é comprovada por este ensaio isolado.
As quatro perdas históricas floor03/floor05/floor07/controlled-lying e os
controles inconclusivos intake16-08/cauca-10/cauca-12/chair08-01 continuam
preservados, assim como a cobertura insuficiente de cauca-03, sem nova
avaliação nesta rodada.

**Única próxima ação:** abrir
[este incidente no painel](http://127.0.0.1:3000/incidentes/3f8db408-fbb1-4286-ad75-be8e9a3ce57a)
e salvar uma **Revisão humana** fiel ao que aconteceu, escolhendo o resultado
correspondente e descrevendo a atividade; clicar em **Registrar ação**.
Não é necessário repetir a captura. Salvar a revisão não altera a reprovação
operacional de cobertura nem aprova o detector em geral.
