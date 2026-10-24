# Validação do MVP de bancada v0.1

**Decisão final — 24/10/2026: CONCLUÍDA NO ESCOPO REVISADO DA BANCADA
(D50/D51).** Demonstração local experimental. Engenharia e fluxos reais
comprovados nos limites abaixo, percepção com perdas conhecidas e valor
assistencial/comercial não validado. Sem publicação ou avanço automático à 09.

Sessão D51 final: 600,660 s totais, 597,453 s entre análises, 576,986 s elegíveis,
20,467 s inelegíveis, 2799 análises, zero eventos/reconexões e ENDED aceito.
Fundador confirmou fechamento automático e Fonte encerrada. Relatou rede,
polichinelos e trecho no chão <10 s com corpo enquadrado, sem alerta: possível
perda/inconclusivo, sem tempo exato/ROI do quadril ou observações individuais
para reconstrução. Não afirmar acerto nesse trecho ou taxa geral de falsos alertas.
[Medições, auditoria e conferência humana](SESSAO_WEBCAM_10MIN_ETAPA_08.md).

Avaliação CAUCAFall executada, candidato congelado e revisão humana anterior:
3/4 alvos detectados, uma perda, zero alertas nos oito ADL, zero duplicações.
107600 ms elegíveis em 142000 ms observados, mais 1800 ms de caudas sem amostra.
Perda por geometria projetada 2D em FallLeftS9, mesmo com quadril no piso.
Nenhuma correção comprovada; amostra pequena, uma sala, quatro categorias ADL.
[Resultados, protocolo, falha e inventário](CAUCAFALL_ETAPA_08.md).

Última revisão de engenharia (estabilização opcional): 14 tarefas demo:verify
aprovadas, 317 Python, 155 API, 100 contratos TS, 20 E2E e quatro testes do
simulador; identidade de 179 arquivos
`a2b76fa33449fac7a438efa10e5470580b6310a6b12530d62bf33790b8aeb991`.
demo:check --engineering exit 0; demo:check exit 2. Fundador conferiu o worker
FILE com inferência durante execução e filtro visual: acompanha bem, movimento
aceitável. Run 5f15051f… ok/ENDED, 32 análises válidas; não comprova webcam.
Filtro opcional, default false, preserva dados brutos/alertas. Métodos anteriores
de fluxo óptico não foram adotados.
[Integração, resultados e limites](EXECUCAO_REAL_E_PREVIA_ETAPA_08.md).
As contagens de revisões anteriores abaixo são históricas; não somá-las.

**Alcance final:** ensaio curto D51 executado/revisado após resolver o conflito
v2/v3 por reset auditado, com backup/histórico preservados. Configuração
`.local/etapa08/webcam-10min.yaml`, RTMO-s/estabilização/piso v3. O teste original
de 30 min não foi comprovado e a falha aos 27min45s permanece; passar 10 min não
comprova correção da falha tardia ou estabilidade prolongada.
Apresentação formal de 5–7 min dispensada por decisão do fundador (D50); roteiro
opcional, sem registrar a apresentação como realizada. Referências históricas
abaixo à obrigatoriedade são superadas por essa decisão.
Avaliação independente exploratória CAUCAFall realizada, com uma perda conhecida;
isso não aprova eficácia geral. O grupo antigo antes reservado ao Full foi usado
posteriormente no diagnóstico/seleção; não avalia independentemente o RTMO.
Auditoria por SHA em `.local/etapa08/perception-split-audit.json`.
LIVE/revisão e offline já atendidos nos limites documentados abaixo.

O checker/manifesto gerados usam lista manual fixa do plano original e
releaseReady=false; não consomem este aceite. Não anunciar aprovação automática.
Esta matriz documenta o fechamento manual no alcance D50/D51. Referências
posteriores a gates pendentes nas revisões datadas são históricas.

Offline em 23/10: replay/entrega/API/painel verificados; fundador confirmou
desconexão e conferência antes de reconectar. Um evento TEST entregue ao
incidente `cbf11212-8a99-444c-89a3-051284628d04`, sem webcam/JPEG. Escopo e
complementos ainda não exercitados no [relatório 08](ETAPA_08.md).

