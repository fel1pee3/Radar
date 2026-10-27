# Decisões, evolução e relação com o dossiê

[Voltar ao README central](../README.md)

## Decisões em vigor — 21/10/2026

| ID | Decisão | Motivo e consequência |
| --- | --- | --- |
| D01 | Construir demonstração antes de procurar parceiro | Instrução atual do fundador substitui a ordem do dossiê |
| D02 | Fundador pode desenvolver sozinho | Sócio/investidor não são pré-requisitos técnicos; negócio não exige divisão societária para começar |
| D03 | Software primeiro, hardware existente | Webcam e arquivos permitem bancada; câmera própria é hipótese futura |
| D04 | Uma fonte/área/pessoa por vez | Limita custo e deixa falhas observáveis |
| D05 | Pessoa no chão/possível queda é o primeiro caso | Um fluxo concreto antes de múltiplos eventos de segurança |
| D06 | Modelo local de pose + regras | Usa base existente e permite medir limitações sem treinar do zero |
| D07 | Toda plataforma local na v0.1 | Demonstra sem serviço pago ou dependência operacional de internet |
| D08 | NestJS + Next.js + Python | Aproveita o repertório já descrito pelo fundador |
| D09 | PostgreSQL e SQLite; Redis adiado | Duas necessidades duráveis diferentes; fila de avisos simples no banco |
| D10 | Replay, depois webcam, depois IP opcional | Substitui RTSP como única porta de entrada do dossiê |
| D11 | Sem streaming web ou clip contínuo | Reduz armazenamento e exposição; pose e snapshot opt-in bastam para demonstrar |
| D12 | Avisos locais/simulados | Comunicação externa e SLA de atendimento precisam de validação própria |
| D13 | Isolamento preparado, um tenant na UI | Evita reescrever segurança sem construir administração SaaS completa |
| D14 | Regras e evidência versionadas | Permite avaliar mudanças sem reescrever o histórico |
| D15 | Porta do PostgreSQL do Compose configurável por `POSTGRES_PORT` | 21/10/2026, etapa 00: a instalação PostgreSQL existente ocupa 5432. Nesta máquina usar 15432 no `.env` privado; manter loopback e 5432 como padrão do exemplo. Não parar nem alterar o banco existente. Sem mudança de contratos HTTP. |
| D16 | Padrão de desenvolvimento 15432 e bloqueio da porta 5432 do host nos comandos Prisma/API | 21/10/2026, etapa 01: instrução atual do fundador exige preservar o PostgreSQL externo. O exemplo passa a usar 15432 e a validação impede apontar acidentalmente a 5432. Atualiza o padrão inicial de D15; o volume e o `.env` existentes permanecem preservados. |
| D17 | E-mail de login único globalmente, normalizado em minúsculas; bootstrap de um proprietário por tenant | 21/10/2026, etapa 01: login recebe e-mail/senha sem seletor de tenant. Sessões e permissões derivam da conta encontrada. Seed repetido não cria outro proprietário quando o e-mail é alterado na configuração e não redefine senha. Não há gestão pública de equipe. |
| D18 | Diagnóstico autenticado `GET /edge/me`, detalhes de local/câmera e alteração de local | 21/10/2026, etapa 01: explicita autenticação/escopo do bearer antes da ingestão, sem implementar eventos/heartbeat. `GET /sites/:id`, `PATCH /sites/:id` e `GET /cameras/:id` complementam a configuração/leitura mínima com os mesmos gates e scoping. |
| D19 | JSON Schema draft-07 como fonte dos envelopes; Ajv/jsonschema e tipos TS gerados | 21/10/2026, etapa 02: evita validar formatos distintos por linguagem. Limites concretos, precisão UTC em milissegundos e validação adicional de índices de pose estão em 03. OpenAPI declara 3.1 para representar const/condições dos schemas; bearer é opaco, não JWT. |
| D20 | Equivalência de episódio inclui todo o envelope exceto eventId; actionId único por tenant | 21/10/2026, etapa 02: explicita campos imutáveis em vez de escolher silenciosamente um subconjunto de sinais. Hash do actionId inclui incidente/corpo, com retorno original persistido. Locks transacionais e unicidades reais cobrem concorrência. IDs de episódio são escopados à câmera; tentativa fora da credencial é 403. |
| D21 | Último heartbeat na Camera e tombstones mínimos de CameraRun | 21/10/2026, etapa 02: apenas sequence do run atual não impediria um pacote atrasado de run substituído de assumir novamente. IDs/horários sem histórico de payloads impedem essa regressão. ENDED fecha o run; pause/end persistidos exibem idade/stale. Retenção dessas chaves será implementada na 07. |
| D22 | Executor de avisos local com polling de um segundo e transações PostgreSQL | 21/10/2026, etapa 02: entrega SIMULATED + auditoria + status atômicos, retomada na inicialização e locks SKIP LOCKED, sem Redis ou provedor externo. Falhas mantêm PENDING para retry; contagem registra commits, sem backoff exponencial nesta etapa. |

