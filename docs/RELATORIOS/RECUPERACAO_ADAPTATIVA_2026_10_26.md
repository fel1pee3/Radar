# Preferência adaptativa de processamento — 26/10/2026

**Rodada concluída; candidato não promovido por regressão de observabilidade.**
Nenhuma webcam aberta, gravação habilitada, peso treinado ou configuração de uso
substituída. Esta rodada investiga prioridade de processamento, mantendo a
referência e os critérios de reconhecimento.

## Referência preservada e hipótese

Leituras: AGENTS, README, STATUS,
[perfil anterior](DESEMPENHO_TRANSMISSAO_2026_10_26.md), código de percepção,
recuperação, LIVE e executor de transmissão. Árvore já tinha alterações locais;
nenhuma foi descartada. Referência: `REFERENCE_4_SPIN` com `RTMO_ADAPTIVE_V3`,
HEAD `eaa845a060db680d679b4563a42a984e3fcc05d2`, fonte de 204 arquivos SHA-256
`ec9f8e7559d58ceacba62cf50f27c34b7514e4d60104e91e155c4f9882602468`.
Código/documentos presentes, diff e resultados anteriores foram preservados em
`.local/detector-evolution/adaptive-f49969ae-a288-426a-9361-6ef56c73b77c/`.
ZIP da referência: `461b7c4b4807dcebd397f129c24fa36eb3032486bc0b1801e10a22d73169ed50`.
Ponteiro privado: `.local/detector-evolution/adaptive-current.json`.

Modelo RTMO e classificador permanecem, respectivamente, SHA-256
`d0703d40d19f3921da51ae725402d5fdae4d2478c7442072d3101bd396f370d8` e
`40d01401851f24cd8c815557970f0dcf42877707afbba38d521ebfa87bd5bd19`.
Configurações, calibrações e resultados anteriores não foram sobrescritos.
O arquivo `rtmo.py` da referência foi comparado byte a byte com o snapshot e
permanece intacto. Threads não foram objeto de nova investigação.

Nos 12 traces de referência da rodada anterior, o caminho selecionado foi
reconstituído pelas regras de seleção congeladas, preservando empates do original.
"Útil" nesta análise significa uma pose com oito essenciais válidos, não
aprovação automática da classificação, contexto ou evento.

| Cenário | Observações | Caminho útil | Continuidade observada |
| --- | ---: | --- | --- |
| Casa, yoga2-01 | 364 | 364 ORIGINAL | Até 24992 ms no mesmo caminho; nenhuma chamada anterior dispensável |
| Sala, yoga2-02 | 186 | 132 ORIGINAL, 38 recortes de proposta, 16 ROTATE_270 | Alternância; maior sequência útil de um caminho, 5480 ms; 70 chamadas anteriores aos vencedores |
| Alvo caro, intake16-03 | 85 | 82 ROTATE_270, 3 ROTATE_180 | ROTATE_270 útil por até 14240 ms seguidos; 170 chamadas anteriores aos vencedores |
| Vazio, intake16-15 | 37 | Nenhum | Não há preferência bem-sucedida para memorizar |

As sequências acima descrevem utilidade perceptual mesmo quando havia lacunas
temporais; não são permanência elegível do detector. A hipótese é sustentada no
alvo caro, parcialmente na sala e não reduz trabalho na casa ou por memória no
vazio. No vazio, o ganho possível vem de distribuir a busca, mantendo NO_POSE e
incerteza explícitos. `path-hypothesis.json` preserva seleção, chamadas anteriores
e sequências de cada repetição.

## Candidato opt-in e limites definidos antes da comparação

`RTMO_PREFERRED_V1` vive em `preferred_rtmo.py`, separado do estimador de referência.
A fábrica e a configuração reconhecem a opção; nenhuma configuração antiga foi
migrada. A política recebe sufixo `-preferred-v1`, sem alteração numérica dos gates;
a identidade do episódio já inclui o método de recuperação.

| Limite | Valor e justificativa |
| --- | --- |
| Trabalho por análise | Até duas chamadas; referência física tinha chamada média de 167 ms, máxima de 229 ms |
| Início de chamada adicional | Somente antes de 220 ms de processamento; não iniciar trabalho adicional já sem margem |
| Inspeção canônica | Prazo de 800 ms, quatro intervalos nominais de análise |
| Lease da preferência | 1600 ms desde inspeção canônica, com sucesso atual necessário para utilizá-la |
| Lacuna de entrada | Mais de 500 ms invalida a preferência, além da quebra temporal já existente |
| Busca | Até 1600 ms de mídia ou oito análises; uma varredura esgotada reinicia pelo original |

