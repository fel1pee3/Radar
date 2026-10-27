# Diagnóstico contrafactual de recuperação — 26/10/2026

## Objetivo e preservação

Rodada solicitada após `bb768abfe0c25e8f9d8a8127c455591718831be6`, árvore limpa.
STATUS real em `docs/STATUS.md`; não existe STATUS na raiz. Leituras: AGENTS,
README, STATUS, relatórios de reaquisição V2, preferência V1 e orientação V3,
estimadores, classificador, FILE/LIVE, executor a 1×, avaliação, testes e contratos.

Referência `REFERENCE_4_SPIN + RTMO_ADAPTIVE_V3`, V1 e V2 preservados. Nenhuma
webcam, câmera IP ou gravação foi aberta; não houve treino, alteração de pesos,
classificador, polígonos, credenciais ou banco da demonstração.

Raiz privada desta rodada:
`.local/detector-evolution/stabilization-ce12cde8-31ee-4665-9727-c5f1da1111d5/`.
Ponteiro: `.local/detector-evolution/stabilization-current.json`.
Snapshot inicial SHA-256
`8ec9eb6f91f387da092801f56ba0910969bcdc812cfe5276338e8f5963821a50`;
fonte inicial, 208 arquivos,
`8625d5671810ede26fc7a80b466138b2566d9432dec68eb3b57dc0565ab7f4fe`.
Protocolos/resultados anteriores continuam separados, com cópias dos agregados
e indicação dos arquivos originais. Esta investigação é desenvolvimento,
não avaliação independente.

## Método reproduzível

Sete timestamps exatos; nenhuma busca pelo frame mais próximo. Cada frame foi
decodificado pelas regras existentes de orientação/largura, identificado por
índice e SHA-256 e testado em três repetições. ORIGINAL primeiro para obter
a proposta atual; cinco alternativas em ordem alternada. O recorte usa uma
cópia da caixa do ORIGINAL do mesmo frame, nunca a proposta de outra tentativa.
Na reprodução final versionada são 126 inferências diagnósticas, sem excluir
alternativas desfavoráveis; as medições auxiliares preliminares ficam separadas.

O executor versionado `scripts/validation/audit-rtmo-recovery.py` registra
score de pessoa, oito essenciais, pontos/qualidades nativos, coordenadas
restauradas, elegibilidade estática, classe, motivos e custo por fase. Resultados
privados: `public-auditor-proof/audit.json`. A aceitação temporal não é avaliada
nesse comando; cada alternativa recebe um QualityGate novo para não interpretar
timestamps esparsos/repetidos como FPS de uma sessão contínua. Uma primeira
medição auxiliar com gate compartilhado gerou LOW_FPS artificial e foi
preservada como preliminar inválida; o executor final corrige essa medição,
sem alterar o gate do detector.

[CSV das 126 medições](DIAGNOSTICO_FRAMES_2026_10_26.csv): score de pessoa,
contagem de essenciais, menor score articular aceito, elegibilidade estática,
classe e custos de preparação/inferência/decodificação/restauração. Sem
coordenadas corporais, imagens ou caminhos privados no CSV público.

O limite de duas chamadas vale para a política experimental por análise.
Enumerar alternativas nesse diagnóstico não é uma execução dessa política;
nenhum resultado contrafactual fica disponível para escolher sua segunda chamada.

## Resultado por frame

Os sete pertencem a **controles negativos já anotados**, não a sete cenas
positivas de pessoa deitada. Aqui se mede observabilidade, não sete acertos de
detecção de acidente. Uma pose aceita tampouco garante uma classificação correta.

| Controle / ms | Score ORIGINAL | Essenciais da proposta não aceita | Recuperações com oito essenciais | Classe após recuperação |
| --- | ---: | ---: | --- | --- |
| intake16-10 / 1200 | 0,648379 | 8 | CENTER_80 | SEATED |
| cauca-11 / 5000 | 0,624467 | 7 | PERSON_PROPOSAL_CROP | KNEELING_OR_CROUCHING |
| cauca-12 / 2400 | 0,666048 | 8 | CENTER_80 | KNEELING_OR_CROUCHING |
| cauca-12 / 2800 | 0,550776 | 8 | PERSON_PROPOSAL_CROP | STANDING_OR_WALKING |
| cauca-12 / 3600 | 0,617210 | 8 | PERSON_PROPOSAL_CROP | STANDING_OR_WALKING |
| cauca-12 / 12400 | 0,506786 | 8 | CENTER_80 | KNEELING_OR_CROUCHING |
| cauca-12 / 13000 | 0,666226 | 8 | CENTER_80 e ROTATE_270 | KNEELING_OR_CROUCHING / LYING |

Em todas as repetições, ORIGINAL ficou abaixo do limiar de pessoa >0,7;
propostas/articulações sub-limiar não foram aceitas como evidência. As
recuperações acima passaram pelos critérios existentes e pela classificação
estática, sem mudar confiança ou completar articulações.

