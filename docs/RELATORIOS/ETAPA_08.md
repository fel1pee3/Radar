# Etapa 08 — Validação final e entrega da demo

## Fechamento — 24/10/2026

Status: **CONCLUÍDA NO ESCOPO REVISADO DA BANCADA** (D50/D51).
Entrega local experimental, sem eficácia geral, uso assistencial/comercial ou
estabilidade prolongada aprovados. Etapa 09 não iniciada; nenhum deploy.
Versionamento posterior por commit/push solicitado pelo fundador em 24/10.

Sessão física continuous-4d4357f7…: 600,660 s totais, 597,453 s entre análises,
576,986 s elegíveis e 20,467 s inelegíveis. 2799 análises, zero eventos e
reconexões, fila vazia, encerramento normal/ACK aceito; fechamento automático e
Fonte encerrada confirmados pelo fundador. Código a2b76fa3… preservado e
demo:check --engineering exit 0. Não repetir suíte ou hardware sem novo motivo.
[Relatório físico completo, denominadores, comandos e artefatos](SESSAO_WEBCAM_10MIN_ETAPA_08.md).

Fundador relatou trecho voluntário no chão de menos de 10 s, corpo enquadrado,
sem alerta. Duração exata/posição do quadril na ROI não confirmadas e sem dados
individuais LIVE para reconstrução: **possível perda/inconclusivo**, não acerto
presumido. Essa cena não é um novo positivo nem amostra independente anotada.
O percurso positivo LIVE anterior já está comprovado; o teste atual atende
continuidade D51, sem comprovar recall ou ausência de falhas de percepção.

| Gate final | Evidência e resultado | Alcance |
| --- | --- | --- |
| Engenharia, acesso, contratos, persistência e recuperação | 14 tarefas demo:verify aprovadas; 317 Python, 155 API, 100 TS, 20 E2E, quatro simulador; hash atual conferido | Mesma fonte de 179 arquivos; simulador não comprova visão |
| Instalação limpa e backup/restore | Registros de recursos exclusivos e locks, imports reais, restore com redação/revogação | Mesmo Windows e caches; bancos pessoais preservados |
| FILE→visão→incidente→revisão | Incidente 6cfd7d88… e relatórios 05 | Reprodução TEST, material de calibração, sem generalização |
| LIVE→visão→incidente→revisão | Incidente 4e6f8c4b…; fundador confirmou evidência e histórico até v4 | Postura voluntária, sem queda provocada |
| Percepção independente exploratória | CAUCAFall congelado, revisão anterior: 3/4 alvos e zero alertas em oito ADL | Uma perda, mesma sala/quatro categorias, cobertura limitada |
| Continuidade nominal D51 | Sessão física auditada e conferência humana desta rodada | 10 min nominais; não comprova 30 min ou correção da falha aos 27min45s |
| Offline | Desconexão confirmada, incidente cbf11212…, API/painel consultados antes de reconectar | Replay/entrega/consulta, sem auditoria geral de telemetria |
| Apresentação formal | DISPENSADA por D50; roteiro disponível | Não executada; operação já exercitada |

Aceite final é documental/manual. O checker e gerador existentes ainda imprimem
gates originais fixos e releaseReady=false; não leem confirmações humanas/D50/D51.
Não alterar esse resultado nem anunciá-lo como aprovação automática. Snapshot
local de fontes e seu manifesto permanecem candidatos técnicos, com esta matriz
como decisão de alcance. Nenhuma publicação ou tag autorizada.

Aceite vinculado às evidências privadas em
`.local/etapa08/final-review-2026-10-24.json`. Gerado pelo comando realmente
executado `uv run --offline --project services/edge --frozen python
.local/etapa08/record-final-stage08-review.py`, exit 0, após conferir hashes da
engenharia, avaliação CAUCAFall e revisão humana da sessão. Não é assinatura
do fundador ou aprovação automática: registra a decisão documental do agente
com base nos relatos e artefatos. Comandos/métricas da sessão estão no relatório
físico; instruções de operação/retomada permanecem em VALIDACAO_MANUAL_ETAPA_08.

Verificações finais da entrega local, realmente executadas em 24/10:

| Comando | Resultado | Evidência/limite |
| --- | --- | --- |
| `pnpm.cmd demo:package` | Exit 0, 238 arquivos | `.local/releases/v0.1-candidate-efddb1fe-3f4b-4568-a51e-d45c09fca68c`; fonte a2b76fa3…, sem publicação |
| `node .local/etapa08/verify-final-package.mjs` | Exit 0, 238 hashes verificados | final-package-verification.json privado; aceite documental anexado como manual-validation.json |
| `git -c core.safecrlf=false diff --check` | Exit 0 | Documentos conferidos, não teste físico adicional |

O manifesto original do gerador continua status=PARCIAL/releaseReady=false, sem
adulteração. O manual-validation.json declara explicitamente o aceite documental
da etapa no alcance D50/D51, não uma liberação automática. Snapshot contém as
fontes/documentação no momento da geração; esta anotação posterior registra sua
verificação. Não inclui ambiente, credenciais, mídia, bancos, pesos ou dependências.

### Backlog priorizado, sem implementação nesta etapa

1. Investigar perdas por projeção 2D, corpo ocluído/objetos e trechos no chão sem
   alerta, com cenas temporizadas antes da análise; preservar resultados adversos.
2. Acrescentar rastreabilidade diagnóstica LIVE privada e limitada por observação,
   com revisão de retenção; hoje só há agregados, sem vídeo para reconstrução.
3. Medir separação entre prévia e inferência para maior fluidez, sem preencher
   articulações rejeitadas ou mudar dados que fundamentam os alertas.
4. Avaliar outras sessões/ambientes e desempenho prolongado. O teste original de
   30 min não foi comprovado e o erro tardio histórico não tem causa demonstrada.
5. Atualizar checker/manifesto para consumir aceite manual vinculado à fonte,
   sem transformar relatos em aprovação automática de percepção. Etapa 09 RTSP
   permanece opcional e depende de solicitação/hardware/acesso documentados.

## Histórico anterior ao fechamento

## 24/10 — conflito após remarcação do piso e recuperação sem apagar histórico

Tentativa informada pelo fundador:
`.local/etapa08/continuous-83559f87-227a-4c36-90d2-d766e4dcd39d`.
worker.json vazio; worker-errors.log contém relatório JSON com
SOURCE_CONFIG_CONFLICT, 2,2272 s totais, uma imagem adquirida e zero análises.
Não é teste de 10 min concluído. Diagnóstico completo em
`webcam-10min-preparation-302fa34d-22d5-40d8-859b-e1884a09a5d6/results/835bf8e2-c546-4fd2-9b60-00d4c7145309/report.json`
dentro de `.local/etapa08/`.

Calibração atual v3. Auditoria read-only calculou os fingerprints com a mesma
configuração/geometria: contexto persistido coincide com o piso arquivado v2 e
difere do v3. A proteção existente impediu reutilizar o checkpoint de outro
piso. Faltou indicar reset-episode nas instruções após remarcação; corrigido o
procedimento manual, sem desabilitar a proteção ou alterar worker/modelo/gates.

Confirmado zero workers de câmera antes da intervenção. Sob os locks existentes,
backup SQLite consistente criado em
`.local/etapa08/webcam-10min-conflict-83559f87/outbox-before-reset.sqlite`.
Executado o reset suportado com motivo `floor-recalibrated-v3-before-10min`.
Auditoria posterior confirma o mesmo runId antigo preservado e aposentado,
zero contextos ativos, um registro de reset, contagens/digests da outbox e
snapshots preservados. Havia zero eventos/episódios/imagens nessa fila.
Não foram alterados PostgreSQL, incidentes existentes, credencial ou marcação v3.
Não houve acesso à câmera nesta correção.

