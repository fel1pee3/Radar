# Estabilização perceptual — comparação final de 26/10/2026

**Rodada concluída; ROI rejeitada para integração e teste físico.**
As 96 transmissões e 144 execuções funcionais foram concluídas. A melhor ROI
ficou em 22/24 na transmissão, mas 27/36 em arquivo completo, contra 30/36 da
referência. Houve três perdas de aceite e uma mudança de tipo de evento.
Esta rodada investiga sete perdas restantes, confronta três estratégias e
mede a melhor alternativa isolada contra referência, V1 e V2. Não declara o
MVP concluído ou uso assistencial validado.

## Diagnóstico e escolha

[Diagnóstico contrafactual, sete frames e estratégias A/B/C](DIAGNOSTICO_RECUPERACAO_2026_10_26.md).
Todos os sete foram reproduzidos em timestamps exatos, com três repetições de
ORIGINAL e das cinco recuperações existentes. As perdas ocorrem principalmente
na aceitação de pessoa e seleção da recuperação; há também discordância de
classificação entre poses aceitas. Não foram explicadas como falha de UI,
interpolação ou problema de threads.

As políticas de sinais atuais e busca por famílias pioraram controles. A ROI
isotrópica de 50% foi a melhor das alternativas medidas, recuperando cauca-12,
mas já apresentou cauca-08 em 79,3103% no piloto. Esse resultado não foi
arredondado nem descartado. Uma variante mantendo a busca V2 também falhou.

**Não foi integrado novo estimador ao worker normal.** O melhor experimento
continua em execução FILE isolada para completar a comparação e caracterizar
as regressões. Seu nome é `RTMO_ROI_CONTEXT_EXPERIMENT_V1`; não é uma opção
nova em ModelConfig e não substitui V1/V2 ou RTMO_ADAPTIVE_V3. A implementação
versionada desta entrega é o auditor contrafactual com proteções de fonte,
timestamp e saída privada. Não se adiciona uma política especulativa ao produto.

## Preservação e protocolo congelado

Início limpo no HEAD `bb768abfe0c25e8f9d8a8127c455591718831be6`.
Raiz `.local/detector-evolution/stabilization-ce12cde8-31ee-4665-9727-c5f1da1111d5/`;
ponteiro `.local/detector-evolution/stabilization-current.json`.
Snapshot inicial e resultados anteriores preservados; protocolos e conclusões
dos relatórios anteriores não foram reescritos.

Fonte medida: 210 arquivos, SHA-256
`910e2d8bc17360800604412ba4ebe559054aae64764809878a7f493ee28fd3f3`.
Snapshot da fonte SHA-256
`cc79281ff567d7992d1ca7275c7d45b6b6266e74fd2ac20f087ae1c965a05140`.
Protocolo SHA-256
`be1cc77fc7c102b39ae96aaab2f579723fac50e28f1eabf5a75a00485d3f6014`.
Artefato privado do experimento SHA-256
`429cbc9f76f936018ef71bc67b2998fa1949a2997ffa37b4584d0fe07c4c6d13`.
O manifesto inclui ambos os hashes: o experimento privado não é confundido com
o código versionado do worker nem omitido da identidade do que foi executado.

O experimento foi carregado somente pelos executores FILE privados; configuração
base V2 e substituição da fábrica são identificadas no manifesto/summary, e a
estratégia efetivamente executada aparece nos traces. Sua ROI usa apenas a caixa
do ORIGINAL atual e margem de metade do lado maior. Proposta horizontal com oito
essenciais prioriza 270°, sem aceitar score sub-limiar. Não há nome de arquivo,
rótulo, timestamp absoluto ou resultado contrafactual na seleção. A margem
foi escolhida entre as duas hipóteses geométricas medidas antes da comparação
final; não foi ajustada para cada vídeo.

Mantidos: duas chamadas por análise experimental, início de chamada adicional
antes de 220 ms, inspeção a 800 ms, lease de 1600 ms, invalidação por lacuna
>500 ms/interrupção/reconexão/geometria, busca de 1600 ms/oito análises. Cada
observação resulta do frame atual. Nenhuma pose, imagem ou ROI antiga é usada
como evidência; NO_POSE não significa cômodo vazio. Prazos são verificados entre
observações, sem garantia de interrupção de uma chamada nativa em andamento.

Pesos RTMO `d0703d40d19f3921da51ae725402d5fdae4d2478c7442072d3101bd396f370d8`
e classificador `40d01401851f24cd8c815557970f0dcf42877707afbba38d521ebfa87bd5bd19`
inalterados. Sem treino, incorporação de novo modelo, alteração de limiares ou
polígonos, ajuste de permanência
de 2000 ms, cobertura de 80%, lacuna de 500 ms ou rearme. Timestamps e
denominadores de avaliação permanecem os anteriores.