Manter aqui decisões novas com data, problema, alternativas consideradas, escolha e impacto nos contratos. Não reabrir tudo a cada prompt.

| ID | Decisão | Motivo e consequência |
| --- | --- | --- |
| D23 | Listar metadados de credenciais por câmera, exclusivo de OWNER | 21/10/2026, etapa 03: revogação após recarregar precisa de ID/version/revokedAt; GET paginado com guards/scoping existentes e sem token/hash. Não houve alteração de identidade, rotação ou schema do banco. |
| D24 | Sessão e rascunhos em memória; polling sequencial por recurso e fetch no-store | 21/10/2026, etapa 03: evita cache entre contas e perda de texto durante atualização. Sessão expirada oculta dados e permite login da mesma conta; troca de conta/logout desmonta o estado. 409 exige nova intenção; retry transitório preserva actionId/corpo. Sem localStorage de sessão ou segredo. |
| D25 | Simulador Node com câmera dedicada e arquivo privado em .local | 21/10/2026, etapa 03: usa bearer, contratos e endpoints existentes, somente SIMULATED, pose sintética, heartbeat e ENDED; aceita UTF-8/BOM do PowerShell. Nenhum produtor Python, captura, modelo ou outbox foi antecipado. |
| D26 | E2E com build, banco e processos exclusivos | 21/10/2026, etapa 03: Playwright 1.64.1/Chromium, portas temporárias e .next-e2e evitam reutilizar/parar processos do fundador. Falhas são injetadas apenas nos recursos próprios; não se altera PostgreSQL 5432 nem o volume da demo. |
| D27 | Pipeline FILE local com Tasks Lite float16/v1, CPU/VIDEO e até duas poses | 21/10/2026, etapa 04: bundle oficial fixado por SHA-256, sem máscara, landmarks corporais11–32 e valores ausentes null; observações não são envelopes de ingestão. Não implementa decisão temporal, câmera ou transporte. |
| D28 | Amostragem por PTS com fallback CFR explícito e fim conservador | 21/10/2026, etapa 04: falha/repetição de timestamp permite somente índice/FPS válido e crescente; mudança para fallback fica registrada. Não corrigir duração somando tempo de CPU. Falha antes da contagem de frames dá DECODE_ERROR; contagem desconhecida não autoriza afirmar EOF e dá END_UNVERIFIED. Reduz falso sucesso em arquivo truncado; pode exigir normalizar metadados. |
| D29 | Calibração privada revisionada e exportação diagnóstica limitada | 21/10/2026, etapa 04: operador seleciona polígono simples normalizado; câmera/orientação/proporção incompatíveis bloqueiam run. Sem salvar frame por padrão. YAML validado usa PyYAML 6.0.3 safe_load; NumPy 2.5.4 já existente passa a direto. Exportação body-only opt-in limitada por observações/bytes, com truncamento explícito. |
| D30 | Separar processamento local de promessa de ausência de telemetria nativa | 21/10/2026, etapa 04: aviso oficial MediaPipe Tasks descreve métricas de uso; DLL instalada contém referências a Clearcut/play.googleapis.com. Inspeção da API Python não encontrou opt-out. Radar não implementa upload de vídeo/poses nem canal externo; ausência total de tráfego do SDK não foi verificada. Não alterar firewall/rede silenciosamente nem anunciar isolamento de rede comprovado. |

## Decisões da etapa 05

