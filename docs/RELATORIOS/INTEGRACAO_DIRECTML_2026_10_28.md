# Integração opt-in DirectML — 28/10/2026

**Integração em arquivo comprovada. Demonstração física preparada e pendente.
Percepção permanece experimental; MVP não aprovado integralmente.**

Partida: `9d149ac165a66865a2d49b7691eb8ab290729032`, com alterações locais
preexistentes em STATUS, relatórios e runner de repetição. Elas foram preservadas.
Leitura de AGENTS, README, STATUS, contratos, motor temporal, ambiente,
[ensaio físico](ENSAIO_FISICO_DIRECTML_2026_10_28.md), prova GPU e código pertinente.

Os comandos da demonstração estão no
[roteiro operacional](../USO_DIRECTML_EXPERIMENTAL.md).
Nenhuma webcam foi aberta nesta entrega. Não houve commit, push ou deploy.
A conferência final confirmou por SHA-256 os 14 arquivos brutos das duas
tentativas físicas antigas, os lockfiles e o runner/relatórios locais anteriores.
O next-env.d.ts regenerado pelo typecheck foi restaurado à cópia inicial.
A outbox da demonstração preparada ainda não existe, confirmando que ela não
foi executada.

## Resultado funcional e arquitetura

`model.executor` aceita CPU (padrão) ou DIRECTML explicitamente.
DirectML exige RTMO_ADAPTIVE_V3 + REFERENCE_4_SPIN, os mesmos pesos e
o adaptador AMD verificado. A opção entra na fábrica normal de estimadores;
o mesmo `run_pipeline/run_live` usa classificador, motor temporal, outbox,
autenticação, entrega, heartbeat, recuperação, API e painel existentes.

O ambiente `experiments/directml` continua isolado, com Python 3.12.15,
onnxruntime-directml 1.23.0 e lockfile preservado. O ambiente normal mantém
onnxruntime CPU 1.23.2. Não foram instalados runtimes concorrentes, alterados
drivers, treinados pesos ou trocados modelos.

`scripts/run-edge.py` executa a CLI normal no ambiente selecionado; não usa
o runner curto experimental para habilitar HTTP. Os guards desse runner
continuam exigindo HTTP/snapshots desligados e duração limitada.

