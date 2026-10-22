# Etapa 05 — Motor temporal e eventos de visão

Data: 21/10/2026. Status: **CONCLUÍDA no escopo da bancada**.
Base: `main`, `fed37f2`; árvore limpa no início. Commit/push autorizados pelo
fundador após a validação. Sem deploy.

## Resultado entregue

Pipeline de arquivo → poses → features → motor temporal → episódio/outbox SQLite
→ entrega HTTP local. O simulador permanece separado. O motor usa tempo da mídia,
sem depender de OpenCV, HTTP, SQLite ou relógio civil. O painel existente já
apresenta REPLAY, sinais, versões e ausência/presença de evidência corporal.

Após investigação autorizada pelo fundador, o Full oficial foi comparado ao Lite
e integrado como opção explícita, mantendo a política e os gates. O arquivo
`piso-f-07` gerou PERSON_ON_FLOOR aos 6000 ms; SQLite/HTTP criaram um incidente
REPLAY/TEST. O fundador confirmou prévia melhorada e sinais/versões/pose no painel.
Retomada EOF e reenvio preservaram o mesmo evento/incidente. **226 testes Python,
124 API e 87 contratos TS aprovados.** Métodos, fontes oficiais, comparação e
evidências na [investigação](INVESTIGACAO_ETAPA_05.md).

Os ensaios anteriores estão preservados abaixo como histórico da fase parcial.
O vídeo original e mais cinco arquivos descritos como filmagens reais pelo
fundador foram executados inicialmente com Lite
com modelo e calibrações reais: todos terminaram normalmente, mas **nenhum gerou
evento**. No lateral houve 6 observações candidatas sem continuidade suficiente;
na vista de cima não houve observação geometricamente elegível. Na quarta
filmagem, `piso-d`, houve 58 observações elegíveis com quadril dentro do piso,
mas ângulo/proporção em 2D excluíram todas. O fundador confirmou pessoa deitada e
orientação correta na prévia: é uma falha observada de detecção nessa cena.
Dois ensaios posteriores também não geraram evento, por qualidade insuficiente
dos pontos e ausência de janela candidata sustentada. Não há anotação temporal
completa para estimar taxas de eficácia. A demonstração positiva
obrigatória por vídeo/modelo e sua conferência no painel ainda estavam pendentes
nesse momento; foram satisfeitas pelo ensaio Full registrado acima.
Teste sintético de integração comprovou persistência/transporte/idempotência;
não substitui essa demonstração real.

Outro arquivo, confirmado pelo fundador como **gerado por IA**, produziu
PERSON_ON_FLOOR pelo modelo/motor e persistiu um evento local em SQLite. Foi
registrado como material SYNTHETIC, sem entrega HTTP; não substitui a prova
positiva com filmagem de pessoa real.

## Ambiente e arquivos

Windows 11 Pro 10.0.26200 x64; PowerShell 5.1; Ryzen 5 5625U, 6 núcleos/12 threads,
15,4 GiB RAM. Node 24.22.1, pnpm 10.34.7, Python nativo 3.12.15, uv 0.13.4.
MediaPipe 1.1.1, único fornecedor cv2: opencv-contrib-python 5.0.0.93; HTTPX 0.28.1.
Não houve nova dependência, alteração de família ou mudança nos lockfiles.
SQLite usa o módulo nativo do Python. Nenhuma câmera física foi aberta.

| Área | Arquivos / resultado |
| --- | --- |
| Política | services/edge/src/radar_edge/policy.py: defaults centralizados e versão explícita; mudar parâmetro mantendo floor-v0.1 é rejeitado |
| Modelo e observabilidade | model.py/config.py/estimator.py: Lite/Full explícitos e SHA correto em evento/fingerprint; metrics.py: diagnósticos agregados por articulação; preview.py: presença/visibilidade alinhadas e início pausado opcional |
| Features e gates | features.py: geometria em pixels, piso normalizado, motivos de inelegibilidade, baixa luz/FPS, lacuna e congelamento por tempo da mídia |
| Núcleo puro | engine.py: OBSERVING/SUSPECTED/ACTIVE/REARMING, cobertura ponderada, trajetória e um evento por episódio |
| Persistência | outbox.py: esquema SQLite v1, WAL/FULL, transações, payload imutável, episódios, checkpoints, resets auditados e estados de entrega |
| Integração | event_runtime.py: envelope compartilhado validado, ancoragem virtual UTC, fingerprint da configuração, locks e métricas agregadas |
| HTTP | delivery.py: cliente loopback, timeout, ACK validado, retries com backoff e suspensão por autenticação |
| CLI/pipeline | cli.py, config.py, observations.py, pipeline.py: events explícito, warm-up na retomada, evaluate/deliver/outbox-status/reset-episode; env/doctor/calibrate preservados |
| Avaliação | evaluation.py, evaluation.example.json: manifesto privado validado, execuções isoladas sem HTTP, correspondência por episódio e denominador zero null |
| Testes | tests/test_temporal.py, test_outbox_delivery.py, test_temporal_pipeline.py, test_evaluation.py e helpers sintéticos; pytest.ini na raiz |
| Integração real | apps/api/test/edge.test.mjs e scripts/test-api.mjs: Python + SQLite + Nest + PostgreSQL em container exclusivo |
| Documentação | STATUS, decisões, ambiente/comandos, inventário, README central/edge, roteiro 05 e este relatório |

API, schemas compartilhados, banco relacional e código do painel não exigiram
alteração funcional. Proprietário, credenciais, cadastros, vídeo, calibração
anterior e volume PostgreSQL preservados. Porta 5432 do host não foi utilizada.

## Decisões e comportamento

- Defaults de docs/04 preservados: 60°, razão altura/largura ≤1, quadril no piso,
  persistência de 2000 ms, fração válida ≥0,8, pelo menos 5 observações válidas,
  lacuna máxima 500 ms; trajetória anterior de 1000 ms e descida ≥0,18 da altura;
  rearmamento após 3000 ms válidos fora da postura. Nenhum limiar foi reduzido
  para o vídeo disparar.
- Ângulo usa `(x * largura, y * altura)`; bbox usa pontos corporais suficientes.
  Ausência, baixa qualidade, corpo cortado, pontos essenciais ausentes/fora da
  imagem, bbox/eixo degenerados e múltiplas poses impedem elegibilidade.
