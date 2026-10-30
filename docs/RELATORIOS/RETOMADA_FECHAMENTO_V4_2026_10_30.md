# Retomada do fechamento V4 — runtime e correções funcionais

Trabalho de 29–30/10/2026. **PARCIAL; MVP não aprovado.**
Base de continuidade: commit local `28925b1`, com as alterações desta rodada
preservadas. Este documento continua o [fechamento V4 anterior](FECHAMENTO_CANDIDATA_V4_2026_10_28.md),
sem reiniciar o protocolo ou transferir automaticamente suas aprovações.

**Consolidação concluída desta rodada:** runtime recuperado, comparações na GPU,
correções funcionais, integração isolada, instalação limpa e backup verificados.
A candidata permanece experimental: 33/36 na regressão conhecida e 11/20 quando
se combinam tempo/cobertura e prazo anotado na comparação final. O checker mantém
reprovações e provas humanas/independentes pendentes; não há aprovação do MVP.

## Resultado já comprovado

O Python voltou a executar sem desativar proteções do Windows. Dois ambientes
experimentais separados usam Python PSF assinado 3.13.17, preservando os ambientes
3.12 bloqueados. Imports nativos e execução real do RTMO na GPU foram comprovados.

A candidata funcional opt-in recupera contexto e distingue incerteza de subtipo
de ausência de evidência corporal. Na regressão FILE conhecida, com inferência nova,
passa de **29/36 para 33/36 aprovações**. Os 16 alvos produzem evento, mas floor03
continua fora do prazo registrado. Dois controles continuam inconclusivos. A matriz
não é avaliação independente e não comprova desempenho em câmera ao vivo.

A comparação corrigida das versões anteriores, ambas na mesma GPU e no mesmo
runtime, não aprovou operação em ritmo real: V3 cumpriu tempo/cobertura em 2/20
transmissões e V4 em 5/20. Esse resultado motivou um piloto delimitado da recuperação
com preferência já existente; a referência ADAPTIVE_V3 permanece disponível.

Nenhuma webcam foi aberta. Não houve treinamento, mudança de pesos, polígonos,
limiares de confiança ou tolerância temporal para obter aprovações. Banco de
demonstração, credenciais, provas anteriores e referências foram preservados.
Sem commit, push ou deploy nesta rodada.

## Preservação e localização das provas

A rodada nova é indicada por `.local/runtime-recovery-current.json`:

`.local/detector-evolution/runtime-recovery-bdd8c4ba-2bdf-4f4b-b586-e914891c5b36`

Nos comandos abaixo, essa raiz é chamada `$rodada`. Os vídeos, configurações,
outboxes, perfis, assinaturas e logs são privados e não devem entrar no Git.
A rodada antiga continua em `.local/mvp-closure-current.json`, sem sobrescrever
seu código congelado, matrizes ou recibos. Seu erro CPU × GPU permanece documentado.

| Componente preservado     | Identidade                                                                 |
| ------------------------- | -------------------------------------------------------------------------- |
| Pesos RTMO                | SHA-256 `d0703d40d19f3921da51ae725402d5fdae4d2478c7442072d3101bd396f370d8` |
| Classificador             | SHA-256 `40d01401851f24cd8c815557970f0dcf42877707afbba38d521ebfa87bd5bd19` |
| Perfil de execução        | REFERENCE_4_SPIN                                                           |
| Recuperação de referência | RTMO_ADAPTIVE_V3                                                           |
| GPU comprovada            | AMD Radeon (TM) Graphics, vendor 1002, device 15E7                         |
| Runtime GPU experimental  | Python 3.13.17; onnxruntime-directml 1.23.0                                |
| Runtime CPU experimental  | Python 3.13.17; onnxruntime 1.23.2                                         |


Ambiente inventariado: Windows 11 Pro 10.0.26200, Ryzen 5 5625U (6 núcleos/12
processadores lógicos), 16.153.144 KiB de memória visível ao SO (cerca de 15,4 GiB),
Radeon 1002:15E7, driver 31.0.21925.1001. hardware-current.json preserva a consulta.
Nenhuma câmera foi testada nesta rodada; não se transfere a prova física antiga.

## Bloqueio do Windows: causa e solução aplicada

A causa demonstrada é **Smart App Control**, política
VerifiedAndReputableDesktop, GUID `{0283ac0f-fff1-49ae-ada1-8a933130cad6}`.
Eventos 3077 e 3089 foram correlacionados pelo ActivityID. O bloqueio registrou
Status 0xC0E90002 e níveis solicitado/validado 2/1; os binários Python 3.12.15
utilizados pelo uv estavam NotSigned. O SHA-256 plano da DLL do evento corresponde
ao arquivo atual; não há demonstração de corrupção. Não se atribuiu gerenciamento
empresarial ou autoria da política sem evidência.

O inventário CiTool sem elevação retornou acesso negado, devidamente registrado.
Isso não invalida a identificação da política pelos outros dados. Zero assinaturas
no evento 3089 com VerificationError=0 também não significa assinatura válida.

A alternativa usa a distribuição Windows normal do Python Install Manager,
Python 3.13.17, obtida da PSF. ZIP, executável e DLL foram conferidos por hash;
Authenticode Valid e signatária Python Software Foundation foram verificados antes
da primeira execução. O pacote inteiro foi extraído em pasta privada nova. Não
houve troca isolada de DLL, instalação global, mudança de PATH/registro, exclusão,
remoção de política ou renomeação para escapar do controle.

**Limitação explícita:** 3.13.18 já existe somente em código-fonte. A 3.13.17 foi a
distribuição Windows assinada verificada nesta prova, não a revisão de segurança
mais recente da série. Continua opção experimental. Os projetos originais e seus
lockfiles exigindo Python 3.12 não foram promovidos silenciosamente para 3.13.

