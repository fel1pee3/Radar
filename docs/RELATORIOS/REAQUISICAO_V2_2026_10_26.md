# Reaquisição canônica do RTMO — 26/10/2026

**Rodada concluída; V2 não elegível para teste físico e referência preservada.**
Omissão de ORIGINAL corrigida e 16/16 frames recuperados, mas um dos quatro
controles continua inconclusivo em arquivo completo e o V2 passou somente
16/24 transmissões técnicas. Não houve promoção do candidato.
Nenhuma webcam aberta ou gravação habilitada. Escopo desta rodada:
corrigir a omissão de ORIGINAL durante a reaquisição, medir as perdas restantes
e verificar custo e observabilidade juntos, sem alterar os critérios.

## Preservação e reprodução

Leituras: AGENTS, README, STATUS,
[relatório do V1](RECUPERACAO_ADAPTATIVA_2026_10_26.md), código do estimador,
busca, LIVE e executor técnico. Início em árvore limpa, commit
`e2759ddf228ec698fe11141d85bdbc28a86c3da9`, fonte de 206 arquivos SHA-256
`816cb569d26d8724660b08f0d927d4c67d19c0231379c8f16603ab35ad0a2cfd`.
Snapshot inicial SHA-256
`82708678f612842512bdcee2bbc3d81a66b278b3a460e2d7f6edfa5049515be5`.

Raiz privada: `.local/detector-evolution/reacquisition-9ddcb23e-7403-4668-b0db-72dd11fd66d6/`;
ponteiro `.local/detector-evolution/reacquisition-current.json`.
Referência `REFERENCE_4_SPIN + RTMO_ADAPTIVE_V3` e `RTMO_PREFERRED_V1` foram
preservados separadamente em `reference/` e `v1/`, com código, protocolos,
auditoria e resultados anteriores. `rtmo.py` e `preferred_rtmo.py` permanecem
byte a byte iguais ao início. Nenhuma configuração existente foi migrada.

Modelo e classificador continuam, respectivamente, SHA-256
`d0703d40d19f3921da51ae725402d5fdae4d2478c7442072d3101bd396f370d8` e
`40d01401851f24cd8c815557970f0dcf42877707afbba38d521ebfa87bd5bd19`.
Pesos, polígonos, instalação/contexto, limiares e temporizadores não foram alterados.

O V1 foi reproduzido nos quatro arquivos completos, com saídas novas:
66,67%; 77,59%; 72,55%; 43,08% de cobertura, nos mesmos controles da auditoria.
Também foram decodificados e inferidos novamente os 16 frames exatos nos quais
o V1 omitia ORIGINAL e a referência encontrava os oito essenciais: **16/16**
voltaram a produzir os oito pontos em ORIGINAL, sem buscar o frame mais próximo
ou mudar timestamps. Evidência em `reproduced-original-evidence.json`.

## Política do V2

Arquivos de implementação: novo `services/edge/src/radar_edge/reacquiring_rtmo.py`,
registro opt-in em `config.py` e `estimator.py`, seletor no
`scripts/validation/benchmark-stream.py` e testes em
`services/edge/tests/test_reacquiring_rtmo.py`. README, STATUS, decisão D56,
guia de uso e índice dos relatórios recebem o resultado; os dois CSVs publicados
contêm métricas, sem vídeo, coordenadas corporais, credencial ou peso.

`RTMO_PREFERRED_V2` é opt-in, implementado em `reacquiring_rtmo.py`, reutilizando
as transformações do V1 sem alterar seu código. Durante acompanhamento estável,
uma orientação bem-sucedida pode continuar primeiro entre inspeções canônicas.
Quando não há preferência válida, **cada frame analisado começa por ORIGINAL**.
Uma pose atual com os oito essenciais encerra a busca. Sem pose suficiente, o
orçamento restante atende uma recuperação selecionada pela busca finita.

Falha da preferência invalida o acompanhamento. ORIGINAL é tentado no mesmo
frame se couber; quando a chamada adicional é impedida, a saída registra
`originalDeferredAfterFailure` e `nextAnalysisPriority: ORIGINAL`. A próxima
análise não pula o original para executar outra alternativa.

