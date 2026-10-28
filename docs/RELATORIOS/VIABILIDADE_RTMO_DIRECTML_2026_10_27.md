# Viabilidade do RTMO na GPU existente — 27/10/2026

## Objetivo e estado

Uma prova de executor para **REFERENCE_4_SPIN + RTMO_ADAPTIVE_V3**:
preservar reconhecimento e reduzir o custo da percepção. **Aceleração útil demonstrada**, preservada como opt-in experimental;
reconhecimento conhecido equivalente, sem promoção do padrão ou aprovação do MVP.
Nenhuma webcam aberta nesta rodada.

Partida: `58a1cab58d7bf982f2ca8af078d0e5ca50773635`, árvore limpa.
Leitura de AGENTS, README, STATUS, relatórios atuais de percepção e transmissão,
RTMO, criação de estimador, pipeline, LIVE e aceite temporal.
Cópia inicial de fontes e hashes em diretório privado novo.
Todos os arquivos desta prova são **desenvolvimento**, sem avaliação independente.

Referência preservada: mesmos bytes ONNX, classificador corporal V3,
pré/pós-processamento, coordenadas, recuperações, limiares, contexto,
amostragem e temporizadores. Nenhum treino, quantização ou conversão da rede.
A troca fica em `experiments/directml/`, sem modificar o worker normal.

## Hardware e compatibilidade efetivos

| Item | Verificado |
| --- | --- |
| Sistema | Windows 11 Pro x64, 10.0.26200 |
| CPU | AMD Ryzen 5 5625U, 6 núcleos / 12 processadores lógicos |
| RAM visível | 16.153.144 KiB, aproximadamente 15,4 GiB |
| Adaptador físico DXGI 0 | AMD Radeon (TM) Graphics, PCI 1002:15E7, revisão C2 |
| Driver | 31.0.21925.1001; data WMI 20/05/2026 UTC |
| DirectX / driver model | DirectX 12, DDI 12, WDDM 3.1, pelo DxDiag |
| Consulta nativa D3D12 | Feature levels 12_1 e 12_0 aceitos; 12_2 não suportado |
| Memória DXGI | 519.634.944 bytes dedicados e 8.270.409.728 compartilháveis |
| Segundo adaptador | Microsoft Basic Render Driver, software; rejeitado |
| Python experimental | CPython 3.12.15 x64 |
| Executor | onnxruntime-directml 1.23.0, DLL DirectML 1.15.4 |
| NumPy / OpenCV / ONNX | 2.5.4 / opencv-contrib-python 5.0.0.93 / 1.19.1 |

WMI, DxDiag e chamadas DXGI/D3D12 foram usados em modo de consulta.
Não houve instalação de driver, mudança global, de energia, firewall ou permissões.
Os limites de memória acima são capacidades declaradas, não consumo medido da GPU.
O nome comercial não foi inferido como “Vega” a partir da família Radeon.

