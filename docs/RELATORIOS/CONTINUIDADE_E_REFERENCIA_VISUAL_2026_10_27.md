# Continuidade da decisão e referência visual — 27/10/2026

**Situação: proteção temporal implementada e verificada; diagnóstico visual parcial.
Nenhum estimador novo promovido e nenhuma aprovação do MVP.**

A primeira entrega protege a continuidade e a entrega de acontecimentos que
envelhecem durante uma interrupção. A segunda executou uma comparação pequena
A/B nas quatro orientações e corrigiu uma divergência comprovada de canais
de cor. O fundador rejeitou a precisão dos rótulos articulares, especialmente F07/F14.
O PCK do primeiro rascunho foi invalidado para julgar o modelo. Uma revisão
V2 baseada somente nas imagens foi preparada, deixando sem coordenada o que
permanece incerto. Não permite atribuir uma classe errada ao classificador
nem certificar capacidade anatômica geral.

## 1. Estado, ambiente e preservação

HEAD inicial: `33d0bd8cf7c4e82d97709cb351087ef065d98767`, main, árvore limpa.
Leitura de AGENTS, README, STATUS, contratos/motor e
[decisão anterior](DECISAO_PERCEPCAO_2026_10_26.md) antes das alterações.

Raiz privada nova:
`.local/detector-evolution/continuity-visual-044f3b50-6b4e-4e01-9d25-29b5016dd082/`.
Ponteiro: `.local/detector-evolution/continuity-visual-current.json`.
`initial-source.zip`, `initial-hashes.json` e `initial-git.json` preservam o início.

Windows 11 Pro build 26200, PowerShell 5.1.26100.9711, Ryzen 5 5625U,
12 processadores lógicos e 15,4 GiB visíveis. Node 24.22.1, pnpm 10.34.7,
Python 3.12.15 e uv 0.13.4. O ambiente isolado existente do par leve usa
ORT 1.23.2, NumPy 2.5.4 e opencv-contrib-python 5.0.0.93, com um único
provedor de cv2. Ambientes, lockfiles e pesos não foram trocados.

REFERENCE_4_SPIN/RTMO_ADAPTIVE_V3, V1/V2 rejeitados, ROI, classificador,
polígonos, configurações e resultados anteriores preservados. As quatro
perdas históricas floor03/floor05/floor07/controlled-lying e os controles
inconclusivos cauca-10/chair08-01 continuam registrados. Não reclassificar
dados de desenvolvimento como avaliação independente.

Não houve abertura de webcam, suspensão física do computador, gravação,
treinamento, deploy, commit ou push. Testes HTTP/PostgreSQL usaram o harness
isolado, com container/volume próprios; não se executaram migrações no banco
de demonstração nem se trocaram credenciais. Docker Desktop estava parado e
foi iniciado em segundo plano para esses testes. As migrações SQLite foram
exercitadas somente em filas novas ou temporárias de teste.

## 2. Política implementada para envelhecimento

O limite de **2000 ms** vale para idade de observação na decisão; a lacuna
máxima continua **500 ms**. Eles são diferentes da janela contratual de
**120000 ms** entre `detectedAt` e entrega LIVE. Nenhum desses limites foi
relaxado. REPLAY/SIMULATED continuam TEST; incoerência de relógio ou futuro
acima de 30000 ms continua CLOCK_UNCERTAIN.

| Fronteira | Comportamento implementado |
| --- | --- |
| Antes da decisão | Frame velho/idade negativa não soma evidência; lacuna no host quebra suspeita mesmo com PTS próximo |
| Antes do checkpoint | Rechecar depois de classificação/payload/snapshot; emissão apenas em memória é descartada se envelheceu, com auditoria NOT_STARTED |
| Durante o checkpoint | Evento, episódio, checkpoint e metadados de relógio entram na mesma transação |
| Depois do retorno do checkpoint | Idade >2000 ms ou checkpoint >500 ms invalida continuidade e marca COMMITTED; evento já salvo permanece |
| Erro SQLite com resultado possivelmente persistido | Interromper com STORAGE_ERROR; auditar UNKNOWN quando o armazenamento permitir, sem afirmar rollback |
| Retomada | Não restaurar janela de suspeita/rearme antiga; episódio ACTIVE permanece, evitando duplicação |
| Imediatamente antes de cada HTTP | Recalcular idade UTC/monotônica; enviar somente restrição conservadora DELAYED ou CLOCK_UNCERTAIN |
| Aviso pendente na API | Reavaliar atualidade no despacho; aviso que envelheceu não recebe nova urgência |
| Reenvio após ACK perdido | Mesmos bytes, eventId e horários; API devolve classe/recibo originais e não cria outro aviso |

