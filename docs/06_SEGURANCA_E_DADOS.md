# Segurança, privacidade e retenção

[Voltar ao README central](../README.md)

Aplicar estas medidas proporcionalmente à bancada. Não é necessário constituir empresa ou conseguir parceiro para desenvolver com dados sintéticos e material próprio autorizado. Antes de uso assistencial com terceiros, avaliar finalidade, responsabilidades e exigências aplicáveis; este pacote não certifica conformidade regulatória.

## Identidades e permissões

| Identidade | Pode | Não pode |
| --- | --- | --- |
| `OWNER` | Configurar local/câmera, emitir/revogar token, revisar incidentes e excluir snapshots | Acessar outro tenant |
| `OPERATOR` | Ver incidentes/evidências autorizadas e registrar ações | Emitir token, alterar câmera ou excluir evidência |
| Device | Enviar eventos, heartbeat e snapshot da câmera vinculada | Fazer login humano, ler incidentes ou enviar para outra câmera |

Sem cadastro público, convite ou recuperação de senha por e-mail nesta versão. Bootstrap local cria um proprietário a partir de segredo informado pelo fundador. Seed não contém senha padrão pública e não reseta senha em toda execução. Uma conta de operador pode ser criada via comando local explícito; não construir gestão completa de equipe.

Senha com Argon2id. Sessão opaca aleatória, guardada com hash no PostgreSQL, expiração inicial de 8 h e revogação no logout. Cookie HttpOnly, SameSite=Lax e Path=/; Secure obrigatório fora da exceção de desenvolvimento restrita a loopback HTTP. Não guardar token humano em localStorage.

Para mutações com cookie, verificar `Origin` exato da interface; rejeitar origem externa ou ausente. API e proxy devem preservar essa informação. Testar tentativa CSRF. Rotas de device usam bearer e não dependem de cookie. CORS não é mecanismo de autenticação.

Token do worker é aleatório, individual, mostrado uma vez e armazenado em hash na API. Rotação revoga o anterior explicitamente. Guardar no computador em arquivo ignorado pelo Git, com permissões locais adequadas. Não usar token humano como segredo de dispositivo.

Na etapa 01, senhas usam Argon2id (64 MiB, três iterações, paralelismo 1); tokens de sessão/worker usam 32 bytes aleatórios e SHA-256 no banco. São tokens de alta entropia, com namespaces separados. O limitador de login é em memória para a instância local: dez tentativas por e-mail e sessenta por IP em cinco minutos, mapa limitado e sem confiar em X-Forwarded-For. Reiniciar o processo reinicia esse limitador; distribuição entre instâncias está fora da bancada. Login também exige Origin exata para evitar login CSRF, e mensagens de falha não distinguem usuário desconhecido de senha incorreta. O corpo JSON tem limite de 64 KiB e validação rejeita propriedades desconhecidas.

`pnpm.cmd setup:owner` e `pnpm.cmd user:create-operator` solicitam senha local com SecureString; transferem-na ao processo filho via ambiente, sem imprimi-la ou gravá-la em arquivo. As variáveis anteriores são restauradas no finally e o buffer BSTR é limpo; isso não promete eliminação de todas as cópias na memória do runtime. Como alternativa, variáveis no `.env` privado são aceitas. Nunca colocar credenciais no comando literal, no `.env.example` ou no relatório. Os scripts não são recuperação/reset de senha.

## Isolamento e exposição

Toda consulta a incidente, câmera, evento, imagem e auditoria é filtrada pelo tenant validado. Testes com dois tenants verificam leitura, alteração, referência cruzada e evidência. A existência de `tenantId` na tabela não prova isolamento.

No MVP, UI/API/PostgreSQL escutam loopback. Não abrir portas de roteador, túneis públicos ou câmera à internet. Operação em outra máquina/LAN não é automaticamente equivalente: exige TLS, controle de acesso e configuração específica. Não desabilitar verificação de certificado para “resolver” conexão.

Nunca confiar em caminhos de arquivo recebidos do navegador. O servidor não abre URI RTSP informada pelo painel; o worker local lê sua própria configuração. Isso reduz a superfície de SSRF. Login recebe limitação de tentativas, tamanho de corpo e mensagens que não revelam existência de usuário.

## Minimização