Os projetos `experiments/python313-cpu` e `experiments/python313-directml` têm
lockfiles separados e somente uma distribuição ONNX Runtime por ambiente. Há
somente um fornecedor de `cv2` em cada um. NumPy, OpenCV, MediaPipe e os pins
pertinentes tiveram compatibilidade de wheel conferida e imports reais executados.
O caminho do worker é adicionado pelo launcher; para pytest nesses projetos de
ambiente, usa-se PYTHONPATH local ao processo, sem instalar o projeto original
como se seu requires-python já tivesse sido migrado.

O [diagnóstico reproduzível](../DIAGNOSTICO_RUNTIME_WINDOWS.md) contém links
oficiais, hashes, versões e os scripts de auditoria/preparação. A auditoria do
script produziu 16 eventos, oito correlações e quatro ambientes. O preparador
foi validado com `-ExistingRuntime -SkipSync`, além de recusas de destino existente
e caminho fora de `.local`. O download e sync completos ocorreram durante a
recuperação; não se afirma que o novo script de preparação repetiu essas etapas.

## Prova de recuperação e computação GPU

A execução inicial FILE sem profiling foi preservada. Uma prova nova com profiling
usou os mesmos pesos e os casos intake16-03 e chair08-02 pelo worker normal.
O positivo gerou um evento; o controle não gerou alerta.

| Caso        | Eventos | Eventos de operadores DML | Auxiliares CPU | Computação GPU comprovada |
| ----------- | ------: | ------------------------: | -------------: | ------------------------- |
| intake16-03 |       1 |                    34.188 |          3.330 | Sim                       |
| chair08-02  |       0 |                     4.928 |            480 | Sim                       |

Essas contagens são eventos de profiling do ONNX Runtime, não número de operadores
únicos nem tempo exclusivo de kernel GPU. Os auxiliares CPU não representam
fallback integral. A prova não depende somente da lista de providers disponíveis.
Evidência: `native-profiled-summary.json`, perfis de operadores e relatórios em
`native-profiled-proof/`. Imports e ambiente: `imports-cpu.json`,
`imports-directml.json` e `native-env-check.json`.

## Comparação corrigida V3 × V4, sem mistura CPU/GPU

Antes da matriz completa, uma comparação curta confirmou executor inicializado,
provider DML, runtime, adaptador, pesos e identidade do código dos dois lados.
Depois foram executadas **40 transmissões FILE técnicas a 1×**: dez cenários,
duas versões, duas repetições, ordem alternada. Não houve HTTP, prévia ou webcam.

Ambas as versões usaram o código V4 anteriormente congelado, Python 3.13.17,
DirectML 1.23.0 e a mesma GPU. O comparador passa a selecionar explicitamente
DirectML e recusa resultado cujo executor efetivo divergir. `source-runtime.json`
registra de onde o worker foi importado. A matriz corrigida está em `paired-v3-v4/`.

| Medida                                            |      V3 GPU | V4 GPU anterior |
| ------------------------------------------------- | ----------: | --------------: |
| Transmissões completas                            |          20 |              20 |
| Tempo e cobertura simultaneamente aprovados       |        2/20 |            5/20 |
| Eventos nos 14 ensaios positivos                  |           6 |              14 |
| Lacunas de observação acima de 500 ms             |          27 |              30 |
| Média das médias de processamento por transmissão |   215,13 ms |       214,05 ms |
| Máximo de processamento observado                 | 1.081,88 ms |       637,90 ms |
| Média das médias de chamadas por análise          |       1,659 |           1,665 |

As médias acima dão o mesmo peso a cada transmissão; não são uma média global
ponderada por decisões. As aprovações da tabela avaliam tempo/cobertura; não
substituem o prazo humano ou o aceite de todas as funções do detector.
[Tabela das 40 transmissões](RETOMADA_V4_GPU_PAREADO_2026_10_29.csv).

No vazio intake16-15, ambos ficaram com cobertura tempestiva de captura de
aproximadamente 63–64%, com lacunas de 555–585 ms: reprovação. Na V4, floor07
teve cobertura de cerca de 66,8% e lacunas acima de 600 ms. chair08-01 continuou
sem alerta, mas com cobertura em torno de 60%, inconclusivo. Melhorar alvos em
FILE não resolveu o custo de recuperação nem a ambiguidade desses controles.

A antiga comparação V3 CPU × V4 GPU permanece inválida para atribuir ganho à V4.
O resultado novo de 5/20 não deve ser apresentado como ganho ou regressão contra
o antigo 6/20 sem reconhecer condições e validade diferentes.

## Correções funcionais opt-in e mecanismo causal

Foram preservados os comportamentos anteriores e acrescentadas opções explícitas.
Os limites foram registrados antes da comparação em
`candidate-limits-before-comparison.json`. A confirmação de chão continua exigindo
observações atuais, qualidade nativa >=0,5 e os temporizadores já existentes.
Não há prolongamento de evidência por pose antiga, preenchimento de articulações,
expansão do piso ou mudança das previsões do classificador aprendido.

### Contexto ARTICULATED_ARM_V1

Além dos sinais V4 existentes, uma cadeia atual de ombro, cotovelo e punho pode
fornecer contexto 2D do piso. Exige corpo suficiente, torso completo, ambos os
joelhos, cotovelo e punho dentro do polígono real e antebraço com extensão mínima
de 0,1 da diagonal corporal observada. O veto de torso em móveis/exclusões permanece.
`hipInFloorZone` continua informando a projeção verdadeira do quadril, mesmo quando
outro mecanismo fornece contexto.

Esse contexto também pode habilitar o ramo geométrico V4 já existente de torso
reclinado com os dois joelhos elevados, inclusive quando a classe bruta é UNKNOWN
ou SEATED. Essa interação foi testada explicitamente; a mudança não se limita a
poses já classificadas como LYING. Trata-se de um indício 2D, não medição física
de contato com o chão ou prova de acidente.

### Ambiguidade NON_FLOOR_GROUP_V1

Somente uma observação UNKNOWN com corpo suficiente, quatro pontos atuais do
torso e orientação ereta observada pode ser agrupada como OTHER_POSTURE quando
a soma dos scores não-deitado é >=0,95 e o score de deitado é <=0,05.
Os scores originais são mantidos; `postureSubtypeUncertain=True` explicita que
o subtipo continua incerto. Não se afirma atividade normal. Ausência de pose,
corpo insuficiente e ambiguidade relevante para deitado continuam inconclusivos.