96 transmissões novas: oito cenários × quatro métodos × três repetições.
Processos novos, ordem alternada, sem inferências concorrentes, prévia desligada,
mesmo aquecimento de uma imagem cinza sintética excluída. Vídeos desde o começo,
com memória vazia; produtor em 1× e consumidor/agendamento LIVE existentes.
Slot recente mantém descartes e atrasos visíveis. São REPLAY/TEST, sem HTTP,
dispositivo, snapshot ou banco da demonstração. Nenhuma sessão física ocorreu.
O agendamento a 1× pode selecionar frames diferentes conforme o custo; os
timestamps reais e idades são preservados. Assim, V2 ter 17/24 nesta rodada,
contra 16/24 na anterior, não representa uma alteração no seu código. Nenhuma
execução antiga foi substituída para obter uma combinação mais favorável.

144 arquivos completos novos: os mesmos 36 por método, positivos/negativos,
quatro controles regredidos, cadeiras e quatro perdas históricas, sem recorte de
trechos desfavoráveis. Execução por caso, alternando os quatro métodos, nove
primeiras posições por método; processo novo a cada par. FILE completo mantém
inicialização fria e começa no frame zero em todos os métodos. A ordem real
fica em `functional-order.json`. Uma execução inicial em lotes foi interrompida
para cumprir a ordem alternada; sete arquivos de referência já completos e o
seguinte parcial permanecem como prelúdio fora da matriz final, sem substituir
qualquer uma das 144 execuções. `full-order-amendment.json` registra essa correção
de execução antes da matriz funcional final, sem mudança de parâmetros.
Escopo de desenvolvimento/regressão; não é avaliação
independente. Ambiente: Windows 11 Pro 26200, Ryzen 5 5625U, seis núcleos/12
processadores lógicos, 15,41 GiB visíveis, Python 3.12.15, ORT 1.23.2 CPU,
MediaPipe 1.1.1 e único provedor cv2 opencv-contrib-python 5.0.0.93.

Variação também ocorreu no FILE completo por causa do orçamento por tempo,
sem mudar as imagens. Em intake16-10, 1000 ms, o piloto adiou a segunda chamada
por EXTRA_CALL_BUDGET; na matriz final ela coube. A ROI produziu uma observação
parcial com cinco essenciais e classe SEATED, aceita como negativo pelas regras
multiclasse preexistentes. Isso elevou cobertura de decisão de 83,3333% no piloto
a 91,6667% na execução final. Não é recuperação de uma pessoa no chão com cinco
pontos: LYING continua exigindo os oito essenciais. O trace distingue estado
LOW_CONFIDENCE, RTMO_PARTIAL_BODY e elegibilidade da classificação. A diferença
de chamadas/motivos está em `pilot-final-timing-differences.json`.

## Resultados em ritmo real

As 96 transmissões encerraram por EOF sem erro. Aceite por método:

| Método | Aprovadas/24 | Perdas de alvo | Alertas indevidos | Duplicações |
| --- | ---: | ---: | ---: | ---: |
| Referência | 14 | 1 | 0 | 0 |
| V1 | 13 | 0 | 0 | 0 |
| V2 | 17 | 0 | 0 | 0 |
| ROI experimental | 22 | 0 | 0 | 0 |

[Dados das 96 execuções](ESTABILIZACAO_TRANSMISSAO_2026_10_26.csv): chamadas
por caminho/análise, processamento, cadência, idades, intervalos inconclusivos,
aquisição, eventos/latências, CPU/RAM, descartes e aquecimento. As médias/P95 na
tabela são medianas das três estatísticas por execução; máximo é o pior das três.
Não são um P95 combinado ou promessa de tempo real. Cadência significa análises/s.