- Áudio desativado e não processado.
- Sem reconhecimento facial, nomes das pessoas observadas ou perfil individual de comportamento.
- Sem gravação contínua da webcam.
- Pose de evidência somente em evento; omitir landmarks faciais. Pose, horário e contexto ainda podem ser dados identificáveis; não chamar de anonimização garantida.
- Modelo e inferência rodam localmente. Pacotes/modelo são baixados no preparo; depois, a demonstração básica não precisa de internet.
- Vídeos de avaliação ficam privados no computador e fora do Git. Ter autorização para ver um vídeo não autoriza automaticamente publicação ou treinamento futuro.

## Evidência JPEG opcional

Default `EVIDENCE_MODE=skeleton`; alternativas `none` e `snapshot`. `none` envia somente sinais/metadados; `skeleton` inclui pontos corporais; `snapshot` também pode anexar uma imagem do evento.

Habilitar snapshot exige configuração local e confirmação do proprietário de que a captura está autorizada. A preferência fica registrada sem dados pessoais desnecessários. Nenhuma chamada de IA pode ativar o modo por conta própria apenas para melhorar a apresentação.

Upload após evento aceito, no máximo um JPEG de até 2 MiB por incidente, referenciado pelo eventId, maior lado até 1280 px. Validar bytes reais, decodificar, limitar pixels e reencodar sem EXIF. Não aceitar SVG, caminho arbitrário ou tipo declarado sem validação. Usar nome opaco e diretório privado fora da árvore pública web. Mesmo hash repetido é idempotente; tentativa de substituir conteúdo retorna conflito. Uma segunda chave de evento deduplicada no mesmo episódio não autoriza outra imagem.

O backend serve a imagem por endpoint autenticado, `Cache-Control: no-store`, sem URL pública permanente. Auditar acesso/exclusão. Falha, ausência ou expiração de imagem não impede revisão do incidente nem é tratada como ausência de ocorrência.

## Política inicial de retenção de bancada

| Dado | Prazo inicial | Comportamento |
| --- | --- | --- |
| Frames de processamento | Apenas memória | Descartados após processamento; buffer limitado |
| Snapshot na API | 24 h após recebimento | Apagar arquivo; preservar marcador de expiração |
| Snapshot pendente no worker | Até 24 h após criação | Expirar imagem sem apagar evento de metadados |
| Pose de evidência | 7 dias após recebimento | Remover lista de pontos, manter sinais mínimos |
| Metadados de incidentes e auditoria | 30 dias | Purga explícita configurada de demo, respeitando vínculos |
| Chaves/hash de recibos de deduplicação | 90 dias | Sem pose/imagem/payload; reenvio após purga não recria incidente |
| Outbox já confirmada | 7 dias | Limpar itens enviados; pendentes não expiram silenciosamente |
| Logs técnicos | 7 dias e limite de tamanho | Rotacionar e eliminar segredos/payloads |
| Vídeos fonte da avaliação | Definido no manifesto local | Não copiar automaticamente para relatórios ou backup |

São defaults de desenvolvimento, não justificativa legal universal. O programa deve indicar expiração/purga e aplicar limpeza idempotente, inclusive após reinício. A purga de 30 dias exige habilitação explícita do proprietário; se desabilitada, informar a retenção efetiva sem fingir que os dados foram apagados. Redação do payload preserva somente o hash original necessário à deduplicação. Retenção de backups também precisa considerar dados visuais; para a demo, backup padrão exclui imagens e vídeos, permanece privado e expira em 7 dias. Não restaurar automaticamente mídia já expirada.

## Auditoria e logs

Auditoria registra login relevante, criação/revogação de credencial, ação de incidente, alteração de configuração e acesso/exclusão de snapshot. Não armazenar senha/token/URL privada/corpo de imagem ou copiar todo payload nos logs.

Logs técnicos usam IDs correlacionáveis e códigos de erro. Não imprimir header Authorization, DSN de banco com senha ou string RTSP completa, inclusive em traceback de biblioteca. Injetar segredos fictícios nos testes e verificar que foram redigidos.

## Antes de sair da bancada

Reavaliar uso pretendido e alegações do produto, base de tratamento dos dados, responsabilidades de atendimento, aceite dos participantes, requisitos da LGPD e eventual enquadramento sanitário. Uso real precisa de responsável e processo de resposta. Não tratar “MVP” ou “bem-estar” como dispensa automática. Isso é um gate do piloto com terceiros; não altera a decisão de construir a demonstração agora.