O recorte de proposta usa somente a caixa calculada pelo ORIGINAL atual. Um
sucesso desse recorte lembra o fluxo ORIGINAL + recorte atual, sem guardar ROI,
imagem ou articulações antigas. Recorte que falha não pode impedir indefinidamente
as outras recuperações; uma pose parcial em ORIGINAL também pode justificar o
recorte atual. As coordenadas são restauradas pelos mesmos métodos já testados.

| Limite preservado | Valor |
| --- | ---: |
| Chamadas por análise | Até 2 |
| Iniciar chamada adicional | Antes de 220 ms |
| Prazo de inspeção canônica no acompanhamento | 800 ms |
| Validade da preferência | 1600 ms |
| Lacuna de entrada que invalida preferência | Mais de 500 ms |
| Busca por ciclo | Até 1600 ms de mídia ou 8 análises |

Os prazos são verificados entre observações; uma chamada nativa em andamento
não é interrompida. Reconexão, interrupção, pausa, geometria, expiração e busca
esgotada mantêm invalidação. Inspeção que encontra duas pessoas preserva a
ambiguidade. Cada resultado vem de inferência real no frame atual; NO_POSE não
confirma ambiente vazio nem prolonga evidência anterior.

Nenhuma alteração em pessoa/NMS, qualidade articular, oito essenciais,
classificador, contexto, permanência de 2000 ms, cobertura de 80%, lacuna máxima
de 500 ms, rearme, timestamps ou denominadores. Nenhuma decisão usa nome de
arquivo, rótulo esperado ou conhecimento da atividade.

## Investigação isolada antes da comparação final

O piloto canônico inicial recuperou três controles para o aceite, mas `cauca-12`
continuou em 70,77%. Inspecionadas as demais perdas: há frames em que ORIGINAL
continua sem pose e o recorte de proposta ou CENTER_80 é necessário. Executar
somente ORIGINAL não resolve esses casos.

Foi avaliada separadamente uma prioridade recente de recuperação, limitada pelo
lease já existente, sem mudar os valores acima. Essa variação levou `cauca-12`
a 69,23% e foi rejeitada. Fontes, testes e resultados estão em
`pilot-canonical-only/` e `pilot-bounded-hint/`. O candidato da comparação final
é o canônico inicial; nenhum parâmetro foi ajustado para aprovar os controles.

## Protocolo da comparação final

Fonte congelada, 208 arquivos, SHA-256
`8625d5671810ede26fc7a80b466138b2566d9432dec68eb3b57dc0565ab7f4fe`.
`candidate-source.json` registra snapshot e hash de `protocol.frozen.json`.
Todas as execuções de desempenho são novas: referência, V1 e V2, em oito
cenários e três repetições por método, ordem alternada, sem inferências concorrentes.
Prévia desligada, processo novo e uma inferência cinza sintética de aquecimento
excluída das observações. A memória começa vazia no primeiro frame do arquivo.

O executor a 1× usa inferência real, agendamento LIVE e slot de frame recente;
sobrecarga gera descartes, sem repetir frames ou alongar o vídeo. As fontes e
eventos são REPLAY/TEST em filas isoladas, sem HTTP, credencial, snapshot, status
global da câmera ou abertura de dispositivo. Isso não é prova de webcam.
Inventário de processos antes/depois registra interferência do desktop.

Os quatro cenários anteriores e `intake16-10`, `cauca-08`, `cauca-11`, `cauca-12`
foram incluídos. Arquivo completo e transmissão técnica são avaliações distintas.
Os materiais já são desenvolvimento/regressão; não são avaliação independente.
Ambiente: Windows 11 Pro 10.0.26200, Ryzen 5 5625U, seis núcleos/12 processadores
lógicos, 15,41 GiB de RAM visível, Python 3.12.15 e ONNX Runtime 1.23.2 CPU,
quatro threads intra-op; versões travadas preservadas. Nenhum dispositivo de
câmera foi acessado; estes resultados não atestam hardware de captura.

## Resultado em ritmo real — 72 transmissões técnicas

As três rodadas encerraram por EOF sem erro. A tabela mostra a mediana das
médias/P95 por execução; máximo é o pior valor das três. Cadência é análise/s
de mídia, não FPS de captura. Inclui aquisição inicial, falhas e reaquisição.
Os dados individuais, chamadas por caminho, idades, CPU/RAM e latências estão
no [CSV das 72 execuções](COMPARACAO_REAQUISICAO_V2_2026_10_26.csv).