Os valores estão em `protocol.frozen.json`, congelado antes da comparação final,
e em constantes do código. Nenhum foi escolhido após os resultados para aprovar
um arquivo. Os prazos são checados entre observações: não interrompem uma chamada
ORT em andamento. O intervalo real de inspeção e eventuais atrasos aparecem nos
traces; 800 ms não é uma garantia de tempo real do sistema operacional.

A memória contém nomes de caminhos, contadores, relógios e geometria. Cada pose
retornada vem de inferência real no frame atual. Não guarda imagem, articulações
ou ROI antiga para reaproveitar como observação. A proposta de recorte só existe
durante a análise atual e é apagada ao terminar. Sucesso de recorte de proposta
mantém o original como primeiro passo na próxima imagem, porque a ROI precisa
ser calculada novamente. A janela central fixa pode ser lembrada, mas sempre
executa inspeção do quadro inteiro antes do recorte em cada análise.

Uma orientação bem-sucedida é tentada primeiro entre inspeções. Na inspeção
periódica, o original precede a preferência; se falhar, a preferência tem prioridade
sobre repetir um recorte redundante. Falha atual ou duas pessoas invalida a memória.
Busca tenta orientações e janela central em imagens novas, respeitando o orçamento;
resultados ausentes/parciais continuam ausentes/parciais e não prolongam evidência.

Reconexão, pausa/retomada, indisponibilidade, mudança de geometria, expiração,
lacuna de entrada e erro de inferência invalidam o estado. A inspeção canônica
periódica evita permanecer apenas num recorte; múltiplas pessoas detectadas nela
são preservadas como ambiguidade. Isso não garante que um modelo encontre toda
pessoa presente. Mover uma câmera sem mudar dimensões ainda exige conferir sua
calibração; a estratégia não mede altura, contato físico com o piso ou identidade.

Inalterados: pessoa >0,7, NMS 0,45, qualidade articular e oito essenciais,
classificador, contexto/polígonos, permanência 2000 ms, cobertura 80%, lacuna
máxima 500 ms, rearme e demais temporizadores. A estabilização visual não fornece
pontos ao detector. Nenhum treino, interpolação, exceção por arquivo ou alteração
de timestamps foi introduzido.

## Falha intermediária preservada

O primeiro smoke do alvo caro reduziu chamadas para 1,258/análise, mas ficou sem
evento e com 45,78% de cobertura. Nas inspeções, um erro de ordem deixava o recorte
consumir a segunda chamada, impedindo a preferência atual. Corrigida a ordem para
cumprir o protocolo; nenhum limite foi alterado. Um teste cobre essa combinação
com proposta de recorte presente. O smoke seguinte gerou evento em 2400 ms,
cobertura 95,37%, sem lacunas >500 ms. As duas execuções permanecem separadas;
nenhuma integra o denominador da comparação final.

## Comparação final em transmissão técnica

24 execuções: quatro cenários × dois métodos × três repetições. Ordem alternada
por caso/rodada, sem inferências concorrentes, prévia desligada, processo novo por
execução e aquecimento real numa imagem cinza sintética, excluída das observações.
Todas começam no primeiro frame com memória vazia. É o executor a 1× da rodada
anterior, com o mesmo agendamento LIVE e slot de frame recente, sem repetir frames
ou processar todos lentamente. Há descartes visíveis quando o consumidor atrasa.

Fonte medida, 206 arquivos: SHA-256
`816cb569d26d8724660b08f0d927d4c67d19c0231379c8f16603ab35ad0a2cfd`.
`candidate-source.json` identifica código, ZIP e hash do protocolo. Pesos, dados,
parâmetros, aquecimento e condições são os mesmos em cada par. Inventários de
processos antes/depois registram interferência do desktop, sem encerrá-los.
O notebook continua Ryzen 5 5625U/12 processadores lógicos, Windows 11,
Python 3.12.15 e ORT 1.23.2 CPU, nas versões travadas do repositório.

