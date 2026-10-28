# Ensaio físico DirectML — 28/10/2026

Status: **PARCIAL — um exemplo de detecção local observado; ensaio completo não aprovado.**

A sessão executada pelo fundador gerou um evento de **Pessoa no chão**, coerente
com seu relato de permanência de 20–30 segundos no piso. Câmera, percepção e
prévia funcionaram juntas. O envio HTTP estava desabilitado: não foi criado
incidente no painel por esta execução.

O encerramento foi manual aos **56,31 s**, antes dos 60 s previstos. A cobertura
e a instrumentação também apresentam limites descritos abaixo. Não foi aberta
câmera, repetido teste, ajustado parâmetro, enviado evento ou alterado o worker
nesta análise. Não há aceite integral do detector ou do MVP.

## Sessão e procedência

Revisão de partida: `9d149ac165a66865a2d49b7691eb8ab290729032`.
Já havia alterações locais da correção de repetição do runner; foram preservadas.

Diretório privado da prova, obtido de
`.local/detector-evolution/directml-current.json`:
`directml-3041f6a1-15eb-4ed8-aa68-3a371c5ed731`.

Sessão selecionada explicitamente:
`physical-prepared/sessions/8433f5f4-43d3-4e16-814a-600e3639aba9/`.
Relatório original:
`results/540dcfe8-9334-4774-907d-233dcb1b10a8/report.json`.
Originais: relatório, decisions.jsonl, configuração efetiva, session.json,
SQLite e dois arquivos de lock. **Sete arquivos preservados por SHA-256.**
O banco foi consultado com `mode=ro&immutable=1`, sem WAL pendente.

A primeira tentativa `90c91667-7596-4871-aaf9-f8f3b446d71f`, com zero eventos,
continua preservada e separada. A pasta `15803273-...` contém somente a
preparação de conferência da correção, sem captura física. Nenhuma foi
misturada ao resultado atual.

Ambiente identificado na prova anterior: Windows 11 Pro x64 10.0.26200,
Ryzen 5 5625U, 12 processadores lógicos, aproximadamente 15,4 GiB de RAM.
Nesta sessão: webcam índice 0/DSHOW, 640×480, rotação zero; DirectML 1.23.0,
adaptador físico AMD Radeon 1002:15E7/DXGI 0, D3D12 12_1/12_0 aceitos.
Não foi feito novo inventário de driver nesta análise.

Referência mantida: **REFERENCE_4_SPIN + RTMO_ADAPTIVE_V3**, classificador
`signed-body-mlp-v3-dev01`, calibração da webcam versão 3.

| Artefato | SHA-256 conferido |
| --- | --- |
| Pesos ONNX | d0703d40d19f3921da51ae725402d5fdae4d2478c7442072d3101bd396f370d8 |
| Classificador V3 | 40d01401851f24cd8c815557970f0dcf42877707afbba38d521ebfa87bd5bd19 |
| Calibração, representação canônica usada pelo contrato | a53ea803ad2cf1fefee076cc07042713f21e5c036bc331598b712edf7d7f24f1 |

O hash dos bytes do JSON de calibração difere do hash canônico por serialização;
o valor canônico corresponde à configuração. Não houve mudança de polígono.

## Confirmação humana e limites da anotação

O fundador informou:

- Ficou deitado mais de 20 e menos de 30 segundos, aproximadamente com os pés
  voltados para a câmera.
- Piso marcado corretamente e corpo inteiro visível ao deitar.
- Ficou em pé parado antes de deitar e antes de desligar.
- Encerrou o teste manualmente.

Não há marcadores humanos precisos de início/fim da postura nem vídeo gravado.
Portanto, não se calculou latência desde o momento real de deitar, sensibilidade,
precisão anatômica por quadro ou taxa de falsos alertas por atividade.
As classes previstas pelo modelo não substituem essa anotação.

## Detecção, persistência e rearme

A origem da captura foi **11:03:23,598**; o encerramento, aproximadamente
**11:04:19,911**, em America/Sao_Paulo. Originais em UTC foram preservados.

O trace usa um relógio de episódio deslocado em −1.953 ms. Os tempos abaixo
são derivados como `timestampMs - sourceTimestampOffsetMs`, a partir da
origem física de captura. Os registros originais não foram reescritos.

