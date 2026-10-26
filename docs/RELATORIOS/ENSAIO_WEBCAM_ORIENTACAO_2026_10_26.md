# Ensaio físico de orientação — auditoria da sessão de 26/10/2026

**Resultado: NÃO APROVADO para o aceite.** Captura e entrega de quatro eventos
funcionaram. A validação das seis tentativas permanece inconclusiva por limites
dos marcadores/durações; há insuficiência de cobertura medida e três janelas
sem alerta. Os seis controles ficaram sem alertas, mas nenhum atende ao gate
completo de cobertura. Quatro revisões humanas ainda não foram salvas.

Esta auditoria não abriu câmera, executou modelo/replay, alterou parâmetros,
reescreveu rótulos anteriores ou repetiu tentativas. Nenhum commit/push/deploy.

## Sessão identificada e evidências preservadas

- Diretório: `.local/detector-evolution/physical-sessions/10347778-faf8-4637-8bcb-601d3cd21364`.
- Marcadores: abertura em 26/10, 11:24:28; fechamento em 11:36:13, UTC−03.
- Worker: **704,774 s** de parede; **701,406 s** entre primeira/última análise.
  Não foi uma medição de 30 minutos nem exatamente 12 minutos contínuos.
- Captura LIVE: índice 0, DSHOW, 640×480; câmera lógica
  `5be84234-7b00-4e87-85e8-b0e68f7c2a6d`.
- Run de captura/API: `c7c9d6e4-b3d3-4b3b-bbc0-9369ffe603e0`.
  Execução temporal/SQLite: `c7ac3e92-44dd-4ec4-8a1e-c786aafbbb38`.
  São identificadores diferentes por função; os quatro eventos usam o run de captura.
- Relatório: `results/0ee7fc3c-79b9-4901-afe4-0e8a45dabcc8/report.json`.
- `status: ok`, `captureState: ENDED`, erro nulo, worker-errors.log vazio;
  12 cenas com pares de início/fim, nenhuma cena aberta ao encerrar.
- 2041 decisões e três registros de status, exportação completa, sem truncamento.
  Evidência skeleton; zero snapshots e `framesSaved: false`.

Modelo RTMO-s SHA `d0703d40d19f3921da51ae725402d5fdae4d2478c7442072d3101bd396f370d8`;
classificador `signed-body-mlp-v3-dev01`, SHA
`40d01401851f24cd8c815557970f0dcf42877707afbba38d521ebfa87bd5bd19`;
recuperação RTMO_ADAPTIVE_V3, política
`floor-rtmo-score-posture-multiclass-v3-dynamics01-adaptive3`.
Calibração `ab0094ef-eee7-478b-8304-bf96139c0d48-v3`, contexto digital SHA
`a53ea803ad2cf1fefee076cc07042713f21e5c036bc331598b712edf7d7f24f1`.
Compatibilidade digital não certifica o enquadramento físico de cada postura.

Fonte atual conferida sem alterações frente ao candidato congelado: 200 arquivos,
SHA `4fab1f96dc5d29d71d9210e4c956143bcdbeda36a7ed583609d89e8b4b36f7f5`.
Não houve ajuste do detector durante esta auditoria.

Evidências e cálculos ficam em
`.local/detector-evolution/physical-audit-3b6b3a73-3908-4afa-b7c9-d4b86e7fef1c/`,
ponteiro `physical-audit-current.json`. Incluem hashes dos arquivos originais,
feedback do fundador, auditoria temporal, contratos e consulta somente leitura
ao PostgreSQL 15432. Hashes de configuração, protocolo, marcadores, SQLite,
logs, relatório e trace conferidos antes/depois: **inalterados**.

## Critérios anteriores e limite dos marcadores