- Cobertura é a soma de intervalos entre dois extremos válidos candidatos,
  limitada aos últimos 2000 ms e sem atravessar lacunas >500 ms. Intervalo com
  extremo inválido não recebe crédito. A primeira candidatura fornece o início
  estimado; postura contrária ou continuidade perdida reinicia a suspeita.
- PERSON_ON_FLOOR é o resultado sem trajetória suficiente. POSSIBLE_FALL exige
  descida observada antes da candidatura e persistência completa no piso. A
  continuidade é operacional: uma pose suficiente, sem lacuna/configuração
  alterada; não há reconhecimento de identidade nem garantia contra troca de
  pessoas sem oclusão detectada.
- Em ACTIVE, qualidade insuficiente não fecha episódio. Rearmamento exige
  intervalos consecutivos válidos fora da postura; invalidez/lacuna reinicia sua
  contagem. Fechar episódio local não encerra o incidente humano na API.
- Gates técnicos: baixa luz <25 por 2 s; taxa <2 análises/s por janela de 5 s;
  lacuna de frame >2 s; frames processados byte a byte idênticos por 10 s. Hash
  de imagem é atualizado em **todos os frames decodificados**, inclusive os
  pulados por amostragem. Essas heurísticas podem marcar cena estática legítima;
  não comprovam obstrução nem doença. Aquecimento/final não inventam tempo coberto.
- `events.enabled` é false por padrão para preservar as configurações da 04.
  A cópia privada `.local/edge-events.yaml` habilita o motor e referencia a
  credencial existente da câmera, sem duplicar ou imprimir seu token. `--poses-only`
  permite manter apenas o percurso da 04.
- SQLite persiste episódio, envelope e checkpoint na mesma transação antes do
  primeiro HTTP. Falha interrompe processamento com STORAGE_ERROR. Locks de
  processo por câmera (inclusive entre outboxes diferentes) e por arquivo SQLite
  impedem execuções concorrentes incompatíveis. O SO libera locks ao fechar/morrer
  o processo; arquivos de lock vazios/pequenos não são prova de processo ativo.
- Retomada normal mantém runId, âncora UTC, payload/eventId/episodeId e checkpoint.
  diagnosticReportId identifica cada relatório, sem trocar a identidade da execução.
  Decode desde o início aquece o rastreador VIDEO, mas não repete decisões,
  exportações ou contagem de rearmamento até o checkpoint. ACTIVE/REARMING volta
  como ACTIVE; suspeitas ainda não emitidas precisam de nova janela completa.
  Arquivo já concluído apenas permite escoar pendências, sem reanalisar a cena.
- Hash de fonte, conteúdo da calibração, política, modelo/worker, dimensões,
  amostragem e modo de evidência identificam a execução. Mudança exige parar e
  `reset-episode --reason ...`, preservando histórico e pendências. Uma avaliação
  intencional usa outra outbox isolada; não se confunde com retomada normal.
- `sourceOffsetMs` identifica o frame da emissão/evidência. occurredAt deriva
  do início candidato; detectedAt da emissão, ambos em relógio virtual ancorado
  a UTC ao criar a execução. Não representam data de gravação. REPLAY é enviado
  sem deliveryClass; a API define TEST, sem urgência.
- EVIDENCE_MODE none omite pose; skeleton envia apenas índices corporais 11–32
  disponíveis do instante de emissão. Sem frame, imagem, vídeo, pontos faciais,
  worldLandmarks ou fluxo contínuo. Snapshot é rejeitado nesta etapa.
- ACK exige eventId correspondente, incidentId UUID, receivedAt válido, duplicate
  coerente com 200/201 e deliveryClass TEST. Rede/408/429/5xx ou ACK inválido deixam
  PENDING com backoff exponencial de 1–60 s; Retry-After numérico pode elevar até
  300 s. 401/403 suspende toda entrega até `deliver --resume-auth` explícito após
  corrigir credencial. Demais erros, inclusive 409/410/422, viram PERMANENT_ERROR.
  Não se copiam corpos de erro/token para logs. Não há retry infinito de erro
  permanente. `outbox-status` mostra contagens, códigos e até 100 confirmações.
- Histórico/itens confirmados permanecem locais nesta etapa; retenção automática
  pertence à 07. Pendentes nunca são apagados silenciosamente.

## Comandos e verificações realmente executados

Todos a partir da raiz, ativando `. ./scripts/activate.ps1` em cada terminal.