| Caso | Método | Chamadas/análise | Processamento médio/P95/máx. (ms) | Cadência | Lacunas >500 ms, R1/R2/R3 |
| --- | --- | ---: | ---: | ---: | --- |
| yoga2-01 | Referência | 1,000 | 170,7 / 191,1 / 260,4 | 4,842 | 0 / 0 / 0 |
| yoga2-01 | V1 | 1,000 | 168,0 / 191,1 / 490,4 | 4,842 | 0 / 0 / 0 |
| yoga2-01 | V2 | 1,000 | 172,4 / 189,1 / 441,5 | 4,802 | 0 / 0 / 0 |
| yoga2-02 | Referência | 1,390 | 233,4 / 451,9 / 686,3 | 3,885 | 0 / 2 / 5 |
| yoga2-02 | V1 | 1,147 | 159,3 / 277,1 / 418,2 | 4,637 | 0 / 0 / 0 |
| yoga2-02 | V2 | 1,270 | 192,3 / 333,7 / 494,2 | 4,449 | 0 / 0 / 0 |
| intake16-03 | Referência | 3,000 | 424,9 / 465,9 / 657,7 | 2,384 | 1 / 0 / 22 |
| intake16-03 | V1 | 1,258 | 179,5 / 299,8 / 421,8 | 4,428 | 0 / 0 / 0 |
| intake16-03 | V2 | 1,273 | 227,4 / 367,3 / 535,2 | 4,087 | 0 / 1 / 0 |
| intake16-15 | Referência | 4,000 | 676,9 / 747,2 / 887,7 | 1,554 | 13 / 11 / 10 |
| intake16-15 | V1 | 1,314 | 261,7 / 386,7 / 454,1 | 3,756 | 0 / 0 / 0 |
| intake16-15 | V2 | 1,913 | 334,8 / 393,8 / 450,9 | 2,979 | 0 / 0 / 0 |
| intake16-10 | Referência | 1,409 | 229,7 / 382,2 / 620,9 | 4,234 | 1 / 0 / 1 |
| intake16-10 | V1 | 1,217 | 199,8 / 298,8 / 378,0 | 4,435 | 0 / 0 / 0 |
| intake16-10 | V2 | 1,261 | 215,8 / 360,6 / 396,1 | 4,435 | 0 / 0 / 0 |
| cauca-08 | Referência | 1,180 | 214,0 / 389,5 / 805,9 | 4,206 | 1 / 2 / 2 |
| cauca-08 | V1 | 1,113 | 207,2 / 360,4 / 492,5 | 4,464 | 0 / 0 / 0 |
| cauca-08 | V2 | 1,137 | 222,3 / 393,3 / 439,0 | 4,292 | 0 / 0 / 0 |
| cauca-11 | Referência | 1,152 | 205,9 / 377,3 / 468,8 | 4,348 | 0 / 0 / 0 |
| cauca-11 | V1 | 1,104 | 197,4 / 351,6 / 460,1 | 4,541 | 0 / 0 / 0 |
| cauca-11 | V2 | 1,159 | 202,4 / 359,2 / 422,4 | 4,348 | 0 / 0 / 0 |
| cauca-12 | Referência | 1,574 | 255,9 / 611,9 / 1106,9 | 3,538 | 3 / 4 / 3 |
| cauca-12 | V1 | 1,358 | 225,5 / 354,4 / 509,8 | 4,000 | 0 / 0 / 0 |
| cauca-12 | V2 | 1,412 | 255,5 / 371,1 / 468,9 | 3,615 | 0 / 0 / 0 |

Cobertura decisória por repetição, sem arredondar para aplicar o gate de 80%:

| Caso | Referência, R1/R2/R3 (%) | V1, R1/R2/R3 (%) | V2, R1/R2/R3 (%) | V2 aprovadas |
| --- | --- | --- | --- | ---: |
| yoga2-01 | 100,00 / 100,00 / 100,00 | 100,00 / 100,00 / 100,00 | 100,00 / 100,00 / 100,00 | 3/3 |
| yoga2-02 | 100,00 / 93,23 / 81,45 | 93,73 / 89,47 / 86,97 | 91,73 / 93,73 / 76,69 | 2/3 |
| intake16-03 | 96,46 / 100,00 / 14,71 | 98,37 / 98,64 / 90,19 | 98,37 / 88,28 / 91,55 | 3/3 |
| intake16-15 | 0,00 / 0,00 / 6,22 | 100,00 / 100,00 / 100,00 | 100,00 / 100,00 / 100,00 | 3/3 |
| intake16-10 | 76,61 / 88,71 / 79,03 | 68,55 / 77,42 / 77,42 | 83,06 / 83,87 / 79,03 | 2/3 |
| cauca-08 | 83,26 / 79,83 / 73,82 | 70,39 / 72,53 / 80,69 | 78,54 / 78,97 / 78,97 | 0/3 |
| cauca-11 | 94,69 / 87,44 / 88,41 | 71,98 / 60,87 / 61,84 | 92,27 / 89,86 / 100,00 | 3/3 |
| cauca-12 | 80,77 / 70,77 / 83,08 | 68,46 / 51,15 / 54,62 | 63,46 / 71,54 / 74,23 | 0/3 |

`intake16-15` é o controle previamente anotado como vazio: nessa linha usa-se
cobertura de captura; cobertura de pose é zero nos três métodos. A anotação
humana preexiste à execução. NO_POSE continua inconclusivo sobre ocupação.

Latências de mídia dos alvos positivos; os demais cinco casos não devem gerar alerta:

| Caso | Referência, R1/R2/R3 (ms) | V1, R1/R2/R3 (ms) | V2, R1/R2/R3 (ms) |
| --- | --- | --- | --- |
| yoga2-01 | 2069 / 2069 / 2069 | 2035 / 2035 / 2135 | 2035 / 2035 / 2102 |
| yoga2-02 | 2200 / 2280 / 5400 | 3480 / 2960 / 3280 | 3840 / 3360 / 5040 |
| intake16-03 | 3400 / 2360 / 2160 | 2240 / 2240 / 2400 | 2320 / 2480 / 2680 |

Todos os nove alvos de cada método geraram PERSON_ON_FLOOR, sem alertas nos
cinco controles e sem duplicações. Isso não aprova as execuções com cobertura
insuficiente ou emissão depois de 5000 ms: sala R3 falhou na referência
e no V2; o alvo caro R3 da referência perdeu cobertura apesar de emitir.

| Caso V2 | Idade no início P95/máx. (ms) | Idade na decisão P95/máx. (ms) | CPU (um núcleo=100%) / pico MiB | Períodos inconclusivos R1/R2/R3 (ms) |
| --- | ---: | ---: | ---: | --- |
| yoga2-01 | 47,9 / 148,0 | 224,0 / 456,0 | 384,8 / 253,5 | 0 / 0 / 0 |
| yoga2-02 | 52,5 / 212,0 | 366,0 / 487,0 | 363,8 / 244,9 | 1320 / 1000 / 3720 |
| intake16-03 | 52,1 / 164,0 | 401,0 / 571,0 | 392,9 / 276,8 | 240 / 1720 / 1240 |
| intake16-15 | 56,8 / 170,0 | 418,0 / 514,0 | 422,9 / 272,5 | 7720 / 7720 / 7720 |
| intake16-10 | 55,0 / 165,0 | 385,9 / 540,0 | 419,9 / 267,9 | 840 / 800 / 1040 |
| cauca-08 | 59,9 / 209,0 | 429,9 / 459,0 | 389,8 / 237,4 | 2500 / 2450 / 2450 |
| cauca-11 | 58,1 / 197,0 | 394,6 / 478,0 | 386,0 / 234,4 | 800 / 1050 / 0 |
| cauca-12 | 59,0 / 171,0 | 412,0 / 522,0 | 392,3 / 239,4 | 4750 / 3700 / 3350 |

Período inconclusivo é o intervalo entre análises com uma extremidade sem
qualidade suficiente ou distância >500 ms. Ele não afirma o que havia na
imagem; no vazio conhecido, a pose permanece indisponível. Prefixos/sufixos
sem análise e todos os intervalos/transições constam de `analysis.json` e
`acquisition-audit.json`, sem retirá-los dos arquivos para favorecer o candidato.