Mantidos os critérios do [roteiro](../USO_DETECTOR_EXPERIMENTAL.md): seis tentativas,
três orientações, aproximadamente 10 s no chão em cada uma; prazo de 5000 ms desde
início humano da postura; cobertura ≥80% em cada alvo/controle; rearme por
3000 ms contínuos de evidência negativa, com 20 s em pé previstos entre tentativas;
sem duplicação. No vazio confirmado, usar cobertura operacional da captura em
vez de exigir pose. Entrega/exibição proposta em até 5 s após decisão; revisão
humana persistida. Persistência do detector permanece 2000 ms, lacuna máxima
500 ms e fração positiva mínima 80%.

O fundador esclareceu durante a auditoria:

1. Clicou início **antes de ir ao chão** e fim **ao voltar ao computador**.
2. Algumas tentativas duraram menos de 10 s ou não foram completadas; não lembra
   quais. Não há autorização para inventar essa distribuição ou retirar tentativas.
3. Ninguém ficou deitado nos seis controles negativos.
4. Não lembra a atividade durante o alerta entre a primeira e segunda lateral.

Logo, as janelas registradas contêm preparação, deslocamento e retorno. Seus
tempos são calculáveis, mas **não são os limites exatos da postura no chão**.
Não usar a primeira predição LYING como início humano, não recortar trechos
favoráveis depois do resultado e não chamar essas durações de tempo real deitado.
As seis posições ficam no denominador de execução. Não há base para afirmar
recall 3/6, seis acertos, três perdas definitivas ou cumprimento do prazo postural.

### Relógios e fórmulas utilizados

O alinhamento usa o relógio monotônico dos marcadores e da captura:

`t_marcador = (hostMonotonicNs − hostMonotonicOriginNs) / 1e6 + sourceTimestampOffsetMs`.

Origem desta sessão: `2982796000000 ns`; offset **−1766 ms**. Ignorar esse offset
deslocaria artificialmente as cenas. O tempo clique→frame de emissão usa a
diferença nessa base. Clique→decisão pronta soma a idade monotônica do frame
ao concluir a decisão/checkpoint. Datas UTC do payload são derivadas da âncora
da execução; transporte/aviso são comparados com `recordedAt` da decisão, sem
misturar relógio de mídia com parede ou considerar `floorDurationMs` uma latência.

Cobertura por janela: soma dos intervalos consecutivos, cortados nos limites
dos marcadores, com ambos os extremos elegíveis e delta ≤500 ms, dividida por
**todo** o tempo entre os cliques. Captura operacional também exclui LOW_FPS,
FRAME_TIMEOUT, LOW_LIGHT e POSSIBLE_FROZEN e exige delta ≤500 ms. Contagem de
poses/análises é informada separadamente. Lacunas conservadoras incluem intervalos
adjacentes às observações não elegíveis. Nada foi removido do denominador.

## As seis tentativas, sem exclusões

Os atrasos abaixo são desde o **clique de preparação até a decisão pronta**,
não desde um início postural conhecido. A coluna de cobertura refere-se à janela
completa dos cliques. Números detalhados no
[CSV das 12 cenas](DADOS/ENSAIO_WEBCAM_2026_10_26.csv).

| Tentativa | Janela | Eventos dentro | Clique→decisão | Cobertura | Maior intervalo inconclusivo / maior delta de análise |
| --- | ---: | ---: | ---: | ---: | --- |
| Lateral 1 | 33,718 s | 1 | 8,437 s | 87,7662% | 1,625 s / 734 ms |
| Lateral 2 | 27,641 s | 1 | 15,579 s | 57,7765% | 7,485 s / 703 ms |
| Pés para câmera 1 | 24,719 s | 0 | — | 71,6170% | 2,640 s / 453 ms |
| Pés para câmera 2 | 26,984 s | 0 | — | **79,7917%** | 2,453 s / 750 ms |
| Cabeça para câmera 1 | 23,469 s | 1 | 9,407 s | 67,4379% | 2,422 s / 765 ms |
| Cabeça para câmera 2 | 24,891 s | 0 | — | 68,1732% | 2,594 s / 812 ms |

Clique→frame de emissão: respectivamente 8234, 15391 e 9188 ms nos três registros
internos às janelas. São todos superiores a 5 s desde o clique; a conclusão
sobre **5 s desde a postura** continua inconclusiva pelos limites dos marcadores.
Somente a primeira janela supera 80% de cobertura; isso não aprova sua latência,
postura/duração ou o ensaio inteiro. **79,7917% não foi arredondado para aprovar.**