| Comando/ação | Resultado e limite |
| --- | --- |
| Leitura de AGENTS/README/status/etapa/referências/anexo/relatório04; git status/rg --files | Base limpa fed37f2, pipeline de poses presente, motor/outbox ainda ausentes |
| node --version, pnpm.cmd --version, uv --version, CIM SO/CPU, docker ps | Versões acima; somente radar-postgres-1 saudável, sem alteração de 5432 |
| Inspeção privada dos campos/configuração e existência da mídia/calibração | Vídeo real disponível no caminho efetivo configurado; não se presumiu teste.mp4; nenhum segredo impresso |
| Consultas à documentação oficial Python sqlite3, SQLite e HTTPX | Controle explícito de transação/commit e timeouts; referências abaixo |
| `uv run --project services/edge --frozen ruff check services/edge --fix`; `ruff format services/edge` | Imports/formatação corrigidos; lint/format final aprovados |
| `$env:RADAR_TEST_GUI='1'`; `uv run --project services/edge --frozen pytest -q` | **185 aprovados**, nenhum skip: 139 anteriores e 46 novos/parametrizados; descoberta pela raiz verificada |
| `pnpm.cmd test:api` | **124 aprovados**: 19 acesso +104 eventos +1 integração Python real; duas migrações aplicadas em PostgreSQL exclusivo; container/volume de teste removidos |
| `pnpm.cmd test:contracts` | **87 TS e 87 Python aprovados**, tipos compartilhados conferidos |
| `pnpm.cmd lint`; `pnpm.cmd lint:edge`; `pnpm.cmd check:edge` | ESLint/Prettier e Ruff aprovados; imports MediaPipe/OpenCV preservados |
| `uv sync --project services/edge --frozen`; `uv build --project services/edge` | 42 pacotes conferidos, wheel/sdist reais gerados e ignorados; lock sem alterações |
| `radar-edge run --config .local/edge-events.yaml --no-preview` via uv frozen | Arquivo real completo, zero eventos; resultados abaixo. Primeira execução de desenvolvimento também foi negativa e seu histórico foi preservado |
| `radar-edge reset-episode --config .local/edge-events.yaml --reason stage05_validation_after_checks` via uv frozen | Reset explícito após checks, com motivo e histórico; nenhum incidente humano foi fechado |
| Repetição do run completo, depois repetição normal do mesmo comando | ENDED com 89 observações; retomada de EOF reconheceu checkpoint 528, mesmo runId e zero novas observações/eventos |
| `uv run --project services/edge --frozen radar-edge evaluate --manifest .local/evaluation.json` | Nova execução intencional isolada, sem HTTP; zero eventos; métricas de eficácia null por ausência de anotações completas |
| Mesmo evaluate com `--replay-speed 2` | ENDED; mesmos 89 frames/timestamps e digest da sequência, zero eventos; medidas abaixo |
| `radar-edge doctor`, `outbox-status` e `deliver` com .local/edge-events.yaml via uv frozen | Doctor executou modelo real; outbox vazia, nenhum envio de evento real possível nessa cena |
| Diagnóstico GET /v1/edge/me com a credencial existente, sem imprimir bearer | API da demonstração estava parada; processo próprio iniciado sem janela para conferir health/ready e credencial: 200, câmera correspondente. Processo próprio encerrado após o diagnóstico; nenhum processo do fundador parado |
| git diff --check, links locais, comparação com valores privados, git check-ignore e inspeção do wheel | Sem erro de whitespace ou link quebrado; 31 arquivos candidatos conferidos contra quatro valores privados sem ocorrência. Lockfiles preservados; wheel com 24 arquivos, sem mídia/modelo/SQLite. Somente radar-postgres-1 permanece saudável; nenhum container de teste restante |

O teste de integração Python usa **observações sintéticas**, explicitamente
identificadas: o motor gera PERSON_ON_FLOOR, grava SQLite, a API real confirma
commit, o cliente perde esse ACK por falha injetada, reabre SQLite e reenvia o
mesmo envelope. Resultado: um recibo, um incidente REPLAY/TEST, ACK duplicate=true,
um aviso local não urgente. Isso é evidência de engenharia, não de visão real.

Testes do pipeline com decoder real e estimador controlado também interrompem em
4 s e 6,2 s, restauram ACTIVE, reiniciam rearmamento, aquecem prefixo sem decisões,
detectam nova situação após recuperação válida e mantêm EOF sem duplicação.
Testes de falha do SQLite verificam rollback de episódio/outbox/checkpoint e
interrupção visível. Cobertura temporal e taxas 2/2,5/4/5/10 Hz são determinísticas.

Houve uma falha intermediária no teste de avaliação: a segunda transição sintética
era uma descida rápida válida, mas a anotação esperava PERSON_ON_FLOOR. Corrigida
a fixture para POSSIBLE_FALL, sem alterar gates. Primeiras passagens de lint
apontaram imports/linhas longas, corrigidos. O arquivo redirecionado pelo PowerShell
5.1 era UTF-16; leitura diagnóstica foi corrigida para esse encoding. Os relatórios
gravados pelo programa são UTF-8. Não se apagaram falhas de histórico.

## Processamento real inicial — histórico da fase parcial

Vídeo `bancada-01`, SHA-256
`3c361aee3f49e2e6ac2688e3afb53622ffd15451ead69874b3e0a76c9cd090c0`.
Arquivo fornecido/autorizado pelo fundador para uso local; origem independente e
redistribuição não foram aprovadas. Pseudônimos e retenção manual da 04 preservados.
530 frames, 1920×1080, ~29,97003 fps, ~17,684 s, processamento 640×360, rotação 0.

Modelo `pose-landmarker-lite-float16-v1`, CPU/VIDEO, num_poses=2, máscaras false,
SHA-256 `59929e1d1ee95287735ddd833b19cf4ac46d29bc7afddbbf6753c459690d574a`.
Calibração do fundador `1140706f-b0e0-4edb-b5a1-9ad60e8e4453-v1`, sem edição dos
9 vértices. Política floor-v0.1, worker edge-temporal-v1, evidence skeleton.

| Medida | Sem espera, outbox principal | Avaliação isolada 2× |
| --- | --- | --- |
| Fim | ENDED | ENDED |
| Lidos/analisados/pulados | 530 /89 /441 | 530 /89 /441 |
| Pose suficiente/baixa qualidade | 84 /5 | 84 /5 |
| Candidatas/eventos | **0 /0** | **0 /0** |
| Taxa por segundo da mídia | 4,9949 | 4,9949 |
| Inferência média | 24,4833 ms | 25,4403 ms |
| Parede total no pipeline | 8,1839 s | 10,1581 s |
| Throughput | 10,8751 análises/s | 8,7615 análises/s |
| CPU do processo, um núcleo=100% | 198,94% | 147,20% |
| Pico working set | 331.632.640 bytes | 327.524.352 bytes |

Todas as 84 observações geometricamente elegíveis ficaram fora dos gates de
quadril no piso, ângulo horizontal e bbox horizontal. As outras 5 têm baixa
qualidade/essenciais insuficientes. Não se inferiu qual atividade humana estava
sendo feita a partir desses agregados. Há 15.816 ms de intervalos elegíveis em
17.618 ms observados; os 66 ms finais até a duração estimada não são inventados
como cobertura. Não houve NO_POSE, múltiplas poses ou fallback de timestamps.

Digest de amostragem idêntico entre velocidades:
`d53fcfe0809b5bf04af3ac8e87708e3e376c9797971e6939e848e33a996cc53e`.
Relatórios privados: `.local/results/edge/eca6e6de-d01d-4918-86a3-b8a7cc60e321/report.json`
e `.local/results/edge/9d906cfb-55f3-4db2-a442-179a7709ad47/report.json`.
Retomada EOF: `.local/results/edge/c5c87d55-2050-411a-9961-6a957a97f7ac/report.json`.
Avaliação 2×: `.local/evaluation/e80adbda-4f05-475f-9518-4aef2d630bb6/evaluation.json`.