| Caso | Método | Chamadas/análise (mediana) | Processamento médio / P95 (ms) | Cadência/s | Lacunas >500 ms (3) | Cobertura % (3) | Latências ms (3) |
| --- | --- | ---: | ---: | ---: | --- | --- | --- |
| yoga2-01 | RTMO_ADAPTIVE_V3 | 1.000 | 143.6 / 171.6 | 4.842 | 0, 0, 0 | 100.00, 100.00, 100.00 | [2035], [2035], [2069] |
| yoga2-01 | RTMO_PREFERRED_V1 | 1.000 | 145.1 / 173.4 | 4.802 | 0, 0, 0 | 100.00, 100.00, 100.00 | [2069], [2069], [2035] |
| yoga2-02 | RTMO_ADAPTIVE_V3 | 1.414 | 191.7 / 368.7 | 4.261 | 0, 0, 5 | 100.00, 100.00, 82.71 | [2200], [2280], [5280] |
| yoga2-02 | RTMO_PREFERRED_V1 | 1.171 | 163.5 / 288.9 | 4.574 | 0, 0, 0 | 93.48, 86.47, 90.23 | [3480], [3880], [3280] |
| intake16-03 | RTMO_ADAPTIVE_V3 | 3.000 | 444.5 / 500.1 | 2.248 | 0, 3, 24 | 100.00, 88.83, 3.27 | [2160], [2200], [] |
| intake16-03 | RTMO_PREFERRED_V1 | 1.258 | 185.7 / 302.4 | 4.428 | 0, 0, 0 | 98.09, 98.37, 98.09 | [2280], [2400], [2320] |
| intake16-15 | RTMO_ADAPTIVE_V3 | 4.000 | 590.2 / 632.3 | 1.684 | 12, 13, 9 | 12.44, 0.00, 0.00 | [], [], [] |
| intake16-15 | RTMO_PREFERRED_V1 | 1.324 | 195.0 / 302.4 | 4.275 | 0, 0, 0 | 100.00, 100.00, 100.00 | [], [], [] |

Os dados completos por execução incluem chamadas reais por caminho/análise,
processamento médio/P95/máximo, cadência, idades, lacunas, cobertura e intervalos
inconclusivos, aquisição, inspeções, eventos/latências/perdas/duplicações, CPU/RAM
e descartes. NO_POSE permanece inconclusivo na percepção. Somente a avaliação do
controle já anotado vazio pelo fundador usa cobertura de captura; não transforma
NO_POSE em inferência de ambiente vazio.

[CSV das 24 execuções](DADOS/ADAPTATIVA_TRANSMISSAO_2026_10_26.csv).
Na tabela, a cobertura do vazio é de captura; sua cobertura de pose permanece
zero. As colunas de latência em mídia e até a decisão estão separadas no CSV.
As medianas de P95 representam três P95 individuais, não um percentil combinado.

O candidato passou nos gates existentes nas **12/12** execuções desses quatro
cenários: nenhum alvo perdido/tardio, alerta indevido ou duplicação; zero lacunas
de mídia acima de 500 ms. No alvo caro, chamadas/análise caíram 58,08% e custo
médio por análise, 58,22%; no vazio, 66,91% e 66,95%. Na sala, 17,20% e 14,71%.
Na casa, não houve economia de chamadas e o custo mediano ficou cerca de 1% maior.
Os ganhos não são universais e não apagam o resultado da regressão.

São economias por análise, com totais de chamadas e CPU também registrados. Por
exemplo, alvo caro: referência 111/102/81 chamadas; candidato 83/84/76. O candidato
observou mais frames, portanto a redução total por sessão é menor que por análise.
Não atribuímos a cada chamada pulada a certeza contrafactual de que ela falharia.
O conjunto continua sendo desenvolvimento, sem números de eficácia independente.

Aquisição inicial do alvo caro ocorreu em 280/240/280 ms; os eventos, em
2280/2400/2320 ms. Não foi avaliado apenas o trecho após descobrir ROTATE_270.
A sala ficou com cobertura de 86,47–93,48%, contra 82,71–100% da referência, e
latências de 3280–3880 ms contra 2200–5280 ms. Houve troca entre continuidade,
observações perdidas e atraso, mesmo passando os gates desses arquivos.
Maior intervalo real entre inspeções canônicas do candidato: 1000 ms no alvo caro
e 960 ms na sala/vazio, pela verificação discreta dos prazos.