A ordem foi alternada, mas o desktop não é um laboratório de carga fixa.
Há variação entre rodadas, inclusive na referência; inventários e custos
ficaram preservados. Nenhuma repetição desfavorável foi descartada.

Em intake16-03, V2 reduziu o custo médio por análise em 55,79% / 43,40% / 56,50% e chamadas/análise em 57,58% / 56,67% / 58,47%, comparado à referência na mesma rodada.

Em intake16-15, V2 reduziu o custo médio por análise em 51,84% / 49,91% / 50,54% e chamadas/análise em 52,59% / 52,17% / 51,04%, comparado à referência na mesma rodada.

O ganho caro foi preservado nas três repetições. Em controles baratos, custo
e cobertura não melhoraram de forma uniforme. A latência adicional após a
mídia inclui a idade do frame na decisão, registrada separadamente no CSV.
Não houve HTTP ou teste de tempo até o painel nesta comparação isolada.

## Auditoria dos mesmos timestamps e regressão

Os mesmos 46 timestamps da auditoria anterior foram confrontados sem deslocar
o frame. A inferência ORIGINAL nativa dos 16 casos omitidos foi reproduzida
antes da comparação final; o fluxo V2 também é avaliado nesses timestamps.
Resultados completos e caminhos por passagem: `same-timestamps-audit.json`.

| Controle | Timestamps auditados | Omitidos com ORIGINAL útil | Esses recuperados pelo V2 | Poses/decisões elegíveis V2 nos timestamps auditados |
| --- | ---: | ---: | ---: | ---: |
| intake16-10 | 4 | 1 | 1 | 3 / 3 |
| cauca-08 | 7 | 2 | 2 | 2 / 2 |
| cauca-11 | 9 | 4 | 4 | 8 / 8 |
| cauca-12 | 26 | 9 | 9 | 15 / 15 |

Nos 24 traces técnicos V2, 174 análises começaram em reaquisição; 0 omitiram ORIGINAL na primeira passagem. Foram registradas 48 reaquisições de oito essenciais após perdas; isso não equivale a confirmar acerto visual em cada quadro.

O alvo caro começou sem pose útil: primeira aquisição em 240/280/280 ms.
As demais cenas com pessoa começaram com oito essenciais no primeiro frame.
No vazio não houve aquisição. `cauca-12` encerrou R1 e R2 ainda sem recuperar
a última perda. Os episódios inteiros, inclusive os não recuperados, estão
em `acquisition-audit.json`.

O trace registra sete adiamentos de chamada adicional e nenhuma omissão de
ORIGINAL após falha da preferência nessa matriz. O caso de orçamento impedir
ORIGINAL é exercitado pelo teste controlado; não foi observado naturalmente
nessas 24 execuções. Maior intervalo observado entre inspeções canônicas:
1000 ms, pois o prazo de 800 ms é verificado na próxima observação, sem
interromper uma chamada nativa nem criar frames intermediários.

Das 46 antigas saídas NO_POSE, 28 viraram observações elegíveis, incluindo os
16 casos de ORIGINAL omitido. Continuam 18 sem observação elegível; em 11 a
referência também falha. Nos outros sete, a referência encontra os oito
essenciais em outra passagem e o V2 continua perdendo:

| Controle / timestamp (ms) | Passagem útil na referência | Tentativas V2 sem pose útil |
| --- | --- | --- |
| intake16-10 / 1200 | CENTER_80, quarta chamada | ORIGINAL + PERSON_PROPOSAL_CROP |
| cauca-11 / 5000 | PERSON_PROPOSAL_CROP, segunda | ORIGINAL + ROTATE_270 |
| cauca-12 / 2400 | CENTER_80, quarta | ORIGINAL + PERSON_PROPOSAL_CROP |
| cauca-12 / 2800 | PERSON_PROPOSAL_CROP, segunda | ORIGINAL + ROTATE_270 |
| cauca-12 / 3600 | PERSON_PROPOSAL_CROP, segunda | ORIGINAL + ROTATE_270 |
| cauca-12 / 12400 | CENTER_80, quarta | ORIGINAL + PERSON_PROPOSAL_CROP |
| cauca-12 / 13000 | ROTATE_270, terceira | ORIGINAL + PERSON_PROPOSAL_CROP |