## Operação implementada na etapa 07 — 22/10/2026

O envelope aceita `evidenceMode` opcional (legacy = skeleton); não se altera um
envelope já persistido. A preferência de câmera é uma barreira adicional: none
suprime pontos em incidente/recibo; snapshot sem autorização OWNER vigente no
recebimento é reduzido a skeleton, sem impedir o incidente. Upload exige a chave
originária do incidente. Outra chave deduplicada do mesmo episódio recebe 409.

`PATCH /cameras/:id/evidence-preference` recebe `{mode,authorized}` e exige OWNER,
Origin e confirmação explícita para snapshot. Preferência/autorização são auditadas.
`PATCH /retention-preference` recebe `{enabled}` e controla somente purga de 30 dias
por tenant; também exige OWNER/Origin e gera auditoria. Não foi habilitada no tenant
existente. `GET /retention-preference` permite ao OWNER conferir o estado.

### Imagem, armazenamento e falhas

Upload é corpo binário, sem multipart/caminho/nome do cliente. Limite HTTP de
2.097.152 bytes, compressão HTTP desabilitada e dois decodificadores simultâneos
(o excedente recebe 429). Somente JPEG real; maior lado 1280 e teto explícito de
1.638.400 pixels; decodificação estrita e timeout de processamento de 3 s. Sharp
0.35.5 reencodifica em JPEG/sRGB sem manter EXIF/XMP/ICC do original. Hash de upload
é SHA-256 dos **bytes originais**; o hash do JPEG normalizado também é guardado.
Repetição idêntica responde `{eventId,incidentId,hash,duplicate:true}` (HTTP 201,
compatível com a resposta inicial); conteúdo diferente dá 409. A expiração não
é renovada por reenvio. Um arquivo ausente pode ser reparado apenas pelo mesmo
conteúdo original ainda autorizado/não expirado; nunca por outro frame.

Diretório default `.local/api-evidence`, resolvido na raiz do repositório mesmo
quando a API roda em apps/api. `LOCAL_DATA_DIR` pode selecionar outro subdiretório
privado do repositório. Nomes UUID opacos, escrita exclusiva/fsync, sem rota estática
ou URL pública. Paths fora de .local e links simbólicos nos ancestrais são recusados.
Teto local: 1000 arquivos e 128 MiB. O serviço é uma instância de bancada, com lock
transacional PostgreSQL para serializar upload/leitura/exclusão/reconciliação.

Escrita ocorre sob lock antes do commit dos metadados; commit interrompido deixa
arquivo órfão, removido pela reconciliação. Não há arquivo temporário com nome do
cliente. Exclusão/expiração grava marcador antes de unlink; falha de filesystem
retorna diagnóstico e deixa trabalho repetível. Leitura verifica prazo, hash e
arquivo sob o mesmo lock; bytes expirados não são servidos mesmo se a rotina falhar.
Estado AVAILABLE com arquivo ausente/corrompido retorna 503, e não 404.
O painel revoga a URL blob no prazo informado mesmo se o polling ficar indisponível,
além de revogá-la na saída da sessão, exclusão ou desmontagem da tela. Marcadores
DELETED/EXPIRED impedem que uma entrega atrasada restaure os bytes.

### Mapa de cópias e limpeza

