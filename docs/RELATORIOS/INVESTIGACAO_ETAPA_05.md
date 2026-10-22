# Investigação de percepção — etapa 05

Data: 21/10/2026. Resultado: fluxo positivo real demonstrado com seleção explícita
do Full, mantendo as falhas e limitações observadas. Complementa o
[relatório 05](ETAPA_05.md) e a decisão D34. Commit/push autorizados pelo fundador
após a validação. Sem deploy.

## Problema investigado

Seis arquivos descritos como filmagens reais pelo fundador terminaram sem evento
com Lite. Ele observou esqueleto piscando/sumindo. Em `piso-d`, confirmou pessoa
deitada, piso correto e orientação correta, mas os gates 2D rejeitaram a postura.
Um vídeo gerado por IA produziu evento local e permaneceu separado; não contou
como prova real. Não se presumiu que todo resultado negativo fosse o mesmo erro.

Inventário preservado: Windows 11 Pro x64, Ryzen 5 5625U, 15,4 GiB RAM,
Python 3.12.15, MediaPipe Tasks 1.1.1, único opencv-contrib-python 5.0.0.93.
Nenhuma dependência/lock alterado. Vídeos, pesos, SQLite e tokens privados.

## Pesquisa e hipóteses

O [guia oficial Python](https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker/python)
descreve VIDEO síncrono com timestamps de mídia e tracking. A
[implementação oficial pinada](https://github.com/google-ai-edge/mediapipe/blob/998a5d77bb3d0e06211b6e9cc1fd6094e6051bfb/mediapipe/tasks/cc/vision/pose_landmarker/pose_landmarker_graph.cc#L285)
habilita smoothing somente para uma pose; com duas poses, o detector pode ser
acionado quando há menos poses rastreadas que o máximo configurado. Isso é um
mecanismo plausível de jitter/custo, não prova da causa exclusiva nem da revisão
exata embutida na DLL instalada. A proteção para segunda pessoa foi mantida:
não se trocou num_poses de 2 para 1 para obter um resultado favorável.

A auditoria do adaptador não encontrou troca incorreta BGR/RGB, timestamps de
CPU substituindo tempo de mídia ou ângulos calculados sem correção por pixels.
Encontrou divergência na prévia: verde dependia só de visibility; o motor também
exigia presence. A prévia foi corrigida para valores atuais finitos, presença e
visibilidade suficientes, sem inventar pontos/poses nem preencher lacunas.

Hipóteses medidas separadamente: (1) Full estima pontos suficientes melhor que
Lite nesses arquivos; (2) alimentar VIDEO a 15 Hz melhora tracking mantendo
decisão a 5 Hz. O segundo ensaio preservou os instantes de decisão e não alterou
a janela temporal. Não houve ajuste de threshold depois de observar os resultados.

## Comparação controlada

Script privado `.local/etapa05/investigate_pose.py`: decoder/modelo reais,
sem HTTP/outbox operacional, mesmos polígonos manuais, resolução, num_poses=2,
presença/visibilidade ≥0,5, política floor-v0.1. Cinco arquivos × duas variantes
× duas cadências = **20 execuções**. Resultados escalares privados em
`.local/etapa05/investigation/`, sem frames ou coordenadas de landmarks exportadas.

Cada célula: **elegíveis / candidatas / eventos** nas decisões a 5 Hz.

| Arquivo / decisões | Lite, inferência 5 Hz | Full, inferência 5 Hz | Lite, inferência 15 Hz | Full, inferência 15 Hz |
| --- | --- | --- | --- | --- |
| piso-e-05 /51 | 15 /0 /0 | 11 /1 /0 | 15 /0 /0 | 11 /1 /0 |
| piso-f-07 /45 | 15 /6 /0 | **40 /32 /1** | 15 /6 /0 | **40 /32 /1** |
| piso-a /109 | 6 /6 /0 | 7 /0 /0 | 5 /5 /0 | 7 /0 /0 |
| piso-b /73 | 0 /0 /0 | 0 /0 /0 | 0 /0 /0 | 0 /0 /0 |
| piso-d /78 | 58 /0 /0 | 53 /0 /0 | 57 /0 /0 | 50 /0 /0 |

O evento Full em `piso-f-07` foi PERSON_ON_FLOOR aos **6000 ms** nas duas
cadências. Ampliar inferência para 15 Hz não corrigiu os outros vídeos e elevou
o custo: nesse arquivo, 45→137 inferências e parede 2,7712→4,9676 s no ensaio
controlado. Lite também ficou sem evento em 15 Hz. Mantida inferência/decisão
a 5 Hz na configuração validada; não foi introduzida complexidade sem ganho.

O diagnóstico por ponto localizou a principal perda do `piso-f-07`: índice 28
(tornozelo direito) abaixo da visibilidade mínima em **29** decisões com Lite e
**3** com Full, nas observações com uma pose. O índice 27 falhou uma vez em cada
variante. Nos outros arquivos:

- `piso-e-05`: tornozelos/joelhos insuficientes; Full não melhorou a elegibilidade.
- `piso-a`: joelho e tornozelo direitos frequentemente insuficientes; também
  houve múltiplas hipóteses de pose. Isso não prova visualmente duas pessoas.
- `piso-b`: tornozelos com presença/visibilidade insuficientes e pontos essenciais
  fora do quadro no resultado do modelo; não se atribuiu isso automaticamente
  a corpo real cortado.
- `piso-d`: muitos pontos suficientes e quadril no piso, mas ambos os modelos
  falharam nos gates de ângulo/proporção. A limitação de perspectiva permanece.

## Implementação decorrente

- Registry de bundles Lite/Full com URL versionada e SHA-256, seleção explícita
  `model.variant` e caminho correspondente; Full exige path explícito.
- Identidade real em doctor, observação, evento e relatório. Hash selecionado no
  fingerprint impede retomar uma execução Lite como se tivesse usado Full.
- `model-fetch --variant full` reproduz o download e rejeita bundle divergente.
  Configurações antigas continuam Lite; nenhum arquivo histórico foi convertido.
- Métricas agregadas por articulação: ausência, valor não finito, fora do quadro,
  baixa presença/visibilidade. Sem série corporal contínua ou mistura de pessoas.
- Prévia usa os critérios de presença/visibilidade da análise e explica motivos.
  `--preview-paused` inicia pausada; Espaço inicia/pausa/retoma, Q/Esc encerra.
  Pausa de interface não altera tempo da cena ou acelera o restante do replay.
- Resumo diferencia checkpoint inicial e último checkpoint persistido, inclusive
  após rollback. Não mudou a transação nem o estado operacional.

O [catálogo oficial](https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker#models)
oferece Full float16/v1. Artefato obtido explicitamente via HTTPS oficial:
9.398.198 bytes, SHA-256
`5134a3aad27a58b93da0088d431f366da362b44e3ccfbe3462b3827a839011b1`.
Origem fixa:
`https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/1/pose_landmarker_full.task`.
O [Model Card](https://storage.googleapis.com/mediapipe-assets/Model%20Card%20BlazePose%20GHUM%203D.pdf)
vinculado aos bundles declara Apache 2.0 para os pesos, registra limitações de
pose/oclusão/enquadramento e não os destina a decisões críticas à vida. Também
lista vigilância fora do uso pretendido; isso é uma limitação de validação/uso,
separada das permissões da licença. Não se declara aprovação assistencial ou
comercial. Ressalva sobre métricas nativas do SDK permanece em D30.

## Percurso positivo na aplicação real

Configuração `.local/edge-piso-f-07-full.yaml`, outbox própria
`.local/etapa05/piso-f-07-full.sqlite`, calibração manual anterior preservada:
`74bfeb97-6767-4cd4-9eb7-531d17d54778-v1`. Origem real declarada pelo fundador,
encontrada na internet; uso local solicitado, procedência/licença de mídia não
verificadas independentemente. Arquivo privado, sem redistribuição.

Resultado nativo: 269 frames lidos, 45 analisados, 224 pulados, 40 poses
geometricamente elegíveis, 32 candidatas, **um evento**. Houve uma observação
MULTIPLE_POSES e quatro LOW_CONFIDENCE, sem remover esses gates.

| Sinal / medida | Valor |
| --- | --- |
| Rótulo / emissão | PERSON_ON_FLOOR /6000 ms |
| Início candidato / duração | 3824 ms /2176 ms |
| Tronco / proporção altura-largura | 89,6352° /0,310274 |
| Quadril no piso / fração temporal válida | true /1 |
| Descida rápida / taxa | false /5 análises/s |
| Elegível / observado | 7200 ms /8816 ms |
| Inferência média / parede total / throughput | 28,6099 ms /3,8183 s /11,7852 análises/s |
| CPU (um núcleo=100%) / pico working set | 142,81% /277.213.184 bytes |
| Evidência | skeleton corporal, sem imagem/vídeo/face |
| Entrega | DELIVERED na primeira tentativa, ACK TEST |

Evento `49adcf39-a7c2-414a-ae8f-852e1a5ca8ee`, episódio
`e0243cb7-bd1d-4705-9070-048f50e663f5`, incidente
`6cfd7d88-ae34-4b48-ad5a-d592cbd020a9`. Relatório privado:
`.local/results/edge/140c032b-0e96-4cdc-9ac5-cad2f3f5aecf/report.json`.
Não nasceu do simulador nem de observações sintéticas.

Reabrir a mesma execução reconheceu EOF/ACTIVE: zero novas análises/eventos,
mesmo runId. Reenvio explícito do payload imutável à API retornou HTTP 200,
duplicate=true, mesmo incidentId. Hash do payload para conferir estabilidade:
`0775cd34e61b2bb5037102f12404bf1217e2d42080a75ea97f5e53785794dd62`.

O fundador confirmou a nova prévia: pessoa deitada, piso correto e esqueleto
melhor. A reprodução com início pausado terminou ENDED, 45 análises, 26,3238 s
de pausa do operador e zero eventos nesse percurso poses-only. Depois confirmou
no painel título, Reprodução/Teste, offset 6000 ms, modelo Full, duração 2176 ms
e pose. A inspeção foi feita pelo fundador; o agente não alega ter visto a tela.

## Avaliação, regressões e limites

`radar-edge evaluate --manifest .local/evaluation-full.json` processou seis
arquivos em outboxes isoladas, sem HTTP: um evento no `piso-f-07`, zero nos
outros cinco. Resultado:
`.local/evaluation/2acb3f64-52c2-46fd-a70f-0525d6fd2ab2/evaluation.json`.
O positivo repetido a 2× produziu o mesmo rótulo e offset, com digest de amostragem
idêntico `f3224226abcd1027b3bba84378b2ef7e2bc05e05c7dd4cc59b8a9f5ee21a4bc3`.
Resultado 2×:
`.local/evaluation/360da6a6-7897-4a00-92d3-82900242d994/evaluation.json`.

Todos continuam CALIBRATION, annotationsComplete=false. Não se transformaram
arquivos usados para escolher o modelo em avaliação independente. Recall,
precisão e falsos alertas/hora continuam null; o alerta da avaliação é
inconclusivo para essas métricas, embora o percurso de engenharia e a postura
tenham sido conferidos. Não houve queda física ou necessidade de socorro
comprovada. Deitar voluntariamente pode atender à regra de postura e continua
sendo confundidor de necessidade de assistência.

Os **226 testes Python finais** passaram sem skip com RADAR_TEST_GUI=1. Incluem
139 anteriores, motor/SQLite/transporte/avaliação e novos testes de seleção/hash
Lite/Full, fingerprint/versões, métricas, prévia e pausa/pacing. **124 testes API**
passaram em PostgreSQL exclusivo, removido ao final. **87 contratos TypeScript
e 87 Python** aprovados (os 87 Python já fazem parte dos 226). Ruff, ESLint,
Prettier, typecheck e wheel/sdist aprovados. Não se somam suítes sobrepostas para
inflar cobertura. As correções finais de pausa executaram novamente a suíte
Python e build; mudanças posteriores somente documentais tiveram checks próprios.

Checagem final: 41 arquivos candidatos, dois tokens privados comparados sem
ocorrência, nenhum link local quebrado, lockfiles intactos, wheel com 24 arquivos
sem mídia/pesos/SQLite. `uv sync --frozen` conferiu 42 pacotes; check:edge importou
MediaPipe/OpenCV/Tasks e confirmou um único fornecedor cv2. Fila validada com um
DELIVERED e zero erros; só PostgreSQL da demonstração permaneceu em Docker,
saudável. A última expressão de rodapé apontada pelo Ruff foi formatada e o
lint final passou, sem mudança de comportamento.

Um teste intermediário consultava versões no resumo reduzido de eventos e falhou;
foi corrigido para conferir o payload persistido no SQLite. Não se alterou a
implementação para satisfazer uma expectativa errada. A normalização automática
de next-env.d.ts pelo typegen foi revertida ao conteúdo de desenvolvimento
anterior, sem mudança funcional de frontend.

**Conclusão da etapa:** o critério de demonstração real foi satisfeito. Isso não
torna a estimação infalível nem resolve todas as projeções; os resultados
desfavoráveis continuam publicados neste relatório. A etapa 06 não foi iniciada.
