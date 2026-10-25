# Evolução do detector — primeira avaliação dos 16 arquivos

Data: 24/10/2026. **AVALIAÇÃO EXECUTADA; NÚCLEO FUNCIONAL NÃO APROVADO.**
Continuação de D52; não altera o fechamento histórico da etapa 08.
[Preparação, procedência e revisão dos contornos](EVOLUCAO_DETECTOR_03.md).

## Resultado principal

As marcações foram corrigidas e os 16 contextos aprovados pelo fundador antes
de executar o detector. A comparação terminou com **2/6 alvos na baseline e
2/6 no candidato corporal V2**, ambos com quatro perdas. Não houve melhora
global de detecção neste lote. V2 recuperou chao_06, mas perdeu chao_04, que a
baseline detectou. Não promover V2 como candidato final do uso pretendido.

Ambas as versões geraram zero alertas nos dez negativos. Baseline: cinco
negativos PASS e cinco INCONCLUSIVE; V2: quatro PASS e seis INCONCLUSIVE.
Não declarar dez acertos por haver silêncio: a maioria dos negativos da V2
não teve observação/classificação suficiente para o aceite ≥80%.

Trinta e duas execuções FILE reais concluíram ok/ENDED, sem fallback de tempo,
erro de captura ou truncamento de diagnóstico. Isso comprova processamento e
persistência, sem eliminar as perdas de percepção/classificação. Nenhum alvo
ou negativo foi retirado do resultado. Nenhuma webcam aberta, treino novo,
mudança de parâmetros após os resultados, HTTP, snapshot ou mensagem externa.

## Referência e protocolo

HEAD 0778e028156bf40ec7ac158ebefdc20010efc041, fonte executável de 188 arquivos,
SHA **65ad8c16cc4859719924a1cf601a1cdb220d5c4e8ce5d45a6774295d2bc73c81**.
As mesmas versões de ambiente do relatório 03: Windows 11, Ryzen 5 5625U,
Python 3.12.15/uv 0.13.4, OpenCV contrib 5.0.0.93, ORT 1.23.2, CPU com quatro
threads intra/inter=1. Nenhuma dependência ou migração acrescentada.

RTMO-s d0703d40… preservado; análise alvo 5/s, largura de processamento 640,
score articular ≥0,5 e detecção de pessoa 0,7. Candidato LINEAR_BODY_V2,
posture-body29-v2 SHA cb02e8742b8e82282706e3570c83d895f34d509033171207c72ae209e64c9664,
política floor-rtmo-score-posture-body-v2, worker edge-posture-v2. Baseline
floor-rtmo-score-v0.1 e motor anterior preservados. Scores V2 0,8/0,2;
persistência/cobertura e limite principal de 5000 ms não foram reduzidos.

Pesos escolhidos somente nos dados antigos. No novo lote, cenas/intervalos e
contornos foram conferidos por grupos pelo fundador; propostas rejeitadas e
suas correções preservadas. Seis alvos já deitados desde 0 ms, sem transição
observada, e dez negativos. Cozinha e primeira sala de jantar explicitamente
confirmadas vazias. Os dois alvos da sala foram aceitos com a observação de
que ainda poderiam ser refinados; isso ficou no recibo.

Lote: 14 clipes IndoorActionDataset e dois GMDCSA24. Os seis positivos são da
mesma pessoa em duas gravações originais; há recortes relacionados nos negativos
e sessão GMD desconhecida. Não são 16 sessões independentes, nem gravações do
cômodo do fundador. A avaliação mede esta amostra e versão, sem estimativa de
eficácia geral ou generalização entre pessoas.

Anotações congeladas antes da primeira previsão, SHA
**6bf43e164066e78f25168fdabba9800e6fecdee323c3376e285a76bf845169ce**.
Baseline primeiro, candidato depois, filas novas e HTTP desligado. Ambos usam
os mesmos arquivos, pisos e extrator; V2 também recebe exclusões manuais de
apoio/oclusão, capacidade inexistente na baseline. É comparação entre sistemas
declarados, não uma ablação que atribui toda diferença apenas aos pesos.

