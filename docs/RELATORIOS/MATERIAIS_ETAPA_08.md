# Novos materiais e investigação de percepção — etapa 08

Data: 22/10/2026. Complemento da [validação](VALIDACAO_MVP.md) e do
[relatório 08](ETAPA_08.md). **Etapa permanece PARCIAL.**

**Atualização de separação em 23/10:** os sete arquivos do grupo antes reservado
foram avaliados com Full congelado, conforme histórico abaixo. Depois,
intake08-02/05/08 e clipes da cadeira do mesmo grupo foram usados no diagnóstico
e na seleção do candidato RTMO/prévia. Para a versão atual, esse grupo passa a
CALIBRATION; não reaproveitar os resultados como avaliação independente.
O split original e as falhas foram preservados. Auditoria por SHA em
`.local/etapa08/perception-split-audit.json`: 23 materiais do split de origem,
zero vídeos independentes desse split para o candidato atual. Os dois clipes
adicionais da cadeira também continuam CALIBRATION. O fornecimento de materiais
não está pendente como se nenhum tivesse sido recebido; faltam novas sessões
separadas e anotações, além dos gates físicos/apresentação documentados no STATUS.

Reavaliação atual dos dois clipes de cadeira, sem nova conferência humana:
RTMO-s/política preservados, `evaluate` em saídas novas, 47/32 análises,
9216/6208 ms elegíveis, zero eventos e caudas de 98 ms por clipe. Ambos ok/ENDED,
sem HTTP, JPEG ou webcam. Equivalência de arquivo/piso com as anotações humanas
verificada; não são dois novos vídeos ou sessões independentes. Relatório em
`.local/evaluation/aaa34eb1-5732-4cf9-ae18-07edc581e81b/evaluation.json`.

## Inventário, autorização e preservação

O fundador forneceu novos arquivos e autorizou o processamento local. Foram
identificados **23 arquivos novos: 21 curtos e dois longos**, todos com hashes
distintos. O fundador mencionou 20 curtos; a verificação encontrou 21 e todos
correspondem ao repositório indicado. Há 28 arquivos no diretório atual, incluindo
cinco antigos que permanecem iguais. Os nomes 05.mp4 e 07.mp4 agora têm bytes
diferentes dos utilizados na etapa 05. Não foi atribuída a eles a prova histórica.

Os dois arquivos históricos foram recuperados da fonte pública em caminhos
novos, sem substituir os atuais: `Subject 3/Fall/05.mp4`, SHA-256
`efbb2c6c4721df503426918056b5ed3f233f77b55595b70dce9f9d68c48e650f`, e
`Subject 3/Fall/07.mp4`, SHA-256
`86a20851a1d3bfacbe11d8977972f95a256893b80cd4de66dc7bb224a4dca55b`.
Os bytes correspondem aos hashes registrados na etapa 05. A revisão da fonte e
a licença MIT são as mesmas documentadas abaixo. Um manifesto paralelo com os
caminhos recuperados reproduziu os seis arquivos históricos: cinco sem evento
e PERSON_ON_FLOOR aos 6000 ms no antigo 07. Isso preserva a prova de calibração;
não transforma esses vídeos em avaliação independente. Configurações, outboxes
e arquivos atuais não foram sobrescritos.

Cópias privadas dos 23 novos arquivos foram preservadas por SHA-256 em
`.local/etapa08/new-media/sources/<sha256>.mp4`, para evitar nova colisão de nomes.
Não houve exclusão/movimentação de arquivos originais. Vídeos, quadros para
inspeção, configurações, pesos e resultados detalhados continuam fora do Git.
Retenção OWNER_MANAGED; não foi criado prazo automático para a mídia fornecida.

A procedência foi informada pelo fundador e confrontada com metadados das fontes.
Correspondência de bytes não é verificação forense de autenticidade nem prova de
acidente real. Nenhum uso de publicação, treinamento ou redistribuição foi realizado.

## Fonte de cada vídeo curto

