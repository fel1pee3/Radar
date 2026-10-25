# Evolução do detector — reserva de 16 vídeos e candidato corporal

Data: 24/10/2026. **PREPARAÇÃO/REVISÃO CONCLUÍDAS; NÚCLEO NÃO APROVADO.**
Atualização da revisão humana: cenas/intervalos dos 16 confirmados; contextos
iniciais reprovados. Os 16 contornos foram refeitos e aprovados pelo fundador,
depois congelados antes de qualquer previsão. Avaliação executada, com resultado
insuficiente em [relatório próprio](EVOLUCAO_DETECTOR_04.md). Fases abaixo.
Continuação da solicitação de núcleo funcional, D52. Não reabre o fechamento
histórico da etapa 08 nem inicia a 09. Nenhum commit, push ou deploy.

## Resultado entregue

Encontrada a pasta privada `.local/videos/Radar_16_Videos_Novos`, com 16 MP4,
README, CSV, proveniência JSON, licenças e três folhas de contato existentes.
O fundador confirmou que os arquivos nunca foram usados para ajustar, treinar
ou escolher modelos do Radar, inclusive em outro chat. Foram mantidos como
**RESERVED_PENDING_ANNOTATION_AND_PROTOCOL**, sem inferência ou treinamento.

Inventário SHA-256/caminho completo da fonte, comparação com os materiais
anteriores, decodificação integral e verificação dos bytes publicados concluídos.
Preparadas propostas de intervalos, pisos/exclusões e janela de conferência
do vídeo original, sem esqueleto ou modelo. Confirmação humana das cenas e dos
contornos permanece pendente; assistir/decodificar sozinho não a produz.

Candidato corporal LINEAR_BODY_V2 implementado, treinado e selecionado apenas
com o desenvolvimento antigo. Referência de código/artefato/parâmetros congelada
antes de qualquer previsão na reserva. Não demonstra por si melhora nesses 16
arquivos, solução das perdas antigas ou funcionamento no cômodo do fundador.

## Ambiente e preservação

Windows 11 Pro 10.0.26200, PowerShell 5.1, Ryzen 5 5625U (6C/12T), cerca de
15,4 GiB de RAM. Node 24.22.1, pnpm 10.34.7, Python 3.12.15, uv 0.13.4.
NumPy 2.5.4, opencv-contrib-python 5.0.0.93, MediaPipe 1.1.1 e ONNX Runtime
1.23.2 preservados. RTMO-s CPU, quatro threads intra/inter=1. Nenhuma instalação,
troca de dependência/lockfile ou migração nesta rodada. Sem webcam aberta.

HEAD 0778e028156bf40ec7ac158ebefdc20010efc041; alterações anteriores preservadas,
sem staging. Baseline e congelamento do candidato de 35 atributos continuam
privados e inalterados. PostgreSQL de demonstração não foi alterado pelo teste
HTTP: banco/container/volume exclusivos do teste removidos ao terminar.

## Procedência e composição

**16 hashes distintos, 4957 quadros decodificados, 195995 ms de conteúdo.**
SHA/tamanho/metadados correspondem aos documentos recebidos. Nenhum coincide
com os 41 vídeos do inventário inicial ou com os históricos recuperados.
Isso comprova identidade dos arquivos e ausência dessas duplicatas, não
independência estatística entre seus recortes.

| IDs locais | Conteúdo proposto, ainda a confirmar | Agrupamento da fonte |
| --- | --- | --- |
| intake16-01 a 04 | Pessoa já no chão, quatro orientações no quarto | IndoorActionDataset S0, Bedroom 1; uma gravação 20201218_112724-114747 |
| intake16-05 e 06 | Pessoa já no chão na sala | IndoorActionDataset S0, LivingRoom 1; uma gravação 20210114_123008-125158 |
| intake16-07 e 08 | Cadeira e pegar objeto | GMDCSA24 Subject 4, ADL/13.mp4 e ADL/17.mp4; sessão desconhecida |
| intake16-09 e 12 | Sentar e limpar, vista frontal da sala | IndoorActionDataset S4, gravação 20210129_103900-104556 |
| intake16-10 e 13 | Sentar e limpar, outro enquadramento da sala | IndoorActionDataset S4, gravação 20210129_163405-164001 |
| intake16-11 | Limpar a sala | IndoorActionDataset S0, gravação 20210114_150036-151348 |
| intake16-14 | Cozinha vazia | IndoorActionDataset S0, gravação 20201218_131544-132708 |
| intake16-15 e 16 | Sala de jantar vazia e caminhar nela | IndoorActionDataset S2, gravação 20201223_144313-144909 |