Esse grupo pode contribuir para reset e rearme nos limites existentes. Por isso,
as verificações incluem a interação com rearme; não é apenas uma alteração visual
ou contagem mais favorável de cobertura.

### Trajetória POSTURE_DYNAMICS_V3

A orientação atual do torso é separada do nome da classe postural. Quatro pontos
de torso válidos podem demonstrar orientação ereta mesmo com subtipo UNKNOWN.
Mantém suporte anterior de 400 ms, janela de movimento de 1.000 ms, rotação >=35°,
deslocamento normalizado >=0,3 e intervalo máximo entre observações reais de 500 ms.

NO_POSE não fornece posição, orientação ou tempo de suporte. Pode interromper
uma nova sequência de suporte; um suporte já completado só permanece útil dentro
dos limites anteriores e com endpoints reais. Lacuna real >500 ms ou captura
inválida elimina a continuidade. A falta de observação não foi inventada para
recuperar a trajetória de cauca-03.

Continuam: persistência de 2.000 ms, fração válida de 80%, cinco observações,
rearme de 3.000 ms e proteção contra decisão com idade superior a 2 s.

### Compatibilidade, diagnóstico e operação

`posture_execution_context` omite somente as duas novas opções quando estão nos
valores antigos, preservando o fingerprint das outboxes V3/V4 existentes. Opções
novas não padrão continuam participando da identidade. Testes verificam retomada
antiga e recusa de checkpoint incompatível sem alterar a fila.

Os relatórios passam a registrar versão e caminho efetivos do Python e pacotes.
Esse metadado foi acrescentado durante a matriz de inferência, sem mudar a lógica
de decisão. Relatórios anteriores à inclusão não foram reescritos para adquirir
campos novos; a identidade deles também é sustentada pelos comandos e ambientes.
O observador pode selecionar `PYTHON313_SIGNED` explicitamente, preservando o
padrão antigo. Não há download automático silencioso de Python nesse caminho.

## Regressão funcional com inferência nova

A reaplicação causal às 2.187 observações salvas foi uma etapa diagnóstica:
arm-only 30/36, group-only 32/36, motion-only 29/36, conjunto 33/36. Essa etapa
não foi chamada de inferência nova. Depois, os **36 vídeos completos** foram
executados novamente pelo worker nativo DirectML, com saídas novas e preservação
dos inputs: `candidate-recovery01/matrix-final/functional/directml/`.

| Medida                                               | V3 de referência | V4 anterior | Correções funcionais atuais |
| ---------------------------------------------------- | ---------------: | ----------: | --------------------------: |
| Cenários conhecidos                                  |               36 |          36 |                          36 |
| Alvos com evento                                     |            12/16 |       16/16 |                       16/16 |
| Alvos dentro do prazo registrado                     |               12 |          14 |                          15 |
| Aprovações completas                                 |            27/36 |       29/36 |                       33/36 |
| Controles aprovados                                  |            16/20 |       16/20 |                       18/20 |
| Controles inconclusivos                              |             4/20 |        4/20 |                        2/20 |
| Alertas nos controles                                |                0 |           0 |                           0 |
| Duplicações                                          |                0 |           0 |                           0 |
| POSSIBLE_FALL nas quatro transições CAUCA históricas |              1/4 |         2/4 |                         3/4 |

O conjunto atual emite dez PERSON_ON_FLOOR e seis POSSIBLE_FALL. Zero alertas
nos controles não significa zero possíveis erros de tipo nos positivos.

| Caso             | Resultado atual e limitação                                                                                               |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------- |
| floor03          | Evento em 5.216 ms do início provisório 0; prazo continua reprovado. Cobertura FILE 98,35%. Não é latência humana precisa |
| floor05          | Evento em 4.416 ms; tipo POSSIBLE_FALL sem referência humana apropriada para aprovar transição                            |
| floor07          | Evento em 3.824 ms; mesma ressalva sobre tipo de transição                                                                |
| controlled-lying | Evento em 4.400 ms; início anotado 3.000 ms preservado, latência anotada 1.400 ms, antes 5.200 ms                         |
| intake16-08      | Cobertura elegível 83,53%; passa nesta regressão FILE                                                                     |
| chair08-01       | Cobertura elegível 98,95%; sem alerta; subtipo não-deitado continua explicitamente incerto quando agrupado                |
| cauca-03         | Cobertura FILE 83,09%; PERSON_ON_FLOOR. Perda de pose durante a trajetória impede aprovar POSSIBLE_FALL                   |
| cauca-10         | Cobertura 64,38%; sem alerta, INCONCLUSIVE                                                                                |
| cauca-12         | Cobertura 79,69%; sem alerta, INCONCLUSIVE; não arredondado para 80%                                                      |

A inspeção de quadros originais de controlled-lying mostrou descida voluntária,
agachamento, apoio sentado e exercício deitada no tapete, com pernas elevadas.
Seu POSSIBLE_FALL é uma suspeita cinemática produzida pelo motor, não comprovação
de queda/acidente. Não foi somado aos acertos de transição CAUCA. floor05/floor07
também não são acertos verificados de transição. A adjudicação desses tipos em
cenas voluntárias permanece necessária.

As quatro perdas históricas permanecem nos relatórios originais e no denominador.
O fato de hoje existir evento nesses arquivos de desenvolvimento não apaga a
avaliação inicial desfavorável nem os controles historicamente inconclusivos.
Os prazos e rótulos herdados não foram mudados a partir das previsões.

## Sondagem perceptual delimitada: espelhamento

Foi testada uma transformação horizontal em somente 12 frames exatos, mantendo
pesos e limiares. A restauração usa coordenadas da imagem original e troca as
articulações anatômicas esquerda/direita. Há testes de involução. O probe não
gera eventos, não entrega HTTP e não salva imagens.

