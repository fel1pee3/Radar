# Fontes técnicas e licenças

[Voltar ao README central](../README.md)

Consulta técnica em **21/10/2026**. As decisões de arquitetura, valores de parâmetros, limites e etapas são propostas específicas deste projeto, não promessas dos fornecedores. Links podem mudar; fixar as versões efetivamente usadas na implementação.

## Fontes primárias consultadas

| Fonte | Uso no plano |
| --- | --- |
| [Node.js — Releases](https://nodejs.org/en/about/previous-releases) | Escolha da linha 24 LTS |
| [NestJS — First steps](https://docs.nestjs.com/first-steps) | Fundação do backend |
| [NestJS — Prisma](https://docs.nestjs.com/recipes/prisma) | Compatibilidade de geração, configuração e módulos |
| [Next.js — Installation](https://nextjs.org/docs/app/getting-started/installation) | Instalação da família 16 |
| [Prisma 7 — Requirements](https://www.prisma.io/docs/orm/v7/reference/system-requirements) | Compatibilidade com Node 24 |
| [Prisma — Upgrade to v7](https://www.prisma.io/docs/guides/upgrade-prisma-orm/v7) | Gerador, configuração e adapter do banco |
| [uv — Working on projects](https://docs.astral.sh/uv/guides/projects/) | Ambiente Python, projeto e lockfile |
| [MediaPipe — Setup Python](https://developers.google.com/edge/mediapipe/solutions/setup_python) | Ambiente e instalação das Tasks |
| [MediaPipe — Pose Landmarker](https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker) | Landmarks corporais e bundles Lite/Full/Heavy |
| [MediaPipe — Python guide](https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker/python) | Modos e uso temporal de poses |
| [ONVIF — Profile T](https://www.onvif.org/profiles/profile-t/) | Referência de recursos de vídeo; não confirma esta câmera |
| [Kapbom — página pública](https://kapbom.com.br/) | Busca de documentação; acesso RTSP da KAP-S069 permaneceu não confirmado |

Contexto de produto: dossiê `Dossie_Estrategico_Radar_de_Acontecimentos.pdf`, preparado em 20/10/2026. Não é dependência de execução e não precisa ser colocado no repositório. A decisão atual de demo antes de parceiro está registrada neste pacote.

## Inventário que a implementação deverá preencher

O [inventário inicial](RELATORIOS/DEPENDENCIAS_E_MODELOS.md) foi criado na etapa 00 com pacote/artefato, versão exata, fonte oficial, licença/termos observados, dependências relevantes e decisão de uso. Atualizá-lo nas próximas etapas. Para modelos: URL de origem, SHA-256 calculado e identificação do bundle. Para dataset: origem, autorização, direitos de uso/redistribuição, finalidade e retenção. Nenhum modelo ou dataset foi obtido na etapa 00.

Separar licença do código, licença do modelo e direitos do vídeo. A licença dos exemplos de uma página não comprova os termos dos pesos. Um arquivo disponível publicamente não é automaticamente redistribuível ou adequado a uso comercial.

Não incluir pesos, vídeos pessoais ou builds FFmpeg no ZIP/repositório por conveniência. Download posterior deve seguir fonte e integridade documentadas. Para OpenCV, registrar o wheel e backend de vídeo; se FFmpeg for distribuído, registrar build/codecs e obrigações aplicáveis.

Ultralytics/YOLO não é dependência desta baseline. Se uma etapa futura o propuser, avaliar os termos específicos antes da adoção em produto fechado; não presumir que um tutorial torna seu uso irrestrito. Não escolher uma licença aberta para o código autoral sem decisão do fundador. Repositório privado pode preservar a estratégia comercial, mas não elimina obrigações das dependências.

Este pacote não contém código de produto de terceiros nem modelos para redistribuição. As verificações de licenças dos artefatos concretos serão registradas quando forem efetivamente selecionados e obtidos.

Complemento 23/10/2026: candidato RTMO-s em adaptador local próprio com ONNX
Runtime 1.23.2 (MIT), sem depender de RTMLib. Fontes primárias: catálogo
[MMPose/RTMO](https://github.com/open-mmlab/mmpose/blob/main/projects/rtmo/README.md),
[LICENSE](https://github.com/open-mmlab/mmpose/blob/main/LICENSE) e
[exceções](https://github.com/open-mmlab/mmpose/blob/main/LICENSES.md).
Código MMPose declara Apache 2.0; a lista de exceções consultada não lista RTMO.
O ZIP oficial não traz licença específica dos pesos. Não foi verificada liberação
comercial por artefato ou pelos sete datasets de treinamento. Essa lacuna fica
registrada, sem conclusão legal de que os pesos sejam irrestritos ou proibidos.
Peso obtido explicitamente permanece privado, sem redistribuição ou treinamento;
uso do candidato delimitado à bancada experimental. Fonte, hashes, versões e
comandos em [integração RTMO](RELATORIOS/INTEGRACAO_RTMO_ETAPA_08.md).

CAUCAFall recebido em 23/10: [V4 / DOI 10.17632/7w7fccy7ky.4](https://data.mendeley.com/datasets/7w7fccy7ky/4),
autores Jose Camilo Eraso, Elena Muñoz, Mariela Muñoz e Jesus Pinto. Fonte oficial
declara CC BY 4.0 e quedas encenadas/ADL. Doze AVIs fornecidos para avaliação
local, sem publicação ou treinamento; atribuição, caminhos/hashes e diferenças
entre metadados de captura e arquivos recebidos no
[relatório CAUCAFall](RELATORIOS/CAUCAFALL_ETAPA_08.md). V5 é revisão distinta;
não atribuir os bytes V4 a ela. A licença do dataset não resolve os termos
específicos dos pesos RTMO nem comprova eficácia assistencial.