| Comando/ação realmente executado | Resultado | Alcance |
| --- | --- | --- |
| `uv run --offline --project services/edge --frozen python .local/etapa08/audit-webcam-10min-conflict.py before` | Exit 0, conflito v2/v3 confirmado, backup criado | Sem câmera, snapshots privados/ignorados |
| `uv run --offline --project services/edge --frozen radar-edge reset-episode --config .local/etapa08/webcam-10min.yaml --reason floor-recalibrated-v3-before-10min` | Exit 0, status ok | Contexto antigo aposentado com auditoria, histórico preservado |
| `uv run --offline --project services/edge --frozen python .local/etapa08/audit-webcam-10min-conflict.py after` | Exit 0, historyAndOutboxPreserved=true | Nenhum contexto ativo; próximos frames ainda não testados |
| `uv run --offline --project services/edge --frozen pytest services/edge/tests/test_outbox_delivery.py -k 'conflicting_source_or_camera or restart_payload_stable_checkpoint_and_explicit_reset_history' -q` | 2 passed, 22 deselected | Verifica bloqueio e reset/preservação; não comprova webcam física |
| `node .local/etapa08/verify-cauca-source.mjs` | Exit 0, a2b76fa3… inalterado | Candidato avaliado preservado, sem nova execução CAUCAFall |
| `Invoke-WebRequest` nos health/ready de API 3001 e proxy 3000 | HTTP 200 nos dois | Readiness, sem autenticação de proprietário |
| Python via stdin com `httpx`, credencial pelo loader existente, `GET /v1/edge/me` | HTTP 200, câmera corresponde à configuração | Loopback, sem exibir token; auth-preflight.json privado |
| `uv run --offline --project services/edge --frozen radar-edge outbox-status --config .local/etapa08/webcam-10min.yaml` | Exit 0, status ok, fila vazia e sem erros de entrega | Leitura após o reset, sem câmera |
| `git -c core.safecrlf=false diff --check` e `git check-ignore` nos caminhos novos privados | Exit 0; helper, backup e preflight ignorados | Verificação documental/privacidade; sem commit |

Pendente: executar novamente observe.ps1 com webcam-10min.yaml, sem nova
remarcação, e revisar a sessão real. Correção do conflito verificada sem hardware;
não declarar sessão física aprovada. Etapa 08 **PARCIAL**. Resultados anteriores,
inclusive falha aos 27min45s e perdas de percepção, preservados.

## D51 — preparação da sessão curta de 10 minutos

23/10/2026: o fundador informou que fará somente 10 min. D51 revisa
explicitamente a duração do gate físico desta bancada; não registra aprovação
do ensaio original de 30 min. A falha aos 27min45s e sua causa histórica não
estabelecida permanecem. Uma sessão curta não comprova correção da falha tardia.
Registro da preparação de 23/10: etapa **PARCIAL**, ensaio curto ainda não
executado naquele momento. A tentativa posterior e sua recuperação estão acima.

Preparada `.local/etapa08/webcam-10min.yaml`, limite de 600 s do worker,
estabilização visual ligada, mesmo RTMO-s/política/gates/credencial referenciada,
JPEG desabilitado. Calibração copiada, resultados/outbox novos e arquivos
anteriores preservados. Sem gravação de vídeo. O timer começa antes da abertura
da câmera/modelo: separar aquecimento e tempo efetivo de captura/inferência,
sem afirmar que 600 s configurados são 600 s de imagens úteis. Conferir
enquadramento/piso em movimento antes da sessão; remarcação só na nova cópia.

Preparação privada:
`.local/etapa08/webcam-10min-preparation-302fa34d-22d5-40d8-859b-e1884a09a5d6/preparation.json`.
Verificações desta preparação, sem acesso físico:

| Comando realmente executado | Resultado | Limite |
| --- | --- | --- |
| `. ./scripts/activate.ps1` | Ferramentas ativadas | Não abre câmera |
| `uv run --offline --project services/edge --frozen python .local/etapa08/prepare-webcam-10min.py` | Exit 0, PREPARED_NOT_EXECUTED, limite 600 s | Config/polígono/SHA do modelo e preservação dos originais verificados; arquivo de credencial apenas existe, sem leitura/autenticação |
| `node .local/etapa08/verify-cauca-source.mjs` | Exit 0, sourceUnchanged=true | SHA a2b76fa3… preservado; documentação/configuração privada não alteram o candidato |
| `pnpm.cmd demo:check --engineering` | Exit 0, engenharia aprovada | releaseReady=false; não comprova sessão física |
| `git -c core.safecrlf=false diff --check` | Exit 0, sem erros | Verificação documental; não substitui execução |
| `git check-ignore` nos três caminhos novos de configuração/helper/registro | Todos ignorados | Nenhum arquivo privado adicionado ao Git |
| `Invoke-WebRequest` nos health/ready da API 3001 e proxy web 3000 | Ambos HTTP 200 | Readiness local neste momento, sem login ou teste físico |
| `Get-CimInstance Win32_Process` filtrando python/uv com radar-edge run/probe/calibrate | Zero workers de câmera ativos | Câmera não aberta nesta preparação |

O checker ainda imprime uma lista genérica dos gates originais, inclusive
apresentação/30 min e percursos já comprovados. Ele não lê as decisões D50/D51
nem certifica confirmações humanas. Interpretar sua aprovação apenas como
engenharia; o estado manual atual está em STATUS/matriz e continua PARCIAL.

Mudanças documentais: decisões D51, critérios da 08, README/status, roteiro
manual, matriz e referências atuais ao ensaio físico. Sem alteração do worker,
timer, modelo, política, locks ou resultado congelado CAUCAFall.

Para executar quando o piso estiver conferido e API/web ligadas:

```powershell
. ./scripts/activate.ps1
powershell -NoProfile -File scripts/validation/observe.ps1 -Config .local/etapa08/webcam-10min.yaml
```

Na preparação de 23/10, o comando acima ainda não havia sido executado.
Para a nova sessão, observar atividades comuns, sem deitar,
pausar ou reiniciar; encerramento automático por volta de 10 min. Depois conferir
recursos, captura/inferência efetivas, períodos inelegíveis, eventos/fila e
encerramento normal. Zero alertas só é esperado se a cena não contiver postura
alvo; não transformar tempo sem pose em ausência comprovada de ocorrências.

## D50 — apresentação formal dispensada pelo fundador

23/10/2026: o fundador informou que já opera o sistema durante a construção e
dispensou a apresentação cronometrada de 5–7 min. Não é uma etapa de aprendizado
a exigir. Roteiro preservado como material opcional; estado **DISPENSADA**, não
executada ou aprovada por inferência. Login, revisões, pausa/retomada/encerramento
já exercitados seguem como evidências operacionais anteriores.

Documentação e matriz atualizadas conforme D50 em decisões. Isso supera as
pendências de apresentação nas seções históricas abaixo. Nenhum código, modelo,
política ou resultado foi alterado; não há nova execução de hardware/testes por
esta mudança documental. Verificação apropriada: git diff --check. Etapa 08
permanece PARCIAL pelo ensaio físico ainda pendente (duração revista em D51);
perda de percepção
e instabilidade da pose continuam registradas. Sem commit/push/deploy.

## Primeira avaliação congelada CAUCAFall

Doze vídeos novos do fundador, 4 alvos e 8 ADL, 2876 quadros/143800 ms;
hashes/tamanhos/20 FPS/720×480 conferidos, V4/CC BY 4.0 verificada na fonte.
Fundador confirmou novidade, os 12 pisos e cenas/faixas antes da inferência,
ressalvando pequenos detalhes do contorno. Candidato SHA a2b76fa3…/modelo/
política congelados. Evaluate exit 0: 12 ok/ENDED, 722 análises, três eventos
PERSON_ON_FLOOR para três de quatro alvos, uma perda, zero duplicações e zero
alertas nos oito ADL. Sem POSSIBLE_FALL, webcam, JPEG, HTTP ou escrita no banco.

142000 ms observados, 107600 ms elegíveis, 34400 ms inelegíveis e 1800 ms de
caudas sem amostra. Nos ADL, apenas 69000 ms elegíveis; zero alertas nesse
período não prova taxa geral nula. Latências dos três acertos: 1000/1800/4000 ms,
com incerteza anotada de até 500 ms. Quatro atividades comuns, uma sala/câmera,
sessões de aquisição desconhecidas. Avaliação executada; eficácia limitada.

Diagnóstico do perdido FallLeftS9, mesmos modelo/piso/gates, sem eventos: no alvo,
36/37 observações elegíveis, quadril dentro em 36/36, zero candidatas. Ângulo
projetado 26,24–41,73° e proporção 1,06–1,97 recusados pelos gates de >=60°/<=1.
Limitação de projeção 2D preservada; não há correção comprovada. Diagnóstico não
é 13ª amostra. Três perdas históricas também permanecem.

Resultado `.local/evaluation/590d9698-a97c-4adc-b212-0fe28db0d1ee/evaluation.json`.
run-cauca-evaluation.py, resumo, auditoria do perdido e verificação de código/
modelo/arquivos: exit 0. Guard de reexecução testado, ALREADY_COMPLETED sem
inferir novamente. Falta o ensaio curto nominal de 10 min (D51); apresentação dispensada
por D50. Etapa PARCIAL.
[Tabelas, denominadores, hashes, protocolo e comandos](CAUCAFALL_ETAPA_08.md).

