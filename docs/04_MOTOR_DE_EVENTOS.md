# Motor temporal e baseline de visão

[Voltar ao README central](../README.md)

## O que a IA faz

MediaPipe estima pontos do corpo. Um módulo de regras temporais usa esses pontos para gerar uma suspeita. Não há treinamento de detector de quedas nem interpretação de intenção. O motor precisa ser uma função testável sobre observações, desacoplada de OpenCV, HTTP e banco.

Modelo inicial: Pose Landmarker **Lite**, MediaPipe Tasks. Pedir até duas poses para poder sinalizar múltiplas pessoas detectadas, mantendo a classificação restrita a uma pose válida. Desativar máscara de segmentação. Testar o custo real no notebook.

Resultado da investigação da etapa 05 (D34): o **Full float16/v1** foi comparado
e passou a ser uma opção explícita para a bancada. Lite permanece como padrão
das configurações anteriores. Ambos exigem bundle oficial com SHA-256 fixado,
duas poses e os mesmos gates; não há troca automática nem redução de qualidade.
O Full viabilizou o fluxo positivo em um arquivo, mas não resolveu todos os
enquadramentos. Veja [investigação 05](RELATORIOS/INVESTIGACAO_ETAPA_05.md).

Usar inicialmente `VIDEO`/`detect_for_video` com timestamps estritamente crescentes tanto para arquivo quanto para a sequência amostrada de webcam. É uma escolha síncrona para facilitar reprodutibilidade; não exige arquivo físico. Captura ao vivo e análise são desacopladas por buffer de um frame. `LIVE_STREAM` assíncrono só entra por decisão posterior motivada.

## Observação interna

Cada observação inclui `runId`, número do frame, timestamp monotônico/mídia, largura/altura, lista de poses, visibilidade de pontos, qualidade do frame, versão da calibração e duração da inferência. Não enviar observações contínuas à API.

Pontos essenciais: ombros e quadris para eixo do tronco; joelhos e tornozelos para extensão do corpo. É necessário haver evidência suficiente dos pontos usados. Não transformar landmarks ausentes em zeros. O `visibility` do modelo é usado como gate técnico e não como chance de emergência.

## Calibração inicial

O operador marca um polígono da região do piso em coordenadas normalizadas sobre um frame local, excluindo cama, sofá e regiões ocultas. O arquivo local inclui resolução/relação de aspecto, orientação e identificação da configuração. Não armazenar o frame de calibração por padrão.

Se a câmera mudar fisicamente, rotacionar, usar PTZ ou alterar proporção, recalibrar. O software detecta mudança de resolução/proporção quando possível; não prometer detectar qualquer deslocamento físico. Desligar auto-tracking/PTZ durante o teste da câmera IP.

## Sinais da baseline v0.1

Todos os valores abaixo são **pontos de partida experimentais para a bancada**, sujeitos a revisão no conjunto de calibração. Não são limiares clínicos, nem foram validados neste documento.

| Parâmetro | Inicial | Uso |
| --- | --- | --- |
| `targetAnalysisFps` | 5 | Taxa pretendida; medir taxa efetiva |
| `minLandmarkVisibility` | 0,5 | Exigir pontos essenciais visíveis |
| `minTorsoAngleDeg` | 60° em relação à vertical | Tronco aproximadamente horizontal |
| `maxBboxAspectRatio` | 1,0 (altura/largura) | Corpo com extensão predominantemente horizontal |
| `floorHoldMs` | 2.000 | Persistência mínima da postura candidata |
| `minValidPoseFraction` | 0,8 na janela | Qualidade temporal suficiente |
| `maxObservationGapMs` | 500 | Lacuna maior invalida continuidade da suspeita |
| `rapidDescentWindowMs` | 1.000 | Janela anterior à postura no chão |
| `minHipDescentNormalized` | 0,18 da altura da imagem | Deslocamento descendente de quadril para rótulo possível queda |
| `rearmHoldMs` | 3.000 | Tempo fora da postura candidata, com observação válida |

Corrigir proporção antes de calcular ângulo e bbox: `x * largura` e `y * altura`. Ângulo em coordenadas normalizadas sem considerar resolução distorce a medida. Bbox usa somente pontos corporais válidos; bbox degenerada ou corpo cortado invalida a observação.

Postura candidata exige simultaneamente: exatamente uma pose suficiente, centro dos quadris dentro do polígono de piso, tronco com ângulo mínimo e proporção corporal compatível. Usar janela temporal com cobertura ponderada por tempo, não número fixo de frames; exigir pelo menos 5 observações válidas na janela inicial. Uma observação válida com postura contrária zera a suspeita. Observações inválidas não contam como postura positiva e só toleram lacunas de até 500 ms. A janela precisa alcançar 2 s com pelo menos 80% de tempo coberto por observações válidas candidatas. Pontos esparsos não podem completar a janela apenas pela passagem do relógio.