| ID | Decisão | Motivo e consequência |
| --- | --- | --- |
| D31 | Checkpoint transacional por fonte/configuração e replay operacional distinto de evaluate | 21/10/2026, etapa 05: reiniciar um arquivo do zero poderia rearmar e duplicar episódio. SQLite mantém âncora/runId/frame/estado; o prefixo só aquece o rastreador. ACTIVE/REARMING restaura ACTIVE, sem reutilizar janelas anteriores. EOF não reanalisa; reset com motivo retira a execução preservando eventos/histórico. Evaluate usa outra outbox e não envia HTTP. Locks de SO por câmera e outbox impedem concorrência incompatível. |
| D32 | Cobertura conservadora e offset da evidência na emissão | 21/10/2026, etapa 05: janela móvel de 2 s soma apenas intervalos com ambos os extremos candidatos válidos, pelo menos cinco observações e lacuna ≤500 ms; invalidez não prova recuperação. sourceOffsetMs referencia a emissão/evidência; occurredAt continua o início candidato e detectedAt a emissão virtual. Gates experimentais originais preservados; alterar parâmetros exige outra policyVersion. |
| D33 | Entrega local explícita, payload imutável e erros locais persistidos | 21/10/2026, etapa 05: eventos/delivery habilitados em cópia privada, default false mantém comandos da 04. ACK é validado contra evento e classe TEST. Retry/backoff apenas transitório; 401/403 suspende até retomada explícita, permanentes preservam item com motivo. Histórico sem purga automática até 07. Nenhum contrato HTTP/relacional precisou ser alterado. |
| D34 | Full float16/v1 selecionável explicitamente; Lite preservado; geometria floor-v0.1 delimitada à projeção 2D | 21/10/2026, etapa 05: investigação autorizada pelo fundador comparou cinco arquivos com Lite/Full e inferência 5/15 Hz mantendo decisões em 5 Hz, duas poses e gates iguais. Full produziu evento em piso-f-07 (40 observações elegíveis contra 15 do Lite); elevar inferência não resolveu as perdas e aumentou custo. Bundle Full oficial fixado por hash; model.variant/path explícitos e SHA no fingerprint impedem retomar execução Lite como Full. Não mudou dependência nem política para forçar disparo. Outros arquivos continuam sem evento, inclusive pessoa deitada projetada verticalmente. Prévia agora aplica presença e visibilidade, tem pausa explícita e diagnósticos agregados por articulação. Resultados CALIBRATION não são eficácia independente; detalhes na investigação da 05. |

## Decisões da etapa 06

| ID | Decisão | Motivo e consequência |
| --- | --- | --- |
| D35 | Webcam nativa em processo spawn com único slot compartilhado e lock de bancada | 21/10/2026: read/open do driver DSHOW podem bloquear sem timeout portátil garantido. Pai encerra/recria processo e IPC por prazo; filho monitora a morte do pai. Índice/backend explícitos, sem varredura; calibração própria de câmera/índice/geometria. Full CPU/VIDEO obrigatório na webcam, sem reduzir gates. Testes de adaptador não substituem enquadramento físico. |
| D36 | Separar sessão de captura de execução persistente e dois transportes independentes | 21/10/2026: heartbeat ENDED não pode ser reaberto com o mesmo runId. Cada inicialização ganha sessão nova; execução SQLite continua preservando checkpoint, episódio ACTIVE e eventos imutáveis. Heartbeat e entrega têm threads/HTTP/SQLite próprios e não esperam inferência; eventos de runs antigos podem ser reenviados conforme o contrato. FILE preserva tempo de mídia e seus eventos anteriores, sem reclassificar como LIVE. |
| D37 | Limites efetivos e limpeza restrita da outbox na 06 | 21/10/2026: defaults 10.000 itens, 100 MiB incluindo WAL/SHM, reserva de 64 KiB antes de inferir, timeout 5 s e backoff 1–30 s com jitter. Retry-After limitado a 300 s. Purga só de payloads DELIVERED com mais de sete dias e episódio fechado/resetado; chaves e estado técnico preservados. Pendentes/permanentes não são removidos. Não antecipa retenção global/snapshots da 07. |
| D38 | Credencial local por clipboard explicitamente solicitado | 21/10/2026: colagem em Read-Host oculto confundiu o fundador; copiar o comando também substituía o token no clipboard. `setup-worker.ps1 -FromClipboard` espera token válido por até dois minutos após iniciar, sem colar/Enter; somente lê o clipboard quando o fundador invoca essa opção. Saída sem segredo, arquivo só dentro de .local e destino existente preservado. Não cria conta, não rotaciona credencial e não altera cadastro automaticamente. |

## Decisões da etapa 07 — 22/10/2026

