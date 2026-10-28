# Referência parcial, probes e localização — 27/10/2026

**Rodada executada. Referência parcial utilizável; YOLOX-m não promovido.**
Foi corrigida a dependência entre diagnóstico de postura e referência humana
completa. Uma única alternativa recuperou a localização em F07/F13, mas trouxe
falso positivo/regressões e não resolveu a qualidade da pose automática.
Não avançar a vídeos completos, transmissão técnica ou webcam nesta rodada.

## 1. Preservação, escopo e ambiente

HEAD inicial `6146dfe509dc2c4adf0184c4f9c866ecd85f2a43`, main limpa.
Lidos AGENTS, README, STATUS e o
[relatório anterior](CONTINUIDADE_E_REFERENCIA_VISUAL_2026_10_27.md),
além dos auditores e contratos reais de percepção/classificação.
Não houve nova implementação de frescor nem investigação de threads.

Raiz privada nova:
`.local/detector-evolution/localization-partial-9eafe929-82f9-4e9d-9ce1-c08bf408735d/`.
Ponteiro: `.local/detector-evolution/localization-current.json`.
Snapshot anterior às edições: `initial-source.zip`, `initial-hashes.json`,
`initial-git.json`. Resultados/referências anteriores não foram regravados.

Windows 11 Pro build 26200, Ryzen 5 5625U, 12 CPUs lógicas, 15,4 GiB visíveis,
PowerShell 5.1, Python 3.12.15 e uv 0.13.4. Ambiente separado
`.local/localization-env-f408735d`, com cópia dos manifestos/lock anteriores:
ORT 1.23.2, NumPy 2.5.4, opencv-contrib-python 5.0.0.93 e um único provedor
de cv2. `uv sync --frozen` instalou 30 pacotes sem modificar o ambiente normal.
Inferência CPU, quatro threads intra/uma inter, como o experimento anterior;
não houve varredura nova de desempenho.

Sem webcam, gravação, treinamento, HTTP de eventos, banco aberto, credenciais
alteradas, commit, push ou deploy. Só houve leitura de imagens autorizadas
existentes e download público do único localizador escolhido.
REFERENCE_4_SPIN/RTMO_ADAPTIVE_V3, candidatos rejeitados, pesos/classificador,
polígonos/configurações e resultados anteriores preservados.
As quatro perdas históricas e controles inconclusivos continuam válidos.
Um frame reconhecido nesta rodada não converte um episódio antigo em acerto.

Neste documento, “localizador atual” é o **YOLOX-tiny do par leve experimental**,
não substituição do RTMO do worker normal. Todos os materiais são desenvolvimento.
A divisão construção/verificação permanece por vídeo, sem independência
garantida de sessão ou participante.

## 2. Referência mínima encerrada e retificação de caixas

Partiu de `visual-reference.source-review-v2.json` e `review-v2.html`.
Presença, quantidade, caixa visível, postura e coordenadas articulares foram
tratadas como informações distintas.

A única conferência solicitada ao fundador mostrou original/marcação lado a
lado e nove T, sem exigir centros ocultos de quadril/ombro/joelho. Resposta:
“estao bons mas o f5, f9 e f14 so marca um tornozelo”.
Foi explicado que o segundo tornozelo desses frames continua incerto.

**Referência utilizável: nove regiões de tornozelo, em seis frames.**
F01: 2; F05: 1; F07: 2; F09: 1; F12: 2; F14: 1.
Os outros grupos ficam sem coordenada; lateralidade anatômica permanece
UNRESOLVED. Não preencher o lado sobreposto nem medir corpo inteiro com
esses nove pontos. As coordenadas confirmadas não foram deslocadas para
acompanhar qualquer previsão.

Artefatos: `partial-reference.frozen.json`,
`human-partial-confirmation.json`, `partial-reference.closed.json`,
`review-ankles.html` e `reference-closed.html`.
Nos demais oito frames, há presença/postura/caixa, sem referência articular
confiável. F01 conserva a incerteza sobre figura/reflexo ao fundo.
F04 tem zero pessoas e nenhuma articulação aplicável.

### Caixas manuais antigas também precisavam de correção

