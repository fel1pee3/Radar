# Evolução do detector — classificador e decisão temporal

24/10/2026. **PARCIAL: candidato executável, MVP funcional não aprovado.**
[Instrumentação/baseline](EVOLUCAO_DETECTOR_01.md) ·
[Escopo](../EVOLUCAO_DO_DETECTOR.md) · [Uso](../USO_DETECTOR_EXPERIMENTAL.md).
08/D50/D51 e suas perdas permanecem históricos; não foi iniciada a etapa 09.

## Ambiente e identidade

Windows 11 Pro 10.0.26200 x64, PowerShell 5.1, Ryzen 5 5625U (6 núcleos/12
threads), aproximadamente 15,4 GiB RAM. Node 24.22.1, pnpm 10.34.7, Python
3.12.15, uv 0.13.4. MediaPipe 1.1.1, OpenCV contrib 5.0.0.93, ONNX Runtime
1.23.2 preservados. PostgreSQL 17.11 local saudável. Sem troca de dependências
ou lockfiles. Nenhuma câmera física aberta nesta rodada.

Baseline limpa 0778e028156bf40ec7ac158ebefdc20010efc041 arquivada antes das
alterações, com configurações/calibrações/modelo/inventário de 41 vídeos atuais.
RTMO-s SHA d0703d40d19f3921da51ae725402d5fdae4d2478c7442072d3101bd396f370d8
mantido. Material privado em `.local/detector-evolution/`; pesos/vídeos nunca
entram no Git. Aliases históricos recuperados não substituem os arquivos atuais.

## Código entregue

- `posture.py`/`posture_training.py`: classificador linear opt-in com artefato
  JSON privado, SHA, instalação, calibração e modelo correspondentes. Sem pickle,
  rede ou ajuste durante execução. CLI posture-train e posture-check.
- `evidence_engine.py`, policy e EventRuntime: persistência, histerese,
  desconhecido sem evidência positiva, recuperação e janelas novas ao pausar/
  reconectar. Episódio ativo preservado; nova política e worker edge-posture-v1.
- `decision_trace.py`, config, pipeline e live: diagnóstico limitado compartilhado,
  qualidade/atributos/contexto, classe, temporal antes/depois, resets/supressões,
  captura indisponível separada. Sete dias, 10000 registros, 10 MiB por execução e
  50 MiB por raiz por padrão; truncamento explícito. Sem imagens automáticas;
  evidence none também redige coordenadas/atributos posicionais.
- `evaluation.py`: todos os alvos no resultado principal, inclusive inelegíveis
  ou excluídos. Latência desde início anotado, prazo de 5000 ms e negativos
  inconclusivos com cobertura insuficiente. Empty scene exige anotação explícita
  e captura saudável, não pose inventada. Preflight impede reavaliar material/
  grupos consultados como reserva final. Matching histórico fica secundário.
- Contratos heartbeat/types/fixtures, health e UI: motivos de pose/observação/
  contexto insuficientes chegam ao painel como execução degradada, em português.
  Evento, deduplicação, armazenamento e revisão preservados. Preview mede
  atualizações de observação, sem confundir com aquisição ou FPS do monitor.
- Testes novos: quotas/TTL/privacidade, falha após checkpoint, retomada/deduplicação,
  histerese/lacunas/recuperação/transição, contexto/hash, treino/divisões e denominador.

## Dados e método