As três janelas sem evento continuam explícitas. Como não sabemos quais foram
incompletas e onde estavam os trechos realmente deitados, seu aceite postural é
INCONCLUSIVO, com possível perda registrada, e não negativo correto.

### O que os traces explicam

- Lateral 1: 142 análises, 130 elegíveis, 65 candidatas. Persistência atingida;
  episódio rearmou dentro da própria janela de cliques, após aproximadamente
  23,984 s do clique. Isso reforça que a janela inclui atividades além da postura.
- Lateral 2: 101 análises, 76 elegíveis, 30 candidatas. Há 17 descritores
  insuficientes, duas ausências de pose e quatro posturas incertas. Novo episódio
  foi emitido; cobertura da janela permanece insuficiente. Rearme posterior
  dentro da janela, a 25,500 s do clique.
- Pés 1: 77 poses observadas, mas **zero candidatas de piso**. Classes incluem
  36 ajoelhado/abaixado, 27 sentado e uma LYING rejeitada por evidência corporal
  incompleta/contexto. O motor permaneceu OBSERVING; não foi supressão por
  episódio antigo. Sem limites humanos da postura, não atribuir todas essas
  classes a uma pessoa efetivamente deitada durante todo o intervalo.
- Pés 2: 89 análises, 86 com pose, **zero candidatas**; 43 sentado, 30
  ajoelhado/abaixado e duas LYING com evidência/contexto insuficientes. Não é
  apenas ausência de pose; classe/qualidade/contexto não sustentaram o alvo.
- Cabeça 1: 77 análises, 67 elegíveis, 32 candidatas; evento após persistência
  de 2141 ms. Há lacunas, e o episódio ainda estava ativo ao começar a janela
  seguinte de preparação.
- Cabeça 2: 82 análises, 73 elegíveis e 23 candidatas. O rearme concluiu a
  **4,360 s do clique**, antes da primeira candidata a 7,141 s. Nenhuma candidata
  positiva dessa janela foi suprimida pelo episódio anterior. Portanto, o rearme
  inicial não é causa comprovada do silêncio. Depois, uma sequência chegou a
  **1813 ms**, mas um delta de **734 ms** reiniciou a suspeita. Vieram resets
  com deltas de **812, 703 e 781 ms**. Outra sequência chegou a **1829 ms** e
  foi interrompida antes dos 2000 ms, seguida de classificação não candidata.
  O trace comprova evidência temporal fragmentada; não comprova duração real da
  postura nem se a classificação acompanhou corretamente o corpo em cada instante.

Não foram reduzidas a persistência, a qualidade ou a tolerância para criar um
alerta artificial. Há limitações observadas de classe/contexto e de cadência;
sem vídeo bruto e anotação precisa, a causa física das diferenças não é isolável.

## Rearme, alerta fora das cenas e duplicação

Intervalos entre cliques de fim/início das seis tentativas: 44,578; 23,219;
53,859; 21,453; 22,031 s. Todos superam a espera operacional de 20 s, mas não
comprovam 20 s fisicamente em pé, nem 3 s de evidência negativa contínua reconhecida.

O motor registrou quatro encerramentos de episódio por evidência negativa
contínua ≥3000 ms. Antes da segunda lateral, o episódio emitido no intervalo
também rearmou. Antes da segunda cabeça, não havia encerramento ainda; ele
ocorreu 4,360 s depois do clique, antes das candidatas dessa tentativa.
Nenhum parâmetro foi alterado para acelerar esse rearme.

O quarto evento ocorreu **às 11:26:41**, fora das 12 janelas anotadas, entre
lateral 1 e lateral 2. Não foi atribuído à segunda lateral para aumentar acertos.
O fundador não lembra a atividade; permanece **não adjudicado**: pode representar
outro trecho no chão, fragmentação de episódio ou alerta indevido. Não há base
para escolher uma dessas interpretações nesta auditoria.

