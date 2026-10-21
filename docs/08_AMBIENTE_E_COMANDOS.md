# Ambiente, configuração e comandos previstos

[Voltar ao README central](../README.md)

**Este documento define a interface de desenvolvimento a construir. Nenhum comando de aplicação abaixo foi implementado ou executado neste pacote de documentação.** Cada etapa deve tornar seus comandos reais e atualizar os exemplos com resultado verificado.

## Pré-requisitos

Git, VS Code, Node.js 24 LTS, pnpm 10, Python 3.12, uv e Docker com Compose. Preferir ambiente nativo do SO para webcam. Primeiro verificar os programas presentes; não reinstalar tudo ou alterar configurações globais sem necessidade.

Não há GPU, conta AWS, OpenAI API, servidor público, cartão de crédito ou assinatura obrigatória. Instalação de pacotes/modelo requer internet inicialmente. O consumo de memória e a capacidade de uma câmera serão medidos; não há especificação inventada para o notebook do fundador.

| Comando de diagnóstico | Uso |
| --- | --- |
| `node --version` / `pnpm --version` | Conferir runtime JS e gerenciador |
| `python --version` / `uv --version` | Conferir runtime e ambiente Python |
| `docker version` / `docker compose version` | Conferir daemon e Compose |
| `git status --short` | Preservar alterações antes de editar |

## Variáveis e arquivos privados

O bootstrap deve gerar `.env.example` sem segredos e orientar cópia local. Validar variáveis na inicialização e falhar com erro compreensível, sem imprimir valores sensíveis.

| Variável/conceito | Onde | Observação |
| --- | --- | --- |
| `DATABASE_URL` | API/migrações | PostgreSQL local com senha particular |
| `API_HOST`, `API_PORT` | API | `127.0.0.1`, `3001` |
| `WEB_ORIGIN` | API | `http://127.0.0.1:3000` |
| `API_INTERNAL_URL` | Web server | `http://127.0.0.1:3001/v1`; não vazar segredos ao client |
| `BOOTSTRAP_EMAIL`, `BOOTSTRAP_PASSWORD` | Setup local | Conta proprietária; não embutir no código |
| `EDGE_API_URL` | Worker/simulador | Endpoint da API local |
| `EDGE_DEVICE_TOKEN` | Worker/simulador | Credencial individual emitida pelo backend |
| `EDGE_CAMERA_ID` | Worker | Registro de câmera autorizado |
| `EDGE_SOURCE_URI` | Worker | Somente para RTSP; nunca em log/argumento CLI |
| `EDGE_MODEL_PATH` | Worker | Bundle obtido de fonte oficial e hash verificado |
| `EVIDENCE_MODE` | Worker | `skeleton` por padrão; `none`/`snapshot` explícitos |
| `LOCAL_DATA_DIR` | API/worker | Raiz privada `.local/` e subdiretórios separados |
| `METADATA_RETENTION_ENABLED` | API | `false` por padrão; proprietário habilita conscientemente a purga de metadados de 30 dias |

Nunca prefixar segredo com `NEXT_PUBLIC_`. Não definir nome de variável de tarefa que substitua `HOME` ou outros diretórios de sistema.

## Comandos que a implementação deve oferecer

Executados a partir da raiz do repositório. Scripts pnpm encapsulam caminhos para reduzir diferenças entre PowerShell e bash; evitar scripts que só funcionem com sintaxe Unix sem documentação.

| Comando-alvo | Introduzido | Efeito esperado |
| --- | --- | --- |
| `pnpm install --frozen-lockfile` | 00, após lock inicial | Instala JS reproduzivelmente |
| `pnpm infra:up` | 00 | Sobe somente PostgreSQL em loopback |
| `pnpm infra:down` | 00 | Para infraestrutura sem excluir volume |
| `pnpm dev:api` / `pnpm dev:web` | 00 | Inicia API e interface em terminais separados |
| `pnpm lint` / `pnpm typecheck` / `pnpm build` | 00 | Verificações JS reais |
| `uv sync --project services/edge --frozen` | 00 | Instala Python pelo lock |
| `pnpm db:generate` / `pnpm db:migrate` | 01 | Gera client e aplica migrações versionadas |
| `pnpm db:seed` | 01 | Cria dados locais idempotentes sem apagar dados |
| `pnpm test:api` / `pnpm test:contracts` | 02 | Testes de API/contratos com banco de teste separado |
| `pnpm demo:simulate` | 03 | Envia evento artificial rotulado, via API autenticada |
| `pnpm test:e2e` | 03 | Fluxo de navegador em ambiente de teste |
| `uv run --project services/edge radar-edge doctor` | 04 | Verifica modelo, arquivos e recursos sem expor segredos |
| `uv run --project services/edge radar-edge calibrate --config .local/edge.yaml` | 04 | Assistente local para delimitar piso |
| `uv run --project services/edge radar-edge run --config .local/edge.yaml` | 04/05 | Arquivo/poses; após 05, emissão real de candidatos |
| `uv run --project services/edge pytest` | 05 | Testes de regras, contrato e persistência |
| `uv run --project services/edge radar-edge evaluate --manifest .local/evaluation.json` | 05/08 | Replay e métricas em relatório privado |
| `uv run --project services/edge radar-edge reset-episode --config .local/edge.yaml --reason scene_reset` | 05 | Reset local explícito, com worker de captura parado e auditoria; não encerra incidente humano |
| `uv run --project services/edge radar-edge probe --config .local/edge.yaml` | 06/09 | Verifica fonte configurada, sem detectar incidente |
| `pnpm demo:check` | 08 | Checa pré-requisitos e consistência sem fabricar resultados |

Definir no Python a descoberta de testes de modo que o comando a partir da raiz funcione; o argumento `--project` do uv seleciona o projeto, não garante sozinho o diretório de trabalho de toda ferramenta. Não esconder falha com `|| true` ou placeholder que sempre retorna sucesso.

O primeiro `pnpm install`/`uv sync` da etapa 00 resolve e cria os locks; os comandos frozen passam a ser usados depois. A CLI `calibrate` precisa de interação do fundador quando não houver ambiente gráfico. Pode oferecer edição manual de pontos validados como alternativa, sem supor que a IA viu o vídeo.

## Sequência final de execução prevista

1. Instalar dependências e preparar `.env`/configuração privada.
2. Subir PostgreSQL; gerar client, aplicar migrações e seed idempotente.
3. Iniciar API e web; fazer login.
4. Cadastrar câmera e obter credencial de worker.
5. Obter modelo, verificar hash/licença e executar diagnóstico.
6. Selecionar fonte, calibrar e iniciar worker em outro terminal.
7. Demonstrar, revisar incidente e consultar relatório.
8. Parar worker e serviços de forma limpa, preservando banco/outbox.

Sem `docker compose down -v`, reset de banco, exclusão de `.local` ou regravação de vídeo como parte do fluxo normal. Testes usam banco dedicado claramente identificado; nunca apontar rotina de limpeza ao banco da demo.

## Falhas comuns a documentar durante a implementação

Webcam ocupada ou sem permissão; caminhos Windows; versão Python sem wheel; múltiplas distribuições `cv2`; falha de decoder; prisma generate ausente; ESM inconsistente; cookie/origin divergentes; banco indisponível; ROI inválida após rotação; token revogado; fim normal de arquivo. Solucionar a causa concreta e registrar o comando real, sem inventar uma compatibilidade universal.
