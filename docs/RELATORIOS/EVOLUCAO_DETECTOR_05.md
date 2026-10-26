# Evolução do detector — classificação V3 e recuperação de percepção

Data: 24–25/10/2026. **PARCIAL: regressão dos 16 aprovada; detector geral ainda não aprovado.**
Escopo D53, separado do fechamento histórico da etapa 08. Não inicia etapa 09.

## Resultado verificável

| Medida nos mesmos 16 arquivos | Referência | V2 anterior | V3 |
| --- | ---: | ---: | ---: |
| Alvos já deitados detectados / total | 2/6 | 2/6 | **6/6** |
| Perdas | 4 | 4 | **0** |
| Alertas nos dez negativos | 0 | 0 | **0** |
| Negativos inconclusivos | 5 | 6 | **0** |
| Latência dos alvos detectados | 2000 ms | 2000 ms | **2000 ms nos seis** |
| Duplicações | 0 | 0 | **0** |

Todos os seis alvos e dez negativos permaneceram no denominador. A espera de
2000 ms, prazo de 5000 ms, cobertura mínima de 80%, arquivos e contornos foram
preservados. Pessoa já deitada tem início real desconhecido: latência contada
desde 0 ms observável do arquivo. Nenhum desses seis gerou POSSIBLE_FALL.

**Os 16 agora são desenvolvimento/regressão autorizado, não reserva.** O ganho
recupera erros conhecidos. O teste original 2/6 permanece inalterado. Não usar
6/6 como estimativa de confiabilidade, generalização entre pessoas ou eficácia
no cômodo do fundador.

## Referências preservadas e artefato

Repositório inicialmente limpo em `3c7ba42cf50a698c784e911795703259eb73ecdc`.
Fonte anterior de 188 arquivos: `65ad8c16cc4859719924a1cf601a1cdb220d5c4e8ce5d45a6774295d2bc73c81`.
Arquivo ZIP local e referências em `.local/detector-evolution/improvement-current.json`,
que aponta para `improvement-a0ebbb63-ed54-46ea-855c-e52595d779da/`.
`reference.json` identifica código, pesos, avaliação e anotações originais.
Anotações originais: `6bf43e164066e78f25168fdabba9800e6fecdee323c3376e285a76bf845169ce`.
O ponteiro da avaliação original foi conferido novamente por SHA após a execução.

RTMO-s continua `d0703d40d19f3921da51ae725402d5fdae4d2478c7442072d3101bd396f370d8`.
V2 anterior: `cb02e8742b8e82282706e3570c83d895f34d509033171207c72ae209e64c9664`.
Novo `signed-body-mlp-v3-dev01`: **`40d01401851f24cd8c815557970f0dcf42877707afbba38d521ebfa87bd5bd19`**.
Segundo treinamento produziu exatamente o mesmo SHA.

Configurações reproduzíveis em `.local/detector-evolution/candidate-v3/`:
`posture.json`, `regression16.json`, 16 YAMLs, `demo-file.yaml` e `webcam-short.yaml`.
Pesos, vídeos, credenciais e observações continuam privados/ignorados pelo Git.
Exemplo público: `services/edge/posture-v3.example.yaml`.

## Mudanças no reconhecimento

Nos alvos 01/02, as poses representavam o corpo deitado, com os oito essenciais
suficientes em 91/68 observações. O descritor V2 usava valores absolutos e perdia
a direção entre ombros, quadris e pernas. A nova descrição preserva coordenadas
relativas com sinal, corrigidas em pixels pela geometria; inclui relações entre
articulações, flexão, score nativo e máscaras explícitas de ponto ausente/usável.
Nenhum nome de arquivo, participante, câmera, sessão ou ambiente entra na predição.

MLP leve NumPy, 84 entradas, 32 unidades tanh, quatro classes: em pé/caminhando,
sentado, ajoelhado/abaixado e deitado. Score máximo ≥0,65 e margem ≥0,15 para
decidir; caso contrário UNKNOWN. Scores não são probabilidades calibradas.
Ponto ausente gera atributo mascarado, sem inventar articulação/confiança.
Negativo reconhecido pode usar pose parcial; evento positivo continua exigindo
os oito pontos reais, contexto e qualidade. Falha de captura, múltiplas pessoas
e origem de confiança incompatível não são superadas pelo classificador.