| Cenário | Método | Chamadas/análise | Processamento médio/P95/máx. (ms) | Cadência | Lacunas >500 ms R1/R2/R3 |
| --- | --- | ---: | ---: | ---: | --- |
| yoga2-01 | Referência | 1,000 | 167,2 / 179,7 / 342,6 | 4,842 | 0 / 0 / 0 |
| yoga2-01 | V1 | 1,000 | 160,4 / 171,7 / 225,5 | 4,842 | 0 / 0 / 0 |
| yoga2-01 | V2 | 1,000 | 162,6 / 175,3 / 238,7 | 4,842 | 0 / 0 / 0 |
| yoga2-01 | ROI experimental | 1,000 | 161,8 / 174,7 / 207,9 | 4,842 | 0 / 0 / 0 |
| yoga2-02 | Referência | 1,438 | 228,4 / 484,0 / 561,3 | 3,885 | 1 / 0 / 4 |
| yoga2-02 | V1 | 1,153 | 179,5 / 323,4 / 376,1 | 4,574 | 0 / 0 / 0 |
| yoga2-02 | V2 | 1,264 | 199,6 / 331,3 / 366,7 | 4,323 | 0 / 0 / 0 |
| yoga2-02 | ROI experimental | 1,123 | 177,7 / 326,7 / 482,2 | 4,637 | 0 / 0 / 0 |
| intake16-03 | Referência | 3,000 | 480,8 / 530,9 / 561,8 | 2,112 | 2 / 15 / 19 |
| intake16-03 | V1 | 1,270 | 210,8 / 347,2 / 509,3 | 4,223 | 1 / 0 / 0 |
| intake16-03 | V2 | 1,290 | 214,8 / 349,2 / 371,9 | 4,155 | 0 / 0 / 0 |
| intake16-03 | ROI experimental | 1,270 | 206,0 / 337,3 / 352,6 | 4,292 | 0 / 0 / 0 |
| intake16-15 | Referência | 4,000 | 612,6 / 692,3 / 837,9 | 1,684 | 13 / 9 / 11 |
| intake16-15 | V1 | 1,333 | 215,6 / 351,4 / 359,9 | 4,145 | 0 / 0 / 0 |
| intake16-15 | V2 | 1,958 | 312,3 / 366,2 / 389,6 | 3,238 | 0 / 0 / 0 |
| intake16-15 | ROI experimental | 2,000 | 318,2 / 357,0 / 534,5 | 3,238 | 0 / 1 / 0 |
| intake16-10 | Referência | 1,348 | 210,2 / 345,4 / 572,9 | 4,435 | 0 / 0 / 2 |
| intake16-10 | V1 | 1,208 | 192,3 / 338,4 / 362,4 | 4,637 | 0 / 0 / 0 |
| intake16-10 | V2 | 1,304 | 212,0 / 351,0 / 418,3 | 4,435 | 0 / 0 / 0 |
| intake16-10 | ROI experimental | 1,261 | 211,9 / 360,9 / 459,6 | 4,435 | 0 / 0 / 0 |
| cauca-08 | Referência | 1,196 | 194,6 / 342,4 / 736,1 | 4,292 | 1 / 1 / 2 |
| cauca-08 | V1 | 1,094 | 183,9 / 346,1 / 393,8 | 4,549 | 0 / 0 / 0 |
| cauca-08 | V2 | 1,115 | 187,0 / 353,2 / 390,8 | 4,549 | 0 / 0 / 0 |
| cauca-08 | ROI experimental | 1,132 | 185,6 / 351,8 / 486,4 | 4,464 | 0 / 0 / 0 |
| cauca-11 | Referência | 1,152 | 193,6 / 355,2 / 373,6 | 4,348 | 0 / 0 / 0 |
| cauca-11 | V1 | 1,122 | 181,6 / 332,5 / 414,4 | 4,541 | 0 / 0 / 0 |
| cauca-11 | V2 | 1,128 | 187,8 / 351,7 / 516,1 | 4,444 | 0 / 0 / 0 |
| cauca-11 | ROI experimental | 1,149 | 206,5 / 374,9 / 725349,6 | 4,444 | 0 / 0 / 0 |
| cauca-12 | Referência | 1,738 | 295,0 / 700,9 / 1054,2 | 3,154 | 5 / 5 / 6 |
| cauca-12 | V1 | 1,291 | 215,6 / 355,9 / 576,3 | 4,154 | 1 / 0 / 0 |
| cauca-12 | V2 | 1,440 | 244,9 / 362,2 / 382,5 | 3,769 | 0 / 0 / 0 |
| cauca-12 | ROI experimental | 1,451 | 232,7 / 353,8 / 384,2 | 3,923 | 0 / 0 / 0 |

Cobertura por repetição, aplicada sem arredondar o gate de 80%:

| Cenário | Referência R1/R2/R3 (%) | V1 R1/R2/R3 (%) | V2 R1/R2/R3 (%) | ROI R1/R2/R3 (%) | ROI aprovadas |
| --- | --- | --- | --- | --- | ---: |
| yoga2-01 | 100,00 / 100,00 / 100,00 | 100,00 / 100,00 / 100,00 | 100,00 / 100,00 / 100,00 | 100,00 / 100,00 / 100,00 | 3/3 |
| yoga2-02 | 96,49 / 100,00 / 86,97 | 93,23 / 93,98 / 92,73 | 91,73 / 85,71 / 90,73 | 100,00 / 100,00 / 100,00 | 3/3 |
| intake16-03 | 92,92 / 27,79 / 18,80 | 93,19 / 98,64 / 98,37 | 97,82 / 98,64 / 98,37 | 98,09 / 97,28 / 98,64 | 3/3 |
| intake16-15 | 0,00 / 23,83 / 6,22 | 100,00 / 100,00 / 100,00 | 100,00 / 100,00 / 100,00 | 100,00 / 92,75 / 100,00 | 3/3 |
| intake16-10 | 89,52 / 91,13 / 67,74 | 77,42 / 73,39 / 73,39 | 73,39 / 78,23 / 70,97 | 80,65 / 87,90 / 87,90 | 3/3 |
| cauca-08 | 87,55 / 81,97 / 76,82 | 62,66 / 79,83 / 81,55 | 80,69 / 76,82 / 85,41 | 85,84 / 81,12 / 83,26 | 3/3 |
| cauca-11 | 88,41 / 88,41 / 86,47 | 67,63 / 69,08 / 78,74 | 100,00 / 92,27 / 91,79 | 100,00 / 95,65 / 91,79 | 3/3 |
| cauca-12 | 60,77 / 63,46 / 59,62 | 58,85 / 62,69 / 62,69 | 61,54 / 64,23 / 60,77 | 84,23 / 72,69 / 76,54 | 1/3 |