Entre dez frames previamente sem pose, recuperou **um**: cauca-12 em 2.600 ms,
score 0,73184 e oito essenciais. As quatro perdas da trajetória de cauca-03,
as duas de intake16-08, as duas de cauca-10 e a outra de cauca-12 permaneceram.
O controle vazio continuou sem pose e o controle positivo de cadeira manteve pose.
Uma passagem adicional tem custo medido na ordem de 80 ms nesta prova limitada.

O resultado não sustenta integrar outra passagem ao worker. **Espelhamento não
integrado.** O score 0,69258 de cauca-03 permaneceu abaixo do limiar 0,7, sem
arredondamento ou redução da exigência. Provas: `mirror-probe/` e `mirror-summary.json`.

A primeira preparação do probe recusou um cabeçalho antigo sem videoSha256.
A auditoria encontrou dois cabeçalhos ausentes; os bytes correspondiam aos hashes
preservados, sem divergência de vídeo. Um protocolo novo acrescentou os cabeçalhos,
preservando o
original e a falha de validação. Isso não alterou pixels ou anotações.

## Recuperação com preferência DirectML: mais barata, rejeitada como substituta

A opção explícita RTMO_PREFERRED_V2 passa pelo worker normal usando uma única
sessão DirectML e o controlador de preferência já existente. O carregador CPU
herdado do controlador não é inicializado. A sessão GPU continua responsável
por hardware, no-fallback, profiling e fechamento. ADAPTIVE_V3 permanece preservado.

Os limites V2 foram mantidos: duas chamadas por análise, início de chamada extra
até 220 ms, inspeção periódica do quadro completo a 800 ms, preferência válida por
1.600 ms, lacuna de entrada de 500 ms e busca de até 1.600 ms/oito análises. A
preferência é somente processamento; toda pose usada precisa vir do frame atual.
Esses limites constam de preferred-v2-limits-before-comparison.json.

Após o piloto FILE de quatro casos, foram executadas oito transmissões novas:
dois cenários, duas estratégias, duas repetições sequenciais com ordem alternada,
mesma GPU/runtime/pesos e nenhuma webcam. O piloto manteve a detecção do positivo
e não alertou no vazio. A opção cumpriu tempo/cobertura em 4/4 transmissões, contra
2/4 da referência deste piloto. Não se transfere esse resultado para todos os casos.

| Cenário | ADAPTIVE_V3 | PREFERRED_V2 |
| --- | --- | --- |
| intake16-03: chamadas médias/análise | 3,00 nas duas repetições | 1,27 / 1,26 |
| intake16-03: processamento médio | 318,22 / 299,41 ms | 135,49 / 152,80 ms |
| intake16-03: processamento P95 | 531,37 / 374,73 ms | 227,51 / 296,11 ms |
| intake16-03: evento | PERSON_ON_FLOOR nas duas | PERSON_ON_FLOOR nas duas |
| intake16-15 vazio: chamadas médias/análise | 4,00 nas duas | 1,86 / 1,84 |
| intake16-15 vazio: processamento médio | 432,42 / 343,31 ms | 197,59 / 168,92 ms |
| intake16-15 vazio: processamento P95 | 516,67 / 362,89 ms | 312,11 / 208,60 ms |
| intake16-15 vazio: alertas | Zero nas duas | Zero nas duas |

A opção preferencial também teve profiling real: 14.476 eventos de operadores
DmlExecutionProvider e 1.410 auxiliares CPU em intake16-03, GPU comprovada.
Prova em preferred-gpu-profile/, relatório 68c1b4c2-2082-448e-af1c-b7f7736d9a4f.
Esses são eventos de profiling do runtime, sem medir tempo exclusivo dos kernels.

O ganho de custo não bastou. A regressão nativa completa dos 36 arquivos manteve
33/36 aprovações agregadas, mas alterou comportamento obrigatório:

| Regressão frente à candidata funcional ADAPTIVE_V3 | Evidência |
| --- | --- |
| cauca-04: perdeu o tipo de transição | POSSIBLE_FALL → PERSON_ON_FLOOR; latência anotada de 1.800 → 3.000 ms |
| Transições históricas com tipo POSSIBLE_FALL | 3/4 → 2/4 |
| cauca-10: piora de cobertura já inconclusiva | 64,38% → 57,53% |
| cauca-12: piora de cobertura já inconclusiva | 79,69% → 70,50% |
| floor07: redução de cobertura, ainda passa no FILE | 97,49% → 86,00% |

**Decisão: RTMO_PREFERRED_V2 rejeitado como substituto desta candidata.** A contagem
33/36, sozinha, esconderia uma perda de transição e menos observação nos controles.
O código permanece como opção experimental explícita e as provas são preservadas;
a candidata preparada mantém RTMO_ADAPTIVE_V3. Não se promove o caminho mais
barato sacrificando reconhecimento. Não se inicia outra busca aberta de modelos.

Provas: preferred-paced-pilot-summary.json, preferred-native-summary.json,
candidate-preferred-v2/matrix-final/ e preferred-gpu-profile/. A comparação final das correções mantidas está na seção seguinte.

## Ritmo real da candidata mantida: 40 transmissões finais

A V4 anterior e a correção atual ADAPTIVE_V3 foram executadas na mesma GPU/runtime,
em dez cenários completos, duas repetições e ordem alternada. Não houve suites,
compilação ou outra inferência nossa concorrente durante essa comparação.
A fonte importada está registrada em paired-current-v4/source-runtime.json e
corresponde a frozen-source-final/. Os cenários são desenvolvimento conhecido.

| Medida | V4 anterior | Correção mantida |
| --- | ---: | ---: |
| Tempo e cobertura simultâneos | 10/20 | 14/20 |
| Tempo/cobertura e prazo anotado de evento | 6/20 | 11/20 |
| Eventos nos 14 ensaios positivos | 14 | 14 |
| Alertas nos seis controles | 0 | 0 |
| Lacunas >500 ms | 11 | 8 |
| Média das médias de processamento | 179,39 ms | 171,63 ms |
| Maior processamento observado | 775,99 ms | 597,13 ms |
| Média das médias de chamadas/análise | 1,694 | 1,667 |
| Cadência por transmissão | 1,94–4,81 análises/s | 2,20–4,93 análises/s |
| CPU média das transmissões, escala de um núcleo | 99,83% | 98,01% |
| Maior pico de working set do processo | 459,06 MiB | 466,54 MiB |