Isso localiza a falha de seleção dentro do orçamento, sem provar que sejam
sempre necessárias quatro chamadas. A lista preserva inferência, qualidade e
tentativas de cada método; não se atribui toda ausência a uma causa visual não
comprovada.

O piloto já localizara perdas em 1200 ms de `intake16-10`, 5000 ms de
`cauca-11` e 2400/2800/3600/12400 ms de `cauca-12`: a referência precisou de
recorte ou CENTER_80 após ORIGINAL sem pose. Parte foi encontrada na terceira/quarta
passagem; parte encontra o recorte quando o V2 aloca a segunda chamada a uma
rotação. Não foi restabelecida a cascata completa para encobrir o problema.

### Arquivos completos — 36 por método, 108 execuções novas

Mesmos frames/amostragem e anotações da regressão anterior, sem limitar o
arquivo ao trecho estável. Todos os resultados individuais, coberturas e
diferenças constam do [CSV de regressão](REGRESSAO_REAQUISICAO_V2_2026_10_26.csv).

| Método | Aprovados/36 | Eventos | Alertas indevidos | Duplicações | Negativos inconclusivos |
| --- | ---: | ---: | ---: | ---: | --- |
| Referência | 30 | 12 | 0 | 0 | cauca-10, chair08-01 |
| V1 | 26 | 12 | 0 | 0 | intake16-10, cauca-08, cauca-10, cauca-11, cauca-12, chair08-01 |
| V2 | 29 | 12 | 0 | 0 | cauca-10, cauca-12, chair08-01 |

Cobertura individual dos quatro controles que regrediram no V1:

| Controle | Referência (%) | V1 (%) | V2 (%) | V2 versus referência (p.p.) | V2 em arquivo |
| --- | ---: | ---: | ---: | ---: | --- |
| intake16-10 | 91,6667 | 66,6667 | 83,3333 | -8,3333 | PASS |
| cauca-08 | 81,0345 | 77,5862 | 81,0345 | 0,0000 | PASS |
| cauca-11 | 96,0784 | 72,5490 | 92,1569 | -3,9216 | PASS |
| cauca-12 | 80,0000 | 43,0769 | 70,7692 | -9,2308 | INCONCLUSIVE |

Latências dos alvos reconhecidos em arquivo completo, desde o início das
faixas humanas preexistentes (não desde um acidente real):

| Caso | Referência (ms) | V1 (ms) | V2 (ms) |
| --- | ---: | ---: | ---: |
| yoga2-01 | 2002 | 2002 | 2002 |
| yoga2-02 | 2000 | 2000 | 3800 |
| intake16-01 | 2000 | 2000 | 2000 |
| intake16-02 | 2000 | 2000 | 2000 |
| intake16-03 | 2000 | 2200 | 2200 |
| intake16-04 | 2000 | 2000 | 2000 |
| intake16-05 | 2000 | 2000 | 2000 |
| intake16-06 | 2000 | 2000 | 2000 |
| cauca-01 | 1000 | 1200 | 1200 |
| cauca-02 | 2200 | 2200 | 2200 |
| cauca-03 | 2200 | 2000 | 2200 |
| cauca-04 | 2600 | 3000 | 3000 |

Todas as quedas numéricas V2 versus referência, inclusive as que mantêm aprovação:

| Caso | Referência (%) | V2 (%) | Diferença (p.p.) | Aceite antes → depois |
| --- | ---: | ---: | ---: | --- |
| yoga2-02 | 100,0000 | 93,6709 | -6,3291 | aprovado → aprovado |
| intake16-03 | 100,0000 | 98,6301 | -1,3699 | aprovado → aprovado |
| intake16-10 | 91,6667 | 83,3333 | -8,3333 | aprovado → aprovado |
| intake16-11 | 100,0000 | 97,1014 | -2,8986 | aprovado → aprovado |
| intake16-16 | 90,1961 | 86,2745 | -3,9216 | aprovado → aprovado |
| cauca-01 | 89,4737 | 85,9649 | -3,5088 | aprovado → aprovado |
| cauca-04 | 92,3077 | 90,3846 | -1,9231 | aprovado → aprovado |
| cauca-09 | 94,0299 | 92,5373 | -1,4925 | aprovado → aprovado |
| cauca-10 | 65,2778 | 58,3333 | -6,9444 | não aprovado → não aprovado |
| cauca-11 | 96,0784 | 92,1569 | -3,9216 | aprovado → aprovado |
| cauca-12 | 80,0000 | 70,7692 | -9,2308 | aprovado → não aprovado |
| floor07 | 32,1656 | 20,3822 | -11,7834 | não aprovado → não aprovado |

