# Arquitetura e stack

[Voltar ao README central](../README.md)

## Topologia da bancada

Três processos de aplicação e um banco: Next.js, NestJS, worker Python e PostgreSQL. O banco roda em Docker Compose; os demais rodam no host para simplificar desenvolvimento e acesso à webcam, especialmente no Windows.

| Processo | Endereço inicial | Responsabilidade |
| --- | --- | --- |
| Web | `http://127.0.0.1:3000` | Interface, autenticação via cookie, leitura e ações |
| API | `http://127.0.0.1:3001/v1` | Autorização, domínio, ingestão e armazenamento |
| PostgreSQL | `127.0.0.1:15432` | Fonte de verdade central; porta interna do container 5432 |
| Worker | Sem porta HTTP | Captura e envio de saída à API |

O navegador usa `/api/*`, reescrito pelo Next para `/v1/*` da API. Não misturar `localhost` e `127.0.0.1` na configuração de cookies/origem. Interface e API têm binds de loopback no modo local. O driver de câmera está no worker, não no servidor web.

Na máquina verificada, `POSTGRES_PORT=15432` no `.env` privado evita conflito com o PostgreSQL já instalado em 5432 (D15/D16). O exemplo da etapa 01 também usa 15432. A porta interna do container continua 5432. A API usa Prisma 7.10.1, gerador `prisma-client` com output explícito em `apps/api/src/generated/prisma`, ESM/NodeNext, adapter-pg 7.10.1 e pg 8.23.1. Gerados são ignorados e reproduzidos por `db:generate`/prebuild. Migrações SQL são versionadas, sem `db push`.

O `prisma.config.ts` carrega explicitamente `apps/api/.env`, preservando variáveis já fornecidas ao processo (inclusive no banco de testes). A URL é validada sem imprimir credenciais e a porta 5432 do host é rejeitada. O pool tem máximo 5 conexões, timeout de conexão de 2 s, statement timeout de 3 s e idle timeout de 5 s. O client conecta sob demanda: indisponibilidade do banco não impede liveness; readiness executa consulta real e retorna 503.

Dockerizar a webcam não é requisito. Não presumir que WSL/Docker Desktop exponha o dispositivo. Em Windows, o caminho principal é Python nativo, com permissão do SO. Um computador diferente para inferência será uma implantação futura com TLS e configuração de rede próprias.

## Dependências escolhidas

| Componente | Política |
| --- | --- |
| Node.js | 24 LTS, patch estável de segurança verificado na implementação |
| Gerenciador JS | pnpm 10, versão exata em `packageManager` e lockfile |
| Backend | NestJS 11; REST; monólito modular |
| Frontend | Next.js 16 App Router, React compatível, TypeScript e Tailwind CSS |
| Prisma | Família 7 estável; `prisma`, client e adapter compatíveis e fixados; não adotar 8 RC |
| Prisma/Postgres | Gerador `prisma-client`, output explícito, adapter `@prisma/adapter-pg`, `pg`, timeouts de conexão |
| Módulos Node | API ESM, `type: module`, configuração coerente com execução e testes; não misturar exemplos CommonJS antigos |
| Banco | PostgreSQL 17, tag de patch fixada no Compose; volume persistente |
| Python | 3.12, `.python-version`, `pyproject.toml` e `uv.lock` |
| Visão | MediaPipe Tasks Python + bundle Pose Landmarker Lite; OpenCV compatível, um único fornecedor de `cv2` |
| Worker | Pydantic v2, HTTPX, biblioteca SQLite da linguagem; CLI `radar-edge` |
| Contratos | JSON Schema versionado; validação nos dois runtimes e exemplos compartilhados |
| Web/API tests | Jest/Supertest e Playwright; ESLint e TypeScript strict |
| Python tests | pytest e Ruff |

Não se exige versão “mais nova” a qualquer custo. A etapa 00 registra a combinação instalada, e a 04 registra o bundle exato, SHA-256, origem e termos. Se o wheel de visão não existir para o SO/arquitetura, diagnosticar antes de continuar; não ocultar com mock. A baseline CPU precede qualquer compra de GPU.

No Prisma 7, seguir a documentação da versão escolhida para configuração da CLI, carregamento de `.env`, output do gerador e adapter. Não copiar a configuração de ORM 6. As versões atuais de Next e Nest também devem ser verificadas contra a família fixada, sem atualizações de major automáticas.

## Organização prevista do repositório

Na etapa 00 foram criados `apps/web`, `apps/api`, `services/edge`, `packages/contracts`, `scripts` e `infra/compose.yaml`. A tabela descreve a organização final prevista; existência do diretório não significa implementação de todo seu conteúdo futuro. Testes de domínio/e2e e modelos serão introduzidos nas etapas próprias.

| Caminho | Conteúdo futuro |
| --- | --- |
| `apps/web/` | Dashboard e páginas de configuração |
| `apps/api/` | NestJS, Prisma schema/migrations e seed local |
| `services/edge/` | Projeto Python `radar_edge`, captura, pose, regras, outbox e CLI |
| `packages/contracts/` | JSON Schemas, exemplos válidos/inválidos e tipos TS |
| `scripts/` | Simulador, preparação local e verificações de desenvolvimento |
| `infra/compose.yaml` | PostgreSQL local; configurações de infraestrutura |
| `tests/e2e/` | Fluxos de navegador e integração |
| `tests/fixtures/` | Dados sintéticos pequenos, sem imagens pessoais |
| `.local/` | Configurações privadas, modelos, outbox, mídia e resultados; ignorado pelo Git |
| `docs/` | Especificações, decisões, status e relatórios |
| `etapas/` | Plano de implementação e prompts |

O Python tem lock próprio. O workspace pnpm cobre apenas os pacotes TypeScript. Não compartilhar modelos de banco com o worker: o contrato de ingestão é o limite entre os processos.