No vazio previamente anotado, a tabela usa cobertura de captura, mantendo
cobertura de pose zero. Isso não transforma NO_POSE em reconhecimento de vazio.
ROI falhou em cauca-12 nas repetições 2 e 3; não há aprovação por média global.

Latências dos eventos desde o começo do trecho anotado, em mídia:

| Cenário | Referência R1/R2/R3 (ms) | V1 (ms) | V2 (ms) | ROI (ms) |
| --- | --- | --- | --- | --- |
| yoga2-01 | 2035 / 2169 / 2069 | 2035 / 2035 / 2035 | 2069 / 2069 / 2035 | 2035 / 2035 / 2035 |
| yoga2-02 | 2120 / 2040 / 2320 | 3920 / 2120 / 3120 | 3880 / 4640 / 3760 | 2000 / 2040 / 2120 |
| intake16-03 | 2200 / 2160 / sem evento | 2240 / 2320 / 2360 | 2400 / 2320 / 2360 | 2440 / 2480 / 2320 |

Na ROI, a latência técnica até a decisão (offset + idade do frame) foi:

| Cenário | Emissões | Mídia: média/P95/máx. (ms) | Até decisão: média/P95/máx. (ms) |
| --- | ---: | ---: | ---: |
| yoga2-01 | 3/3 | 2035,0 / 2035,0 / 2035,0 | 2234,3 / 2248,4 / 2250,0 |
| yoga2-02 | 3/3 | 2053,3 / 2112,0 / 2120,0 | 2245,0 / 2306,7 / 2313,0 |
| intake16-03 | 3/3 | 2413,3 / 2476,0 / 2480,0 | 2604,0 / 2680,1 / 2688,0 |

São três emissões por cenário, sem inferir generalização estatística desse N.
Não foi medido tempo até o painel por estes executores isolados; persistência
e contratos são verificados separadamente. A referência perdeu o alvo caro R3
e perdeu cobertura em R2 apesar do evento; todas as falhas foram preservadas.

| ROI experimental | Idade no início P95/máx. (ms) | Idade na decisão P95/máx. (ms) | CPU um núcleo=100% / pico MiB | Inconclusivo R1/R2/R3 (ms) |
| --- | ---: | ---: | ---: | --- |
| yoga2-01 | 45,9 / 212,0 | 205,0 / 383,0 | 358,0 / 254,8 | 0 / 0 / 0 |
| yoga2-02 | 48,4 / 196,0 | 354,1 / 496,0 | 343,9 / 242,1 | 0 / 0 / 0 |
| intake16-03 | 53,4 / 210,0 | 374,2 / 387,0 | 391,2 / 278,6 | 280 / 400 / 200 |
| intake16-15 | 55,5 / 233,0 | 405,0 / 576,0 | 424,3 / 271,8 | 7720 / 7720 / 7720 |
| intake16-10 | 55,3 / 119,0 | 402,9 / 485,0 | 382,6 / 266,9 | 960 / 600 / 600 |
| cauca-08 | 56,0 / 225,0 | 388,0 / 534,0 | 366,3 / 233,9 | 1650 / 2200 / 1950 |
| cauca-11 | 64,1 / 196,0 | 398,9 / 725381,0 | 366,5 / 236,0 | 0 / 450 / 850 |
| cauca-12 | 63,0 / 219,0 | 408,3 / 547,0 | 377,4 / 237,0 | 2050 / 3550 / 3050 |

Períodos inconclusivos são intervalos entre observações sem duas extremidades
elegíveis ou com lacuna >500 ms. Não descrevem um estado físico confirmado.
No vazio conhecido, a ausência de pose continua desconhecida na percepção.
Prefixos/sufixos, transições e aquisição/perda/reaquisição estão em analysis.json
e acquisition-audit.json; não foram cortados para medir só o trecho estável.
Inventários antes/depois registram carga do desktop. Variação do notebook
permanece uma limitação; nenhuma execução desfavorável foi descartada.

