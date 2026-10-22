# Etapa 07 — Evidência opcional, retenção e proteção

Data: 22/10/2026, America/Sao_Paulo.
Status: **CONCLUÍDA no escopo solicitado**.
Base: main `c5e1c5410135b01e260a267940b041d75538a68d`, etapa 06.
Ambiente: Windows 11 Pro x64, PowerShell 5.1; Ryzen 5 5625U/15,4 GiB
registrados na 06; Node 24.22.1, pnpm 10.34.7, Python 3.12.15, uv 0.13.4,
Docker Engine 29.1.3. MediaPipe/Full, OpenCV único e critérios de qualidade
preservados. Nesta etapa nenhuma câmera/vídeo pessoal foi aberto.
Commit e push autorizados pelo fundador em 22/10/2026; sem deploy; etapa 08 não iniciada.

## Resultado entregue

Modos none/skeleton/snapshot, JPEG pontual opcional, envio separado após ACK do
evento e armazenamento privado. Estado, autorização, leitura e exclusão no painel;
retomada/reenvio e retenção testados com imagem sintética sem pessoas.

O padrão continua skeleton. A configuração real da webcam foi apenas consultada:
`jpegEnabled=false`, `snapshotAuthorized=false`, sem abrir fonte ou SQLite.
A migração acrescentou campos/tabela com defaults conservadores; não habilitou
snapshot nem purga no tenant do fundador. Limpeza automática API default false;
rodada explícita e agendamento habilitado foram exercitados em testes isolados.
Não afirmar que os dados existentes já foram apagados pela política de retenção.

A conclusão física da etapa 06 foi conferida em STATUS/relatório e código; suas
limitações (estante, fluidez e falta de positivo LIVE) permanecem para avaliação
final. Não houve nova validação física nem alteração do detector nesta etapa.

## Arquivos e decisões

- API: `apps/api/src/evidence.ts`, módulo/aplicação/configuração, ingestão,
  detalhe de incidente/catálogo e CLI. `technical-logger.ts` restringe fatos de log.
- Banco: `apps/api/prisma/schema.prisma` e migração SQL aditiva
  `20261022000100_evidence_retention`; FKs compostas de tenant, slot único,
  checks de estados/modo e limite de bytes. Formato SQLite v2 aditivo no worker.
- Worker: `evidence.py`, `retention.py`, `event_runtime.py`, `outbox.py`, `delivery.py`,
  integração FILE/LIVE, diagnóstico/CLI/saúde e exemplos com autorização false.
- Web: `components/evidence.tsx`, detalhe/configuração, modelos e rótulos.
- Contrato: campo opcional evidenceMode, tipo gerado e quatro fixtures novas;
  envelopes antigos e hashes já persistidos permanecem válidos.
- Testes: `apps/api/test/evidence.test.mjs`, gerador sintético, probes Python,
  `services/edge/tests/test_evidence.py`, ajustes de migração/retenção anteriores
  e fluxo Playwright. Harness preserva bancos/volumes/processos da bancada.
- Operação: scripts `demo:evidence`, `retention:run`, exemplos e OpenAPI;
  documentação central, segurança, arquitetura, decisões, status e roteiro 07.
- Dependência: Sharp 0.35.5 direto na API, já presente nessa versão no lock da web;
  Node 24 compatível, pacote Apache-2.0 consultado localmente. Lock pnpm atualizado;
  nenhuma nova dependência Python ou distribuição cv2. Não houve troca de major.

Decisões D39–D43: consentimento por câmera e local, hash original vs normalizado,
marcadores irreversíveis, filesystem sob lock e fila de BLOBs limitada. Prazos,
limites e mapa de cópias em [segurança](../06_SEGURANCA_E_DADOS.md).

## Comportamento e recuperação

Upload binário estrito de até 2 MiB; maior lado 1280 px, até 1.638.400 pixels,
duas decodificações simultâneas. JPEG é decodificado/reencodificado sem EXIF.
Content-Type não define o formato aceito. Caminho do cliente nunca é usado.
Armazenamento privado com nomes opacos, limite de 1000 arquivos/128 MiB.

A chave originária do evento é a única que autoriza a imagem. Hash dos bytes
originais repetido é idempotente; conteúdo diferente ou outra chave do episódio
dá 409. ACK contém eventId/incidentId/hash/duplicate; o worker confere tudo antes
de eliminar BLOB. Reenvio não renova prazo. Exclusão/expiração bloqueia restauração
por reenvio. Mesmo original ainda válido pode reparar arquivo fisicamente ausente;
arquivo inconsistente ou falha de disco é indisponibilidade, não ausência definitiva.

Banco e filesystem não têm transação distribuída: arquivo fsync sob lock antes do
commit; interrupção deixa órfão reconhecível. Marcador de remoção é commitado antes
do unlink; falha mantém tarefa repetível. Reconciliação serializada limpa órfãos e
marcadores com bytes restantes. A leitura sempre testa expiração e hash.