Uma descida rápida exige quadris válidos antes e depois, mesma continuidade da pose, fonte sem mudança de configuração e deslocamento descendente no intervalo. Ela só muda o rótulo para `POSSIBLE_FALL` **depois** de satisfazer a persistência no chão. Sem trajetória suficiente, usar `PERSON_ON_FLOOR`.

Essa regra pode confundir alongamento, deitar voluntariamente ou perspectiva. O polígono não mede altura real em 3D. Registrar esse limite e os confundidores; não ocultá-los com linguagem de certeza.

O ângulo e a proporção são relativos aos eixos da imagem. Pessoa deitada na
direção da profundidade pode projetar tronco vertical e caixa alta, falhando na
regra mesmo com quadril dentro do piso e pontos suficientes; isso foi observado
em `piso-d`. Para floor-v0.1, o enquadramento precisa permitir a projeção corporal
predominantemente horizontal prevista nos gates. Não se declara suporte a toda
vista superior/diagonal. Uma homografia do piso ou world landmarks centrados no
quadril não fornecem automaticamente gravidade/altura física para resolver isso.
Não girar a imagem ou deslocar ROI apenas para forçar alerta. Uma política que
amplie esse domínio exigirá versão própria, calibração e avaliação separadas.

## Máquina local por câmera

| Estado | Entrada | Saída/comportamento |
| --- | --- | --- |
| `OBSERVING` | Captura e configuração válidas | Ao iniciar postura candidata, ir a `SUSPECTED` |
| `SUSPECTED` | Janela candidata em andamento | Se critérios completarem, persistir episódio/evento e ir a `ACTIVE`; se perder continuidade, voltar a observar |
| `ACTIVE` | Evento já criado | Nenhum novo evento para a mesma situação; manter episódio mesmo se envio falhar |
| `REARMING` | Postura deixa de ser candidata de forma observável | Após 3 s válidos, fechar episódio local e voltar a observar; se postura voltar antes, retornar a `ACTIVE` |

Qualidade insuficiente congela o episódio `ACTIVE`, mas não conta tempo para rearmar. Em `SUSPECTED`, lacuna acima de 500 ms zera a suspeita. Sair do enquadramento não comprova recuperação e não encerra o incidente. A v0.1 pode exigir reset manual explícito do episódio local após saída prolongada; registrar reset com motivo e nova execução. Não repetir alerta continuamente porque a pessoa permaneceu no chão.

Persistir `episodeId`, `eventId`, estado ativo e evento na mesma transação SQLite. Em reinício, restaurar episódio ativo para evitar duplicação da mesma cena; não reutilizar relógio monotônico da execução anterior. Reiniciar a janela de rearmamento. Trocar a fonte/calibração exige parar a execução e iniciar uma nova configuração, com histórico do reset.

O fechamento do episódio local habilita detectar uma nova situação. O fechamento do incidente na API é uma ação humana independente. Não bloquear nova situação só porque o incidente anterior continua aberto.

## Captura e qualidade

- Arquivo: ler timestamps da mídia; verificar monotonicidade. Se necessário, usar índice/FPS validado, registrando o fallback. Não usar velocidade do CPU como tempo da cena.
- Webcam: relógio monotônico do host; capturar o frame mais recente. Não repetir a última imagem como se fosse nova após erro de leitura.
- Terminar arquivo gera `ENDED`, não “câmera offline inesperada”. Pausa solicitada gera `PAUSED`.
- FPS abaixo do necessário, baixa iluminação e repetição suspeita são flags. “Imagem possivelmente congelada” é uma heurística: cena parada ou pessoa imóvel também pode produzir frames semelhantes.
- O teste determinístico de congelamento injeta frames/timestamps repetidos. No equipamento real, medir falsos avisos dessa heurística. Não afirmar detecção universal de obstrução.
- Duas poses, corpo cortado, baixa visibilidade ou ausência de ROI impedem classificar aquela janela. Registrar motivo de indisponibilidade da observação, sem inventar resultado negativo.

Defaults técnicos de qualidade, também experimentais: FRAME_TIMEOUT após 2 s sem frame novo; LOW_FPS abaixo de 2 análises/s por 5 s; LOW_LIGHT com luminância média abaixo de 25/255 por 2 s; POSSIBLE_FROZEN após 10 s de frames decodificados byte a byte idênticos. Essas condições tornam novas janelas inelegíveis. Registrar períodos de aquecimento/fim de arquivo separadamente e não aplicar limiar de FPS de relógio civil ao replay acelerado. Permitir ajustar os limiares com versão registrada; medir falsos avisos em cena estática e iluminação real.