SQLite passa aditivamente a versão **3**: tabelas `delivery_timing` e
`timing_audit`. O envelope continua protegido pelo trigger de imutabilidade.
Backup aceita versões 1/2/3 e conserva os novos metadados, sem incluir JPEG.
Não há atualização de esquema PostgreSQL nesta entrega.

O relógio de agendamento de retry é separado do relógio de atualidade.
Metadados incluem sessão de processo, instante monotônico, UTC e idade do
frame ao gravar. Divergência civil/monotônica >30 s ou monotônico regressivo
produz CLOCK_UNCERTAIN. Em processo novo, evento LIVE pendente com contexto
novo de relógio e ainda dentro de 120 s fica conservadoramente CLOCK_UNCERTAIN;
se o UTC já comprova atraso >120 s, DELAYED. Filas legadas sem esse contexto
usam a regra UTC existente: não é possível reconstruir seu monotônico passado.

A restrição é persistida separadamente para não desaparecer após reinício ou
retry. Não se alteram `occurredAt`, `detectedAt`, `emittedAt`, corpo JSON,
hash ou recibo anterior. O header opcional `X-Radar-Delivery-State` aceita
somente DELAYED/CLOCK_UNCERTAIN; CURRENT é rejeitado com 400. Mesmo sem header,
a API continua aplicando as regras de idade e relógio.

No painel, CURRENT passa a dizer **“Recebido na janela”**: é a classificação
histórica do recebimento, não uma afirmação de que a pessoa continua naquela
postura ao consultar a página depois. O aviso tem sua atualidade reavaliada
sem reescrever o recibo. Worker e API precisam desta versão para aplicar a
restrição de relógio do worker; não se reiniciou a demonstração pessoal.

A quebra de continuidade invalida a observação anterior para cobertura, mas
preserva seu timestamp no denominador. A lacuna não desaparece das métricas.

## 3. Provas de persistência e entrega

Doze testes novos em `test_decision_freshness.py`, com relógios injetados:
interrupção antes da decisão, entre payload/checkpoint, dentro da transação,
após commit e antes do envio; regressão do relógio civil; lacuna de host;
commit seguido de erro; retomada; ACK perdido; migração v2→v3; denominador
de cobertura; isolamento do relógio de retry e restrição durável.

Um teste no harness real usa observações sintéticas LIVE, **sem abrir câmera**:
a transação SQLite conclui; o relógio do worker avança 125 s antes do retorno;
a API real recebe o corpo intacto com DELAYED e aviso local sem urgência.
O UTC do evento ainda está a menos de 120 s do relógio real do servidor:
isso verifica a restrição adicional, não apenas o cálculo UTC já existente.
Outra prova conserva o recibo CURRENT após perder ACK e reenviar atrasado.

A proteção não é cancelamento transacional nem promessa de prazo máximo do
sistema operacional. Um processo pode ser interrompido entre quaisquer
instruções; rechecagens, registro conservador e verificação no servidor tratam
a retomada sem apagar uma decisão que pode ter sido confirmada.

## 4. Referência visual congelada

**14 frames de 11 vídeos**, seis de construção e oito de verificação, sem
sobreposição de arquivo entre os grupos. Mesma pessoa pode aparecer em vídeos
diferentes; a origem não permite garantir sessões distintas. A separação
comprovada é por arquivo, sem independência alegada por sessão/participante. Todos são
DEVELOPMENT. Frames PNG sem perdas, PTS, caminhos de origem e SHA-256 estão
em `visual-frames.json`; protocolo em `visual-protocol.frozen.json`.

