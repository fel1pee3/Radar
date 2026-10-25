# Evolução do núcleo de detecção — um cômodo

24/10/2026. **PARCIAL; candidato implementado, demonstração funcional não aprovada.**
Solicitação atual do fundador, independente do fechamento histórico da etapa 08.
[Instrumentação](RELATORIOS/EVOLUCAO_DETECTOR_01.md) ·
[Comparação e limites](RELATORIOS/EVOLUCAO_DETECTOR_02.md) ·
[Novo lote e candidato corporal](RELATORIOS/EVOLUCAO_DETECTOR_03.md) ·
[Avaliação dos 16 arquivos](RELATORIOS/EVOLUCAO_DETECTOR_04.md) ·
[Roteiro curto](USO_DETECTOR_EXPERIMENTAL.md).

## Escopo e aceite

Câmera fixa, um cômodo, uma pessoa, região observada e exclusões confirmadas,
iluminação/enquadramento declarados, processamento local e revisão humana.
PERSON_ON_FLOOR é postura persistente; POSSIBLE_FALL exige evidência adicional
de transição, não comprova acidente ou necessidade médica.

Aceite a preparar antes das previsões finais: pessoa já deitada em três
orientações observáveis, transição voluntária segura, cadeira, rede se
observável, ajoelhamento, pegar objeto, ambiente vazio e perda de observação.
Meta inicial: alerta em até 5000 ms do início anotado, sem mover esse início
para quando o algoritmo passou a aceitar a pose. Não provocar quedas.

Todos os alvos acordados permanecem no denominador principal, inclusive perdas
por pose insuficiente. Informar cobertura/incerteza separadamente. Não tratar
silêncio com pouca observação como acerto, ou aumentar só a suavidade do desenho
como melhora da detecção. Separar classificação corporal de contexto: polígono
é região 2D da imagem, não prova de contato com chão nem altura física.

## Baseline preservada e dados

Baseline limpa: commit 0778e028156bf40ec7ac158ebefdc20010efc041, fonte de 179
arquivos SHA a2b76fa33449fac7a438efa10e5470580b6310a6b12530d62bf33790b8aeb991.
RTMO-s CPU mantido como extrator, SHA
d0703d40d19f3921da51ae725402d5fdae4d2478c7442072d3101bd396f370d8;
política floor-rtmo-score-v0.1. ZIP de código, parâmetros/configurações/pisos,
versões e hashes locais em `.local/detector-evolution/baseline-0778e02/`.

Inventário inicial: 41 vídeos em .local/videos, incluindo 12 CAUCAFall.
Os 12 CAUCAFall orientam esta correção e são **DEVELOPMENT para a nova versão**.
A avaliação histórica 3/4, sua perda FallLeftS9, demais perdas e LIVE inconclusivo
permanecem inalterados. Na primeira rodada não havia conjunto final novo.
Recebidos 16 arquivos novos confirmados pelo fundador, com seis alvos positivos
e dez negativos avaliados após congelar as anotações. Procedência por bytes e
decodificação verificadas. Fundador confirmou as cenas/intervalos e reprovou
as marcações de contexto iniciais. Os 16 contornos foram refeitos, revistos e
aprovados por grupos antes da inferência, sem mudar pesos/limiares. Fundador
aceita os dois alvos da sala e ainda deseja refinamento visual. Contexto/anotações
congelados antes das previsões; comparação FILE concluída, sem HTTP/webcam.
Não inventar independência entre pessoas, sessões, recortes ou versões de um arquivo.

Treinamento local leve só será usado se justificado e com permissões verificadas.
CAUCAFall V4 declara CC BY 4.0 na fonte; atribuir autores/versão, manter mídia
privada. MIT do repositório GMDCSA24 não será tratado automaticamente como prova
de uma permissão específica para treinamento sobre todos os vídeos. Nenhum peso
RTMO será redistribuído. Sem troca de estimador, dependências, conta/serviço pago
ou LLM por frame nesta instrumentação.

## Incrementos

1. Preservar baseline e inventariar procedência/anotações locais.
2. Instrumentar decisões FILE/LIVE com limites, retenção e distinção entre
   ausência de detecção, pose insuficiente, postura desconhecida e captura indisponível.
3. Reproduzir perdas e gerar linhas do tempo; comparar alternativas de postura
   e contexto com negativos, mantendo sequência temporal real.
4. Integrar candidato versionado, histerese/incerteza/recuperação, persistência
   e deduplicação; não reutilizar tempo de pausa/reconexão.
