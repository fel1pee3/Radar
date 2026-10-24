# Dependências e modelos — inventário

Atualização: 24/10/2026. Escopo: etapas 00–08 verificadas no alcance revisado da
demo de bancada D50/D51; execução local Windows x64. Registros anteriores são históricos, com complementos
por etapa. Full positivo em calibração não constitui avaliação independente.

Sessão física final: RTMO-s CPU experimental, mesmo SHA fixado, webcam 0/DSHOW
640×480 e piso v3, sem mudança de dependências/modelos. 2799 análises em 600,660 s,
sem eventos; trecho voluntário no chão <10 s sem alerta permanece possível perda/
inconclusivo. Uso comercial/redistribuição dos pesos não liberados por este teste.
[Resultados e limites](SESSAO_WEBCAM_10MIN_ETAPA_08.md).

## Verificação na etapa 08

Nenhuma dependência, família, lock ou bundle novo. Instalações frozen repetidas
em node_modules/.venv novos, com caches externos declarados. Full foi novamente
obtido pela URL oficial versionada durante a preparação limpa e seu SHA-256
`5134a3aad27a58b93da0088d431f366da362b44e3ccfbe3462b3827a839011b1`
foi conferido antes da inferência real em vídeo sintético sem pessoa. Artefatos
nativos, modelo e ferramentas não acompanham a candidata local de fontes.

Registro da preparação `.local/etapa08/clean-install.json`; [matriz final](VALIDACAO_MVP.md).
Ressalvas do Model Card/telemetria, licenças transitivas e redistribuição de codecs
permanecem. Funcionamento offline ainda não foi comprovado; não se afirma ausência
de tráfego externo do SDK. Não houve nova auditoria jurídica de licenças.
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

## Adições da etapa 05 — motor e entrega local

Nenhuma dependência ou lockfile alterado. SQLite vem com o Python nativo; HTTPX
0.28.1 e jsonschema 4.26.0 já estavam fixados e agora são usados na entrega local
e validação do envelope real. MediaPipe/OpenCV/modelo/termos da 04 preservados.
Nenhum serviço externo ou modelo novo foi introduzido.

O arquivo autorizado bancada-01 foi processado pelo motor floor-v0.1 em dois
ritmos, com zero candidatos/eventos; hash e calibração da 04 preservados.
Integração Python→SQLite→API→PostgreSQL validada com observações **sintéticas**.
Não se confunde esse teste com inferência positiva real. Prova positiva e painel
continuam pendentes no [relatório 05](ETAPA_05.md).

Depois foram processados `piso-a` (lateral, 109 observações) e `piso-b` (vista de
cima, 73 observações), fornecidos pelo fundador, com calibrações próprias marcadas
por ele. Ambos terminaram sem evento: seis candidatas sem continuidade no lateral
e nenhuma pose elegível na vista de cima. Hashes, medidas e limitações registrados
no relatório 05; nomes originais, vídeos e manifestos continuam privados. Modelo,
política, gates e licenças não foram alterados para esses ensaios.

Novo material `piso-c-ai`, confirmado pelo fundador como vídeo gerado no Gemini:
SHA-256 `22ffc2aaccb4d086da652b8919b3720a0ac3f4fe74ed5751f410f2f59fdd0318`,
3.134.134 bytes, 24 fps/10 s. Identificado como SYNTHETIC nos manifestos locais.
Produziu um evento PERSON_ON_FLOOR local, sem HTTP, usando o mesmo modelo/política.
Não substitui filmagem real nem valida eficácia. Não foram aprovados termos de
redistribuição/treinamento do conteúdo gerado; arquivo permanece privado.

Quarta filmagem real `piso-d`, confirmada como câmera/celular pelo fundador:
SHA-256 `76495b5cfff2c33b0c505252832ce5e798222ab14e29565a05fe2199d0fe4a65`,
1.791.840 bytes, 480×854, aproximadamente 23,9591 fps/15,5265 s. Piso e prévia
confirmados por ele: orientação correta e pessoa deitada no chão. Processamento
completo gerou 78 observações, 58 elegíveis, zero candidatas/eventos por limites
de ângulo/proporção em 2D. Mesmo modelo/política, sem ajuste para forçar disparo.
Uso local, retenção manual e mídia privada; origem independente e redistribuição
não verificadas/autorizadas. Resultado desfavorável detalhado no relatório 05.

