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

## O que permanece do dossiê

O caso de uso assistivo, o processamento local, o reconhecimento de concorrentes, o fluxo humano, a necessidade de medir falsos alertas e a evolução por evidências. O pacote atual define uma bancada mais acessível para começar; não apaga os requisitos de um futuro serviço real.

## Trajetória depois da v0.1

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