| ID | Decisão | Motivo e consequência |
| --- | --- | --- |
| D39 | Modo de evidência opcional no envelope e consentimento OWNER por câmera | Legacy skeleton preserva envelopes/hash antigos. Snapshot exige escolha/autorização na API e flag local separada; sem autorização, metadados continuam aceitos e imagem fica desabilitada. Nenhum vídeo/webcam do fundador foi habilitado para JPEG. |
| D40 | Hash original, imagem normalizada e slot único originário | SHA-256 dos bytes de entrada torna reenvio idempotente; Sharp 0.35.5 valida/reencodifica sem EXIF. Outra chave do episódio não substitui imagem. Deleção/expiração deixa marcador durável; leitura nunca é pública nem cacheável. |
| D41 | Filesystem privado serializado e reconciliação durável | Escrita exclusiva/fsync antes de commit; falha deixa órfão reconciliável. Marcador antes de unlink impede ressurreição. Ausência física inesperada é 503; somente reenvio idêntico ainda autorizado pode reparar arquivo ausente sem renovar expiração. |
| D42 | JPEG pontual em BLOB SQLite, sem arquivo por frame | Até 100 imagens/20 MiB e teto global da outbox. Evento/checkpoint/imagem atômicos, instante igual ao da emissão; upload após ACK do evento. BLOB removido após ACK de imagem ou 24 h; falha de imagem não apaga evento. Formato SQLite v2 aditivo. |
| D43 | Redação de todas as cópias e opt-in operacional para dados existentes | Poses/recibos detalhados 7 dias, imagens 24 h, metadados 30 dias só com preferência OWNER, recibos mínimos 90 dias. Agendamento API default false para não purgar dados existentes automaticamente; comando explícito e job habilitado verificados em isolamento. Supera a exceção de D37 para payload confirmado de episódio ativo: pode expirar em 7 dias porque o checkpoint guarda apenas estado, não pose. Pendentes permanecem imutáveis/limitados. |

## Decisões da etapa 08 — 22/10/2026

| ID | Decisão | Motivo e consequência |
| --- | --- | --- |
| D44 | Engenharia automatizada separada dos gates manuais e revisão por hash de conteúdo | Código local ainda sem commit deve ser identificado além do HEAD. demo:verify registra comandos/saídas; demo:check retorna 2 para gates manuais pendentes, sem declarar webcam/percepção/offline aprovados. Relatórios da 08 ficam PARCIAL pela indisponibilidade física/coleta informada pelo fundador. |
| D45 | Restore somente em banco/diretório novos, com revogação e redação antes de HTTP | Evita sobrescrever bancada, servir imagem ausente/vencida ou enviar com bearer restaurado. Dump custom PostgreSQL e SQLite backup com locks; mídia excluída e estado de episódio/pendentes preservado. Nenhuma cópia de segredo/arquivo pessoal automática. Prazo privado de backup sete dias; sem criptografia/forense prometida. |
| D46 | Adaptador RTMO-s opcional para investigar a cadeira, 23/10/2026 | Melhora visual confirmada motivou integração real FILE/LIVE pela interface existente, ONNX Runtime CPU fixado, sem RTMLib ou segundo cv2. Obtenção explícita e SHA fixado; configurações Full/Lite preservadas. Uso experimental de bancada; licença do código não foi tomada como liberação comercial específica dos pesos. |
| D47 | Score articular separado de visibilidade/presença, 23/10/2026 | Política floor-rtmo-score-v0.1 identifica qualitySource=RTMO_KEYPOINT_SCORE e minKeypointScore. Preserva geometria/persistência e oito pontos essenciais. Evento v1 ganha variante corporal confidence, restrita ao modelo RTMO fixado e à família de política. Envelopes antigos visibility continuam válidos. Atualizar API/web/contracts/Python juntos; leitores antigos não suportam o novo formato. Não inventar visibility/presence, face, dedos ou profundidade. |
| D48 | Priorizar acompanhamento corporal, continuidade e fluidez medidos, 23/10/2026 | O fundador reforçou que deseja um MVP bem executado, com corpo bem acompanhado e prévia estável. Investigar erros de pose e desempenho nos vídeos existentes, preservar resultados desfavoráveis e medir custo real antes de adotar mudanças. Não preencher pontos rejeitados nem confundir desenho suave com precisão ou sucesso dos alertas. A preferência orienta a qualidade; não cria promessa de zero erros ou alteração automática dos critérios de conclusão da 08. [Investigação quadro a quadro](RELATORIOS/QUADRO_A_QUADRO_ETAPA_08.md). |