No último frame, a alternativa também revelou discordância de classificação:
duas poses aceitas resultaram em classes diferentes numa cena anotada negativa.
Não é legítimo escolher a transformação conhecendo esse rótulo futuro, nem
transformar uma classe LYING isolada em alerta; o motor ainda exige persistência.
Em coordenadas restauradas da imagem original, a diferença entre seus pontos
essenciais teve mediana de 24,06 pixels e máximo de 79,16 pixels. Ângulo do
tronco: 76,82°/88,79°; razão corporal: 0,9322/0,6272. A restauração geométrica é
testada, mas não há ground truth articular para declarar qual pose tem melhor
alinhamento anatômico. `class-disagreement-13000.json` registra essa comparação.

O V2 não perdeu esses frames por um único defeito. Em alguns descartou um
recorte após falha anterior e foi à rotação; em outros gastou a segunda chamada
num recorte sem pose, enquanto a referência chegava a CENTER_80 ou ROTATE_270
na terceira/quarta passagem. A omissão de ORIGINAL já corrigida não explica
essas sete perdas. Há falha de seleção sob orçamento e sensibilidade do
estimador ao enquadramento/orientação, além da discordância de classe acima.

## Sinais disponíveis e alternativas

Essenciais da proposta, score, caixa e orientação são calculáveis antes da
segunda chamada. Usá-los para priorizar trabalho não torna uma proposta
rejeitada uma pessoa aceita. Nos sete frames, seis têm oito essenciais da
proposta, mas precisam de recuperações diferentes; contagem e orientação
sozinhas não determinam a alternativa útil. As políticas abaixo foram fixadas
antes de seus pilotos, sem nomes, rótulos ou timestamps absolutos.

**A — seleção atual:** proposta horizontal com oito essenciais prioriza 270°;
oito essenciais em outra orientação priorizam CENTER_80; proposta parcial,
recorte atual. A memória de processamento permanece limitada. Piloto completo
de sete arquivos: yogas e alvo caro passaram, mas cauca-08 ficou em 70,6897%
e cauca-12 em 60%. Rejeitada.

**B — localização/ROI mais barata:** HOG/SVM padrão do OpenCV, sem download ou
novo pacote, foi medido em 13 frames, três repetições. A documentação descreve
o detector padrão para janelas de 64×128 e a busca multiescala.
[Referência oficial do OpenCV](https://docs.opencv.org/4.13.0/d5/d33/structcv_1_1HOGDescriptor.html).
Foram 39 chamadas, média de 25,68 ms; nove dos 13 frames não produziram caixa,
incluindo os quatro exemplos positivos difíceis de yoga/alvo caro. Nenhuma
ausência foi interpretada como cômodo vazio. Custo inferior não demonstrou
localização suficiente; não foi integrado um novo modelo.

Também foram testados recortes da proposta atual com margem isotrópica de 25%
e 50% do lado maior, sem alterar a inferência RTMO. Recuperaram, respectivamente,
4/7 e 5/7 frames auditados. Nenhuma margem resolveu tudo. Na extensão aos mesmos
sete arquivos completos, a ROI de 50% preservou os três positivos, elevou
cauca-12 a 81,5385%, mas deixou cauca-08 em **79,3103%**, abaixo de 80%.
Não se arredondou esse valor para aprovar o controle.

**C — aquisição/recuperação separadas:** mantida a aquisição por ORIGINAL,
com busca finita por famílias de transformações e observações atuais. Piloto:
intake16-10 em 70,8333%, cauca-08 em 72,4138% e cauca-12 em 66,1538%.
Uma verificação adicional isolou a ROI de 50% mantendo a máquina de busca do
V2: 75%, 75,8621% e 78,4615%, respectivamente. O ganho da ROI não elimina o
problema de seleção/continuidade. Nenhuma dessas buscas foi integrada.

## Decisão para a comparação final

B apresentou a melhor sustentação dos pilotos, mas ainda falhou num controle
previamente aprovado. Será comparado como **experimento isolado FILE**,
`RTMO_ROI_CONTEXT_EXPERIMENT_V1`, sem novo valor no seletor normal do worker.
Não há evidência para substituir a referência ou anunciar uma política pronta.

O experimento mantém duas chamadas, orçamento adicional de 220 ms, ORIGINAL na
reaquisição, inspeções de 800 ms, lease de 1600 ms, lacuna de 500 ms e busca de
1600 ms/oito análises. Escolhas usam apenas o frame atual e preferência recente.
Sem alterar pesos, limiares, oito essenciais, contexto, persistência de 2000 ms,
cobertura de 80%, rearme, timestamps ou denominadores. A execução a 1× e a
regressão completa determinarão o benefício e as perdas restantes.

Resultados finais, matriz completa e recomendação:
[Estabilização perceptual](ESTABILIZACAO_PERCEPTUAL_2026_10_26.md).

## Reprodução sem câmera

Na raiz, com os vídeos/artefatos privados preservados:

```powershell
. ./scripts/activate.ps1
uv run --offline --project services/edge --frozen python scripts/validation/audit-rtmo-recovery.py --manifest .local/detector-evolution/stabilization-ce12cde8-31ee-4665-9727-c5f1da1111d5/seven-frame-manifest.json --output .local/audit-rtmo-nova-saida --repeats 3
```

A saída precisa ser nova e privada. O manifesto contém `cases`, cada qual com
`caseId`, `configPath` de FILE/rtmo-s e `timestampMs` inteiro exato. O comando não
cria evento, incidente ou execução LIVE; não abre banco/HTTP/webcam. Logs
corporais detalhados permanecem em `.local/`.