Em yoga2-02, a redução do custo médio por análise da ROI versus referência, por rodada, foi 26,38% / 22,21% / 18,16%. Chamadas reais estão no CSV; não é uma previsão contrafactual de chamadas economizadas em cada frame.

Em intake16-03, a redução do custo médio por análise da ROI versus referência, por rodada, foi 56,76% / 57,16% / 56,75%. Chamadas reais estão no CSV; não é uma previsão contrafactual de chamadas economizadas em cada frame.

Em intake16-15, a redução do custo médio por análise da ROI versus referência, por rodada, foi 49,80% / 44,79% / 51,40%. Chamadas reais estão no CSV; não é uma previsão contrafactual de chamadas economizadas em cada frame.

Economia por análise não significa a mesma redução no custo de toda a sessão:
a ROI observa mais frames. No alvo caro, chamadas totais foram 102/96/93 na
referência e 82/82/80 na ROI; CPU total foi 64,92/66,89/65,98 s contra
55,97/60,95/61,17 s. No vazio, CPU da ROI ficou 38,33/34,78/37,41 s, contra
36,31/38,70/38,58 s da referência: a primeira rodada consumiu mais CPU total.
O ganho principal é custo por análise e maior observabilidade dentro do mesmo
tempo de conteúdo, sem promessa de economia uniforme de energia.

## Regressão completa e frames auditados

144 execuções finais novas, 36 por método, todas as anotações anteriores
preservadas. [CSV dos 144 resultados](ESTABILIZACAO_REGRESSAO_2026_10_26.csv).

| Método | Aprovados/36 | Eventos | Alertas indevidos | Duplicações | Negativos inconclusivos |
| --- | ---: | ---: | ---: | ---: | --- |
| Referência | 30 | 12 | 0 | 0 | cauca-10, chair08-01 |
| V1 | 26 | 12 | 0 | 0 | intake16-10, cauca-08, cauca-10, cauca-11, cauca-12, chair08-01 |
| V2 | 29 | 12 | 0 | 0 | cauca-10, cauca-12, chair08-01 |
| ROI experimental | 27 | 12 | 0 | 0 | intake16-16, cauca-08, cauca-10, chair08-01 |

Os quatro controles anteriormente regredidos:

| Caso | Referência (%) | V1 (%) | V2 (%) | ROI (%) | ROI versus referência (p.p.) | Aceite ROI |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| intake16-10 | 91,6667 | 66,6667 | 83,3333 | 91,6667 | 0,0000 | PASS |
| cauca-08 | 81,0345 | 77,5862 | 81,0345 | 79,3103 | -1,7241 | INCONCLUSIVE |
| cauca-11 | 96,0784 | 72,5490 | 92,1569 | 96,0784 | 0,0000 | PASS |
| cauca-12 | 80,0000 | 43,0769 | 70,7692 | 81,5385 | 1,5385 | PASS |

Latência dos alvos com evento, desde o início humano anotado, sem deslocar
timestamps ou relabelar tipos para favorecer o resultado:

| Caso | Referência (ms) | V1 (ms) | V2 (ms) | ROI (ms) |
| --- | ---: | ---: | ---: | ---: |
| yoga2-01 | 2002 | 2002 | 2002 | 2002 |
| yoga2-02 | 2000 | 2000 | 3800 | 2000 |
| intake16-01 | 2000 | 2000 | 2000 | 2000 |
| intake16-02 | 2000 | 2000 | 2000 | 2000 |
| intake16-03 | 2000 | 2200 | 2200 | 2200 |
| intake16-04 | 2000 | 2000 | 2000 | 2000 |
| intake16-05 | 2000 | 2000 | 2000 | 2000 |
| intake16-06 | 2000 | 2000 | 2000 | 2000 |
| cauca-01 | 1000 | 1200 | 1200 | 1000 |
| cauca-02 | 2200 | 2200 | 2200 | 2200 |
| cauca-03 | 2200 | 2000 | 2200 | 2200 |
| cauca-04 | 2600 | 3000 | 3000 | 4000 |

Todas as quedas numéricas de cobertura da ROI versus referência, mesmo com PASS:

| Caso | Referência (%) | ROI (%) | Diferença (p.p.) | Aceite antes → depois |
| --- | ---: | ---: | ---: | --- |
| intake16-03 | 100,0000 | 98,6301 | -1,3699 | aprovado → aprovado |
| intake16-12 | 93,4783 | 86,9565 | -6,5217 | aprovado → aprovado |
| intake16-16 | 90,1961 | 70,5882 | -19,6078 | aprovado → não aprovado |
| cauca-04 | 92,3077 | 75,0000 | -17,3077 | aprovado → não aprovado |
| cauca-08 | 81,0345 | 79,3103 | -1,7241 | aprovado → não aprovado |
| floor05 | 37,9121 | 31,0440 | -6,8681 | não aprovado → não aprovado |
| floor07 | 32,1656 | 16,2420 | -15,9236 | não aprovado → não aprovado |