As médias dão o mesmo peso a cada transmissão. O custo permanece dominado pelo
estimador: estas correções de contexto/classificação não constituem uma redução
demonstrada e consistente do custo do modelo. As variações de carga/cadência mudam
quais frames entram na análise; não se atribui toda diferença à regra funcional.
A própria V4 anterior passou 10/20 aqui e 5/20 na primeira comparação corrigida;
essas rodadas não devem ser combinadas como se fossem condições idênticas.

Reprovações atuais preservadas: floor07 repetição 1 (lacuna 540,35 ms),
controlled-lying repetição 2 (562,18 ms), cauca-10 nas duas (cobertura 56,51%/53,42%,
com lacuna 507,24 ms na segunda), intake16-03 repetição 2 (505,52 ms) e vazio
intake16-15 repetição 2 (captura tempestiva 61,86%, lacuna 597,34 ms).
Na primeira repetição, o vazio passou com 99,48% de captura. Não se escolheu só
a repetição favorável.

O prazo registrado também reprova floor03 nas duas (5.336,76/5.325,98 ms até
a decisão disponível no host) e floor05 na segunda (5.178,94 ms). Os inícios 0
são provisórios, não latências humanas precisas; mantêm-se no denominador.
Por isso 14/20 **não** significa 14 aprovações completas: com o prazo anotado,
são 11/20. Não houve perda de emissão dos sete positivos nas duas repetições,
nem duplicação dentro de cada sessão isolada. cauca-03 continuou PERSON_ON_FLOOR;
cauca-04 alternou PERSON_ON_FLOOR/POSSIBLE_FALL. O tipo de transição ainda é instável.

Inicialização da sessão: média 416,53/414,44 ms, máximos 652,04/551,29 ms,
respectivamente. Aquecimento sintético excluído pelo executor existente:
119,47/117,85 ms em média. Isso é registrado separadamente; os gates usam a
duração integral do arquivo e o relógio do host da fonte, com cabeças/caudas
sem observação mantidas. Não é medição do tempo entre ligar o programa e uma
pessoa deitar. O timer LIVE de 600 s inclui inicialização e ainda não foi testado
nesta candidata.

CPU usa process_time versus relógio de parede, em escala de um núcleo (há 12
processadores lógicos); não é uso global do notebook nem utilização da GPU.
Memória é GetProcessMemoryInfo/PeakWorkingSetSize da vida do processo, incluindo
inicialização, sem isolar VRAM ou páginas compartilhadas. O P95 de idade máximo
por transmissão foi 670,85/610,56 ms; os limites de 2 s não foram relaxados.

[40 transmissões](RETOMADA_V4_RITMO_REAL_2026_10_30.csv).
Detalhes privados: paired-current-summary.json, paced-diagnostics-final.json e
paced-resources-latencies-summary.json. A comparação de hipóteses anterior,
mais rápida no piloto mas regredida, permanece separada e rejeitada.

### Onde o custo ainda bloqueia

Nos 918 perfis candidatos desta comparação, 628 análises usaram uma chamada.
O máximo completo dessas análises foi 252,13 ms; uma chamada individual chegou
a 229,05 ms. Estes dados não demonstram que uma passagem GPU, sozinha, inviabilize
o limite de 500 ms. Os maiores custos de inferência restantes estão nas buscas
com três/quatro passagens: intake16-03 chegou a 479,23 ms só em inferência e o
vazio a 592,75 ms. Cortar chamadas sem preservar a transição já foi rejeitado.

Há também uma interrupção distinta: controlled-lying repetição 2 mediu 319,44 ms
no estágio checkpoint, contra 219,02 ms na percepção, somando 542,31 ms completos.
Isso comprova latência naquele estágio, não a causa física do armazenamento/SO.
Não se alterou durabilidade SQLite para esconder o pico. Esse diagnóstico não
atribui automaticamente todas as oito lacunas do host a uma mesma causa.
remaining-cost-diagnostic.json preserva os perfis responsáveis. Uma próxima
intervenção deve separar busca perceptual e persistência; não exige nova webcam
nem justifica trocar o modelo automaticamente.

## Integração atual em banco isolado

A suíte de navegador completa passou: **22/22**, desktop e mobile. Em cada layout,
uma execução de intake16-03 produziu um PERSON_ON_FLOOR; chair08-02 não alertou.
Cada fixture teve exatamente um incidente REPLAY/TEST, um recibo e um aviso local.
O reenvio recebeu duplicate=true com o mesmo incidente, sem segunda emissão.
A revisão automatizada foi salva, recarregada no navegador e persistiu na versão 2.
Não representa revisão humana do fundador.

| Layout | Incidente de teste | Evento |
| --- | --- | --- |
| Desktop | 6d1e4d73-fdcd-4c4d-80e3-6ee6922ade2d | 9e1498f6-db4b-4c81-a5bb-60f25595033f |
| Mobile | 5f3de23c-e146-40c5-b82e-a73f7aaa39e2 | 55208b0f-1454-4ce3-b62d-90e035b270f3 |

As quatro execuções terminaram ENDED, sem pendentes, sem vídeo/snapshot e com
perfil final para cada decisão. O positivo comprova 34.188 eventos de operadores
DML e 3.330 auxiliares CPU; o controle, 4.928 e 480. Esses contadores não são tempos
exclusivos de GPU. O modelo e runtime são os mesmos da prova assinada.
Provas privadas: integration-verified-summary-final.json, browser-confirmed.log e
os dois verification.json indicados pelo resumo. PostgreSQL/portas foram exclusivos;
os recursos de teste foram removidos, preservando a demonstração.

A API também passou nas **161 verificações**, agora com exitCode real 0 registrado
em api-confirmed-command.json. O status ambíguo do redirecionamento PowerShell
anterior foi preservado; não foi usado como sucesso inferido.