Métodos de CPU/RAM/parede/inferência iguais aos explicitados na etapa 04: tempo
de processo inclui threads nativas, pode ultrapassar 100%; pico de memória é do
processo inteiro. Parede inclui setup/decode/modelo/SQLite/pacing/cleanup, antes de
gravar JSON. Números deste notebook/arquivo não são promessa de tempo real.

## Dois vídeos adicionais — vista lateral e vista de cima

O fundador forneceu dois arquivos na pasta reservada e descreveu uma mulher
deitando, vista lateral, e outra já deitada, vista de cima. Autorização para
processamento local registrada nos manifestos privados; origem independente,
publicação e treinamento não foram autorizados. Nomes originais e mídia não foram
incluídos no Git. Papel CALIBRATION, sem anotações temporais completas e sem
relato de acidente/necessidade de assistência.

| Item | piso-a: lateral | piso-b: vista de cima |
| --- | --- | --- |
| SHA-256 | 81786b87925a23e980a58ae358914840a3ecb3ad043e66470c19e33c3d50c640 | 0f688837428a63aaeb2766a332058d33fbe06f802888ab4230a9ab3672c7ffe9 |
| Bytes / dimensão / FPS | 8.464.548 /1280×720 /60 | 5.135.538 /1366×720 /24 |
| Duração estimada / processada | 21.750 ms /640×360 | 14.625 ms /640×337 |
| Lidos / analisados / pulados | 1305 /109 /1196 | 351 /73 /278 |
| NO_POSE / LOW_CONFIDENCE / MULTIPLE_POSES / ONE_VALID_POSE | 4 /85 /14 /6 | 0 /73 /0 /0 |
| Observações candidatas / eventos | **6 /0** | **0 /0** |
| Tempo elegível / observado | 400 ms /21.600 ms | 0 ms /14.417 ms |
| Inferência média / parede / throughput | 23,7773 ms /8,6923 s /12,5399 análises/s | 22,7074 ms /5,0988 s /14,3172 análises/s |
| CPU processo (um núcleo=100%) / pico working set | 176,70% /272.793.600 bytes | 137,90% /273.006.592 bytes |
| Calibração / versão / vértices | 9597a4fe-247f-452b-96c1-1f599618479d /1 /7 | 47806063-88ed-45d3-b723-9c2759313d58 /1 /4 |
| Resultado | ENDED, estado SUSPECTED, outbox vazia | ENDED, estado OBSERVING, outbox vazia |

Os dois pisos foram marcados pelo fundador na GUI, em arquivos separados,
preservando os nove vértices da calibração da 04. Na seleção da vista de cima,
a primeira geometria foi rejeitada. Uma tentativa de processamento ficou em
CALIBRATION_REQUIRED, sem carregar o modelo ou fingir ausência de ocorrência.
Após C/limpar e nova marcação, a janela fechou, o arquivo foi salvo e a execução
completa acima foi realizada. A marcação lateral foi confirmada e salva depois.

A vista de cima apresentou pontos essenciais fora da imagem **no resultado do
modelo** e insuficientes/baixa qualidade nas 73 observações; isso não comprova
que o corpo real estivesse cortado. Na lateral, as seis observações suficientes
atenderam à geometria candidata, mas não sustentaram 2 s com cobertura ≥80%.
MULTIPLE_POSES significa duas hipóteses retornadas pelo modelo, não constatação
visual pelo agente de duas pessoas. O agente não enviou frames ao chat nem
inspecionou o conteúdo pessoal fora da janela local do fundador.

Comandos executados via `uv run --project services/edge --frozen`:

```powershell
radar-edge doctor --config .local/edge-piso-a.yaml
radar-edge doctor --config .local/edge-piso-b.yaml
radar-edge calibrate --config .local/edge-piso-b.yaml --frame-ms 1000
radar-edge run --config .local/edge-piso-b.yaml --no-preview
radar-edge calibrate --config .local/edge-piso-a.yaml --frame-ms 1000
radar-edge run --config .local/edge-piso-a.yaml --no-preview
radar-edge evaluate --manifest .local/evaluation-pisos.json
```

O processamento completo foi invocado pelo mesmo `run_pipeline` da CLI em script
Python privado para salvar JSON UTF-8 e inspecionar apenas agregados. Diagnósticos
e calibrações usaram a CLI literalmente. Os comandos run da lista também foram
executados pela CLI após esse processamento: retomaram EOF com zero observações
novas, preservando o runId e sem evento novo. Relatórios dos processamentos completos:
`.local/results/edge/7f54fd9c-6cf5-4e47-82bc-a75ee8d9ca12/report.json` (lateral) e
`.local/results/edge/44c345e2-8688-428c-bcaf-649067c99754/report.json` (vista de cima).
Evaluate reprocessou ambos em outboxes isoladas sem HTTP, confirmou zero eventos
e os mesmos tempos elegíveis. Relatório:
`.local/evaluation/eb0592a8-9fb0-427a-b7d4-f38e31e801c8/evaluation.json`.
Recall, precisão e falsos alertas/hora permanecem null, sem alvos temporalmente
anotados. Não há novo incidente a conferir no painel. A API/credencial retornaram
200 e câmera correspondente, sem alteração dos processos já ativos do fundador.

Os gates, modelo e política não foram alterados. Este é um resultado desfavorável
da baseline nestas cenas, não uma aprovação da visão nem garantia de que outra
gravação produzirá alerta. As descrições de deitar voluntariamente são
confundidores reais fornecidos pelo fundador; as demais atividades seguem sem
ensaio real. Uma próxima cena precisa permitir ao modelo observar os pontos
essenciais durante tempo suficiente; não provocar queda física.