Revisão mais recente (23/10), após correção de status: demo:verify exit 0 em
14 tarefas, 289 Python, 155 API, 100 contratos TS, 20 E2E, quatro testes do
simulador e verificações de lint/tipos/build/restore/instalação. SHA-256
`dbc52bbd34ff7d64f73db55f7aadc5d70ccd50c6306b160f2c11159f4383021b`,
173 arquivos. demo:check --engineering exit 0; demo:check exit 2. A causa do
encerramento físico aos 27 min não foi comprovada; correção de I/O reproduzida
não completa os 30 min nem melhora por si a pose. Relato do fundador e provas em
[estabilidade da webcam](ESTABILIDADE_WEBCAM_ETAPA_08.md). Release PARCIAL.

Complemento 23/10/2026: [integração RTMO](INTEGRACAO_RTMO_ETAPA_08.md) e 40
pipelines nativos em 20 clipes de calibração, com filas isoladas e sem HTTP.
8/12 eventos Full/RTMO, três perdas mantidas, dois vídeos de sentar sem emissão.
Quatro emissões novas não são automaticamente acertos. Melhora da pose na cadeira
confirmada e preservada no adaptador; geometria/piso e eficácia continuam limitadas.
Revisão de engenharia anterior à correção de status aprovada por demo:verify,
14 jobs: 283 Python,
155 API, 100 contratos TS, 20 E2E, quatro testes do simulador, além de
lint/tipos/build/restore/instalação. Fingerprint
17d8cfcf12dce20fa271de96819f70a46af903390a875348646fa3aa10ae04e0, 171 arquivos.
Os registros de testes abaixo preservam também a baseline anterior; não somar
suas contagens às da nova revisão. Aprovação final/percepção continuam pendentes.

Data: 22/10/2026. **Decisão: PARCIAL — candidata local, sem liberação final.**
Engenharia verificada nos escopos abaixo; avaliação independente, webcam positiva,
30 minutos contínuos, operação sem internet e apresentação humana permaneciam pendentes.
Atualização 23/10: ensaio RTMO LIVE curto de 90,48 s produziu um incidente
CURRENT entregue; fundador conferiu pose e sinais no painel e forneceu histórico
de reconhecimento/revisão Postura no chão confirmada, chegando à versão 4.
Fluxo LIVE→incidente→revisão atendido no ensaio curto; 30 min,
avaliação independente, complementos offline e apresentação continuam pendentes.
O fundador informou indisponibilidade física hoje e necessidade de gravar novas cenas.

**Complemento posterior:** o fundador forneceu 23 novos materiais (21 curtos e dois
longos). [Associação de fontes/hashes, licenças e resultados](MATERIAIS_ETAPA_08.md).
Sete curtos do Subject 1 foram mantidos separados dos usados em calibração: uma
detecção e três perdas entre quatro alvos com janela suficiente na anotação
provisória do assistente; três posturas curtas/limítrofes adicionais preservadas.
Confirmação humana e mais confundidores anotados permanecem pendentes. Análise
de 56 minutos de conteúdo de yoga foi REPLAY com medição de poses, sem classificar
a montagem inteira com uma ROI fixa. Não satisfaz o gate de 30 minutos LIVE.

[Relatório 08](ETAPA_08.md) · [Passos para concluir](../VALIDACAO_MANUAL_ETAPA_08.md).

## Revisão, ambiente e método

Base Git `68ac3d60418ecc6b272990f6c48a14c62918ed13`, main. **Código com alterações
locais da 08, sem commit**; não atribuir ao HEAD os resultados do código diferente.
Identidade do conteúdo executado, comandos, duração e logs em
`.local/etapa08/engineering.json`; SHA de código normalizado por CRLF/LF, excluindo
documentação e arquivo next-env.d.ts gerado. Cópia limpa registra sua identidade
em `clean-install.json`; candidata registra hashes individuais em `release.json`.

Windows 11 Pro 10.0.26200/x64, PowerShell 5.1, Ryzen 5 5625U, 6 núcleos/12 threads,
15,4 GiB RAM visível; Node 24.22.1, pnpm 10.34.7, Python 3.12.15, uv 0.13.4,
Docker Engine 29.1.3/Compose 5.0.1, PostgreSQL 17.11. Banco pessoal preservado em
127.0.0.1:15432 e PostgreSQL preexistente 5432 intacto. Chromium dos testes
Playwright 1.64.1, desktop 1440×1000 e viewport móvel 390×844; não aparelho físico.