A documentação oficial exige GPU compatível com DirectX 12 e, na sessão DirectML,
execução sequencial e memory patterns desativados. Aplicados
`ORT_SEQUENTIAL`, `enable_mem_pattern=False` e dimensão de sessão
`batch=1`; quatro threads intra-op e uma inter-op preservadas.
Não há chamadas Run concorrentes na mesma sessão.
A seleção `device_id=0` corresponde à enumeração DXGI verificada.
[Requisitos e opções oficiais do DirectML](https://onnxruntime.ai/docs/execution-providers/DirectML-ExecutionProvider.html).

O pacote DirectML não oferece a versão 1.23.2 usada pela referência CPU.
Foi escolhida 1.23.0, na mesma família e com wheel CPython 3.12/Windows x64;
não houve varredura de versões. Por isso há **três braços**:
CPU de referência 1.23.2, CPU comparável 1.23.0 e DirectML 1.23.0.
Nos dois últimos, opções de sessão são iguais. Cada ambiente contém uma única
distribuição ONNX Runtime e uma única distribuição que fornece cv2.
[Distribuição usada](https://pypi.org/project/onnxruntime-directml/1.23.0/).

Ambiente novo com `pyproject.toml`, `uv.lock`, `.python-version` e `.venv` própria.
O ambiente normal e `.local/pose-env-965d2e5d` continuam intactos.

## Modelo e execução efetiva

ONNX verificado com `onnx.checker`: IR 6, opset ai.onnx 11, 729 nós,
entrada float32 `[batch,3,640,640]`; saídas float32 dets/keypoints.
Inicializadores: 192 FLOAT e oito INT64. Nenhuma reescrita do arquivo.
O inventário completo dos operadores permanece privado.

- Pesos SHA-256: `d0703d40d19f3921da51ae725402d5fdae4d2478c7442072d3101bd396f370d8`.
- Classificador SHA-256: `40d01401851f24cd8c815557970f0dcf42877707afbba38d521ebfa87bd5bd19`.

A compatibilidade não foi deduzida somente do opset ou da lista de providers:
o grafo foi carregado e executado sobre pixels reais e os operadores foram
atribuídos por profiling ORT. Fallback automático de sessão foi desativado;
uma sessão que caia integralmente em CPU é rejeitada.

No primeiro profiling de uma passagem real:

- **154 eventos de operador em DmlExecutionProvider**, incluindo sete partições
  DmlFusedNode, MatMul/FusedMatMul, operações geométricas e tensoriais.
- **15 em CPUExecutionProvider**: NMS, Gather, Unsqueeze, Concat, Mul, Less,
  Where e Reshape. É execução híbrida, com computação efetiva na GPU.
- Duas MemcpyToHost e duas MemcpyFromHost explícitas por chamada.

Um segundo profiling cobriu os quatro casos, com três aquecimentos sintéticos
e nove chamadas reais: 1.848 eventos DML e 180 CPU. Foram 24 cópias para host e
24 para device; 904.946 µs acumulados nas regiões de cópia da timeline do host.
Esse número **inclui esperas/sincronização** e não mede isoladamente o custo
físico do barramento. Não houve eventos fence explícitos nesse JSON; isso
não significa ausência de sincronização.

O perfil mostra sete partições fundidas, não expõe individualmente todos os
operadores internos de cada partição nem timestamps exclusivos do hardware GPU.
Assim, não se atribui automaticamente cada um dos 80 Conv do ONNX a um evento
individual. A origem DML dos blocos computacionais e das multiplicações foi
comprovada. [Formato e uso do profiling ORT](https://onnxruntime.ai/docs/performance/tune-performance/profiling-tools.html).

A cronometragem envolve `session.run` síncrono com saídas NumPy na CPU.
Na prova pequena há ainda cópia CPU explícita antes de encerrar o tempo;
hashes e persistência dos arrays ocorrem depois. Na transmissão, o decode
original consome as saídas antes da decisão. Não se mediu somente o envio
assíncrono. O tempo da sessão inclui inferência, transferências e os operadores
internos em CPU; o perfil de host não permite separar tempo puro de GPU de
todas as esperas.

## Prova pequena e gate congelado

Quatro PNGs já existentes, autorizados, sem abrir fonte física:

| Frame | Cenário | Caminhos/chamadas | Resultado |
| --- | --- | --- | --- |
| F01 | yoga2-01, passagem original | ORIGINAL / 1 | LYING, elegível |
| F09 | intake16-03, recuperação cara | ORIGINAL, recorte de proposta, rotação 270° / 3 | LYING, elegível |
| F12 | intake16-07, cadeira | ORIGINAL / 1 | SEATED, sem candidato de chão |
| F04 | intake16-15, vazio | ORIGINAL, recorte de proposta, 180°, CENTER_80 / 4 | Sem pose; não comprova vazio |

Cinco rodadas, três executores e quatro casos: **60 análises reais**.
Três chamadas sintéticas de aquecimento por processo; nenhum frame real usado
para aquecer. Ordem de executores alternada e ordem de casos invertida nas
rodadas pares. Uma única medição nativa ativa por vez.

Antes da comparação foram fixados: nenhuma mudança de aceitação/caminho/postura,
mesmos hashes dos tensores de entrada por passagem, investigação para diferença
acima de 0,5 pixel em caixa, um pixel em ponto ou 0,005 em score. Para avançar:
GPU com média menor nos quatro casos, redução agregada de pelo menos 15% contra
CPU comparável, P95 sem piora e computação GPU comprovada. Esses valores julgam
o experimento; não alteram limiares do detector.

Resultado: **24,15% menos processamento agregado**, gate atendido.
A cadeira teve ganho médio pequeno, 1,70%, e duas das cinco comparações pareadas
foram mais lentas na GPU. Os outros casos tiveram ganho médio de 23–28%.
As rodadas finais variaram em ambos os executores. Temperatura, frequência,
potência e carga externa de GPU não foram medidas; não se atribui a variação
a uma causa não observada.

Caixas, pontos, scores nativos e do classificador foram comparados.
Maior diferença corporal observada: 0,000267 pixel; maior diferença de score
nativo: 0,000000775. Nenhuma mudança de aceitação ou tensor de entrada.
Isso comprova equivalência nesta amostra, não exatidão anatômica.

[Tempos dos 12 grupos de quadro/executor, inicialização e aquecimento](VIABILIDADE_RTMO_DIRECTML_MICRO_2026_10_27.csv).

Inicialização e aquecimento não foram embutidos como inferência estável.
No primeiro profiling, carregamento de sessão levou 2.727,6 ms e primeira
análise real sem aquecimento 368,5 ms. Na primeira rodada de tempos, inicializações
CPU 1.23.2 / CPU 1.23.0 / DML foram 189,5 / 207,1 / 395,6 ms; primeiras chamadas
sintéticas 136,4 / 114,7 / 222,8 ms. Não se limpararam caches do driver.
As chamadas seguintes e cada lote estão registrados separadamente.

## Transmissão técnica a 1×

Foi reutilizado `scripts/validation/benchmark-stream.py` e seu fluxo LIVE sobre
`PacedFileSource`: mesmo buffer de último frame, relógio do host, agendamento,
qualidade, classificador e motor. FILE/REPLAY/TEST, nunca webcam.
Cada execução tem outbox e diagnósticos novos, sem HTTP ou snapshot.

Três repetições sequenciais em ordem alternada, três executores e cinco cenas:
**45 transmissões completas**. Mesmos quatro cenários da rodada anterior mais
o controle da cadeira. Os arquivos “yoga2” são os recortes de 25,025 s e 16 s
já usados naquela comparação, não novos ensaios dos programas longos de yoga.
A recuperação cara tem 14,72 s; vazio 7,76 s; cadeira aproximadamente 5,8 s.

Critérios preservados: duração completa como denominador, lacuna de 500 ms
para contar cobertura, idade final da decisão até 2 s, cobertura mínima 80%,
evento positivo até 5 s do início anotado, ausência de duplicação e alerta
indevido. Cabeça/cauda não observadas são publicadas; completar EOF não aprova
tempo real. No vazio usa-se cobertura de captura conforme a avaliação anterior,
sem transformar ausência de pose em certeza de cômodo vazio.

**GPU: 15/15 aprovações técnicas; cada braço CPU: 11/15.**
Todos produziram um evento nos três alvos e zero nos dois controles.
A CPU falhou por custo/cobertura/latência, não por ausência total de evento:
no alvo caro, uma referência CPU demorou 7.844 ms e a CPU comparável 5.953 ms;
GPU ficou entre 2.391 e 2.593 ms.

Médias/P95/máximos abaixo são agrupados pelas análises de três execuções,
sem calcular “média de P95”. O processamento total vai até a etapa de prévia
(desabilitada); a escrita do próprio perfil é registrada separadamente.
Idade/cobertura usam as decisões finais e o relógio do host.

| Cenário | Executor | Média / P95 / máximo (ms) | Aprovações |
| --- | --- | --- | --- |
| yoga2-01 | cpu-reference | 146.7 / 177.7 / 321.0 | 3/3 |
| yoga2-02 | cpu-reference | 191.3 / 392.6 / 465.7 | 3/3 |
| intake16-03 | cpu-reference | 431.8 / 502.8 / 743.7 | 2/3 |
| intake16-15 | cpu-reference | 574.1 / 627.9 / 642.8 | 0/3 |
| intake16-07 | cpu-reference | 162.6 / 224.8 / 318.6 | 3/3 |
| yoga2-01 | cpu-matched | 148.6 / 183.7 / 528.1 | 3/3 |
| yoga2-02 | cpu-matched | 197.8 / 411.8 / 505.0 | 3/3 |
| intake16-03 | cpu-matched | 438.3 / 526.0 / 653.1 | 2/3 |
| intake16-15 | cpu-matched | 576.7 / 643.3 / 701.8 | 0/3 |
| intake16-07 | cpu-matched | 164.1 / 261.8 / 455.9 | 3/3 |
| yoga2-01 | directml | 100.3 / 141.2 / 207.0 | 3/3 |
| yoga2-02 | directml | 146.4 / 301.7 / 619.1 | 3/3 |
| intake16-03 | directml | 310.7 / 377.8 / 510.3 | 3/3 |
| intake16-15 | directml | 421.5 / 492.6 / 557.8 | 3/3 |
| intake16-07 | directml | 111.4 / 188.7 / 302.7 | 3/3 |

Contra CPU na mesma versão, a redução média foi de 26–33% nos cinco cenários.
As chamadas não foram cortadas: original 1, alvo caro 3, vazio 4 por análise;
cadeira cerca de 1,05 e yoga2-02 cerca de 1,47 na GPU, conforme os frames
efetivamente amostrados. A aceleração permitiu analisar mais frames; por isso
os totais de chamadas de uma transmissão podem ser maiores.

A pior cobertura GPU foi 99,87% em yoga2-01, 94,50% em yoga2-02,
96,20% no alvo caro, 81,44% de captura no vazio e 99,39% na cadeira.
No vazio a elegibilidade de pose continua zero. Há margem pequena no controle
vazio: não é garantia de estabilidade prolongada.

A GPU ainda teve três lacunas de decisão acima de 500 ms no total:
uma em yoga2-02 e duas no vazio. O máximo de processamento de yoga2-02 foi
619,1 ms, maior que os 465,7 ms da referência CPU, apesar de média/P95 menores.
Nenhuma decisão ultrapassou 2 s ou teve relógio ausente/idade inicial negativa.
Não se eliminam esses picos da comparação.

[Todas as 45 execuções](VIABILIDADE_RTMO_DIRECTML_STREAMS_2026_10_27.csv) ·
[15 agregados: cadência, idades, fases, chamadas por caminho, CPU e memória](VIABILIDADE_RTMO_DIRECTML_AGREGADOS_2026_10_27.csv) ·
[124 intervalos sem cobertura, com início/fim na mídia](VIABILIDADE_RTMO_DIRECTML_LACUNAS_2026_10_27.csv).
As somas dos intervalos foram conferidas contra o avaliador original nos 45 streams.
Os períodos sem elegibilidade não são afirmações de ausência de pessoa.

Consumo médio normalizado pelos 12 processadores lógicos: CPU de referência
26–35% da máquina; GPU 6–11%. Pico de working set do processo: aproximadamente
245–279 MiB na CPU e 423–448 MiB na GPU. São medidas do processo, incluindo
setup, aquecimento, decode, logs e espera. Não medem toda a VRAM, driver,
consumo energético ou carga de outros aplicativos. Ganho médio não implica
cinco análises por segundo em todas as recuperações.

## Regressão, preservação e decisão final

**Decisão: aceleração útil, mantida como opção experimental.** A referência
normal permanece em CPU. Não houve fallback integral, perda funcional nova
ou redução de qualidade para produzir os ganhos medidos.

Regressão completa existente, CPU 1.23.2 × GPU 1.23.0: **72 execuções FILE,
36 pares**, sem ritmo real. Aprovação com duração completa: **27/36 em ambos**.
Mesmos timestamps analisados nos 36 pares, mesmos tipos/offsets dos eventos,
posturas, elegibilidade, critérios, caminhos de recuperação e estados temporais.
Os valores contínuos foram julgados separadamente: maior diferença dos
essenciais foi 0,001741 pixel e dos scores 0,000002921; nenhum caso excedeu
as tolerâncias congeladas. Scores do classificador nos quatro quadros diferiram
no máximo em 0,000000024.

**Nove resultados continuam sem aprovação, nos dois executores:**

| Caso | Resultado preservado |
| --- | --- |
| floor03, floor05, floor07, controlled-lying | Quatro alvos sem evento |
| intake16-08 | Controle inconclusivo; cobertura 77,10% |
| cauca-03 | Evento em 2,2 s, mas cobertura 79,23% |
| cauca-10 | Controle inconclusivo; cobertura 64,38% |
| cauca-12 | Controle inconclusivo; cobertura 79,69% |
| chair08-01 | Controle inconclusivo; cobertura 64,42% |

As perdas não foram excluídas da matriz. Nenhum novo alerta indevido,
duplicação ou reprovação introduzida pela GPU nesta regressão.
Classificar um evento como POSSIBLE_FALL em um arquivo já conhecido não
comprova acidente real ou necessidade de socorro.
[36 comparações funcionais](VIABILIDADE_RTMO_DIRECTML_REGRESSAO_2026_10_27.csv).

**479 testes Python passaram; uma GUI física opt-in foi ignorada.**
Cobrem opções de sessão, rejeição de provider ausente/fallback integral,
distribuições concorrentes, saída CPU, perfil sem computação GPU,
comparação numérica, restauração da fábrica, guards do futuro teste físico
e a suíte existente de recuperação/coordenadas/contratos/motor/continuidade.
Lint normal do worker, lint do experimento e formatação passaram.
Nenhum teste automatizado é apresentado como validação de câmera física.

Respostas finais:

1. **Hardware compatível:** sim, por DXGI/D3D12, driver inventariado e execução real.
2. **GPU usada:** sim, comprovada no grafo; NMS e auxiliares continuam na CPU.
3. **Ganho suficiente nos cenários técnicos:** sim, 15/15 no gate de cobertura/
   idade/latência, com redução média de 26–33% contra CPU na mesma versão.
   Há picos e pouca margem no vazio; não é garantia prolongada nem de 5 Hz.
4. **Reconhecimento conhecido preservado:** sim, na amostra numérica e nos
   36 arquivos; a qualidade anatômica anterior e quatro perdas continuam.
5. **Decisão:** aceleração útil opt-in; nenhuma troca do padrão.
6. **Fundamento para teste físico curto:** sim. Somente preparado, não executado.

Uma passagem GPU ficou em cerca de 89–100 ms na transmissão; a recuperação
com três/quatro chamadas ainda consome aproximadamente 311/422 ms completos.
O limite restante está principalmente no trabalho de recuperação e nos picos,
além das falhas perceptuais conhecidas; esta rodada encerra a hipótese GPU,
sem iniciar outra busca de modelo/executor.

Foi preparada uma configuração separada de **60 s**, derivada de
`.local/detector-evolution/candidate-orientation/webcam-controlled.yaml`:
`physical-prepared/webcam-directml-60s.yaml`, dentro do diretório privado da prova.
Mantém câmera, calibração, classificador, qualidade e temporizadores da referência;
usa outbox/diagnósticos novos, HTTP/snapshots desligados e prévia em movimento.
O arquivo base não foi alterado. O plano registra hashes e exige conferir se
o enquadramento continua correspondente ao piso antes de uma execução futura.

O runner `experiments/directml/worker.py` só aceita referência V3 autorizada,
duração até 120 s, outbox inexistente e entrega/imagem desligadas.
Foi verificada a configuração e testados seus guards; **o runner não foi
executado nesta rodada**. O futuro teste precisa medir câmera + GPU + prévia
juntas e não pode ser aprovado antecipadamente pelos resultados FILE.
Nem mesmo um teste físico favorável apagará as falhas históricas ou aprovará
integralmente o MVP.


## Implementação e reprodução

Código novo em `experiments/directml/`:

- Inventário Windows/DXGI/ONNX e fábrica de sessão isolada, com rejeição de
  adaptador software, versão diferente e distribuições ORT concorrentes.
- Prova dos mesmos pixels, exportação privada das saídas e comparador
  numérico/comportamental. Profiling separado dos tempos.
- Conexão por contexto de processo ao executor existente, com restauração
  da classe original mesmo após exceção. Nenhuma edição no RTMO normal.
- Orquestradores sequenciais, auditoria de duração completa e regressão FILE.
- Testes sem hardware das fronteiras de sessão, fallback, materialização CPU,
  análise do perfil, comparação de pontos e isolamento do worker.

Diretório privado desta execução:
`.local/detector-evolution/directml-3041f6a1-15eb-4ed8-aa68-3a371c5ed731/`.
Contém protocolos congelados, hashes, inventários, logs, perfis ORT, saídas
NumPy, outboxes novas e relatórios. O DxDiag bruto permanece privado.
O ponteiro é `.local/detector-evolution/directml-current.json`.

Preparação e comandos efetivamente executados, na raiz:

```powershell
. ./scripts/activate.ps1
uv lock --project experiments/directml
uv sync --project experiments/directml --frozen
uv run --project experiments/directml --frozen python experiments/directml/audit.py --model .local/models/rtmo_s_body7_640.onnx --output .local/detector-evolution/directml-3041f6a1-15eb-4ed8-aa68-3a371c5ed731/hardware-model-audit.json
```

Além do inventário, foram executados consultas CIM, DxDiag oculto e consulta
nativa DXGI/D3D12, o probe de placement e o preparador privado do protocolo
pequeno. O runner privado executou `probe.py` com os três backends na ordem
congelada, cinco vezes. Cada comando e seus resultados estão nos logs
`micro-rN-BACKEND.log` e `result.json`.

As etapas seguintes efetivamente executadas:

```powershell
$prova = (Get-Content .local/detector-evolution/directml-current.json -Raw | ConvertFrom-Json).root
uv run --project experiments/directml --frozen python experiments/directml/analyze.py --root $prova
uv run --project experiments/directml --frozen python experiments/directml/run_streams.py --protocol "$prova/stream-protocol.frozen.json"
uv run --project experiments/directml --frozen python experiments/directml/analyze_streams.py --root $prova
uv run --project experiments/directml --frozen python experiments/directml/probe.py --protocol "$prova/micro-protocol.frozen.json" --backend directml --output "$prova/profile-four-cases" --profile
uv run --project experiments/directml --frozen python experiments/directml/run_functional.py --protocol "$prova/functional-protocol.frozen.json"
```

Esses comandos de medição recusam sobrescrever saídas. Para repetir, use um
diretório novo e o procedimento em [experiments/directml/README.md](../../experiments/directml/README.md).
Os comparadores somente reavaliam registros existentes.

Ocorrências de implementação: preparador privado inicial usou o nome inexistente
`calibration.path`; corrigido para `calibrationPath` antes de iniciar qualquer
stream. Ruff encontrou importações após bootstrap, linhas longas e zip sem
strict explícito; corrigidos. As falhas de comando não foram resultados
negativos de GPU nem foram apagadas para atribuir aprovação ao modelo.

Checagens finais realmente executadas:

```powershell
uv run --project experiments/directml --frozen python experiments/directml/analyze_functional.py --root $prova
uv run --project experiments/directml --frozen python experiments/directml/coverage.py --root $prova
uv run --project services/edge --frozen pytest services/edge/tests experiments/directml/tests -q
pnpm.cmd lint:edge
uv run --project services/edge --frozen ruff check services/edge
uv run --project services/edge --frozen ruff check --config services/edge/pyproject.toml experiments/directml
uv run --project services/edge --frozen ruff format --check --config services/edge/pyproject.toml experiments/directml
```

Também executados `uv lock --project experiments/directml --check`
e `git diff --check`, ambos aprovados.

Resultados: análise sem regressões de evento/decisão, 479 aprovados + uma GUI
ignorada, lint e formatação aprovados. Uma execução adicional de Ruff com
`--config` explícito aplicado também ao worker classificou os imports a partir
da raiz errada e apontou 44 ordenações. A descoberta normal de configuração
do worker passou sem editar esses arquivos.

Inventário/prova pequena/perfis/streams/regressões completaram sem falha de
provider ou inferência. Os preparadores privados congelaram protocolos e
geraram a configuração física **sem abri-la**. Os comparadores e exportadores
somente leram os dados medidos. Código, configs, pesos e classificador foram
conferidos contra os hashes preservados. Foram conferidos 100 insumos originais;
nenhum código/lockfile do worker normal mudou. As únicas alterações em arquivos
anteriores são adições em README, STATUS, índice de relatórios e D61.
HEAD permaneceu 58a1cab, sem commit. Cópia final e hashes em
`final-source.zip`, `final-source-identity.json` e `preservation.json` privados.

Somente para uma futura execução física explicitamente solicitada, depois de
conferir o enquadramento e o piso; **não executado nesta rodada**:

```powershell
. ./scripts/activate.ps1
$prova = (Get-Content .local/detector-evolution/directml-current.json -Raw | ConvertFrom-Json).root
uv run --project experiments/directml --frozen python experiments/directml/worker.py --config "$prova/physical-prepared/webcam-directml-60s.yaml"
```

Esse último comando abre a câmera por até 60 s e cria somente dados privados
locais; não registra vídeo nem entrega incidentes ao painel. O objetivo futuro
é medir disponibilidade/custo com a fonte física, sem provocar queda.
A câmera permanece fechada durante toda a prova relatada aqui.


Nenhuma instalação de driver, câmera aberta, alteração de polígonos, pesos,
banco ou credenciais; nenhum commit, push, deploy ou aprovação integral do MVP.