## Seis alvos, todos mantidos

Latência desde o início anotado, sem deslocá-lo para quando o modelo aceita a
pose. Pessoa já deitada não prova queda ou necessidade de assistência.

| Arquivo | Baseline | V2 | Diagnóstico da V2 |
| --- | --- | --- | --- |
| chao_01_quarto_vista_superior | Perda | **Perda** | 91/91 poses essenciais válidas, quadril dentro da região; classifica OTHER_POSTURE em todas. Score deitado 0,00255–0,00349 |
| chao_02_quarto_lateral | Perda | **Perda** | 68 poses válidas classificadas OTHER_POSTURE, score 0,0162–0,0235; 15 observações com pontos fora do quadro. Cobertura 79,3% |
| chao_03_quarto_sentido_oposto | Perda | **Perda** | Nenhuma pose detectada nas 74 análises. Ausência de detecção não significa ausência real da pessoa |
| chao_04_quarto_diagonal | 2000 ms | **Perda, regressão** | 43 poses válidas e quadril dentro, mas score 0,468–0,616: todas UNKNOWN, sem evidência positiva |
| chao_05_sala_lateral | 2000 ms | **2000 ms** | 65 análises LYING; cobertura decisória 100% |
| chao_06_sala_de_costas | Perda | **2000 ms, recuperação** | 41 análises LYING; cobertura decisória 100% |

Os quatro perdidos contam integralmente como perdas; não são descartados como
fora de escopo para elevar o resultado. Nos alvos 01/02/04, os quadris avaliados
ficaram dentro da região: expandir novamente o piso não corrige a classificação.
No alvo 03, a falha precede o classificador. Os scores são saídas não calibradas
do modelo linear, não probabilidade médica ou medida de visibilidade física.

V2 emitiu dois PERSON_ON_FLOOR, sem duplicação, atraso >5000 ms ou
POSSIBLE_FALL injustificado. Não houve ensaio de transição real nesse lote.
O ganho anterior no desenvolvimento CAUCAFall (4/4) não se confirmou como ganho
global nesses novos enquadramentos. As três perdas históricas e a possível
perda LIVE permanecem registradas separadamente, sem aprovação retrospectiva.

## Dez negativos

PASS exige ausência de evento e cobertura decisória ≥80%, salvo cenas vazias
confirmadas, cuja cobertura é de captura saudável. INCONCLUSIVE continua no
denominador dos dez negativos. Nenhuma cena foi reduzida ou excluída.

| Arquivo | Baseline | V2 | Cobertura V2 e motivo principal |
| --- | --- | --- | --- |
| comum_01_cadeira_quarto | PASS | **INCONCLUSIVE** | 0% decisória; 28 poses válidas, mas classificação incerta em apoio excluído |
| comum_02_pegar_objeto | PASS | PASS | 83,7% |
| comum_03_sentar_no_sofa | INCONCLUSIVE | INCONCLUSIVE | 18,8%; incerteza/apoio e intervalos sem pose |
| comum_04_sentar_outro_angulo | INCONCLUSIVE | INCONCLUSIVE | 0%; incerteza e ausência de pose |
| comum_05_limpar_sala | PASS | PASS | 97,1% |
| comum_06_limpar_sala | INCONCLUSIVE | INCONCLUSIVE | 65,2%; intervalos sem pose |
| comum_07_limpar_outro_angulo | INCONCLUSIVE | INCONCLUSIVE | 64,7%; intervalos sem pose |
| comum_08_cozinha_vazia | PASS | PASS | 100% de captura; vazio confirmado pelo fundador |
| comum_09_sala_de_jantar_vazia | PASS | PASS | 100% de captura; vazio confirmado pelo fundador |
| comum_10_caminhar_sala_de_jantar | INCONCLUSIVE | INCONCLUSIVE | 45,1%; ausência de pose/pontos insuficientes |