MediaPipe 1.1.1, único opencv-contrib-python 5.0.0.93, Full CPU/VIDEO, duas poses,
sem máscara. Full float16/v1, SHA-256
`5134a3aad27a58b93da0088d431f366da362b44e3ccfbe3462b3827a839011b1`,
política floor-v0.1 e critérios de qualidade preservados. Não houve ajuste para
forçar detecção, rotação artificial do vídeo ou novo modelo.

## Matriz final de aceite

| Critério | Método | Resultado | Evidência | Limitação/pendência |
| --- | --- | --- | --- | --- |
| Autenticação/sessão/Origin/papéis | API e navegador reais em banco exclusivo | Verificado | test:api, test:e2e | Credenciais sintéticas, não senha pessoal |
| Isolamento de tenant/câmera/imagem | FKs, acesso HTTP, bearer e sessão | Verificado | API acesso/eventos/evidência | Uma UI de tenant; não SaaS operacional |
| Contratos TS/Python | Mesmas fixtures + tipos gerados | Verificado | 100 TS +100 Python | Python desses contratos já integra a suíte total |
| Motor temporal, qualidade e rearmamento | Fixtures de observações e regressão FILE | Verificado em engenharia | pytest; engine/features/outbox | Fixtures não certificam percepção |
| Idempotência, concorrência e auditoria | Reenvio/ACK perdido/locks/transações | Verificado | API e probes Python reais | Não é teste de corte elétrico |
| Outbox/restart/API indisponível | SQLite + processos Python/Nest exclusivos | Verificado | Testes edge/resilience | Webcam positiva permanece separada |
| Frames novos e saúde | Falhas/slots/relógio/pausa/retomada | Verificado nos adaptadores e ensaio LIVE curto | pytest/API e histórico físico 06/08 | Não substitui continuidade de 30 min |
| Evidência opt-in/acesso/exclusão/retenção | JPEG sintético, relógio injetado, navegador | Verificado | 16 evidência API, testes Python/E2E | JPEG real/purga pessoal continuam desabilitados |
| Logs sem segredos fictícios | Sentinelas nos testes e busca nos logs | Verificado no escopo dos testes | Logger/evidência/acesso | Não auditoria geral do SO/SDK |
| Lint/tipos/build/imports/locks | Comandos reais registrados | Verificado | demo:verify | Avisos de dependências existentes registrados |
| Instalação em pasta/banco vazios | Cópia atual, frozen, migrações, seed, API/web/Full | Verificado | demo:install-check | Mesmo Windows/caches, internet disponível no preparo |
| Backup e restore isolado | pg_dump/pg_restore + SQLite backup | Verificado | test:backup e pytest backup | Dados sintéticos; sem backup pessoal ou desastre físico |
| Arquivo → visão → evento | Full nos seis arquivos históricos, inclusive cópias recuperadas por hash | Verificado em calibração | evaluation-calibration.log e recovered-legacy/evaluation.log | Um positivo aos 6000 ms, cinco sem evento; sem anotações completas |
| Arquivo → incidente → revisão humana | Percurso real 05 e tela conferida | Verificado em calibração | Incidente histórico 6cfd7d88… e investigação 05 | Não exigir repetir o percurso; apresentação formal dispensada D50 |
| Cenário alvo e confundidor independentes | CAUCAFall novo, candidato congelado e revisão humana anterior | Avaliação exploratória executada; uma perda | CAUCAFALL_ETAPA_08; evaluation 590d9698… | 3/4 alvos; zero alertas em oito ADL, só 69 s elegíveis nos negativos; mesma sala e quatro atividades. Não comprova eficácia geral. Grupo histórico continua CALIBRATION |
| Prévia estabilizada no worker FILE | Inferência durante execução e conferência do fundador | Verificado neste arquivo | Run 5f15051f… e human-review.json | Melhoria visual; não corrige perdas do detector nem comprova FPS LIVE |
| Evento LIVE por visão → incidente → revisão | Webcam 0/DSHOW, RTMO, piso v2; 90,48 s | Verificado neste ensaio | Incidente 4e6f8c4b…; histórico do painel fornecido pelo fundador, reconhecimento/revisão até v4 | Postura voluntária confirmada, sem queda; não comprova eficácia geral ou 30 min |
| Webcam contínua ≥30 min — critério original, duração revista em D51 | RTMO físico + monitor de recursos | Não aprovado: encerrou em 27 min 45,64 s | Sessão continuous-d0ff0c09… e relatório ETAPA_08 | PROCESSING_ERROR sem causa histórica comprovada; 7906 análises, zero eventos; fundador relatou cadeira/pés apoiados e oscilação da pose. Resultado histórico preservado |
| Ensaio curto de 10 min nominais — D51 | Webcam 0/DSHOW, RTMO-s, estabilização, piso v3 e monitor | Verificado: 600,660 s e encerramento normal confirmado pelo fundador | continuous-4d4357f7…; diagnóstico 3192ea80…; relatório SESSAO_WEBCAM_10MIN | 597,453 s observados, 576,986 s elegíveis, zero eventos. Trecho no chão <10 s sem alerta inconclusivo/possível perda. Não comprova 30 min ou correção da falha tardia |
| Execução sem internet | Desconexão confirmada pelo fundador, tentativa externa falhou, loopback preservado | Verificado para replay/entrega/consulta API e painel | offline-check-865f2042…; incidente cbf11212… | Não exercitados webcam, novo login, ação humana e reenvio durante desconexão; não é auditoria de telemetria |
| Apresentação formal 5–7 min pelo fundador | Roteiro opcional; operação exercitada durante desenvolvimento | DISPENSADA pelo fundador | D50 em decisões, 23/10/2026 | Não executada; não altera gates de percepção, engenharia ou continuidade física |
| Câmera IP/KAP-S069 | Etapa 09 opcional | Fora do gate | Plano mantido | Não implementada/testada |