## Avaliação e evolução

Separar captura, estimativa de pose, extração de features, regras, persistência e transporte. A primeira avaliação pode mostrar que MediaPipe não basta nas condições pretendidas. Nesse caso, manter o fluxo e comparar outro modelo via interface, com licença e regressão documentadas.

Feedback de operador não atualiza parâmetros automaticamente. Revisar, criar nova versão de política e reexecutar cenários separados da calibração. Não ajustar no conjunto final e reapresentá-lo como teste independente. IDs de modelo/política/calibração devem permitir reproduzir cada resultado.

## Candidato RTMO da etapa 08 — 23/10/2026

RTMO-s é selecionável explicitamente para investigação da pose falsa na cadeira.
Não altera os defaults Lite/Full nem as configurações já existentes. Usa ONNX
Runtime CPU, quatro threads intra-op/uma inter-op, sem RTMLib. Só exporta os doze
pontos corporais COCO correspondentes aos índices anatômicos 11–16 e 23–28 usados
pelo Radar. Ausentes não são interpolados, e não são inventados dedos/pés, z,
visibility ou presence. Pessoas distintas detectadas são preservadas após NMS;
a existência de uma única pose continua obrigatória para classificar.

Política `floor-rtmo-score-v0.1`: `qualitySource=RTMO_KEYPOINT_SCORE` e
`minKeypointScore=0.5`. Exige todos os oito pontos essenciais, finitos, dentro
do quadro e com score suficiente. Score é uma medida nativa do estimador,
sem equivalência comprovada com visibilidade física, presence ou probabilidade
de emergência. Modelos/políticas de origens de qualidade distintas não podem
ser misturados. Os demais gates geométricos, de qualidade temporal, persistência,
rearmamento e idempotência são preservados. A família de política e o novo campo
de evidência são definidos por D46/D47 e pelo contrato compartilhado atualizado.

Na comparação integrada de 20 clipes, os três perdidos continuaram sem evento.
Qualidade de pose melhorou, mas os quadris estimados ficaram fora da ROI nos
trechos deitados. Uma ROI de pixels do chão não mede a altura real do quadril ou
a espessura do corpo na projeção. Não expandir ROI para parede/móvel nem reduzir
os gates para transformar perdas em aprovação. Estudar/calibrar a geometria com
versão explícita e avaliação independente antes de prometer correção geral.
Novos alertas em ADL podem corresponder a postura voluntária no piso; não
presumir necessidade de ajuda ou classificar automaticamente como falso/verdadeiro
sem anotação de cena. [Resultados](RELATORIOS/INTEGRACAO_RTMO_ETAPA_08.md).
# Evolução opt-in do motor — 24/10/2026

As seções anteriores documentam a baseline. O candidato LINEAR_CONTEXT_V1 é
experimental e exige artefato privado com SHA-256, instalação declarada,
calibração confirmada com hash e modelo RTMO-s correspondente. Não é ativado
por atualizar o repositório. [Escopo, resultados e aceite](EVOLUCAO_DO_DETECTOR.md).

Em vez de exigir horizontalidade projetada, o candidato usa 35 atributos de
articulações/relações corporais em pixels e contexto da imagem. Um classificador
linear ajustado localmente separa postura deitada de outras posturas: score
≥0,8 indica deitado; ≤0,2 indica outra postura; o intervalo é desconhecido.
Esses scores não são probabilidades calibradas. Todos os oito pontos essenciais
continuam exigindo qualidade nativa ≥0,5; desenho estabilizado não entra no motor.

O classificador principal é binário. Subtipos descritivos conservadores usam
geometria para em pé/caminhando e ajoelhado/abaixado; sentado exige contexto de
cadeira confirmado. Ambiguidade entre agachamento e cadeira permanece outra
postura/desconhecido. Não há acurácia multiclasse medida nem identificação de
apoio pela imagem. Áreas de cadeira/cama/rede configuradas são exclusões da
decisão de chão; sobreposição que torne contato inobservável deve ser excluída,
sem alegar medição física de altura pelo polígono.

EVIDENCE_V2 mantém janela de 2000 ms, cobertura positiva ≥80%, cinco observações
e lacuna máxima de 500 ms. Tempo positivo só é somado entre duas observações
positivas reais consecutivas. Uma oscilação curta não apaga imediatamente a
suspeita; desconhecido nunca acrescenta tempo positivo. Outra postura persistente
reinicia suspeita (600 ms); a tolerância de lacuna continua limitada a 500 ms.
Recuperação exige 3000 ms contínuos de outra postura reconhecida. Incerteza não
encerra o episódio persistido nem produz outro alerta. Pausa, reconexão e retomada
recriam janelas sem reutilizar tempo; episódio ativo continua preservado.