Duplicação técnica observada: quatro eventId/episodeId distintos, quatro ACKs
CURRENT com `duplicate: false`, uma tentativa HTTP por evento, um recibo e um
incidente por eventId. Não houve duplicação de ingestão observada. Não foi feito
reenvio nesta sessão/auditoria. **Duplicação semântica** entre episódios físicos
não pode ser descartada no alerta fora das cenas; fica pendente de contexto.

## Todos os seis controles

O fundador confirmou ausência de pessoa deitada nesses controles. Não houve
eventos nem candidatas em nenhuma das seis janelas.

| Controle | Janela | Alertas | Cobertura decisória | Cobertura operacional de captura | Resultado pelo gate completo |
| --- | ---: | ---: | ---: | ---: | --- |
| Cadeira | 21,875 s | 0 | 73,2846% | 96,4297% | INCONCLUSIVO, cobertura <80% |
| Ajoelhar | 19,578 s | 0 | 72,2290% | 79,8090% | INCONCLUSIVO |
| Pegar objeto | 17,969 s | 0 | 57,6493% | 73,6491% | INCONCLUSIVO |
| Caminhar | 32,719 s | 0 | 69,4337% | 83,4286% | INCONCLUSIVO |
| Cômodo vazio | 18,688 s | 0 | não exige pose | **0%** | INCONCLUSIVO, gate operacional |
| Retornar caminhando | 26,750 s | 0 | 68,9869% | 82,1869% | INCONCLUSIVO |

Zero alertas indevidos **dentro desses controles confirmados** é um resultado
favorável observado; não basta para PASS com cobertura insuficiente. A atividade
do alerta fora das cenas não é conhecida, portanto não se afirma zero alertas
indevidos em toda a sessão nem se calcula especificidade geral.

No vazio: 33 análises NO_POSE, todas com LOW_FPS, deltas atravessando a janela
acima de 500 ms e inferência média **519,962 ms**. A cobertura operacional usada
pelo protocolo combina saúde e cadência; **0% não significa câmera desligada**.
Frames continuaram chegando e eram recentes, sem reconexão/erro de captura.
NO_POSE não foi usado para confirmar ambiente vazio: o rótulo vem da cena marcada
pelo operador, cujos limites exatos de ausência também não foram registrados.
Não se corrigiu a métrica ou removeu o requisito para aprovar esse controle.

## Desempenho LIVE efetivamente medido

| Medida | Resultado |
| --- | ---: |
| Aquisições até o último snapshot consumido | 20376 |
| Snapshots consumidos, incluindo preparação | 2042 |
| Frames analisados | 2041 |
| Frames intermediários sobrescritos no slot | 18334 |
| Cadência de aquisição entre índices observados | 29,015/s |
| Cadência efetiva de análise | **2,908/s** |
| Novas apresentações da prévia | 2,909/s |
| Inferência média / P95 / máxima | 300,569 / 555,845 / 771,685 ms |
| Idade do frame no início, média / P95 / máxima | 19,897 / 47 / 79 ms |
| Idade ao concluir decisão, média / P95 / máxima | 331,282 / 594 / 1000 ms |
| Classificação corporal média / máxima | 0,259 / 1,313 ms |
| Deltas de análise >500 ms | **281** |
| Maior delta de análise | **1797 ms** |
| Descartes de análise por idade >2000 ms | 0 |
| CPU do processo worker | 2627,875 CPU-s; 372,868% de um núcleo lógico |
| Pico de memória do processo worker | 240,85 MiB |
| Reconexões / pausas / erros | 0 / 0 / 0 |

CPU/memória não incluem integralmente o processo auxiliar de captura nem os
demais serviços do computador. Percentis calculados sobre as decisões, por
interpolação linear. Não confundir taxa da câmera com taxa do desenho/modelo.
Os contadores do source se referem ao último consumo, sem contabilizar como total
exato os frames posteriores a ele durante a inferência final/encerramento.