A inspeção dos originais demonstrou que F07/F08 excluíam braços e incluíam
chão abaixo do corpo. Em vez de alterar o limiar para aceitar o candidato,
foram retificadas as extensões **visíveis** por imagem, com aproximação manual
de cerca de 8 pixels, sem inferir corpo atrás de móvel. Treze caixas foram
atualizadas; F04 continua sem caixa. Os nove tornozelos ficaram inalterados.

A retificação ocorreu **depois das previsões do candidato**; isso está declarado
em `body-reference-rectification.json`. Não se copiou a saída do modelo como
verdade. Amostra, pesos, pixels, limiares e critérios não mudaram, e as avaliações
com as caixas antigas foram conservadas. Não alegar avaliação independente.
Não houve novas inferências para essa reavaliação de caixas.

Exemplo F07: caixa original fornecida [153,6; 259,2; 544; 329,4] px;
extensão visível retificada [162; 239; 523; 310] px.
O mesmo box automático do candidato tem IoU **0,481** contra a primeira e
**0,727** contra a segunda. Ambos os resultados foram preservados; limiar
de associação continua **0,5**. A referência antiga não era adequada para
atribuir essa diferença inteira ao localizador.

O PCK do rascunho articular anterior continua invalidado. As medidas novas
usam somente os nove tornozelos conferidos, não reabilitam aquele PCK.
Caixas manuais continuam instrumento offline; nenhuma dependência manual
nova foi colocada no produto.

## 3. Por que havia zero probes

O código antigo bloqueava antes de chamar o classificador:

1. Máscara numérica de **oito** essenciais, score bruto na projeção 0,5–1,
   coordenadas finitas e dentro do quadro.
2. Concordância com todos os pontos humanos anotados e presença dos quatro
   grupos articulares. Os próprios rótulos de concordância foram rejeitados.

Nas 224 linhas CORRECTED_RGB já salvas (A automático e B com caixa fornecida),
há 184 poses. A auditoria exata da condição antiga encontrou:

| Bloqueio antigo | Poses | Interpretação |
| --- | ---: | --- |
| B — máscara de oito passa, mas faltam grupos humanos | 10 | Referência incompleta impedia o probe |
| B — máscara de oito passa, mas o alinhamento do rascunho reprova | 10 | Dependência indevida de métrica invalidada |
| C — máscara de oito falha e faltam grupos humanos | 52 | Duas condições antigas |
| A — máscara de oito falha, com quatro grupos no rascunho | 112 | Reprovação numérica antiga; não prova incapacidade anatômica |

Logo, **20 poses passavam a antiga máscara e eram bloqueadas só pela referência**.
Não era correto deduzir “modelo/classificador incompatível” dos zero probes.

### Outro bloqueio: oito pontos não é o requisito para todo diagnóstico V3

A leitura de `posture_multiclass.py` mostrou que o V3 já aceita pelo menos
quatro pontos válidos, incluindo três de ombros/quadris, para formar o
descritor parcial. Corpo completo continua obrigatório para evidência positiva
de pessoa no chão. A implementação do classificador/pesos/limiares **não mudou**.

O auditor passa a usar essa regra existente, sem depender de coordenadas
humanas para chamar o shadow. Usa o classificador real para decidir se o
descritor, scores, margem, geometria e contexto permitem uma saída.
LYING parcial conserva FLOOR_BODY_EVIDENCE_INCOMPLETE e nunca autoriza evento.

Resultado final do cache: **82 probes pontuados**, 44 em A e 38 em B.
Desses, 20 tinham a máscara completa antiga e 62 usam suporte parcial já
existente. Outras 102 poses não passam nem o requisito numérico parcial V3.
As 82 chamadas não são 82 acertos, nem novas observações independentes.

Os scores continuam **RTMPOSE_SIMCC_SCORE**, sem normalização/clipping ou
renomeação como visibilidade. A projeção numérica no contrato RTMO é
**shadow não validado**. Passar 0,5 não certifica anatomia nem equivalência
de probabilidade/confiança entre estimadores.

