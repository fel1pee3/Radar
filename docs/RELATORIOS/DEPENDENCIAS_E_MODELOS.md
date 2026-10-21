# Dependências e modelos — inventário inicial

Data: 21/10/2026. Escopo: etapa 00, execução local Windows x64.
Versões diretas fixadas nos manifests; árvores completas e integridades nos arquivos
`pnpm-lock.yaml` e `services/edge/uv.lock`. Não foi escolhida uma licença para o código autoral.

## Ferramentas e infraestrutura

| Artefato | Versão usada | Fonte oficial / termos | Decisão |
| --- | --- | --- | --- |
| Node.js | 24.22.1 LTS | [Distribuição e checksums](https://nodejs.org/dist/v24.22.1/), [licenças](https://github.com/nodejs/node/blob/v24.22.1/LICENSE) | ZIP portátil Windows x64 em `.local/tools`; MIT e avisos de componentes incluídos |
| pnpm | 10.34.7 | [Pacote do projeto](https://www.npmjs.com/package/pnpm/v/10.34.7), MIT | `packageManager` exato; workspace somente TypeScript |
| Python | 3.12.15 | [CPython](https://www.python.org/downloads/), [distribuição usada pelo uv](https://github.com/astral-sh/python-build-standalone) | CPython instalado pelo uv; PSF e licenças dos componentes da distribuição |
| uv | 0.13.4 | [PyPI oficial](https://pypi.org/project/uv/0.13.4/), MIT OR Apache-2.0 | Bootstrap local, lock Python separado |
| PostgreSQL | 17.11 | [Imagem oficial](https://hub.docker.com/_/postgres), [licença PostgreSQL](https://www.postgresql.org/about/licence/) | Compose local; imagem inclui sistema Debian e componentes com termos próprios |
| Docker Desktop / Engine / Compose | 4.57.0 / 29.1.3 / 5.0.1 | [Docker Desktop](https://docs.docker.com/subscription/desktop-license/) | Instalação já existente; apenas iniciada. Elegibilidade/licença da conta do fundador não foi auditada e nenhum plano foi contratado |

SHA-256 calculado e conferido com `SHASUMS256.txt` oficial para
`node-v24.22.1-win-x64.zip`:
`d2046d28c2c3dcd211ac5145c0bf30e2047ef9dfb306693c8c6e2eccd8b95fa5`.

Digest observado de `postgres:17.11`:
`postgres@sha256:a63c1ea3f6a3a5a1621f97d2aba3b30faecfab4224c1b0000cc85ced57bb1939`.
O Compose fixa a tag de patch; o digest registra a imagem obtida nesta verificação.

## Dependências TypeScript diretas

Licenças declaradas consultadas no registro npm para as versões exatas. A tabela não
substitui o exame de avisos e componentes transitivos antes de distribuir binários.

| Pacote / fonte do publicador | Versão | Licença declarada | Uso |
| --- | --- | --- | --- |
| [next](https://www.npmjs.com/package/next/v/16.4.2), [eslint-config-next](https://www.npmjs.com/package/eslint-config-next/v/16.4.2) | 16.4.2 | MIT | App Router, rewrite e lint web |
| [react](https://www.npmjs.com/package/react/v/19.3.1), [react-dom](https://www.npmjs.com/package/react-dom/v/19.3.1) | 19.3.1 | MIT | Interface mínima |
| [@nestjs/common](https://www.npmjs.com/package/@nestjs/common/v/11.2.7), [@nestjs/core](https://www.npmjs.com/package/@nestjs/core/v/11.2.7), [@nestjs/platform-express](https://www.npmjs.com/package/@nestjs/platform-express/v/11.2.7) | 11.2.7 | MIT | API ESM; Nest requer Node >=20 |
| [reflect-metadata](https://www.npmjs.com/package/reflect-metadata/v/0.2.2) | 0.2.2 | Apache-2.0 | Metadados de decorators do Nest |
| [rxjs](https://www.npmjs.com/package/rxjs/v/7.8.2) | 7.8.2 | Apache-2.0 | Runtime Nest |
| [tailwindcss](https://www.npmjs.com/package/tailwindcss/v/4.3.3), [@tailwindcss/postcss](https://www.npmjs.com/package/@tailwindcss/postcss/v/4.3.3) | 4.3.3 | MIT | Estilos locais, sem fontes remotas |
| [typescript](https://www.npmjs.com/package/typescript/v/5.9.3) | 5.9.3 | Apache-2.0 | Strict, NodeNext na API e bundler na web |
| [eslint](https://www.npmjs.com/package/eslint/v/9.39.5), [@eslint/js](https://www.npmjs.com/package/@eslint/js/v/9.39.5) | 9.39.5 | MIT | Família compatível com plugins React/a11y usados pelo Next |
| [typescript-eslint](https://www.npmjs.com/package/typescript-eslint/v/8.72.0) | 8.72.0 | MIT | Lint TypeScript |
| [prettier](https://www.npmjs.com/package/prettier/v/3.9.10) | 3.9.10 | MIT | Formatação; especificações originais excluídas do autoformat |
| [@types/node](https://www.npmjs.com/package/@types/node/v/24.19.2) | 24.19.2 | MIT | Tipos Node 24 |
| [@types/react](https://www.npmjs.com/package/@types/react/v/19.3.0), [@types/react-dom](https://www.npmjs.com/package/@types/react-dom/v/19.3.0) | 19.3.0 | MIT | Tipos React |
| [concurrently](https://www.npmjs.com/package/concurrently/v/10.0.6) | 10.0.6 | MIT | Compiler watcher + execução ESM na API; requer Node >=22 |

O npm sinaliza ESLint 9 como fora de suporte. Foi mantido para evitar incompatibilidade
com os peers publicados `eslint-plugin-react@7.37.5` (`^9.7`) e
`eslint-plugin-jsx-a11y@6.10.2` (`^9`); ambos não declaram ESLint 10.
Nenhum peer conflitante foi observado na instalação. Reavaliar quando esses plugins
suportarem a próxima família; não atualizar major automaticamente.

Na etapa 00 não houve ORM ou migração. As dependências efetivamente introduzidas
na etapa 01 estão registradas abaixo; versões da web, Nest, Node, pnpm e Python
foram preservadas.

### Adições da etapa 01 — 21/10/2026

Licenças declaradas verificadas para as versões concretas no registro do publicador npm.

| Pacote / fonte | Versão | Licença declarada | Uso/decisão |
| --- | --- | --- | --- |
| [prisma](https://www.npmjs.com/package/prisma/v/7.10.1), [@prisma/client](https://www.npmjs.com/package/@prisma/client/v/7.10.1), [@prisma/adapter-pg](https://www.npmjs.com/package/@prisma/adapter-pg/v/7.10.1) | 7.10.1 | Apache-2.0 | Mesma versão CLI/client/adapter; aceita Node 24 e TS 5.9; gerador prisma-client/ESM com output explícito; sem adotar 8 RC |
| [pg](https://www.npmjs.com/package/pg/v/8.23.1) / [@types/pg](https://www.npmjs.com/package/@types/pg/v/8.23.1) | 8.23.1 | MIT | Driver/pool PostgreSQL e tipos, com timeouts explícitos |
| [argon2](https://www.npmjs.com/package/argon2/v/0.45.1) | 0.45.1 | MIT | Binário nativo carregado no Windows/Node 24; hash/verificação Argon2id reais nos testes |
| [@nestjs/swagger](https://www.npmjs.com/package/@nestjs/swagger/v/11.4.7) | 11.4.7 | MIT | OpenAPI derivado dos controllers/DTOs, JSON local sem UI extra |
| [class-validator](https://www.npmjs.com/package/class-validator/v/0.14.3) | 0.14.3 | MIT | Validação fechada de entrada no Nest |
| [class-transformer](https://www.npmjs.com/package/class-transformer/v/0.5.1) | 0.5.1 | MIT | DTOs e conversão explícita de limite de paginação |
| [@types/express](https://www.npmjs.com/package/@types/express/v/5.0.6) | 5.0.6 | MIT | Tipos do adapter Express 5 do Nest |
| [jest](https://www.npmjs.com/package/jest/v/30.5.2) / [@types/jest](https://www.npmjs.com/package/@types/jest/v/30.0.0) | 30.5.2 / 30.0.0 | MIT | Integração ESM, usando VM modules somente no processo de testes |
| [supertest](https://www.npmjs.com/package/supertest/v/7.3.1) / [@types/supertest](https://www.npmjs.com/package/@types/supertest/v/7.2.1) | 7.3.1 / 7.2.1 | MIT | HTTP real contra API compilada e banco exclusivo |

Referências da integração: [Prisma 7](https://www.prisma.io/docs/guides/upgrade-prisma-orm/v7),
[gerador](https://www.prisma.io/docs/orm/prisma-schema/overview/generators),
[OpenAPI Nest](https://docs.nestjs.com/openapi/introduction) e
[node-argon2](https://github.com/ranisalt/node-argon2). O config carrega `.env`
explicitamente pelas APIs do Node; não foi necessário adicionar dotenv.

Build scripts permitidos foram ampliados somente para Prisma/engines e argon2.
Os scripts de `@scarf/scarf` (telemetria de instalação) e `@parcel/watcher` ficaram
bloqueados/não necessários aos comandos verificados, registrados na configuração
do workspace. Avisos de glob transitivo e VM modules do Jest não foram tratados
como falhas de execução nem ocultados. Não foi feita auditoria completa de todas
as dependências transitivas ou uma aprovação de redistribuição comercial.

## Python: artefatos instalados

| Pacote / fonte oficial | Versão | Licença/termos observados | Dependências e decisão |
| --- | --- | --- | --- |
| [mediapipe](https://pypi.org/project/mediapipe/1.1.1/) | 1.1.1 | Apache 2.0 declarada no pacote | Tasks/PoseLandmarker importados; depende de opencv-contrib-python, NumPy, matplotlib, flatbuffers, absl-py, certifi e sounddevice |
| [opencv-contrib-python](https://pypi.org/project/opencv-contrib-python/5.0.0.93/) | 5.0.0.93 | Metadado Apache 2.0; wrapper `cv2/LICENSE.txt` MIT; OpenCV Apache-2.0 e avisos de terceiros em `cv2/LICENSE-3RD-PARTY.txt` | Único fornecedor cv2, com GUI WIN32UI e backends DirectShow/Media Foundation compilados |
| [pydantic](https://pypi.org/project/pydantic/2.14.1/) | 2.14.1 | MIT | Base de validação do futuro worker; pydantic-core 2.50.1 |
| [httpx](https://pypi.org/project/httpx/0.28.1/) | 0.28.1 | BSD-3-Clause | Base HTTP do futuro worker; nenhum envio implementado |
| [ruff](https://pypi.org/project/ruff/0.17.1/) | 0.17.1 | MIT | Lint/formatter de desenvolvimento |
| [hatchling](https://pypi.org/project/hatchling/1.32.4/) | 1.32.4 | MIT | Backend de build exato em ambiente isolado |

Wheels selecionados para esta máquina, com hashes registrados no `uv.lock`:

- `mediapipe-1.1.1-py3-none-win_amd64.whl`: SHA-256 `a4b27829e808cd659e7cf481cbbbfc31917092a1ebcb7eafed2395dbabcd2499`.
- `opencv_contrib_python-5.0.0.93-cp37-abi3-win_amd64.whl`: SHA-256 `461622db95c964652d4d8fda171034961c3de270f78a6095aaad31050771774a`.

`cv2.getBuildInformation()` informou OpenCV 5.0.0 e FFmpeg pré-compilado habilitado.
O aviso incluído no wheel identifica FFmpeg com texto LGPL 2.1. Não foi feita uma
auditoria completa dos codecs/build flags para redistribuição comercial. Instalação
local não constitui aprovação para empacotar o FFmpeg; nenhum wheel/DLL/build foi
adicionado ao Git. Preservar e revisar esses avisos ao preparar uma distribuição.

Transitivos relevantes observados: NumPy 2.5.4 (metadado com BSD-3-Clause, 0BSD,
MIT, Zlib e CC0-1.0), matplotlib 3.11.2 (avisos próprios e de fontes/componentes),
flatbuffers 25.12.19 (Apache 2.0), sounddevice 0.5.6 (MIT), certifi 2026.10.19
(MPL-2.0). A árvore exata dos 31 pacotes do ambiente está no lock; não foi alegada
uma auditoria de licença completa de todas as dependências transitivas.

## Modelos, vídeos e datasets

Nenhum bundle de pose foi obtido, carregado ou versionado. URL, SHA-256 calculado
e termos do modelo serão registrados na etapa 04 antes de inferência.
Nenhum vídeo, dataset ou câmera foi utilizado. A captura de tela de validação é
somente da página vazia do projeto e permanece em `.local/`, fora do Git.