## Congelamento atual

candidate-freeze-release.json vincula **283 arquivos**, HEAD 28925b1, árvore suja,
à fonte SHA-256 084c41bbda833a347f10114fd3fb659dd1292b3c7cccd51f61a896d846309149.
A cópia está em frozen-source-release/. A fonte de percepção é idêntica à
frozen-source-final/ usada nas 40 transmissões; somente o instalador e seu teste
foram consolidados depois. final-source-and-observation-parity.json comprova
zero mudanças nos arquivos de percepção e zero diferenças de features, scores e
eventos nas 2.187 observações reais salvas (não é inferência nova). O primeiro congelamento, anterior à correção
do log de preparação, foi preservado separadamente. Não é um commit.

A correção final do preparador evita que progresso normal do uv em stderr vire
NativeCommandError terminante no Windows PowerShell. Ela captura os fluxos pelo
Process API e decide pelo exit code real. A preparação completa com runtime já
verificado e os dois sync frozen passou em runtime-preparation-verified.log.
Há guarda contra UV_PROJECT_ENVIRONMENT externo: rejeitou o redirecionamento
antes de criar a saída. Não houve modificação global de variável ou política.

## Preparação física, sem execução

A configuração nova physical-600/config.yaml foi preparada com o caminho normal
DirectML, REFERENCE_4_SPIN e RTMO_ADAPTIVE_V3, as correções funcionais mantidas,
entrega local habilitada e evidência corporal. Snapshot permanece desautorizado;
nenhum vídeo é gravado. O limite nominal é 600 segundos.

preparation.json registra cameraOpened=false, httpSent=false e executor solicitado
ainda não inicializado:
preparar a configuração não demonstra captura, executor iniciado ou entrega. A
calibração e credencial existentes foram preservadas. O runtime 3.13 assinado deve
ser selecionado explicitamente no observador, sem alterar o padrão antigo.

**Ainda não elegível para novo ensaio:** a preparação não supera as reprovações
em arquivos, os controles inconclusivos ou a reprovações na comparação de ritmo real.
Nenhuma ação física é solicitada nesta consolidação. O resultado deve ser
reavaliado antes de qualquer execução autorizada da webcam.

## Comandos e verificações executados até esta consolidação

Na raiz, os comandos Python exigem a ativação das ferramentas. Para as suites no
novo projeto de ambiente, PYTHONPATH foi definido somente no processo:

```powershell
. ./scripts/activate.ps1
$rodada = (Get-Content .local/runtime-recovery-current.json -Raw | ConvertFrom-Json).root
$env:PYTHONPATH = Join-Path (Get-Location) 'services/edge/src'
```

| Comando/ação realmente executado                                                                                      | Resultado e prova                                                                                                                                            |
| --------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Leitura de pyvenv.cfg, hashes, Authenticode, eventos e registro SAC                                                   | Bloqueio identificado; runtime-binaries.json, homes.jsonl, events-correlated.json e ci-registry.json                                                         |
| CiTool -lp -json                                                                                                      | Acesso negado ao inventário; citool-policies.json preservado                                                                                                 |
| Download PSF, verificação de manifesto, SHA e assinaturas antes da execução                                           | Runtime assinado executou; runtime-selection.json e signed-runtime.json                                                                                      |
| `uv sync --project experiments/python313-cpu --python <python-assinado> --no-python-downloads` e equivalente DirectML | Dois ambientes separados sincronizados; sync-cpu.log e sync-directml.log                                                                                     |
| Imports nativos nos dois ambientes                                                                                    | Passaram; imports-cpu.json e imports-directml.json                                                                                                           |
| `uv run --project experiments/python313-cpu --frozen python scripts/run-edge.py env`                                  | Passou; MediaPipe Tasks e OpenCV GUI reais; native-env-check.json                                                                                            |
| Prova FILE nativa com profiling habilitado                                                                            | Positivo 1 evento, controle 0, GPU comprovada nos dois; native-profiled.log e native-profiled-summary.json                                                   |
| `compare-candidate-streams.py` com comparação curta e depois dez cenários/duas repetições                             | 40 transmissões completas e verificadas; paired-smoke-corrected-cli.log, paired-v3-v4.log                                                                    |
| Aplicação causal às 2.187 observações preservadas                                                                     | Variantes isoladas e conjunto comparados; candidate-cache.log. Não é inferência nova                                                                         |
| `run-candidate-regression.py --protocol <rodada>/candidate-recovery01/protocol.json`                                  | 36 FILE nativos completos; 33/36 aprovações, candidate-native-final.log                                                                                      |
| Testes de contexto corrigidos                                                                                         | 27 passaram; context-tests-fixture-corrected.log                                                                                                             |
| Testes de interação do contexto e rearme                                                                              | 13 passaram; context-interaction-tests.log                                                                                                                   |
| Testes temporais V3 focados                                                                                           | 40 passaram; temporal-v3-tests-19847bff-072f-4157-8e05-7a3f69ef1452.log                                                                                      |
| Testes de identidade de execução/checkpoint                                                                           | Cinco passaram; posture-identity-tests.log                                                                                                                   |
| `uv run --project experiments/python313-cpu --frozen pytest services/edge/tests experiments/directml/tests -q` | Execução inicial: 550 passaram, uma GUI ignorada, software-regression.log. Consolidação atual após correções: 607 passaram, uma GUI ignorada em 27,64 s, software-regression-final.log |
| Probe horizontal delimitado com protocolo verificado                                                                  | 1/10 frames perdidos recuperado; mirror-probe-verified.log; não integrado                                                                                    |
| Testes do adaptador de preferência DirectML e controlador pertinente                                                  | 22 passaram; directml-reacquiring-final-tests.log. Adaptador testado sem equivaler sozinho a prova física GPU                                                |
| `run-candidate-regression.py --native-only` no piloto de quatro arquivos                                              | Dois positivos com evento e dois controles sem alerta; preferred-pilot.log                                                                                   |
| Comparação pareada das recuperações em dois cenários, duas repetições | PREFERRED_V2: 4/4 tempo/cobertura, ADAPTIVE_V3: 2/4; custo reduzido no piloto; preferred-paced-pilot-summary.json |
| Regressão nativa PREFERRED_V2 dos 36 arquivos | 33/36, mas perda de transição em cauca-04 e pior cobertura em controles; substituição rejeitada; preferred-native-summary.json |
| Profiling real da opção PREFERRED_V2 | GPU comprovada com auxiliares CPU; preferred-gpu-profile/ |
| Testes de proteção do harness FILE | 31 passaram; native-harness-tests-final.log |
| Testes de preparação DirectML/identidade | 24 passaram; directml-preparation-tests.log |
| Suites API com PostgreSQL isolado | 161 passaram; api-confirmed.log e api-confirmed-command.json registram exitCode real 0 |
| Preparação da configuração nominal de 600 s | Configuração válida, RTMO_ADAPTIVE_V3 mantido, sem abrir câmera ou enviar HTTP; physical-600/preparation.json |