Casos antes aprovados que ficaram sem aceite no V2: cauca-12. Tipos/quantidade de eventos divergentes da referência: nenhum.

As quatro perdas históricas `floor03`, `floor05`, `floor07` e
`controlled-lying` permanecem na matriz, sem retirar seus alvos. Os controles
`cauca-10` e `chair08-01` já inconclusivos também permanecem. As quatro
transições CAUCA continuam com apenas uma POSSIBLE_FALL; as outras três
produzem PERSON_ON_FLOOR. Esses materiais são desenvolvimento/regressão,
sem alegar avaliação independente ou eficácia de acidentes reais.

## Verificações e decisão

Os dez novos testes comportamentais cobrem falha da preferência com retorno
de ORIGINAL, recuperação ainda necessária, recorte que falha sem impedir a
busca, orçamento, interrupção/reconexão/geometria, múltiplas pessoas e busca
esgotada. Observações controladas mudam com o timestamp atual; não são prova
visual. Os testes existentes verificam a restauração de coordenadas das quatro
transformações reutilizadas e a ausência de ROI antiga.

Comandos realmente executados nesta rodada, na raiz após
`. ./scripts/activate.ps1`:

| Comando | Resultado |
| --- | --- |
| `uv run --offline --project services/edge --frozen python .local/detector-evolution/reproduce-reacquisition.py RTMO_PREFERRED_V1` | Quatro arquivos, defeito reproduzido |
| Mesmo comando com `RTMO_PREFERRED_V2` | Piloto dos quatro controles; três PASS, um abaixo do gate |
| `uv run --offline --project services/edge --frozen python .local/detector-evolution/audit-original-and-protocol.py` | 16 frames exatos, 16 poses com oito essenciais em ORIGINAL |
| `uv run --offline --project services/edge --frozen python .local/detector-evolution/compare-reacquisition.py` | 72 transmissões novas, todas EOF/exit 0; aceites perceptuais separados acima |
| `uv run --offline --project services/edge --frozen python .local/detector-evolution/regress-reacquisition.py RTMO_ADAPTIVE_V3` | 36 arquivos, exit 0; 30 aprovados |
| Mesmo comando com `RTMO_PREFERRED_V1` | 36 arquivos, exit 0; 26 aprovados |
| Mesmo comando com `RTMO_PREFERRED_V2` | 36 arquivos, exit 0; 29 aprovados |
| `uv run --offline --project services/edge --frozen pytest services/edge/tests -q` | 409 passaram; `RADAR_TEST_GUI=1`, GUI sintética sem webcam |
| `uv run --offline --project services/edge --frozen ruff check services/edge scripts/validation/benchmark-stream.py` | Passou |
| `uv run --offline --project services/edge --frozen ruff format --check services/edge scripts/validation/benchmark-stream.py` | Passou |
| `pnpm.cmd lint` | Passou |
| `pnpm.cmd typecheck` | Passou |
| `pnpm.cmd build` | Passou |
| `pnpm.cmd --filter @radar/contracts test` | 104 passaram |
| `pnpm.cmd test:api` | 159 passaram, banco exclusivo de testes |
| `pnpm.cmd test:e2e` | 20 passaram, desktop/mobile e serviços exclusivos |
| `pnpm.cmd check:edge` | Imports reais MediaPipe 1.1.1, OpenCV 5.0.0 e ORT 1.23.2; camera_opened=false |
| `uv run --offline --project services/edge --frozen python .local/detector-evolution/check-reacquisition-preservation.py` | 34 configurações/vídeos originais e hashes dos quatro cenários preservados; estimadores, protocolo e arquivo de fonte iguais |
| `node .local/detector-evolution/check-reacquisition-source.mjs` | Mesmos 208 arquivos e SHA-256 da fonte medida, HEAD inalterado |

