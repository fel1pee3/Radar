# Decisão limitada de percepção — 26/10/2026

**Rodada executada; nenhum substituto aprovado e nenhum ensaio físico preparado.**
A referência REFERENCE_4_SPIN/RTMO_ADAPTIVE_V3 continua sendo comparador.
Ela também falha nos critérios; não é verdade de terreno nem solução aprovada.
A medição/avaliação foi corrigida. A regra geométrica congelada e a única
alternativa detector leve + RTMPose não demonstraram reconhecimento suficiente.

## 1. Estado preservado e ambiente

HEAD inicial `bb768abfe0c25e8f9d8a8127c455591718831be6`.
As alterações já existentes foram arquivadas antes da edição; não foram revertidas.
Raiz privada desta rodada:
`.local/detector-evolution/perception-decision-965d2e5d-b865-4cce-b328-7631dc9017a3/`.
Ponteiro: `.local/detector-evolution/decision-current.json`.

`initial-workspace.zip`, `initial-hashes.json` e `initial-status.txt` preservam o
início. `preserved-root.json` identifica a rodada anterior. Não foram regravados
seus traces, avaliações, protocolos, pesos ou resultados. Referência, V1, V2,
ROI, classificador, vídeos, polígonos, banco e credenciais existentes mantidos.
O experimento ROI continua privado e não registrado como estimador normal.

Windows 11 Pro, build 26200, PowerShell 5.1.26100.9711, Ryzen 5 5625U,
12 CPUs lógicas e 15,4 GiB visíveis. Python 3.12.15, uv 0.13.4,
ORT 1.23.2, NumPy 2.5.4 e opencv-contrib-python 5.0.0.93.
Sem abertura de webcam, gravação, HTTP de eventos ou acesso de escrita ao banco.
As filas do smoke test são novas e isoladas.

## 2. O que explica os 725 segundos

A execução original é ROI, cauca-11, r1; permaneceu intacta.

| Medida bruta | Valor |
| --- | ---: |
| Último frame decidido, tempo de mídia | 2150 ms |
| Duração do arquivo | 10400 ms |
| Inferência desse frame | 215,394 ms |
| Estágio checkpoint | 725127,762 ms |
| Processamento total do frame | 725349,647 ms |
| Idade registrada ao finalizar a decisão | 725381 ms |
| Maior intervalo entre inícios de análises no host | 312 ms |
| Maior intervalo entre decisões finalizadas, reconstruído | 725344 ms |
| CPU do processo / tempo total | 11,344 s / 729,284 s |
| Frames pulados pelo produtor atrasado | 152 |

O log System do Windows registra suspensão por **Button or Lid**, sono de
20:59:40,670 UTC a 21:11:47,023 UTC, e ajuste do relógio civil de
724475 ms na retomada. A decisão final foi registrada às 21:11:46,776 UTC.
A evidência sustenta suspensão/interrupção do computador durante o intervalo
contabilizado no checkpoint. **Não sustenta 725 s de computação SQLite ou
inferência.** Não há instrumentação interna para localizar a instrução exata
da transação na qual ocorreu a suspensão. Evidência privada: `power-events.json`
e trace original identificado em `temporal-regrade-final/regraded.json`.

Não houve erro de unidade milissegundo/nanosegundo. O tempo decorrido incluía a
interrupção; o erro era aceitar esse resultado como transmissão adequada.
A fonte terminou de decodificar pulando frames após a retomada. Como não houve
nova análise, o intervalo entre **inícios** não mostrou a pausa final.
EOF e exit 0 só comprovavam encerramento do arquivo.

### Correções realizadas

- `stream_acceptance.py` inclui idade da decisão final, intervalos entre
  decisões no host e cobertura sobre a **duração inteira** da fonte.
- A reconstrução usa os pares monotônicos de término/idade já existentes;
  não depende do relógio UTC nem troca os timestamps da mídia. Existe fallback
  documentado para traces sem esse par; os originais desta comparação têm o par.
- Intervalos elegíveis exigem observações atuais nos dois extremos, lacunas de
  mídia e host de até 500 ms e idades de até 2000 ms. Cobertura mínima 80% e
  prazo de evento 5000 ms foram preservados.
- Latência técnica de evento é medida desde a origem do stream/intervalo
  anotado até a decisão no host, além da latência de mídia. Os três alvos
  técnicos deste lote começam em 0 ms; isso é específico ao protocolo existente.