## Módulos da API

| Módulo | Limite |
| --- | --- |
| `Identity` | Login/logout, sessões, papéis e proprietário local |
| `Sites` | Local e câmera lógica, cadastro mínimo |
| `Devices` | Credencial de worker vinculada a uma câmera, rotação e revogação |
| `Ingest` | Validar eventos/heartbeat e deduplicar |
| `Incidents` | Estado, revisão, ações e listagem |
| `Notifications` | Caixa local e entrega simulada persistente |
| `Evidence` | Snapshot opcional autenticado e expiração |
| `Audit` | Registro de ações e acessos relevantes |
| `Health` | Disponibilidade da API/banco e cálculo de saúde de captura |

Não separar em serviços remotos. Regras de transição pertencem ao backend. O frontend exibe opções e trata conflitos; não é fonte de verdade.

## Persistência e filas

No worker, a transação SQLite salva evento e estado ativo do episódio antes do envio. Eventos permanecem até confirmação de persistência pela API. Heartbeats são efêmeros: só importa o mais recente, e não entram na mesma fila durável.

Na API, uma transação cria recibo do evento, incidente, auditoria e intenção de aviso. Um executor simples no Nest processa intenções do PostgreSQL, com chave única e retomada após reinício. A entrega simula um canal e cria um registro local; não há provedor externo.

Redis/BullMQ fica fora da v0.1. Para uma única instância e avisos de demonstração, a fila no banco basta. Se acrescentarmos distribuição e múltiplos workers, o módulo poderá ganhar BullMQ mantendo o banco como verdade durável. Frames e poses contínuas nunca passam por fila de mensagens.

## Dados visuais

Por padrão: frames em memória, pose de evidência de um único momento do evento, sinais resumidos e metadados. Não enviar todas as poses. A interface desenha o esqueleto com coordenadas de ombros, quadril, joelhos e tornozelos; não necessita landmarks faciais.

Snapshot é um JPEG de evento, habilitado explicitamente, enviado em endpoint separado após a ingestão. A imagem não condiciona a criação do incidente. Não haverá clip contínuo, armazenamento S3 ou live stream web no MVP.

## Limites de recursos

- Uma fonte por worker e um worker ativo de bancada por vez.
- Buffer de captura ao vivo com o frame mais recente; não acumular atraso ilimitado.
- Meta inicial 5 inferências/s a 640 pixels de largura, mantendo proporção. Medir FPS real, CPU/RAM e frames descartados.
- Outbox de metadados limitada inicialmente a 10.000 itens ou 100 MiB; atingir limite interrompe novas inferências e informa erro, sem apagar pendentes silenciosamente.
- Timeout de HTTP inicial 5 s; backoff exponencial com jitter de 1 até 30 s para falhas transitórias.
- Evidência binária tem limites separados; falha de snapshot não remove metadados do incidente.

Os números são limites iniciais de bancada, ajustáveis por configuração documentada. Não representam capacidade certificada ou compromisso de serviço.

## Implementação de captura e recuperação da etapa 06

WEBCAM usa processo nativo Windows com spawn e um único slot de pixels em memória
compartilhada (3.932.160 bytes). Captura numera aquisições e usa relógio monotônico;
inferência consome somente o frame novo mais recente. Modelo Full explícito,
CPU/VIDEO e política floor-v0.1 preservados. Um lock de SO mantém uma única webcam
ativa de bancada, inclusive durante pausa. Arquivos mantêm o relógio de mídia.

Heartbeat e entrega usam threads HTTP separadas, sem bloquear a inferência e sem
fila histórica de heartbeat. Cada thread possui suas conexões SQLite/HTTP. O runId
da sessão é novo a cada inicialização; a execução persistente guarda checkpoint
e episódio ativo. Eventos já gravados conservam seu runId e payload nos reenvios.
Essa separação também permite retomar FILE após um heartbeat ENDED.

Open/read podem bloquear no driver: a captura é encerrada por prazo no processo
pai, com IPC novo a cada reconexão. O filho monitora a morte do pai. A recuperação
automática é limitada por configuração. Nenhuma propriedade de timeout do OpenCV
foi presumida como garantia de timeout no DSHOW.

Limites contam itens e bytes de SQLite/WAL/SHM, com reserva antes de novas decisões.
A limpeza da 06 remove somente payloads confirmados há mais de sete dias de
episódios fechados/resetados; mantém pendentes, erros permanentes e chaves de
deduplicação. Não implementa retenção global/snapshot da etapa 07.


## Evidência e retenção da etapa 07

EvidenceService no monólito, sem serviço externo. Sharp 0.35.5 direto na API
reaproveita a versão já fixada no lock da web. JPEG privado é normalizado e servido
somente por sessão/tenant; filesystem e banco usam reconciliação sob lock, não uma
promessa de transação distribuída. Slot/tombstone único por incidente preserva
origem e impede substituição/ressurreição.

O worker codifica só o frame que emite o evento; BLOB pontual entra na mesma
transação SQLite do checkpoint. Usa Delivery/HTTP/credencial existentes após ACK
de metadados, com limite separado e expiração. Não há fila de frames/imagens
contínuas. Episódio ativo precisa somente do checkpoint de estado: permite limpar
envelope confirmado aos sete dias sem perder o bloqueio de duplicação.

RetentionJob chama a mesma rotina idempotente na inicialização/60 s quando
explicitamente habilitado. Agendamento default false preserva dados existentes;
purga de metadados é um segundo opt-in OWNER, por tenant. A API nega leitura de
JPEG expirado independentemente de limpeza física já executada. Ver mapa completo
em [segurança](06_SEGURANCA_E_DADOS.md) e decisões D39–D43.