5. Medir arquivos de desenvolvimento/seleção, congelar candidato e avaliar
   quatro alvos/oito negativos novos anotados anteriormente. Depois preparar
   webcam a ser iniciada pelo fundador quando disponível.

## Diagnóstico opt-in

`diagnostics.exportDecisions: true` habilita decisions.jsonl por execução, nas
mesmas configurações privadas de FILE/LIVE. Defaults: até 10000 registros,
10 MiB por execução, 50 MiB de decisões no diretório e retenção de sete dias.
Limites ajustáveis dentro dos tetos do schema. Um escritor ativo por raiz de
diagnóstico serializa quota/retenção; usar raízes distintas se necessário.
Retenção só remove decisions.jsonl expirados em pastas UUID, sem tocar mídia,
modelos, calibrações, fila, observações ou relatórios históricos.

Registra tempos da fonte, qualidade real dos pontos essenciais, atributos,
critérios, região da imagem, estados antes/depois, evidência temporal e emissão/
supressão/reset. Sem vídeo/imagens, segredos ou interpolação da prévia. No modo
de evidência none, não registra coordenadas/qualidade numérica de pontos.
Truncamento fica explícito em decisionExport; não reconstruir períodos ausentes
como se estivessem observados. Erro de gravação é visível; evento já persistido
continua na outbox, sem duplicação automática após retomada.

## Operação e limites atuais

Webcam não será aberta automaticamente. Diagnóstico inicial usa arquivos,
resultados/fila separados e entrega HTTP desligada. Nenhum commit/push/deploy
autorizado nesta evolução. Avisos atuais são registros locais/simulados no
painel; não há envio a celular ou contato externo. Fluidez vem depois da
correção de detecção, com captura/inferência/exibição medidas separadamente.

## Resultado do candidato

Resultado consolidado das sete cenas positivas conhecidas de regressão: baseline
3/7 com alerta, candidato 4/7; três perdas históricas permanecem. Os inícios das
três cenas antigas ainda são provisórios, portanto não calcular acurácia global
ou latência agregada como avaliação formal. Elas não foram removidas por serem
contexto não suportado; continuam falhas do sistema nesse inventário. O LIVE
histórico sem alerta permanece possível perda/inconclusivo, sem virar acerto.

Worker FILE real, com RTMO-s e SQLite: **4/4 alvos de desenvolvimento/seleção**,
ante 3/4 da baseline, latências 1400/1400/3800/4000 ms, zero duplicações. Zero
alertas nos oito negativos, mas apenas três passaram o gate de observação ≥80%;
cinco inconclusivos. Não tratar os cinco silêncios como acertos. Esse problema
de cobertura também ocorre na baseline; nenhum alvo foi removido do resultado.
Esses quatro alvos são o subconjunto CAUCAFall do inventário acima.

Classificador linear local, 35 atributos, 310 observações em seis clipes S5/S7;
seis clipes S9/S10 para seleção, agrupados por participante. Mesmo ambiente e
sessões desconhecidas. Doze ajustes consultaram a seleção; esses dados não são
avaliação independente do novo candidato. Artefato privado
posture-cauca-symmetric-v1, SHA
154196a21b4c567f1bc1d3654f7a9527b20dc222a213b66ecf3803da3dc7ed04.

Instalação experimental CAUCAFall-room-camera03, calibração/hash e geometria
confirmados. Não habilita o cômodo do fundador. As três perdas floor03/05/07
continuam: Full perde qualidade; RTMO recupera a pose, mas o quadril fica fora
da região. O score deitado alto em experimento fora do escopo não resolve
contato/contexto. Não expandimos o piso a partir das previsões.

Comparação de detecção de pessoa com limiar 0,7/0,5 recuperou observações e tornou
conclusivo mais um negativo, deixando quatro inconclusivos. Não adotada: faltam
ensaios de ambiente vazio/apoios para justificar mudança. Worker mantém 0,7.

Implementados: classificador opt-in, contexto/exclusões de apoios, motor
EVIDENCE_V2 com histerese/incerteza/recuperação, diagnóstico FILE/LIVE limitado,
flags no painel, treinamento reproduzível e proteção do conjunto reservado.
Subtipos descritivos em pé/sentado/ajoelhado não têm acurácia multiclasse medida.

Faltam dados novos do cômodo, desenvolvimento que cumpra o aceite e webcam
iniciada pelo fundador depois dos arquivos,
com entrega/revisão/aviso conferidos. O fundador preparará os vídeos depois;
webcam não aberta. Não repetir apresentação dispensada nem teste histórico de 30 min.