Como hipótese para o próximo ensaio, foi solicitado um enquadramento diagonal
com corpo inteiro, cabeça e pés visíveis, em vez de oclusão lateral ou vista
diretamente de cima. Não é garantia de funcionamento. A hipótese parte dos gates
e falhas observadas; o [Model Card oficial](https://storage.googleapis.com/mediapipe-assets/Model%20Card%20BlazePose%20GHUM%203D.pdf)
também registra sensibilidade à posição/escala/orientação e degradação por
oclusão. O ângulo oblíquo específico não foi validado nesses ensaios.

## Vídeo gerado por IA — ensaio sintético adicional

O fundador confirmou que o novo arquivo foi gerado por IA no Gemini. Identificador
`piso-c-ai`, SHA-256
`22ffc2aaccb4d086da652b8919b3720a0ac3f4fe74ed5751f410f2f59fdd0318`,
3.134.134 bytes, 1280×720, 24 fps, 240 frames/10 s. Uso local autorizado;
redistribuição/treinamento e licença do material gerado não foram aprovados.
Manifesto privado identifica material SYNTHETIC, generationMethod AI_VIDEO e
qualifiesAsRealCameraVideo=false, sem pressupor que existe pessoa física filmada.

O fundador marcou 4 vértices do piso na GUI; calibração separada
`98d00698-0572-45df-bf77-c0305f0d30af-v1`, instante de 1000 ms. Configuração
`.local/edge-piso-c-ai.yaml`, SQLite `.local/etapa05/piso-c-ai.sqlite`, delivery
desabilitada neste ensaio. Fonte FILE continua usando mode REPLAY; isso descreve
a leitura do arquivo, sem converter seu conteúdo sintético em filmagem real.

Resultado completo com Tasks Lite CPU/VIDEO e política floor-v0.1 **inalterados**:

| Medida | Resultado |
| --- | --- |
| Captura / frames | ENDED; 240 lidos, 50 analisados, 190 pulados |
| Taxa por tempo da mídia | 4,9832 análises/s |
| Qualidade inicial de pose | 46 ONE_VALID_POSE, 4 LOW_CONFIDENCE; zero NO_POSE/MULTIPLE_POSES |
| Features elegíveis / candidatas | 31; outras 19 foram inelegíveis por pontos fora do quadro/corpo cortado nos resultados do modelo |
| Cobertura elegível / observada | 5624 ms /9833 ms |
| Evento | **1 PERSON_ON_FLOOR**, emissão no offset **6417 ms** |
| Sinais no instante de emissão | 2000 ms de postura, tronco 76,9687°, bbox 0,3903, quadril no piso, fração temporal válida 1, descida rápida false, taxa 5 |
| Evidência | 22 pontos corporais; nenhuma imagem ou ponto facial |
| Estado final / outbox | ACTIVE /1 PENDING, zero tentativas HTTP |
| Inferência média / parede / throughput | 22,8445 ms /3,5265 s /14,1784 análises/s |
| CPU processo (um núcleo=100%) / pico working set | 128,93% /261.554.176 bytes |

Evento `1089037a-8e71-4d43-9ff9-4303155a6d71`, episódio
`cc2a0f60-4e82-4d98-88f7-c544cfacc633`. Relatório privado:
`.local/results/edge/fa3d84c8-8491-4762-960d-0fb6499966fc/report.json`.
Esse evento nasceu de estimativa real de poses sobre frames artificiais; não
foi injetado pelo simulador de eventos. A fração temporal não mede acurácia,
probabilidade de acidente ou necessidade de assistência. Como não houve descida
observada suficiente, o rótulo não foi POSSIBLE_FALL.

Comandos efetivamente executados na raiz, com prefixo
`uv run --project services/edge --frozen`:

```powershell
radar-edge doctor --config .local/edge-piso-c-ai.yaml
radar-edge calibrate --config .local/edge-piso-c-ai.yaml --frame-ms 1000
radar-edge run --config .local/edge-piso-c-ai.yaml --no-preview
radar-edge evaluate --manifest .local/evaluation-piso-c-ai.json
```

O processamento completo foi invocado via `run_pipeline(load_config(...))` em
script Python privado para salvar agregados UTF-8. O run CLI posterior retomou
EOF/ACTIVE com zero novas observações; o mesmo eventId/episodeId ficou preservado
e a outbox continuou contendo um único evento. Sem tentativa de entrega: PENDING
representa delivery desabilitada, não uma falha da API. Nenhum incidente foi
publicado no painel a partir desse arquivo.

Evaluate reprocessou em outbox isolada, material SYNTHETIC, sem HTTP. Reproduziu
PERSON_ON_FLOOR no offset 6417 ms. Novos IDs são esperados nessa avaliação
intencional, sem duplicar a outbox operacional. Relatório:
`.local/evaluation/34b411ca-47d6-4fbf-a12d-a3dc02875eb4/evaluation.json`.
Sem anotação temporal completa, o alerta é inconclusivo para métricas: recall,
precisão e falsos alertas/hora continuam null. Não houve alteração de código ou
reexecução das suítes automatizadas neste ensaio de arquivo/configuração.

Naquela fase a etapa permaneceu PARCIAL: esse resultado ampliou a evidência de
processamento e persistência em material artificial; os ensaios Lite em arquivos
descritos como reais ainda estavam sem evento. O positivo Full foi obtido depois.

## Quarta filmagem real — postura confirmada, critérios em 2D não atendidos

O fundador confirmou que `piso-d` é filmagem de câmera/celular, autorizou o uso
local, marcou o piso e conferiu a prévia a 0,5×: **imagem orientada corretamente e
pessoa deitada no chão durante vários segundos**. Essa confirmação qualitativa
foi registrada no manifesto privado, sem inventar intervalos temporais exatos.
Material REAL_VIDEO, papel CALIBRATION, retenção manual; origem independente e
redistribuição não verificadas/autorizadas. Mídia e nome original ficam privados.

SHA-256 `76495b5cfff2c33b0c505252832ce5e798222ab14e29565a05fe2199d0fe4a65`.
Arquivo de 1.791.840 bytes; 480×854, aproximadamente 23,9591 fps e 15,5265 s.
Sem rotação ou ampliação. Calibração `3b9b1252-0e5c-407b-99c1-9bb20795abe4-v1`,
11 vértices selecionados pelo fundador. Configuração `.local/edge-piso-d.yaml`,
SQLite separado `.local/etapa05/piso-d.sqlite`. Mesmo modelo e floor-v0.1.

| Medida | Resultado |
| --- | --- |
| Captura / frames | ENDED, sem erro; 372 lidos, 78 analisados, 294 pulados |
| Qualidade inicial | 60 ONE_VALID_POSE, 4 NO_POSE, 10 LOW_CONFIDENCE, 4 MULTIPLE_POSES |
| Features elegíveis / candidatas / eventos | **58 /0 /0** |
| Tempo elegível / observado | 10.267 ms /15.401 ms |
| Quadril dentro do piso entre as elegíveis | **58/58** |
| Ângulo do tronco entre as elegíveis | 0,1590–51,4636°; política exige ≥60° da vertical da imagem |
| Razão altura/largura corporal entre as elegíveis | 1,0174–2,0590; política exige ≤1 |
| Estado final / outbox | OBSERVING /vazia, nenhum evento enviado |
| Taxa por tempo da mídia | 4,9997 análises/s |
| Inferência média / parede / throughput | 24,9461 ms /4,8532 s /16,0719 análises/s |
| CPU processo (um núcleo=100%) / pico working set | 111,40% /238.657.536 bytes |

As 58 observações elegíveis falharam simultaneamente em TORSO_NOT_HORIZONTAL e
BBOX_NOT_HORIZONTAL. Os outros 20 instantes foram inelegíveis. A métrica inicial
ONE_VALID_POSE não substitui a validação geométrica mais estrita das features.
O diagnóstico adicional reexecutou decoder/modelo/features com a mesma geometria,
sem HTTP ou escrita de episódios, e gravou apenas 78 linhas de sinais escalares
no arquivo privado `.local/etapa05/diagnostic-features-piso-d.json`.

**Resultado desfavorável:** a postura deitada confirmada pelo operador não foi
detectada. A confirmação e os sinais são compatíveis com limitação de perspectiva
da regra em coordenadas da imagem: corpo deitado fisicamente não implica eixo
horizontal ou caixa mais larga do que alta na projeção. Isso é uma interpretação
dos resultados, não uma medida 3D da cena. A marcação de piso passou; repeti-la ou
girar artificialmente a imagem não resolveria essa limitação de forma válida.
Não houve mudança de thresholds, modelo ou orientação para obter um alerta.
Sem anotações temporais completas, não se calcula recall/precisão desse ensaio.

Comandos/ações realmente executados, a partir da raiz:

```powershell
. ./scripts/activate.ps1
uv run --project services/edge --frozen radar-edge doctor --config .local/edge-piso-d.yaml
uv run --project services/edge --frozen radar-edge calibrate --config .local/edge-piso-d.yaml --frame-ms 1000
uv run --project services/edge --frozen radar-edge run --config .local/edge-piso-d.yaml --poses-only --preview --replay-speed 0.5
```

Doctor abriu o arquivo e inferiu pose no primeiro frame. Calibração e prévia
fecharam normalmente, exit 0. O processamento completo com eventos habilitados
foi executado em Python via `run_pipeline(load_config('.local/edge-piso-d.yaml'))`,
com resultado em `.local/etapa05/run-piso-d-result.json` e relatório nativo em
`.local/results/edge/a3b3c535-8e29-45f6-b51a-997f0244c882/report.json`.
API e credencial existente responderam 200, com câmera correspondente, sem
expor token. Não houve evento para publicar/conferir no painel. Nenhuma alteração
de código ou reexecução das suítes foi necessária neste ensaio; alterações finais
foram de documentação e metadados privados. A etapa ficou **PARCIAL** naquele
momento, antes da investigação com Full.

Conferência final deste ensaio: `uv run --project services/edge --frozen radar-edge
outbox-status --config .local/edge-piso-d.yaml` retornou status ok, fila vazia,
sem erro de entrega ou confirmação de incidente. `pnpm.cmd exec prettier --check`
nos cinco documentos atualizados passou; `git diff --check` passou, com avisos
de normalização CRLF/LF em documentos anteriores. A leitura diagnóstica inicial
via Python encontrou encoding cp1252 incompatível com símbolos dos documentos;
foi repetida com PYTHONIOENCODING=utf-8. Nenhuma falha de leitura foi tratada como
falha de captura ou eliminada do registro de trabalho.

## Dois arquivos adicionais da internet — piso-e-05 e piso-f-07

O fundador disponibilizou outros dois arquivos e os descreveu como vídeo real
encontrado na internet. Origem REAL_VIDEO registrada com base nessa declaração;
não houve verificação independente, URL fornecida ou licença de redistribuição
aprovada. Processamento solicitado somente no computador; nomes originais,
mídia, credencial e manifestos permanecem em `.local/`, fora do Git.
Papel CALIBRATION, retenção manual e anotações temporais incompletas.

Cada arquivo recebeu configuração/calibração/outbox própria. O fundador marcou
11 vértices de piso em cada janela e confirmou o fechamento ao salvar. Mesmo
Tasks Lite CPU/VIDEO, skeleton e política floor-v0.1, sem mudança dos gates.

| Medida | piso-e-05 | piso-f-07 |
| --- | --- | --- |
| SHA-256 | efbb2c6c4721df503426918056b5ed3f233f77b55595b70dce9f9d68c48e650f | 86a20851a1d3bfacbe11d8977972f95a256893b80cd4de66dc7bb224a4dca55b |
| Bytes | 10.206.712 | 9.262.980 |
| Dimensões originais / processamento / rotação | 1280×720 /640×360 /0 | 1280×720 /640×360 /0 |
| FPS metadata / duração estimada | 29,8526 /10.049,37 ms | 29,8048 /9.025,40 ms |
| Frames lidos / analisados / pulados | 300 /51 /249 | 269 /45 /224 |
| ONE_VALID_POSE / LOW_CONFIDENCE / NO_POSE | 15 /35 /1 | 15 /30 /0 |
| Features elegíveis / candidatas / eventos | **15 /0 /0** | **15 /6 /0** |
| Tempo elegível / observado | 2192 ms /10.016 ms | 2608 ms /8816 ms |
| Exclusões nas observações elegíveis: piso / ângulo / proporção | 15 /15 /15 | 7 /9 /7 |
| Estado final / outbox | OBSERVING /vazia | OBSERVING /vazia |
| Taxa por tempo da mídia | 4,9920 análises/s | 4,9909 análises/s |
| Inferência média / parede / throughput | 22,1023 ms /3,8146 s /13,3697 análises/s | 22,4535 ms /2,4175 s /18,6146 análises/s |
| CPU processo (um núcleo=100%) / pico working set | 134,35% /265.695.232 bytes | 189,38% /273.059.840 bytes |
| Calibração, versão 1 | 4166d9d6-3a3b-4b12-a05c-e1c0eb527b87 | 74bfeb97-6767-4cd4-9eb7-531d17d54778 |

Ambos terminaram ENDED, exit 0, sem erro e sem fallback temporal. Não houve
MULTIPLE_POSES. No primeiro, 36 observações não tinham todos os pontos essenciais
com qualidade suficiente; nas outras 15, nenhuma passou pela geometria candidata.
No segundo, 30 observações foram inelegíveis por qualidade/pontos insuficientes;
as seis candidatas restantes não sustentaram os 2 s com cobertura mínima de 80%.
O total de tempo elegível inclui posturas contrárias e não implica uma janela
candidata contínua. Os motivos de exclusão podem se sobrepor no mesmo instante.
Não houve observação positiva persistente para gerar evento ou incidente.

API e credencial existente conferidas com GET /v1/edge/me: HTTP 200 e câmera
correspondente, sem exibir bearer. Delivery foi habilitada nas duas configurações
depois dessa conferência; não havia evento para enviar. Processos do fundador,
volume e históricos anteriores foram preservados.

Comandos/ações executados na raiz com prefixo
`uv run --project services/edge --frozen`:

```powershell
radar-edge calibrate --config .local/edge-piso-e-05.yaml --frame-ms 1000
radar-edge calibrate --config .local/edge-piso-f-07.yaml --frame-ms 1000
radar-edge run --config .local/edge-piso-e-05.yaml --poses-only --preview --replay-speed 0.5
radar-edge run --config .local/edge-piso-f-07.yaml --poses-only --preview --replay-speed 0.5
```

Doctor e processamento completo foram executados em Python privado via
`doctor(load_config(...))` e `run_pipeline(load_config(...))`, salvando resultados
UTF-8. Prévias repetidas a pedido do fundador, sem HTTP, eventos ou alterações
dos checkpoints. Resultados completos em `.local/etapa05/run-piso-e-05-result.json`
e `.local/etapa05/run-piso-f-07-result.json`. Relatórios nativos, respectivamente:
`.local/results/edge/8b659840-baa1-411f-9a85-9a988390d628/report.json` e
`.local/results/edge/68d50a43-e15c-4cf5-9ecb-7e80a398ea4d/report.json`.
Resultado negativo preservado; nenhum teste foi removido ou limiar reduzido.

As duas prévias terminaram normalmente em ambas as reproduções, 51/45 análises,
events desabilitado e framesSaved=false. Depois de pedir a repetição, o fundador
relatou que o esqueleto verde pisca e apaga em vez de acompanhar continuamente;
é reconhecível, mas precisa melhorar. O comentário foi sobre o conjunto das
prévias, sem atribuir intervalos exatos a cada arquivo. Foi registrado assim nos
manifestos, sem inventar confirmação individual de orientação ou alvos temporais.
Essa instabilidade é coerente com LOW_LANDMARK_QUALITY medido, mas não demonstra
que exista uma única causa de oclusão, modelo ou enquadramento para ambos.
Não foram interpolados pontos para mascarar a perda nem alterados os thresholds.

`radar-edge outbox-status --config` nas duas configurações retornou status ok,
fila vazia e sem erros de entrega. Não há novo incidente para verificar no painel.
A etapa ficou **PARCIAL** naquele momento. A estimação de pose/continuidade e a
limitação de perspectiva motivaram a investigação posterior, preservando esses
ensaios negativos. Não houve mudança funcional de código nem nova execução das
suítes automatizadas nesse ensaio inicial de arquivos/configurações.

## Fechamento após investigação

A [investigação](INVESTIGACAO_ETAPA_05.md) registra pesquisa oficial, 20 comparações
controladas, escolha explícita do Full e as falhas que permanecem. Não foram
relaxados limiares, removida a detecção de múltiplas poses, rotacionada a fonte
artificialmente ou alterado o piso para forçar emissão.

Comandos adicionais realmente executados na raiz, com ativação em cada terminal:

| Comando/ação | Resultado |
| --- | --- |
| Download HTTPX do Full oficial versionado; cálculo SHA-256 | 9.398.198 bytes, hash 5134a3aad27a58b93da0088d431f366da362b44e3ccfbe3462b3827a839011b1, privado |
| `uv run --project services/edge --frozen python .local/etapa05/investigate_pose.py` | 20 comparações reais Lite/Full ×5/15 Hz, decisões 5 Hz; somente Full em piso-f-07 produziu evento |
| `uv run --project services/edge --frozen radar-edge model-fetch --variant full` | Artefato existente verificado, sem novo download |
| `doctor(load_config('.local/edge-piso-f-07-full.yaml'))` e `run_pipeline(...)` em Python privado | Modelo Full real, calibração compatível; um PERSON_ON_FLOOR aos 6000 ms, DELIVERED na primeira tentativa |
| Repetição do run; POST do mesmo payload persistido por HTTPX | EOF com zero novas análises/eventos; HTTP 200 duplicate=true, mesmo incidente |
| `uv run --project services/edge --frozen radar-edge evaluate --manifest .local/evaluation-full.json` | Seis arquivos reais em outboxes isoladas, sem HTTP: um evento no positivo, demais zero; métricas null por GT incompleto |
| `uv run --project services/edge --frozen radar-edge evaluate --manifest .local/evaluation-full-positive.json --replay-speed 2` | Mesmo PERSON_ON_FLOOR/6000 ms/digest, sem depender do ritmo de processamento |
| `uv run --project services/edge --frozen radar-edge run --config .local/edge-piso-f-07-full.yaml --poses-only --preview-paused --replay-speed 0.5` | Prévia real ENDED, 45 análises, pausa 26,3238 s; fundador confirmou piso/pessoa deitada e melhora do esqueleto |
| Link direto para o incidente da API no painel | Fundador confirmou Reprodução/Teste, offset, Full, duração e pose; nenhuma inspeção visual fictícia pelo agente |
| `$env:RADAR_TEST_GUI='1'`; `uv run --project services/edge --frozen pytest -q` | **226 aprovados**, nenhum skip, após a correção final de pausa |
| `pnpm.cmd test:api`; `pnpm.cmd test:contracts` | **124 API**, **87 TS e 87 Python**, PostgreSQL exclusivo removido, demo preservada |
| `pnpm.cmd lint`; `pnpm.cmd typecheck`; `pnpm.cmd lint:edge`; `uv build --project services/edge` | Aprovados; build Python repetido após pausa; sem alteração de dependências/locks |
| `uv sync --project services/edge --frozen`; `pnpm.cmd check:edge` | 42 pacotes conferidos; imports reais MediaPipe/OpenCV/Tasks ok, somente opencv-contrib-python como fornecedor cv2 |
| Prettier nos documentos/exemplo alterados; `git diff --check`; revisão privada de links/segredos/artefatos | 41 arquivos candidatos, dois tokens privados comparados sem ocorrência, nenhum link local quebrado; modelos/mídia/SQLite ignorados, locks/dependências intactos, wheel com 24 arquivos sem assets privados |
| `radar-edge outbox-status --config .local/edge-piso-f-07-full.yaml`; `docker ps` | Um DELIVERED, zero erros; somente radar-postgres-1 saudável, nenhum container de teste restante |

A última verificação de formato Ruff apontou uma expressão do rodapé da prévia
que ainda precisava de formatação. Foi formatada, e lint:edge passou em todos os
35 arquivos Python; nenhuma condição ou resultado de teste foi alterado.

## Avaliação e limitações

Manifesto validado com hash, autorização, retenção, pessoa/sessão/ambiente
pseudonimizados, papel e origem REAL_VIDEO/SYNTHETIC. evaluate cria outbox nova por
avaliação e não envia HTTP. Compatibilidade de hash/FPS/duração é conferida.
Correspondência fixada antes: mesmo kind, emissão no intervalo-alvo ou até 2 s
depois; no máximo um acerto por alvo, demais alertas associados são duplicações.
Intervalos excluídos e alertas inconclusivos aparecem separados. Denominadores
zero aparecem null (não estimável). Intervalos-alvo curtos/fora da mídia ou
sobrepostos são rejeitados. Elegibilidade desconta sobreposição temporal exata
com os intervalos excluídos, sem armazenar sequência ilimitada em memória.

O vídeo existente é material CALIBRATION, reutilizado como diagnóstico, com
annotationsComplete=false. Recall, precisão e falsos alertas/hora não são
estimáveis; não se declarou um negativo perfeito nem validação independente.
Anotações de postura e necessidade de assistência são separadas; o programa não
estima necessidade de socorro. Alongar/deitar voluntariamente no chão podem
disparar e continuam sendo confundidores. Os dois arquivos adicionais de deitar,
descritos pelo fundador, foram processados sem eventos; outros confundidores não
foram testados em vídeo nesta etapa. Não houve queda física solicitada ou provocada.

Avisos nativos XNNPACK, feedback tensors e NORM_RECT permanecem visíveis. Ressalva
de telemetria MediaPipe da D30 permanece: Radar não envia mídia, mas ausência total
de tráfego nativo não foi auditada. Firewall/permissões preservados.

## Critérios e pendências

| Critério | Estado | Evidência/ação restante |
| --- | --- | --- |
| Features, persistência temporal, trajetória, rearmamento e episódio prolongado | VERIFICADO EM TESTES | Testes determinísticos e regressões, geometria corrigida e motivos explícitos |
| SQLite/transação/retomada/payload estável/locks | VERIFICADO | Rollback injetado, restart com ativo/rearmando, checkpoint e fonte conflitante |
| HTTP real e timeout após commit, mesmo incidente | VERIFICADO COM ENTRADA SINTÉTICA | Python + Nest + PostgreSQL exclusivo, 124 testes API |
| Contratos e checks afetados | VERIFICADO | 226 Python, 87 TS, 124 API, lint, typecheck e build; locks preservados |
| Modelo real + motor em vídeo autorizado | VERIFICADO, LIMITAÇÕES REGISTRADAS | Full: um evento em piso-f-07; cinco outros arquivos sem evento; perdas de qualidade/perspectiva preservadas |
| Vídeo real positivo → evento → incidente REPLAY | **VERIFICADO** | Evento 49adcf39-a7c2-414a-ae8f-852e1a5ca8ee, incidente 6cfd7d88-ae34-4b48-ad5a-d592cbd020a9, Full e floor-v0.1, offset 6000 ms |
| Conferência do incidente real no painel, sinais/versões/evidência | **VERIFICADO PELO FUNDADOR** | Confirmou título, Reprodução/Teste, Full, offset 6000 ms, duração 2176 ms e pose; também confirmou prévia/piso |
| Evaluate com manifesto e episódios | VERIFICADO EM SINTÉTICO; DIAGNÓSTICO REAL SEM ALVOS | Correspondência/duplicação/exclusão/null testados; real sem anotação completa não mede eficácia |

Antes da investigação foi preparada `.local/edge-positive.yaml`, com fonte esperada `.local/videos/piso.mp4`,
videoId piso-01, autorização inicialmente false e calibração separada em
`.local/calibration-positive.json`. Ao receber o arquivo autorizado, confirmar o
caminho, marcar piso real sem incluir cama/sofá e executar. Reutiliza o mesmo
SQLite/câmera com reset explícito antes de trocar de fonte; não apaga histórico.
Esse caminho hipotético não é o usado na demonstração final. A configuração
validada é `.local/edge-piso-f-07-full.yaml`; não precisa receber novo vídeo ou
refazer piso. Nenhuma verificação obrigatória da 05 permanece pendente. Não se
exigiu a meta ampliada de 12 vídeos/30 minutos para esta etapa. Eficácia em amostra
independente, outras perspectivas, webcam e retenção continuam em seus escopos.

## Como reproduzir e próxima etapa

Siga [roteiro manual 05](../VALIDACAO_MANUAL_ETAPA_05.md), que inclui infraestrutura,
processamento, consulta de confirmações, retomada e avaliação. O vídeo da 04 não
gera incidente com os gates atuais; esse resultado é esperado no roteiro.

**Etapa 05 concluída para a demonstração experimental.** A etapa 06 continua
NÃO INICIADA e exige nova solicitação. Sem webcam, RTSP, snapshots, retenção
automática, treinamento, serviços pagos ou comunicação externa nesta entrega.

Referências técnicas consultadas: [sqlite3 Python 3.12](https://docs.python.org/3.12/library/sqlite3.html),
[transações SQLite](https://www.sqlite.org/transactional.html) e
[timeouts HTTPX](https://www.python-httpx.org/advanced/timeouts/).