Treino somente CAUCAFall V4, CC BY 4.0 declarada na
[fonte dos autores](https://data.mendeley.com/datasets/7w7fccy7ky/4): José Camilo
Eraso, Elena Muñoz, Mariela Muñoz e Jesús Pinto. Uso local de atributos derivados;
sem redistribuir mídia ou retreinar RTMO. Licenciamento experimental do RTMO
continua sem alegação de liberação comercial. GMDCSA24 não entrou no treino:
MIT de software não foi presumida como autorização específica de toda a mídia.

Os 12 CAUCAFall são desenvolvimento/seleção desta versão. Treino: seis clipes
S5/S7, 310 observações elegíveis com intervalos de chão previamente confirmados.
Seleção: seis S9/S10. Divisão por participante, sem quadros aleatórios entre
treino/teste. Mesmo cômodo/câmera, sessões desconhecidas; não alegar independência
por sessão. Anotações binárias não foram inventadas como rótulos multiclasse.

Doze ajustes de descritor/regularização comparados. As primeiras alternativas
detectavam S9 mas perdiam S10. Escolhido symmetric-body-context-35-v1:
coordenadas corporais simétricas normalizadas, relações de comprimentos,
cossenos articulares e contexto 2D. Logística NumPy, 3000 passos, taxa 0,05,
L2 0,01, balanceamento por classe/vídeo, padronização somente no treino. Guardas
de anotação 500 ms e 1000 ms antes do início. Deitado ≥0,8, outra postura ≤0,2,
intervalo desconhecido; scores não são probabilidades calibradas.

Artefato posture-cauca-symmetric-v1, SHA
**154196a21b4c567f1bc1d3654f7a9527b20dc222a213b66ecf3803da3dc7ed04**.
Reproduzido em destino novo com bytes/hash idênticos. Restrito à instalação
CAUCAFall-room-camera03, geometria e calibrações confirmadas. Não valida o cômodo
do fundador. Modelo principal binário; subtipos conservadores em pé/ajoelhado e
sentado com apoio confirmado não têm acurácia multiclasse medida. Pose isolada
pode não distinguir cadeira/agachamento/rede; áreas ambíguas devem ser excluídas
ou reenquadradas, sem alegar altura/contato físico pelo polígono.

## Comparação real FILE

**Resultado principal consolidado do inventário conhecido: três de sete cenas
positivas com alerta na baseline, quatro de sete no candidato; três perdas
continuam.** São os quatro alvos CAUCAFall abaixo e as três cenas históricas
floor03/05/07. Os inícios destas três continuam provisórios: isso é um inventário
de regressão, não estimativa de recall/latência global. Contexto não suportado
conta como falha em observar a cena, sem removê-la. A possível perda LIVE
permanece inconclusiva separadamente, sem informação temporal/ROI suficiente para
tratá-la como episódio formal ou acerto. Ledger privado
candidate-01/consolidated-regressions.json preserva os sete SHA distintos.

RTMO real e SQLite, 722 análises por rodada, mesmos arquivos/pisos, filas novas,
sem HTTP ou prévia. Protocolo registrado antes das previsões do worker integrado.
A seleção já foi consultada: **não é avaliação independente do novo candidato**.

| Alvo | Latência baseline | Latência candidato |
| --- | --- | --- |
| FallSittingS5 | 1000 ms | 1400 ms |
| FallBackwardsS7 | 1800 ms | 1400 ms |
| FallLeftS9 | Perda | 3800 ms |
| FallLeftS10 | 4000 ms | 4000 ms |

**3/4 → 4/4 alvos**, quatro dentro de 5000 ms; zero duplicações. S5 ficou
400 ms mais lento. Todos os alvos continuam no denominador. Zero alertas nos
oito negativos, mas apenas cauca-05/06/07 passam observação ≥80%; cinco são
inconclusivos, também na baseline. Cobertura decisória do candidato nos demais:
cauca-08 51,7%; 09 67,2%; 10 52,8%; 11 68,6%; 12 32,3%. Não contar silêncio
nesses cinco como acerto. S9/S10 também têm cobertura global abaixo de 80%
(51,0%/69,2%), apesar da emissão no prazo; conjunto não tem aceite integral.

Foram quatro PERSON_ON_FLOOR, sem prova de acurácia de POSSIBLE_FALL. A nova
exigência de sequência em pé/descida tem testes sintéticos; transição real
controlada ainda precisa de validação específica.

112,584 s de parede nos 12 arquivos, 436,203 s de CPU acumulada, inferência média
ponderada 134,782 ms e classificação 0,229 ms/análise; pico de memória do processo
251.281.408 bytes. Tempo total inclui setup/decodificação/SQLite/diagnóstico;
não é comparação controlada com outra sessão nem garantia LIVE. Preview
desligado: zero atualizações exibidas, sem FPS de monitor estimado.

Baseline-traces-pointer.json e candidate-01/integrated-pointer.json apontam
relatórios/configs/filas/resultados em `.local/detector-evolution/`. Candidato:
758 registros de decisão/status completos, sem truncamento ou imagem gravada.

## Perdas e experimentos adicionais

S9 baseline: 36/37 observações elegíveis no alvo, quadril dentro nas elegíveis,
ângulo aproximadamente 26–42° e aspecto incompatíveis com gates antigos. Novo
descritor reconheceu a perspectiva sem reduzir esses gates.

floor03/05/07 são, por SHA, intake08-02/05/08. Seis sequências armazenadas foram
reprocessadas com runtime/diagnóstico novo, Full e RTMO; não é nova inferência.
Full mantém perdas de qualidade. RTMO recupera a pose, mas o quadril fica fora
da região em 29/30, 28/28 e 22/22 observações elegíveis de todo o clipe,
respectivamente. **Três perdas ainda não resolvidas.** Score deitado alto em
experimento fora do escopo não resolve contexto nem autoriza transportar modelo.
Polígonos não foram ampliados para disparar. Timelines CSV/JSONL no ponteiro
legacy-traces-pointer.json, com hashes de entrada e identidade da fonte.

Auditadas 20 sequências RTMO já armazenadas: duas cadeiras sem evento, perdas
preservadas e demais emissões registradas. Sem anotação completa, alertas adicionais
não foram declarados acertos ou falsos positivos.

Experimento real de detecção de pessoa 0,7/0,5, mesmos pesos, qualidade articular
≥0,5 e classificador congelado: ambos 4/4 alvos e zero alertas/duplicações nos
oito negativos. 0,5 tornou conclusivo mais um negativo e antecipou S10 em 1200 ms;
quatro negativos continuaram inconclusivos. Não adotado: faltam cobertura e
ambiente vazio/apoios para justificar mudança. Worker permanece 0,7. Protocolo
e resultados em detection-confidence-01; sem mudança de pesos/estimador.

Trecho LIVE histórico no chão sem alerta continua possível perda/inconclusivo.
Não há observações brutas suficientes para atribuir a causa retrospectivamente.
Nenhuma nova aprovação física inferida dos testes de arquivo/sintéticos.

## Comandos executados

Na raiz após `. ./scripts/activate.ps1`. Scripts/dados/logs privados em
`.local/detector-evolution/`. Sem commit, push ou deploy.

| Comando | Resultado |
| --- | --- |
| `python .local/prepare-detector-baseline.py` via uv frozen/offline | Exit 0; baseline/41 vídeos arquivados |
| `python .local/detector-evolution/run-baseline-traces.py` via uv | Exit 0; 12 arquivos reais, 3/4 reproduzido |
| `python .local/detector-evolution/compare-posture-prototypes.py` e variante `compare-posture-prototypes-v2.py` via uv | Exit 0; 12 ajustes, resultados preservados |
| `python .local/detector-evolution/audit-selection-regressions.py` via uv | Exit 0; 20 sequências armazenadas |
| `python .local/detector-evolution/trace-legacy-losses.py` via uv | Exit 0; seis timelines/diagnósticos Full/RTMO |
| `uv run --offline --project services/edge --frozen radar-edge posture-train --manifest .local/detector-evolution/candidate-01/training-manifest.json --output .local/detector-evolution/candidate-01/posture.json` | Exit 0; 310 observações |
| Mesmo comando com destino `posture-reproduced.json` | Exit 0; bytes/SHA idênticos |
| `python .local/detector-evolution/run-candidate-files.py` via uv | Exit 0; 12 arquivos reais e quatro eventos persistidos |
| `python .local/detector-evolution/compare-detection-confidence.py` via uv | Exit 0; comparação 0,7/0,5, worker preservado |
| `uv run --offline --project services/edge --frozen ruff check services/edge` e `ruff format` | Lint/imports/formatação corrigidos e aprovados |
| `uv run --offline --project services/edge --frozen pytest services/edge/tests -q`, RADAR_TEST_GUI=1 | 344 passed em 18,61 s na revisão final, sem pulos; GUI artificial não é webcam |
| `pnpm.cmd --filter @radar/contracts types:generate` e `pnpm.cmd --filter @radar/contracts test` | Tipos atualizados e 104 testes TS/AJV aprovados |
| `pnpm.cmd typecheck` | Exit 0, três pacotes |
| `pnpm.cmd test:api` | Exit 0, 159 testes, banco isolado, demonstração preservada |
| `pnpm.cmd build` | Exit 0, contratos/API/Next compilados |
| `pnpm.cmd lint` | Exit 0, ESLint e Prettier |
| `pnpm.cmd test:e2e` | Exit 0, 20 testes desktop/mobile, recursos isolados removidos |
| `uv run --offline --project services/edge --frozen radar-edge posture-check --config .local/detector-evolution/candidate-01/demo-file.yaml` | Exit 0; hashes/contexto válidos, fonte/banco não abertos |
| `python .local/detector-evolution/verify-current-replay.py` via uv | 24 sequências armazenadas, fingerprints e emissões iguais aos ensaios congelados; sem nova inferência |
| `node .local/detector-evolution/validate-native-events.mjs` | Exit 0, quatro envelopes nativos no validador TS/AJV, além da validação Python na emissão |
| `python .local/detector-evolution/check-demo-cli.py` via uv | Exit 0; CLI real em cópia de configuração com fila nova, S9 aos 6800 ms, sem imagem/HTTP/webcam |
| `python .local/detector-evolution/check-reserved-guard.py` via uv | Exit 0 no verificador; CLI recusou os vídeos conhecidos como reserva com FINAL_EVALUATION_LEAKAGE e exit 1 esperado, sem inferência |
| `python .local/detector-evolution/consolidate-regressions.py` via uv | Exit 0; sete cenas positivas conhecidas, três perdas preservadas no resultado consolidado |
| `python .local/detector-evolution/freeze-candidate.py` via uv | Exit 0; fonte/artefato/configurações/métricas arquivados privadamente; sem congelar traces brutos para contornar TTL |
| `pnpm.cmd exec node .local/detector-evolution/native-http-runner.mjs` | Exit 0; quatro eventos reais → quatro incidentes, reenvios 200 sem duplicar, quatro avisos locais SIMULATED; revisão por ator de teste, não humano |
| `docker compose --env-file .env -f infra/compose.yaml ps` | PostgreSQL saudável, somente 127.0.0.1:15432 |

Forma completa dos helpers: `uv run --offline --project services/edge --frozen`
antes de cada comando Python da tabela. Tentativas de helpers interrompidas por
PATH sem ativação e identificador de instalação inválido foram corrigidas; não
contam como ensaios aprovados. O helper HTTP também precisou de correções de
inicialização do pnpm e da fixture Camera/Device, sem alteração do produto.
As verificações finais listadas passaram. Não foram repetidos backup/restore e
instalação limpa nesta evolução: não houve migração/dependência nova; suas provas
históricas não são apresentadas como execução nova. Arquivos gerados pelo Next
foram restaurados ao estado anterior depois dos testes.

## Integração nativa isolada

Os quatro envelopes emitidos a partir das observações RTMO reais preservaram
pose/sinais/versões ao passar por HTTP/Prisma/PostgreSQL. Criado banco descartável,
com credenciais/câmera de teste, sem tocar banco/volume da demonstração. Primeiro
envio 201, reenvio idêntico 200, quatro recibos e quatro incidentes. O executor
registrou quatro avisos de canal SIMULATED, não urgentes por serem REPLAY/TEST.
Endpoint de revisão exercitado com ator automatizado e nota explícita de teste.
Isso comprova o caminho técnico; **não é revisão humana do fundador**, conferência
visual de postura ou aviso externo. Resultado em native-http-result.json, logs
privados, container/volume exclusivos removidos.

## Pendências e condições de avanço

Referência experimental congelada: fonte executável de 188 arquivos, SHA
**1b4d9af845500734efedd5afe96b6ac56b0bd4b1fdd5f19f27bd318b777eefb8**, HEAD
0778e02 com alterações intencionais sem commit. Ponteiro
`.local/detector-evolution/candidate-01/freeze-pointer.json`: ZIP de fonte,
hashes do modelo/artefato, configurações e relatórios agregados. Não equivale a
selecionar/aprovar um candidato final do cômodo do fundador. A coleta e seleção
desse cômodo continuam pendentes; congelar sua referência antes da futura reserva.

Faltam dados novos do cômodo, anotações/aceite em três orientações e transição
segura, cadeira/rede/ajoelhar/pegar objeto, vazio/perda de observação, conjunto
reservado de quatro alvos e oito negativos e sessão física iniciada pelo fundador.
Incluem conferência pelo fundador da entrega, incidente, revisão humana, aviso
e não duplicação na nova demonstração. Rodada de comparação usa filas locais com
HTTP desligado; integração técnica com envelopes reais passou em banco isolado.
Nenhum desses
critérios foi dispensado para aprovar a evolução.

O fundador preparará gravações depois e autorizou continuar código/testes. Sessões
inteiras distintas permitem repetir a mesma pessoa, declarando limites; não
inventar independência entre recortes. Roteiro preparado, sem abrir webcam,
repetir apresentação dispensada ou exigir os 30 minutos históricos.

Aviso existente é atualização visual/lista e canal SIMULATED em Avisos locais.
Não é mensagem externa. Conferência de como chama atenção do operador fica na
nova demonstração; nenhum aviso ao celular foi implementado/testado.