O buffer permaneceu limitado ao único slot mais recente. Sobrescrita de cerca de
90% dos frames é a política de descarte, não 18334 falhas do driver. Idade inicial
máxima de 79 ms não indica acúmulo progressivo de imagens antigas. O driver nativo
não foi perfilado internamente. Os custos de inferência/recuperação e do pipeline
explicam parte da cadência; não foi isolada a causa de cada atraso, inclusive o
delta máximo de 1797 ms. Não culpar iluminação/câmera por esses números sem prova.

Foram 3628 inferências nativas em 2041 análises: ORIGINAL 2041; recorte de proposta
1039; inversão 180° 269; recorte central 269; nova rotação 270° seis e 90° quatro.
A recuperação nova não foi o trabalho predominante nesta sessão. Reduzir apenas
seu número de chamadas não é uma correção demonstrada dos demais problemas.

Cobertura global: **274591/701406 ms = 39,1487%**; cobertura operacional de captura
498189/701406 = 71,0272%. Contagem elegível: 1135/2041 = 55,6100%; pose presente:
1773/2041 = 86,8692%; oito essenciais suficientes: 874/2041 = 42,8221%. São
métricas diferentes. O global inclui aproximação ao computador, transições e
intervalos não anotados; não é recall das posturas. A recomputação dos dois
totais temporais coincide exatamente com o relatório do worker.

Os 281 deltas maiores que 500 ms somam 176655 ms de intervalos; o excesso sobre
500 ms por delta soma 36155 ms. Não confundir essas somas nem chamá-las de tempo
de queda ou de captura perdida. A cadência solicitada de 5 análises/s não foi
atingida na média; frames recentes não garantiram observabilidade contínua.
O desempenho operacional necessário ao aceite permanece insuficiente/inconclusivo.

## Entrega, aviso e revisão no painel

Consultas somente leitura ao PostgreSQL da demonstração, **15432**, em 26/10,
11:45:50 e 11:59:27 UTC−03, ambas com zero revisões. Quatro incidentes correspondem exatamente aos quatro ACKs da
SQLite, fonte WEBCAM, modo LIVE, classe CURRENT e política/modelo esperados.
Todos são PERSON_ON_FLOOR, sem POSSIBLE_FALL. Não houve teste de queda física.