## Prévia adicional solicitada: outro vídeo com estabilização

Preparado 20.mp4/intake08-17, já CALIBRATION, SHA-256
`2c50d5e3b8dc82baf8246bab4b86273fb93375ceea287f1d334a7bc56342fa36`.
RTMO-s em cada quadro e VisualSmoother com os mesmos parâmetros aprovados.
Sem alterações no produto/configurações originais, motor, HTTP ou webcam.
Mantidos os vídeos novos para futura avaliação independente. Piso exibido é
o diagnóstico anterior do clipe; esta reprodução não confirma seu alinhamento.

Executado helper privado prepare-another-stabilized-preview.py, exit 0:
342 quadros processados e decodificados no MP4 final, 282 com doze pontos,
60 NO_POSE; 56,59 s de preparo. Saída a 29,85 quadros/s é pré-processada,
não desempenho de inferência ao vivo. Ausências não foram preenchidas.
Material em `.local/etapa08/another-stabilized-preview-aecfc57c-dcf7-4854-b2f6-1ec8b161d1e5/`.

Helper preview-another-stabilized.ps1 validado e iniciado com janela pausada,
título “Radar - outro video estabilizado - REPLAY”, PID Python 24036 confirmado
na abertura, sem stderr. Espaço reproduz/pausa; R repete; Q/Esc fecha.
Conferência posterior: fundador relatou bom acompanhamento/fluidez, com esqueleto
piscando. Auditoria localizou 60 NO_POSE em 342 quadros, distribuídos em 29
intervalos. Ausências da saída bruta preservadas, sem redução de limiar ou alegação
de correção. Apenas prévia; não satisfaz avaliação independente ou 30 min físicos.

Reabrir:

```powershell
powershell -NoProfile -File .local/etapa08/preview-another-stabilized.ps1
```

## Continuação sem webcam, após adiamento pelo fundador

O fundador informou “Deixamos o teste físico para depois”. Câmera não aberta;
pendência de 30 min preservada, sem iniciar outro ensaio automaticamente.

Reavaliados dois clipes negativos de cadeira cujos pisos e ausência de pessoa
deitada o fundador já havia confirmado. Manifestos/anotações anteriores
vinculados ao RTMO atual por SHA do vídeo e igualdade da geometria/polígono do
piso; sem pedir nova conferência da mesma cena. Configurações e saídas exclusivas,
modelo/política fixados, modo CALIBRATION, sem HTTP/JPEG/GUI. Não foi teste novo
de fluidez: a prévia fica desabilitada durante evaluate.

| Cena | Análises | Observado/elegível (ms) | Cauda não amostrada (ms) | Eventos |
| --- | ---: | ---: | ---: | ---: |
| chair08-01 | 47 | 9216 | 98 | 0 |
| chair08-02 | 32 | 6208 | 98 | 0 |
| Total | 79 | 15424 | 196 | 0 |

Ambos ok/ENDED. Nenhum alvo anotado e nenhum alerta: recall/precisão/latência
não estimáveis, não 100%. Amostra de uma atividade/grupo, com menos de 16 s;
não comprova taxa geral de falsos alertas nem sessão independente. Conteúdos
originais, anotações e calibrações conferidos por hash após a execução: intactos.
Perdas anteriores nos três vídeos de pessoa no chão permanecem registradas.

Executados: prepare-current-negative-evaluation.py (exit 0), radar-edge evaluate
(exit 0) e auditoria Python via stdin (exit 0). Artefatos privados em
`.local/etapa08/current-negative-evaluation-d77fb491-7a06-407f-9c62-251cace82da6/`;
resultado `.local/evaluation/aaa34eb1-5732-4cf9-ae18-07edc581e81b/evaluation.json`,
SHA-256 `37c7dde77348cc909ad600eacad708b09d595654f2cb53584a938a753aee9cc0`.

Reprodução, sem abrir webcam ou enviar eventos à API:

```powershell
. ./scripts/activate.ps1
$validationPlan = Get-Content -Raw -Encoding UTF8 .local/etapa08/current-negative-evaluation-latest.json | ConvertFrom-Json
uv run --offline --project services/edge --frozen radar-edge evaluate --manifest $validationPlan.manifest
```

Plano de coleta/anotação em `.local/etapa08/current-evaluation-plan.json`.
Há zero vídeos independentes anotados para o candidato atual neste inventário.
Meta documental de quatro alvos e oito confundidores mantida, com sessões reais
identificadas; não exige 12 pessoas ou inventa independência por recortes.
Anotar antes de executar o detector. Deitar voluntariamente pode ser acerto de
postura e não implica acidente/necessidade de ajuda; não exigir zero evento de
postura nesse confundidor. Novas gravações e confirmação de intervalos ainda
dependem do fundador; não foram solicitadas como ação imediata nesta retomada.

## Execução cadenciada e estabilização opcional no worker

Verificação geral final: demo:verify exit 0, 14 tarefas, 317 Python sem skip,
155 API, 100 contratos TS, 20 E2E, quatro testes do simulador, frozen/lint/tipos/
build/imports, backup/restore e instalação limpa. Código SHA
`a2b76fa33449fac7a438efa10e5470580b6310a6b12530d62bf33790b8aeb991`, 179 arquivos.
demo:check --engineering 0; demo:check 2 esperado; diff --check 0.
Execução FILE normal conferida pelo fundador: “Acompanha bem; movimento aceitável”.
Report 5f15051f-41e4-4144-a417-c1fe8207e7f2 terminou ok/ENDED, 32 análises
válidas, sem ausências/erro. Pausa inicial de 1129,76 s registrada separadamente;
não converter tempo total com pausa em FPS do modelo. Sem câmera ou eventos.
Etapa continua parcial.

Auditoria de separação por SHA confirmou que intake08-02/05/08 reaparecem na
comparação RTMO como floor03/05/07. O grupo de sete vídeos antes reservado ao
Full e a mesma origem dos vídeos da cadeira passaram a apoiar diagnóstico e
seleção; não servem como avaliação independente do candidato atual. Mantidos
split e resultados históricos; nova classificação em
`.local/etapa08/perception-split-audit.json`. Revisão humana FILE em
`.local/etapa08/stabilized-worker-check/human-review.json`, vinculada ao hash
do report e do vídeo.

Preparada `.local/etapa08/webcam-final-stabilized.yaml`, opção visual ligada,
limite de 1830 s, sem JPEG, com cópia própria do piso e resultados/fila novos. Modelo/hash, config e
estrutura do piso conferidos; config/piso originais preservados. Credencial
apenas existe no arquivo: autenticação e enquadramento atual não verificados.
Não abriu câmera ou outbox. Preparo não aprova continuidade. O fundador não
precisa deitar novamente: o percurso LIVE/revisão já está comprovado.

Nesta retomada, executado o helper privado record-current-validation.py: a
primeira execução interrompeu na auditoria por usar nomes de caso em vez dos
IDs dos arquivos. Corrigida a correspondência por SHA-256, execução exit 0.
Não houve mudança no código do produto ou nos resultados históricos. Próximos
gates: percepção/anotações independentes, 30 min contínuos e apresentação.
Complementado o preparo por Python via stdin (exit 0): calibração copiada para
o diretório exclusivo, igualdade estrutural conferida, original intacto e
configuração recarregada. Isso impede que eventual remarcação dessa cópia altere
o piso anterior. Nenhum acesso físico ou ensaio de 30 min realizado nesta retomada.

Executados seis ensaios FILE no ritmo original com inferência real, slot único,
267 análises/1170 quadros publicados, sem quadros futuros/repetidos. Cadência
medida de 7,2–7,4 desenhos/s sem janela e 5,2 na execução GUI; não são 30 FPS.
Filtro de cerca de 0,3–0,4 ms por análise, com inferência como custo dominante.
Integrada opção processing.previewStabilization (default false), apenas visual,
sem alterar dados de alertas, identidade ou frequência de decisões. Equivalência
com candidato: 1236 quadros e diferença 0 px. CLI normal em vídeo autorizado
terminou com 32 análises válidas, sem ausência/HTTP. 38 testes direcionados passaram.
[Detalhes, comandos e verificação geral](EXECUCAO_REAL_E_PREVIA_ETAPA_08.md).

As seções seguintes preservam as fases de pesquisa anteriores à integração.

## Continuação: pose real por quadro e custo no notebook