A primeira pose, mudanças/perdas da preferência e recuperação estão nos traces e
em `analysis.json`; os materiais permitem medir aquisição inicial e perdas de
pose na sala. Não há queda/reconexão de dispositivo físico nestes arquivos;
essas invalidações são verificadas por testes sintéticos, sem alegação de webcam.
Os mesmos vídeos já são desenvolvimento/regressão, não avaliação independente.

## Regressão, verificações e decisão

Regressão funcional completa em **36 arquivos**, com referência anterior
preservada e mesmo material/anotações. Os 12 eventos continuaram presentes:
seis alvos dos 16, os dois yogas e quatro posturas CAUCA. Sem alerta fora dos
alvos ou duplicação; POSSIBLE_FALL continua em somente uma das quatro transições.
As quatro perdas históricas continuam sem evento: `floor03`, `floor05`, `floor07`
e `controlled-lying`. A cobertura de floor07 ainda caiu de 32,17% para 12,10%.
Os dois negativos já inconclusivos foram mantidos; surgiram **quatro novos**:

| Controle | Cobertura da referência | Cobertura do candidato |
| --- | ---: | ---: |
| intake16-10 | 91,67% | 66,67% |
| cauca-08 | 81,03% | 77,59% |
| cauca-11 | 96,08% | 72,55% |
| cauca-12 | 80,00% | 43,08% |

Assim, dos 20 negativos, somente 14 ficaram com cobertura suficiente, contra
18 na referência. Ausência de alerta nesses quatro novos casos não é acerto.
`cauca-10` e `chair08-01` continuam inconclusivos.
[Comparativo completo dos 36 arquivos](DADOS/ADAPTATIVA_REGRESSAO_2026_10_26.csv).

Investigação por timestamps idênticos: nos quatro controles novos, houve 46
observações NO_POSE; em 37 delas o candidato não executou ORIGINAL. Em 16 desses
mesmos timestamps, a referência encontrou os oito essenciais já na primeira
passagem ORIGINAL. Nos demais, parte da recuperação precisava de outros caminhos.
O limitador de 220 ms **não adiou chamadas nessas observações inelegíveis**.
A causa demonstrada é a ordem/busca distribuída após perder a preferência, que
deixou de inspecionar o original em frames onde ele já voltara a ser útil.
`lost-observation-audit.json` preserva os exemplos e caminhos correspondentes.

Não se aumentou lacuna, tempo de busca, orçamento ou cobertura tolerada para
reclassificar esses controles. A melhora nos quatro arquivos técnicos não
compensou a regressão. V1 foi mantido apenas como opção experimental, sem migrar
configurações ou preparar outra comparação para tentar aprovar esses arquivos.

Verificações realmente executadas; logs privados em `checks/`:

| Comando | Resultado |
| --- | --- |
| `uv run --offline --project services/edge --frozen pytest services/edge/tests -q`, com `RADAR_TEST_GUI=1` | 399 passaram, incluindo 16 testes da estratégia e GUI sintética sem câmera |
| `uv run --offline --project services/edge --frozen ruff check services/edge scripts/validation/benchmark-stream.py` | Passou |
| `uv run --offline --project services/edge --frozen ruff format --check services/edge scripts/validation/benchmark-stream.py` | 80 arquivos conferidos |
| `pnpm.cmd lint` | Passou |
| `pnpm.cmd typecheck` | Passou |
| `pnpm.cmd build` | Web, API e contratos compilaram |
| `pnpm.cmd test:contracts` | 104 TS e 104 Python passaram; os Python já fazem parte dos 399 |
| `pnpm.cmd test:api` | 159 passaram, com banco descartável exclusivo |
| `pnpm.cmd test:e2e` | 20 passaram, desktop/mobile, recursos exclusivos removidos |
| `pnpm.cmd check:edge` | Imports reais e provedor único de OpenCV confirmados; nenhuma câmera aberta |
| `docker compose --env-file .env -f infra/compose.yaml ps` e inspeção das portas | Demo saudável em 15432; serviço independente continuou escutando em 5432 |
| `git diff --check` e auditoria final de hashes | Sem erros de whitespace; fonte/protocolo congelados e configurações, vídeos, modelos e calibrações preservados; lockfiles inalterados |

