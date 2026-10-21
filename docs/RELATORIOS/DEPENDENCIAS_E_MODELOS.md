# Dependências e modelos — inventário inicial

Data: 21/10/2026. Escopo: etapas 00–04, execução local Windows x64; validação 04 concluída em um arquivo autorizado.
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

## Adições da etapa 02: contratos e testes

| Pacote / fonte oficial | Versão | Licença declarada | Uso |
| --- | --- | --- | --- |
| [ajv](https://www.npmjs.com/package/ajv/v/8.20.0) | 8.20.0 | MIT | JSON Schema draft-07 em TS/API; sem coerção |
| [ajv-formats](https://www.npmjs.com/package/ajv-formats/v/3.0.1) | 3.0.1 | MIT | UUID/formats; date-time UTC estrito compartilhado é validado explicitamente |
| [json-schema-to-typescript](https://www.npmjs.com/package/json-schema-to-typescript/v/16.0.0) | 16.0.0 | MIT | Geração/verificação de tipos, somente desenvolvimento |
| [jsonschema](https://pypi.org/project/jsonschema/4.26.0/) | 4.26.0 | MIT | Validação Python dos mesmos schemas/exemplos, sem captura |
| [pytest](https://pypi.org/project/pytest/9.1.1/) | 9.1.1 | MIT | Testes de contratos, somente desenvolvimento |

Versões/licenças diretas consultadas nos metadados oficiais npm/PyPI.
Referências de implementação: [Ajv](https://ajv.js.org/guide/getting-started.html),
[jsonschema](https://python-jsonschema.readthedocs.io/en/stable/validate/) e
[locks PostgreSQL 17](https://www.postgresql.org/docs/17/explicit-locking.html).
As árvores completas estão nos locks: o ambiente Python passou de 31 para 41
pacotes, preservando as versões anteriores e somente opencv-contrib-python como
fornecedor de cv2. Não houve atualização de família de framework, ORM ou visão.
Não foi feita auditoria completa de licenças transitivas/redistribuição comercial.

## Adições da etapa 03: navegador e simulador

`@playwright/test` **1.64.1**, somente desenvolvimento, licença declarada
Apache-2.0, Node>=20 conforme metadados oficiais de
[npm](https://www.npmjs.com/package/@playwright/test/v/1.64.1).
`playwright`/`playwright-core` transitivos da mesma versão estão no lock.
Instalado Chromium/Chrome for Testing **156.0.8078.4**, revisão 1248, pelos
downloads oficiais da ferramenta. Os binários permanecem fora do Git; não foi
feita aprovação de redistribuição desses binários. O instalador gerenciou seu
cache local e removeu revisões de navegador que considerou não utilizadas.

Web passou a depender de `@radar/contracts` via workspace para os tipos.
Simulador usa APIs nativas do Node e contratos existentes; nenhuma dependência
de runtime externa adicional. Frameworks e versões Python preservados.
Referências consultadas: [configuração Playwright](https://playwright.dev/docs/test-configuration),
[efeitos/cleanup React](https://react.dev/reference/react/useEffect) e
[self hosting/cache Next](https://nextjs.org/docs/app/guides/self-hosting).

## Modelos, vídeos e datasets (registro histórico após a03)

Nenhum bundle de pose foi obtido, carregado ou versionado. URL, SHA-256 calculado
e termos do modelo serão registrados na etapa 04 antes de inferência.
Nenhum vídeo, dataset ou câmera foi utilizado. Screenshots da etapa 03 mostram
somente dados/pose sintéticos e permanecem em `.local/`, fora do Git.

## Adições da etapa 04 — visão local em arquivo

| Pacote | Versão | Origem/termos | Decisão |
| --- | --- | --- | --- |
| PyYAML | 6.0.3 | [PyPI oficial](https://pypi.org/project/PyYAML/6.0.3/), MIT; metadados consultados | safe_load + validação fechada Pydantic; única dependência nova no ambiente |
| NumPy | 2.5.4 | Mesma distribuição e termos já registrados acima | Agora dependência direta porque o adaptador usa arrays; sem trocar versão |

Lock passa de 41 para 42 pacotes. MediaPipe 1.1.1/OpenCV5.0.0.93/Python 3.12.15 e
demais versões preservados. Único fornecedor de cv2: opencv-contrib-python.
PyYAML wheel cp312-win_amd64 no lock:
`5fcd34e47f6e0b794d17de1b4ff496c00986e1c83f7ab2fb8fcfe9616ff7477b`.
Não se introduziu biblioteca FFmpeg/PyAV ou segundo OpenCV. Decode usa backend
FFmpeg já incluído no wheel; avisos de redistribuição anteriores permanecem.

### Bundle realmente obtido

- Identificação: `pose-landmarker-lite-float16-v1`.
- Origem oficial versionada: [Google Storage — Lite float16/1](https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task).
- Destino privado: `.local/models/pose_landmarker_lite.task`; **5.777.746 bytes**.
- SHA-256 calculado: `59929e1d1ee95287735ddd833b19cf4ac46d29bc7afddbbf6753c459690d574a`.
- ZIP/bundle contém `pose_detector.tflite` e `pose_landmarks_detector.tflite`.
- Procedimento reproduzível: `uv run --project services/edge --frozen radar-edge model-fetch`.
  HTTPS, URL/version/hash constantes; arquivo divergente é rejeitado, sem sobrescrita.
- Carregado e executado de verdade com Tasks 1.1.1, CPU, VIDEO, num_poses=2 e
  máscaras desativadas; executado em vídeo sintético sem pessoas e no arquivo
  autorizado `bancada-01`, com 89 observações de pose em cada replay completo.

Termos do modelo: o [Model Card BlazePose GHUM3D](https://storage.googleapis.com/mediapipe-assets/Model%20Card%20BlazePose%20GHUM%203D.pdf),
ligado pelo [catálogo oficial de bundles](https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker),
inclui Lite/Full/Heavy e declara Apache License 2.0 na seção LICENSED UNDER (página2).
Essa é a evidência referente ao modelo; não se utilizou o rodapé de licença dos
exemplos para concluir a licença dos pesos. O cartão limita o uso pretendido a
pose/fitness e não a decisões críticas de vida; seus resultados não medem este
notebook nem certificam detecção de quedas. Pesos e documentos baixados não são
redistribuídos no Git. Não foi feita aprovação de distribuição comercial.

### Biblioteca e tráfego

O [aviso MediaPipe Tasks vigente](https://developers.google.com/edge/mediapipe/solutions/tasks#mediapipe_tasks_privacy_notice),
datado 05/06/2026, declara input no dispositivo e coleta de métricas de uso do SDK.
A fonte pública de logging usa um dummy logger, mas isso não prova o comportamento
do wheel: a DLL instalada, de 62.025.728 bytes, contém referências a Clearcut e
play.googleapis.com. Presença dessas strings não prova envio observado. A API
Python instalada foi inspecionada; não foi encontrado opt-out documentado nela.

O pipeline autoral não envia vídeo/poses e não importa cliente HTTP; somente o
comando explícito model-fetch usa HTTPS. Não houve captura/auditoria de rede nem
validação em ambiente isolado; não se afirma ausência total de tráfego nativo.
Não houve regra de firewall, mudança de permissões ou troca de pacote para
contornar a questão. Validar isolamento antes de prometer operação sem tráfego.

### Material usado

Vídeo sintético gerado localmente por OpenCV, sem pessoa, áudio ou imagem
de terceiros, para infraestrutura:
`synthetic-04-infrastructure`, SHA-256
`e396a18be5813bc10d79a776613a03a27875dfdcbc829e50d635bdbf93de3dfe`,
320×240,10fps,20frames/2s. Vídeo/relatórios/preview sintético ficam em
`.local/etapa04`.

Arquivo real fornecido pelo fundador no diretório reservado do projeto:
`bancada-01`, SHA-256
`3c361aee3f49e2e6ac2688e3afb53622ffd15451ead69874b3e0a76c9cd090c0`,
4.744.892 bytes, 1920×1080, 530 frames, aproximadamente 17,684 s. O pedido de uso
autoriza processamento local; origem/autoria não foram verificadas de forma
independente e não se pressupõe autorização de redistribuição. O vídeo e seu
nome original permanecem privados. Manifesto local registra `participant-01`,
`session-04-01` e `environment-04-01`; retenção fica sob gestão do fundador,
sem prazo de exclusão configurado. Não houve busca em pastas pessoais.

O fundador selecionou o piso na GUI e confirmou pose/região na prévia. Três
execuções terminaram normalmente, sem gravar frames nem exportar poses. Medidas
e limites no [relatório 04](ETAPA_04.md). Um arquivo não constitui dataset de
avaliação de eficácia; múltiplas pessoas reais não foram testadas.