[GMDCSA24 — repositório dos autores](https://github.com/ekramalam/GMDCSA24-A-Dataset-for-Human-Fall-Detection-in-Videos),
revisão `5abac7693229900cf80f722e878fbb119211fc1c`.
SHA-1 de Git blob foi calculado com cabeçalho/tamanho e comparado à árvore da
fonte, resolvendo os nomes repetidos **pelos bytes**. SHA-256 local registrado
abaixo; o manifesto privado também guarda Git blob SHA-1 e URL completa.

O repositório apresenta o conjunto como detecção de quedas; a descrição de
quedas encenadas/atividades foi fornecida pelo fundador. Há 19 arquivos na pasta
Fall e dois na pasta ADL. Esses rótulos de diretório não são anotações temporais
nem estabelecem necessidade de ajuda. Há três identificadores de participantes
na fonte; não foram inferidas identidades por rosto nem verificadas datas/sessões.

Licença encontrada: [MIT na raiz do repositório](https://github.com/ekramalam/GMDCSA24-A-Dataset-for-Human-Fall-Detection-in-Videos/blob/5abac7693229900cf80f722e878fbb119211fc1c/LICENSE),
copyright 2024 Ekram Alam. Não se presumiu aprovação adicional de direitos de
imagem, treinamento ou distribuição comercial dos vídeos; esta tarefa manteve
uso local privado e atribuição. O README dos autores referencia o dataset v2.0
[DOI 10.5281/zenodo.12921216](https://doi.org/10.5281/zenodo.12921216).

| ID | Arquivo local em .local/videos | Caminho exato na fonte | SHA-256 local |
| --- | --- | --- | --- |
| intake08-01 | `03 (1).mp4` | [Subject 3/Fall/03.mp4](https://github.com/ekramalam/GMDCSA24-A-Dataset-for-Human-Fall-Detection-in-Videos/blob/5abac7693229900cf80f722e878fbb119211fc1c/Subject%203/Fall/03.mp4) | `267abab9b0ca7f4ef8425e2bfb2272ffeae1165fc2e3523ca1a6e0a62046b912` |
| intake08-02 | `03.mp4` | [Subject 1/Fall/03.mp4](https://github.com/ekramalam/GMDCSA24-A-Dataset-for-Human-Fall-Detection-in-Videos/blob/5abac7693229900cf80f722e878fbb119211fc1c/Subject%201/Fall/03.mp4) | `b17c5217c0050c959c45f7ead8ce80fa1c459d62109f25ea72461ac729d5307c` |
| intake08-03 | `04 (1).mp4` | [Subject 3/Fall/04.mp4](https://github.com/ekramalam/GMDCSA24-A-Dataset-for-Human-Fall-Detection-in-Videos/blob/5abac7693229900cf80f722e878fbb119211fc1c/Subject%203/Fall/04.mp4) | `a90c5a6f8c2c1bb899bf01f20615b896f67492e4267d2483cdbeacd71db62c92` |
| intake08-04 | `04.mp4` | [Subject 1/Fall/04.mp4](https://github.com/ekramalam/GMDCSA24-A-Dataset-for-Human-Fall-Detection-in-Videos/blob/5abac7693229900cf80f722e878fbb119211fc1c/Subject%201/Fall/04.mp4) | `a5563045241b462989867ea7973cf08cf5a4684ed43d47e104de1f4964794d5d` |
| intake08-05 | `05.mp4` | [Subject 1/Fall/05.mp4](https://github.com/ekramalam/GMDCSA24-A-Dataset-for-Human-Fall-Detection-in-Videos/blob/5abac7693229900cf80f722e878fbb119211fc1c/Subject%201/Fall/05.mp4) | `1aad4e2ee93b5498283fdc4a0478a5913dffc2ac8e2538574cd821ffb1b485f1` |
| intake08-06 | `06 (1).mp4` | [Subject 3/Fall/06.mp4](https://github.com/ekramalam/GMDCSA24-A-Dataset-for-Human-Fall-Detection-in-Videos/blob/5abac7693229900cf80f722e878fbb119211fc1c/Subject%203/Fall/06.mp4) | `c76b7b74f56b344c11a8cdae0e7f5e01e6ab89af048ba220c1a4687891d15f34` |
| intake08-07 | `06.mp4` | [Subject 1/Fall/06.mp4](https://github.com/ekramalam/GMDCSA24-A-Dataset-for-Human-Fall-Detection-in-Videos/blob/5abac7693229900cf80f722e878fbb119211fc1c/Subject%201/Fall/06.mp4) | `00f5e6f80632f9ba8cb054755c0a8d40afc66eca705ed14ad5f2c34a6822424f` |
| intake08-08 | `07.mp4` | [Subject 1/Fall/07.mp4](https://github.com/ekramalam/GMDCSA24-A-Dataset-for-Human-Fall-Detection-in-Videos/blob/5abac7693229900cf80f722e878fbb119211fc1c/Subject%201/Fall/07.mp4) | `e584c98e13100befb24fa1854987d8adb50324e0f73dd6278661a8887b428b86` |
| intake08-09 | `08 (1).mp4` | [Subject 3/ADL/08.mp4](https://github.com/ekramalam/GMDCSA24-A-Dataset-for-Human-Fall-Detection-in-Videos/blob/5abac7693229900cf80f722e878fbb119211fc1c/Subject%203/ADL/08.mp4) | `b383bb83a22b286cfc65fdd934137ee8b29e84aef7be0b540271d7c69d10fa8b` |
| intake08-10 | `08.mp4` | [Subject 1/Fall/08.mp4](https://github.com/ekramalam/GMDCSA24-A-Dataset-for-Human-Fall-Detection-in-Videos/blob/5abac7693229900cf80f722e878fbb119211fc1c/Subject%201/Fall/08.mp4) | `db2f0ead5f8daf17df4b9fbad5ed30debeffd37ec451eb72ec004e1e8972fbb9` |
| intake08-11 | `09.mp4` | [Subject 3/ADL/09.mp4](https://github.com/ekramalam/GMDCSA24-A-Dataset-for-Human-Fall-Detection-in-Videos/blob/5abac7693229900cf80f722e878fbb119211fc1c/Subject%203/ADL/09.mp4) | `5100230c1f7d22a400ca810b9eef7162853cb556484648bf5c9fbf1844df618d` |
| intake08-12 | `11.mp4` | [Subject 3/Fall/11.mp4](https://github.com/ekramalam/GMDCSA24-A-Dataset-for-Human-Fall-Detection-in-Videos/blob/5abac7693229900cf80f722e878fbb119211fc1c/Subject%203/Fall/11.mp4) | `d6651bf5f65931f583b48d6a3275c0d42b6d0f21a1db70e1c7ec4bdea24ac789` |
| intake08-13 | `13.mp4` | [Subject 3/Fall/13.mp4](https://github.com/ekramalam/GMDCSA24-A-Dataset-for-Human-Fall-Detection-in-Videos/blob/5abac7693229900cf80f722e878fbb119211fc1c/Subject%203/Fall/13.mp4) | `295489f450694ee828a8be2a4d441b4c1c44961c9548205edf67fa992701871b` |
| intake08-14 | `15.mp4` | [Subject 2/Fall/15.mp4](https://github.com/ekramalam/GMDCSA24-A-Dataset-for-Human-Fall-Detection-in-Videos/blob/5abac7693229900cf80f722e878fbb119211fc1c/Subject%202/Fall/15.mp4) | `4f288257071fb98f363a771c40a24a0088100c4b9b15b770d95b4a0ef599fa63` |
| intake08-15 | `16.mp4` | [Subject 1/Fall/16.mp4](https://github.com/ekramalam/GMDCSA24-A-Dataset-for-Human-Fall-Detection-in-Videos/blob/5abac7693229900cf80f722e878fbb119211fc1c/Subject%201/Fall/16.mp4) | `ba99029162ed00d1eeb4021320e70b116141a37f1f1150d13304a9d3d78d09a0` |
| intake08-16 | `19.mp4` | [Subject 2/Fall/19.mp4](https://github.com/ekramalam/GMDCSA24-A-Dataset-for-Human-Fall-Detection-in-Videos/blob/5abac7693229900cf80f722e878fbb119211fc1c/Subject%202/Fall/19.mp4) | `92b7789b30b1cd1381263a582f5292296060d5929b45dee2396271b8711d2b3e` |
| intake08-17 | `20.mp4` | [Subject 2/Fall/20.mp4](https://github.com/ekramalam/GMDCSA24-A-Dataset-for-Human-Fall-Detection-in-Videos/blob/5abac7693229900cf80f722e878fbb119211fc1c/Subject%202/Fall/20.mp4) | `2c50d5e3b8dc82baf8246bab4b86273fb93375ceea287f1d334a7bc56342fa36` |
| intake08-18 | `21.mp4` | [Subject 3/Fall/21.mp4](https://github.com/ekramalam/GMDCSA24-A-Dataset-for-Human-Fall-Detection-in-Videos/blob/5abac7693229900cf80f722e878fbb119211fc1c/Subject%203/Fall/21.mp4) | `3db7463e737831e8e97971e903664c787044341c8531c3519e30388473bd7abe` |
| intake08-19 | `23.mp4` | [Subject 2/Fall/23.mp4](https://github.com/ekramalam/GMDCSA24-A-Dataset-for-Human-Fall-Detection-in-Videos/blob/5abac7693229900cf80f722e878fbb119211fc1c/Subject%202/Fall/23.mp4) | `7c9d0973f9a1561e93ec4c8b29208a9884a0dd09033ddb412fbac56d0ed409d1` |
| intake08-20 | `24.mp4` | [Subject 2/Fall/24.mp4](https://github.com/ekramalam/GMDCSA24-A-Dataset-for-Human-Fall-Detection-in-Videos/blob/5abac7693229900cf80f722e878fbb119211fc1c/Subject%202/Fall/24.mp4) | `23a5d10a0186988424efae79e133f380d71974b5b057491a954f932a4f46d6bd` |
| intake08-21 | `25.mp4` | [Subject 2/Fall/25.mp4](https://github.com/ekramalam/GMDCSA24-A-Dataset-for-Human-Fall-Detection-in-Videos/blob/5abac7693229900cf80f722e878fbb119211fc1c/Subject%202/Fall/25.mp4) | `fafe0e19c418fd99bc56df0e590547dbb11059be2532fe698021b70d4870bb29` |

## Vídeos longos

Origem: Saint Paul Neighborhood Network / Third Age Yoga with Andy Gilats,
disponibilizados no Internet Archive. Metadados dos dois itens declaram
**Creative Commons Attribution 3.0**, com [URL da licença](https://creativecommons.org/licenses/by/3.0/).
Nome exato do arquivo, tamanho e SHA-1 local correspondem aos metadados de download.
Não se deduziu licença apenas da disponibilidade gratuita do vídeo. Atribuição
mantida; nenhum conteúdo foi publicado nem utilizado para treinar pesos.

- [Third_Age_Yoga_with_Andy_Gilats_-_Episode_1](https://archive.org/details/Third_Age_Yoga_with_Andy_Gilats_-_Episode_1), arquivo `Third_Age_Yoga_with_Andy_Gilats_-_Episode_1.mp4`: 1586.286 s; SHA-256 `4eddb130ebed423551d9da40babd7285d34e838582d8b5f9c5aa8d43f8f52dae`.
- [Third_Age_Yoga_with_Andy_Gilats_-_Episode_2](https://archive.org/details/Third_Age_Yoga_with_Andy_Gilats_-_Episode_2), arquivo `Third_Age_Yoga_with_Andy_Gilats_-_Episode_2.mp4`: 1781.715 s; SHA-256 `8948b87872b2e5f36489a92b955fdd9f774c0b66cd4c38ecaf2abb94974a5864`.

Os vídeos incluem cortes, títulos e reenquadramentos. Uma ROI fixa não é válida
para a montagem inteira. O processamento integral executou decodificação e Full
real para medir qualidade/recursos, **sem motor temporal de piso, eventos ou HTTP**.
Uma imagem inteira usada no cálculo de qualidade não foi declarada piso calibrado.
Logo, este ensaio não calcula falsos alertas, recall de postura ou continuidade LIVE.

| Item | Frames decodificados | Inferências | Conteúdo até último frame analisado (s) | Parede (s) | Inferência média (ms) | CPU, 100%=1 núcleo | Pico working set (bytes) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| intake08-22 | 47541 | 7932 | 1586.220 | 254.956 | 28.242 | 127.94 | 244273152 |
| intake08-23 | 53398 | 8909 | 1781.615 | 297.518 | 29.637 | 126.33 | 245075968 |

Total: 100.939 frames decodificados e 16.841 inferências, cerca de 56min08s de
conteúdo. 84.098 frames foram pulados por amostragem intencional; não são frames
perdidos de uma webcam. Métodos: process_time/perf_counter, tempo de inferência em
detect_for_video e GetProcessMemoryInfo; pico é do processo inteiro, inclusive
uso anterior no segundo arquivo. Parte do trabalho coincidiu com diagnósticos
curtos; não é benchmark de CPU isolada ou capacidade certificada.

| Item | NO_POSE | ONE_VALID_POSE | LOW_CONFIDENCE | MULTIPLE_POSES |
| --- | ---: | ---: | ---: | ---: |
| intake08-22 | 186 | 5826 | 1854 | 66 |
| intake08-23 | 183 | 6184 | 2499 | 43 |

ONE_VALID_POSE descreve o estado da observação, não cobertura confiável ou piso.
Planos fechados cortam o corpo; não há obrigação de detectar pose suficiente em
todos esses frames. Contagens de motivos de qualidade podem se sobrepor.
Detectores heurísticos de corte foram apenas pistas de revisão, não usados como
segmentação validada nem garantia de enquadramento. Blocos de 30 s foram guardados
sem exportação contínua de poses/imagens.

## Separação antes dos ensaios

Full oficial, política floor-v0.1, visibilidade/presença 0,5, duas poses, largura
640 e decisões 5 Hz foram preservados. Nenhum peso ou limiar foi treinado/ajustado.

- Calibração/investigação: 14 curtos dos Subjects 2 e 3 e os dois episódios de yoga.
- Avaliação reservada: sete curtos do Subject 1, separados por participante/ambiente
  de origem e congelados antes da inferência. Não se alega sete sessões independentes.
- As ROIs foram selecionadas pelo assistente sobre quadros vistos; o JSON registra
  ASSISTANT_VISUAL_REVIEW e humanReviewPending=true. Não foi atribuída ao fundador
  uma seleção/validação que ele não realizou.
- Anotações da avaliação foram preparadas antes da inferência, por inspeção visual
  de quadros a cada 200 ms, com incerteza de aproximadamente 200 ms. Confirmação
  humana ainda pendente. São resultados exploratórios contra essas anotações.

## Calibração/investigação: resultado desfavorável preservado

| Arquivo | Análises | Elegível (ms) | Eventos PERSON_ON_FLOOR / offset (ms) |
| --- | ---: | ---: | --- |
| `03 (1).mp4` | 28 | 3024 | 4624 |
| `04 (1).mp4` | 28 | 208 | nenhum |
| `06 (1).mp4` | 28 | 3984 | 2400 |
| `08 (1).mp4` | 25 | 608 | nenhum |
| `09.mp4` | 39 | 2800 | nenhum |
| `11.mp4` | 45 | 384 | nenhum |
| `13.mp4` | 21 | 2416 | 3808 |
| `15.mp4` | 59 | 2416 | nenhum |
| `19.mp4` | 78 | 6800 | 11424 |
| `20.mp4` | 58 | 6592 | 11424 |
| `21.mp4` | 46 | 6816 | 8400 |
| `23.mp4` | 38 | 2016 | nenhum |
| `24.mp4` | 36 | 3616 | nenhum |
| `25.mp4` | 37 | 5184 | 6224 |

Sete eventos em 14 arquivos não são recall: as posturas e durações de todos esses
arquivos não têm anotação temporal completa. Nenhum POSSIBLE_FALL foi emitido.
Há perdas por pontos essenciais insuficientes, projeção e duração curta. Os dois
ADL não geraram evento, mas isso não prova rejeição geral de alongamento/yoga.

Comparação adicional, somente nos 14 curtos de calibração: Full a 15 inferências/s,
com decisões ainda a 5 Hz e mesmos gates/ROIs, contra o Full a 5 Hz. Os dois
produziram os mesmos sete eventos, com os mesmos offsets. Mais inferências não
melhoraram o resultado neste ensaio. Não foi aplicado esse custo ao produto,
nenhum modelo/threshold foi selecionado com o resultado do conjunto reservado.

## Avaliação reservada: sete vídeos, anotações provisórias

Regra já documentada: mesmo kind, emissão dentro do alvo ou até 2 s depois do fim,
um match por alvo, duplicações separadas. Quatro posturas têm janela >=2 s.
As outras três posturas são reais na filmagem, mas o trecho restante no chão é
menor que a persistência mínima da baseline. Elas continuam listadas abaixo,
excluídas por duração do protocolo e **não rotuladas como negativos**. Essa exclusão
não equivale a dizer que a baseline atendeu esses três vídeos do dataset Fall.

| ID / arquivo | Intervalo de postura anotado (ms) | Janela >=2 s | Evento | Resultado provisório |
| --- | --- | --- | --- | --- |
| intake08-02 / `03.mp4` | 3400–5922 | sim | nenhum | perdido |
| intake08-04 / `04.mp4` | 3200–4961 | não | nenhum | curto; não pontuado como negativo |
| intake08-05 / `05.mp4` | 3400–5858 | sim | nenhum | perdido |
| intake08-07 / `06.mp4` | 4000–5697 | não | nenhum | curto; não pontuado como negativo |
| intake08-08 / `07.mp4` | 2400–5153 | sim | nenhum | perdido |
| intake08-10 / `08.mp4` | 2200–4353 | sim | 3808 | detectado |
| intake08-15 / `16.mp4` | 4200–6097 | não, provisório | nenhum | limítrofe; não pontuado como negativo |

O `16.mp4` é limítrofe: antecipar seu início anotado em cerca de 200 ms pode
levar a janela acima de 2 s. A classificação de duração depende da revisão humana;
o denominador provisório de quatro alvos deve ser revisto se a anotação mudar.

Contagens exploratórias: **1 alvo detectado e 3 perdidos entre 4 alvos com janela
suficiente**; três posturas curtas adicionais não pontuadas. Um alerta, zero
incidentes extras de episódio e zero alertas fora dos alvos nesta amostra curta.
25% é apenas a fração 1/4 contra anotação do assistente neste recorte, **não uma
acurácia geral**. Confirmação humana e negativos representativos continuam faltando.
O evento saiu aos 3808 ms; latência contra o início provisório 2200 ms: 1608 ms,
com incerteza da anotação. A janela interna do motor pode começar durante a
transição, portanto não equivale a confirmação de acidente nem reação clínica.

Necessidade de ajuda não foi anotada; não há recall de acidentes reais, eficácia
assistencial ou taxa confiável de falsos alertas/hora. Os sete vídeos do conjunto
reservado pertencem à pasta Fall, não são um conjunto negativo de cotidiano.
Não ajustar a baseline com esses resultados e depois reapresentar a mesma amostra
como avaliação independente. Se ela passar a orientar mudança de política, preservar
estes resultados e reservar outra avaliação para a versão nova.

## Janela estática de yoga e qualidade da calibração

### Revisão visual posterior do 03.mp4 pelo fundador

O fundador assistiu à prévia do intake08-02: descreveu o esqueleto como bom,
mas oscilando quando a pessoa permanece deitada, e o piso como compreensível,
porém precisando de marcação mais precisa. Isso não confirma corpo inteiro,
horário de início da postura, precisão dos pontos nem aprovação definitiva do piso.

Uma inspeção dos dados completos disponíveis da prévia, sem nova inferência,
reaplicou extract_features/QualityGate com os mesmos critérios e polígono.
Entre 3408 e 5824 ms (13 amostras, início da postura ainda provisório), 11
tinham baixa confiança nos pontos 25 e 27, joelho e tornozelo esquerdos; apenas
duas eram elegíveis e candidatas, aos 5024 e 5616 ms. Nestas duas, quadril já
dentro do piso, ângulos 78,47°/78,91° e razões 0,263/0,254. Não há continuidade
suficiente para a janela de 2 s. Refinar o piso sozinho não corrige essas perdas
de qualidade. Esses números não medem erro de coordenada nem jitter contra
referência humana de articulações; não foi criada uma métrica de estabilidade.

Diagnóstico privado: `.local/etapa08/new-media/review-intake08-02/baseline-diagnosis.json`.
Criada configuração de revisão nesse diretório, com cópia do piso, resultados
próprios e eventos/HTTP desabilitados. O fundador concluiu a remarcação pela GUI,
salva como versão 2 com sete pontos. Reprocessamento das mesmas observações
armazenadas, com features/QualityGate/TemporalEngine nativos, manteve 2/13
candidatas no trecho final, 11 inválidas e nenhum evento no vídeo, tanto na v1
como na v2. Depois o fundador confirmou explicitamente que o contorno revisado
acompanha o chão. Registro privado em review-intake08-02/human-review.json;
isso confirma o piso, não melhora da pose, corpo inteiro ou horários anotados.
Resultado privado do comparativo:
`review-intake08-02/floor-comparison-0127e28b-a7ec-41b4-b1c2-2fc41f5db396.json`.
Original e resultado reservado permanecem intactos; uma futura
alteração orientada por essa revisão deve preservar o resultado congelado e
ter outra avaliação para aferir ganho. Nenhum filtro visual ou gate foi alterado.

O [guia oficial do MediaPipe](https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker/python)
descreve saída por pontos/coordenadas, presence/visibility e tracking em VIDEO;
isso não fornece um rótulo de pessoa imóvel ou necessidade de ajuda. A prévia
atual desenha somente pontos atuais válidos. Suavização visual exigiria medir
também atraso e comportamento diante de perda de pose, sem preencher ausência
de evidência para satisfazer o motor.

Comandos de revisão (calibração executada pelo fundador; prévia posterior iniciada
pelo agente e alinhamento do contorno confirmado pelo fundador):

```powershell
uv run --project services/edge --frozen radar-edge calibrate --config .local/etapa08/new-media/review-intake08-02/config.yaml --frame-ms 0
uv run --project services/edge --frozen radar-edge run --config .local/etapa08/new-media/review-intake08-02/config.yaml --poses-only --preview-paused --replay-speed 0.25
```

### Diagnóstico de pose após a confirmação do piso

Foi executado o comando privado abaixo com o estimador real Full CPU/VIDEO,
duas poses, critérios 0,5 preservados. Um único frame do 03 (índice 119, offset
4016 ms, 640×360) foi repetido 30 vezes com timestamps artificiais de 200 ms.
Não é uma nova filmagem nem avaliação independente. Não houve motor temporal,
HTTP, gravação de frames ou uso desse ensaio como positivo.

```powershell
uv run --project services/edge --frozen python .local/etapa08/new-media/review-intake08-02/static-pose-diagnostic.py
```

Exit 0. As 30 observações continuaram LOW_CONFIDENCE por visibilidade dos pontos
25 e 27. Para os outros seis pontos essenciais, após excluir as cinco primeiras
inferências, houve 24 pares consecutivos válidos por ponto, com mediana/p95 de
deslocamento iguais a 0 px. Para 25/27 não houve par válido: métricas null,
sem representar ausência de erro por zero. O teste não reproduziu oscilação dos
pontos válidos nessa entrada idêntica; não demonstra estabilidade sob variações
reais de pixels ou melhora no vídeo original. A sobreposição de pernas visível
na filmagem é compatível com a baixa visibilidade, sem prova causal isolada.
Resultado: review-intake08-02/static-pose-ea0c395d-eb63-43b0-b82e-ca1997fbc43e.json.

Inspeção nativa das observações dos três vídeos perdidos, desde os inícios
provisórios já anotados, preservando os mesmos gates:

| Vídeo | Início provisório (ms) | Amostras | Elegíveis | Candidatas | Pontos com visibilidade insuficiente |
| --- | ---: | ---: | ---: | ---: | --- |
| 03.mp4 | 3400 | 13 | 2 | 2 | 25 e 27 em 11 amostras |
| 05.mp4 | 3400 | 13 | 0 | 0 | 28 em 12 amostras; 26 em 6 |
| 07.mp4 | 2400 | 14 | 0 | 0 | 26 e 28 em 14 amostras |

Não há falha de presence nesses pontos nesse recorte; a restrição é visibility.
Contagens de pontos podem se sobrepor. Resultado privado
loss-review-8529ee2f-2008-4e41-b2be-e954479e5493.json. Os inícios de postura
continuam provisórios; não se declarou confirmação humana desses intervalos.
Foram criadas cópias de revisão próprias para 05/07, eventos/HTTP desabilitados.
O 07 foi reprocessado com run --poses-only --no-preview (exit 0, 26 inferências);
o 05 foi aberto por Start-Process/uv com --poses-only --preview-paused
--replay-speed 0.25 para revisão humana. O fundador considerou o esqueleto
razoável e **reprovou a ROI v1 do 05**, por estar alta e incluir parede. Isso
não é confirmação de corpo inteiro, exatidão dos pontos ou horário da postura.
A ROI inicial selecionada pelo assistente não deve ser apresentada como piso
validado. A perda por baixa visibility também está registrada e não é corrigida
automaticamente pela remarcação. Registro em review-intake08-05/human-review.json.
Foi aberta a calibração GUI do 05 na cópia privada, com o comando abaixo.
O fundador concluiu e salvou a versão 2 com sete pontos. Reaplicação das mesmas
observações completas pela implementação nativa de features/qualidade/motor
manteve 13/13 amostras inválidas desde o início provisório de 3400 ms e nenhum
evento no vídeo, tanto com o piso original como com o revisado. Não houve nova
inferência, HTTP ou escrita em outbox nesse comparativo. Resultado privado:
review-intake08-05/floor-comparison-3de930f3-ecdd-4266-aee0-302fd22a4c0f.json.
Prévia FILE da v2 aberta pausada a 0,25x; o fundador confirmou depois que o piso
agora está correto. Registro em review-intake08-05/human-review-v2-confirmed.json,
sem atribuir confirmação de estabilidade/corpo inteiro/horário da postura.
O arquivo human-review.json preserva a rejeição da v1 e human-review-v2-pending.json
permanece como registro histórico anterior à confirmação. A janela própria do 05
foi encerrada pelo agente via CloseMainWindow, após verificar a árvore do processo
uv registrado; não foi contada como nova execução completa do vídeo. Foi aberta
a prévia FILE do 07 por Start-Process/uv, --poses-only --preview-paused
--replay-speed 0.25, em review-intake08-08/config.yaml. Conferência humana do
piso/pose do 07 resultou em acompanhamento considerado bom para MVP pelo fundador,
mas piso reprovado para uso sem remarcação. Isso não confirma visibilidade integral
de pernas/pés, precisão quantitativa ou os intervalos de postura. Registro privado
em review-intake08-08/human-review.json. Aberta a calibração GUI do 07, por
Start-Process/uv: calibrate --config
.local/etapa08/new-media/review-intake08-08/config.yaml --frame-ms 0.
Fundador salvou o piso v2 com oito pontos pela GUI. Reaplicação das mesmas
observações completas a features/qualidade/motor manteve 14/14 amostras
inelegíveis desde o início provisório de 2400 ms e nenhum evento no vídeo
com ambos os pisos. Nenhuma nova inferência, HTTP ou outbox nesse comparativo.
Resultado privado: review-intake08-08/floor-comparison-4e052ee7-b746-47e2-97be-70bbd2796f18.json.
Registro da marcação salva em human-review-v2-pending.json; prévia v2 aberta
pausada a 0,25x com --poses-only. O fundador confirmou o alinhamento do piso v2;
confirmação em review-intake08-08/human-review-v2-confirmed.json. Isso conclui
a revisão dos pisos dos três vídeos perdidos, sem validar estabilidade de pose
ou os intervalos humanos de postura.

Depois dessas confirmações foi executada novamente a cadeia completa de
inferência Full e motor temporal, em filas novas e sem HTTP:

```powershell
uv run --project services/edge --frozen radar-edge evaluate --manifest .local/etapa08/new-media/review-floor-v2-manifest.json
pnpm.cmd demo:check --engineering
```

Ambos exit 0. O manifesto paralelo marca esta rodada como CALIBRATION, com
annotationsComplete=false: os alvos ainda são provisórios e não se declara
avaliação independente nova após revisar o resultado. Nenhum original foi
reclassificado/sobrescrito. Novos resultados com piso v2:

| Vídeo | Observado (ms) | Elegível no vídeo inteiro (ms) | Eventos |
| --- | ---: | ---: | ---: |
| 03.mp4 | 5824 | 2400 | 0 |
| 05.mp4 | 5824 | 3216 | 0 |
| 07.mp4 | 5024 | 1008 | 0 |

Elegibilidade do vídeo inteiro não equivale a duração de postura candidata.
Pisos confirmados não corrigiram as perdas por qualidade; nenhuma alteração
de modelo/gate/suavização foi feita. Resultado privado
`.local/evaluation/070c7242-8e3e-4188-bd0e-37adcc7fef98/evaluation.json`, log
`.local/etapa08/new-media/review-floor-v2-evaluation.log`. Percepção continua
não aprovada, etapa 08 PARCIAL; os demais gates físicos/offline permanecem.

As ROIs iniciais sem aceite
humano mantêm provisória a interpretação da avaliação congelada. Baseline reservada e
outboxes originais preservadas. Nenhuma mudança em filtros, modelo ou política.

```powershell
uv run --project services/edge --frozen radar-edge calibrate --config .local/etapa08/new-media/review-intake08-05/config.yaml --frame-ms 0
```

### Janela de yoga

Um diagnóstico adicional usou os frames originais entre 22:00 e 22:20 do episódio
1, sem recodificar e preservando offsets. Não é nova amostra independente.
Foram processados 20 s de pessoa voluntariamente deitada; 19.786 ms entre
observações foram elegíveis. Não houve evento: a ROI conservadora do primeiro
ensaio excluiu o quadril em todas as 100 observações. Isso é limitação daquela
calibração, **não demonstração de que o modelo reconhece exercício ou dispensa ajuda**.
O resultado foi preservado, sem deslocar ROI apenas para obter disparo. Falta
confirmar manualmente uma região de piso adequada para cada plano estático.

## Reproduzir os diagnósticos locais e estado da entrega

### Dois vídeos adicionais de sentar na cadeira

Recebidos após a comparação de modelos, com autorização de processamento local
implícita no pedido de teste. Correspondência exata Git blob SHA-1 na revisão
GMDCSA24 `5abac7693229900cf80f722e878fbb119211fc1c`, sem inferir origem pelo nome:

| ID | Arquivo fornecido | Caminho completo na fonte | SHA-256 |
| --- | --- | --- | --- |
| chair08-01 | sentar-cadeira1.mp4 | [Subject 1/ADL/11.mp4](https://github.com/ekramalam/GMDCSA24-A-Dataset-for-Human-Fall-Detection-in-Videos/blob/5abac7693229900cf80f722e878fbb119211fc1c/Subject%201/ADL/11.mp4) | `cb12602e5cd5d3e2ed9b6f9026926bb6609cb06428e07dce916e5527a9b2e5e9` |
| chair08-02 | sentar-cadeira2.mp4 | [Subject 1/ADL/13.mp4](https://github.com/ekramalam/GMDCSA24-A-Dataset-for-Human-Fall-Detection-in-Videos/blob/5abac7693229900cf80f722e878fbb119211fc1c/Subject%201/ADL/13.mp4) | `406dd142be0bf973302caabf38f1109d939b5f0154ef88158b3adc5a50859d51` |

Mesma licença MIT da raiz já registrada; nenhum direito adicional de divulgação
ou treinamento presumido. Cópias privadas por hash, metadados e quadros de
inspeção em `.local/etapa08/chair-intake-376f023c-bd1d-4ff4-8a49-101b5c073596`.
Decodificação integral com FileSource/FFmpeg: 277 frames, último timestamp 9280 ms,
e 187 frames, último timestamp 6272 ms, respectivamente. Originais preservados.
Contato visual a cada 500 ms mostra andar/posicionar cadeira/sentar/ler no primeiro
e andar/sentar no segundo, sem postura no chão nos quadros inspecionados.
Isso ainda não é anotação humana completa; nenhum modelo foi executado nesses
novos vídeos nesta preparação.

Ambos são da mesma pasta de origem Subject 1 usada na investigação; datas/sessões
reais e identidades não foram confirmadas. Classificação CALIBRATION_CONFUSER,
sem chamar os dois clipes de sessões independentes ou duas categorias distintas.
Não contam automaticamente como conclusão dos oito confundidores do protocolo.
Configurações próprias, Full preservado, câmera UUID/piso/resultados separados,
eventos e HTTP desabilitados na prévia. Anotações provisórias privadas, piso e
revisão completa pelo fundador pendentes.

Iniciada GUI calibrate --config
.local/etapa08/chair-intake-376f023c-bd1d-4ff4-8a49-101b5c073596/chair08-01/config.yaml
--frame-ms 0, por Start-Process/uv. O fundador concluiu e salvou o piso v1 com
dez pontos. Abriu-se por Start-Process/uv a prévia do primeiro, --poses-only
--preview-paused --replay-speed 0.5, para revisão integral da cena e piso.
Esta prévia usa inferência Full, mas não o motor temporal nem HTTP. Confirmação
humana integral e teste de alertas foram feitos depois: fundador confirmou piso
correto e ninguém deitado no chão após a solicitação de assistir até o fim.
Registro human-review.json e manifesto negativo completo foram gravados antes
da execução do motor temporal; prévia não apresentou o resultado do classificador.
Mantém-se CALIBRATION, por falta de independência de sessão/origem.

Comandos efetivamente executados com uv frozen: python
.local/etapa08/prepare-chair01-evaluation.py (exit 0), seguido de radar-edge
evaluate --manifest
.local/etapa08/chair-intake-376f023c-bd1d-4ff4-8a49-101b5c073596/chair08-01/evaluation-manifest.json
(exit 0). Inferência Full/motor reais, fila exclusiva, sem HTTP: zero eventos,
9216 ms observados, 8624 ms elegíveis no vídeo inteiro, 98 ms de cauda não
observada; duas observações com baixa qualidade/ponto essencial insuficiente.
Resultado compatível com a cena negativa nesse ensaio, sem estimar taxa geral de
falsos alertas a partir de nove segundos. Elegibilidade não é precisão de pose.
Resultado privado `.local/evaluation/df336f4b-9549-4fa3-95cd-c1d2e56ffe91/evaluation.json`.

Depois foi aberta a calibração GUI do segundo vídeo, em chair08-02/config.yaml,
mesmos argumentos calibrate/--frame-ms 0. Fundador salvou o piso v1 com nove
pontos, confirmado por load_calibration. Aberta a prévia Full do segundo por
Start-Process/uv com --poses-only --preview-paused --replay-speed 0.5 para
conferência integral da cena e alinhamento do piso, ainda pendentes. Ainda não
houve teste temporal do segundo; não contar ausência de alerta em poses-only
como acerto negativo.

Na revisão do segundo, fundador relatou que o esqueleto passa a acompanhar a
cadeira/pernas da cadeira ao sentar de lado. Não confirmou explicitamente piso
ou anotação negativa integral naquele momento. A prévia terminou status ok/ENDED, com 32
observações exportadas completas e motor desabilitado. Inspeção dos dados e
reaplicação nativa de features/QualityGate/TemporalEngine, sem inferência nova,
HTTP ou outbox: ONE_VALID_POSE em 32/32, elegibilidade técnica em 31/32 (uma
BODY_CROPPED), zero candidatas e zero emissões. Isso é diagnóstico, sem afirmar
aprovação negativa ou precisão dos pontos. A prévia não detectou uma segunda
pose nesse vídeo; há uma pose com potencial associação incorreta de membros à
estrutura da cadeira. Quadros de 4000/6000 ms mostram tronco/braço acompanhando
a pessoa e parte dos pontos inferiores junto à cadeira, com perna parcialmente
oculta. Sem pontos humanos de referência, erro articular não foi quantificado.

Evidências privadas em chair08-02/chair-confusion-diagnosis.json e
diagnostic-overlay-{3024,4000,6000}.jpg, gerados pelo renderizador local sobre
observações existentes; não foram publicados ou usados para treinar pesos.
Este caso evidencia que confiança >=0,5 e desenho verde não garantem localização
correta. Mantido como falha/limitação de pose a investigar, sem suavização para
esconder o problema e sem nova alteração de modelo/política. Conferência humana
do piso e da cena completa ficou pendente antes de formalizar teste negativo.

Depois de novas reproduções (explicitamente sem correção do esqueleto), o fundador
confirmou piso correto e ninguém deitado durante a cena inteira. Gravados
chair08-02/human-review.json e evaluation-manifest.json antes de executar o teste
temporal completo. Executado com uv frozen: radar-edge evaluate --manifest
.local/etapa08/chair-intake-376f023c-bd1d-4ff4-8a49-101b5c073596/chair08-02/evaluation-manifest.json,
exit 0. Full/motor reais, fila nova, sem HTTP: zero eventos, 6208 ms observados,
5808 ms elegíveis e 98 ms de cauda não observada; uma observação BODY_CROPPED.
Resultado privado `.local/evaluation/f16e47b6-2ef1-460e-a318-f58b7f7e7e41/evaluation.json`.

Os dois ensaios completos somam 15424 ms observados, 14432 ms elegíveis, caudas
de 196 ms e zero eventos. São dois clipes da mesma categoria/mesmo grupo de
origem, não duas sessões independentes confirmadas. O resultado de alertas é
compatível com as cenas negativas confirmadas; não comprova precisão articular,
taxa geral de falsos alertas ou conclusão dos oito confundidores. A associação
de parte dos pontos à cadeira permanece registrada como falha/limitação de pose.
Não houve alteração de modelo, critério, suavização ou dados operacionais.

### Diagnósticos anteriores

Scripts de investigação, dados e configurações privadas estão em
`.local/etapa08/new-media`; não são dependências ocultas da instalação do produto.
Os comandos realmente executados, a partir da raiz com activate.ps1:

```powershell
uv run --project services/edge --frozen python .local/etapa08/new-media/run-shorts.py
uv run --project services/edge --frozen radar-edge evaluate --manifest .local/etapa08/new-media/heldout-manifest.json
uv run --project services/edge --frozen python .local/etapa08/new-media/run-long-quality.py
uv run --project services/edge --frozen python .local/etapa08/new-media/run-yoga-window.py
uv run --project services/edge --frozen python .local/etapa08/new-media/compare-tracking.py
uv run --project services/edge --frozen radar-edge evaluate --manifest .local/etapa08/new-media/recovered-legacy/evaluation-full.json
```

Cada comando encerrou com exit 0. O run curto retoma a outbox ao repetir; evaluate
cria saídas novas. O script de janela é investigação com fila própria, sem HTTP.
Não rodar script antigo nos novos 05.mp4/07.mp4; seus hashes e ROIs são diferentes.
Inspeção de metadados e SHA, associação Git/Archive e calibração MANUAL_POINTS foram
feitas por scripts locais de preparação; não se executou treinamento de pesos.

Provas preservadas em inventory.json, split-plan.json, source-mapping.json,
archive-mapping.json, short-calibration-results.json, heldout-annotations.json,
heldout-result.json, intake08-22-long-quality.json, intake08-23-long-quality.json e
tracking-comparison-summary.json, além dos relatórios/outboxes de cada execução.
Recuperação histórica: recovered-legacy-sources.json e
recovered-legacy/evaluation.log; resultado em
`.local/evaluation/388044ef-0565-46ff-b3aa-fd42c274ff7f/evaluation.json`.

A contribuição concreta é procedência verificável, arquivos protegidos contra
colisão, avaliação separada, diagnósticos reproduzíveis e perdas medidas. Não há
melhora de precisão comprovada nem mudança silenciosa do detector. Os dados mostram
que ainda há trabalho de robustez; calibrar piso não substitui qualidade de pose.

A etapa 08 permanece parcial: revisão humana de anotações/piso, mais confundidores
anotados, fluxo LIVE positivo, 30 min reais de webcam, operação sem internet e
apresentação. Os 56 min de conteúdo foram replay acelerado (cerca de 9 min de
parede nas duas execuções), não observação física contínua de webcam.