`visual-reference.first-image-draft.json` conserva o primeiro rascunho.
A revisão por imagem anterior às previsões está congelada em
`visual-reference.frozen.json`, SHA-256
`c9fd7c8a0da4dce69e641d5eecab59719c485c3a1fa13c0c2ea2fd8ece98890b`.
Não se usaram previsões como referência, não se preencheram juntas ocultas,
nem se corrigiram coordenadas depois para aprovar uma saída.

| Frame | Grupo | Arquivo / PTS ms | Postura observável | Pessoas visíveis |
| --- | --- | --- | --- | --- |
| F01 | Construção | yoga2-01 / 2503 | Deitada | 1; possível figura/reflexo adicional incerto |
| F02 | Construção | intake16-10 / 2480 | Sentada; sofá confundidor | 1 |
| F03 | Construção | cauca-11 / 5200 | Ajoelhada/agachada | 1 |
| F04 | Construção | intake16-15 / 3880 | Cômodo vazio | 0 |
| F05 | Construção | intake16-08 / 3120 | Abaixa o tronco | 1 |
| F06 | Construção | floor03 / 2944 | Apoio de mãos e joelhos | 1 |
| F07–08 | Verificação | yoga2-02 / 1600 e 8000 | Deitada | 1 |
| F09–11 | Verificação | intake16-03 / 1480, 7360, 11760 | Deitada, pernas flexionadas/sobrepostas | 1 |
| F12 | Verificação | intake16-07 / 2752 | Sentada, uma perna elevada | 1 |
| F13 | Verificação | cauca-12 / 10450 | Ajoelhada/agachada | 1 |
| F14 | Verificação | floor07 / 2576 | Deitada de lado | 1 |

F06 é o frame próximo do meio do arquivo definido pelo protocolo. **Não é
uma pessoa já deitada nesse instante.** Isso não altera a anotação do episódio
completo nem apaga a perda histórica.

As caixas são extensões visíveis do corpo, aproximadas, apenas para diagnóstico
offline. Não são novas marcações manuais exigidas pelo produto. Grupos de
ombros/quadris/joelhos/tornozelos mantêm pontos observáveis, quantidade não
observável e incerteza; lateralidade anatômica não distinguível fica UNRESOLVED.
Nenhuma junta foi marcada como fora do quadro sem evidência; ocultação não é
a mesma coisa que corte. No vazio, não existem articulações de referência.

**Referência articular rejeitada na conferência humana.** Primeiro o fundador
achou F01 plausível; ao conferir os seis, apontou deslocamentos em todos,
sobretudo F07/F14, dois T na mesma perna e J/O errados em F09, e o J inferior
de F12. Registro literal: `human-visual-review.json`. Isso invalida o PCK
para avaliar o modelo; não é uma falha nova da previsão, que não estava
desenhada na prancha. O CSV conserva os números brutos com
`anatomyReferenceValidity=REJECTED_DRAFT...` ou UNVERIFIED_DRAFT. O CSV
anterior e o JSON nativo permanecem arquivados.

A prancha inicial `visual/review.html` e `review-six.jpg` continua intacta.
Após a crítica, foi feita inspeção ampliada dos **originais**, com grade
de pixels, sem usar os pontos previstos como resposta. Nova referência
`visual-reference.source-review-v2.json` e prancha
`visual/review-v2.html` colocam original e marcação lado a lado.
F07 passa a ter somente dois tornozelos observáveis para conferir; não se
inventam ombro/quadril/joelho na roupa escura. F09 mantém um joelho e um
tornozelo, evitando duplicar o membro sobreposto. F12 tem somente o joelho
distinguível da perna elevada. F14 mantém só um tornozelo; centros de ombro,
quadril e joelho ficam incertos. F01/F05 também deixam sem coordenada os
centros que não consigo determinar com segurança. Os detalhes estão por frame.