Na avaliação original não houve mudança de política/modelo/gates. A comparação
posterior RTMO usa qualidade/política distintas, sem reclassificar os resultados
antigos como aprovação do candidato. Os seis vídeos de
investigação permanecem CALIBRATION; arquivos/sessões repetidos não viram amostras
independentes. Novas funcionalidades/expansão não integram esta validação.

## Complemento da etapa 08 — estabilização visual

Complemento de 23/10/2026 — **D49: estabilização somente na prévia, opt-in**.
Após conferência humana do replay e medição cadenciada, incorporar o filtro visual
com `processing.previewStabilization` false por padrão. Pontos ciano não entram
em features, eventos, evidência ou checkpoint. Não alterar frequência de análise
para igualar a aparência do vídeo pré-processado; medir custo e idade real dos
quadros. Parâmetros preservam o candidato conferido, sem preenchimento de pontos
ausentes. [Implementação e provas](RELATORIOS/EXECUCAO_REAL_E_PREVIA_ETAPA_08.md).

## Dispensa da apresentação formal da etapa 08

23/10/2026 — **D50: apresentação cronometrada de 5–7 minutos dispensada pelo
fundador**. O fundador informou que já opera o sistema durante a construção e
não quer uma etapa de aprendizado/apresentação formal. O uso e as confirmações
de login, revisão de incidente e controles durante o desenvolvimento permanecem
como evidências operacionais. O roteiro preparado é opcional e não bloqueia a
conclusão da bancada. Registrar **DISPENSADA**, nunca apresentação executada.

Esta decisão supera as referências anteriores à apresentação como pendência
obrigatória. Não altera o teste contínuo físico de 30 min, os resultados de
percepção, os requisitos de engenharia/privacidade ou o uso pretendido da demo.
Naquele registro, o ensaio de 30 min continuava adiado; a duração foi revista
posteriormente pelo fundador em D51, abaixo.

## Revisão da duração do ensaio físico da etapa 08

23/10/2026 — **D51: sessão nominal de 10 minutos por escolha explícita do
fundador**. O fundador informou que fará somente 10 minutos. Para esta bancada,
substituir o gate de duração de 30 min por um ensaio curto com limite de 600 s
do worker, sem gravar vídeo. Preparação, enquadramento e eventual remarcação do
piso acontecem antes da sessão medida. Não exige deitar novamente: o percurso
LIVE positivo e sua revisão já foram comprovados.

O cronômetro atual começa antes de abrir câmera/carregar modelo. Registrar
separadamente duração total, aquecimento e tempo efetivo com captura/inferência;
600 s configurados não significam 600 s de imagens úteis. Exigir encerramento
normal, relatório de recursos/saúde, intervalos inelegíveis, erros, eventos e fila;
não aprovar só pelo tempo do terminal. Pausa, reinício ou falha não ficam ocultos.

O teste original de 30 min **não foi comprovado**. Sua falha aos 27min45s e a
causa histórica não estabelecida permanecem registradas; passar 10 min não
comprova correção de falha tardia ou estabilidade prolongada. Esta é uma redução
explícita do alcance da evidência por decisão do fundador, não um resultado
positivo do teste original. Modelo, política, qualidade e demais gates mantidos.
A etapa 08 permanece PARCIAL até executar e revisar o novo ensaio. Não libera
piloto assistencial nem avança automaticamente à etapa 09.

Registro de execução de 24/10: D51 atendida em sessão de 600,660 s e encerramento
confirmado pelo fundador, com durações elegíveis/lacunas e limitações anotadas.
Etapa encerrada no escopo revisado da bancada. Houve trecho no chão <10 s sem
alerta, possível perda/inconclusivo; não aprovar eficácia geral por isso.
[Medições e relato humano](RELATORIOS/SESSAO_WEBCAM_10MIN_ETAPA_08.md).

## D52 — evolução funcional do detector, separada da etapa 08