- `evaluation.py` usa a duração declarada e verificada do vídeo no denominador,
  inclusive cabeça/cauda não observadas. Não muda alvos ou exclusões.
  `observedMs` preserva o tempo observado; `evaluatedDurationMs` identifica
  separadamente o denominador completo.
- `benchmark-stream.py` inclui `wallTimingAcceptance`. `complete` continua
  significando EOF íntegro; não é aprovação de percepção. O gate temporal
  também exige contexto/anotações para o aceite final.

O caso suspenso passa de 100% sobre o trecho observado para **18,75%** de
cobertura válida da fonte completa, com uma decisão velha e cauda de 8250 ms.
**Reprovado, inclusive sendo a última decisão/EOF.** Nenhum valor foi descartado.

A proteção do worker normal contra frame velho ocorre depois da inferência.
Ela não constitui deadline de transação ou de entrega: o checkpoint pode atrasar
depois desse ponto. Esta entrega corrige a avaliação e o relógio técnico;
não afirma ter implementado cancelamento transacional ou resolvido esse risco.

### Outra inconsistência: idades iniciais negativas

Quatorze das 96 execuções continham 15 idades iniciais negativas, de poucos ms.
O produtor FILE guardava o instante **agendado** como aquisição e não rechecava
um timeout que acordasse antes dele. Isso não indica ausência dos tempos finais.
Os pares de término/idade permitem reconstruir o horário final no eixo do host.

A consolidação preliminar estrita marcou alguns desses registros como ausentes
e imprimiu 14/10/14/18 aprovações; ela foi preservada em
`temporal-regrade/` e `temporal-regrade-exact/`, mas **não é o resultado final**.
Não se truncou a idade negativa para zero. A avaliação final conserva sua
contagem e usa o tempo final disponível. Em novas execuções, PacedFileSource
recheca a espera e registra publicação monotônica real, mantendo PTS e taxa 1×.
O smoke final registrou 33 decisões, zero idades iniciais negativas, idade
máxima 578 ms, gap de mídia máximo 360 ms e cobertura de captura 96,9072%.
É teste técnico de FILE conhecido como vazio; não comprova webcam nem deduz
ambiente vazio pela ausência de pose.

## 3. Reavaliação uniforme, sem repetir as matrizes

Foram recalculados os mesmos 96 streams e 144 arquivos, quatro métodos.
Não se selecionou outra execução para substituir a suspensão.

| Método | Streams: anterior → final /24 | FILE completo: anterior → final /36 |
| --- | ---: | ---: |
| Referência | 14 → 14 | 30 → 27 |
| V1 | 13 → 13 | 26 → 25 |
| V2 | 17 → 17 | 29 → 27 |
| ROI experimental | 22 → 21 | 27 → 26 |

FILE não ritmado é avaliação em tempo de mídia, não comprovação de tempo real.
Novas perdas de aceite pelo denominador completo: cauca-03 e cauca-12 na
referência; intake16-08 em todos os métodos; cauca-03 em V2.
Os resultados anteriores continuam históricos, com esta retificação explícita.
O CSV [de reavaliação](DECISAO_PERCEPCAO_REAVALIACAO_2026_10_26.csv) contém as 240 linhas.

As quatro perdas históricas — floor03, floor05, floor07 e controlled-lying —
continuam perdas de episódio. Bons frames esparsos em floor07 não as corrigem.
Cauca-10 e chair08-01 continuam controles inconclusivos; nada foi convertido
em acerto por silêncio. Os episódios antigos e a ausência de alertas indevidos
registrada no protocolo anterior não foram reescritos.

## 4. Última prova pequena da geometria ORIGINAL

Protocolo e regra congelados antes das novas previsões:
`protocol.frozen.json`, SHA-256
`9b31775b6b0dcec099c55f2f4625f04f7a6d29ceef39bf18e8014869385bf6a6`.

Construção: yoga2-01, intake16-10, cauca-11, intake16-15.
Verificação: yoga2-02, intake16-03, cauca-08, cauca-12, intake16-07, floor07.
Três frames por vídeo, nos PTS mais próximos de 10%, 50% e 80% da duração,
escolhidos antes da inferência. Trinta frames únicos, duas repetições nativas por
caminho; referência real executada uma vez por frame, após aquecimento igual.
Separação interna por vídeo, **não por participantes independentes**.
Todo o material continua DEVELOPMENT, já conhecido pelo projeto.