| Cópia | Conteúdo e política aplicada |
| --- | --- |
| Frame/pose corrente | Memória de captura/inferência; sem fila de frames ou gravação contínua |
| Incident.pose | Pontos de um evento; rotina redige em 7 dias do receivedAt e grava poseRedactedAt |
| EventReceipt.payload | Envelope detalhado redigível; rotina remove em 7 dias do recebimento, conserva payloadHash/eventId/episodeId/receivedAt/classe |
| Novo recibo de episódio já redigido | Não repõe pose; compara hash original e grava somente envelope sem pontos |
| Evidence | Referência/hash e marcador; JPEG expira 24 h do primeiro upload aceito; slot sem upload expira 24 h do incidente |
| Arquivo JPEG API | Diretório privado; unlink após marcador; órfãos removidos sob lock |
| SQLite outbox | Envelope pendente imutável; confirmado removido aos 7 dias, inclusive em episódio ativo; estado do episódio permanece sem pontos |
| SQLite snapshots | BLOB pontual na mesma transação do evento; até 100 imagens / 20 MiB, além do teto global da outbox; expira até 24 h da criação, inclusive permanente/auth bloqueada; ACK válido remove BLOB |
| SQLite WAL/SHM | secure_delete e checkpoint TRUNCATE, também em limpeza; leitor concorrente pode adiar truncamento, repetido após liberação/fechamento |
| Diagnósticos Python | Exportação opt-in body-only; none remove pontos também do JSONL; limpeza de observations.jsonl/report.json conhecidos em diretórios UUID, 7 dias e teto conjunto 20 MiB |
| Logs API | Somente fatos técnicos controlados, sem copiar strings de bibliotecas/headers/payload; segmentos até 1 MiB, teto total 10 MiB e 7 dias, limpeza ao escrever/reiniciar |
| Metadados/auditoria API | Purga aos 30 dias somente com preferência OWNER habilitada; remove relações e mantém recibo mínimo com incidentId=null/expiredAt |
| Recibos mínimos | Retidos no mínimo até 90 dias; purgados após esse prazo quando o incidente já foi purgado; impedem recriação por chave/episódio enquanto retidos |
| CameraRun | Chaves aposentadas por 90 dias; lease atual preservado |
| Vídeos fonte/modelos/calibrações | Não são copiados por esta etapa; limpeza de diagnóstico não os remove |

Pendentes de metadados não são apagados/redigidos para cumprir prazo: poderiam
conflitar com o payload cujo ACK se perdeu. Permanecem limitados pela outbox, com
erro visível quando não entregáveis; é exceção operacional explícita à retenção
visual até entrega/resolução local. Encerrar episódio não elimina essa pendência.
Nenhuma limpeza promete apagamento forense do disco, SSD ou cópias externas.
Saída de terminal e logs redirecionados pelo operador ficam sob sua gestão; não
são silenciosamente varridos pela aplicação.

### Habilitar a rotina

`RETENTION_JOBS_ENABLED=false` é o default de migração operacional: preserva os dados
existentes sem executar uma purga retroativa. O `.env` do fundador não foi alterado.
Com true, `RetentionJob` roda na inicialização e a cada 60 s, sem sobreposição;
`pnpm.cmd retention:run` executa uma rodada explícita. Ambos usam a mesma rotina e
mantêm tarefas/estados recuperáveis no banco. Sem agendamento ou rodada manual,
não alegar que bytes/pontos foram apagados automaticamente. JPEG expirado continua
bloqueado na leitura. A preferência de metadados de 30 dias é separada e default false.
No worker ativo com entrega habilitada, a limpeza conhecida roda a cada 60 s;
com worker parado use `radar-edge cleanup`. Não varre outras outboxes ou vídeos.

### Backup privado e restauração

Não há backup automático nem cópia de mídia implementados. Se o operador fizer
backup da bancada, o conjunto padrão é somente banco/configuração privada, excluindo
`.local/api-evidence`, vídeos, modelos, screenshots e diagnósticos visuais. O dump
continua sensível (inclusive contas e poses ainda retidas): guardar fora do Git,
com acesso local restrito e prazo de 7 dias; remover manualmente a cópia após esse
prazo. Não afirmar exclusão de backup externo, sincronizado ou já exportado.

Restaure primeiro num banco e diretório exclusivos, sem servir tráfego. Não copie
mídia automaticamente. Como o backup padrão não inclui JPEG, marque todos os slots
restaurados EXPIRED (preserve DELETED), apague referências objectKey e bytes, mantenha
hashes/chaves e registre a operação técnica. Isso impede reenviar/restaurar imagens
que a cópia não contém. Execute a rotina de retenção **no banco restaurado** antes
de abrir a interface: timestamps originais governam poses/recibos expirados. Não
substitua esses horários pela data do restore. Valide login, ausência de mídia,
deduplicação e metadados no ambiente exclusivo antes de qualquer troca de banco.
Esta etapa não criou/restaurou um backup dos dados pessoais do fundador.

Reprodução: [roteiro 07](VALIDACAO_MANUAL_ETAPA_07.md). Decodificação/metadata:
[Sharp constructor](https://sharp.pixelplumbing.com/api-constructor/) e
[Sharp output](https://sharp.pixelplumbing.com/api-output/).