Conferência posterior do filtro visual concluída pelo fundador: acompanhamento
bom, boa fluidez, ausência de partes desaparecendo e menor tremor na cadeira 2;
pequenas oscilações ainda visíveis. Não relatou atraso, mas não houve medição
humana de latência. Candidato e parâmetros preservados, sem integração automática
ou aprovação LIVE. Não pedir novamente a mesma conferência como se pendente.

Fundador confirmou melhora de acompanhamento/fluidez e esqueleto visível na
cadeira 2; apontou tremor em repouso. Investigação adicional de estabilização
visual, preservando observações/alertas: seis vídeos, mesmos pontos nos 1236
quadros, 11 testes específicos aprovados. Ruído sintético de posição parada
reduziu de 1,95 para 0,99 px; não é precisão anatômica. Comparação aberta pausada
para conferir tremor e atraso, sem adoção no worker.

Executadas 1236 inferências em seis vídeos por modelo, sem webcam ou HTTP.
RTMO-s manteve 12 pontos em 187/187 quadros da cadeira 2; no conjunto, 29 quadros
sem pose. Custo completo 7,66–8,03 quadros/s. RTMO-t oficial obtido apenas para
pesquisa privada: mais rápido, mas 160 quadros sem pose; não adotado. Threads
4/2/1 medidas em ordem balanceada, mantendo quatro na configuração atual.
Reaplicação pura nos 210 quadros comuns reproduziu a baseline RTMO-s; todos os
quadros mudaram tipo/tempo do positivo histórico sem corrigir as três perdas.
Frequência operacional preservada. Comparação por quadro aberta pausada para
conferência de alinhamento, sem alegar FPS LIVE. 39 regressões direcionadas e
demo:check --engineering passaram. Preferência do fundador registrada em D48.
[Método, resultados, arquivos e comandos](QUADRO_A_QUADRO_ETAPA_08.md).

## Investigação da fluidez e do alinhamento

Conferência posterior do fundador: direita mais fluida, mas alinhamento não
confirmado devido ao piscar. Diagnóstico reproduzido: na cadeira 2, 32 âncoras
com 12 pontos aceitos; acompanhamento perde segmentos em 74/155 quadros
intermediários. Alternativa direta da âncora testada nos mesmos 20 clipes
piorou o conjunto (1380 contra 1094 quadros com perdas) e não foi adotada.
13 regressões direcionadas passaram; sem alteração do código operacional ou
novo teste físico. Registro detalhado no complemento do relatório de fluidez.

Executados dois candidatos de acompanhamento visual em material de calibração,
sem webcam/inferência nova/HTTP: 20 clipes, 4581 quadros e 776 âncoras originais
conferidas por hash, câmera, tempo e calibração. Comparações privadas a cadência
da mídia (~30 quadros/s) mostram diferença para a prévia dos quadros analisados
(~5/s), mas perderam segmentos intermediários. Não medem desempenho LIVE nem
comprovam melhora anatômica. Nenhum candidato foi importado pelos laços normais
FILE/LIVE ou ativado na câmera. Posições estimadas ciano não são evidência.

Ferramenta pública de validação, tracker isolado e 13 regressões adicionados.
Nova verificação completa: demo:verify exit 0, 14 tarefas, 302 Python, 155 API,
100 contratos TS, 20 E2E, quatro testes do simulador, lint/tipos/build,
backup/restore e instalação limpa. demo:check --engineering 0; demo:check 2.
SHA atual de 177 arquivos:
`7927d913436cd52cc7cbcf330ec01a845f31cf8e79cd58b5a5d931810d2a142f`.
Evidências anteriores preservadas; resultados detalhados, perdas dos dois
candidatos e instruções para assistir em
[FLUIDEZ_E_ALINHAMENTO_ETAPA_08](FLUIDEZ_E_ALINHAMENTO_ETAPA_08.md).

## Ordem dos próximos trabalhos

Critérios reconferidos no prompt original do fundador e em
`07_VALIDACAO_E_DEMO.md`. Próximo trabalho técnico: investigar fluidez/alinhamento
em arquivos existentes, sem webcam; completar análise de percepção e seus
limites. Depois permanece o requisito obrigatório de 30 min contínuos, que não
foi atendido pela sessão de 27m45s, e a apresentação final pelo fundador.
Não iniciar repetição física automaticamente. LIVE→incidente→revisão já foi
comprovado; replay/serviços offline também. Combinações offline não exercitadas
permanecem limites informados, sem criar novos gates independentes do prompt.
[Responsáveis e sequência](../VALIDACAO_MANUAL_ETAPA_08.md).

## Offline em replay e serviços — verificado em 23/10

O fundador executou `powershell -NoProfile -File .local/etapa08/test-offline.ps1`
e confirmou expressamente que desconectou Wi-Fi/cabo e conferiu o incidente
no painel antes de reconectar. Resumo do script: 18:53:43.779Z–18:54:22.088Z,
externalProbeFailed true, API/proxy web HTTP 200, workerExit/deliveryExit 0,
completed true e cameraOpened false. Horários exatos de desconexão/retorno
não medidos pelo script; desconexão e conferência são confirmação humana.

Report FILE/RTMO: status ok, sem erro, 45 análises, um POSSIBLE_FALL aos 4224 ms,
DELIVERED=1, deliveryErrors vazio, snapshots=0. Evento
`d1625d93-fff1-488b-9eb7-bea88c9e486c`; incidente
`cbf11212-8a99-444c-89a3-051284628d04`, recebido pela API às
2026-10-23T18:54:18Z. O fundador forneceu conteúdo da página marcada
Reprodução/Teste, com RTMO, pose, descida rápida, duração no piso 2208 ms,
fração válida 1 e histórico de criação/aviso local. Estado Aberto/Não revisado.
Título Possível queda é classificação do motor em replay, sem comprovação de
acidente real. Artefatos originais preservados em
`.local/etapa08/offline-check-865f2042-8e8a-4218-8e51-f73d10f6b7ce/` e
`.local/etapa08/offline-replay-5f6e3d47-3b60-44ac-b0c2-e7a11c1cf921/results/b07ca1d9-53c8-4f2f-96f4-c762f80b6614/report.json`.

Teste de replay, entrega e consulta no painel sem internet atendido neste
escopo. Não foram exercitados webcam offline, novo login, ação humana ou
reenvio do evento enquanto desconectado. Sem instalação/model-fetch durante
o teste, sem mudança de interfaces/firewall pela IA ou upload de vídeo.
Não marcar esses complementos como executados. Etapa permanece PARCIAL.

### Preparação preservada

Após a revisão humana, preparada configuração privada FILE/RTMO em
`.local/etapa08/offline-replay.yaml`, usando a cópia recuperada do vídeo
histórico autorizado, modelo/política já testados, calibração correspondente,
fila/resultados novos e credencial da câmera FILE apenas referenciada. Sem
JPEG, preview ou webcam. Não é avaliação independente nova.

API `/v1/health/ready` e proxy web `/api/health/ready` retornaram HTTP 200.
Executado `powershell -NoProfile -File .local/etapa08/test-offline.ps1 -PrepareOnly`:
configuração, existência de vídeo/calibração/credencial e SHA do modelo verificados;
não autenticou credencial, abriu câmera, executou replay ou alterou banco.
Sintaxe PowerShell validada. O modo de teste aguarda 30 s para o fundador
desconectar internet, registra tentativa externa e serviços locais, roda replay
com `uv --offline`, verifica ACK TEST/REPLAY em SQLite read-only e preserva logs.
Marcador impede reaproveitar execução anterior como nova prova.

Na preparação, o teste ainda estava pendente. A execução e confirmação humana
posteriores estão documentadas acima. Webcam offline e novo login/revisão
manual ainda não são provas feitas. Nenhuma interface ou firewall alterado.

## Observação humana e correção de estabilidade após a sessão

O fundador relatou cadeira com pés apoiados, saída do quadro por menos de um
minuto e nenhuma postura deitada. Percebeu baixa fluidez, pontos sumindo e
reaparecendo/desalinhados, principalmente em movimento rápido. Relato retrospectivo,
sem horários ou gravação para reavaliar articulações. Zero eventos nesse período
confirma apenas a não emissão nesta atividade informada, sem eficácia geral.

Investigação sem câmera reproduziu uma disputa Windows ao substituir o arquivo
de status aberto pelo leitor. Correção limitada de I/O e diagnóstico, com 289
testes Python aprovados; não afirma causa histórica nem melhora de pose ou
conclusão dos 30 min. [Alterações, comandos, provas e limitações](ESTABILIDADE_WEBCAM_ETAPA_08.md).
Verificação final após fixar o leitor: demo:verify exit 0, 14 tarefas;
289 Python, 155 API, 100 contratos TS, 20 E2E e quatro testes do simulador,
lint/tipos/build, imports, locks, backup/restore e instalação limpa aprovados.
demo:check --engineering exit 0; demo:check exit 2 por gates manuais.
Uma rodada preliminar foi recusada pela guarda de identidade porque houve
ajuste durante a execução; foi preservada e repetida, sem ignorar essa guarda.