| Marco | Tempo desde a origem da captura |
| --- | ---: |
| Primeiro frame analisado | 3,187 s |
| Primeira classificação LYING, ainda intermitente | 16,312 s |
| Início da sequência contínua de 105 observações LYING | 21,812 s |
| Frame que confirmou o evento | 23,922 s |
| Decisão do evento pronta no host | aproximadamente 24,047 s |
| Última observação dessa sequência LYING | 43,312 s |
| Entrada em REARMING | 43,719 s |
| Rearme concluído, OBSERVING/episódio fechado | 46,781 s |
| Último frame analisado | 55,515 s |

A sequência contínua cobre **21,5 s entre a primeira e a última observação**,
compatível com o relato de 20–30 s no chão. Antes dela houve classificações
incertas e reinícios de suspeita; esse trecho não foi apagado.

Evento local `ae8b3802-06be-47fd-8646-00e9dd6848fe`,
episódio `8f845011-84bd-448d-8f17-f31242386c13`:

- `PERSON_ON_FLOOR`, LIVE; duração de evidência no piso **2.110 ms**,
  fração válida 1,0 e 4,5 análises/s na janela do evento.
- Sem descida rápida observada: não houve evento `POSSIBLE_FALL`.
- Uma emissão no trace, um evento no relatório e uma linha na outbox:
  `PENDING`, zero tentativas, sem ACK ou entrega.
- Nenhuma segunda emissão registrada. Isso comprova a ausência de duplicação
  nesta execução, sem estimar taxa geral de falsos alertas.
- Rede: heartbeat e eventos `NOT_SENT`; zero snapshots e nenhum vídeo salvo.

**2.110 ms é a persistência acumulada pelo detector, não latência humana.**
O critério de evento em até 5 s desde um início humano anotado continua sem
verificação nesta sessão. O relato de ficar em pé não fornece janelas exatas
para aprovar cada controle individualmente.

## Custo, cadência e qualidade observada

| Medida | Amostras | Média / P95 / máximo |
| --- | ---: | ---: |
| Percepção, incluindo as tentativas por análise | 243 | 97,7 / 184,4 / 407,4 ms |
| Processamento total, incluindo prévia | 242 | 119,9 / 245,1 / 523,9 ms |
| Runtime/checkpoint/métricas | 242 | 10,4 / 22,7 / 201,9 ms |
| Prévia | 242 | 10,6 / 17,8 / 57,6 ms |
| Idade do frame na decisão | 243 | 127,5 / 277,9 / 546,0 ms |

P95 calculado por interpolação linear sobre as amostras individuais.
São tempos do aplicativo/host, não tempos exclusivos dos kernels GPU.

243 análises; 4,62 análises/s entre frames analisados e 4,32/s incluindo toda
a sessão, inicialização e encerramento. A prévia registrou 4,64 atualizações
de observação/s. O metadado da câmera de 30 FPS não significa prévia ou
detector a 30 FPS. A meta configurada de análise permanece 5/s.

306 chamadas ao modelo, média 1,26 por análise:

| Caminho | Chamadas | session.run médio |
| --- | ---: | ---: |
| ORIGINAL | 243 | 75,0 ms |
| PERSON_PROPOSAL_CROP | 39 | 75,1 ms |
| ROTATE_180 | 12 | 81,8 ms |
| CENTER_80 | 12 | 75,9 ms |

198 análises fizeram uma chamada; 33 fizeram duas; seis fizeram três e seis
fizeram quatro. Inicialização da sessão ORT: 387,5 ms; sem aquecimento sintético.

Foram adquiridos 1.600 frames e consumidos 244, incluindo o frame de preparação.
1.356 sobrescritas são a política intencional de buffer com apenas o frame mais
recente; não são 1.356 falhas de câmera. Zero reconexões e erro de captura nulo.

Qualidade do estimador: 198 `ONE_VALID_POSE`, 33 `LOW_CONFIDENCE`, 12
`NO_POSE`; oito análises também marcaram pontos fora da imagem.
Na classificação houve 17 `UNKNOWN` e três poses insuficientes.
Esses grupos não são todos mutuamente exclusivos. Ausência de pose não prova
ausência de pessoa, e baixa confiança não prova que o corpo saiu do quadro.