Qualquer falha crítica futura de acesso, perda silenciosa ou uso de frame antigo
impede liberação. Os testes atuais não encontraram essas falhas no escopo exercitado;
não se promete ausência universal de falhas.

## Material realmente disponível e resultados desfavoráveis

Inventário inicial desta rodada, antes do novo fornecimento: sete arquivos únicos
no diretório autorizado, seis descritos como filmagens reais
e um confirmado como gerado por IA. Os seis reais já foram usados na investigação
e seleção do Full: **CALIBRATION**, não EVALUATION. A quantidade de pessoas/sessões
independentes não foi confirmada. Os pseudônimos antigos são identificadores,
não prova de participantes diferentes. Naquele momento ainda não havia material
novo. O complemento posterior acima registra os 23 recebidos, sem apagar a medição
histórica nem reutilizar calibração como teste independente.

Hashes, origem declarada, termos/ausência de URL e calibrações anteriores estão no
[inventário](DEPENDENCIAS_E_MODELOS.md) e na [investigação 05](INVESTIGACAO_ETAPA_05.md).
O pedido autoriza processamento local; redistribuição/treinamento não foram
presumidos. Vídeos, nomes originais, manifestos e outboxes permanecem privados.

Reexecução histórica desta rodada `evaluate --manifest .local/evaluation-full.json`, Full, 5 Hz,
sem HTTP, saídas novas, sem alterar outboxes operacionais:

| ID | Análises | Tempo observado (ms) | Elegível (ms) | Eventos | Inferência média (ms) |
| --- | ---: | ---: | ---: | ---: | ---: |
| bancada-01 | 89 | 17618 | 15216 | 0 | 36,17 |
| piso-a | 109 | 21600 | 600 | 0 | 28,58 |
| piso-b | 73 | 14417 | 0 | 0 | 29,13 |
| piso-d | 78 | 15401 | 8554 | 0 | 29,99 |
| piso-e-05 | 51 | 10016 | 1408 | 0 | 30,06 |
| piso-f-07 | 45 | 8816 | 7200 | 1 | 28,11 |