O caso 03 tinha propostas de pessoa com score aproximadamente 0,59–0,62,
rejeitadas pelo limiar de 0,7. Inversão de 180° encontrou a pessoa com score
0,87–0,90 e oito pontos suficientes. Recuperação opt-in `RTMO_ADAPTIVE_V2`:
inferência original; quando não há pose ou faltam essenciais, recorte ampliado
da proposta de pessoa; se continua sem pose, inversão e recorte central.
Proposta ≥0,3 serve apenas para escolher recorte, nunca para aceitar pessoa.
Toda pose aceita ainda vem de inferência com detecção >0,7; scores ≥0,5 nos
pontos usados. Escala/origem/inversão são restauradas à imagem original,
preservando timestamps, polígonos e múltiplas detecções. Sem interpolação.

Classificação sozinha recuperou 01/02/04, chegando a 5/6, mas deixou cinco
negativos inconclusivos. Recuperação V1 chegou a 6/6 e nove negativos PASS.
Recorte da proposta, V2, resolveu a cobertura restante de caminhar/abaixar e
os pontos que saíam do quadro em 02: **6/6 e dez PASS**. As fases adversas
foram preservadas. Não houve comparação RGB adicional: nos erros conhecidos
de classe, a pose passou a distinguir as posturas; os bloqueios históricos
restantes são contexto/projeção e observação da transição. Isso não demonstra
reconhecimento visual de contato com piso ou móveis.