## Sessão contínua RTMO — falha antes dos 30 min

Conferência após encerramento: report status error, PROCESSING_ERROR genérico,
totalWallSeconds 1665,6411 (27 min 45,64 s), abaixo dos 1800 s obrigatórios.
7906 análises: 6877 ONE_VALID_POSE, 516 LOW_CONFIDENCE e 513 NO_POSE; zero
eventos, candidatas ou snapshots. Isso não comprova ausência de falsos negativos
ou identificação correta de toda pose. Intervalo entre primeira/última análise
1662,734 s, elegibilidade temporal acumulada 1420,690 s. Motivos de exclusão
se sobrepõem; não somar como eventos ou durações independentes.

Inferência média 118,24 ms, 4,75 análises/s de tempo total. Pico de memória do
processo 236.347.392 bytes; soma máxima de working sets da árvore monitorada
349.970.432 bytes (páginas compartilhadas podem contar duas vezes). CPU acumulada
4439,28 s, 266,52% de um núcleo lógico, 12 disponíveis. Monitor: 1446 amostras,
maior intervalo 1,364 s; 1443 RUNNING/heartbeat ACCEPTED, três iniciais sem
status observado, uma amostra FRAME_TIMEOUT. Não foi observada PAUSED nos
status amostrados; amostragem não prova ausência de interrupções entre amostras.

Adaptador: 49.646 frames adquiridos, zero reconexões e errorCode null; terminou
reportando RUNNING nos metadados próprios, enquanto tratamento genérico marcou
heartbeat ERROR/CAPTURE_ERROR. Não há evidência para culpar driver ou webcam.
O except genérico descartou tipo/trace da exceção e worker-errors.log está vazio;
causa exata não comprovada. Investigação posterior reproduziu um defeito de I/O
e adicionou diagnóstico seguro, conforme complemento acima. Não atribuir essa
correção automaticamente ao erro histórico nem declarar a sessão aprovada.

Logs e SQLite preservados. Leitura de report.json, worker.json e resources.jsonl,
e resumo agregado em resource-summary.json executados sem reabrir a webcam.
Gate contínuo NÃO APROVADO; relato posterior do fundador registrado acima.
Não confundir zero alertas com acerto comprovado. Sem repetição automática.

Em 23/10, aproximadamente 14:30 locais, API inicialmente desligada foi iniciada
com `pnpm.cmd --filter @radar/api start`; `/v1/health/ready` retornou HTTP 200,
login web também HTTP 200. Configuração privada validada em
`.local/etapa08/webcam-rtmo-30min.yaml`: mesmo modelo/política/piso v2 e webcam 0,
maxRunSeconds 1830, sem limite de observações, exportação até 10000 observações/
50 MiB, outbox e resultados novos, snapshots desabilitados. Configurações dos
ensaios anteriores preservadas. Fundador não realizará postura no chão nesta
sessão; avaliar estabilidade e atividades cotidianas, sem alegar positivo novo.

Executado `powershell -NoProfile -File scripts/validation/observe.ps1 -Config
.local/etapa08/webcam-rtmo-30min.yaml` em processo oculto. Prévia LIVE confirmada,
amostra inicial de recursos com seis processos, heartbeat ACCEPTED/RUNNING,
sem qualidade degradada ou erro de captura e análise inicial em cerca de 4,67 Hz.
Logs/recursos em `.local/etapa08/continuous-d0ff0c09-4e15-45ea-9754-42539fcd5814/`;
launcher em `.local/etapa08/continuous-rtmo-launch.json`. Preparação e início
confirmados; resultado final desfavorável descrito acima. Nenhum vídeo gravado
pelo monitor.

## Ensaio curto RTMO LIVE — 23/10/2026

Após confirmação do fundador, launcher privado aguardou 30 s e executou
`uv run --project services/edge --frozen radar-edge run --config
.local/etapa08/webcam-rtmo.yaml --preview`. Encerrou automaticamente com status
ok, captureState ENDED e erro null, em 90,48 s. Webcam 0/DSHOW, calibração v2.
405 análises, 326 ONE_VALID_POSE, 77 LOW_CONFIDENCE e 2 NO_POSE;
inferência média 133,02 ms, 4,48 análises/s de tempo total, pico de memória do
processo 236.363.776 bytes. CPU acumulada 248,61 s em threads nativas (274,77%
de um núcleo lógico, 12 disponíveis); não representa uso de 274% do computador.

Um PERSON_ON_FLOOR, evento `d4cebe2e-7fbe-41c7-a138-3beb910f5b77`, entregue
em uma tentativa: ACK CURRENT, duplicate false, incidente
`4e6f8c4b-d366-4787-8f31-645fee7988c5`, recebido em
2026-10-23T16:59:02.840Z. Consulta da outbox feita em SQLite mode=ro;
DELIVERED=1, sem erro de entrega, snapshots vazios e framesSaved false.
Heartbeat final aceito, ENDED. Logs em `.local/etapa08/live-rtmo-latest.json`;
relatório em `.local/etapa08/rtmo-webcam/results/6f92235d-f4b1-4fd5-b05f-8de7b20f57a9/report.json`.

O fundador abriu o incidente e forneceu o conteúdo do painel: Ao vivo/Atual,
Aberto v1, modelo RTMO, calibração v2, pose corporal, quadril no piso, duração
2109 ms, fração válida 1, sem descida rápida e sem imagem. Conferência de
recepção/exibição confirmada. Na conferência inicial ainda estava Não revisado.
Depois o fundador forneceu o histórico auditado do painel: reconhecimento
v1→2 às 14:05:12; Postura no chão confirmada v2→3 às 14:05:37; repetição da
mesma revisão v3→4 às 15:48:06, em 23/10, America/Sao_Paulo. Nota confirma
teste controlado com pessoa já deitada, sem queda. Evidência desta confirmação
é o histórico fornecido pelo fundador; não houve nova leitura SQL das ações
nesta conferência. Gate visão LIVE→incidente→revisão atendido no ensaio
delimitado, sem alegar acidente real ou eficácia geral. A revisão repetida
permanece auditada e não constitui outro incidente; nada foi removido.
Este ensaio curto não atende 30 min contínuos, novas cenas
independentes, offline ou apresentação. Etapa continua PARCIAL.

Atualizado: 23/10/2026, America/Sao_Paulo. **Status: PARCIAL**.

Preparação física em 23/10: `radar-edge probe --config
.local/etapa08/webcam-rtmo.yaml --seconds 60 --preview` terminou com status ok,
índice 0/DSHOW, 1449 frames consumidos e nenhuma reconexão, sem inferência ou
gravação de frames. Fundador confirmou enquadramento. Após tentativas de captura
bloqueadas pelo operador, `radar-edge calibrate --config
.local/etapa08/webcam-rtmo.yaml --frame-ms 20000` permitiu sair da frente antes
da imagem parada; calibração privada versão 2 salva com status ok, sem frame
salvo. Fundador informou conclusão da marcação. `pnpm.cmd infra:up` retornou
PostgreSQL Healthy; `pnpm.cmd dev:api` e `pnpm.cmd dev:web` iniciados, com
HTTP 200 em `/v1/health/live` (3001) e `/login` (3000). Esse preparo antecedeu
o ensaio RTMO LIVE descrito acima. Logs privados em
`.local/etapa08/enquadramento-latest.json` e `marcacao-webcam-latest.json`.

Base: main `68ac3d60418ecc6b272990f6c48a14c62918ed13`; árvore limpa no início.
Código avaliado inclui alterações locais da 08, identificadas por hash em
`.local/etapa08/engineering.json`. Sem commit, push, tag, publicação ou deploy.

SHA-256 do conteúdo após a correção de status:
`dbc52bbd34ff7d64f73db55f7aadc5d70ccd50c6306b160f2c11159f4383021b`.
173 arquivos de engenharia no fingerprint; documentação e next-env.d.ts gerado
ficam fora desse hash. A candidata contém também documentação e hashes por arquivo.
Revisão anterior da integração RTMO:
`17d8cfcf12dce20fa271de96819f70a46af903390a875348646fa3aa10ae04e0`, 171 arquivos.
O hash anterior d597ed295ea9fe5121b63a0e1895c2e58029b0e858c029e39538cd6c0c175d55
identificava 168 arquivos antes do adaptador RTMO; evidência anterior arquivada.