CPU do processo principal: 29,16 s, equivalente a 51,77% de um processador
lógico ou 4,31% normalizado pelos 12. Pico de working set: 393,87 MiB.
Não inclui toda a CPU do processo filho da câmera, memória do driver/GPU,
potência ou temperatura. Não houve braço CPU físico simultâneo para comparação.

## Cobertura no horizonte inteiro e interrupções

Mantidos o auditor temporal existente, intervalo máximo de 500 ms, idade de
decisão até 2.000 ms e referência de cobertura mínima de 80%. Não se recortou
somente o trecho estável ou o trecho no chão para aprovar o ensaio.

| Denominador | Cobertura de decisão elegível | Cobertura de captura tempestiva |
| --- | ---: | ---: |
| 60 s previstos | **70,18%** (42.109 ms) | 84,35% (50.610 ms) |
| 56,31 s efetivamente executados, informativo | **74,78%** | 89,87% |

Nem mesmo usando a duração executada a cobertura de decisão chega a 80%.
O quociente interno 42.109/52.328 = 80,47% exclui início/fim; não é usado como
aceite. Cobertura de captura não substitui cobertura de reconhecimento.

Há uma lacuna entre decisões prontas de **546 ms**, entre aproximadamente
5,094 e 5,640 s do host. Dois intervalos entre frames analisados excedem
500 ms: 532 e 546 ms. As duas interrupções temporais
`HOST_OBSERVATION_GAP` não são a mesma contagem da lacuna entre decisões:
a primeira usa o início da observação, a segunda a decisão final.

Intervalos sem cobertura de decisão elegível no horizonte de 60 s,
em segundos desde a origem física (incluem desconhecimento, início e fim):

| Início | Fim |
| ---: | ---: |
| 0,000 | 7,359 |
| 16,312 | 20,750 |
| 21,172 | 21,609 |
| 43,312 | 43,719 |
| 54,750 | 60,000 |

Não são períodos comprovados de câmera desligada ou de ambiente vazio.
A primeira aquisição analisada veio em 3,187 s; a cauda desde o último frame
analisado até os 60 s é 4,485 s. O auditor FILE retorna cabeça/cauda no relógio
de episódio; esses campos brutos foram preservados na auditoria privada e
não confundidos com tempos físicos LIVE.

## Falhas e limites de observabilidade preservados

1. **Falta o último perfil de processamento.** São 243 decisões e 242 perfis;
   a decisão final, timestamp de episódio 53.562 ms, não tem perfil.
   No LIVE, sair pela prévia quebra o loop antes de emitir esse perfil
   (`services/edge/src/radar_edge/live.py`, bloco após `preview.show`).
   É compatível com o encerramento manual; a tecla específica não foi informada.
   O auditor marca `timingComplete=false` e `timingGate=false`.
   Não se fabricou o perfil nem se excluiu a decisão para passar o critério.
2. **Estados resumidos inconsistentes.** O relatório superior e o trace terminam
   ENDED, mas `source.captureState` e o heartbeat local conservam RUNNING;
   `heartbeat.outboxPending=0` diverge da outbox PENDING=1.
   São snapshots que não devem ser usados como prova do estado final.
   O fluxo chama `source.close()`; esses campos não demonstram câmera reaberta.
3. **Relógio do envelope precisa de cuidado.** O payload salva detectedAt
   14:03:47.937Z, mas a inserção SQLite registra 14:03:47.655Z: diferença de
   +282 ms. A âncora do episódio e o deslocamento aplicado à captura não
   coincidem exatamente. Os valores foram preservados; a análise de idade usa
   o monotônico do host. Não se usa esse UTC como latência humana precisa.
4. **Metadado genérico do modelo ainda diz delegate=CPU.** O campo vem da
   especificação comum do RTMO, enquanto experimentalExecutor registra a
   sessão DirectML. Não é evidência isolada de fallback nem rótulo confiável
   para identificar o executor desta prova.

Nenhuma dessas inconsistências foi corrigida ou ocultada nesta avaliação.

## O que está comprovado sobre a GPU

O relatório desta sessão identifica ORT 1.23.0, DmlExecutionProvider,
adaptador físico AMD 1002:15E7, execução sequencial, memory patterns desligados,
batch=1 e fallback automático de sessão desabilitado, sem erro registrado.