24/10/2026, instrução atual do fundador: desenvolver/investigar núcleo funcional
para um cômodo em incrementos verificáveis, além do diagnóstico enquanto houver
recursos/dados. Preservar 08/D50/D51 e baseline; manter RTMO-s inicialmente.
Treinamento local leve autorizado somente se justificado e com permissão dos
materiais verificada, sem usar avaliação reservada ou dividir quadros do mesmo
vídeo como amostras independentes. Diagnóstico explícito, limitado e com retenção,
sem gravação automática de imagens/vídeo. Persistência de postura, histerese,
incerteza e transição serão comparadas; nova versão de política quando houver
mudança de comportamento. Webcam só pelo fundador após arquivos. Sem commit,
push, deploy, serviço pago ou mensagens externas. Estado próprio em
[evolução do detector](EVOLUCAO_DO_DETECTOR.md); não iniciar a etapa 09.

Complemento de 24/10: fundador forneceu Radar_16_Videos_Novos e confirmou não
ter usado seus 16 arquivos em ajustes/treino/seleção do Radar. Preservar como
reserva, com agrupamentos reais das fontes e anotações antes das previsões.
Candidato corporal LINEAR_BODY_V2 preparado somente com o desenvolvimento
antigo para investigar outros enquadramentos; não transportar o modelo de
35 atributos restrito ao CAUCAFall nem alegar validação do cômodo do fundador.
Após corrigir os contornos e obter confirmação humana dos 16 arquivos,
primeira avaliação congelada: baseline/V2 2/6 alvos, quatro perdas; V2 com
seis negativos inconclusivos e sem melhora global. **Não promover V2 como
candidato final.** Manter resultado adverso e fonte/anotações; não modificar
limiares/pisos para aprovar esse lote. Caso ele oriente um sucessor, passa a
desenvolvimento para esse sucessor, com outra reserva para aceite.
[Preparação](RELATORIOS/EVOLUCAO_DETECTOR_03.md) e
[resultado](RELATORIOS/EVOLUCAO_DETECTOR_04.md).

## O que permanece do dossiê

O caso de uso assistivo, o processamento local, o reconhecimento de concorrentes, o fluxo humano, a necessidade de medir falsos alertas e a evolução por evidências. O pacote atual define uma bancada mais acessível para começar; não apaga os requisitos de um futuro serviço real.

## D53 — correção e regressão do detector V3, 25/10/2026

Solicitação do fundador autoriza treino local leve, comparação de percepção e
evolução da decisão. Os 16 vídeos já consultados passam a DEVELOPMENT/REGRESSION;
preservar a avaliação original e exigir nova reserva por gravação/sessão. Não
sortear frames entre partições. Reusar os contornos aprovados, sem redesenho
por postura. Permanecem 2000 ms de persistência e prazo de 5000 ms.

V3 preserva orientação, máscaras de ausência e score nativo; quatro classes
internas e abstenção. RTMO e dependências existentes mantidos. Recuperação
opcional por recorte da proposta de pessoa e inversão/recorte central, com
coordenadas restauradas e limiar de aceitação preservado. Políticas antigas
continuam disponíveis. Sessão física requer ação do fundador, sem abertura
automática de câmera. Resultados: [incremento 05](RELATORIOS/EVOLUCAO_DETECTOR_05.md).
Não aprova uso assistencial, piloto, eficácia geral nem inicia etapa 09.

## D54 — investigação de cadência sem novo ensaio físico, 26/10/2026

Por solicitação do fundador, medir o custo por fase e comparar até duas hipóteses
de execução, preservando o candidato, critérios e falhas. Transmissão técnica de
arquivo a 1× usa agendamento LIVE e inferência real, mas é REPLAY/TEST isolado,
sem HTTP, webcam ou gravação. Comparação de três repetições em quatro casos não
demonstrou ganho consistente com duas threads ou sem espera ativa; manter quatro
threads com espera ativa padrão. Não treinar, redesenhar polígonos, relaxar a
persistência/qualidade/lacuna ou pedir nova sessão de 12 minutos para compensar.
[Perfil, resultados e reprodução](RELATORIOS/DESEMPENHO_TRANSMISSAO_2026_10_26.md).

## D55 — preferência de processamento e regressão, 26/10/2026

Investigar a recuperação repetida, preservando REFERENCE_4_SPIN e V3. Candidato
RTMO_PREFERRED_V1 usa somente inferências atuais, preferência finita, inspeção
canônica e busca limitada. Os limites foram fixados antes das 24 comparações.
Economia de chamadas nos casos caros não autoriza perder observabilidade:
quatro novos controles inconclusivos nos 36 arquivos impedem a promoção de V1.
Manter configurações existentes; nenhum novo teste físico preparado ou executado.
Sem treino, alteração de polígonos ou relaxamento dos gates.
[Resultados e decisão](RELATORIOS/RECUPERACAO_ADAPTATIVA_2026_10_26.md).