Implementação RTMO fundamentada no [projeto oficial](https://github.com/open-mmlab/mmpose/tree/main/projects/rtmo).
Mesmos pesos e licenças previamente registrados; nenhuma dependência/modelo
externo novo, upload ou treino automático durante execução.

## Treinamento e separação

Manifesto privado `multiclass-training.json`, anotações em
`annotations-before-v3.json`, preparados antes das previsões V3.
28 clipes no protocolo: 12 CAUCAFall antigos e os 16 agora de desenvolvimento.
Intervalos de postura revisados pelas imagens originais; rótulo genérico
fall/ADL não foi convertido automaticamente em postura. Observabilidade dos
16 preserva conferência do fundador; intervalos adicionais de classe/movimento
são anotação técnica das imagens, sem atribuir sua autoria ao fundador.

TRAIN/SELECTION separados por gravação/sessão conhecida; GMD de sessão
desconhecida agrupado conservadoramente. Pessoas podem aparecer em gravações
distintas de ambas as partições: isso está declarado, sem alegar generalização
entre participantes. Quatro positivos do quarto pertencem à mesma sessão;
dois da sala, a outra. Os seis são da mesma pessoa. Nenhum sorteio de frames
entre partições. Não há nova FINAL_RESERVED disponível.

CAUCAFall mantém treino S5/S7 e seleção S9/S10, agrupados por participante,
com gravações originais não identificadas. Isso não estabelece independência
por sessão nesses arquivos; a separação conhecida por gravação aplica-se ao
IndoorActionDataset. Não inventamos sessões independentes para o acervo antigo.

Seed 1729, Adam 1800 passos, learning rate 0,01, L2 0,001. Padronização somente
TRAIN; balanceamento por classe e grupo de gravação. Espelhamento horizontal
e remoção mascarada de um ponto só no treino. 1725 entradas com aumentação:
450 em pé, 207 sentado, 207 ajoelhado/abaixado e 861 deitado. Não são 1725 cenas
independentes. CAUCAFall, IndoorActionDataset e GMDCSA24 têm procedência/permissões
CC BY 4.0 registradas; sem publicar os arquivos. Yoga não foi usado para treino.

## Quatro perdas conhecidas

| Alvo | V2 | V3 verificado em FILE real |
| --- | --- | --- |
| chao_01_quarto_vista_superior | OTHER, perda | LYING, evento 2000 ms, cobertura 100% |
| chao_02_quarto_lateral | OTHER/pontos fora, perda | LYING, evento 2000 ms, cobertura 100% com recuperação |
| chao_03_quarto_sentido_oposto | NO_POSE, perda | Inferência invertida restaurada, evento 2000 ms, cobertura 100% |
| chao_04_quarto_diagonal | UNKNOWN, regressão | LYING, evento 2000 ms, cobertura 100% |

05/06 permaneceram detectados, ambos em 2000 ms e com cobertura 100%.

## Dez negativos e observabilidade

Captura saudável durante todo o intervalo amostrado dos dez. A tabela usa
tempo decisório conservador com ambos os extremos elegíveis; cenas vazias
dependem de anotação humana anterior, não de NO_POSE. Nenhuma cena foi encurtada.
Os últimos 40–225 ms não amostrados de cada clipe ficam fora do tempo observado,
explicitamente separados no diagnóstico completo.

| ID / atividade | Tempo observado | Decisório | Cobertura de aceite | Resíduo / resultado |
| --- | ---: | ---: | ---: | --- |
| 07 cadeira lateral | 5424 ms | 5424 ms | 100% | SEATED; PASS |
| 08 pegar objeto | 6000 ms | 4800 ms | 80% | 4 NO_POSE, 1 UNKNOWN; PASS |
| 09 sentar frontal | 6400 ms | 6000 ms | 93,75% | 1 UNKNOWN; PASS |
| 10 sentar de costas | 4800 ms | 4400 ms | 91,67% | 1 UNKNOWN; PASS |
| 11 limpar sala | 13800 ms | 13800 ms | 100% | em pé/caminhando; PASS |
| 12 limpar frontal | 9200 ms | 8600 ms | 93,48% | 2 NO_POSE; PASS |
| 13 limpar de costas | 6800 ms | 6800 ms | 100% | em pé/caminhando; PASS |
| 14 cozinha vazia | 45600 ms | não exige pose | 100% captura | vazio confirmado; PASS |
| 15 sala de jantar vazia | 7600 ms | não exige pose | 100% captura | vazio confirmado; PASS |
| 16 caminhar/abaixar | 10200 ms | 9200 ms | 90,20% | 4 UNKNOWN; PASS |

Zero eventos em todos. PASS não significa observação perfeita: 08 está no
limite de cobertura e há abstenções reais. `iteration-summary.json` inclui
classes, motivos, disponibilidade, caudas e duração por estado, sem reclassificar
ausência de pose como vazio. Traces distinguem proposta abaixo do limiar,
pessoa localizada, pose insuficiente, postura desconhecida/reconhecida e
captura degradada. O RTMO conjunto não é um detector independente de presença.

## Decisão temporal e regressões adicionais

V3 usa `POSTURE_DYNAMICS_V1`, sem mudar LEGACY/V1/V2: mudança de orientação
do tronco e deslocamento de quadril/ombros normalizado pelo tamanho corporal,
com histórico observado em pé/sentado por ≥400 ms e janela de movimento de
1000 ms. O movimento pode anteceder brevemente a classificação LYING. Só após
persistência positiva de 2000 ms pode sair POSSIBLE_FALL. Não é medição física
de altura/aceleração, nem prova de acidente/intenção. Descida controlada rápida
pode ser ambígua. Evidência desconhecida não soma tempo positivo; lacunas,
evidência antiga, rearme de 3 s e deduplicação continuam limitados/testados.

CAUCAFall, com intervalos de movimento anotados nas imagens e permanência
subsequente previamente confirmada, antes da nova execução FILE:

| Cena encenada | Evento V3 | Latência desde permanência anotada |
| --- | --- | ---: |
| FallSitting S5 | PERSON_ON_FLOOR | 1000 ms |
| FallBackwards S7 | POSSIBLE_FALL | 2200 ms |
| FallLeft S9 | PERSON_ON_FLOOR | 2200 ms |
| FallLeft S10 | PERSON_ON_FLOOR | 4000 ms |

São **4/4 alertas de permanência, mas 1/4 transições reconhecidas como possível
queda**. Não contar os outros três como acerto de POSSIBLE_FALL. Movimento
ausente/insuficiente e mudanças posturais projetadas de maneira inadequada
continuam limitando essa classificação. Na cena S7, movimento anotado desde
3200 ms; emissão 7200 ms: 4000 ms desde início do movimento, 2200 ms desde
início anotado da permanência. Não confundir os dois relógios.

Oito ADL CAUCA sem evento: caminhar, sentar, pegar objeto, ajoelhar. Sete PASS;
pegar objeto S10 ainda inconclusivo, cobertura 65,28%. Três perdas antigas
floor03/05/07 continuam sem evento, com projeção do quadril fora do contexto
de piso na maior parte das poses LYING. Não expandimos ROI para fazê-las passar.
Inícios desses três permanecem provisórios, sem inventar recall/latência formal.
Controle adicional real de deitar voluntariamente em colchonete também perdeu
PERSON_ON_FLOOR: contexto fora e trechos indeterminados. Ausência de
POSSIBLE_FALL nesse controle não aprova a distinção entre queda e deitar.

Inventário desta rodada ampliada: 14 cenas-alvo (seis do lote, quatro CAUCA,
três históricas e o controle voluntário), dez com alerta e quatro sem. Esse
total mantém as perdas visíveis; não é recall formal agregado, pois os três
inícios históricos e o controle têm anotações de precisão diferente.

Próximos experimentos específicos: examinar suporte/contato corporal e projeção
do contexto nos três históricos, com anotação física antes de rever o gate;
avaliar trajetória multijuntas e recuperação da percepção nas transições,
incluindo descidas voluntárias lentas/rápidas. Não promover o candidato enquanto
essas limitações e a avaliação reservada do uso pretendido estiverem abertas.

## Ambiente, custo e fluxo

Windows 11 Pro 10.0.26200, Ryzen 5 5625U, 6 núcleos/12 threads, 15,4 GiB RAM.
Python 3.12.15, uv 0.13.4, Node 24.22.1, pnpm 10.34.7. NumPy 2.5.4,
ORT 1.23.2, MediaPipe 1.1.1 e único provedor cv2 opencv-contrib-python 5.0.0.93.
Nenhuma dependência instalada ou lockfile alterado. Não foi testada câmera física.

Repetição final pelo evaluate público: 986 análises, 194024 ms observados de
195994,9 ms de conteúdo. **259,484 s de parede, 1035,891 s de CPU**, inferência
média 232,699 ms, pico de processo 280,83 MiB. Leitura/decodificação/resize
13,424 s medidos separadamente. Prévia desligada nessa comparação. Ensaio
separado de exibição FILE: 25 análises em 5,434 s de parede, amostragem de 5/s
na mídia; leitura 284,29 ms totais, inferência média 112,15 ms, chamadas de
prévia 318,87 ms totais (12,75 ms por desenho, incluindo espera do OpenCV).
Encerrou STOPPED_LIMIT conforme configuração, sem eventos. Não mede FPS de
webcam, não comprova precisão/fluidez em outros vídeos nem promete 30 FPS.
Classificação e gravação também têm medidas próprias.

Referência histórica: 154,56 s parede / 619,69 CPU; V2: 171,62 / 688,09.
Classificação V3 sem recuperação: 150,75 / 602,50, mas perdeu um alvo e deixou
cinco negativos inconclusivos. A recuperação custa inferências adicionais,
sobretudo em cenas vazias. São medições de rodadas na mesma máquina, sem controle
rigoroso de processos de fundo; não estimativa causal precisa de velocidade.
O custo piorou, embora a regressão principal tenha melhorado.

Dez envelopes nativos SQLite atravessaram HTTP/contratos/API/PostgreSQL isolado,
porta efêmera 54627, dez incidentes/avisos locais, reenvio sem duplicação. Banco
descartável removido. Teste técnico do endpoint de revisão foi identificado como
automático, sem substituir a conferência do fundador.

Replay adicional real no banco da demonstração **15432**, preservando 5432 e
os cadastros: incidente `1d192fe1-b325-4ff8-907e-dee9007ce29e`, PERSON_ON_FLOOR,
REPLAY/TEST, 2000 ms, aviso local SIMULATED. Fundador confirmou e registrou
“Conferência do replay V3 de desenvolvimento”; banco conferido com versão 2,
PERSON_ON_FLOOR_CONFIRMED e uma ação. É vídeo do dataset numa câmera lógica FILE,
não filmagem do cômodo do fundador. Nenhuma comunicação externa, snapshot ou upload.

## Comandos e verificações realmente executados

Prefixo Python usado: `uv run --offline --project services/edge --frozen`.

| Comando/ação | Resultado |
| --- | --- |
| git status, inventário, leitura dos documentos/configurações/artefatos e git archive | referência limpa preservada, dados mantidos |
| python .local/detector-evolution/prepare-multiclass-development.py | manifesto e anotações separados dos originais |
| radar-edge posture-train --manifest …/multiclass-training.json --output …/posture-v3-dev01.json | treino local concluído |
| repetição posture-train para posture-v3-reproduced.json | mesmo SHA, 1725 entradas com aumentação |
| python .local/detector-evolution/run-multiclass-development.py | classificação isolada: 5/6, cinco inconclusivos |
| mesmo helper com --recovery, V1 e depois V2 | 6/6; nove e depois dez negativos PASS; fases preservadas |
| python .local/detector-evolution/diagnose-rtmo-misses.py e diagnose-proposal-crop.py | comparações reais de percepção, sem reduzir limiar |
| python .local/detector-evolution/run-old-regressions-v3.py; repetido com --resume | 12 CAUCA + três históricos + controle; erro do helper ao receber duração float corrigido, execuções/filas preservadas |
| python .local/detector-evolution/verify-current-replay.py | 24 sequências antigas reproduzidas; fingerprints e eventos iguais |
| radar-edge evaluate --manifest .local/detector-evolution/candidate-v3/regression16.json | exit 0; 16 ok/ENDED, seis alvos/10 PASS, análise final conferida |
| pytest services/edge/tests -q | **366 passaram**, uma GUI pulada; inclui o preparador de contexto |
| ruff check/format nos fontes/testes alterados | erros iniciais de formatação corrigidos; check passou |
| pnpm.cmd lint; pnpm.cmd typecheck; pnpm.cmd build | passaram |
| pnpm.cmd test:e2e | **20 passaram**, desktop/mobile, recursos isolados removidos |
| pnpm.cmd --filter @radar/contracts test | **104 passaram**, tipos gerados e schemas compatíveis |
| pnpm.cmd exec node .local/detector-evolution/native-http-runner-v3.mjs | dez envelopes nativos, dez avisos, zero duplicação, banco isolado removido |
| radar-edge env | imports reais e único cv2 verificados |
| python .local/detector-evolution/measure-v3-file-preview.py | 25 desenhos FILE medidos, janela encerrada pelo limite, sem webcam/eventos |
| radar-edge posture-check para demo-file.yaml e webcam-short.yaml | ok, sem abrir fontes/bancos |
| radar-edge run --config .local/detector-evolution/candidate-v3/demo-file.yaml --no-preview; radar-edge deliver --config …/demo-file.yaml | evento real entregue, ACK TEST; revisão humana conferida no banco |
| python scripts/validation/confirm-posture-context.py --config …/webcam-short.yaml --confirmed | preparo sobre calibração histórica, backup/fila anterior preservados, sem abrir câmera |

Ocorreram erros de invocação de shell/comando auxiliar e testes de desenvolvimento;
foram corrigidos antes da repetição. Não foram falhas silenciosas de captura.
Em especial, a primeira conferência de revisão encontrou versão 1/zero ações;
o fundador foi informado, salvou a ação e a segunda conferência comprovou versão 2.

Snapshot executável final: 197 arquivos,
`27aa36e4c2d0b13c9a0fc3b00d900db67ab25da6bd3ece59393620bfe2bdf467`.
A rodada final de inferência começou com snapshot de 194 arquivos `4c5965c3…`;
os três arquivos adicionais são o preparador explícito de contexto e seu teste,
verificados separadamente, sem alteração da inferência/classificador/motor.
`final-regression-summary.json`, `iteration-summary.json`, traces e resultados
individuais ficam no diretório privado desta iteração. Retenção normal de
diagnósticos continua aplicada; agregados não contêm vídeo/quadros.
`freeze-v3-result.py` verificou os 16 hashes novamente e gerou
`final-freeze-manifest.json` com anotações/modelos/configurações/resultados e
ZIP privado da fonte atual. SHA do ZIP:
`6aad349bb29468f4cbefb33010e4afcf03548a75cbbdc9e230f5bc43e43aff40`.

## O que falta para aprovar o uso pretendido

A regressão dos 16 passou. **A entrega funcional completa permanece reprovada/incompleta**:
três perdas históricas, controle de deitar perdido, uma atividade antiga com
observação insuficiente e transição reconhecida em apenas 1/4 das quedas encenadas.
Não há dados reservados novos nem sessão física V3. Não substituímos esses gates
por compilação ou treino bem-sucedido.

Congelar candidato e reservar pelo menos quatro novos episódios já no chão e
oito atividades comuns de sessões não consultadas, mais transições encenadas
reservadas e controles. Para o cômodo: três orientações, passagem voluntária,
cadeira, ajoelhar/pegar objeto, sofá/rede, vazio e oclusão/retorno. Vídeos de
10–20 s por cena, piso/corpo inteiro, câmera fixa e luz adequada; nenhuma queda
física provocada. [Comandos curtos e ordem da sessão](../USO_DETECTOR_EXPERIMENTAL.md).

Sem commit, push ou deploy. Serviços locais da demonstração iniciados para a
conferência humana, sem alterar permissões de câmera ou o PostgreSQL preexistente.

Complemento posterior em 25/10: o fundador executou o primeiro ensaio LIVE V3.
Um evento foi entregue; a classificação física permanece pendente de anotação.
[Medições, evento e limites da sessão](SESSAO_WEBCAM_V3_2026_10_25.md).