A proposta corporal atual pode orientar uma tentativa, nunca aceitar uma pessoa
abaixo do limiar. A regra usa o vetor médio ombros→quadril em pixels:
horizontal escolhe 270°/90° conforme seu sinal; invertido vertical escolhe 180°;
caso contrário CENTER_80. Núcleo ausente orienta recorte da proposta atual.
A regra é heurística, não uma garantia de orientação anatômica canônica.
Não usa nome, rótulo, timestamp absoluto, pose anterior ou resultado futuro.
Máximo duas chamadas, início da segunda antes de 220 ms; limiares preservados.

Comparadores: ORIGINAL→CENTER_80 fixo e busca de referência existente.
Critério prévio: recuperar pelo menos 80% dos frames ORIGINAL insuficientes na
verificação, sem perder corpos contra a escolha fixa, sem novo LYING indevido
nos controles; custo mediano ≤200 ms e P95 ≤500 ms; inspeção anatômica obrigatória.

| Verificação | Frames únicos com oito essenciais /18 | Custo médio / mediano |
| --- | ---: | ---: |
| Regra geométrica | 17 | 147,7 / 118,1 ms |
| Fixa CENTER_80 | 14 | 148,4 / 118,1 ms |
| Busca real da referência | 18 | 194,8 / 142,7 ms |

Geometria/fixa somam tempos das inferências contrafactuais do frame atual;
não são duas transmissões independentes. A referência executa sua busca real.
Custos dessa tabela incluem preparação/inferência/restauração, sem persistência,
prévia ou aquisição; não são desempenho do sistema completo.

A regra recuperou **3/4 frames insuficientes (75%)**, todos os três do mesmo
vídeo intake16-03 por rotação 180°. Perdeu yoga2-02 aos 1600 ms nas duas
repetições: escolheu 90°, enquanto 270° reconhece a pessoa deitada.
A direção escolhida não é sustentada por esse contraexemplo. Não foi invertida
depois de olhar esse resultado para fazer o vídeo passar.
Nove frames de construção com pessoa já eram completos em ORIGINAL; os três
vazios ficaram sem pose. A construção não forneceu demonstração de qual
recuperação generalizaria.

**Esta regra não sustentou o critério e foi encerrada, sem nova busca de margens.**
Existe sinal útil limitado, não evidência para descartar toda geometria possível
ou para promover um seletor. Os sete frames históricos permaneceram diagnóstico,
não foram reapresentados como conjunto independente.

Foram confrontadas imagens, poses restauradas e posturas. Recuperação de oito
pontos não é oito articulações comprovadamente corretas: pernas sobrepostas,
oclusão pela cadeira e apoio no mobiliário continuam ambíguos. Nenhum ground
truth articular foi inventado. As imagens privadas e os pontos atuais permitem
auditar essa limitação.

## 5. Uma alternativa: localização independente + RTMPose

Usado o par lightweight documentado pelo RTMLib: **YOLOX-tiny HumanArt 416×416 +
RTMPose-s Body7 192×256**, CPU ORT com quatro threads/uma interop/spin, mesma
família da referência. Não houve varredura de modelos. O índice consultado não
fornecia RTMDet-nano pessoa em ONNX pronto; escolheu-se o par oficial leve da
biblioteca, sem exportar uma nova cadeia PyTorch/MMDeploy.