**A V2 ainda não é verdade anatômica validada** e não foi usada para repetir
inferências ou publicar nova precisão. Não prometer ponto “perfeito” quando
a imagem não permite observá-lo. Uma versão intermediária V2a foi arquivada.
A figura de fundo de F01 e a lateralidade de membros continuam incertas.
F09 representa também a vista comum de F10/F11. A revisão é pequena, sem
nova gravação; nenhuma falha foi apagada.

## 5. Auditoria do par leve e correção única

Mesmo par e mesmo ambiente da rodada anterior: YOLOX-tiny HumanArt + RTMPose-s
body7, RTMLib 0.0.16. Nenhum peso novo baixado ou seletor incorporado ao worker.

| Arquivo ONNX | SHA-256 preservado |
| --- | --- |
| detector.onnx | ceb11c07298f95c50d7c5abeb906d03340c85f23aa79e3e66966e7fb6c307250 |
| pose.onnx | 9aeb635b83f86aea45cf45d85798f7eba1a162de8e0d721c44e54fe5eebaf47d |

**Divergência comprovada: BGR era fornecido também à pose.** O pacote oficial
da pose declara `Normalize(to_rgb=true)`, com média/desvio em RGB, enquanto
o detector declara `to_rgb=false`. RTMLib 0.0.16 aplica affine/normalização
e transposição, mas não converte esses pixels BGR para RGB nesse caminho.
A correção `pose_input_from_bgr` converte somente a imagem da pose;
o detector mantém BGR. Metadados originais `pipeline.json`/`detail.json`,
arquivos ONNX e wheel continuam preservados no experimento anterior.