DirectML inicializa com execução sequencial, memory patterns desativados,
batch=1, quatro threads intra-op e uma inter-op, conforme os
[requisitos oficiais](https://onnxruntime.ai/docs/execution-providers/DirectML-ExecutionProvider.html).
Falha de ambiente, adaptador ou inicialização gera
`DIRECTML_INITIALIZATION_FAILED`; não há substituição silenciosa por CPU.
Operadores auxiliares na CPU continuam permitidos e identificados no profiling.

Hardware da prova: Windows 11 Pro x64, Ryzen 5 5625U, 12 processadores lógicos,
aproximadamente 15,4 GiB RAM. As sessões reais selecionaram DXGI 0,
AMD Radeon (TM) Graphics, PCI 1002:15E7, D3D12 12_1/12_0.
Não houve novo levantamento/instalação de driver.

## Correções de encerramento e diagnóstico

- LIVE e FILE finalizam o perfil em `finally`, inclusive quando Q/Esc,
  Ctrl+C ou uma falha após a decisão interrompe a prévia. Etapas não concluídas
  ficam sem duração disponível; não se preenchem com medições anteriores.
  As configurações desta entrega habilitam `profileProcessing`.
- A captura é liberada antes do heartbeat final. O resumo posterior lê novamente
  a outbox em conexão somente leitura e informa o total real não entregue,
  inclusive quando HTTP estiver desligado.
- O arquivo privado de status também recebe o estado final, sem manter RUNNING
  por ser apenas a última amostra do loop.
- `stopReason` distingue saída da prévia, controle stop, limite de duração,
  limite de observações e Ctrl+C. Interrupção manual não vira comprovação dos
  60 segundos completos.
- Runtime, versão, providers e adaptador efetivamente inicializados ficam no
  relatório. `delegate` passa a DIRECTML quando apropriado. Inicialização
  DirectML falhada fica `initialized=false`, providers vazios e delegate nulo.
  Novas execuções do runner antigo também recebem identificação correta.
- A limpeza das threads ocorre mesmo quando a consulta final ao banco falhar;
  o erro não transforma uma fila desconhecida em zero pendentes.

Nada disso fabricou o perfil ausente ou corrigiu retroativamente os resumos
das sessões físicas anteriores.

### Causa do detectedAt adiantado

Na sessão antiga, a captura começou em 14:03:23.597878Z, mas a âncora do episódio
foi criada em 14:03:25.968Z. O `max(...)` usado para garantir timestamps
crescentes escolheu deslocamento −1.953 ms, em vez de aproximadamente −2.370 ms.
A combinação adiantou o UTC mapeado em cerca de 417 ms. O evento acabou com
detectedAt 14:03:47.937Z, enquanto a inserção SQLite foi 14:03:47.655Z: +282 ms.

Nas novas execuções LIVE, uma execução nova recebe a origem UTC da captura como
âncora. `created_at` continua sendo o instante real de criação no SQLite.
Amostras usam o tempo monotônico de aquisição; não se deslocam timestamps
artificialmente para ultrapassar o checkpoint. Ao retomar, a âncora antiga e
os envelopes persistidos permanecem intactos. Se o relógio atual não permitir
progressão coerente, a execução falha com `LIVE_CLOCK_INCOHERENT`.

`detectedAt` representa a amostra que confirmou a suspeita; a persistência vem
depois. Não é o início humano de deitar nem, necessariamente, o instante do
commit. Idade antes/depois da decisão, checkpoint, envio e tratamento de
CLOCK_UNCERTAIN/DELAYED continuam protegidos pelos mecanismos existentes.
Nenhum limiar de envelhecimento ou evidência foi aumentado.

## Prova completa sem webcam

Executada pelo Playwright no fluxo existente, com PostgreSQL, API e painel
exclusivos, portas efêmeras e conta sintética. Não se usou banco de demonstração.
Os dados do teste foram descartados com seu container; o comprovante privado
registra o que foi persistido e recuperado antes do descarte.

Configurações foram clonadas dos arquivos autorizados de desenvolvimento,
preservando pixels, polígonos, qualidade, classificador e temporizadores.
Somente a identidade da câmera/calibração foi vinculada à câmera do banco de
teste, com hash canônico correspondente e credencial exclusiva.

| Verificação | Resultado real |
| --- | --- |
| Positivo conhecido intake16-03 | 74 decisões reais; um PERSON_ON_FLOOR em offset 2.000 ms |
| Controle chair08-02 | 32 decisões reais; zero eventos/alertas |
| Modo e classe | REPLAY / TEST |
| Outbox → API | Evento entregue, zero pendentes finais |
| Episódio positivo | Um incidente, um recibo |
| Reenvio do mesmo envelope | HTTP 200, duplicate=true, mesmo incidente, mesmo recibo |
| Aviso local | Uma intenção e uma entrega; sem mensagem externa |
| Revisão via painel | Salva, versão 2, recuperada após recarregar e confirmada no banco |
| Encerramento | Heartbeat ENDED e outboxPending=0 |
| Perfil por decisão | 74/74 no positivo e 32/32 no controle |
| Imagens/vídeo | Nenhum salvo |

Revisão usada no teste:
“REVISÃO AUTOMATIZADA DE TESTE DirectML/REPLAY. Não representa revisão humana do fundador.”
Foi registrada pela conta sintética de teste. Não representa revisão humana do
fundador nem avaliação independente dos vídeos.

Comprovante final:
`.local/directml-integration-e2e/cdcfd1e9-1608-4f6e-960d-09607d68bc89/verification.json`.
Incidente exclusivo do teste: `252e609c-1c3a-49a0-9882-75f050d056e5`.
Esse ID não deve ser procurado no banco de demonstração após o descarte.

### Computação GPU nesta prova

Profiling do ORT habilitado nos dois arquivos, finalizado e lido após fechar
a sessão. O verificador encontrou computação DML, incluindo nós fundidos,
em vez de usar somente a lista de providers.

| Arquivo | Eventos de nós DML | Eventos de nós CPU | Computação GPU comprovada |
| --- | ---: | ---: | --- |
| intake16-03 | 34.188 | 3.330 | Sim |
| chair08-02 | 4.928 | 480 | Sim |

Os auxiliares/NMS e as transferências permanecem no grafo conforme a
[prova anterior](VIABILIDADE_RTMO_DIRECTML_2026_10_27.md). O JSON completo de
profiling está privado junto de cada relatório. Contagens de nós não são FPS
nem tempos exclusivos de kernels. Esta é prova nova em FILE, não profiling
retroativo da sessão física antiga.

Uma primeira tentativa E2E parou no preparador do controle porque um campo
opcional videoSha256 não existia naquele item. O preparador passou a calcular
o hash do arquivo efetivamente usado; logs/resultados dessa tentativa continuam
privados e separados. A prova foi repetida em banco/saídas novos e passou;
a verificação final após as correções também passou.

## Regressão do detector

**72 execuções FILE sequenciais:** CPU de referência e o novo executor
DirectML, alternando a ordem por arquivo, nas mesmas 36 cenas e anotações.
O protocolo foi copiado para diretório novo e os hashes de entrada conferidos.
Não houve webcam, HTTP ou snapshots nessa matriz.

| Resultado | CPU 1.23.2 | DirectML 1.23.0 |
| --- | ---: | ---: |
| Aprovações pelo critério funcional existente | 27/36 | 27/36 |
| Novas regressões de aprovação no DirectML | — | 0 |
| Casos com eventos/decisões semânticas diferentes | — | 0 |
| Alertas indevidos / duplicações no conjunto | 0 / 0 | 0 / 0 |
| Transições injustificadas segundo as anotações existentes | 0 | 0 |

Maior diferença observada nos pontos essenciais: 0,001741 pixel; score:
0,000002921. Não se exigiu igualdade bit a bit. Não houve outlier acima do gate
numérico existente.

As quatro perdas `floor03`, `floor05`, `floor07` e `controlled-lying`
continuam sem evento em ambas as versões. Os controles `intake16-08`,
`cauca-10`, `cauca-12` e `chair08-01` continuam inconclusivos.
`cauca-03` gera evento, mas continua abaixo do aceite de cobertura.
Não foram removidos, retocados, transformados em acertos ou usados para
selecionar outros parâmetros.

Esta regressão é desenvolvimento em FILE, sem comprovação de ritmo real ou
avaliação independente. Não é uma nova comparação de desempenho CPU/GPU.

[Resultados por arquivo](INTEGRACAO_DIRECTML_REGRESSAO_2026_10_28.csv).

Durante a execução foi corrigida apenas a exportação da configuração efetiva:
a primeira parte salvava a base antes da escolha do executor pelo argumento
`--native-worker`. Os envelopes, traces e relatórios de execução, com executor
real, não foram alterados. A invocação congelada identifica CPU/DirectML em todos
os casos; o diagnóstico dessa diferença está em
`regression-config-diagnostic.json`. Não houve mudança perceptual ou de
limiares. Reexecutar o orquestrador no mesmo destino agora é recusado antes
de truncar logs.

## Cobertura da sessão física anterior, sem mudar o critério

O auditor lê somente o relatório e o trace antigos. Foram mantidos 500 ms
para intervalos, 2 s de idade e 80% de cobertura, sem recortar o começo/fim.

| Horizonte | Decisão elegível | Captura tempestiva |
| --- | ---: | ---: |
| 60 s previstos | 42.109 ms / **70,18%** | 50.610 ms / 84,35% |
| 56,3134663 s executados | **74,78%** | 89,87% |

Partição dos **17.891 ms sem cobertura de decisão** nos 60 s, sem contar
intervalos sobrepostos duas vezes:

| Parcela observável nos registros | Duração |
| --- | ---: |
| Inicialização até a aquisição do primeiro frame analisado | 3.187 ms |
| Intervalos com observações sem decisão elegível/tempestiva | 9.876 ms |
| Último intervalo: perfil ausente e observações também inelegíveis | 343 ms |
| Cauda após última aquisição analisada até encerrar | 798,4663 ms |
| Parte dos 60 s não executada após encerramento manual | 3.686,5337 ms |

A inicialização inclui abrir a captura/preparar o runtime; não se atribui todo
esse tempo ao modelo. A cauda inclui o processamento final e a saída: sem
perfil final não é possível separá-los por completo. Os 343 ms não são
atribuídos exclusivamente ao perfil ausente, porque as observações finais
também eram inelegíveis.

Há dois intervalos entre frames acima de 500 ms (532 e 546 ms) e uma lacuna
entre decisões prontas de 546 ms, no início da sessão. Nesse pico, a próxima
análise mediu 311,5 ms de percepção e 200,8 ms na etapa de checkpoint;
processamento total 523,9 ms. São tempos de parede por etapa, não prova de
qual recurso físico causou a espera. Não se conclui que o disco ou a GPU falhou.

Essas lacunas sobrepõem observações inelegíveis e não são somadas de novo à
partição. Nenhuma decisão excedeu 2 s de idade. Classes NO_POSE/UNKNOWN e
baixa confiança são previsões do detector; não indicam que a pessoa saiu do
quadro ou que a cena estava vazia.

**A causa física das perdas de percepção permanece indeterminada onde não há
vídeo ou anotação precisa.** O relato humano é preservado; não há latência
desde início humano mensurável nesta sessão. O numerador interno que daria
80,47% entre frames analisados não foi usado para aprovar.

[Intervalos e atribuição limitada](INTEGRACAO_DIRECTML_COBERTURA_2026_10_28.csv).

## Demonstração física preparada

Configuração nova, em `physical-demo/config.yaml` sob a prova desta entrega;
ponteiro curto `.local/directml-demo-current.json`.

- Webcam 0/DSHOW, mesma calibração versão 3, até o limite de 60 s.
- DIRECTML opt-in, prévia estabilizada e HTTP habilitado.
- Credencial existente `.local/webcam-device.json` conferida em transação
  READ ONLY: ativa e vinculada à WEBCAM correta. Nenhum token exibido/rotacionado,
  heartbeat enviado ou registro de demonstração alterado nessa conferência.
- Sem vídeo/snapshots por padrão; profiling por operador desligado na sessão
  física para evitar esse custo diagnóstico extra. Traces e perfis das etapas
  permanecem habilitados.
- Outbox/resultados novos. Reexecuções usam a recuperação normal; não apagam
  evento pendente nem criam novo episódio artificialmente.

[Comandos de API, painel e worker; sequência segura e revisão](../USO_DIRECTML_EXPERIMENTAL.md).
A configuração e os contextos foram validados sem abrir a fonte.
A credencial de demonstração não foi usada para enviar eventos nesta entrega.

A demonstração precisa comprovar LIVE→evento→incidente→aviso→revisão do fundador,
cobertura, cadência/idade, rearme e encerramento. Um clique ou contagem antes
de caminhar não conta como início da postura. Sem marcadores precisos, latência
humana continua pendente. As limitações de percepção permanecem mesmo que um
exemplo físico funcione.

## Arquivos e verificação reproduzível

Principais alterações: config/estimator/rtmo/directml e inventário de adaptador;
live/pipeline/health; origem temporal em event_runtime/outbox; testes de
encerramento e preservação; launcher, preparadores e auditor; prova Playwright
no painel existente. Sem migração de schema, alteração de pesos, polígonos,
classificador, qualidade, temporizadores, .env ou lockfiles.

Prova privada:
`.local/detector-evolution/directml-integration-757f4105-e1ad-46ca-8efb-995ad297eb3e`.
Inclui snapshot/hashes iniciais, protocolo, 72 resultados, comparação, preparação,
auditoria da sessão e conferência da credencial. Dados pessoais, tokens,
vídeos, SQLite e pesos continuam fora do Git.

| Comando/ação realmente executado | Resultado |
| --- | --- |
| pytest services/edge/tests experiments/directml/tests | 493 passaram; uma GUI física opt-in ignorada |
| pytest do guard de repetição da regressão | Passou, sem truncar log existente |
| Ruff lint/formatação dos módulos, testes e quatro scripts novos | Passaram após correções |
| pnpm.cmd test:api | 161 testes, cinco suítes; banco exclusivo |
| pnpm.cmd test:e2e, somente DirectML/desktop | Uma prova final passou; banco/API/painel exclusivos |
| pnpm.cmd typecheck | Contratos, API e web passaram |
| Builds da API e web pelo executor E2E | Passaram |
| ESLint do teste de painel | Passou |
| run_functional.py --native-worker | 72 execuções, sem erro de execução |
| analyze_functional.py | Mesmos 27/36, sem regressões semânticas |
| audit-live-coverage.py | Mesmos 70,18% e 74,78%; originais intactos |
| Preparador de demonstração | Validou e preparou; cameraOpened=false, httpSent=false |
| Consulta da credencial | VALID, READ ONLY; sem rotação ou alteração do banco |

Comandos da prova e verificações, na raiz:

```powershell
. ./scripts/activate.ps1
uv run --project services/edge --frozen pytest services/edge/tests experiments/directml/tests -q
uv run --project services/edge --frozen ruff check services/edge
uv run --project services/edge --frozen ruff format --check services/edge
pnpm.cmd test:api
pnpm.cmd typecheck
$prova = (Get-Content .local/detector-evolution/directml-current.json -Raw | ConvertFrom-Json).root
$env:RADAR_DIRECTML_PROTOCOL = "$prova/functional-protocol.frozen.json"
pnpm.cmd test:e2e --grep 'DirectML real FILE' --project desktop --output ".local/directml-e2e-results-$([guid]::NewGuid())"
```

O último comando usa arquivos privados já existentes e GPU real; cria banco
exclusivo, nunca abre webcam. No CI sem protocolo/GPU, esse teste opt-in é
ignorado explicitamente, não apresentado como prova de GPU.

Para repetir a regressão, use **um destino novo**:

```powershell
. ./scripts/activate.ps1
$prova = (Get-Content .local/detector-evolution/directml-current.json -Raw | ConvertFrom-Json).root
$novo = ".local/directml-regression-$([guid]::NewGuid())"
New-Item -ItemType Directory -Path $novo | Out-Null
$protocolo = Get-Content "$prova/functional-protocol.frozen.json" -Raw | ConvertFrom-Json
$protocolo.outputRoot = $novo
$protocolo | ConvertTo-Json -Depth 30 | Set-Content "$novo/functional-protocol.frozen.json" -Encoding UTF8
uv run --project services/edge --frozen python experiments/directml/run_functional.py --protocol "$novo/functional-protocol.frozen.json" --native-worker
uv run --project services/edge --frozen python experiments/directml/analyze_functional.py --root $novo
```

O carregador aceita UTF-8 com ou sem BOM, incluindo a saída do Windows
PowerShell 5.1. As saídas existentes não podem ser reutilizadas.

## Decisão

A opção GPU está integrada e o percurso funcional em FILE foi comprovado até
revisão persistida no painel. CPU continua padrão. A demonstração física
completa está somente preparada, sem captura automática nesta entrega.
A confiabilidade de detecção continua não comprovada para uso geral:
quatro perdas, controles inconclusivos e cobertura física insuficiente foram
mantidos, sem aprovação integral do MVP.