[Código RTMLib e licença](https://github.com/Tau-J/rtmlib/blob/main/LICENSE).
O par é descrito na [solução oficial Body](https://github.com/Tau-J/rtmlib/blob/main/rtmlib/tools/solution/body.py).
Pesos obtidos do [espelho do autor](https://huggingface.co/Tau-J/RTMPose/tree/main),
revisão fixada `cd4d7095f5cfc9cfc4f46289bee91ea4a1e1d9fd`.
Os ZIPs incluem metadados de deploy com origem dos checkpoints OpenMMLab.

| Artefato ONNX | SHA-256 |
| --- | --- |
| Detector | ceb11c07298f95c50d7c5abeb906d03340c85f23aa79e3e66966e7fb6c307250 |
| Pose | 9aeb635b83f86aea45cf45d85798f7eba1a162de8e0d721c44e54fe5eebaf47d |

**Código e pesos foram conferidos separadamente.** O pacote RTMLib 0.0.16
tem licença Apache-2.0; o repositório dos modelos também declara Apache-2.0.
Há [declaração do autor sobre a série RTMPose](https://github.com/Tau-J/rtmlib/issues/65).
Os arquivos consultados não trazem uma licença individual resolvendo todos os
termos dos dados de treino HumanArt/Body7 para esses dois checkpoints.
Isso permanece pendente para incorporação/distribuição; não se concluiu que
a licença do código, sozinha, autoriza qualquer uso dos pesos. Não se
redistribuíram modelos nem se treinaram pesos nesta rodada.

Ambiente isolado em `.local/pose-env-965d2e5d/`, com pyproject e uv.lock próprios.
A primeira localização mais longa falhou na carga de DLL do Windows e foi
preservada. Copiar os mesmos bytes para caminho curto resolveu a carga.
O wheel foi extraído em vendor privado, com hash verificado, sem instalar seus
dois requisitos concorrentes de cv2: o ambiente contém **somente**
opencv-contrib-python. Os lockfiles/ambiente da aplicação não foram alterados.

### Anatomia, coordenadas, scores e custo completos

Mesmos 30 frames, duas repetições; PNG sem perdas com hash BGR igual ao da
inferência RTMO. Uma passagem preliminar com JPEG foi preservada e excluída da
comparação final. Não foi escolhida a melhor repetição por vídeo.

COCO-17: 5/6 ombros, 7/8 cotovelos, 9/10 punhos, 11/12 quadris, 13/14 joelhos,
15/16 tornozelos, convertidos para os índices corporais existentes.
Pré/pós-processamento oficial mantém escala/centro do recorte SimCC; quarter-turn
é restaurado para a imagem original, sem trocar rótulos esquerdo/direito.
As pranchas finais foram inspecionadas em conjunto com os frames sem desenho.

Native scores SimCC: **0,1161–0,9155** neste lote, identificados como
RTMPOSE_SIMCC_SCORE, sem inventar visibility/presence. Estar em [0,1] não
calibra esse score como RTMO. O classificador atual foi aplicado apenas em
**shadow diagnóstico** com proxy explícito de score/limiar; seu resultado não
autoriza evento nem é um contrato novo de produção. Modelo/artefato/política
da aplicação continuam vinculados ao RTMO.

Recuperação limitada a ORIGINAL e 270°, segunda orientação iniciada antes de
220 ms quando a observação atual é insuficiente. Até um detector e uma pose
por orientação; multiplicidade fica inconclusiva, sem escolher uma pessoa.
Máximo quatro chamadas de rede por frame nesse experimento; esse custo não
foi apresentado como o orçamento de duas chamadas do seletor RTMO.

| Medida final | Construção, 24 observações | Verificação, 36 observações |
| --- | ---: | ---: |
| Oito essenciais pelo proxy, não prova de visibilidade | 8 | 12 |
| Sem pose selecionada | 14 | 12 |
| Multiplicidade reportada | 6 | 4 |
| Processamento completo médio | 50,3 ms | 61,5 ms |
| P95 / máximo | 78,9 / 82,3 ms | 99,7 / 105,1 ms |
| Detector, soma média por análise | 43,7 ms | 50,6 ms |
| Pose, soma média por análise | 5,8 ms | 9,9 ms |
| Chamadas médias / máximo | 1,83 / 3 | 2,50 / 4 |

Inicialização das duas sessões: 190,1 ms; aquecimento sintético: 45,6 ms,
ambos separados da média. O custo completo inclui localização, recortes,
inferências, transformações, restauração, pós-processamento e shadow classifier.
Começa no frame já decodificado, como o perfil de processamento da referência;
não inclui captura, persistência, HTTP ou desenho. Não é FPS LIVE garantido.

Observações pelas imagens, não apenas contagem:

- Yoga2-02 aos 1600 ms: pessoa deitada visível, sem localização aceita na
  alternativa; a referência recupera. É falha de localização/recuperação.
- Intake16-03: poses parciais e, em outros frames, multiplicidade de caixas
  para uma pessoa. No detector exportado aparecem duas caixas de pessoa
  sobrepostas, não duas pessoas comprovadas. Sem relaxar multiplicidade.
- Intake16-10: falsa caixa no sofá além da pessoa. Saídas nativas e labels
  foram inspecionados; não se tratou todo segundo box como pessoa verdadeira.
- Cadeira: a perna oculta continua incerta; desenho mais curto pode representar
  score insuficiente, não necessariamente pior localização de toda a pessoa.
- Yoga2-01 aos 2503 ms: cena deitada e pose visualmente plausível, mas o shadow
  classifier chama SEATED. Compatibilidade da distribuição/descritor precisa
  de validação separada; não se atribuiu todo erro ao estimador.
- Cauca-11/12: perda de membros na postura baixa e ausência de localização
  na recuperação. Cômodo vazio permaneceu sem pose, sem alegar prova pelo silêncio.
- Suplemento de pegar objeto/abaixar: três frames de intake16-08, definidos
  em protocolo separado antes das inferências suplementares. Shadow SEATED
  nos três; seis/oito/oito essenciais pelo proxy. Não são avaliação reservada
  nem foram adicionados para aumentar a taxa do gate principal. O membro
  sobreposto continua sem ground truth de visibilidade.

**Custo promissor; reconhecimento não preservado. Alternativa rejeitada nesta
configuração.** Não se executou a matriz completa nem se geraram episódios
para alegar taxa de alerta/latência/duplicação. Não há resultado novo de evento
da alternativa a entregar/revisar no painel. Falha em qualidade antes dessa
fase é motivo para parar, não para publicar um novo detector.

## 6. Evento diferente da referência não é erro automático

Em cauca-01, referência emite PERSON_ON_FLOOR; ROI, POSSIBLE_FALL, ambos aos
5000 ms. A sequência de 1600–4000 ms mostra pessoa saindo da cadeira e
descendo ao piso. A mudança é **visualmente plausível**; igualdade de tipo
com a referência não foi exigida.

A anotação existente é de postura depois da transição, início 4000 ms com
incerteza aproximada de 500 ms, sem intervalo preciso de descida anotado.
As trajetórias do quadril e a disponibilidade de pose antes do episódio
diferem entre os métodos. Classificação LYING já aos 3000 ms também pode ser
precoce em relação à postura final no piso. Assim, o tipo POSSIBLE_FALL não
foi contado como transição validada nem como erro apenas por divergir.
Precisão temporal da transição permanece inconclusiva; anotação preservada.
Queda encenada não comprova acidente real ou necessidade de assistência.

## 7. Decisão e próximo trabalho concreto

1. **Avaliação temporal correta antes? Não.** Ignorava cauda completa e podia
   aprovar decisão final muito atrasada. Suspensão explica o grande tempo
   decorrido, não custo de inferência. Mecanismo de avaliação/relógio corrigido.
2. **Geometria prediz recuperação fora da construção? Parcialmente, abaixo do
   gate.** Três frames de um vídeo recuperados; outro vídeo discriminante perdido.
   Regra congelada encerrada nesta rodada; não há justificativa para integrá-la.
3. **Alternativa melhora custo e qualidade juntos? Não.** Muito mais rápida,
   mas perde localização/corpo e apresenta incompatibilidade do classificador.
4. **Onde estão os erros?** Localização: falso box/duplicidade/ausência.
   Pose: oclusão e corpo parcial. Classificação: distribuição do estimador e
   posturas confundidas. Contexto: ROI 2D não comprova contato ou altura; não
   houve alteração de polígonos. Temporal: lacunas, persistência/interrupção
   e denominador de avaliação. Não são todos o mesmo problema.
5. **Estratégia que continua:** preservar a referência para comparar futuras
   correções; não promover V1/V2/ROI, regra geométrica ou esse par RTMPose.
   Uma inferência leve cabe no orçamento observado; o bloqueio não é uma
   impossibilidade geral de CPU. Na referência, recuperação múltipla ainda
   custa; no par leve, faltam localização robusta e observações compatíveis.
6. **Antes do teste físico curto:** corrigir/tratar deadline de decisão que
   atravesse persistência/interrupção; demonstrar em FILE localização de
   pessoa deitada/ocluída sem caixa de sofá ou duplicidade não resolvida;
   qualificar scores e o classificador separadamente com pontos anotados ou
   visibilidade humana suficiente. Só depois disso há fundamento para nova
   comparação completa desde inicialização/perda/reaquisição, com custo total
   e os gates corrigidos. Nenhuma nova webcam está preparada como aprovada.

Faltam capacidade demonstrada de localização/pose nessas vistas e referência
articular/visibilidade para separar definitivamente alguns erros. Não faltou
uma confirmação rotineira do fundador. Não se solicita outra gravação física
para compensar esses problemas técnicos.

## 8. Implementação e verificações executadas

Arquivos desta rodada: módulo/testes de stream_acceptance; correção de relógio
e teste de PacedFileSource; denominador de evaluation.py; integração no
benchmark-stream.py; CLI read-only regrade-streams.py; este relatório/CSV,
STATUS, índice de relatórios, README e D58. Scripts e fontes experimentais
executados permanecem privados na raiz apontada e em
`rtmpose-experiment/executed-sources/`, com modelos fora do Git.

| Comando efetivamente executado | Resultado |
| --- | --- |
| git status --short; leitura de AGENTS/README/STATUS/relatórios/código | Alterações existentes inventariadas e preservadas |
| Get-WinEvent, System, janela 17:58–18:13 local, IDs 1/42/107 | Suspensão/retomada e ajuste de relógio encontrados |
| uv run --project services/edge --frozen python scripts/validation/regrade-streams.py ... | 96 streams + 144 FILE recalculados, sem nova inferência |
| uv run --project services/edge --frozen python .local/detector-evolution/probe-perception-choice.py | 30 frames, seis caminhos, duas repetições, referência por frame |
| uv run --project services/edge --frozen python .local/detector-evolution/prepare-rtmpose-isolated.py | ZIPs/wheel oficiais documentados obtidos e hasheados |
| uv sync --project .../rtmpose-experiment --python services/edge/.venv/Scripts/python.exe | Ambiente criado; primeiro caminho falhou por comprimento da DLL |
| uv sync --project .local/pose-env-965d2e5d --frozen --python services/edge/.venv/Scripts/python.exe | Mesmo lockfile em caminho curto; carga funcionou |
| uv run --project .local/pose-env-965d2e5d --frozen python .local/detector-evolution/probe-rtmpose-isolated.py | 60 observações finais com PNG idêntico; preliminar JPEG preservada |
| probe-rtmpose-isolated.py --input .../bending-input.json --output .../bending-results.json | Seis observações suplementares, fora do gate |
| uv run --project services/edge --frozen python scripts/validation/benchmark-stream.py ... | Dois smoke tests FILE isolados; o final usa o relógio corrigido, EOF/exit 0 |
| uv run --project services/edge --frozen pytest services/edge/tests -q -rs | **424 passed, 1 skipped**, 18,99 s; skip da GUI explícita |
| uv run --project services/edge --frozen ruff check services/edge scripts/validation | Passou |
| uv run --project services/edge --frozen ruff format --check services/edge scripts/validation | 91 arquivos já formatados |

Houve checks intermediários e ajustes de lint, além do diagnóstico nativo do
detector e inspeções das pranchas com view_image. Logs finais:
`pytest-final-summary.json` e `executor-smoke-final.log`. Não foram repetidos build,
testes TS/API/E2E: não houve alteração nesses componentes nesta rodada.
Teste de engenharia não aprova percepção; a GUI ignorada não é evidência
de câmera física.

## Reproduzir sem câmera

Na raiz, para auditar os originais novamente e criar saída nova:

```powershell
. ./scripts/activate.ps1
$round = (Get-Content .local/detector-evolution/decision-current.json | ConvertFrom-Json).root
$out = Join-Path $round ("regrade-" + [guid]::NewGuid())
uv run --project services/edge --frozen python scripts/validation/regrade-streams.py --experiment-root .local/detector-evolution/stabilization-ce12cde8-31ee-4665-9727-c5f1da1111d5 --output $out
uv run --project services/edge --frozen pytest services/edge/tests/test_stream_acceptance.py services/edge/tests/test_paced_file.py services/edge/tests/test_floor_acceptance.py -q
```

Reexecutar somente a pequena alternativa, com artefatos privados já existentes:

```powershell
. ./scripts/activate.ps1
$round = (Get-Content .local/detector-evolution/decision-current.json | ConvertFrom-Json).root
$out = Join-Path $round ("rtmpose-repeat-" + [guid]::NewGuid() + ".json")
uv sync --project .local/pose-env-965d2e5d --frozen --python services/edge/.venv/Scripts/python.exe
uv run --project .local/pose-env-965d2e5d --frozen python .local/detector-evolution/probe-rtmpose-isolated.py --output $out
```

O script recusa sobrescrever resultados existentes. Essas reproduções
dependem dos vídeos/artefatos privados desta máquina. Nenhum segredo é pedido.
Sem commit, push, deploy ou aprovação integral do MVP.