Windows 11 Pro 10.0.26200 x64, PowerShell 5.1; Ryzen 5 5625U, 6 núcleos/12 threads,
15,4 GiB RAM; Node 24.22.1, pnpm 10.34.7, Python 3.12.15, uv 0.13.4;
Docker Engine 29.1.3, PostgreSQL 17.11. Full/Lite e seus gates preservados;
ONNX Runtime 1.23.2 e opção experimental RTMO descritos no complemento.

## Resultado entregue

Complemento de 23/10/2026: adaptador RTMO-s integrado, qualidade explicitamente
distinta e contrato compartilhado/API/web compatíveis com confidence. Full/Lite
preservados e configurações do fundador mantidas. Comparação nativa em 20 clipes,
40 execuções/1552 inferências, 8/12 eventos Full/RTMO. As três perdas continuam
registradas; dados de calibração não aprovam eficácia independente. Detalhes,
arquivos, comandos e verificações da revisão em
[INTEGRACAO_RTMO_ETAPA_08](INTEGRACAO_RTMO_ETAPA_08.md). O texto abaixo preserva
a cronologia anterior: RTMO era apenas pesquisa naquele momento.

Verificação geral da integração RTMO, antes da correção de status:
demo:verify exit 0, 14 jobs; 283 Python,
155 API, 100 contratos TS (e 100 Python incluídos nos 283), 20 E2E e quatro
testes do simulador. Backup/restore e instalação limpa passaram. Vinte envelopes
nativos reais também passaram nos validadores Python e TS/AJV, sem HTTP.
Docker Desktop estava fechado na primeira tentativa da API; iniciado normalmente
em segundo plano e execução geral repetida. Nenhum requisito foi ignorado.
Gates manuais e qualidade da percepção continuam pendentes, releaseReady=false.

Investigação posterior da cadeira: teste nativo de segmentação do Full não
forneceu verificação independente suficiente; a máscara também incluiu a
estrutura da cadeira. RTMO-s foi testado em projeto uv privado isolado, com
lock próprio e somente opencv-contrib-python fornecendo cv2. Foram 210
inferências em seis clipes, sem eventos/HTTP ou troca do worker. Comparação visual
chair08-02 usou observações Full originais e quadros de pixels idênticos, 32/32
confirmados por SHA-256. Fundador assistiu e confirmou melhora das pernas sem
associação ao pé traseiro da cadeira. Média RTMO 126,49 ms, P95 152,15 ms;
dois tempos acima de 200 ms. Melhora visual localizada, sem eficácia estimada.
Integração operacional permanece pendente: score RTMO não pode ser apresentado
como visibility/presence do MediaPipe, nem preencher pontos ausentes para fazer
o motor passar. Não foi entregue uma substituição no pipeline atual. Fontes,
comandos, artefatos, custos e próximos critérios técnicos em
[INVESTIGACAO_CADEIRA_ETAPA_08](INVESTIGACAO_CADEIRA_ETAPA_08.md).

Revisão de chair08-02 identificou falha relatada pelo fundador: pontos do corpo
sobre estrutura da cadeira ao sentar de lado. Reaplicação nativa das observações
salvas, sem inferência nova/HTTP/outbox: uma pose em 32/32, 31/32 elegíveis,
zero candidatas/emissões. Renderizações privadas em 3024/4000/6000 ms auxiliam
a inspeção; não há anotação articular quantitativa. Piso e cena negativa integral
não confirmados: caso não marcado como aprovado. Evidência de limitação da pose
mesmo com confiança técnica suficiente; nenhuma alteração de detector aplicada.

Posteriormente, fundador confirmou piso correto e ausência de pessoa deitada na
cena inteira de chair08-02, ciente de que o esqueleto continuava sem correção.
Registro humano/manifesto negativos gravados antes do teste completo; evaluate
do segundo via uv frozen retornou 0: Full/motor reais, sem HTTP e com fila nova,
zero eventos, 6208 ms observados, 5808 ms elegíveis, cauda 98 ms. Resultado privado
f16e47b6-2ef1-460e-a318-f58b7f7e7e41/evaluation.json. Dois ensaios de sentar
somam 15424 ms observados e 14432 ms elegíveis; zero eventos é compatível com
essas cenas, sem corrigir a pose ou concluir a avaliação independente. Mantida
classificação CALIBRATION por mesma origem de grupo, sessões não confirmadas.

Fundador informou que não assistiu à reprodução integral de chair08-02 e pediu
reabertura. Reaberta por Start-Process/uv a mesma prévia FILE poses-only, pausada
a 0,5x, com logs privados novos. Confirmação de piso/cena integral continua
pendente; nenhuma anotação negativa completa foi atribuída a essa resposta.

Recebidos depois dois vídeos de sentar na cadeira: hashes correspondem exatamente
a GMDCSA24 Subject 1/ADL/11.mp4 e 13.mp4. Preparação Python com uv frozen copiou
bytes por SHA, decodificou 277/187 frames e gerou contatos privados, sem inferência.
Configurações e anotações provisórias separadas; mesma origem de grupo já usada,
CALIBRATION_CONFUSER, sem independência confirmada. Iniciada por Start-Process/uv
a calibração FILE de chair08-01 em cópia privada. Piso, anotação humana integral
e execução do detector nesses novos arquivos ainda pendentes. Depois, fundador
salvou o piso v1 de chair08-01, dez pontos. Prévia Full poses-only aberta pausada
a 0,5x para revisão integral, sem motor temporal ou HTTP. Sem aprovação negativa
por ausência de alerta em prévia. Depois o fundador confirmou a cena negativa
integral e o piso do primeiro; prepare-chair01-evaluation.py registrou isso antes
de evaluate, ambos via uv frozen com exit 0. Full/motor reais, sem HTTP, zero
eventos; 9216 ms observados, 8624 ms elegíveis, 98 ms de cauda não observada.
Resultado privado df336f4b-9549-4fa3-95cd-c1d2e56ffe91/evaluation.json. Somente
ensaio curto de calibração, sem taxa geral de falsos alertas. Aberta calibração
GUI do segundo (chair08-02/config.yaml); fundador salvou v1 com nove pontos.
load_calibration validou o arquivo e abriu-se prévia Full poses-only, pausada
a 0,5x, com logs privados próprios. Conferência integral, anotação negativa
humana e teste temporal do segundo ainda pendentes. Detalhes no
[inventário de materiais](MATERIAIS_ETAPA_08.md); nenhum dado enviado à API.

Comparação posterior de Full e Heavy concluída em 17 clipes, com inferência e
motor reais, sem alterar gates nem configurações operacionais. Heavy não recuperou
os três perdidos, gerou 3 eventos contra 7 do Full e teve média de inferência
62,43 ms contra 27,21 ms. Não adotado; percepção ainda não aprovada. Método,
hashes, licença, recursos, comandos e resultados na
[comparação de pose](COMPARACAO_POSE_ETAPA_08.md). Ambos comandos exit 0.

Complemento após o fundador fornecer novos vídeos: [MATERIAIS_ETAPA_08](MATERIAIS_ETAPA_08.md)
registra 23 novos arquivos, fontes/hash/licenças, calibração separada de avaliação,
replay integral dos dois longos, comparação 5/15 Hz e resultados desfavoráveis.
Nenhuma mudança no detector/gates/pesos foi aplicada. Arquivos históricos de nomes
substituídos foram recuperados por SHA em novos caminhos; dados existentes intactos.

Matriz de aceite e relatório final com separação de engenharia, percepção e valor
assistencial. Comandos de diagnóstico/validação, instalação em diretório novo,
backup PostgreSQL e outbox SQLite sem mídia, restore isolado com revogação/redação,
configuração física separada, monitor de recursos/saúde e roteiro de apresentação.
Candidata v0.1 local, explicitamente parcial; não há nova funcionalidade de produto.

As regressões exercitaram implementações reais, migrações SQL e bancos exclusivos.
Reexecução dos seis arquivos históricos de calibração com Full mantém um positivo
no antigo 07 aos 6000 ms e cinco sem evento, inclusive após recuperar os arquivos
por hash em caminhos separados. Inicialmente não havia material independente;
o complemento acima registra a avaliação posterior dos novos curtos, com perdas
e anotações ainda provisórias. O fundador hoje não pode fazer o teste físico. Nenhuma
webcam/pessoa foi aberta para compensar isso, nenhum evento LIVE foi artificialmente
injetado para satisfazer o gate e nenhum limiar foi reduzido.

## Arquivos e decisões