Os testes cobrem perda atual sem reutilizar pose, falha e mudança de preferência,
lease, busca finita, orçamento, inspeção de múltiplas pessoas, pausa/reconexão,
geometria, descarte de ROI antiga e restauração de quatro transformações. A falha
intermediária da ordem foi corrigida antes da comparação congelada. Os testes de
engenharia passarem não reclassifica os quatro controles da regressão: V1 continua
rejeitado. Sem reinstalação, nova dependência, migração ou nova aprovação de release.

| Pergunta de fechamento | Conclusão |
| --- | --- |
| A hipótese foi sustentada? | Sim no alvo caro; parcialmente na sala. Não há preferência útil no vazio e não há trabalho redundante na casa. |
| Chamadas e custo caíram consistentemente? | Sim por análise nos três cenários com recuperação, nas três repetições. Casa não teve ganho; totais/CPU não são confundidos com custo por análise. |
| O reconhecimento foi preservado? | Os 12 eventos e seus tipos foram mantidos, mas a observabilidade não: quatro novos negativos inconclusivos e redução de cobertura em outros arquivos. Preservação integral falhou. |
| Atende aos critérios nos quatro cenários técnicos? | Sim, 12/12. Isso não equivale a passar a regressão ou aprovar o detector. |
| Há fundamento para preparar teste físico curto? | Não nesta revisão: primeiro corrigir a regressão de busca sem reduzir requisitos. Nenhum protocolo de webcam novo foi preparado ou executado. |

**Manter REFERENCE_4_SPIN + RTMO_ADAPTIVE_V3 como referência/configuração existente.**
RTMO_PREFERRED_V1 permanece opt-in para reprodução da pesquisa e dos defeitos.
Não houve promoção automática ou aprovação do MVP.

Uma chamada nativa isolada chegou a 324,687 ms no candidato e 281,569 ms na
referência durante esta comparação; não há evidência, nestes casos, de que uma
única passagem impossibilite por si só o limite de lacuna de 500 ms. A casa
sustentou cerca de 4,8 análises/s com uma passagem. A cascata de três/quatro
chamadas explica o bloqueio de cadência, e a busca truncada/distribuída explica
a nova perda de observação. A próxima investigação deve preservar uma passagem
canônica útil durante a reaquisição e reavaliar o custo da recuperação; estes
dados não justificam atribuir o defeito à câmera nem obrigam trocar modelo/executor.
Isso tampouco prova desempenho suficiente em todo notebook ou resolve as perdas
físicas de classificação nas orientações de pés.

## Reprodução

Na raiz, com os mesmos materiais privados desta bancada:

```powershell
. ./scripts/activate.ps1
$saida = ".local/benchmarks/adaptive-$([guid]::NewGuid())"
uv run --offline --project services/edge --frozen python scripts/validation/benchmark-stream.py --config .local/detector-evolution/perception-dce2d01b-278b-4029-a405-974ffb0d00e9/candidate-final/intake16-03/comparison.yaml --output $saida --recovery RTMO_PREFERRED_V1
```

Para referência, use `--recovery RTMO_ADAPTIVE_V3`, sempre com nova saída. O comando
força FILE autorizado, REPLAY/TEST, sem HTTP, credencial, snapshot, status global
de câmera ou abertura de dispositivo. `complete: true` não é aprovação do detector.

Comandos privados realmente executados nesta rodada:

```powershell
node .local/detector-evolution/freeze-adaptive.mjs
uv run --offline --project services/edge --frozen python .local/detector-evolution/analyze-path-preference.py
node .local/detector-evolution/freeze-adaptive-candidate.mjs
uv run --offline --project services/edge --frozen python .local/detector-evolution/run-adaptive-comparison.py
uv run --offline --project services/edge --frozen python .local/detector-evolution/analyze-adaptive-comparison.py
uv run --offline --project services/edge --frozen python .local/detector-evolution/regression-adaptive.py
```

Os arquivos privados de resultados preservam logs, configurações isoladas e
anotações. Nenhum vídeo/peso/segredo entrou no Git. Banco da demonstração em 15432,
serviço independente em 5432, credenciais e proprietário permanecem preservados.
Sem commit, push, deploy, câmera IP, gravação ou abertura de webcam nesta rodada.
