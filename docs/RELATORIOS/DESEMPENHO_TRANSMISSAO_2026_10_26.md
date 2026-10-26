# Processamento de transmissão — 26/10/2026

**Rodada de investigação executada; gargalo não resolvido. Referência preservada.**
Nenhuma webcam foi aberta. As duas opções de execução comparadas não demonstraram
ganho consistente de desempenho e reconhecimento. O núcleo continua experimental,
sem aprovação do MVP ou solicitação de outro ensaio físico nesta rodada.

## Objetivo e referência

Investigar a fragmentação temporal comprovada no
[ensaio físico](ENSAIO_WEBCAM_ORIENTACAO_2026_10_26.md), sem mudar seus resultados,
pesos, pisos, qualidade, cobertura mínima, permanência de 2000 ms ou lacuna máxima
de 500 ms. Não houve treinamento nem mudança de dependências.

Antes das alterações, foram preservados os 200 arquivos de código, incluindo
alterações locais, diff e inventário. Referência: HEAD
`eaa845a060db680d679b4563a42a984e3fcc05d2`, fonte
`4fab1f96dc5d29d71d9210e4c956143bcdbeda36a7ed583609d89e8b4b36f7f5`.
ZIP privado SHA-256
`020fe75187a228175769b59d1928588e53703d9aff534f4857f0e517c4b12722`.
A referência desta rodada já contém `RTMO_ADAPTIVE_V3`; não confundir com o
`RTMO_ADAPTIVE_V2` usado como referência na rodada anterior de orientação.

Raiz privada: `.local/detector-evolution/throughput-03f3c29b-a314-4f7a-a1f5-c02ad31d2ccd/`;
ponteiro `throughput-current.json`. `protocol.json` registra configuração,
SHA-256 de cada vídeo, calibração, pesos e classificador antes da comparação.
RTMO: `d0703d40d19f3921da51ae725402d5fdae4d2478c7442072d3101bd396f370d8`;
classificador V3: `40d01401851f24cd8c815557970f0dcf42877707afbba38d521ebfa87bd5bd19`.
Fonte medida: `5e52ef7041f359c44cc98997b471eed9209f8df32c2c6e7d43288ceb4738ebe9`
(203 arquivos). O snapshot dessa fonte foi reconstituído revertendo apenas edições
posteriores em testes e validado pelo mesmo SHA-256, sem reverter o workspace;
`measured-source-reconstructed.zip` e o procedimento ficam na raiz privada.
Fonte final de 204 arquivos, com ajustes nos testes:
`ec9f8e7559d58ceacba62cf50f27c34b7514e4d60104e91e155c4f9882602468`;
ZIP `0e8e373829de9440f94503038531e5038c47ee74402c45bfb565285b33b3705c`.
O código executável de inferência/agendamento permaneceu igual ao medido.

## Ambiente e procedimento

Windows 11 Pro 10.0.26200; Ryzen 5 5625U, 6 núcleos/12 processadores lógicos,
15,4 GiB de RAM. Python 3.12.15, uv 0.13.4, ONNX Runtime 1.23.2 CPU,
NumPy 2.5.4, OpenCV contrib 5.0.0.93; Node 24.22.1 e pnpm 10.34.7.
Nenhum equipamento foi comprado ou alterado. Temperatura e frequência efetiva
da CPU não foram medidas; não atribuir a elas a variação observada.

Foram 36 transmissões técnicas: quatro arquivos × três perfis × três repetições,
sequenciais, alternando a ordem dos perfis por caso/rodada. Houve mais três
execuções exploratórias do arquivo da sala com prévia ligada, uma por perfil.
Um smoke anterior e um microperfil de quatro frames por arquivo foram preservados
separadamente; não entram no denominador das 36 comparações principais.

Cada processo carrega o mesmo modelo e executa uma inferência real de aquecimento
em imagem cinza sintética, excluída do relógio e das observações. Não há repetição
de frames reais para aquecer ou fabricar evidência. O produtor começa depois disso,
publica a 1× pelos timestamps do arquivo, com um único slot substituível. A análise
usa o mesmo laço de agendamento, qualidade, recuperação, classificação, decisão e
SQLite de LIVE; quando fica lenta, perde frames intermediários, sem alongar o vídeo.