POSSIBLE_FALL requer, antes da postura deitada, pelo menos duas observações em
pé cobrindo 400 ms dentro da janela de 1000 ms, sem quebra de observação, e
descida observada do quadril ≥0,18 da altura da imagem. Sem essa evidência, a
persistência pode emitir PERSON_ON_FLOOR. Essa transição tem testes sintéticos;
seu desempenho em transições reais ainda precisa de validação específica.

Treinamento só por comando explícito posture-train. Manifesto registra licença,
hashes, anotações e divisões; seleção/reserva não são abertas para ajuste. Divisão
por participante ou por sessões conhecidas inteiras; reutilizar o fundador em
sessões novas não estabelece generalização entre participantes. A avaliação do
candidato acrescenta primaryFloorAcceptance: todos os alvos contam, inclusive
inelegíveis/excluídos, latência desde início anotado e limite de 5000 ms. O
matching histórico por tipo permanece secundário e inalterado.

Complemento experimental LINEAR_BODY_V2: descritor symmetric-body-shape-29-v1
remove seis atributos absolutos de posição/escala da imagem. Ajustado apenas
nos dados antigos; não demonstra generalização por ter menos atributos.
Artefato exige contextMode=OPERATOR_CONFIRMED_FIXED_CAMERA, SHA, calibração
confirmada e família floor-rtmo-score-posture-body-v2. A família anterior de
35 atributos mantém vinculação à instalação aprendida e comportamento congelado.
Na V2, outra postura reconhecida em uma exclusão de apoio continua evidência
negativa; postura deitada ou incerta ali permanece inelegível para confirmar
chão. Isso não transforma exclusão em prova de contato ou altura. Limiares de
qualidade 0,5, scores 0,8/0,2 e persistência não foram reduzidos.

Anotação local opcional transitionObserved=false declara que a cena não mostra
transição para o chão. POSSIBLE_FALL nessa faixa conta como alerta de postura
no resultado principal, mas também como unjustifiedTransitionAlerts e impede
approved. Não modificar a anotação após ver a previsão. Anotação ausente não
certifica transição e preserva a leitura histórica dos manifestos.


## Interrupção durante a decisão e persistência — 27/10/2026

LIVE e transmissão técnica FILE com instante de aquisição verificam idade
máxima de 2000 ms antes da decisão, antes e depois do checkpoint. Lacuna
do host >500 ms quebra continuidade mesmo com PTS próximo. Checkpoint que
retorna após >500 ms também invalida a observação para continuidade/cobertura.
A suspeita precisa de novas observações; episódio ativo persistido continua
ativo até recuperação válida. Não reutilizar pontos ou tempo positivo anterior.

Antes de iniciar a transação, emissão apenas em memória pode ser rejeitada
como NOT_STARTED se envelheceu. Depois de commit conhecido, preservar evento,
episódio, horários e envelope; auditar COMMITTED e quebrar continuidade.
Erro com resultado possivelmente confirmado é UNKNOWN, nunca rollback alegado.
O timestamp anterior continua no denominador de cobertura, como inelegível:
a lacuna não desaparece da avaliação.

SQLite v3 acrescenta delivery_timing/timing_audit. Contexto de relógio acompanha
o evento na mesma transação. Cada envio HTTP reavalia atualidade pela janela
contratual de 120 s e incoerência de relógio; não confundir essa janela com
a idade máxima de observação de 2 s. Nenhum cancelamento transacional ou
deadline do sistema operacional é prometido. FILE não cadenciado conserva
o relógio de mídia; testes de suspensão usam relógios injetados, sem hardware.
[Implementação e testes](RELATORIOS/CONTINUIDADE_E_REFERENCIA_VISUAL_2026_10_27.md).


## Candidata opt-in V4 (28–29/10/2026)

As regras anteriores continuam nas políticas existentes. A candidata
MULTICLASS_CONTEXT_V4 separa qualidade, suficiência corporal, postura e contexto
2D distribuído; POSTURE_DYNAMICS_V2 observa o movimento também no início da
suspeita. Usa somente pontos atuais do estimador, sem interpolação como evidência.
Não muda 2 s de persistência, 500 ms de lacuna, idade de 2 s ou rearme de 3 s.
O rótulo POSSIBLE_FALL exige trajetória adicional, não o nome do arquivo.
[Limites, resultados e reprovações](RELATORIOS/FECHAMENTO_CANDIDATA_V4_2026_10_28.md).