445 análises; **87,868 s observados, 32,978 s elegíveis**. São somas dos intervalos
entre observações conforme o motor, não 30 min de câmera nem exposição independente.
Diferença 54,890 s inclui qualidade insuficiente e lacunas. Cada relatório detalha
motivos e cauda não observada; contagens de motivos podem se sobrepor e não devem
ser somadas como duração. O positivo continua PERSON_ON_FLOOR aos **6000 ms**.
Não foi observado rótulo POSSIBLE_FALL nesses replays. Sem quedas reais anotadas,
recall de queda real não é estimável.

Resultado privado:
`.local/evaluation/f37a91d2-e9fa-4ca3-83e3-357a345ae03f/evaluation.json`, cópia de
consulta `.local/etapa08/calibration-evaluation.json`.
AnnotationsComplete=false: recall, precisão, perdas anotadas, duplicações por alvo
e falsos alertas/hora **não estimáveis**. Um evento em seis arquivos não é “16,7%
de acurácia”; não há denominador de episódios anotados para esse cálculo.

As cenas de pessoa deitada não detectadas continuam registradas: pontos essenciais
intermitentes, vista superior e projeção 2D com tronco vertical. Full melhorou o
07, mas não eliminou essas perdas. A pose falsa na estante e a fluidez em 5 Hz
relatadas na 06 não foram resolvidas/medidas novamente pela 08. Nenhuma afirmação
de necessidade de ajuda foi validada. Deitar voluntariamente pode satisfazer a
postura e continuar sem necessidade assistencial.

## Regras de avaliação e medições restantes

Correspondência predefinida: mesmo kind, emissão no intervalo-alvo ou até 2000 ms
depois do fim, um match por alvo; demais alertas na janela são duplicações.
Intervalos excluídos e anotações incompletas geram inconclusivos. Denominador zero
é null/não estimável. missed só é calculado com anotações completas. O validador
recusa hash repetido e sessão compartilhada entre CALIBRATION/EVALUATION; isso
não detecta automaticamente recortes/parentesco de vídeos, que exigem manifesto fiel.

Meta documental permanece 12 cenas (4 de pessoa no chão e 8 confundidores), com
separação por sessão e papel. Antes do novo fornecimento havia zero vídeos novos;
agora há sete curtos reservados, com rótulos provisórios, mas ainda não oito
confundidores curtos completos/anotados. Não preencher
as 12 vagas com recortes/replays do material de calibração. Anotar primeiro origem,
autorização, hash, sessão/ambiente/pessoa, FPS/duração, alvos, confundidores e
períodos não observáveis. Revisar períodos sem alerta para contar perdas.

Ensaio contínuo LIVE da 08: **não executado**, tempo total/elegível, CPU/RAM,
captura/inferência, frames descartados, eventos, duplicações, erros e outbox
**não medidos**. O histórico de poucos minutos da 06 não atende esse gate.
Monitor preparado amostra a árvore viva de processos por Win32_Process aproximadamente
a cada segundo, CPU cumulativa/working set somado e saúde local com idade. CPU
normalizada: delta CPU/delta parede ×100 (100%=um núcleo); memória pode contar
páginas compartilhadas e CPU de filho encerrado pode desaparecer da soma. Relatório
interno mede processo principal separadamente; não misturar como total do host.
Elegibilidade temporal vem do motor; captura e intervalos sem frame devem ser
reconciliados com as amostras. Monitor sozinho não revisa perdas ou anota pessoas.

Latência confirmada por anotação humana ainda não estimável. No novo recorte
reservado há uma medida provisória de 1608 ms contra anotação do assistente,
com incerteza de aproximadamente 200 ms. No positivo histórico de calibração,
janela candidata interna 2176 ms não é
latência contra ground truth. Transporte/painel atuais não foram medidos por
observação física; polling configurado em 2 s não é uma medição de latência.

## Decisão inicial de 22/10 e próximo passo — histórico superado

Engenharia disponível para bancada e restore reproduzível. **Release v0.1 não
liberada** enquanto faltarem os gates acima. Candidata local de fontes, sem pesos,
vídeos, segredos, dependências ou publicação, preparada por demo:package.

Para concluir: seguir o roteiro 08 com sessão física segura, novos vídeos anotados,
teste offline e apresentação. Reavaliar resultados desfavoráveis sem mudar gates
somente para aprovação. Valor assistencial/comercial, eficácia clínica e piloto
com terceiros continuam não validados. Etapa 09 opcional não bloqueia a bancada.