- `scripts/validation/{check,verify,source}.mjs`: pré-requisitos, execução real de
  checks/logs/códigos, hash de fonte e gates manuais separados. Exit 2 significa
  engenharia aprovada com liberação final pendente; --engineering limita o escopo.
- `scripts/validation/clean-install.mjs`: snapshot do código atual sem privados,
  locks, ambiente novo, banco/migrações/bootstrap, web/API/proxy e Full reais.
- `scripts/backup.mjs`: dump custom/hash/prazo, recusa cliente ativo, restore novo,
  revoga sessões/bearers, expira mídia e reaplica retenção antes de servir HTTP.
- `scripts/validation/test-backup.mjs`: prova integrada sintética de restore,
  relações, inicialização, autenticação, redação, auditoria e deduplicação.
- `services/edge/src/radar_edge/backup.py`, CLI e `tests/test_backup.py`: cópia
  SQLite consistente com locks, sem JPEG, preservando pendentes/checkpoint; restore
  em destino novo sem abrir fonte ou enviar HTTP.
- `evaluation.py`/`test_evaluation.py`: origem/autorização/confundidores/motivos,
  modelo/piso no resultado, perdas somente com anotações completas; recusa
  arquivo repetido e vazamento de sessão entre calibração e avaliação.
- `scripts/validation/{prepare.py,observe.ps1,package.mjs}`: preparação preservando
  originais, fila/piso próprios, coleta sem vídeo e candidata privada com hashes.
- `package.json`: demo:check, demo:verify, demo:install-check, demo:package,
  backup:create, backup:restore e test:backup, sem dependências novas.
- README/status, matriz, operação/backup, apresentação, roteiro 08 e inventário.

Sem migração, mudança de schema HTTP, nova família de modelo, biblioteca, política
ou lockfile. Snapshot permanece skeleton/false na webcam. Nenhum purge/backup foi
executado nos dados do fundador. PG 15432, PG 5432, proprietário, credenciais,
calibrações, outboxes e volume existentes preservados.

## Verificações reais

Leituras/inventário por Get-Content, rg, git status/log e CIM; prompt anexado,
AGENTS, README, STATUS, etapa 08, docs 01–10, relatórios 00–07, inventário e roteiros
foram consultados. Existência documental não substituiu reexecução dos checks.

| Comando/ação executada | Resultado | Evidência/limite |
| --- | --- | --- |
| `. ./scripts/activate.ps1`; versões Node/pnpm/uv/Docker; CIM; docker ps | Ambiente acima, banco pessoal saudável 15432 | Sem alterar ferramentas globais ou serviço 5432 |
| `pnpm.cmd install --frozen-lockfile`; `uv sync --project services/edge --frozen` | Aprovados | Locks preservados |
| `pnpm.cmd test:contracts` | 91 TS +91 Python aprovados | Compartilhados, não somar Python novamente |
| `pnpm.cmd test:demo` | 4 aprovados | Transporte artificial separado da percepção |
| `pnpm.cmd test:api` | 145 aprovados | 19 acesso +16 evidência +108 eventos +1 edge +1 resiliência |
| `pnpm.cmd test:e2e` | 18 aprovados, desktop/móvel | Banco/API/web/contas sintéticas, sem usar conta pessoal |
| `uv run --project services/edge --frozen pytest services/edge/tests -q`, RADAR_TEST_GUI=1 | 266 aprovados, sem skips | Inclui 2 backup e 2 avaliação novos; janela GUI sintética |
| `pnpm.cmd lint`; `pnpm.cmd typecheck`; `pnpm.cmd build`; `pnpm.cmd lint:edge`; `pnpm.cmd check:edge` | Aprovados | ESLint/Prettier/TS/Ruff e imports reais |
| Ruff check/format em `scripts/validation/prepare.py`; parser PowerShell em observe.ps1 | Aprovados | Monitor não executado fisicamente |
| `pnpm.cmd test:backup` | Aprovado após correções abaixo | Dump/restore reais exclusivos, login, credenciais revogadas, snapshot 410, pose/recibo redigidos, duplicação impedida |
| `pnpm.cmd demo:install-check` | Aprovado após separar NODE_ENV | Instalação/venv novos, caches externos declarados, modelo oficial novamente obtido/verificado, sem privados copiados |
| `uv run --project services/edge --frozen radar-edge evaluate --manifest .local/evaluation-full.json` | Exit 0, seis CALIBRATION, um evento aos 6000 ms | Não conta como avaliação independente; sem HTTP |
| `uv run --project services/edge --frozen python scripts/validation/prepare.py` | status ok, câmera/credenciais não abertas | Arquivos originais preservados; copia referência privada, não valor do token |
| `node --env-file=apps/api/.env .local/etapa07/project-inventory.mjs` | Contagens pessoais preservadas | Somente contagens; não leu senha/hash/pose pessoal |
| `pnpm.cmd demo:verify` | Executa a matriz automatizada com logs por comando | engineering.json registra revisão alterada/hash; não aprova gates físicos |
| `pnpm.cmd demo:check --engineering`; `pnpm.cmd demo:check` | Exit 0 e exit 2, respectivamente, conforme esperado | Engenharia aprovada nesta revisão; release continua pendente |
| Injeção de hash desatualizado em engineering.json, seguida de restauração | demo:check --engineering recusou com exit 1; registro original voltou a exit 0 | Não aceitou resultado de código diferente |
| `pnpm.cmd demo:package` | Exit 0, snapshot de 217 arquivos versionáveis, releaseReady=false | Candidata privada em .local/releases/v0.1-candidate-<uuid>, sem publicação |
| Auditoria UTF-8/artefatos/links e sentinelas; `git diff --check` | 27 arquivos candidatos, sem artefatos privados, links quebrados ou sentinelas nos logs verificados | Não procurou/expôs valores privados reais; locks intactos |

Logs privados `.local/etapa08/verify-*.log`, `verification.log`,
`evaluation-calibration.log`; resultados `engineering.json`, `clean-install.json`
e `backup-test-<id>/result.json`. A candidata local registra os arquivos efetivos
e seus hashes; não contém mídia, modelos ou credenciais.

Contagens pessoais consultadas: 1 tenant, 1 usuário, 3 locais, 4 câmeras, 4 devices,
3 incidentes, 3 recibos e 27 auditorias. Não houve reset, revisão automática dos
incidentes pessoais, rotação de bearer, mudança de origem, firewall ou rede global.

### Rodada posterior com os novos materiais

Comandos, caminhos privados e resultados detalhados no
[complemento](MATERIAIS_ETAPA_08.md). Executados com uv frozen: run-shorts.py,
evaluate do manifesto reservado, run-long-quality.py, run-yoga-window.py,
compare-tracking.py e evaluate do manifesto histórico recuperado; todos exit 0.
O código de saída confirma execução, não qualidade de detecção: o conjunto
reservado teve uma detecção e três perdas entre quatro alvos provisórios, além
de três posturas curtas/limítrofes. Não houve envio HTTP desses ensaios.

Depois da investigação, `pnpm.cmd demo:check --engineering` continuou com exit 0
e `pnpm.cmd demo:check` com exit 2 (gates manuais pendentes). Não se repetiu a
suíte completa sem mudança de código: o fingerprint de engenharia aprovado
permanece o mesmo. Auditoria Python de UTF-8/links/candidatos e hashes dos 23
novos arquivos/cópias privadas passou; 28 arquivos alterados/novos e 218 candidatos
versionáveis, sem mídia privada entre eles. `git diff --check` passou; avisos de
normalização CRLF/LF foram informativos. Consulta somente de contagens pessoais
reconfirmou os mesmos 1/1/3/4/4/3/3/27. Docker mostra apenas radar-postgres-1
saudável, loopback 15432. Nenhum teste físico foi atribuído a essa rodada.
`pnpm.cmd demo:package` também foi reexecutado: exit 0, 218 arquivos na candidata
privada atualizada, releaseReady=false, mesmo hash de engenharia. A candidata
anterior de 217 arquivos permanece como registro da rodada anterior.

## Falhas encontradas e corrigidas