Falhas intermediárias foram preservadas: import de radar_edge sem PYTHONPATH,
fixture de contexto com quadril ausente, CLI de comparação ainda sem os novos
argumentos na primeira chamada, cabeçalho de hash ausente no primeiro probe e
quoting PowerShell no primeiro teste do preparador, duas expectativas antigas do
preparador na suite de software e indisponibilidade inicial do Docker na API.
As 161 verificações API passaram após disponibilidade do Docker e o código de
saída real 0 foi registrado em execução posterior. A primeira preparação completa também preservou runtime-preparation-final.log:
o progresso do uv em stderr provocava NativeCommandError, corrigido e verificado
na preparação posterior. As falhas foram tratadas sem editar
as provas anteriores. Não são ocultadas por uma contagem posterior de testes.

## Reprodução sem abrir a câmera

Os diretórios de saída precisam ser novos. Não execute novamente sobre uma
matriz ou outbox já existente. Para reproduzir a comparação corrigida das versões
anteriores, use o código congelado antigo e os mesmos protocolos, nunca inferindo
o provider pelo nome de uma pasta. O comparador verifica o executor efetivo.

```powershell
$anterior = (Get-Content .local/mvp-closure-current.json -Raw | ConvertFrom-Json).root
uv run --project experiments/python313-directml --frozen --no-python-downloads python scripts/validation/compare-candidate-streams.py --candidate-root $anterior --reference-root .local/detector-evolution/directml-integration-757f4105-e1ad-46ca-8efb-995ad297eb3e --output ".local/comparacao-gpu-$([guid]::NewGuid())" --source-root "$anterior/frozen-source"
```

A reprodução da regressão exige clonar o protocolo para outputRoot novo e
preservar hashes/targets; não altere parâmetros apenas para a execução repetir.
O harness FILE normal verifica fontes autorizadas, arquivos pinados, evidência
corporal e entrega desabilitada. Nenhum comando desta seção abre webcam.

## Gates e pendências

| Critério                                          | Situação comprovada nesta consolidação                                    |
| ------------------------------------------------- | ------------------------------------------------------------------------- |
| Bloqueio Windows identificado                     | APROVADO: SAC, causa e alternativa assinada demonstrados                  |
| Execução Python CPU/DirectML e imports            | APROVADO nos ambientes experimentais separados                            |
| Computação GPU após mudança de runtime            | APROVADO por profiling real, não apenas lista de providers                |
| Comparação V3 × V4 corrigida                      | EXECUTADA: mesma GPU/runtime/pesos; operação em ritmo real REPROVADA      |
| Regressão funcional atual completa                | REPROVADA para aceite integral: 33/36, floor03 e dois controles restantes |
| Quatro transições históricas                      | PARCIAL: 3/4 tipos reconhecidos; cauca-03 não recuperado                  |
| Tipos em descidas voluntárias                     | PENDENTE de adjudicação; não declarar queda/acidente comprovado           |
| Integração após estas alterações                  | APROVADA em REPLAY/TEST isolado: dois layouts, revisão automatizada persistida  |
| Congelamento e checker da fonte final             | APROVADO o vínculo; engenharia exit 0, integral exit 1                |
| Avaliação realmente independente                  | PENDENTE: dados usados nos ajustes continuam desenvolvimento              |
| Opção de custo PREFERRED_V2 | REJEITADA como substituta: mais barata no piloto, mas perde reconhecimento de transição e cobertura |
| Sessão física nominal de 600 s da candidata atual | PREPARADA, PENDENTE de elegibilidade; não executada e não solicitada nesta rodada |
| MVP funcional integral                            | NÃO APROVADO                                                              |

A reserva mínima continua sendo quatro cenas de pessoa já no chão e oito de
atividades comuns, separadas por gravação/participante das usadas em ajustes,
com procedência e intervalos humanos. Isso não autoriza chamar vídeos antigos de
reserva nem dispensa as reprovações técnicas. As provas antigas de 600 s,
27min45s, offline e revisões humanas mantêm seu escopo e vínculo originais.

Nenhuma ação administrativa ou captura é necessária agora. Para destravar a
avaliação independente, a entrega humana mínima é um único lote novo com quatro
cenas de pessoa já no chão e oito de atividades comuns, com origem e intervalos
humanos, de gravações/participantes não usados nos ajustes. Esse lote não substitui
a correção das falhas técnicas e não deve ser usado para ajustar a candidata
congelada. Não é solicitado outro ensaio físico nesta rodada.



## Instalação limpa e restauração verificadas

A opção explícita de instalação limpa PYTHON313_SIGNED validou assinatura/bytes
pelo preparador antes de executar o runtime. Uma cópia nova usou o lockfile CPU
3.13, sem baixar outro interpretador, com PYTHONPATH somente para o código copiado.
Passaram instalação pnpm/uv congelada, configuração sem segredos copiados,
build, migrações, seed sintético, import/modelo MediaPipe Full, worker FILE
sintético sem pessoa e login API/painel por proxy. Não comprova eficácia RTMO,
DirectML em outra máquina, captura ou funcionamento offline.

