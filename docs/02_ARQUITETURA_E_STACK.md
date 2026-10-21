# Arquitetura e stack

[Voltar ao README central](../README.md)

## Topologia da bancada

Três processos de aplicação e um banco: Next.js, NestJS, worker Python e PostgreSQL. O banco roda em Docker Compose; os demais rodam no host para simplificar desenvolvimento e acesso à webcam, especialmente no Windows.

| Processo | Endereço inicial | Responsabilidade |
| --- | --- | --- |
| Web | `http://127.0.0.1:3000` | Interface, autenticação via cookie, leitura e ações |
| API | `http://127.0.0.1:3001/v1` | Autorização, domínio, ingestão e armazenamento |
| PostgreSQL | `127.0.0.1:5432` | Fonte de verdade central |
| Worker | Sem porta HTTP | Captura e envio de saída à API |

O navegador usa `/api/*`, reescrito pelo Next para `/v1/*` da API. Não misturar `localhost` e `127.0.0.1` na configuração de cookies/origem. Interface e API têm binds de loopback no modo local. O driver de câmera está no worker, não no servidor web.

Na máquina verificada na etapa 00, `POSTGRES_PORT=15432` no `.env` privado evita conflito com o PostgreSQL já instalado em 5432 (D15). A porta interna do container continua 5432. Nenhuma integração da API com o banco foi implementada nesta etapa.

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