JPEG local só é codificado no instante do evento, com frameIndex/timestamp iguais
à observação. Snapshot/checkpoint/evento são persistidos juntos em SQLite; falha
na imagem mantém metadados e erro visível. Até 100 BLOBs/20 MiB, mais limite global
da outbox; expiração 24 h mesmo em erro permanente/auth bloqueada. Sem arquivo de
imagem por frame ou gravação contínua. Confirmados perdem payload aos 7 dias,
inclusive com episódio ativo: executions.engine guarda apenas estado e continua
impedindo nova emissão. Pendentes nunca são redigidos ou apagados silenciosamente.

## Verificações reais

| Comando/ação realmente executado | Resultado observado | Limite |
| --- | --- | --- |
| `git status --short`, leitura do prompt/AGENTS/README/status/etapas/referências e inventário `rg --files` | Base limpa na main; etapa 06 documentada/concluída | Não assumiu software só pela documentação |
| `. ./scripts/activate.ps1`; `node --version`; `pnpm.cmd --version`; `uv --version`; Python `--version`; Docker `info` | Versões acima e daemon disponível | Sem instalar câmera/permissão global |
| `pnpm.cmd --filter @radar/api add sharp@0.35.5 --save-exact` | Dependência e lock atualizados | Warnings preexistentes ESLint/glob e scripts opcionais ignorados; sem atualização de major |
| `pnpm.cmd contracts:generate` | Tipos regenerados a partir do schema | Payloads já gravados não foram editados |
| `prisma migrate diff --from-migrations ...` | Falhou por falta de shadowDatabaseUrl | Não apontou a banco pessoal; corrigido usando schema base do Git |
| `prisma migrate diff --from-schema ../../.local/etapa07/schema-before.prisma --to-schema prisma/schema.prisma --script --output ...` | SQL aditivo real gerado após corrigir unique composta da relação 1:1 | Nenhum db push/reset |
| `pnpm.cmd db:generate`; `pnpm.cmd --filter @radar/api exec prisma format` | Client/schema gerados/formatados | Migração SQL versionável |
| `pnpm.cmd test:api` | 145 aprovados: 19 acesso + 16 evidência + 108 eventos/contratos + 1 edge + 1 resiliência | PostgreSQL/volume exclusivos; somente imagens/contas sintéticas |
| Probe Python real via teste de API | Evento aceito, imagem aceita com ACK perdido, novo processo reenvia, uma evidência e bytes locais removidos | Sem modelo/vídeo; prova de transporte/persistência |
| `pnpm.cmd test:contracts` | 91 TS + 91 Python aprovados; tipos consistentes | Mesmas fixtures entre linguagens |
| `uv run --project services/edge --frozen pytest services/edge/tests -q`, com RADAR_TEST_GUI=1 | 262 aprovados, sem skips | Sem nova prova de webcam; fixtures e regressões anteriores |
| `pnpm.cmd lint:edge` | Ruff check/format aprovados, 45 arquivos | Inclui novos módulos/testes |
| `pnpm.cmd test:e2e` | 18 aprovados em Chromium desktop/móvel; fluxo de JPEG e regressões | Viewport móvel, não celular físico |
| `pnpm.cmd demo:evidence` | 1 aprovado, demonstração desktop sintética independente | Screenshot privado inspecionado; retângulo sem pessoa; última rodada conferiu também expiração do blob com polling indisponível |
| `radar-edge evidence-status --config .local/edge-webcam.yaml` via uv frozen | skeleton, JPEG false, autorização false, fonte/DB não abertos | Não carrega modelo nem demonstra captura |
| `pnpm.cmd infra:status`; inventário agregado por Node antes/depois; `pnpm.cmd db:migrate` | postgres saudável em 15432; migração aplicada; contagens preservadas | Não executou retenção no banco do fundador |
| `pnpm.cmd install --frozen-lockfile`; `uv sync --project services/edge --frozen`; `pnpm.cmd lint`; `pnpm.cmd typecheck`; `pnpm.cmd build`; `pnpm.cmd openapi:generate` | Aprovados; OpenAPI regenerado | Logs/scripts opcionais ignorados conforme política pnpm existente |

Contagens antes/depois da migração no banco da bancada: 1 tenant, 1 usuário,
3 locais, 4 câmeras, 4 devices, 3 incidentes, 3 recibos e 27 auditorias.
O inventário usou `.local/etapa07/project-inventory.mjs`, somente count; não leu
senhas/hashes/tokens ou payloads pessoais. O serviço externo 5432 foi preservado.

Logs privados de execução: `.local/etapa07/test-api-final.log`, `test-e2e.log` e
`demo-evidence.log` e `demo-evidence-final.log`. A busca de segredos compara apenas valores **fictícios**
injetados com logs da aplicação; não procurou segredos reais do fundador.
Teste de bytes em SQLite/WAL após ACK/fechamento não encontrou o JPEG sintético.
Não generaliza para apagamento forense de SSD/backups.

## Critérios da etapa