A [prova anterior](VIABILIDADE_RTMO_DIRECTML_2026_10_27.md) contém profiling
dos mesmos pesos e executor: 154 eventos DML e 15 CPU por chamada perfilada,
incluindo computação GPU e auxiliares/NMS na CPU.
Isso sustenta a procedência do executor usado.

**Esta sessão física não coletou profiling por operador do ORT.**
PROCESSING_PROFILE mede etapas do aplicativo; não é atribuição de nós à GPU.
Portanto, não se apresenta a lista de providers como nova comprovação de
execução por operador nesta webcam, nem se afirma haver somente computação GPU.
A atribuição detalhada desta sessão não pode ser recuperada retroativamente.

## Decisão e pendências

| Critério | Resultado |
| --- | --- |
| Câmera, inferência real e prévia juntas | Funcionaram nesta sessão |
| Exemplo de pessoa no chão, orientação próxima aos pés | Um evento local, coerente com o relato |
| Persistência e retorno a OBSERVING | Registrados; um episódio fechado |
| Decisões com idade até 2 s | Nenhuma excedeu; máximo 546 ms |
| 60 segundos completos | Não: encerramento manual em 56,31 s |
| Cobertura de decisão de pelo menos 80% | Não: 70,18% no horizonte previsto |
| Instrumentação completa até a última decisão | Não: falta um perfil |
| Latência desde início humano / controles separados | Inconclusivos, sem marcadores precisos |
| Profiling GPU específico desta execução física | Não coletado; prova anterior separada |
| Entrega e revisão no painel | Não exercitadas; HTTP desligado |
| Precisão anatômica, outras orientações e quatro perdas históricas | Não revalidadas |

Há evidência útil de detecção no cômodo. Não se aprova o teste completo de 60 s
nem o MVP. Permanecem as quatro perdas históricas
`floor03/floor05/floor07/controlled-lying` e controles inconclusivos:
este exemplo positivo não os transforma em acertos.

O próximo trabalho técnico é corrigir o fechamento dos diagnósticos e a
identificação/consistência de metadados e relógios antes de exigir nova
conferência física ou apresentar integração completa como validada.
Entrega ao painel e revisão seriam uma próxima entrega específica; não foram
implementadas, habilitadas ou executadas nesta análise. Não foi solicitado
outro ensaio ao fundador nem houve repetição automática.

## Reprodução da análise, sem câmera

Auditor privado:
`.local/detector-evolution/analyze-directml-physical-2026-10-28.py`.
A análise inicial ficou em `physical-audit-a8d0ed10-10c3-4746-828c-d475a78d9334`;
a análise final, com conferência do hash canônico e relógios, em
`physical-audit-88b49140-6f2d-45f1-bd1a-5c29c204caac`, sob a prova privada.
Incluem summary.json, hashes antes/depois e CSVs derivados, sem nova inferência.

Comandos realmente executados (duas saídas novas, ambas com código zero):

```powershell
. ./scripts/activate.ps1
$prova = (Get-Content .local/detector-evolution/directml-current.json -Raw | ConvertFrom-Json).root
$auditoria = "$prova/physical-audit-$([guid]::NewGuid())"
uv run --project services/edge --frozen python .local/detector-evolution/analyze-directml-physical-2026-10-28.py --report "$prova/physical-prepared/sessions/8433f5f4-43d3-4e16-814a-600e3639aba9/results/540dcfe8-9334-4774-907d-233dcb1b10a8/report.json" --output $auditoria
git diff --check
```

O auditor recusa saída existente, consulta SQLite somente em leitura e confere
hashes dos sete originais antes/depois, pesos, classificador e contexto.
A segunda execução é reanálise dos mesmos dados; não é repetição do ensaio.
A conferência final também verificou o manifesto dos sete arquivos da primeira
tentativa e os vínculos locais dos documentos.

Nesta rodada mudaram apenas documentos e artefatos privados de análise.
Não houve alteração do detector ou ambiente; testes funcionais de modelo não
foram reexecutados como se fossem nova evidência. Os testes da correção de
repetição continuam documentados no [relatório próprio](REPETICAO_WEBCAM_DIRECTML_2026_10_28.md).
Sem commit, push, deploy, envio ao painel ou gravação de mídia pelo assistente.