## D56 — reaquisição canônica sem promoção automática, 26/10/2026

Preservar referência e V1 separadamente. RTMO_PREFERRED_V2 opt-in começa cada
análise em reaquisição com ORIGINAL, mantendo os limites de trabalho e os
critérios de observação. Corrigir a prioridade não basta para aprovar o candidato:
os quatro controles precisam recuperar o aceite em arquivo completo e nas
repetições a 1×, sem regredir os outros casos ou perder eventos/tipos.
Resultados negativos e quedas numéricas de cobertura permanecem registrados.
Nenhuma configuração existente é migrada; nenhuma webcam é aberta nesta rodada.
Comparação concluída: V2 recuperou 16/16 omissões e três controles em arquivo,
mas cauca-12 permaneceu inconclusivo e somente 16/24 transmissões passaram.
Manter a referência; não preparar ensaio físico para V2 com esses resultados.
[Comparação, perdas restantes e decisão](RELATORIOS/REAQUISICAO_V2_2026_10_26.md).

## D57 — estabilização orientada por diagnóstico, 26/10/2026

Sete frames reproduzidos com alternativas isoladas; sinais atuais, localização
barata/ROI e busca finita comparados. Não presumir RTMO_PREFERRED_V3 nem integrar
uma nova política apenas por recuperar alguns frames. A melhor ROI melhorou
cenários, mas falhou em duas das 24 transmissões técnicas e já tinha um controle
inconclusivo no piloto. Permanecer em experimento FILE isolado, sem novo seletor
do worker normal, novo modelo ou alteração dos critérios. Completar a matriz
funcional e registrar todas as regressões; nenhuma preparação física com esses
resultados. Auditor contrafactual reproduzível é código da entrega.
Matriz concluída: ROI 27/36 contra 30/36 da referência, três perdas novas de
aceite e tipo alterado em cauca-01; 12 eventos sem novos alertas indevidos ou
duplicações. Rejeitar integração, preservando o ganho condicionado e as falhas.
[Diagnóstico A/B/C](RELATORIOS/DIAGNOSTICO_RECUPERACAO_2026_10_26.md) ·
[Matriz e recomendação](RELATORIOS/ESTABILIZACAO_PERCEPTUAL_2026_10_26.md).

## Trajetória depois da v0.1

Complemento a D53 — 26/10/2026: rodada limitada a duas hipóteses de percepção,
sem treino nos dois novos vídeos de yoga. Referência V3 congelada e preservada;
RTMO_ADAPTIVE_V3 opt-in acrescenta recuperação de orientação com os mesmos
scores, coordenadas restauradas, contexto e limites temporais. Os dois vídeos
orientaram alterações e passam a desenvolvimento/regressão. Sessão física nova
requer disponibilidade explícita do fundador e marcadores humanos independentes;
não abrir webcam automaticamente, gravar vídeo ou aprovar o MVP por esses arquivos.
Perdas históricas e restrições de uso permanecem.
[Resultado e critérios do ensaio](RELATORIOS/PERCEPCAO_ORIENTACAO_V3_2026_10_26.md).

| Fase | Próxima prova | Condição de avanço |
| --- | --- | --- |
| Demo local | Tecnologia e fluxo reproduzíveis | Etapa 08 concluída e limites conhecidos |
| Apresentação a interessados | Problema relevante, resposta e orçamento | Conversas com demonstração concreta; sem prometer eficácia não medida |
| Piloto acompanhado | Funcionamento em outro ambiente | Escopo autorizado, responsáveis, protocolos de dados/atendimento e avaliação do uso pretendido |
| Primeira versão comercial | Instalação repetível e suporte viável | Desempenho adequado ao escopo, contrato, custos medidos e cliente disposto a pagar |
| Distribuição maior | Onboarding e manutenção sem trabalho artesanal excessivo | Lista de câmeras testadas, observabilidade e operação de suporte |
| Mais sensores/eventos | Ganho mensurável por caso de uso | Dataset, contrato, avaliação e riscos próprios para cada expansão |
| Hardware próprio | Vantagem sobre comprar equipamentos existentes | Demanda, capital, requisitos de hardware, cadeia de fornecimento e suporte justificam investimento |

