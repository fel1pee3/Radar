# Comparação de pose na etapa 08

Data: 22/10/2026, America/Sao_Paulo. Etapa 08 PARCIAL.

## Objetivo e método

Comparar Full e Heavy com critérios preservados, diante das perdas registradas
após a revisão humana dos pisos. Experimento local de calibração/diagnóstico,
sem instalar Heavy no produto ou trocar configurações operacionais.

São 17 curtos: os 14 de calibração dos Subjects 2/3 e os três perdidos do
Subject 1 (03/05/07), agora em cópias de diagnóstico com piso v2 confirmado
pelo fundador. Os três não constituem avaliação independente de uma alternativa
selecionada depois de observar suas falhas. Não usar os quatro restantes do
mesmo participante/sessão desconhecida como nova avaliação independente.
A avaliação congelada continua preservada, com suas anotações provisórias.

Mesmo arquivo/hash, orientação, largura 640, timestamps da mídia e ROI por caso;
CPU/VIDEO, duas poses, sem máscaras, inferência e decisão a 5 Hz, presence e
visibility 0,5, política floor-v0.1. Features, QualityGate e TemporalEngine reais.
Sem HTTP, outbox operacional, webcam, filtros novos ou treinamento de pesos.
Os pisos dos outros 14 curtos ainda têm seleção do assistente sem aceite humano.

Processos separados por variante, clipes sequenciais. Inferência média/P95 são
medidas locais; memória é pico working set do processo inteiro e cumulativo
entre clipes. Parede/CPU incluem setup, hash, decodificação e cleanup. Replay
acelerado não demonstra capacidade LIVE, estabilidade de 30 min ou latência
contra anotação humana. Mais observações válidas não provam articulações corretas.

## Artefatos e fonte