A frase de oito pontos no protocolo inicial está preservada. A descoberta
posterior e a correção são documentadas como auditoria do contrato existente,
não escolha de valor após ver o resultado de um arquivo.

| Frame | Poses salvas A+B | Passam 8 antigos | Permitem descritor V3 / probes | Classes shadow nas quatro orientações, A+B |
| --- | ---: | ---: | ---: | --- |
| F01 | 12 | 8 | 8 | LYING 4; SEATED 4 |
| F02 | 16 | 0 | 0 | Insuficiente |
| F03 | 10 | 0 | 2 | KNEELING_OR_CROUCHING 2 |
| F04 | 0 | 0 | 0 | Vazio; nenhum probe esperado |
| F05 | 16 | 8 | 14 | SEATED 6; UNKNOWN 2; KNEELING_OR_CROUCHING 2; LYING 4 |
| F06 | 18 | 0 | 10 | UNKNOWN 2; LYING 8 |
| F07 | 8 | 0 | 0 | Sem localização em A; B histórico numericamente insuficiente |
| F08 | 10 | 2 | 2 | LYING 2 |
| F09 | 18 | 0 | 10 | LYING 10 |
| F10 | 20 | 0 | 10 | LYING 10 |
| F11 | 18 | 0 | 8 | LYING 8 |
| F12 | 14 | 0 | 8 | SEATED 8 |
| F13 | 8 | 0 | 0 | Sem localização em A; B histórico numericamente insuficiente |
| F14 | 16 | 2 | 10 | LYING 10 |

São duas repetições dos mesmos pixels. O reconhecimento corporal correto de
uma classe não comprova decisão temporal. F05 é abaixar, classe sem equivalente
direto no vocabulário de quatro classes do artefato. LYING ali e em F06
(mãos/joelhos) são saídas posturais indevidas do shadow, preservadas, não
alertas reais produzidos nesta rodada. Em várias dessas saídas a própria
guarda de corpo incompleto impede evidência positiva.

## 4. Reutilização e medidas anatômicas parciais

`reassess-pose-cache.py` verifica hashes de pesos e referência original,
identidade dos pixels, dimensões, PTS, vídeo e orientação, antes de reutilizar
as previsões CORRECTED_RGB. Não instancia estimador, câmera ou outbox.
224 linhas reavaliadas; **zero inferências de modelo por revisão de rótulo**.
Passagens intermediárias e resultados antigos permanecem arquivados.

A classificação é separada da medição anatômica. Os grupos sem referência
não penalizam pontos inventados nem bloqueiam o diagnóstico de postura.
Cada ponto observado é associado bijetivamente dentro do grupo; um tornozelo
previsto não pode ser usado duas vezes. Fórmula preservada: tolerância
máxima entre 8 pixels e 5% da diagonal da caixa visível. Distâncias em pixels
e aceitação numérica ficam separadas; ponto de score baixo pode ter posição
próxima sem ser aceito como evidência.

| Caminho | Frames com pontos efetivamente medidos | Comparações repetidas de tornozelos | Dentro da tolerância | Mediana da distância |
| --- | --- | ---: | ---: | ---: |
| A YOLOX-tiny | F01/F05/F09/F12/F14 | 32 | 18 | 14,877 px |
| B salvo, caixa histórica fornecida | F01/F05/F07/F09/F12/F14 | 72 | 50 | 12,672 px |
| A YOLOX-m | F01/F05/F07/F09/F12/F14 | 64 | 30 | 18,286 px |

Em A, entram somente caixas associadas ao corpo de referência; todas as saídas
continuam registradas. Os denominadores diferem: não usar essa tabela para
anunciar ganho/perda global de precisão. São **nove pontos únicos**, não
168 articulações independentes nem precisão do corpo inteiro.

No subconjunto pareado em que ambos têm uma única caixa associada, são
28 comparações repetidas: **14 dentro da tolerância em cada método**;
medianas 20,545 px (tiny) e 18,563 px (m). Não demonstra melhora anatômica
consistente. Detalhes: `paired-ankle-analysis.json`.

Os recortes B salvos continuam exatamente os usados na rodada anterior:
**não são recortes recalculados pelas caixas retificadas**. Isso é explícito
no JSON. Não se reaproveitou como se a transformação de entrada tivesse mudado
sem custo.