Antes aprovados que perderam aceite na ROI: intake16-16, cauca-04, cauca-08. Divergências de quantidade/tipo de evento: cauca-01.

As quatro perdas históricas não foram removidas:

| Caso | Referência: cobertura/eventos | V1 | V2 | ROI |
| --- | --- | --- | --- | --- |
| floor03 | 41,4835% / 0 | 41,4835% / 0 | 41,4835% / 0 | 41,4835% / 0 |
| floor05 | 37,9121% / 0 | 37,9121% / 0 | 37,9121% / 0 | 31,0440% / 0 |
| floor07 | 32,1656% / 0 | 12,1019% / 0 | 20,3822% / 0 | 16,2420% / 0 |
| controlled-lying | 11,1111% / 0 | 25,0000% / 0 | 11,1111% / 0 | 11,1111% / 0 |

Os controles já inconclusivos cauca-10 e chair08-01 também permanecem na
matriz. A precisão de POSSIBLE_FALL continua separada da postura de chão;
esses resultados não são recall de acidentes reais nem avaliação independente.

Nos mesmos timestamps, os quatro métodos foram confrontados pelo trace da
execução completa. Resultados em final-seven-audit.json; não são resultados de
uma política que conhece antecipadamente o vencedor contrafactual.

| Cenário / ms | Referência: essenciais/elegível | V1 | V2 | ROI | Classe ROI |
| --- | --- | --- | --- | --- | --- |
| intake16-10 / 1200 | 8 / sim | 0 / não | 0 / não | 8 / sim | SEATED |
| cauca-11 / 5000 | 8 / sim | 0 / não | 0 / não | 8 / sim | KNEELING_OR_CROUCHING |
| cauca-12 / 2400 | 8 / sim | 0 / não | 0 / não | 8 / sim | KNEELING_OR_CROUCHING |
| cauca-12 / 2800 | 8 / sim | 0 / não | 0 / não | 0 / não | NO_PERSON_DETECTED |
| cauca-12 / 3600 | 8 / sim | 0 / não | 0 / não | 8 / sim | KNEELING_OR_CROUCHING |
| cauca-12 / 12400 | 8 / sim | 0 / não | 0 / não | 7 / sim | KNEELING_OR_CROUCHING |
| cauca-12 / 13000 | 8 / sim | 0 / não | 0 / não | 8 / sim | LYING |

A ROI produziu oito essenciais em 5/7 e decisão elegível em 6/7. Em 12400 ms
há sete essenciais e classificação negativa parcial, permitida pelas regras
existentes; isso não atende evidência corporal de pessoa no chão. Em 2800 ms
continuou NO_POSE. Em 13000 ms a classe LYING ocorre em controle anotado
negativo, também observada na alternativa da referência; não houve alerta
persistente. Esses fatos impedem chamar todos os seis elegíveis de acertos.

Na transmissão técnica da ROI, 133 análises começaram em reaquisição e todas
começaram por ORIGINAL. Foram registradas 22 reaquisições de oito essenciais;
o alvo caro levou 280/400/200 ms à primeira pose útil. Os outros cenários com
pessoa começaram com oito essenciais em 0 ms; no vazio não houve aquisição.
As transições, perdas e ciclos inconclusivos estão em acquisition-audit.json.
O limite de duas chamadas foi conferido por análise; não se contaram tentativas
puladas como inferências nem se reutilizou evidência antiga.

## Verificações executadas

Os sete novos testes públicos protegem timestamp exato, ausência de aproximação,
rejeição de webcam antes de abrir fonte/modelo, limites de repetição e manifesto
estrito, inclusive rejeição de bool/float como timestamp. Nove testes privados
do artefato experimental verificam dados atuais, prioridade canônica, teto de
chamadas/orçamento, invalidação, múltiplas pessoas, ausência explícita e
restauração geométrica da ROI. Esses testes sintéticos não provam reconhecimento.

Após `. ./scripts/activate.ps1`, comandos realmente executados:

| Comando | Resultado |
| --- | --- |
| `uv run --offline --project services/edge --frozen python scripts/validation/audit-rtmo-recovery.py --manifest .local/detector-evolution/stabilization-ce12cde8-31ee-4665-9727-c5f1da1111d5/seven-frame-manifest.json --output .local/detector-evolution/stabilization-ce12cde8-31ee-4665-9727-c5f1da1111d5/public-auditor-proof --repeats 3` | Sete frames exatos, 126 inferências, sem câmera/HTTP; hashes iguais à reprodução auxiliar |
| `uv run --offline --project services/edge --frozen python .local/detector-evolution/compare-cheap-localization.py` | 39 HOG e ROI de 25%/50% em 13 frames; localização insuficiente, sem integração |
| `uv run --offline --project services/edge --frozen python .local/detector-evolution/run-context-pilot.py A_CURRENT_SIGNALS` | Sete arquivos, cinco PASS e duas regressões |
| Mesmo comando, `C_BOUNDED_CONTEXT` | Quatro PASS e três regressões |
| Mesmo comando, `B_CURRENT_ROI` | Seis PASS, cauca-08 abaixo do gate |
| Mesmo comando, `B_BOUNDED_ROI` | Quatro PASS, três controles abaixo do gate |
| `uv run --offline --project services/edge --frozen python .local/detector-evolution/compare-stabilization.py` | 96 transmissões novas, todas EOF/exit 0; aceites perceptuais separados |
| `uv run --offline --project services/edge --frozen python .local/detector-evolution/compare-stabilization-functional.py` | 144 arquivos finais, ordem alternada, todos exit 0; 30/26/29/27 aprovados |
| `uv run --offline --project services/edge --frozen pytest services/edge/tests -q` | 416 passaram, `RADAR_TEST_GUI=1`, GUI sintética sem captura |
| `uv run --offline --project services/edge --frozen pytest .local/detector-evolution/test_stabilization_experiment.py -q` | Nove passaram, artefato congelado da ROI |
| `uv run --offline --project services/edge --frozen ruff check services/edge scripts/validation/benchmark-stream.py scripts/validation/audit-rtmo-recovery.py` | Passou |
| Mesmo escopo, `ruff format --check` | Passou |
| `pnpm.cmd lint` | Passou |
| `pnpm.cmd typecheck` | Passou |
| `pnpm.cmd build` | Passou |
| `pnpm.cmd --filter @radar/contracts test` | 104 passaram |
| `pnpm.cmd test:api` | 159 passaram, PostgreSQL exclusivo |
| `pnpm.cmd test:e2e` | 20 passaram, desktop/mobile em serviços exclusivos |
| `pnpm.cmd check:edge` | Imports reais, um provedor OpenCV, nenhuma câmera aberta |
| `uv run --offline --project services/edge --frozen python .local/detector-evolution/validate-stabilization-outboxes.py` | 48 eventos nativos persistidos, 12 únicos por método, contratos REPLAY válidos; leitura SQLite somente leitura |
| `uv run --offline --project services/edge --frozen python .local/detector-evolution/check-stabilization-preservation.py` | 34 configurações/vídeos e quatro cenários completos com pesos/classificador/calibrações inalterados; referência/V1/V2 byte a byte iguais |
| `node .local/detector-evolution/check-stabilization-source.mjs` | Mesmos 210 arquivos de fonte, hash e HEAD congelados |

As onze verificações de engenharia foram disparadas por
`powershell -NoProfile -File .local/detector-evolution/check-stabilization.ps1`;
logs e resultados estão em `checks/`. Análises: `analyze-stabilization-comparison.py`,
`supplement-stabilization-audit.py` e renderizadores preservados na mesma pasta.
Nenhum peso ou dependência foi instalado. A alteração gerada pelo build nas duas
importações de `apps/web/next-env.d.ts` foi restaurada ao conteúdo inicial.

Persistência de incidentes, idempotência e contratos foram verificados nos
testes isolados da API/E2E, incluindo fluxo Python e painel. As novas filas
nativas foram conferidas separadamente; seus eventos não foram enviados ao
banco da demonstração nem apresentados como uma nova conferência humana do painel.
Nenhuma validação física foi realizada. Engenharia passar não aprova percepção.

## Decisão e menor investigação seguinte

| Critério obrigatório | Resultado da ROI |
| --- | --- |
| Quatro controles regredidos recuperados em arquivo completo | Falhou: cauca-08 em 79,3103%; os outros três passaram |
| Nenhum caso antes aprovado perder aceite | Falhou: intake16-16, cauca-04 e cauca-08 |
| Cobertura/latência nas 24 transmissões | Falhou: 22/24; cauca-12 R2/R3 em 72,6923%/76,5385% |
| Preservação dos 12 eventos e tipos | Quantidade preservada, tipo mudou em cauca-01: PERSON_ON_FLOOR → POSSIBLE_FALL |
| Sem novo alerta indevido ou duplicação | Passou neste conjunto: zero em ambos |
| Duas chamadas e observações atuais | Passou nos traces/testes; zero omissões de ORIGINAL nas 133 reaquisições |
| Benefício computacional mensurável | Demonstrado por análise em caminhos caros, sem ganho uniforme de CPU total |
| Sem nomes, rótulos, futuro ou critérios alterados | Preservado; experimento identificado por artefato/hash, avaliação separada |
| Preparar teste físico | Não: vários critérios obrigatórios falharam |