Uma apresentação pode ser feita pelo próprio fundador; não implica compromisso de sociedade. Investimento é uma decisão de negócio posterior. Não há necessidade de oferecer participação para obter feedback de uma demo.

## O que pode se tornar um ativo da empresa

Compatibilidade realmente testada, implantação compreensível, avaliações reproduzíveis, dados autorizados com boa anotação, políticas temporais eficazes, integração à rotina de resposta e capacidade de suporte. Um dashboard ou um modelo público sozinho não garante defesa competitiva.

## Hipóteses que continuam abertas

Desempenho no notebook e em ambientes novos; acesso local da KAP-S069; aceitação de câmera e privacidade; taxa tolerável de falsos alertas; custo por instalação; disponibilidade de responsável para responder; disposição de pagar. O protótipo pode medir parte dessas hipóteses, não todas.

## Regra para evitar crescimento prematuro

Nova funcionalidade só entra no MVP se for necessária para demonstrar ou verificar o fluxo definido. Ideias de rua, áudio, identificação nominal, sensores novos, aplicativo, plataforma de parceiros ou câmera própria são registradas como backlog, não implementadas pela IA sem uma nova decisão.

Se o modelo de pose não servir, comparar outra base com licença compatível e manter o restante do produto. Se a KAP-S069 não expuser stream, manter webcam. Se o fluxo não gerar utilidade para interessados, rever o caso de uso antes de ampliar hardware e infraestrutura.

## D58 — decisão limitada e retificação temporal, 26/10/2026

Suspensão confirmada explica o tempo decorrido de 725 s no checkpoint.
O aceite antigo não tratava adequadamente EOF tardio; passa a considerar duração
inteira e decisão final no host, mantendo os limites. O produtor FILE registra
publicação real e rechecagem de espera, sem mover PTS. Resultados antigos
preservados: reavaliação dos streams 14/13/17/21 de 24; FILE completos
27/25/27/26 de 36, por referência/V1/V2/ROI.

Regra geométrica congelada rejeitada (3/4 recuperações); par leve YOLOX-tiny +
RTMPose-s rápido, mas com perdas de percepção e contrato de scores não
qualificado para o classificador atual. Não integrado. Sem treino, troca
automática do worker, limiares por arquivo ou nova busca de margens.

Referência é comparador, não verdade de terreno. Tipo diferente em cauca-01
requer cena/anotação, não igualdade cega. Perdas e controles inconclusivos
mantidos. Novo teste físico depende de localização/pose demonstradas, scores
compatíveis e tratamento de interrupção até o fechamento da decisão.
[Relatório](RELATORIOS/DECISAO_PERCEPCAO_2026_10_26.md).


## D59 — continuidade e diagnóstico visual delimitado, 27/10/2026

Solicitação do fundador: proteger decisão envelhecida e separar localização,
pose e classificador com pequena referência visual, sem webcam ou nova busca
ampla. Implementar rechecagens até entrega/aviso, sem modificar envelope,
horários ou apagar commit possivelmente confirmado. Preservar critérios
retificados, referência REFERENCE_4_SPIN, rejeitados e quatro perdas históricas.

Amostra interna de 14 frames/11 vídeos, construção/verificação por vídeo,
quatro orientações e duas repetições. Caixa fornecida é oráculo diagnóstico
offline, não dependência do produto nem desempenho automático. Scores nativos
não equivalem a visibilidade RTMO; classificador exige anatomia qualificada.

Correção perceptual comprovada: honrar RGB na pose RTMPose-s do auditor isolado,
mantendo BGR no detector e pesos/pós-processamento. Duplicidades compatíveis
com NMS exportado e falso sofá permanecem separados, sem fusão ou limiar novo.
Pessoa não localizada em F07/F13 independe de classificador. Rótulos articulares
foram rejeitados pelo fundador como imprecisos; PCK não vale para julgar o
modelo. Revisão V2 por imagem mantém incertos sem coordenada; nenhuma
classificação nova foi executada por falta de qualificação. A antiga saída shadow errada não isola, por si só,
incompatibilidade do classificador.

Não promover o par leve ou repetir matriz completa com essa evidência.
Próximo passo específico é conferir a pequena referência e reavaliar anatomia
A/B antes de atribuir a causa restante ou propor calibração. Sem treino,
novo ensaio físico ou aprovação integral.
[Relatório e reprodução](RELATORIOS/CONTINUIDADE_E_REFERENCIA_VISUAL_2026_10_27.md).