| Cena / horário UTC−03 | Incidente | Decisão registrada→recepção API | Decisão→aviso local | Revisão persistida |
| --- | --- | ---: | ---: | --- |
| Lateral 1, 11:25:55 | [d279453b…](http://127.0.0.1:3000/incidentes/d279453b-7756-4402-9491-a5cf6e576828) | 318,143 ms | 890,143 ms | UNREVIEWED, versão 1 |
| Fora das cenas, 11:26:41 | [c152dea8…](http://127.0.0.1:3000/incidentes/c152dea8-bf52-4e9c-b50d-292163786d05) | 192,804 ms | 558,804 ms | UNREVIEWED, versão 1 |
| Lateral 2, 11:27:21 | [ab962466…](http://127.0.0.1:3000/incidentes/ab962466-d055-453e-8fb2-f3c800753c22) | 255,652 ms | 285,652 ms | UNREVIEWED, versão 1 |
| Cabeça 1, 11:30:12 | [51555bf7…](http://127.0.0.1:3000/incidentes/51555bf7-31e2-44e3-a121-c65f7f106daa) | 196,518 ms | 919,518 ms | UNREVIEWED, versão 1 |

API/aviso atenderam ao limite proposto de 5 s após a decisão nesses quatro
registros. Existem quatro recibos e quatro avisos DELIVERED, canal **SIMULATED**,
urgência true segundo o contrato LIVE/CURRENT. São avisos locais; nenhuma
notificação externa foi enviada. CURRENT não é um selo de eficácia ou de teste:
a natureza controlada permanece no protocolo. Não houve falsificação REPLAY/TEST.

O banco contém **zero ações humanas e zero revisões** nesses quatro incidentes.
Não foram registradas ações pelo auditor para simular uma revisão. A sessão
completa tem **zero marcadores HUMAN_PANEL_VISIBLE**; a exibição visual em até
5 s permanece não verificada. Não afirmar que o painel deixou de exibir, nem
substituir esse critério pelo tempo de recepção da API. Heartbeat final ENDED,
run correspondente e sequência 370 estão persistidos. O source.captureState
RUNNING do relatório bruto é seu último estado de aquisição; não prevalece sobre
o encerramento do worker/heartbeat.

## Sessões anteriores próximas, também preservadas

| Sessão | Parede | Cenas encerradas | Eventos | Observação |
| --- | ---: | ---: | ---: | --- |
| 93edb060… | 6,203 s | 0/12 | 0 | preparação, não é controle negativo aprovado |
| 62003183… | 89,924 s | 1/12 | 0 | primeira janela lateral sem evento; execução incompleta |
| 10347778… | 704,774 s | 12/12 | 4 | sessão principal auditada acima |

Na segunda sessão há um marcador de painel visível, mas nenhum evento gerado
nessa execução. Pode corresponder a registro já existente; não foi atribuído à
sessão principal nem usado para aprovar sua entrega/exibição. Nenhuma tentativa
anterior foi apagada ou substituída por uma posterior.

## Comandos e verificação realmente executados nesta auditoria

| Comando/ação | Resultado |
| --- | --- |
| git status, leitura de AGENTS/README/STATUS, roteiro e relatório anterior | alterações existentes preservadas, critérios localizados |
| inventário das três physical-sessions, leitura de marcadores/protocolo/relatórios | sessão completa identificada e duas incompletas mantidas |
| uv run --offline --project services/edge --frozen python .local/detector-evolution/audit-physical-session.py | doze janelas, relógios, intervalos, candidatos, custo e entregas auditados; totais temporais conferem |
| node --env-file=apps/api/.env .local/detector-evolution/audit-physical-database.mjs | quatro incidentes/recibos/avisos, zero revisões, ENDED; consulta somente leitura |
| uv run --offline --project services/edge --frozen python .local/detector-evolution/finish-physical-audit.py | quatro contratos nativos válidos, hashes originais inalterados, CSV de 12 cenas |
| node .local/detector-evolution/audit-physical-source.mjs | fonte igual ao candidato congelado; parâmetros não alterados |

O primeiro helper de banco consultou um nome de modelo Prisma inexistente;
foi corrigido para Camera.lastHeartbeat e repetido somente em leitura, sem
alteração no software ou no banco. Nenhum erro foi tratado como aprovação.
Lint de documentação/diff e conferências finais estão registrados nesta entrega.
As suítes de engenharia anteriores não foram repetidas: esta solicitação auditou
dados existentes e atualizou documentação, sem alteração de código executável.

## O que passou e o que continua pendente

**Funcionou e foi verificado:** captura LIVE encerrada sem erro; frames recentes
em buffer limitado; quatro emissões de pessoa no chão; quatro entregas atuais,
incidentes e avisos locais únicos; zero alertas nas seis janelas negativas
confirmadas; integridade dos registros e encerramento ENDED no banco.

**Não atende ao aceite ou não foi comprovado:** prazo real desde postura e
duração das seis tentativas; três janelas positivas sem alerta; cobertura <80%
em cinco janelas positivas e nos seis controles pelo critério correspondente;
cadência/lacunas e qualidade de pose/classificação; significado do evento fora
das cenas e eventual duplicação semântica; exibição visual no prazo; quatro
revisões humanas. Não chamar a execução de “seis tentativas aprovadas”.

As lacunas e limitações medidas permanecem no relatório. Para fechar a avaliação
postural será necessário um protocolo com limites humanos confiáveis e conclusão
das tentativas, em nova execução somente se solicitada/autorizada. Esta auditoria
não repetiu o teste e não escolheu novos parâmetros. As revisões dos quatro
incidentes atuais podem ser feitas pelo fundador no painel; o evento sem contexto
deve preservar essa incerteza. Reserva independente, observação prolongada e
reconhecimento de queda continuam pendentes; os históricos de perdas não mudaram.