| Critério obrigatório | Evidência |
| --- | --- |
| none/skeleton sem JPEG e snapshot opt-in | Teste bloqueia imencode; modo local real segue skeleton/false; consentimento OWNER/Origin e flag local separados |
| Limites/formato/metadata e isolamento | JPEG inválido, PNG disfarçado, truncamento, >2 MiB, lado >1280, cabeçalho 65000×65000, EXIF removido; sessão/tenant/device/RBAC/CSRF verificados |
| Idempotência e concorrência | Upload repetido/paralelo, conteúdo diferente, chave alternativa de episódio; leitura/exclusão/upload concorrentes e marcadores |
| Retenção de todas as cópias aplicáveis | Relógio injetado para imagem/pose/recibo/outbox, purga opt-in, recibo mínimo 90 dias, diagnósticos/logs; episódio ativo restaurado após limpar payload confirmado |
| Falha de imagem não perde incidente | Erro de captura, quota, disco/DB e ACK perdido mantêm incidente/estado revisável; retomada de processo Python real |
| Exclusão/acesso/preferência auditados | Auditoria persistida, OWNER exclui; Playwright mantém revisão após exclusão |
| Logs sem segredos | Logger por lista de fatos, EXIF/credencial/senha fictícios ausentes nos logs testados; limite/expiração testados |
| Operação local e documentação fiel | Sem porta pública, mídia real ou integração nova; documentação e roteiro descrevem agendamento/purga desligados e limites |

## Como reproduzir

Siga [VALIDACAO_MANUAL_ETAPA_07](../VALIDACAO_MANUAL_ETAPA_07.md), com os seis passos:
modo padrão; JPEG sintético; permissões; exclusão/auditoria; retenção isolada;
limpeza/deduplicação. Não precisa criar conta ou copiar credencial real para validar
esta etapa. `pnpm.cmd retention:run` é comando real de limpeza, não de diagnóstico:
não foi executado no banco pessoal; tem exemplo e efeitos separados no roteiro.

## Falhas encontradas e corrigidas

A conferência adicional de expiração no navegador usa prazo curto controlado e revoga o blob mesmo sem polling; não espera 24 h. Um seletor de teste perdeu acento no pipe PowerShell, foi corrigido em UTF-8 e o fluxo passou novamente.

O limite binário rejeita compressão HTTP sem descompactar; o filtro foi ajustado
para retornar 415 permanente e mensagem de tamanho apropriada à rota, em vez de
classificar essa rejeição como falha interna. Esse caso foi reexecutado na API.


- Migração: diff de diretório exigia shadow DB; usado schema base, sem improvisar
  conexão ao banco externo. Relação 1:1 precisava unique composta de tenant/incidente.
- Fixtures antigas esperavam duas migrações; agora verificam as três. Seed não
  cria câmera, então o teste novo passou a criar suas câmeras explicitamente.
- Terceiro upload paralelo recebeu corretamente 429 do teto de decodificação;
  teste de idempotência usa dois uploads simultâneos dentro do limite.
- Fixture padrão não tinha pose, portanto não provava redação; adicionados pontos
  corporais sintéticos antes do teste de retenção.
- Probe de reinício inicialmente não avançava o relógio de retry; corrigido o
  relógio injetado entre processos, preservando backoff de produção.
- Codificação do pipe PowerShell gerou bytes inválidos numa edição Python local;
  arquivo corrigido em UTF-8 e checks/regressões reexecutados. Não atribuir esse
  erro de edição a defeito de câmera ou modelo.
- Revisão identificou que preferência none precisava continuar valendo no recibo
  de um episódio antigo mesmo depois de trocar preferência: corrigido e testado.
- Leitura de arquivo ausente segue 503; reenvio do mesmo original ainda autorizado
  agora pode reparar a perda sem mudar hash/expiração. Exclusão/expiração não pode.

## Limites e pendências

Snapshot real continua desabilitado por escolha de escopo; funcionalidade validada
com pixels sintéticos autorizados pelo prompt. Isso não é pendência física da 07.
O agendamento API e a purga de 30 dias não foram ativados para o fundador. Sem
agendamento/rodada explícita, não afirmar exclusão automática de visuais antigos.
UI/API estão prontas para indicar estados e permitir a opção consciente de limpeza.

Não criou/restaurou backup pessoal, não apagou cópias externas nem certificou
conformidade legal. Política de backup privado/sem mídia/restauração antes de servir
está documentada. Filesystem é privado, não cifrado por esta aplicação; usuários
locais com acesso à pasta/banco precisam continuar restritos pelo SO. Perda
irrecuperável do disco não é resolvida por retries. Suporte Linux/MSMF e celular
físico não foram testados. D30 sobre SDK nativo permanece; não se alegou bloqueio
de telemetria ou tráfego total verificado. Detector/FPS/estante continuam limites
anteriores da percepção; esta etapa não promete corrigi-los.

## Próxima etapa elegível

A 08 é elegível somente por nova solicitação, após esta conclusão funcional. Nenhuma implementação
da validação final/release foi iniciada. Commit e push autorizados posteriormente pelo fundador; sem deploy.