`PacedFileSource` usa FFmpeg e uma thread de decodificação, sem dispositivo físico.
Webcam usa outro produtor/processo: esta reprodução técnica não mede driver,
sensor ou captura física. Os relatórios e observações dizem `REPLAY` e
`TECHNICAL_PACED_FILE_NOT_WEBCAM`; eventos são TEST, em filas novas, sem HTTP,
credencial, snapshot, escrita de status da câmera ou envio à demonstração.

Os quatro arquivos são desenvolvimento/regressão, já conhecidos: os dois de yoga,
`intake16-03` com recuperação cara e `intake16-15` vazio. Não são avaliação reservada
nem prova de generalização. Nenhum contorno foi redesenhado.

Arquivos principais: `paced_file.py` implementa o produtor; `live.py` compartilha
o laço real e mede fases; `rtmo.py` separa custos e oferece os perfis opt-in;
`config.py`, `estimator.py` e `pipeline.py` propagam a opção; `event_runtime.py`
isola a identidade dos episódios e mede decisão/persistência; `decision_trace.py`
usa as mesmas cotas/retenção para o perfil adicional. Novos testes cobrem ritmo,
sobrescrita, frame único, erro de decoder, bloqueio de webcam/HTTP e identidade.

## Hipóteses comparadas

| Perfil | Alteração isolada |
| --- | --- |
| REFERENCE_4_SPIN | Referência: quatro threads intra-op, espera ativa padrão |
| CPU_2_SPIN | H1: duas threads intra-op, mantendo espera ativa |
| CPU_4_SLEEP | H2: quatro threads, desabilitando espera ativa |