Mais dois arquivos descritos pelo fundador como filmagens reais da internet:
`piso-e-05`, SHA-256
`efbb2c6c4721df503426918056b5ed3f233f77b55595b70dce9f9d68c48e650f`,
10.206.712 bytes; e `piso-f-07`, SHA-256
`86a20851a1d3bfacbe11d8977972f95a256893b80cd4de66dc7bb224a4dca55b`,
9.262.980 bytes. Fonte, autoria e licença não verificadas independentemente;
sem autorização de redistribuição presumida. Ambos foram calibrados manualmente
e processados por completo com o mesmo modelo/política, sem evento. Resultados
51/45 observações e 0/6 candidatas registrados no relatório 05. Mídia privada,
retenção manual; nenhuma alteração de dependência, lock ou peso de modelo.

### Comparação e seleção explícita do Full na etapa 05

Nenhuma dependência Python nova. Bundle adicional oficial
`pose-landmarker-full-float16-v1`, obtido via URL versionada
`https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/1/pose_landmarker_full.task`.
9.398.198 bytes, SHA-256 calculado
`5134a3aad27a58b93da0088d431f366da362b44e3ccfbe3462b3827a839011b1`.
Peso privado em `.local/models/pose_landmarker_full.task`, registry fixado e
reprodução por `radar-edge model-fetch --variant full`. Sem redistribuição de pesos.