**O que causava as perdas?** ORIGINAL rejeitou a pessoa abaixo de 0,7, apesar
de propostas com vários pontos; a recuperação útil variou com contexto/orientação
e a segunda chamada frequentemente foi alocada a outro caminho. Os scores
aceitos também não garantiram pose/classificação estáveis: houve discordância
de dezenas de pixels e classes distintas no mesmo frame. Não se demonstrou que
duas chamadas sejam matematicamente insuficientes: há alternativa útil nos sete,
mas ela não é conhecida antecipadamente pela política.

**O que foi corrigido?** A entrega tornou o diagnóstico reproduzível, estrito
quanto a fonte/timestamp e separado da decisão temporal. No experimento,
recuperaram-se cinco dos sete com corpo completo e seis decisões elegíveis;
o segundo yoga ficou em 100% nas três transmissões e com emissão em
2000/2040/2120 ms. Isso não é uma correção geral adotada no worker. Não houve
alteração da referência, V1/V2 ou parâmetros para aparentar melhora.

**O que permanece?** As quatro perdas históricas, o frame de 2800 ms sem pose,
o frame parcial de 12400 ms, a classe LYING num negativo em 13000 ms e as
regressões completas/técnicas acima. Na ROI, quatro negativos ficaram
inconclusivos e um positivo que passava perdeu cobertura. A mudança de tipo em
cauca-01 ocorreu num material descrito como queda encenada, com início anotado
incerto até 500 ms; não foi reclassificada para esconder a diferença, nem usada
para alegar maior precisão geral de quedas. Quantidade de eventos não equivale
a comportamento preservado.

**Em que foi superior?** 22/24 transmissões contra 14/24 da referência, 13/24 V1
e 17/24 V2; menor custo por análise nos cenários caros e melhor cobertura/latência
na sala. Porém, a matriz completa teve 27/36, pior que referência 30/36 e V2
29/36. Sete quedas numéricas de cobertura estão publicadas, inclusive em casos
que mantiveram PASS. Não existe superioridade global demonstrada.

**O custo é adequado?** O teto de duas chamadas foi preservado e ajudou a
cadência. Ainda não há margem/qualidade suficientes para declarar funcionamento
confiável em todos os cenários: cauca-12 perdeu cobertura sem lacuna >500 ms
nas três transmissões. O bloqueio não é apenas fila antiga ou atraso da captura;
faltam observações elegíveis com os caminhos selecionados. Não foi demonstrada
inviabilidade universal de uma passagem; o cenário de uma passagem manteve
100% em três repetições. Também não se prometem 30 FPS ou estabilidade física.

**Próxima investigação mínima:** antes de outro candidato ou webcam, medir se a
geometria corporal completa da proposta ORIGINAL atual, além de contagem/caixa,
prediz qual recuperação precisa ser executada. Fazer um experimento pequeno e
congelado nos sete frames, nos positivos difíceis e no vazio já existentes,
avaliando separadamente precisão anatômica/classes discordantes. Um descritor
de proposta pode orientar trabalho, mas nunca aceitar pessoa/pose sub-limiar.
Qualquer regra precisa depois recuperar os três casos regredidos e passar a
matriz completa. Se esses sinais não forem preditivos, comparar uma alternativa
de percepção/localização licenciada em custo e reconhecimento, como hipótese
arquitetural separada; não insistir em margens de ROI ou trocar contratos para
aprovar. Não há motivo experimental para repetir um ensaio físico agora.

**Decisão:** rejeitar integração da ROI, manter `REFERENCE_4_SPIN +
RTMO_ADAPTIVE_V3`, preservar todos os resultados e encerrar a rodada sem promoção.
Nenhuma política nova foi adicionada ao seletor normal do worker. O núcleo
continua em desenvolvimento; o MVP não foi aprovado integralmente.

## Reprodução

O auditor versionado e seu comando estão no [diagnóstico](DIAGNOSTICO_RECUPERACAO_2026_10_26.md).
Para a comparação exata desta bancada, após ativar `scripts/activate.ps1`, os
auxiliares preservados são `compare-stabilization.py`,
`benchmark-stabilization-job.py`, `compare-stabilization-functional.py` e
`functional-stabilization-job.py`, dentro de
`.local/detector-evolution/`. Eles exigem os materiais privados autorizados.
Saídas completas e traces ficam na raiz da rodada. Não publicar vídeos,
pesos, credenciais ou coordenadas corporais.

Não houve webcam, gravação, câmera IP, alteração de banco/credenciais,
commit, push, deploy, aprovação integral do MVP ou preparação de ensaio físico.