O recibo novo clean-install-current.json preservou o histórico. O runtime PSF
externo verificado, Docker/cache e internet para pacotes/modelo foram pré-requisitos
explícitos; .env/.local da demonstração não foram copiados. Cinco testes de guarda
passaram. Backup/restauração em bancos sintéticos isolados também passou,
incluindo relações, revogação, redaction e deduplicação; originalDemoModified=false.
Provas: clean-install-confirmed-command.json, clean-install-current.json e
backup-confirmed-command.json. Nenhum banco pessoal foi restaurado ou alterado.

## Comandos finais e veredito do checker

Nos comandos abaixo, $rodada é a raiz indicada por .local/runtime-recovery-current.json.
Os logs registram os argumentos efetivos e o exit code do processo filho; o helper
privado run-check.mjs apenas capturou stdout/stderr e gravou esses recibos.

| Comando realmente executado | Resultado e comprovante |
| --- | --- |
| pnpm.cmd lint | Passou; lint-consolidated-command.json |
| pnpm.cmd typecheck | Passou; typecheck-final-command.json |
| pnpm.cmd build | Passou; build-final-command.json |
| pnpm.cmd --filter @radar/contracts test | 104/104; contracts-js-final-command.json |
| pnpm.cmd test:demo | 4/4; simulator-final-command.json |
| uv run --project experiments/python313-cpu --frozen --no-python-downloads pytest services/edge/tests experiments/directml/tests -q | 607 passaram, uma GUI opt-in ignorada; python-consolidated-command.json |
| uv run --project experiments/python313-cpu --frozen --no-python-downloads ruff check services/edge; ruff format --check services/edge | Ambos passaram, recibos edge-lint-consolidated e edge-format-consolidated |
| uv run --project experiments/python313-cpu --frozen --no-python-downloads python scripts/run-edge.py env | Imports reais passaram; edge-env-consolidated-command.json |
| pnpm.cmd test:api com RADAR_EDGE_RUNTIME_PROJECT=experiments/python313-cpu e PYTHONPATH do código | 161/161, exit 0; api-confirmed-command.json |
| pnpm.cmd test:e2e com RADAR_DIRECTML_PROTOCOL=$rodada/candidate-recovery01/protocol.json e RADAR_DIRECTML_RUNTIME_PROJECT=experiments/python313-directml | 22/22, incluindo duas integrações GPU reais; browser-confirmed-command.json |
| compare-candidate-streams.py --candidate-root $rodada/candidate-recovery01 --reference-root $anterior/matrix-final --output $rodada/paired-current-v4 --source-root $rodada/frozen-source-final --repeats 2, no runtime DirectML 3.13 | 40 completos, 10/20 anterior contra 14/20 atual em tempo/cobertura; paired-current-v4.log |
| summarize-candidate-streams.py --root $rodada/paired-current-v4 --output docs/RELATORIOS/RETOMADA_V4_RITMO_REAL_2026_10_30.csv, no runtime CPU 3.13 | 40 linhas derivadas, sem inferência |
| pnpm.cmd test:backup | Passou em bancos sintéticos isolados; backup-confirmed-command.json |
| pnpm.cmd demo:install-check com RADAR_VALIDATION_RUNTIME=PYTHON313_SIGNED, RADAR_SIGNED_PYTHON=$rodada/python-3.13.17/python.exe e RADAR_CLEAN_INSTALL_RESULT=$rodada/clean-install-current.json | Instalação limpa passou; clean-install-confirmed-command.json |
| select-worker.py --config <caminho relativo preparado> --runtime PYTHON313_SIGNED | Configuração/argumentos válidos; physical-command-validation.json, sem abrir câmera |
| pnpm.cmd demo:check --engineering --evidence $rodada/release-evidence.json --engineering-evidence $rodada/engineering.json | Exit 0: 14 verificações de engenharia aprovadas |
| pnpm.cmd demo:check --evidence $rodada/release-evidence.json --engineering-evidence $rodada/engineering.json | Exit 1: reprovação funcional preservada; releaseReady=false |

As linhas Python abreviadas de comparação/resumo foram executadas com
uv run --project experiments/python313-directml ou experiments/python313-cpu,
respectivamente, --frozen --no-python-downloads python scripts/validation/<script>.
Os argumentos completos e identidades efetivas estão nos logs e protocolos
vinculados; não se infere executor a partir do nome da pasta.

| Gate final | Resultado |
| --- | --- |
| Pré-requisitos locais e engenharia | APROVADO, 14 verificações vinculadas |
| Regressão conhecida | REPROVADO: 33/36 |
| Transições e confundidores de queda | REPROVADO: 3/4 FILE, tipo instável no stream e voluntárias sem adjudicação |
| Ritmo real, avaliação técnica separada | REPROVADO: 14/20 tempo/cobertura; 11/20 também no prazo anotado |
| Reserva independente | PENDENTE |
| LIVE 600 s, revisão humana, offline e recuperação vinculados à candidata atual | PENDENTE; provas históricas não transferidas automaticamente |
| Apresentação formal | DISPENSADO por D50 |
| Aprovação integral do MVP | NÃO |

Para consultar os resultados, sem abrir câmera ou reenviar eventos:

~~~powershell
. ./scripts/activate.ps1
$rodada = (Get-Content .local/runtime-recovery-current.json -Raw | ConvertFrom-Json).root
pnpm.cmd demo:check --engineering --evidence "$rodada/release-evidence.json" --engineering-evidence "$rodada/engineering.json"
pnpm.cmd demo:check --evidence "$rodada/release-evidence.json" --engineering-evidence "$rodada/engineering.json"
~~~

O primeiro deve retornar 0 e o segundo 1 para este estado. Engenharia aprovada
não aprova o detector. Os comandos de API, painel, seleção do runtime e worker
de 600 s estão em [Uso V4](../USO_CANDIDATA_V4.md); a câmera ficou fechada e sua
execução não é solicitada enquanto persistirem as reprovações técnicas.

Sem commit, push, deploy ou aprovação integral. Dados, banco, credenciais,
modelos, referências e provas anteriores foram preservados.