Revisão posterior do novo 03.mp4: feedback visual do fundador e análise por
amostra documentados em [materiais 08](MATERIAIS_ETAPA_08.md). Preparada cópia
privada para remarcação do piso, com eventos desabilitados, sem sobrescrever
configurações/resultados originais. A análise Python reaplicou features/gate
a observações existentes: 11/13 amostras finais com qualidade insuficiente em
joelho/tornozelo; duas candidatas já dentro do piso. Ainda não corrigida a perda;
nenhum ganho de estabilidade alegado. Nenhum código de produto mudou nessa revisão.
`radar-edge doctor --config .local/etapa08/new-media/review-intake08-02/config.yaml`
passou com inferência real e piso compatível, sem webcam. `pnpm.cmd demo:check
--engineering` e `git diff --check` retornaram 0 após o registro. A nova marcação
foi concluída pelo fundador na GUI: versão 2 com sete pontos. Reaplicação nativa
das mesmas observações manteve duas candidatas, onze inválidas na janela final
e nenhum evento no vídeo com ambos os pisos; não houve nova inferência nesse
comparativo, HTTP ou escrita na outbox. A prévia FILE revisada foi iniciada
por Start-Process/uv, pausada e a 0,25x, poses-only, com logs privados próprios;
fundador confirmou depois que o novo contorno corresponde ao piso. Diagnóstico
privado static-pose-diagnostic.py executado com uv frozen, exit 0: 30 inferências
reais de pixels idênticos com relógio artificial, sem motor/HTTP; pontos válidos
estáveis após aquecimento, mas joelho/tornozelo insuficientes nas 30 amostras.
Não é ganho de estabilidade comprovado em vídeo. Trechos finais de 05/07 também
apresentam baixa visibility em joelho/tornozelo, sem poses elegíveis; detalhes
e denominadores no complemento. 07 reprocessado em cópia poses-only sem GUI,
exit 0; prévia do 05 iniciada pausada para revisão humana. Nenhuma modificação
de produto, dependência, peso, threshold ou outbox operacional.

Revisão humana do 05: esqueleto considerado razoável, ROI v1 reprovada por
incluir parede. Rejeição registrada em arquivo privado e relatório de materiais;
o resultado congelado permanece provisório, sem apagar a falha da calibração.
Iniciado por Start-Process/uv o comando calibrate --config
.local/etapa08/new-media/review-intake08-05/config.yaml --frame-ms 0, somente
FILE na cópia privada, com logs próprios. Fundador salvou v2 com sete pontos.
Comparação nativa das mesmas observações com v1/v2: 13/13 amostras finais
inelegíveis e nenhum evento com ambos os pisos, sem inferência nova ou outbox.
Abriu-se a prévia v2 pausada a 0,25x, poses-only; o fundador confirmou o alinhamento
do novo piso. A janela própria foi fechada por CloseMainWindow após verificar
a árvore do processo registrado, sem contabilizar replay completo. Iniciada
por Start-Process/uv a prévia --poses-only --preview-paused --replay-speed 0.25
da configuração .local/etapa08/new-media/review-intake08-08/config.yaml (07.mp4);
conferência humana ainda pendente. Nenhuma webcam, API ou envio acionado.

Na retomada solicitada pelo fundador, conferiu-se que a prévia anterior do 07
estava encerrada com status ok, sem confirmação humana registrada. Reaberta
a mesma cópia FILE por Start-Process/uv com --poses-only --preview-paused
--replay-speed 0.25, com novo diretório privado de logs e sem alterar calibração,
modelo ou gates. Aguardar conferência do piso e da pose antes de registrar aceite.

Revisão do 07 recebida: fundador considerou o esqueleto bom para MVP e solicitou
remarcação do piso. Registro privado preserva ausência de confirmação de pernas/pés
inteiros e horários. Iniciado Start-Process/uv calibrate --config
.local/etapa08/new-media/review-intake08-08/config.yaml --frame-ms 0, FILE na
cópia privada. Fundador concluiu: piso v2 com oito pontos. Comparativo nativo
das mesmas observações com v1/v2 manteve 14/14 amostras finais inelegíveis
e nenhum evento no vídeo. Não houve nova inferência ou alteração de fila nesse
comparativo. Prévia v2 aberta por Start-Process/uv, poses-only, pausada a 0,25x;
fundador confirmou depois que o contorno do piso está correto. As três
remarcações (03/05/07) ficam confirmadas visualmente. Executado evaluate
--manifest .local/etapa08/new-media/review-floor-v2-manifest.json: exit 0,
Full/inferência/motor reais, filas exclusivas e sem HTTP, zero eventos nos três.
O manifesto de diagnóstico separado usa CALIBRATION/anotações incompletas,
preservando avaliação congelada. Resultado privado
.local/evaluation/070c7242-8e3e-4188-bd0e-37adcc7fef98/evaluation.json.
demo:check --engineering continuou exit 0. A perda de percepção não foi corrigida;
nenhuma mudança de modelo, política ou threshold. Etapa permanece PARCIAL.
Nenhuma mudança no modelo, gates, resultado congelado ou outbox operacional.

1. Novo teste de backup chamou `process` em vez de `TemporalEngine.step`; corrigida
   a fixture para a API real, sem alterar motor/gates.
2. Cópia SQLite tinha bytes JPEG antigos até consolidar WAL; adicionados fechamento
   explícito e checkpoint TRUNCATE após remoção/VACUUM. Teste de bytes sintéticos
   passou preservando original/pendente/episódio ativo; sem promessa forense.
3. Import direto do caminho interno de Sharp não existia; resolução passa pelo
   package.json da API, compatível com o pacote instalado.
4. Restore tentou usar pg_restore enquanto a imagem ainda atendia pelo socket
   temporário de inicialização; esperar readiness TCP corrigiu o teste real.
5. Primeiro build limpo herdou NODE_ENV=development da API e falhou em useContext
   no prerender Next. Build/start web agora usam production; API local conserva a
   exceção HTTP development restrita a loopback. Não mudaram React/Next.
6. Formatação/imports corrigidos após Ruff/Prettier. Avisos preexistentes de ESLint,
   scripts opcionais bloqueados e VM modules permanecem documentados.

## Critérios, pendências e reprodução

**Histórico do registro inicial:** a tabela abaixo precede os testes LIVE,
offline e CAUCAFall e as decisões D50/D51. Não representa a pendência atual;
consultar o início deste relatório, STATUS e matriz para o estado vigente.

A [matriz final](VALIDACAO_MVP.md) é a referência por critério, método e evidência.
O [roteiro 08](../VALIDACAO_MANUAL_ETAPA_08.md) permite iniciar projeto, conferir
checks, preparar piso, medir sessão, revisar incidentes e reunir novas cenas.
[Operação/backup](../OPERACAO_E_BACKUP.md) e [apresentação](../ROTEIRO_APRESENTACAO.md)
contêm comandos e comportamento esperado.

| Gate pendente | Por quê | Ação exata | Evidência esperada |
| --- | --- | --- | --- |
| Coleta/anotação independente | Sete curtos reservados avaliados com anotações provisórias; faltam revisão e negativos | Revisar piso/intervalos do novo conjunto; completar oito confundidores anotados; preservar separação de calibração | Hash/origem/autorização, sessões honestas, intervalos completos, contagens e perdas |
| LIVE positivo e revisão humana | Fundador indisponível fisicamente hoje | Calibrar .local/etapa08/webcam.yaml; executar observe.ps1; postura segura já no chão | Evento por visão LIVE, incidente, sinais, confirmação humana/auditoria |
| 30 min contínuos | Não foi realizado; sessões antigas são curtas | Mesmo monitor, sem pausas, ≥1800 s observados e anotação dos cenários | Relatório, recursos/saúde, tempo elegível/inválido, FPS/descarte/CPU/RAM, erros/fila e revisão de perdas |
| Sem internet | Rede global preservada; preparo foi online | Fundador desconecta acesso externo, mantém loopback e repete fluxo preparado | Acesso externo falha, API/web/modelo/entrega/revisão locais funcionam; horários/alcance registrados |
| Demo e revisão FILE | Roteiro preparado; não apresentado hoje | Executar roteiro 5–7 min e registrar revisão real no painel | Fundador consegue operar/parar/retomar e mostrar limites sem auxílio oculto |

Naquele registro, nenhum gate obrigatório havia sido removido. As revisões
posteriores explícitas do fundador estão em D50/D51. zeroDenominator=null; **não estimável**
para eficácia independente, falsos alertas/hora LIVE e latências humanas ainda não
medidas. Snapshot sintético não conta como câmera; o antigo 07.mp4 continua calibração.
Limitações de estante/perspectiva/perdas continuam explícitas. Valor assistencial
e comercial não foi validado. Não alegar conformidade legal ou ausência de SDK
telemetria por funcionamento normal.

## Próxima etapa elegível

O registro inicial de pendências acima é histórico; fechamento e limitações
atuais estão no início deste relatório. Etapa 09 é opcional, não iniciada e
depende de nova solicitação. Não executar o backlog automaticamente.