Em comum_03, V2 também classificou cinco observações como LYING em região de
poltrona. A exclusão manual impediu evidência positiva de chão. Isso demonstra
a utilidade daquele contexto declarado e uma confusão residual do classificador;
não é reconhecimento automático de todos os móveis nem desempenho multiclasse
comprovado. O motor não somou tempo desconhecido como tempo positivo.

## Processamento e verificações

| Medida observada | Baseline | V2 |
| --- | --- | --- |
| Análises reais | 986 | 986 |
| Tempo total de parede, soma dos arquivos | 154,557 s | 171,615 s |
| CPU acumulada, inclui threads nativas | 619,688 s | 688,094 s |
| Inferência média ponderada pelo número de análises | 127,484 ms | 142,443 ms |
| Maior pico de working set do processo | 293371904 bytes | 320905216 bytes |
| Tempo observado na fonte | 194024 ms | 194024 ms |
| Tempo elegível para decisão | 106248 ms | 86424 ms |
| Tempo de captura saudável | 194024 ms | 194024 ms |

Rodadas sequenciais, sem controle térmico de benchmark pareado; não atribuir
causalmente toda diferença de tempo à classificação. Memória é pico acumulado
da vida do processo, não incremento isolado de cada clipe. Prévia desligada;
não há medição de FPS de monitor, fluidez LIVE ou estabilidade física. Conteúdo
total 195995 ms; caudas não amostradas somam 1971 ms por versão, explicitadas nos
relatórios. Captura terminou normalmente, sem apagar o restante dos alvos.

Comandos realmente executados nesta rodada, após `. ./scripts/activate.ps1`:

| Comando | Resultado |
| --- | --- |
| `uv run --offline --project services/edge --frozen python .local/detector-evolution/finalize-intake16-annotations.py` | Exit 0; 16 cenas/contornos aprovados, zero previsões anteriores à anotação |
| `uv run --offline --project services/edge --frozen python .local/detector-evolution/prepare-intake16-evaluation.py` | Exit 0; recibos/hashes/contextos verificados, manifestos/configurações preparados sem inferência |
| `uv run --offline --project services/edge --frozen python .local/detector-evolution/run-intake16-evaluation.py` | Exit 0; 32 FILE reais, todas ok/ENDED, comparação adversa preservada |
| `uv run --offline --project services/edge --frozen python .local/detector-evolution/summarize-intake16-evaluation.py` | Exit 0; tabelas, diagnósticos por caso e métricas agregadas |
| `uv run --offline --project services/edge --frozen python .local/detector-evolution/verify-intake16-evaluation.py` | Exit 0; 32 execuções SQLite concluídas, quatro envelopes nativos, zero tentativas HTTP/JPEG, mídia/fonte/anotações preservadas, 32 traces completos |
| `pnpm.cmd exec node .local/detector-evolution/validate-intake16-events.mjs` | Exit 0; os quatro envelopes reais aceitos pelo contrato compartilhado TS/AJV event-v1 |
| `uv run --offline --project services/edge --frozen python .local/detector-evolution/freeze-intake16-result.py` | Exit 0; resultados agregados e recibos preservados, sem arquivar traces brutos ou alterar o teste para aprová-lo |

Conferência final: links locais da documentação válidos, hashes dos agregados
congelados verificados, 16 vídeos originais inalterados e fonte 65ad8c16… igual.
git diff --check sem erros, nada staged, lockfiles inalterados nesta revisão;
PostgreSQL de demonstração saudável e limitado a 127.0.0.1:15432.

Os quatro envelopes são dois da baseline e dois da V2, em filas distintas.
Permanecem PENDING, com zero tentativas, porque a entrega estava desabilitada.
Não foram criados quatro incidentes no painel da demonstração por essa rodada.
A integração HTTP isolada anteriormente verificada continua evidência anterior.
Não houve commit, push ou deploy; banco/volume de demonstração preservados.