São seis candidatos positivos da **mesma pessoa em duas gravações originais**,
dez negativos, sete gravações IAD identificadas e um agrupamento GMD conservador
com sessão desconhecida. Não são 16 pessoas/sessões independentes. Dois negativos
parecem vazios e precisam dessa confirmação explícita para usar saúde de captura
na avaliação; ausência de pose não prova ambiente vazio. Parte do corpo pode
ficar cortada no vídeo de pegar objeto: manter esse período e informar cobertura.

Os 14 clipes IAD correspondem aos membros exatos do ZIP oficial, comparados por
SHA-256 e CRC32 com leitura HTTP Range: 16882937 bytes em 45 solicitações. O
ZIP de 977124409 bytes não foi baixado integralmente nem seu MD5 recalculado.
Os dois GMD correspondem aos bytes publicados na revisão
5abac7693229900cf80f722e878fbb119211fc1c. Nenhuma mídia foi enviada a terceiros,
copiada para o Git ou modificada. Respostas públicas de metadados e associação
de cada arquivo ao caminho completo permanecem no inventário privado.

Fontes: [IndoorActionDataset v1/Zenodo](https://zenodo.org/records/14551902),
[repositório dos autores](https://github.com/DaniDeniz/IndoorActionDataset),
[GMDCSA24 na revisão verificada](https://github.com/ekramalam/GMDCSA24-A-Dataset-for-Human-Fall-Detection-in-Videos/tree/5abac7693229900cf80f722e878fbb119211fc1c)
e [metadados GMD/Zenodo](https://zenodo.org/api/records/12921216).
IAD: repositório BSD 3-Clause, metadados Zenodo CC BY 4.0; registrar ambas as
declarações sem presumir resolvida a diferença. GMD: MIT no repositório, CC BY 4.0
no registro Zenodo. Não houve treino com esses materiais; permanecerão privados.
Autorias e limites dos pesos em [fontes/licenças](../10_FONTES_E_LICENCAS.md).

## Candidato e decisões

Arquivos principais: config.py/features.py para a seleção/identificação do
método, posture.py/posture_training.py para descritor/artefato/treino,
event_runtime.py/pipeline.py para versionamento, evaluation.py para o aceite
de transição e decision_trace.py para identificar corretamente o método.
Regressões em test_posture_candidate.py e test_floor_acceptance.py; documentação
de contratos, motor, decisões, fontes, status e uso atualizada. Mudanças da
evolução anterior foram preservadas, incluindo contratos/flags da interface.

O classificador anterior tem 35 atributos, incluindo seis de posição/escala
absolutas na imagem. Não pode ser transportado do CAUCAFall para esses cômodos
como se sua instalação já estivesse validada. V2 utiliza os primeiros 29
atributos corporais normalizados e simétricos, sem aqueles seis atributos.
Isso é uma hipótese experimental a testar, não garantia de invariância a
perspectiva, oclusão ou estimativas incorretas dos pontos.

Comparados três valores L2 (0,01/0,1/1) somente nas 310 observações antigas de
treino S5/S7 e na seleção S9/S10. L2=0,01 preservou os quatro alvos; as outras
variantes perderam um alvo de seleção. Nenhum novo vídeo foi inferido ou usado
para escolher pesos/limiares. O treinamento segue explícito, sem ajuste em run.

Artefato privado **posture-body29-v2**, descritor symmetric-body-shape-29-v1,
SHA **cb02e8742b8e82282706e3570c83d895f34d509033171207c72ae209e64c9664**.
RTMO-s preservado, SHA
**d0703d40d19f3921da51ae725402d5fdae4d2478c7442072d3101bd396f370d8**.
Política floor-rtmo-score-posture-body-v2; worker edge-posture-v2. Scores
deitado/outra postura 0,8/0,2, qualidade articular 0,5, detecção de pessoa 0,7,
análise alvo 5/s e demais parâmetros temporais preservados.

Contexto da V2 exige artefato/hash, modelo, geometria, calibração/hash e região
confirmados manualmente. Uma postura reconhecida como outra pode fornecer
evidência negativa em área de apoio; deitado/desconhecido nesse apoio continua
impedindo confirmação de chão. Essa mudança é da V2: a semântica de exclusão,
pesos e vinculação à instalação da V1 foram preservados. O artefato V1 foi
reproduzido com SHA idêntico 154196a2… em destino separado.

Manifestos ganham anotação local opcional transitionObserved. Os seis alvos
propostos já começam deitados: anotar false após conferência. Uma emissão
POSSIBLE_FALL ali pode corresponder à presença no chão, mas é uma transição
injustificada e impede aprovação. Não remover o alvo nem transformar essa
emissão em prova de detecção de queda. Nenhuma mudança no envelope HTTP.

## Verificações reais

Todos os comandos abaixo foram executados nesta continuação, a partir da raiz,
após `. ./scripts/activate.ps1`. Para os helpers Python da tabela, prefixo completo
`uv run --offline --project services/edge --frozen python`. Helpers, dados e
logs específicos do lote são privados; não fazem parte de uma instalação limpa.

| Comando/ação | Resultado observado |
| --- | --- |
| `python .local/detector-evolution/audit-intake16.py` via uv | Exit 0; 16 arquivos, hashes conferidos, 4957 quadros decodificados, sem inferência |
| `python .local/detector-evolution/verify-intake16-sources.py` via uv | Exit 0; 14 membros ZIP e dois arquivos GitHub correspondem aos bytes locais |
| `python .local/detector-evolution/compare-body-shape-only.py` via uv | Exit 0; três ajustes com dados antigos; L2=0,01 preservou 4/4 alvos |
| `uv run --offline --project services/edge --frozen radar-edge posture-train --manifest .local/detector-evolution/candidate-body-v2/training-manifest.json --output .local/detector-evolution/candidate-body-v2/posture.json` | Artefato treinado sobre 310 observações antigas, parâmetros iguais ao protótipo selecionado |
| Reprodução do manifesto V1 em `candidate-body-v2/legacy-reproduction.json` | Bytes/SHA idênticos ao artefato anterior |
| `python .local/detector-evolution/check-body-v2-runtime.py` via uv | Exit 0; 32 sequências antigas com runtime/SQLite real, sem nova inferência, 4/4 CAUCA, zero eventos nas duas cadeiras; três perdas antigas mantidas |
| `python .local/detector-evolution/verify-current-replay.py` via uv | Exit 0; 24 sequências baseline/V1 com fingerprints e emissões preservados |
| `python .local/detector-evolution/check-body-v2-file.py` via uv | Exit 0; inferência FILE real no antigo S9, 52 decisões, 29 atributos, um evento aos 6800 ms, sem imagem/HTTP/webcam |
| `pnpm.cmd exec node .local/detector-evolution/native-http-runner-v2.mjs` | Exit 0; quatro eventos nativos V2 de observações RTMO antigas → quatro incidentes, reenvios sem duplicação, quatro avisos locais; banco exclusivo removido |
| `uv run --offline --project services/edge --frozen ruff format services/edge` | Formatação ajustada; verificação final: 65 arquivos formatados |
| `uv run --offline --project services/edge --frozen ruff check services/edge` | Exit 0 |
| `uv run --offline --project services/edge --frozen pytest services/edge/tests -q` | Última rodada: **348 passed, 1 skipped**, 21,26 s; GUI artificial não habilitada para evitar interromper a conferência |
| `$env:RADAR_TEST_GUI='1'; uv run --offline --project services/edge --frozen pytest services/edge/tests/test_pose_pipeline.py::test_real_preview_window_stops_by_limit_and_closes -q` | Rodada separada: **1 passed**, 1,70 s; apenas janela com conteúdo artificial, não webcam |
| `python .local/detector-evolution/prepare-intake16-review.py` via uv | Exit 0; 16 propostas de anotação/região com confirmação falsa; fontes dos rascunhos desautorizadas para impedir execução acidental |
| `review-intake16.py` com Python do ambiente uv, janela local | Vídeos originais; começa pausado, sem estimador, treino, câmera ou gravação; conferência humana ainda pendente |
| `python .local/detector-evolution/freeze-body-v2.py` via uv | Exit 0; fonte, modelo leve, parâmetros e resultados antigos preservados antes da reserva |
| `python .local/detector-evolution/prepare-intake16-evaluation.py` via uv | Exit 2 esperado, ANNOTATIONS_PENDING; nenhum manifesto ativo/inferência criado sem a conferência humana |
| `radar-edge posture-check` via uv, configuração do ponteiro file-check do candidato V2 | Exit 0; artefato/modelo/contexto conferidos, sourceOpened=false e databaseOpened=false |
| `node --input-type=module -e "import { sourceIdentity } from './scripts/validation/source.mjs'; process.stdout.write(JSON.stringify(sourceIdentity()));"` | 188 arquivos, SHA idêntico ao congelamento, HEAD preservado |

A rodada completa final não foi apresentada como 349 testes sem pulos: são
348 sem GUI nessa execução, mais a verificação separada da janela artificial.
Os 104 testes TS, 159 API, 20 E2E, lint/tipos/build da rodada anterior permanecem
evidências anteriores, não execuções novas desta rodada sem mudança TypeScript.
O teste HTTP V2 verificou o endpoint de revisão com ator automatizado: não é
revisão humana do fundador, aviso externo ou conferência visual da postura.

Na regressão antiga, os quatro alvos CAUCA mantiveram latências de
1400/1400/3800/4000 ms; três perdas históricas continuam no denominador do
inventário conhecido. Zero alertas em negativos não equivale a aprovação
quando falta cobertura. O resultado 4/4 continua desenvolvimento/seleção.

## Referência congelada e reprodução

Fonte executável: **188 arquivos**, SHA
**65ad8c16cc4859719924a1cf601a1cdb220d5c4e8ce5d45a6774295d2bc73c81**.
Ponteiro `.local/detector-evolution/candidate-body-v2/freeze-pointer.json`:
arquivo ZIP da fonte, artefato, manifesto de treino, protocolo e métricas antigas.
Não arquiva traces brutos para contornar retenção. Não contém vídeos, RTMO ou
segredos. Nenhum aceite funcional ou validação do cômodo está implícito.

Inventário e propostas em
`.local/detector-evolution/intake16-3fa1c073-e15b-4b19-a391-f95b762401e7/`,
localizáveis também por `.local/detector-evolution/intake16-pointer.json`.
As propostas iniciais foram substituídas por anotações aprovadas e congeladas
ao final da revisão registrada abaixo; os dados rejeitados foram preservados.

Para reabrir **somente a consulta dos arquivos e contornos**, depois da avaliação:

```powershell
. ./scripts/activate.ps1
uv run --offline --project services/edge --frozen python .local/detector-evolution/review-intake16-context.py
```

Alt+Tab encontra “Radar - revisao dos contornos - sem IA”. Espaço inicia e
pausa; após a avaliação C não altera o contexto congelado; R repete;
Q/Esc encerra. Amarelo indica região de piso proposta, vermelho apoio excluído.
N/B mudam de clipe; pular não confirma uma cena. A sequência tem cerca de
3 min 16 s de conteúdo, além do tempo de pausas. Arquivos não são modificados.

## Pendências e próxima execução

1. Fundador conferir os seis alvos, seus intervalos propostos desde 0 ms e os
   dez negativos, incluindo as duas cenas vazias. Confirmar ou corrigir pisos e
   exclusões **antes** de conhecer as previsões.
2. Registrar essa confirmação, congelar anotações/calibrações e manifestos com
   hash; o preparador privado recusa confirmação ausente e não roda inferência.
3. Executar baseline e V2 em FILE, filas novas/HTTP desligado. Comparar todos
   os seis alvos e dez negativos, latência desde o início anotado ≤5000 ms,
   duplicações, cobertura, transições injustificadas, recursos e incerteza.
   Mesmos arquivos/pisos/RTMO/limiares de qualidade; V2 usa apoios manuais
   declarados, capacidade inexistente na baseline histórica, sem alterá-la.
4. Publicar resultados adversos também. Se a reserva orientar ajustes, passa
   a desenvolvimento; não reutilizar como avaliação independente da correção.
5. Ainda faltam rede/ajoelhamento persistente, transição segura, dados do cômodo
   e futura conferência física/entrega/revisão/aviso pelo fundador. Os vídeos
   públicos não substituem essa demonstração no uso pretendido.

Até essas verificações, **não há aprovação do núcleo funcional**. Não solicitar
novo teste físico agora, repetir os 30 minutos históricos ou provocar queda.

## Revisão humana do contexto — continuação de 24/10

O fundador assistiu aos 16 arquivos e confirmou a proposta de cenas/intervalos:
seis já no chão e dez sem pessoa deitada no chão. **Reprovou os contornos
originais**: piso mal delimitado e exclusões que deixavam móveis de fora ou
cobriam áreas erradas. A geometria matematicamente válida não comprova uma
anotação visual correta; não executar a reserva com essas marcações.

A causa da preparação inadequada foi usar propostas manuais aproximadas,
reaproveitadas por enquadramento, sem detalhar suficientemente os pixels do
vídeo original. Não havia detector automático de chão ou móveis nessas linhas.
As propostas rejeitadas foram preservadas em revisão privada separada, com
calibrações anteriores e feedback. Nenhum dado de previsão foi usado para
refazê-las; **até congelar as anotações não havia inferência nesse lote**, nem
uso para treino/escolha do modelo.

Quadros originais dos enquadramentos foram examinados em memória com grade de
coordenadas, sem salvar imagem/vídeo ou executar estimador. Propostas refeitas
para piso e áreas de apoio/oclusão, por cena. Cama e cadeira distinguem-se de
áreas ambíguas; sofá não é rotulado como cama. O banco existe no terceiro
vídeo do quarto e a cadeira do GMD não foi copiada para o arquivo sem cadeira.

Na janela de revisão, amarelo mostra o limite configurado e verde claro mostra
a região restante após excluir as máscaras vermelhas. Números identificam as
exclusões manuais. O verde claro não é detecção, segmentação de pixels de piso
ou confirmação de postura. A nova janela começa pausada e pode mostrar somente
o grupo em revisão, sem repetir a confirmação das cenas.

| Grupo | Estado da revisão humana |
| --- | --- |
| intake16-01 a 04, quarto | **Aprovado pelo fundador:** “Os contornos do quarto agora estão corretos” |
| intake16-05 e 06, pessoa no chão na sala | **Aprovados pelo fundador**, com observação de que ainda podem melhorar e pedido de refinamento visual preservado |
| intake16-07 | Primeiro refinamento reprovado em cadeira/parede; cadeira e duas estantes separadas, nova proposta aprovada |
| intake16-08 a 10 e 12 a 16 | **Aprovados pelo fundador**, incluindo confirmação explícita das cenas vazias e da caminhada |
| intake16-11, limpeza da sala | Cadeira branca acrescentada à máscara; **aprovado pelo fundador**. Hipótese de deslocamento não comprovada, corrigida no registro |

As 16 calibrações foram confirmadas somente após as respostas do fundador.
`context-approvals.json` associa cada aprovação aos hashes da calibração e das
exclusões; alterar esses dados depois exige nova revisão. `scene-confirmation.json`
preserva a confirmação das cenas e a rejeição inicial do contexto. Inventário
original, mídias, parâmetros e artefatos congelados não foram modificados.

Comandos desta revisão, após ativação e com o mesmo prefixo uv frozen/offline:

| Comando/ação | Resultado |
| --- | --- |
| `python .local/detector-evolution/inspect-intake16-context.py` com IDs das cenas | Quadros/grade e sobreposições apenas em memória, sem modelo ou arquivos de imagem |
| `python .local/detector-evolution/revise-intake16-context.py` | Snapshot dos contornos rejeitados; registro de cenas confirmadas; propostas novas do quarto |
| `python .local/detector-evolution/revise-intake16-other-context.py` | Propostas dos 12 restantes preservadas em diretório novo; contorno com cruzamento recusado antes de gravar e corrigido; execução final exit 0 |
| `python .local/detector-evolution/prepare-context-review-player.py` | Janela de contexto separada preparada, sem alterar o registro da revisão completa das cenas |
| `review-intake16-context.py intake16-01 intake16-02 intake16-03 intake16-04` com Python do ambiente | Quatro vídeos do quarto conferidos/aprovados pelo fundador |
| `review-intake16-context.py intake16-05 intake16-06` com Python do ambiente | Próximo grupo aberto pausado, sem erro de inicialização |
| `python .local/detector-evolution/prepare-intake16-evaluation.py` | Exit 2 esperado: CONTEXT_REVIEW_PENDING, 16 cenas confirmadas, 4 contextos confirmados, 12 pendentes; sem inferência |

Depois dessa verificação, o fundador aprovou os dois alvos da sala, com a
qualificação de que podem melhorar. Recibo preservado por
`record-context-approval.py intake16-05 intake16-06 --answer ... --refinement-requested`;
contador atualizado para 6/16, sem mudar as regiões já aceitas. Aberta a
conferência de intake16-07/08 com launch-context-review.ps1. O primeiro foi
reprovado novamente em cadeira/parede: a proposta havia unido estantes de lados
diferentes do batente, e as posições dos pés da cadeira precisavam de correção.
Imagem ampliada examinada, móveis separados e cadeira desenhada por partes;
união visual remove linhas internas duplicadas sem mudar a região configurada.
Nova resposta aprovou o primeiro; depois o fundador aprovou o segundo e os quatro
vídeos de poltronas/limpeza, cozinha e sala de jantar. Por fim aprovou a cadeira
branca no vídeo restante. Todas as respostas foram associadas aos dados vigentes.

Correção da hipótese sobre a cadeira branca: não foi comprovado que se movia.
Nos quadros de 0/6800/13000 ms, registro geométrico de fundo a 640×545 mostrou
resíduo mediano de 0,063/0,089 px e deslocamento projetado na região da cadeira
abaixo de 0,1 px. Assento no início/fim: 68 correspondências internas e mediana
de deslocamento 0 px; no meio, oclusão impede a mesma confirmação. Isso não é
prova de imobilidade em todos os quadros. O defeito confirmado era a omissão da
cadeira na máscara. Hipótese anterior mantida como hipótese rejeitada/não
estabelecida no histórico, sem alegar detecção ou acompanhamento automático.

O preparador também exige os estados de aprovação de cada vídeo e verifica os
hashes dos recibos de contexto antes de preparar manifestos ativos. Aprovação
genérica não substitui contornos revistos. Os testes Python anteriores não
foram repetidos por essa edição de dados/ferramentas privadas; código do worker,
artefato, política e dependências continuam congelados. Corrigir contexto não
aprova o núcleo funcional. Nenhum arquivo ou alvo foi removido.

Preparação final executada por finalize-intake16-annotations.py e
prepare-intake16-evaluation.py: exit 0, seis alvos completos desde 0 ms,
transitionObserved=false, dez negativos e duas cenas vazias confirmadas.
Anotações, recibos, calibrações e manifestos congelados em
confirmed-33b57a7b-e6c0-4836-8a99-c81b7360ddb8. SHA de annotations-freeze.json:
**6bf43e164066e78f25168fdabba9800e6fecdee323c3376e285a76bf845169ce**.
Pipeline usa cópias de calibrações confirmadas; pesos e código mantêm o SHA
65ad8c16… antes de ambas as rodadas. Run-intake16-evaluation.py iniciou a
comparação baseline e V2, nesta ordem, com filas novas, HTTP desligado, sem
webcam ou treino. Concluiu 32 execuções ok/ENDED: 2/6 alvos em cada versão,
quatro perdas e V2 com seis negativos inconclusivos; não aprovado. Não alterar
contornos a partir dos resultados. Tabelas e comandos no relatório 04.