As verificações de engenharia foram executadas pelo auxiliar privado
`powershell -NoProfile -File .local/detector-evolution/check-reacquisition.ps1`;
dez comandos com exit 0, logs e resultados em `checks/`. Análise reproduzível
nos auxiliares `analyze-reacquisition-comparison.py`,
`supplement-reacquisition-audit.py` e `summarize-reacquisition-native.py`.
Agregados publicados não contêm poses ou mídia privada.

Os testes de API/E2E usaram PostgreSQL e portas exclusivos; não usaram o banco
da demonstração. A alteração gerada pelo build nas duas importações de
`apps/web/next-env.d.ts` foi restaurada ao conteúdo inicial. Nenhum lockfile ou
dependência mudou. `check:edge` confirmou um único provedor de cv2,
opencv-contrib-python 5.0.0.93, Python 3.12.15 e ausência de abertura de câmera.
Engenharia aprovada não substitui os critérios perceptuais que falharam.

### Decisão: V2 não elegível; referência mantida

| Condição de avanço | Resultado |
| --- | --- |
| Corrigir ORIGINAL omitido na reaquisição | Sim: 16/16 frames reproduzidos e recuperados; zero omissões nas 174 análises técnicas em reaquisição |
| Recuperar os quatro controles em arquivo completo | Não: três PASS; cauca-12 em 70,7692% |
| Nenhum caso antes aprovado ficar sem aceite | Não: cauca-12 continua regredido; 12 casos têm queda numérica de cobertura |
| Preservar eventos/tipos, sem alerta indevido ou duplicação | Sim nos 36 arquivos: 12 eventos com os mesmos tipos; zero novos alertas indevidos/duplicações |
| Cobertura e latência cumpridas nas repetições técnicas | Não: 16/24 aprovadas; sala R3 em 5040 ms e 76,69%; controles também insuficientes |
| Preservar economia nos caminhos caros | Sim nas três repetições, sem elevar o teto de duas chamadas |
| Preparar um ensaio físico curto | Não, os critérios anteriores não foram satisfeitos |

A omissão foi corrigida, mas **o reconhecimento não foi integralmente
preservado**. A quantidade de eventos é a mesma; a observabilidade não é.
V2 permanece opt-in para diagnóstico. Nenhum comando/roteiro novo de webcam
foi preparado. A referência preservada também não atende todas as transmissões
técnicas desta rodada: 14/24 aprovadas. Mantê-la não é aprovar sua eficácia.

O bloqueio restante é a seleção da recuperação dentro do orçamento. Nos sete
frames acima, ORIGINAL falha; a segunda passagem escolhida não encontra a pose
que outra transformação encontra. A prioridade recente experimental tampouco
resolveu isso. Não houve busca adicional de limiares ou exceções por arquivo.

`native-call-costs.json` separa a execução nativa do resto: médias de ORIGINAL
por cenário V2 entre 149,1 e 166,5 ms, P95 até 213,0 ms e máximo 289,9 ms.
Uma única passagem tem pouca margem para a meta de cinco análises/s, mas não
foi demonstrado que ela inviabilize universalmente os critérios: o cenário
de uma passagem ficou com 100% de cobertura nas três rodadas. Já a busca pode
gastar duas chamadas e ainda perder a observação necessária. Reavaliar a seleção
ou uma percepção com recuperação menos custosa exige nova hipótese e comparação;
repetir um ensaio físico agora não resolve esse bloqueio demonstrado em arquivo.

## Reprodução em arquivo

```powershell
. ./scripts/activate.ps1
$saida = ".local/benchmarks/reacquisition-$([guid]::NewGuid())"
uv run --offline --project services/edge --frozen python scripts/validation/benchmark-stream.py --config .local/detector-evolution/perception-dce2d01b-278b-4029-a405-974ffb0d00e9/candidate-final/cauca-12/comparison.yaml --output $saida --recovery RTMO_PREFERRED_V2
```

Comparar com `RTMO_ADAPTIVE_V3` ou `RTMO_PREFERRED_V1`, sempre em outra saída.
O comando exige arquivo autorizado e não abre webcam. `complete: true` confirma
EOF sem erro, sem aprovar reconhecimento, cobertura ou ausência de incidentes.

Banco da demonstração em 15432, serviço independente da 5432, proprietário,
credenciais, configurações e arquivos privados preservados. Sem treino, câmera IP,
commit, push, deploy ou aprovação integral do MVP nesta rodada.