Código do worker e contratos não mudaram durante a revisão; continuam na fonte
congelada que passou 348 testes sem GUI e a verificação separada de janela
artificial. Não apresentar esses testes como nova execução nesta rodada de
dados. Hashes das configurações também foram auditados depois da execução,
com modificação anterior ao plano; essa lista posterior não é apresentada como
um compromisso criptográfico publicado previamente. As anotações e o artefato
tinham seus próprios hashes congelados antes das previsões.

verification.json separa `scope=ENGINEERING_INTEGRITY_CHECKS`/`status=ok` de
`detectorAcceptance.status=REJECTED`, com 2/6 alvos, quatro perdas e seis
negativos inconclusivos; functionalMvpApproved=false. Um resultado técnico
verde não equivale a aprovação de detecção.

## Evidências e reprodução

Ponteiro `.local/detector-evolution/intake16-pointer.json` localiza o lote.
Dentro dele, evaluation-pointer.json aponta para
confirmed-33b57a7b-e6c0-4836-8a99-c81b7360ddb8, com execution-plan.json,
annotations-freeze.json, manifestos, configurações, comparison.json, analysis.json,
verification.json e eventos nativos. Relatórios/filas originais também ficam
em `.local/evaluation/`. Vídeos/modelos não estão no Git; helpers são específicos
dos materiais privados desta bancada, não requisitos de instalação limpa.

Resultado agregado preservado por result-freeze-pointer.json; SHA do manifesto
de fechamento **9248b285b2704b20f650ed086b5006cbd2cea597f440a726c286705bf29f9699**.
O snapshot contém métricas, anotações/recibos e hashes, sem cópias de traces
brutos para contornar seus sete dias de retenção. O inventário original continua
imutável; o estado atual dos 16 passa a EVALUATED_HELD_OUT_FROZEN_V2. Revisão
visual é somente consulta e helpers de remarcação recusam material já avaliado.

Para consultar o resultado nesta bancada:

```powershell
. ./scripts/activate.ps1
$radarIntake = Get-Content .local/detector-evolution/intake16-pointer.json -Raw | ConvertFrom-Json
$radarResult = Get-Content (Join-Path $radarIntake.root 'evaluation-pointer.json') -Raw | ConvertFrom-Json
Get-Content (Join-Path $radarResult.root 'verification.json') -Raw
```

Para repetir somente FILE com a mesma fonte/artefato congelados:

```powershell
uv run --offline --project services/edge --frozen radar-edge evaluate --manifest (Join-Path $radarResult.root 'candidate-manifest.json')
```

O comando cria outras filas/relatórios, mantém HTTP desligado e não abre webcam.
O helper da primeira comparação recusa sobrescrever uma execução já iniciada.
Repetir o mesmo ensaio não produz uma nova avaliação independente.

## Decisão e trabalho restante

A etapa de **corrigir e conferir as marcações deste lote terminou**. O teste
do detector terminou com resultado insuficiente. Congelar e preservar esse
primeiro resultado reservado; não baixar limiares ou mover regiões para fazê-lo
passar. O lote continua avaliado, sem ser usado para treino/seleção nesta versão.
Se orientar ajuste/escolha de um sucessor, classificá-lo como desenvolvimento
para esse sucessor e obter outra reserva para seu aceite.

O trabalho seguinte é de percepção/classificação: reconhecer o corpo deitado
em perspectivas novas, recuperar/recusar explicitamente poses incompletas e
distinguir apoios. Desenvolver com materiais permitidos de desenvolvimento e
anotações completas, incluindo negativos, sem reaproveitar esta reserva como
prova independente de uma correção. Um único classificador linear treinado em
poucas cenas antigas não teve generalização demonstrada aqui.

Continuam faltando desenvolvimento/avaliação no cômodo do fundador, rede e
ajoelhamento persistente, transição segura e futura demonstração física com
entrega/revisão humana/aviso. Não pedir outro teste de câmera agora nem repetir
a apresentação dispensada. V2 permanece opt-in e experimental; nenhuma
configuração LIVE existente foi promovida automaticamente a ele.