O [catálogo oficial](https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker#models)
vincula Lite/Full/Heavy ao mesmo
[Model Card](https://storage.googleapis.com/mediapipe-assets/Model%20Card%20BlazePose%20GHUM%203D.pdf),
que declara Apache 2.0 para o modelo (página 2). O uso pretendido é pose/fitness;
o documento lista vigilância fora desse escopo e não destina o modelo a decisões
críticas à vida. Isso registra limitações de adequação/validação, sem inventar
termo adicional que revogue Apache. Não foi feita aprovação de uso comercial ou
assistencial. D30 sobre métricas nativas permanece aplicável.

Comparação real manteve duas poses e gates iguais: Full melhorou piso-f-07 de
15 para 40 observações elegíveis e gerou um PERSON_ON_FLOOR aos 6000 ms, entregue
à API/painel. Não melhorou todos os arquivos. Lite permanece como padrão das
configurações antigas. Novas configs Full/outboxes e manifestos preservam
calibrações e falhas anteriores. Modelo selecionado é identificado por SHA no
fingerprint e por ID no evento, sem troca automática. Métodos/resultados na
[investigação 05](INVESTIGACAO_ETAPA_05.md). Os arquivos usados para selecionar o
modelo continuam CALIBRATION e não constituem avaliação independente.


## Complemento da etapa 07 — JPEG privado

Sharp 0.35.5 foi promovido a dependência direta da API com pnpm e versão exata;
já era a versão transitiva da web. Node 24.22.1 preservado, lock atualizado e
instalação frozen verificada. `package.json` instalado declara Apache-2.0.
Decodificação/reencodificação real, remoção EXIF e limites foram testados, sem
capturar imagem pessoal. Bundles nativos/libvips continuam sujeitos aos respectivos
avisos da distribuição; não é um parecer de conformidade comercial/legal.
Fontes primárias: [constructor](https://sharp.pixelplumbing.com/api-constructor/)
e [output/metadata](https://sharp.pixelplumbing.com/api-output/).
Nenhuma dependência Python/modelo/cv2 foi trocada nesta etapa.

## Complemento da etapa 08 — novos vídeos e procedência recuperada

Atualização de 23/10: ONNX Runtime 1.23.2 (MIT) integrado ao ambiente operacional
com uv/lock para o adaptador RTMO opcional. MediaPipe/OpenCV/NumPy anteriores
preservados, importados e usados em inferência real no mesmo ambiente; somente
opencv-contrib-python fornece cv2. RTMLib continua exclusivamente na pesquisa
privada, não no produto. Código do adaptador próprio com modelo oficial fixado
por SHA; nenhuma redistribuição dos pesos. Resultado/termos delimitados em
[INTEGRACAO_RTMO_ETAPA_08](INTEGRACAO_RTMO_ETAPA_08.md). A descrição abaixo
registra o estado anterior da pesquisa isolada.

Pesquisa posterior da cadeira, fora do ambiente operacional: projeto uv privado
com Python 3.12.15, RTMLib 0.0.16, ONNX Runtime 1.23.2, NumPy 2.5.4 e
opencv-contrib-python 5.0.0.93; lock próprio. RTMLib declara duas distribuições
de cv2; override explícito da pesquisa exclui opencv-python, e auditoria confirmou
somente contrib instalado/importado. Não adotar esse ambiente como substituto
do worker sem revisão de compatibilidade. Código RTMLib e MMPose declara Apache
2.0; licença específica do artefato/modelo não foi comprovada separadamente.
RTMO-s ONNX obtido do catálogo oficial OpenMMLab, SHA-256 local
`d0703d40d19f3921da51ae725402d5fdae4d2478c7442072d3101bd396f370d8`;
não há full digest publicado verificado. ZIP sem arquivo LICENSE, apenas
deploy/detail/pipeline JSON e ONNX. Uso restrito à comparação privada, sem
treinamento ou redistribuição. O fundador confirmou melhora visual na cadeira;
não há integração operacional nem equivalência entre scores RTMO e os gates
visibility/presence atuais. [Fontes e resultados](INVESTIGACAO_CADEIRA_ETAPA_08.md).

Complemento de 23/10: RTMO-t body7/416 obtido do catálogo oficial somente para
pesquisa privada, sem entrar no registro/configuração operacional. ONNX
27342008 bytes, SHA-256
`20aad6e2e42359cac1c5b4a0b2da00e29bfe91a72a782fdcf287d273a04c1b24`.
Mesmo ONNX Runtime/NumPy/cv2 já instalados, sem lock ou dependência nova. Mais
rápido e com mais perdas de pose no conjunto testado; não adotado. ZIP, URL,
hashes, limitações de licença e medições em
[QUADRO_A_QUADRO_ETAPA_08](QUADRO_A_QUADRO_ETAPA_08.md). Novo experimento de
filtro visual tem implementação própria e não instala pacote externo.

Posteriormente, Heavy float16/v1 foi obtido **somente para comparação privada**,
sem alteração do modelo ativo ou registro de variantes do produto. Bundle oficial
30.664.242 bytes, SHA-256 calculado
`64437af838a65d18e5ba7a0d39b465540069bc8aae8308de3e318aad31fcbc7b`,
verificado contra tamanho/MD5 da API oficial de metadados. O Model Card comum
declara Apache 2.0, com as mesmas limitações de uso/adequação documentadas.
Fonte, metadados e comparação em [COMPARACAO_POSE_ETAPA_08](COMPARACAO_POSE_ETAPA_08.md).
Resultado desfavorável; Heavy não adotado. Arquivo .research.task privado,
nenhuma dependência/lock/threshold ou configuração operacional alterada.

Nenhuma dependência, peso ativo, threshold ou lockfile foi alterado para os novos
ensaios. O [inventário de materiais 08](MATERIAIS_ETAPA_08.md) associa os 21 curtos
novos ao caminho completo GMDCSA24 por Git blob SHA-1, registra SHA-256 local e
revisão da fonte. A raiz do repositório declara MIT, copyright 2024 Ekram Alam.
Os dois episódios Third Age Yoga with Andy Gilats têm nome/tamanho/SHA-1
compatíveis com os metadados do Internet Archive, que declaram CC BY 3.0.
Links primários e hashes individuais estão naquele relatório; arquivos continuam
privados, sem redistribuição ou treinamento de pesos.

A procedência antes não confirmada de `piso-e-05` e `piso-f-07` foi resolvida
posteriormente: os hashes históricos correspondem a `Subject 3/Fall/05.mp4` e
`Subject 3/Fall/07.mp4` do mesmo repositório, revisão
`5abac7693229900cf80f722e878fbb119211fc1c`. Cópias recuperadas por hash ficam em
caminhos separados dos novos 05/07 do Subject 1. A descrição anterior reflete
o que era conhecido naquela etapa; ambos históricos continuam CALIBRATION.
Não se infere autorização adicional de direitos de imagem ou uso assistencial
a partir da licença do repositório. Material usado para ajustar/selecionar
parâmetros/modelos permanece CALIBRATION; a avaliação reservada foi registrada
antes da inferência e tem anotações provisórias do assistente.

CAUCAFall V4, DOI 10.17632/7w7fccy7ky.4: doze AVIs novos recebidos na etapa 08,
20 FPS/720×480 verificados, 143800 ms e hashes individuais no
[relatório CAUCAFall](CAUCAFALL_ETAPA_08.md). Página oficial Mendeley declara
CC BY 4.0; autores/atribuição preservados. Uso reservado para avaliação local,
sem treino/publicação; fontes, direitos do vídeo e termos do modelo separados.
Fundador confirmou novidade, os 12 pisos e as propostas de cenas/intervalos
antes da primeira inferência. Nenhuma dependência/modelo/lock foi alterado.