[Catálogo oficial](https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker#models)
e [Model Card](https://storage.googleapis.com/mediapipe-assets/Model%20Card%20BlazePose%20GHUM%203D.pdf).
O cartão declara Apache 2.0 para Lite/Full/Heavy e uso pretendido em pose/fitness;
suas limitações continuam aplicáveis. Nenhuma validação assistencial é inferida.

Full ativo: SHA-256
`5134a3aad27a58b93da0088d431f366da362b44e3ccfbe3462b3827a839011b1`.
Heavy experimental: bundle oficial float16/v1,
`https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float16/1/pose_landmarker_heavy.task`,
30.664.242 bytes, SHA-256 calculado
`64437af838a65d18e5ba7a0d39b465540069bc8aae8308de3e318aad31fcbc7b`.
Download HTTPS confrontado com tamanho e MD5 base64 publicados na API de metadados
do bucket: `RT3sTQLMxNPOgStt6E+lFg==`, geração `1682642785425305`.
SHA-256 foi calculado localmente e fixado para carregar o experimento; não foi
apresentado como assinatura publicada pelo autor. Peso privado em
`.local/models/pose_landmarker_heavy.research.task`, fora do Git.

Scripts/manifesto/logs privados em `.local/etapa08/new-media`;
comparação em `model-comparison-8ba0d8cb-ce3c-4034-86ac-359fcbea0b33`.
O núcleo deriva do script da comparação de tracking, com medição adicional de
inferência/CPU/memória; adaptador Heavy é privado. A aplicação conserva seu
registro Lite/Full e verificação de hash existentes, sem dependência oculta desse
script para instalação ou execução.

Comandos reais:

```powershell
. ./scripts/activate.ps1
uv run --project services/edge --frozen python .local/etapa08/new-media/run-model-comparison.py --variant full
uv run --project services/edge --frozen python .local/etapa08/new-media/run-model-comparison.py --variant heavy
```

## Resultado

Ambos os comandos terminaram com exit 0: 652 inferências/análises por variante,
1304 no total. Arquivos por clipe, summary.json e logs privados preservados.

| Medida local | Full | Heavy |
| --- | ---: | ---: |
| Clipes | 17 | 17 |
| Observações elegíveis, vídeo inteiro | 327/652 | 243/652 |
| Eventos, sem recall estimável | 7 | 3 |
| Inferência média ponderada (ms) | 27,21 | 62,43 |
| Parede acumulada dos clipes (s) | 35,81 | 57,34 |
| CPU acumulada (s) | 61,89 | 86,48 |
| Pico working set do processo (bytes) | 273506304 | 340803584 |

| ID | Eventos Full / offsets (ms) | Eventos Heavy / offsets (ms) |
| --- | --- | --- |
| intake08-01 | 1 / 4624 | 0 |
| intake08-03 | 0 | 0 |
| intake08-06 | 1 / 2400 | 1 / 2400 |
| intake08-09 (ADL) | 0 | 0 |
| intake08-11 (ADL) | 0 | 0 |
| intake08-12 | 0 | 0 |
| intake08-13 | 1 / 3808 | 0 |
| intake08-14 | 0 | 0 |
| intake08-16 | 1 / 11424 | 1 / 12800 |
| intake08-17 | 1 / 11424 | 0 |
| intake08-18 | 1 / 8400 | 0 |
| intake08-19 | 0 | 0 |
| intake08-20 | 0 | 0 |
| intake08-21 | 1 / 6224 | 1 / 5824 |
| intake08-02, 03.mp4 revisado | 0 | 0 |
| intake08-05, 05.mp4 revisado | 0 | 0 |
| intake08-08, 07.mp4 revisado | 0 | 0 |

Todos os eventos foram PERSON_ON_FLOOR. Os três clipes revisados continuaram sem
evento. Nas janelas finais de postura provisoriamente anotadas, Full/Heavy tiveram
2/8 observações elegíveis entre 13 no 03, 0/2 entre 13 no 05 e 0/0 entre 14 no 07.
Esse aumento localizado de qualidade no 03 não sustentou a janela de emissão.
O Heavy não recuperou os casos perdidos e deixou de emitir quatro eventos
produzidos pelo Full; sua média de inferência foi aproximadamente 2,29 vezes maior.
Isso não prova que os sete eventos sejam verdadeiros acidentes ou que três sejam
melhor controle de falsos positivos: os alvos/negativos não têm anotação humana
completa. Dois ADL sem eventos não medem taxa confiável de falsos alertas.

**Decisão:** Heavy não adotado. Full operacional, critérios, dependências e locks
preservados. O subpasso de comparar esta alternativa foi executado, mas o item de
qualidade da percepção não foi aprovado e nenhuma melhoria foi comprovada.
Falta investigar uma solução que sustente evidência corporal nas condições
pretendidas, com negativos anotados e avaliação nova antes da adoção. Não reduzir
visibility, esconder pontos ausentes ou usar estes mesmos casos como avaliação
independente de uma versão escolhida a partir deles.

## Pendências para encerrar a etapa

Posteriormente, uma comparação com família diferente (RTMO-s) mostrou melhora
visual no confundidor da cadeira, confirmada pelo fundador. Ainda não é uma
troca do modelo operacional ou solução comprovada dos três eventos perdidos.
Veja [investigação específica](INVESTIGACAO_CADEIRA_ETAPA_08.md).

Verificação posterior: demo:check --engineering retornou 0; demo:check retornou
2, mantendo liberação pendente. Auditoria dos 34 resultados, tipo dos eventos,
SHA-256/ignore do peso privado, links do relatório e git diff --check passaram.
Não se repetiu a suíte completa: código de engenharia e seu fingerprint
permanecem iguais, somente diagnóstico privado e documentação mudaram.

Qualidade de percepção e avaliação anotada continuam pendentes. Engenharia
automatizada já verificada é separada dessas provas. Também faltam LIVE positivo
com revisão humana, webcam contínua por 30 min, execução offline e apresentação.
Etapa 09 opcional não foi iniciada. Sem commit, push, publicação ou treinamento.