## 5. Uma única alternativa de localização

Escolhida **YOLOX-m HumanArt, 640×640**, mantendo RTMPose-s RGB 192×256.
A documentação oficial oferece essa variante na mesma família e o código
RTMLib a usa na configuração balanced; permite trocar só o localizador,
com suporte ONNX/CPU e decodificador já conhecido.
[Modelo e configuração oficial](https://github.com/open-mmlab/mmpose/tree/main/projects/rtmpose) ·
[Integração RTMLib](https://github.com/Tau-J/rtmlib/blob/main/rtmlib/tools/solution/body.py).

Origem: repositório Tau-J/RTMPose, revisão fixada
`cd4d7095f5cfc9cfc4f46289bee91ea4a1e1d9fd`.
Metadados consultados declaram Apache-2.0; código upstream também Apache-2.0.
O ZIP não contém licença específica por checkpoint. A declaração encontrada,
URLs e hashes foram preservados; isso não certifica direitos sobre todos os
dados de treinamento nem liberação comercial.
[Origem dos artefatos](https://huggingface.co/Tau-J/RTMPose) ·
[Licença upstream](https://github.com/open-mmlab/mmpose/blob/main/LICENSE).

| Artefato | SHA-256 |
| --- | --- |
| ZIP YOLOX-m | a000224fd8ba283202bc62d4a5fcdfe353adb9f468777dbac1ea2ada2093adde |
| ONNX YOLOX-m | 3dea6513388889f0fff4b77bf7a26013600321b9eb9ceb0e9a400a82572f5f23 |
| RTMPose-s preservado | 9aeb635b83f86aea45cf45d85798f7eba1a162de8e0d721c44e54fe5eebaf47d |

ONNX novo: 101400344 bytes, privado. Nenhum peso no Git.
YOLOX recebe BGR, conforme seu pipeline; RTMPose recebe RGB.
Score de filtro continua 0,3; NMS exportado continua IoU 0,65.
Não houve novo NMS, fusão, redução de limiar, escolha por postura esperada,
treino ou outra alternativa executada.

Amostra congelada antes das inferências: mesmos 14 frames, quatro orientações
e duas repetições com ordem invertida. Não escolher a orientação vencedora
como se fosse uma política online. Limite de 20 caixas aborta erro explícito,
sem truncar caixas para forçar uma pessoa.

**112 chamadas de detector e 94 de pose**, mais duas chamadas sintéticas de
aquecimento. Previsões/tempos da base foram reutilizados. Apenas o candidato
foi inferido novamente para esta comparação; nenhum vídeo completo.

## 6. Resultados por frame

[Tabela completa por frame](REFERENCIA_PARCIAL_LOCALIZACAO_2026_10_27.csv).
Abaixo, orientação original, primeira repetição. As repetições reproduziram
as mesmas caixas/poses; não são novos exemplos. N é a quantidade de essenciais
que passam a projeção numérica fixa. “Probe” não significa evidência aprovada.
Quantidade primária é 1 nos frames com pessoa, exceto F01 com fundo incerto;
F04 tem zero.

| Frame / presença e postura | Referência articular disponível | Tiny: caixas / N / shadow | M: caixas / N / shadow | Componente que bloqueia ou conclusão limitada |
| --- | --- | --- | --- | --- |
| F01, deitada | 2 tornozelos; demais incertos | 1 / 8 / LYING | 1 / 8 / UNKNOWN | Regressão de diagnóstico; classe incerta apesar da máscara completa |
| F02, sentada | Sem coordenadas | 2 / 3,2 / sem probe | 2 / 3,0 / sem probe | Falsa caixa no sofá persiste; pose insuficiente |
| F03, ajoelhada | Sem coordenadas | 1 / 6 / KNEELING | 1 / 5 / KNEELING | Diagnóstico parcial negativo plausível; corpo completo não medido |
| F04, vazio | Não aplicável | 0 / — / — | 0 / — / — | Original vazio; nova falsa caixa em M a 270° |
| F05, abaixando | 1 tornozelo | 1 / 8 / SEATED | 1 / 8 / UNKNOWN | Vocabulário/postura incertos; não comprova observação negativa robusta |
| F06, mãos/joelhos | Sem coordenadas | 1 / 5 / UNKNOWN | 1 / 7 / LYING incompleto | Classe corporal indevida, sem evidência completa de chão |
| F07, deitada | 2 tornozelos | 0 / — / — | 1 / 3 / sem probe | Localização recuperada; recorte/qualidade numérica ainda insuficientes |
| F08, deitada | Sem coordenadas | 0 / — / — | 2 / 2,8 / UNKNOWN | Nova ambiguidade de caixas sobre uma pessoa |
| F09, deitada | 1 tornozelo | 1 / 1 / sem probe | 1 / 0 / sem probe | Pose/score não qualificam descritor nessa orientação |
| F10, deitada | Sem coordenadas | 2 / 1,0 / sem probe | 1 / 0 / sem probe | Duplicidade reduzida; pose continua insuficiente |
| F11, deitada | Sem coordenadas | 2 / 0,1 / sem probe | 1 / 0 / sem probe | Duplicidade reduzida; pose continua insuficiente |
| F12, sentada | 2 tornozelos | 1 / 6 / SEATED | 1 / 6 / SEATED | Diagnóstico parcial acompanha postura; não mede corpo inteiro |
| F13, ajoelhada | Sem coordenadas | 0 / — / — | 1 / 1 / sem probe | Localização recuperada; qualidade da pose/score ainda bloqueia |
| F14, deitada | 1 tornozelo | 1 / 8 / LYING | 1 / 7 / LYING incompleto | Regressão de evidência completa no shadow |

F07: IoU automático original **0,727**; F13: **0,926** contra caixas visíveis
retificadas. YOLOX-tiny continua sem caixa nos dois em todas as quatro
orientações. Portanto, há **melhora localizada de localização automática**.
No original, a associação do corpo primário vai de 10/13 para 13/13 frames
com pessoa; isso não é recall de incidentes ou precisão geral.

Falso sofá em F02 é distinto da duplicidade sobre a pessoa em F10/F11.
No M essas duplicidades foram reduzidas sem fusão adicional, mas surgiram
duas caixas sobre a mesma cena/pessoa em F08. A caixa maior inclui excesso
de contexto e só uma corresponde suficientemente à caixa visível.
F04 vazio ganha uma caixa no sofá a 270°, nas duas repetições.
Nenhuma caixa foi eliminada pelo rótulo esperado.

Prancha privada `comparison-review.html`: originais, tiny e m lado a lado,
todas as caixas amarelas e pontos nativos; verde marca apenas a projeção
numérica ≥0,5, cinza mostra pontos de score menor. Não é esqueleto inventado
nem evidência de visibilidade. Imagens críticas foram inspecionadas localmente.

### Dois recortes manuais novos para separar as causas restantes

Como as caixas de referência mudaram, o B histórico não respondia se um
recorte corrigido resolveria a pose original. Foram feitos **somente dois**
probes novos de pose: F07 e F13 em 0°, com caixa fornecida corrigida.
Transformação de recorte diferente exige inferência nova; o restante ficou
em cache. Nenhum novo modelo/localizador ou margem foi experimentado.

| Frame | Caixa automática M | Caixa fornecida corrigida | Conclusão permitida |
| --- | --- | --- | --- |
| F07 | 3 essenciais; sem descritor V3 | 8 essenciais; shadow LYING | Precisão/extensão do recorte afeta a pose; presença de box e IoU 0,727 não bastam |
| F13 | 1 essencial; sem probe | 1 essencial; sem probe | Corrigir localização não resolve a qualidade da pose/score nesse frame |

Arquivo `current-reference-box-two-probes.json`. B não é localização automática.
Em F07, a anatomia humana anotada continua sendo só dois tornozelos:
oito scores e uma classe correta não certificam posição correta de todo o corpo.

Isso não autoriza atribuir automaticamente erros de classe ao estimador nem
ao classificador. A relação SimCC→artefato RTMO continua não qualificada.
F07 oferece hipótese concreta de recorte; F13 conserva bloqueio na pose/score,
antes do classificador. Não iniciar série automática de margens/modelos.

## 7. Custo e decisão de avanço

Custo a partir do frame decodificado, com rotação, detector, preprocessamento,
inferências de pose em todas as caixas, pós-processamento e restauração.
Aquecimento e inicialização separados. Não inclui captura, desenho, HTTP,
persistência ou anotação de referência. Shadow corrigido foi reexecutado
sobre saídas salvas e seu custo é indicado separadamente, não como medição
LIVE contínua.

| Orientação | M: percepção média / P95 / máximo, ms | Shadow corrigido médio separado, ms | Tiny histórico: média, ms |
| --- | --- | --- | --- |
| 0° | 301,513 / 356,575 / 414,592 | 0,164 | 48,739 |
| 90° | 289,527 / 310,267 / 344,322 | 0,053 | 47,830 |
| 180° | 288,499 / 312,476 / 325,285 | 0,119 | 50,727 |
| 270° | 298,132 / 346,092 / 397,410 | 0,141 | 51,001 |

28 medições por orientação. Carregamento das duas sessões: 422,570 ms;
aquecimento: 350,603 ms. O custo maior é observado, mas a base histórica não
é benchmark contemporâneo pareado de velocidade: não calcular ganho percentual
ou FPS LIVE. O limite de duas chamadas da antiga estratégia RTMO não foi
usado como regra universal.

**Decisão: não promover o YOLOX-m nem avançar a vídeos/transmissão.**
Recuperação dos dois boxes não preservou toda a amostra:
novo falso box vazio, nova ambiguidade, regressões F01/F14 e qualidade
insuficiente nos alvos. Desempenho temporal, cadência, idade de frames e
latência de eventos não foram medidos para esse candidato; não registrar zero.
Não existe nova política online de orientação, evento ou prova física.

## 8. Código, verificações e reprodução

Mudanças somente no diagnóstico offline:

- `pose_audit.py`: máscara numérica, disponibilidade de descritor e avaliação
  de caixas separados da referência.
- `audit-pose-reference.py`: shadow sem gate humano completo; usa contrato
  parcial existente do V3; eventos sempre desautorizados.
- `reassess-pose-cache.py`: reutilização com validação de identidade e causas
  do gate antigo, mantendo identificação do recorte B histórico.
- `compare-localizer.py`: único localizador alternativo fixado por SHA, pose
  RGB imutável, saídas novas e caixas múltiplas preservadas.
- `test_pose_diagnostics.py`: dez casos novos pertinentes.

| Comando/ação realmente executado | Resultado |
| --- | --- |
| git status/log e snapshot | main inicialmente limpa, HEAD 6146dfe |
| Consulta a documentação/metadata oficial | YOLOX-m selecionado; Apache-2.0 declarado; hashes registrados |
| uv sync no ambiente novo, --frozen | 30 pacotes, um cv2, manifestos anteriores preservados |
| Reavaliações de cache | 224 linhas finais; 82 probes; zero chamadas a estimadores por revisão de referência |
| Comparação do candidato congelado | 112 detector + 94 pose + duas chamadas de aquecimento; 112 linhas |
| Dois B com caixa corrigida | Duas chamadas adicionais de pose, sem detector; F07 8 pontos/LYING, F13 1 ponto |
| Testes dirigidos pose_diagnostics + pose_audit | 22 passaram |
| Pytest completo final | **458 passaram, 1 GUI explícita ignorada**, 16,74 s |
| pnpm lint:edge e ruff dos três scripts | Passaram |
| git diff --check / preservação final | Verificados no encerramento, fontes e pesos preservados |

Confer?ncia final de preserva??o: **67 arquivos cr?ticos e 52 relat?rios anteriores intactos**; modelos/classificador e manifestos conferidos por SHA-256. Identidade das fontes execut?veis (221 arquivos, excluindo documenta??o e dados privados):
`40aeafd221498d667aca5900f38b7bba2c9009d79480a282f41392c9d6faf8b1`.
Registros privados: `preservation-final.json` e `final-verification.json`.

Falhas operacionais corrigidas: ordenação/formatação de imports na criação
dos scripts; sumarizador tentou acessar IoUs articulares de frame vazio sem
referência de pontos. A correção trata ausência de referência como não
mensurável, preservando o falso box do vazio. Não mudou inferência ou gate.
Probes intermediários com oito pontos e avaliação com caixas antigas ficam
preservados; não foram substituídos silenciosamente pela última versão.

Sem webcam, testes físicos, backend/contratos alterados ou treino.
Não se repetiram API/TypeScript/build ou a matriz completa: não houve mudanças
nesses componentes nem precondição perceptual para ampliar o experimento.

Na raiz, verificações:

```powershell
. ./scripts/activate.ps1
uv run --project services/edge --frozen pytest services/edge/tests -q
pnpm.cmd lint:edge
uv run --project services/edge --frozen ruff check scripts/validation/audit-pose-reference.py scripts/validation/reassess-pose-cache.py scripts/validation/compare-localizer.py
```

Reavaliar o cache com os arquivos privados já presentes, sem inferência:

```powershell
. ./scripts/activate.ps1
$info = Get-Content .local/detector-evolution/localization-current.json | ConvertFrom-Json
$env:PYTHONPATH = (Resolve-Path services/edge/src).Path
$output = "$($info.root)/cache-repeat-$([guid]::NewGuid())"
uv run --project $info.environment --frozen python scripts/validation/reassess-pose-cache.py --reference "$($info.root)/partial-reference.closed.json" --cache "$($info.previous)/pose-audit-final/audit.json" --cache-reference "$($info.previous)/visual-reference.frozen.json" --output $output
```

`compare-localizer.py --help` lista a reprodução do ensaio nativo.
Entradas reais usadas: `partial-reference.frozen.json`, `protocol.frozen.json`,
cache anterior `pose-audit-final/audit.json`, vendor RTMLib 0.0.16 da rodada
de decisão, `candidate-artifact.json` e a pose preservada.
A saída exige diretório novo. Reproduzir o ensaio inicial conserva a avaliação
antiga; a referência fechada só atualiza a análise das saídas salvas.
Não rodar modelos novamente para uma mudança de rótulo.

Pranchas privadas podem ser abertas por:

```powershell
Start-Process "$($info.root)/reference-closed.html"
Start-Process "$($info.root)/comparison-review.html"
```

Imagens, pesos, vídeo, configurações privadas e cache não entram no Git.
A reprodução depende desses materiais locais autorizados.

## 9. Respostas finais e próximo trabalho específico

1. **Referência parcial utilizável?** Sim, para presença/postura/caixa visível
   aproximada e nove regiões de tornozelo em seis frames. Não para articulações
   ocultas, lateralidade, corpo inteiro, contato físico com piso ou eficácia geral.
2. **Por que zero probes?** Duas restrições do auditor: gate humano completo/
   alinhamento invalidado e exigência de oito para qualquer classe. O V3 já
   permite descritor parcial. Corrigido o auditor; 82 probes reais em cache,
   sem mexer no detector ou validar a equivalência de scores.
3. **F07/F13 localizados automaticamente?** Sim, com YOLOX-m original,
   IoUs 0,727/0,926 na referência visível retificada; falhas de pose continuam.
4. **Falsos positivos/regressões?** Sofá persistente; novo falso box vazio270;
   duplicidade/ambiguidade F08; F01 UNKNOWN e F14 corpo incompleto onde o tiny
   produzia LYING completa no shadow. Tudo preservado, sem fusão por conveniência.
5. **O que melhorou e falta?** Auditor e mensuração corrigidos, localização
   recuperada nesses dois frames. Falta obter pose/contrato de score que
   sustentem reconhecimento automático preservando os controles.
   F07 aponta recorte automático; F13 continua pose/score mesmo com caixa
   fornecida. Não descartar toda a pose ou treinar classificador por esse total.

Próxima hipótese deve partir dessas duas causas discriminadas, com uma
proposta específica autorizada. Nenhum novo modelo, busca de margem, vídeo
completo ou protocolo físico foi iniciado automaticamente. Referência do
worker preservada e MVP continua não aprovado.