Fontes verificadas: [CAUCAFall V4](https://data.mendeley.com/datasets/7w7fccy7ky/4),
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/),
[GMDCSA24 LICENSE na revisão dos arquivos](https://github.com/ekramalam/GMDCSA24-A-Dataset-for-Human-Fall-Detection-in-Videos/blob/5abac7693229900cf80f722e878fbb119211fc1c/LICENSE),
[homografia e hipótese de plano, OpenCV](https://docs.opencv.org/4.x/d9/dab/tutorial_homography.html).
Homografia não transforma, por si, pontos corporais fora do plano em medição de altura.

## Reserva nova e candidato de 29 atributos

O lote Radar_16_Videos_Novos tem 14 clipes do IndoorActionDataset e dois do
GMDCSA24. Os seis positivos são da mesma pessoa em duas gravações originais;
há recortes de gravações comuns nos negativos. Não são 16 pessoas/sessões
independentes. Não inclui rede, ajoelhamento persistente ou transição para o
chão: os positivos já começam deitados. A pasta train da fonte não determina
o papel local; o fundador confirmou que esses bytes nunca orientaram o Radar.

O candidato anterior usa seis atributos absolutos da imagem, por isso não pode
ser transportado como se fosse válido nesses cômodos. LINEAR_BODY_V2 retém 29
atributos corporais normalizados, mantendo RTMO-s/qualidade/limiares temporais.
Treino e seleção usaram somente o CAUCAFall antigo. Artefato posture-body29-v2,
SHA cb02e8742b8e82282706e3570c83d895f34d509033171207c72ae209e64c9664.
Nova política floor-rtmo-score-posture-body-v2 e worker edge-posture-v2.
Contexto continua manual, confirmado por hash/calibração/geometria; não mede
altura ou contato. Uso em instalação nova é experimental e exige avaliação.

Na V2, outra postura reconhecida em área de apoio pode fornecer evidência
negativa; deitado/desconhecido nesse apoio continua impedindo confirmação de
chão. V1 conserva sua semântica congelada. Novas anotações transitionObserved=false
impedem aprovar uma emissão POSSIBLE_FALL em cena que já começa deitada, mesmo
quando ela detecta corretamente a presença no piso. Sem anotação de transição,
não alegar precisão desse tipo de evento.

Conferir vídeos originais/pisos sem IA antes de inferir; congelar versão e
anotações, manter todos os seis alvos e dez negativos no resultado. Cobertura
baixa continua inconclusiva. Não ajustar com a reserva e reutilizá-la como
avaliação independente. Três perdas antigas e possível perda LIVE preservadas.

As exclusões vermelhas são regiões manuais de apoio/oclusão, não uma
segmentação automática de todos os objetos. Não inferir posição de móveis
pela cor do desenho. Uma cadeira que se desloca invalida a hipótese de contorno
fixo para ela; esse caso precisa de tratamento/revisão explícitos, mantendo o
vídeo no conjunto. Refinar a região olhando a imagem original antes de prever
é anotação de contexto; expandi-la após ver erros do detector seria ajuste
com a reserva e mudaria seu papel para desenvolvimento.

## Resultado reservado — candidato V2 não aprovado

Baseline e V2: **2/6 alvos**, quatro perdas em cada; latências dos detectados
2000 ms. V2 recuperou chao_06 e perdeu chao_04, que a baseline detectava. Zero
duplicações ou alertas nos dez negativos; V2 tem quatro negativos PASS e seis
INCONCLUSIVE, ante cinco/cinco da baseline. Não houve ganho global nesse lote.

Nos alvos chao_01/02, V2 classifica a pessoa deitada como outra postura apesar
de poses utilizáveis; chao_03 não retorna pose e chao_04 fica incerto. Os
quadris avaliados de 01/02/04 estão dentro da região, sem motivo para ampliar
o piso a partir dessas previsões. Em cinco análises de uma cena sentada, V2
indicou LYING e a exclusão manual de poltrona bloqueou confirmação de chão.
Silêncio em contextos incertos não comprova precisão.

São 32 execuções reais ok/ENDED, com diagnósticos completos e integridade
preservada. O lote permanece avaliação da versão congelada, sem treino ou
ajuste pós-resultado nesta rodada. Caso oriente um sucessor, passa a
desenvolvimento para esse sucessor, exigindo outra reserva independente.
As três perdas históricas e possível perda LIVE permanecem. Próximo trabalho
é de percepção/classificação e coleta no uso delimitado; V2 não foi promovido
a configurações LIVE. [Tabela por caso e reprodução](RELATORIOS/EVOLUCAO_DETECTOR_04.md).