Inter-op permanece em uma thread e a execução sequencial padrão foi preservada.
As opções foram fundamentadas na
[documentação oficial de threads do ONNX Runtime](https://onnxruntime.ai/docs/performance/tune-performance/threading.html).
Somente chaves suportadas pela versão instalada foram usadas. O microperfil também
mediu `CPU_2_SLEEP` após as duas opções isoladas: média 612,203 ms contra 383,678 ms
da referência, nos mesmos 16 frames, com contagens de pose iguais. Não foi promovido
nem incluído na matriz principal, pois as opções isoladas já não sustentavam ganho.

## Desempenho e reconhecimento por cenário

Mediana das três execuções sem prévia; lacunas e cobertura mostram os três
resultados individuais, sem esconder variação. Latência é desde o início anotado
do clipe de pessoa já no chão, não desde a primeira pose aceita.

| Caso | Perfil | Análises/s | Processamento médio / P95 (ms) | Lacunas >500 ms (3 execuções) | Cobertura % (3 execuções) | Eventos / execuções |
| --- | --- | ---: | ---: | --- | --- | ---: |
| yoga2-01 | REFERENCE_4_SPIN | 4.802 | 181.3 / 200.8 | 0, 0, 1 | 100.00, 100.00, 98.00 | 3/3 |
| yoga2-01 | CPU_2_SPIN | 4.201 | 238.1 / 276.5 | 0, 1, 0 | 100.00, 97.86, 100.00 | 3/3 |
| yoga2-01 | CPU_4_SLEEP | 4.842 | 186.0 / 205.6 | 0, 0, 0 | 100.00, 100.00, 100.00 | 3/3 |
| yoga2-02 | REFERENCE_4_SPIN | 3.822 | 242.6 / 513.1 | 0, 5, 4 | 100.00, 83.46, 85.96 | 3/3 |
| yoga2-02 | CPU_2_SPIN | 3.008 | 334.7 / 710.8 | 8, 11, 7 | 69.17, 52.13, 70.93 | 3/3 |
| yoga2-02 | CPU_4_SLEEP | 3.822 | 244.8 / 498.9 | 4, 5, 3 | 86.72, 83.21, 89.47 | 3/3 |
| intake16-03 | REFERENCE_4_SPIN | 1.907 | 531.9 / 573.8 | 15, 21, 24 | 27.52, 6.54, 8.45 | 1/3 |
| intake16-03 | CPU_2_SPIN | 1.431 | 724.2 / 848.1 | 22, 19, 20 | 0.00, 0.00, 0.00 | 0/3 |
| intake16-03 | CPU_4_SLEEP | 1.703 | 599.3 / 680.6 | 23, 24, 20 | 10.90, 0.00, 12.53 | 0/3 |
| intake16-15 | REFERENCE_4_SPIN | 1.425 | 723.6 / 757.9 | 10, 10, 10 | 0.00, 0.00, 0.00 | 0/3 |
| intake16-15 | CPU_2_SPIN | 1.166 | 970.1 / 1096.6 | 9, 8, 8 | 0.00, 0.00, 0.00 | 0/3 |
| intake16-15 | CPU_4_SLEEP | 1.425 | 741.6 / 806.8 | 10, 10, 10 | 0.00, 0.00, 0.00 | 0/3 |

Os dados completos por execução incluem média/P95/máximo do processamento,
cadência por relógio de vídeo e monotônico, lacunas, idades de entrada/decisão,
cobertura, eventos, latências, perdas, duplicações, CPU/RAM e descartes:
[CSV das 39 execuções](DADOS/TRANSMISSAO_2026_10_26.csv).
Os intervalos inconclusivos e suas razões estão em `analysis.json`, junto das
análises de lacunas e processos concorrentes; os traces originais ficam preservados.
`latenciesMs` segue o critério em tempo de mídia; a coluna adicional
`decisionLatenciesFromMediaStartMs` inclui a idade do frame até a decisão,
relativa ao início da transmissão técnica. CPU e memória abrangem o processo
inteiro, inclusive carga/aquecimento/decoder; 100% de CPU equivale a um processador
lógico, não à máquina inteira.

Não houve alerta indevido nem duplicação nos quatro casos deste comparativo.
Isso não aprova o vazio: todas as repetições do vazio tiveram cobertura elegível
zero e resultado inconclusivo. O caso caro ficou sem evento em 2/3 repetições da
referência e nas seis das opções; mesmo a referência que emitiu teve cobertura
insuficiente. Yoga da sala com duas threads emitiu tarde nas três repetições,
entre 6240 e 13160 ms, com cobertura de 52,13–70,93%: reprovação funcional.

## Localização do custo e das lacunas

Na referência, 672 análises produziram 1023 chamadas reais ao modelo. Inferência
com preparação/recuperações ocupou **95,95%** do processamento medido; somente
`session.run` ocupou aproximadamente **94,21%**. A classificação somou 268 ms
(0,15%); checkpoint SQLite 4631 ms (2,55%); diagnóstico de decisão 295 ms (0,16%).
Não há base para culpar o banco da demonstração: esses checkpoints são SQLite
privado e nenhum HTTP foi executado.

| Passagem | Chamadas | Tempo total (s) | Média por chamada (ms) |
| --- | ---: | ---: | ---: |
| ORIGINAL | 672 | 112,483 | 167,386 |
| PERSON_PROPOSAL_CROP | 176 | 30,658 | 174,192 |
| ROTATE_270 | 98 | 17,344 | 176,983 |
| ROTATE_180 | 40 | 6,931 | 173,287 |
| CENTER_80 | 37 | 6,405 | 173,114 |

Preparação por passagem somou 2248 ms; decodificação/NMS das saídas, 312 ms;
restauração de coordenadas, 18 ms. O restante da inferência inclui transformação
da imagem, seleção de caminhos e controle do adaptador, sem ser atribuído a rede
ou câmera. As frequências são deste conjunto selecionado; não extrapolam para a
sessão física, onde as novas rotações ocorreram apenas dez vezes em 3628 inferências.

No perfil físico preservado, ORIGINAL + PERSON_PROPOSAL_CROP somaram 515,202 s
dos 613,462 s de inferência. As dez rotações novas somaram aproximadamente 1,749 s,
menos de 0,3% desse custo. Portanto, elas foram preservadas; removê-las não
atacaria a parcela principal medida e perderia a recuperação já comprovada.

A espera deliberada de agendamento somou 15,631 s na referência, registrada
separadamente do processamento. Nos maiores intervalos da referência, de cerca
de 813 ms monotônicos, a inferência anterior consumiu 800–808 ms; a prévia estava
desligada e o intervalo fora do processamento era inferior a 1 ms. Assim, essas
lacunas novas são explicadas pelo processamento, sem inferir a causa de pausas
históricas não instrumentadas.

No Python 3.12 deste Windows, `monotonic` usa GetTickCount64, resolução 15,625 ms;
as fases usam QueryPerformanceCounter, resolução declarada 0,0001 ms. O resíduo
entre esses relógios ficou em até 15,365 ms absolutos. Não tratar esse resíduo como
custo exato de diagnóstico. A escrita adicional do perfil somou 45,718 ms, medida
fora das fases. O critério de lacuna usa timestamps do arquivo, sem relaxamento.

A lacuna de 1797 ms da sessão física antiga segue **sem causa totalmente medida**:
a inferência imediatamente anterior durou 259 ms e a idade até decisão, 281 ms.
Faltava instrumentação para distribuir o restante entre espera, agendamento,
captura, persistência ou interface. O novo perfil permite essa distinção em
execuções futuras; não preenche retroativamente os dados antigos.

Com prévia ligada, o desenho/apresentação custou aproximadamente 11–12 ms por
análise em média, máximo de 62,6 ms. Houve somente uma repetição por perfil nessa
verificação exploratória: não permite atribuir causalmente toda a diferença de
cadência à interface. Nenhum ganho robusto dependeu de desligar o desenho.

Frames sobrescritos incluem a amostragem deliberada de 25/30 para até cinco
análises/s, além da sobrecarga. Não equivalem todos a falha de captura. O slot não
cresce. As idades máximas incluem o frame final ainda não consumido após EOF;
sem novos frames ele pode envelhecer até a próxima análise. Isso é separado de
fila crescente e aparece nos dados, sem descartar o fim dos clipes do resultado.

O inventário antes/depois de cada execução registra interferência do desktop:
Code, Chrome, serviços do Windows, WebView e Docker consumiram CPU. Não foram
encerrados processos do fundador. Processos restritos ou que terminaram entre as
amostras podem faltar nesse inventário. A ordem alternada e as três repetições
reduzem o viés de ordem; não eliminam toda a variação da máquina.

## Regressões, verificações e reprodução

Verificações realmente executadas, além da matriz acima:

| Comando | Resultado |
| --- | --- |
| `uv run --offline --project services/edge --frozen pytest services/edge/tests -q`, com `RADAR_TEST_GUI=1` | 383 testes passaram; GUI usa imagem sintética, sem webcam |
| `uv run --offline --project services/edge --frozen pytest services/edge/tests/test_runtime_profiles.py services/edge/tests/test_paced_file.py -q` | Cinco testes passaram após ajustes finais nos testes |
| `pnpm.cmd lint:edge` | Ruff e formatação passaram |
| `uv run --offline --project services/edge --frozen ruff check scripts/validation/benchmark-stream.py` e `ruff format --check` no mesmo arquivo | Passaram |
| `pnpm.cmd check:edge` | Imports reais de MediaPipe, OpenCV e ORT passaram; um único provedor de `cv2`; nenhuma câmera aberta |
| `pnpm.cmd lint` | Passou |
| `pnpm.cmd typecheck` | Passou |
| `pnpm.cmd build` | Web, API e contratos compilaram |
| `pnpm.cmd test:contracts` | Verificação dos tipos gerados e contratos TS/Python passou |
| `pnpm.cmd test:api` | 159 testes passaram, em PostgreSQL exclusivo descartável |
| `pnpm.cmd test:e2e` | 20 testes passaram, desktop/mobile e recursos exclusivos |
| `git diff --check` | Sem erros de whitespace; avisos CRLF/LF do Git preservados |
| `docker compose --env-file .env -f infra/compose.yaml ps` e consulta das portas locais | PostgreSQL saudável em 15432; serviço independente continuou escutando em 5432 |

Durante a implementação, Ruff apontou ajustes de imports, pares consecutivos e
comprimento de linha. Um teste novo usava inicialmente nome de política fora da
família RTMO e falhou no validador; a fixture foi corrigida, preservando o
validador. As verificações acima registram os resultados finais. API/E2E usam
fixtures controladas; não contam como percepção física ou revisão humana nova.
Não foi repetida a instalação limpa/backup da etapa 08: não houve mudança de
dependência, lock, banco ou migração nesta rodada, nem nova aprovação de release.

Regressão funcional: **72 FILE completos**, 36 com REFERENCE_4_SPIN e os mesmos 36
com CPU_4_SLEEP. Nos dois perfis, a comparação com a referência preservada da
rodada anterior encontrou **zero diferenças** em eventos/timestamps de mídia,
tempo elegível, tempo observado, cobertura de captura e razões de rejeição.
Cada perfil gerou 12 eventos; nenhum alerta fora dos alvos e nenhuma duplicação.
Os seis alvos dos 16 arquivos continuaram reconhecidos em 2000 ms. Os dois yogas
continuaram em 2002 e 2000 ms no processamento completo em arquivo.

Preservados sem alerta: `floor03`, `floor05`, `floor07` e `controlled-lying`.
POSSIBLE_FALL continua limitado a uma das quatro transições CAUCA; reconhecer
postura no chão nas demais não comprova reconhecer a transição. Dos 20 negativos,
18 tiveram cobertura suficiente; `cauca-10` e `chair08-01` continuam inconclusivos.
[Resultados dos 72 casos](DADOS/REGRESSAO_TRANSMISSAO_2026_10_26.csv).

Somente os dois controles previamente confirmados vazios pelo fundador usam a
cobertura de captura na avaliação, conforme a anotação anterior; isso não é
inferência de ambiente vazio por NO_POSE. Os scores brutos também foram
preservados, e a consolidação com essas anotações fica em `regression-summary.json`.
Nenhuma exceção por arquivo foi acrescentada ao detector. A regressão completa
em arquivo não usa descarte por sobrecarga e **não substitui** o ensaio de
transmissão: os mesmos alvos que funcionam nesse modo podem falhar em ritmo real.
CPU_2_SPIN já foi rejeitado nas três repetições dos quatro casos técnicos e no
microperfil; não foi submetido à regressão completa de 36 casos.

Para repetir uma transmissão técnica, com os materiais privados desta bancada:

```powershell
. ./scripts/activate.ps1
$saida = ".local/benchmarks/stream-$([guid]::NewGuid())"
uv run --offline --project services/edge --frozen python scripts/validation/benchmark-stream.py --config .local/detector-evolution/perception-dce2d01b-278b-4029-a405-974ffb0d00e9/candidate-final/yoga2-02/comparison.yaml --output $saida --runtime-profile REFERENCE_4_SPIN
```

`--preview` liga a prévia de arquivo. Para comparar as opções isoladas, use um
novo diretório para cada execução e `CPU_2_SPIN` ou `CPU_4_SLEEP`. O comando recusa
sobrescrever saídas, exige FILE autorizado e desliga o envio. Não abre webcam.
Instalação nova exige vídeos, calibrações e artefatos correspondentes, que não
pertencem ao Git.

Comandos adicionais realmente executados nesta bancada, todos pelos locks:

```powershell
node .local/detector-evolution/freeze-throughput.mjs
uv run --offline --project services/edge --frozen python .local/detector-evolution/profile-cpu-options.py
uv run --offline --project services/edge --frozen python .local/detector-evolution/run-throughput.py
uv run --offline --project services/edge --frozen python .local/detector-evolution/analyze-throughput.py
uv run --offline --project services/edge --frozen python .local/detector-evolution/regression-throughput.py REFERENCE_4_SPIN
uv run --offline --project services/edge --frozen python .local/detector-evolution/regression-throughput.py CPU_4_SLEEP
```

Os auxiliares privados registram a matriz e as anotações existentes. A ferramenta
reutilizável versionável é `scripts/validation/benchmark-stream.py`; não depende
de inferência pré-calculada. Os diretórios antigos não foram substituídos.

## Decisão e pendências

Preservar **REFERENCE_4_SPIN**. As opções ficam explícitas para reprodução técnica;
nenhuma configuração da webcam ou demonstração foi migrada. Menor consumo de CPU
com duas threads veio acompanhado de pior cadência, latência e cobertura. Sem
espera ativa, diferenças pequenas mudaram de sentido entre casos/repetições e o
caso caro continuou falhando. Não há fundamento para combinar ou promover opções.

O bloqueio restante é o custo acumulado de múltiplas inferências reais em CPU,
sem margem suficiente para manter lacunas até 500 ms nos casos difíceis. Esta
rodada não comprova que custo seja a única causa de perdas nas orientações de pés,
nem corrige o reconhecimento dos quatro arquivos históricos. Não foi preparado
um novo ensaio físico como se houvesse candidato melhor: falta primeiro uma
redução consistente desse custo, preservando reconhecimento e critérios.
O teste físico, as revisões humanas antigas e avaliação independente continuam
pendentes no estado de aceite do detector; não foram removidos nem aprovados.

Banco da demonstração em 15432, serviço independente em 5432, proprietário,
credenciais, vídeos e calibrações preservados. Sem commit, push, deploy, câmera IP,
gravação ou abertura de webcam nesta rodada.