A implementação foi confrontada com o
[código oficial de RTMLib](https://github.com/Tau-J/rtmlib/blob/main/rtmlib/tools/pose_estimation/rtmpose.py)
e com os metadados exatos dos pacotes já baixados. A evidência determinante
é a combinação dos metadados fixados com a wheel local 0.0.16, não assumir
que a versão mais recente tenha o mesmo comportamento.

Detector: entrada [1,3,416,416]; pose: [batch,3,256,192], batch dinâmico;
saídas decodificadas COCO17 [1,17,2] e scores [1,17]. O batch dinâmico foi
aceito após inspeção, sem mudar resolução/modelo. Índices anatômicos mantidos,
sem trocar esquerda/direita ao girar. Coordenadas de centros de pixels e
arestas de caixas têm convenções diferentes, verificadas contra rotações
reais de pixels/máscaras OpenCV em 0/90/180/270°.

NMS foi inspecionado no ONNX real, com leitura protobuf sem instalar pacote
novo; estrutura confrontada com o
[proto oficial ONNX 1.19.1](https://github.com/onnx/onnx/blob/v1.19.1/onnx/onnx.proto).
O nó NonMaxSuppression_490 contém máximo 200, IoU 0,649999976 e score
0,0099999998. A branch end-to-end de RTMLib aplica depois filtro nativo
de score >0,3. Nenhum desses valores foi alterado. Parâmetros do construtor
para outra branch não reescrevem esse NMS exportado. Duas caixas com
IoU próximo de 0,64 podem sobreviver ao limite 0,65; isso não comprova erro
do decodificador. Evidência: `onnx-nms-audit.json`.

A única correção perceptual foi **honrar o contrato RGB da pose no experimento
isolado**. Não se mexeu em NMS, margens, classificação, polígonos ou política
de recuperação do Radar. A correção temporal é a outra entrega explicitamente
solicitada, não um novo candidato perceptual.

## 6. Comparação A/B e quatro orientações

A = localização automática seguida de pose em **todas** as caixas.
B = pose com **caixa corporal de referência fornecida**, sem detector.
B não mede localização automática e não é solução incorporada ao produto.

Quatro orientações canônicas, duas repetições, ordem invertida na segunda,
LEGACY_BGR e CORRECTED_RGB. Mesmos pixels, pesos e caixas automáticas para
o contraste de cor; detector executado uma vez por frame/orientação/repetição
e custo atribuído a ambas as alternativas de cor. Nenhuma escolha da melhor
orientação por conhecimento da resposta foi proposta para produção.
Vazio em B não dispara o fallback de imagem inteira do pacote.

**448 linhas de comparação**, não 448 ensaios independentes:
112 execuções efetivas de detector e 368 de pose, mais duas chamadas de
aquecimento sintético. Contagens de detector nas linhas somam 224 por
compartilhamento entre BGR/RGB; não são 224 chamadas efetivamente executadas.
Aquecimento 83,168 ms e inicialização 176,412 ms registrados separadamente.
Resultados nativos: `pose-audit-final/audit.json`.
O campo descritivo `referenceUsedForAssociationOnly` saiu true também em B;
`audit-metadata-erratum.json` explicita que em B a caixa dirige o recorte.
O CLI foi corrigido, preservando resultados e fonte executada em
`executed-auditor.py`; não se repetiu inferência por essa correção de metadado.
[Tabela das 448 linhas](CONTINUIDADE_VISUAL_AUDITORIA_2026_10_27.csv).

Caixas automáticas após restauração, CORRECTED_RGB, nas duas repetições
determinísticas (ordem 0/90/180/270):

| Frame | Caixas por orientação | Leitura sustentada |
| --- | --- | --- |
| F01 | 1 / 0 / 0 / 1 | Corpo principal encontrado em 0/270; fundo incerto |
| F02 | 2 / 0 / 1 / 1 | Em 0°, uma pessoa e falsa caixa no sofá; outras caixas não equivalem a reconhecimento correto |
| F03 | 1 / 0 / 0 / 0 | Localização depende de orientação |
| F04 | 0 / 0 / 0 / 0 | Sem caixa no frame vazio; não prova continuidade ou cobertura |
| F05 | 1 / 1 / 1 / 1 | Caixa corporal nas quatro; pose ainda requer rótulos articulares |
| F06 | 1 / 1 / 2 / 1 | Duas caixas em uma pessoa em 180° |
| F07 | 0 / 0 / 0 / 0 | Pessoa deitada não localizada em nenhuma das quatro |
| F08 | 0 / 0 / 0 / 1 | Caixa de 270° tem IoU 0,24 com a referência; não contar como corpo corretamente localizado |
| F09 | 1 / 1 / 2 / 1 | Duplicidade sobre uma pessoa em 180° |
| F10 | 2 / 1 / 2 / 1 | Duplicidade, não duas pessoas confirmadas |
| F11 | 2 / 1 / 1 / 1 | Duplicidade em 0° |
| F12 | 1 / 1 / 0 / 1 | Caixa parcial em 90/270, IoU ~0,43 |
| F13 | 0 / 0 / 0 / 0 | Pessoa agachada não localizada; ausência não é vazio |
| F14 | 1 / 1 / 0 / 2 | Corpo localizado em alguns ângulos; duplicidade em 270° |

**Falha de localização isolada:** F07 e F13 contêm pessoa visível e nenhuma
caixa nas quatro orientações. Isso independe de classificador e dos pontos
articulares aproximados. Não se demonstrou que trocar apenas o classificador
resolveria essas perdas.

**Anatomia A/B — medida não validada:** o auditor compara posições observáveis por grupo, associação
bijetiva dos dois lados incertos e raio de 5% da diagonal corporal, mínimo
8 pixels. Um score alto não conta como ponto correto. PCK e distâncias
permanecem no CSV/JSON como dados brutos de referência rejeitada; não usar
para comparar precisão anatômica de A/B ou BGR/RGB. Em F01, o subconjunto visível
chega a PCK 1,0 em alguns ângulos de A e B, mas quadris não estão anotáveis:
isso não qualifica uma pose completa para classificação. Nenhuma saída
satisfez os quatro grupos observáveis e a máscara atual de oito essenciais.
Logo, **zero execuções do classificador** nesta comparação.

B não demonstrou anatomia completa validada; a imprecisão do rascunho também
impede concluir “o modelo é incapaz”. A revisão compacta V2 registra precisamente os
pontos ainda observáveis/incertos em F07/F09/F12/F14 para separar essa dúvida. Postura
na tabela é inspeção humana da imagem, não acerto de classe do pipeline.
Não se atribuiu ao estimador uma classe errada sem primeiro qualificar pontos.

### Custo completo da percepção, CORRECTED_RGB

28 amostras por célula, 14 frames × duas repetições. Milissegundos.
A inclui rotação, localização/preprocessamento/inferência/pós-processamento,
pose por caixa, conversão de cor e restauração. B omite localização porque a
caixa é fornecida. Custo começa no frame decodificado; não inclui leitura PNG,
captura, auditoria dos rótulos, persistência, HTTP ou desenho. Classificador
não foi executado. Não converter esse custo em FPS LIVE garantido.

| Orientação | A média / P95 / máximo | B média / P95 / máximo |
| --- | --- | --- |
| 0° | 48,739 / 64,389 / 68,947 | 11,730 / 15,093 / 15,704 |
| 90° | 47,830 / 56,771 / 58,203 | 12,029 / 15,398 / 16,321 |
| 180° | 50,727 / 70,603 / 79,168 | 11,711 / 14,858 / 14,978 |
| 270° | 51,001 / 62,145 / 67,980 | 11,958 / 14,327 / 14,717 |

B inclui o vazio sem chamada de pose; não usar sua média como custo de um
detector automático. Médias A com BGR legado: 48,063 / 47,680 / 50,630 /
50,543 ms. A conversão RGB é correção de contrato, não aceleração ou ganho
de precisão demonstrado. Quatro passagens têm custo distinto de uma só;
o limite de duas chamadas do seletor RTMO não foi imposto ao diagnóstico.

## 7. Classificação e decisão de implementação

| Componente | Conclusão desta rodada |
| --- | --- |
| Localização | F07/F13 falham antes da pose; falso sofá e duplicidades separados por imagem |
| Pose/orientação | Divergência RGB corrigida; rótulos articulares rejeitados, V2 em revisão, capacidade anatômica inconclusiva |
| Classificador | Zero probes qualificados; incompatibilidade não demonstrada por esta amostra |
| Contexto | Piso/exclusões preservados; não são causa da ausência de caixas |
| Continuidade temporal | Risco reproduzido com relógio injetado e protegido até a entrega/aviso |

O shadow antigo SEATED em pessoa deitada permanece evidência histórica de
uma saída, mas **não prova incompatibilidade isolada do classificador**:
havia confusão de canais e ausência de referência articular qualificada.
Não houve treino nem limiar menor para fazer o exemplo passar. Scores SimCC
não foram renomeados como visibilidade ou tratados como probabilidade RTMO.
O caminho diagnóstico explicitamente identifica qualquer projeção no artefato
legado como não validada; nesta rodada ela nunca foi executada.

**Próximo trabalho único sustentado:** qualificar a pequena referência
articular V2 somente onde há pontos realmente observáveis e reavaliar A/B
sobre esses mesmos frames antes de decidir trocar
localizador, pose ou calibrar classificador. A correção de pré-processamento
já está implementada; não há fundamento para outra troca automática agora.

Se uma pose plenamente observável for validada e só a classe falhar, a
calibração futura deve usar observações nativas desse estimador com contratos
próprios de score e divisão por sessão/participante inteira, incluindo
deitada nas três orientações e negativas cadeira/ajoelhar/abaixar. Verificação
deve ficar fora do ajuste. Isso é procedimento condicional, não treino
executado ou autorização de busca ampla.

Pipeline automático ainda não demonstrou qualidade promissora: **não executar
matriz completa nem preparar teste físico** com base nesse diagnóstico.

## 8. Verificações executadas e falhas preservadas

| Comando/ação real | Resultado |
| --- | --- |
| Inventário, git status e snapshots privados | HEAD inicial limpo; fontes preservadas antes das edições |
| Testes iniciais frescor + outbox | 33 passaram; ajustes posteriores ampliaram os casos de frescor para 12 |
| Primeiro pytest completo | 445 passaram, 2 falharam, 1 ignorado: backup rejeitava SQLite v3 |
| Correção de backup + testes dirigidos | Backup aceita 1/2/3; casos pertinentes passaram |
| Pytest completo final | **448 passaram, 1 GUI explícita ignorada**, 23,91 s |
| pnpm test:api, tentativa inicial | Docker parado; não alcançou banco de teste |
| pnpm test:api, após ligar Docker | Primeira execução encontrou acoplamento indevido do relógio de retry à idade; corrigido, sem reduzir a asserção |
| pnpm test:api, execução final | **161 passaram**, incluindo commit interrompido, ACK perdido e aviso envelhecido |
| pnpm lint | Passou |
| pnpm lint:edge + ruff do auditor | Import fora de ordem corrigido; verificação final passou |
| pnpm typecheck e pnpm build | Passaram em contratos/API/web |
| Auditor A/B, primeiro início | Assert de batch fixo rejeitou shape dinâmico antes das previsões; corrigido conforme metadados |
| Auditor A/B final | 448 linhas, quatro ângulos, duas repetições; zero classifier probes |
| Regressão FILE nativa restrita | Quatro execuções EOF, saídas isoladas, sem HTTP nem webcam |
| git diff --check e preservação | Conferência final registrada junto aos hashes |

Regressão FILE da referência, com o código de persistência novo:
yoga2-01 gerou PERSON_ON_FLOOR aos 2002 ms, 24825 ms elegíveis/observados;
cadeira intake16-07 sem evento, 5424/5424 ms; vazio intake16-15 sem evento,
0/7600 ms elegíveis/observados, **não tratado como reconhecimento confirmado**;
floor07 sem evento, 1616/5024 ms, **perda histórica preservada**.
Não é a matriz completa nem avaliação independente.

## 9. Arquivos principais e reprodução

Worker: `freshness.py`, `event_runtime.py`, `delivery.py`, `outbox.py`,
`live.py`, `backup.py`. API: `event-support.ts`, `ingest.ts`,
`notifications.ts`. Painel: rótulo em `components/ui.tsx`.
Auditor: `pose_audit.py` e `scripts/validation/audit-pose-reference.py`.
Testes novos/estendidos e documentos de contratos, motor, decisões e STATUS.

Na raiz, verificações sem webcam:

```powershell
. ./scripts/activate.ps1
uv run --project services/edge --frozen pytest services/edge/tests -q
pnpm.cmd lint
pnpm.cmd lint:edge
pnpm.cmd typecheck
pnpm.cmd build
pnpm.cmd test:api
```

`test:api` requer Docker funcionando e usa seus recursos temporários exclusivos.
Para reproduzir a medição histórica, com os arquivos privados presentes,
escolha **saída nova**; não sobrescrever a final. O comando abaixo usa o
rascunho original preservado: seus PCK continuam inválidos para avaliar
qualidade. Não rodar a V2 como avaliação aprovada antes de conferir os rótulos:

```powershell
. ./scripts/activate.ps1
$env:PYTHONPATH = (Resolve-Path services/edge/src).Path
$round = (Get-Content .local/detector-evolution/continuity-visual-current.json | ConvertFrom-Json).root
$previous = (Get-Content .local/detector-evolution/decision-current.json | ConvertFrom-Json).root
$output = "$round/pose-audit-repeat-$([guid]::NewGuid())"
uv run --project .local/pose-env-965d2e5d --frozen python scripts/validation/audit-pose-reference.py --reference "$round/visual-reference.frozen.json" --output $output --vendor "$previous/rtmpose-experiment/vendor" --detector .local/pose-env-965d2e5d/artifacts/detector.onnx --pose .local/pose-env-965d2e5d/artifacts/pose.onnx
```

Nenhum download automático; SHA divergente falha. O comando não faz HTTP,
não abre webcam e não atualiza banco pessoal. A prancha V2 pode ser aberta
com `Start-Process "$round/visual/review-v2.html"`. Imagens/ambientes/pesos,
tokens e configurações privadas continuam fora do Git.

**Encerramento:** proteção temporal verificável entregue. Auditoria executada,
com falha de localização concreta e correção RGB comprovada, mas qualificação
anatômica/classificação ainda parcial. Preservar a referência e a revisão pequena
pendente; não declarar estabilização perceptual ou eficácia do MVP.
