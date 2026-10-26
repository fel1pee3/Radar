# Status de construção

**25/10/2026 — dois vídeos novos de yoga testados com referência, V2 e V3.**
V3 detectou pessoa já no chão nos dois, em 2002/4000 ms. No segundo,
referência/V2 demoraram 12400 ms; V3 reduziu NO_POSE de 33 para 11 das 80
análises. Cobertura V3 **79,7468%**, abaixo do gate de 80%: caso permanece
parcial, sem arredondar para aprová-lo. Primeiro vídeo teve cobertura 100%.
Seis execuções FILE ok/ENDED, seis envelopes locais, zero duplicação/HTTP/JPEG.
Sem treino/alteração de parâmetros; modelos congelados e registros anteriores
preservados. Não substitui a validação física ou uma reserva final.
[Resultados e comandos](RELATORIOS/TESTE_DOIS_VIDEOS_YOGA_V3_2026_10_25.md).

**25/10/2026 — primeiro teste físico V3: INSATISFATÓRIO PARA O ACEITE.**
Sessão `continuous-cf26651e…` encerrou sem erro após 106,06 s: 377 análises,
cadência 3,67/s, cobertura decisória conservadora 56,72%. Gerou um alerta
PERSON_ON_FLOOR LIVE/CURRENT, entregue e com aviso local. Incidente
`b1c438bc-ee52-4e13-ad9e-8e5d966a862a`, ainda sem revisão na consulta.
Fundador relatou três idas ao chão de 5–7 s, em pé entre elas e piso correto:
um alerta para três tentativas, duas sem alerta separado. Duração no chão era
suficiente; não aprovar o teste só pela entrega. Tempos exatos/duração em pé
ainda desconhecidos; reconhecimento, lacunas e rearme precisam de investigação.
Sem nova captura nesta análise.
[Resultados e próximos passos](RELATORIOS/SESSAO_WEBCAM_V3_2026_10_25.md).

**25/10/2026 — candidato V3: regressão dos 16 APROVADA; núcleo funcional ainda PARCIAL.**
Após autorização de novo treino local, os 16 materiais passaram a desenvolvimento/regressão.
A avaliação original 2/6 permanece íntegra. Classificador multiclasse com orientação e
qualidade explícitas, recuperação RTMO por recorte/inversão e decisão temporal versionada:
**6/6 pessoas já no chão em 2000 ms, zero alertas nos dez negativos, dez PASS com
cobertura ≥80%, zero duplicações**. Repetido pelo comando público evaluate, 986 análises,
259,48 s de processamento para 195,99 s de conteúdo: custo maior, sem promessa de 30 FPS.
Não equivale a avaliação independente nem aprovação do cômodo do fundador.

CAUCAFall antigo: quatro alertas de permanência no chão, mas **somente 1/4 transições
encenadas gerou POSSIBLE_FALL**; os outros três geraram PERSON_ON_FLOOR. Oito negativos
sem alerta, um ainda inconclusivo. Três perdas históricas e um controle adicional de
deitar voluntariamente continuam sem evento por contexto/observação: não foram retirados.
Dez envelopes nativos passaram pela API isolada com avisos locais e sem duplicação.
Replay adicional no banco de demonstração, porta 15432, conferido pelo fundador:
incidente `1d192fe1-b325-4ff8-907e-dee9007ce29e`, revisão humana salva, versão 2.
Avisos são locais, canal SIMULATED; nenhuma comunicação externa ou webcam nesta rodada.

Faltam avaliação nova reservada, melhoria das transições/perdas restantes e sessão
física V3. [Comparativo, comandos e limites](RELATORIOS/EVOLUCAO_DETECTOR_05.md) ·
[Reproduzir e testar no cômodo](USO_DETECTOR_EXPERIMENTAL.md).
Sem commit, push, deploy ou início da etapa 09 nesta solicitação.

Resultado anterior preservado:

**Evolução do núcleo — 24/10/2026: PARCIAL; MVP funcional não aprovado.**
Recebidos 16 vídeos inéditos confirmados pelo fundador: seis candidatos de
pessoa já no chão e dez negativos, com duas cenas vazias. Todos decodificados
integralmente e associados por SHA aos bytes das fontes publicadas. Reserva
anotada e congelada antes das previsões. Fundador confirmou cenas/intervalos
dos 16 e reprovou as marcações originais de piso/exclusões. Revisão manual:
**16/16 contornos refeitos e aprovados**, com refinamento visual ainda desejado
nos dois alvos da sala. **Comparação FILE executada:** baseline e V2 detectaram
2/6 alvos em 2000 ms e perderam quatro. V2 recuperou chao_06 e regrediu em
chao_04; nenhum ganho global. Zero alertas nos dez negativos; baseline 5 PASS/5
inconclusivos, V2 4 PASS/6 inconclusivos. V2 não aprovado como candidato final.
Trinta e duas execuções ok/ENDED, 986 análises por versão, traces completos,
quatro envelopes locais validados no contrato TS/AJV e SQLite; zero HTTP,
JPEG ou webcam. Fonte congelada 65ad8c16… preservada, sem novo treino.
Hipótese anterior de movimento da cadeira branca não foi comprovada;
a omissão da cadeira na máscara foi corrigida e conferida pelo fundador.
As cores são regiões manuais, sem reconhecimento automático de móveis.
Não são 16 sessões independentes nem gravações
do cômodo do fundador. Candidato LINEAR_BODY_V2 preparado com 29 atributos
corporais, ajustado/selecionado somente nos dados antigos; preserva o modelo de
35 atributos e sua restrição de instalação. Verificações e pendências no
[preparação](RELATORIOS/EVOLUCAO_DETECTOR_03.md) e nos
[resultados da avaliação](RELATORIOS/EVOLUCAO_DETECTOR_04.md).
As quatro perdas novas foram localizadas: duas classificações erradas apesar
de pose suficiente, uma ausência de pose e uma postura incerta. Corrigir piso
não resolve essas falhas. As três perdas históricas continuam preservadas;
desenvolvimento/validação no cômodo do fundador e novo aceite permanecem pendentes.

Estado anterior, preservado como referência do candidato de 35 atributos:
Baseline 0778e02 preservada, RTMO-s mantido. Classificador opt-in, contexto,
motor com histerese, diagnósticos FILE/LIVE, treino reproduzível e incerteza no
painel implementados. Inventário consolidado de regressões positivas: **4/7 cenas
com alerta; três perdas históricas ainda não resolvidas**, ante 3/7 na baseline.
No subconjunto CAUCAFall, FILE real: 4/4 alvos de desenvolvimento/seleção, ante 3/4,
latências 1400/1400/3800/4000 ms, sem duplicações. Zero alertas nos oito negativos,
mas cinco inconclusivos por observação insuficiente. Passaram 344 testes Python,
104 contratos TS, 159 API, 20 E2E, lint, tipos e build. Quatro envelopes reais do
candidato também atravessaram HTTP em banco isolado, com avisos locais e sem
duplicação; revisão automatizada não conta como conferência do fundador. Modelo restrito ao
CAUCAFall, três perdas históricas preservadas. Faltam dados novos do cômodo,
aceite, reserva final e webcam iniciada pelo fundador; ele preparará vídeos depois.
[Plano](EVOLUCAO_DO_DETECTOR.md) · [Relatório](RELATORIOS/EVOLUCAO_DETECTOR_02.md).
O fechamento histórico da 08 abaixo não é aprovação dessa nova entrega.

**Última atualização — 24/10/2026:** etapa 08 **CONCLUÍDA NO ESCOPO REVISADO
DA BANCADA** (D50/D51), demonstração local experimental.

Sessão LIVE de 600,660 s encerrou normalmente: 2799 análises, intervalo observado
597,453 s, elegível 576,986 s e inelegível 20,467 s. Zero eventos/candidatas,
reconexões ou pendências; ENDED aceito pela API e Fonte encerrada confirmada
pelo fundador. Modelo RTMO-s/gates preservados, estabilização visual ligada,
piso v3. [Medições e conferência humana](RELATORIOS/SESSAO_WEBCAM_10MIN_ETAPA_08.md).

O fundador relatou sentar/deitar em rede, polichinelos e trecho no chão de menos
de 10 s com corpo enquadrado, sem alerta. Registrar possível perda/inconclusivo:
duração exata e quadril dentro da ROI não confirmados; sem vídeo/observações LIVE
individuais para reconstruir a causa. Não é prova de acerto do detector nessa cena.
Cadência observada de análise/prévia cerca de 4,7/s, não 30 FPS; poucas ausências
do desenho segundo o fundador. Perda CAUCAFall 1/4 e demais limitações mantidas.

Engenharia de 179 arquivos a2b76fa3… preservada, demo:check --engineering 0.
Matriz final consolidada: FILE/LIVE→incidente→revisão, CAUCAFall exploratório,
offline delimitado, instalação/restore e ensaio curto comprovados. Apresentação
dispensada D50; teste original de 30 min não comprovado, duração revista D51.
Isso não comprova correção da falha histórica aos 27min45s ou eficácia geral.
O checker imprime gates manuais originais fixos e releaseReady=false; não lê
esta revisão humana. Fechamento documental/manual, sem alegar aprovação automática.
Validação encerrada sem commit/push/deploy; em 24/10 o fundador solicitou o
versionamento por commit/push. Sem deploy, piloto assistencial ou início da 09.

## Histórico anterior ao fechamento de 24/10

Tentativa de 10 min continuous-83559f87… bloqueada após 2,23 s, zero análises,
por SOURCE_CONFIG_CONFLICT. A calibração remarcada é v3; o contexto persistido
correspondia exatamente à v2. Não foi falha de pose nem ensaio de 10 min completo.
Worker parado: backup SQLite privado, reset-episode com motivo técnico e auditoria
antes/depois executados. Execução anterior aposentada/preservada, zero eventos/
snapshots antes e depois, um registro de reset e nenhum contexto ativo restante.
Piso novo preservado; nenhuma câmera aberta pela correção. API/proxy HTTP 200 e
GET /v1/edge/me 200 com escopo correto, sem exibir token. Duas regressões de
conflito/reset passaram; código congelado a2b76fa3… inalterado. Repetir somente
o comando de observação, sem remarcar novamente. Sessão física continua pendente.
[Diagnóstico e comandos](RELATORIOS/ETAPA_08.md).
Decisão D50 do fundador: apresentação formal de 5–7 min **DISPENSADA**, não
executada. Operação já exercitada durante o desenvolvimento; roteiro opcional,
sem sessão de aprendizado. Referências históricas à apresentação como pendência
são superadas por essa decisão.
**D51 — duração revista pelo fundador:** próximo ensaio físico limitado a 10 min
nominais, 600 s do worker, sem gravar vídeo. Configuração privada
`.local/etapa08/webcam-10min.yaml` preparada/validada; tentativa de 24/10 bloqueada
por conflito de calibração, contexto renovado conforme registro acima. Nenhuma
sessão de 10 min concluída até aqui.
O timer inclui abertura/modelo; duração efetiva e aquecimento serão separados.
Piso copiado e depois remarcado pelo fundador, modelo/hash verificados e originais
preservados; câmera fechada após a falha e não reaberta pela correção.
Antes do teste, conferir enquadramento/piso atuais. Encerramento normal, saúde,
recursos, períodos inelegíveis e eventos/fila precisam ser revisados.
O teste original de 30 min não foi comprovado: falha aos 27min45s preservada.
Uma sessão curta não demonstra correção da falha tardia ou estabilidade prolongada.
CAUCAFall avaliado: 12 arquivos novos (4 alvos/8 ADL), piso/cenas/faixas
confirmados pelo fundador antes da inferência e candidato congelado. Todos
ok/ENDED: 722 análises, 3/4 alvos detectados, uma perda, zero alertas nos oito
ADL e zero duplicações. 107600 ms elegíveis/142000 ms observados, caudas de
1800 ms. Perda FallLeftS9: quadril dentro em 36/36 observações elegíveis no alvo,
mas geometria projetada 2D fora dos gates. Não corrigida por esta avaliação.
Quatro atividades comuns, mesma sala/câmera; não é eficácia geral ou 12 sessões.
Avaliação exploratória executada e documentada, mantendo limites/desfecho adverso.
Pendente: executar/revisar a sessão curta de 10 min nominais (D51).
Apresentação formal dispensada (D50). Etapa 08 permanece PARCIAL.
[Resultados, diagnóstico, protocolo e reprodução](RELATORIOS/CAUCAFALL_ETAPA_08.md).
Prévia adicional solicitada: 20.mp4/intake08-17, material já CALIBRATION,
processado por quadro com RTMO-s e o mesmo filtro visual, aberto pausado.
Fundador confirmou fluidez/acompanhamento, mas relatou piscar; 60/342 quadros
NO_POSE em 29 intervalos. Limitação preservada, sem mudança de limiar. Não usou
vídeos novos reservados ou webcam nem aprovou eficácia geral. Detalhes no relatório 08.
Historicamente, o fundador deixou o teste físico de 30 min para depois; D51
define agora o ensaio curto de 10 min. Não iniciar webcam
automaticamente. Continuação sem câmera: dois clipes de cadeira com anotação
humana reavaliados no RTMO atual, 79 análises, 15424 ms elegíveis/observados,
196 ms de cauda não amostrada e zero eventos. Mesmo grupo/categoria, CALIBRATION;
sem estimativa independente de eficácia. Plano de novas cenas preparado em
`.local/etapa08/current-evaluation-plan.json`. Resultados e limites no relatório 08.
Verificação geral após estabilização: 14 tarefas aprovadas, 317 Python, 155 API,
100 contratos TS, 20 E2E, simulador, frozen/lint/tipos/build/imports, restore e
instalação limpa. SHA atual a2b76fa33449fac7a438efa10e5470580b6310a6b12530d62bf33790b8aeb991,
179 arquivos; demo:check --engineering 0, demo:check 2 por gates manuais.
Fundador conferiu a CLI normal durante inferência: “Acompanha bem; movimento
aceitável”. Execução 5f15051f… terminou ok/ENDED, 32 análises com pose válida,
sem webcam, eventos ou HTTP. Pausa inicial de 1129,76 s separada das métricas;
não usar seu tempo total como desempenho de inferência. Conferência FILE encerrada.
Estabilização integrada como opção da prévia FILE/LIVE, false por padrão.
Somente desenho ciano; observações, evidência, frequência e identidade da execução
preservadas. Medição cadenciada com inferência real: cerca de 7,2–7,4 desenhos/s
sem janela e 5,2 com janela no ensaio, sem promessa de 30 FPS. CLI normal terminou
a cadeira com 32 análises válidas e sem ausências. 38 regressões direcionadas
passaram; resultado geral no relatório desta rodada.
[Integração, medições e reprodução](RELATORIOS/EXECUCAO_REAL_E_PREVIA_ETAPA_08.md).

Auditoria do material: os sete vídeos antes reservados para Full pertencem ao
grupo de ambiente posteriormente usado no diagnóstico/seleção do candidato.
Resultados históricos preservados; esse grupo é CALIBRATION para a versão atual,
sem avaliação independente comprovada. Cenas novas precisam ser anotadas antes
da análise, com modelo/política fixados. Preparo privado atual do ensaio curto em
`.local/etapa08/webcam-10min.yaml`: modelo/hash e estrutura do piso
verificados, saída/fila novas, sem abrir câmera ou autenticar credencial.
Depende de disponibilidade física; não requer repetir a postura no chão.

Histórico da pesquisa anterior à integração opcional:
Fundador conferiu a estabilização na cadeira 2: acompanha bem, com boa fluidez,
sem partes desaparecendo e com menos tremor; pequenas oscilações permanecem.
Confirmação visual desta cena pré-processada, sem prova de FPS LIVE ou precisão
geral. Parâmetros do candidato preservados; integração operacional e desempenho
na velocidade real continuam pendentes. Não repetir a mesma conferência.
Fundador conferiu RTMO-s por quadro na cadeira 2: visível, mais fluido e
acompanhando melhor, com tremor parado. Experimento privado de estabilização
visual executado em 1236 quadros, mantendo pontos disponíveis e dados brutos;
11 testes específicos passaram após ajuste de resposta. Comparação aberta
pausada; não adotada no worker nem usada nos alertas. Redução de oscilação
sintética não comprova precisão corporal ou desempenho LIVE.
Investigação quadro a quadro: 1236 imagens em seis vídeos por modelo. RTMO-s
manteve 12 pontos em 187/187 quadros da cadeira 2, sem fluxo óptico; custo completo
7,66–8,03 quadros/s, sem comprovar precisão ou FPS LIVE. RTMO-t privado foi mais
rápido e perdeu mais poses no conjunto; não adotado. Reaplicação temporal mostrou
que aumentar análises pode mudar tipo/horário do alerta. Worker, frequência de
decisões, gates e locks preservados. Comparação por quadro aberta pausada para
conferir alinhamento. Preferência de qualidade registrada em D48.
[Dados e comandos](RELATORIOS/QUADRO_A_QUADRO_ETAPA_08.md).
Conferência humana da comparação: direita mais fluida, mas segmentos piscam e
impedem confirmar alinhamento. Diagnóstico localizou perdas no acompanhamento
entre análises da cadeira 2 (74/155 quadros intermediários), apesar de 12 pontos
aceitos nas 32 âncoras. Uma tentativa direta da última âncora piorou as perdas
no conjunto de 20 clipes e não foi adotada. 13 regressões direcionadas passaram;
sem mudança operacional, câmera ou novos incidentes. Detalhes no relatório abaixo.
Investigação da fluidez: comparação em 20 clipes/4581 quadros, preservando 776
observações originais. Fluxo óptico e variante por vizinhança deram cadência
visual maior em replay, mas ainda perderam segmentos; não adotados no worker
operacional e sem prova de precisão anatômica ou desempenho LIVE. Sem webcam.
[Métodos, perdas, comparação e comandos](RELATORIOS/FLUIDEZ_E_ALINHAMENTO_ETAPA_08.md).
Offline verificado em replay/serviços em 23/10: fundador confirmou desconexão
de Wi-Fi/cabo e conferência do incidente antes de reconectar. Tentativa externa
falhou; API e proxy HTTP 200; RTMO FILE terminou com um evento REPLAY/TEST
entregue, incidente `cbf11212-8a99-444c-89a3-051284628d04`. Sem webcam ou JPEG.
Webcam offline, novo login/revisão offline e reenvio offline não exercitados.
Sessão contínua RTMO de 23/10 encerrou aos 1665,64 s (27 min 45,64 s), com
PROCESSING_ERROR e captura final ERROR; não atingiu os 30 min. Foram 7906
análises e zero eventos. O adaptador informou zero reconexões e nenhum erro
próprio de captura; a causa da exceção de processamento ainda não foi determinada.
Não atribuir ao hardware o rótulo genérico CAPTURE_ERROR do heartbeat final.
Logs preservados em `.local/etapa08/continuous-rtmo-launch.json`; teste não aprovado,
sem repetição automática da webcam. Fundador relatou cadeira/pés apoiados, saída
do quadro inferior a um minuto, sem postura no chão; pose oscilando/desalinhada.
Investigação reproduziu bloqueio Windows na publicação do status, com correção
de tentativas limitadas e diagnóstico seguro; 289 testes Python passaram.
Causa histórica não comprovada e fluidez/precisão da pose não corrigidas.
[Resultados e limites](RELATORIOS/ESTABILIDADE_WEBCAM_ETAPA_08.md).
Preparação física atual: webcam 0/DSHOW conferida pelo fundador em probe sem
inferência, calibração privada RTMO v2 salva após espera de 20 s para liberar
a visão do chão. Banco Healthy, API e login web HTTP 200. Ensaio RTMO LIVE de
90,48 s executado com encerramento automático: 405 análises e um PERSON_ON_FLOOR
entregue em uma tentativa, classe CURRENT, sem duplicação, JPEG ou erro final.
Incidente `4e6f8c4b-d366-4787-8f31-645fee7988c5` conferido pelo fundador no
painel, Ao vivo/Atual com pose e sinais. Fundador forneceu histórico auditado:
reconhecimento v1→2 às 14:05:12 e revisão Postura no chão confirmada v2→3 às
14:05:37, com nota de teste controlado sem queda; nova revisão equivalente v3→4
às 15:48:06. Fluxo LIVE→incidente→revisão atendido neste ensaio. A revisão
repetida não é outro incidente. Não substitui 30 min ou avaliação independente.
RTMO-s agora integrado como opção experimental real no worker FILE/LIVE,
sem trocar configurações Full/Lite. Qualidade/contrato confidence explícitos,
ONNX Runtime fixado e único cv2. Download oficial e hashes verificados. Comparação
nativa com motor/fila: 20 clipes × Full/RTMO, 776 inferências por modelo,
8/12 eventos; oito casos emitidos pelo Full preservados, quatro casos adicionais,
incluindo dois ADL ainda sem anotação humana completa. Isso não é medida de
eficácia. Os dois vídeos de sentar continuaram sem eventos; os três perdidos
continuaram sem evento, com quadril fora da ROI durante os trechos deitados.
Gates/ROIs não foram relaxados para aprovar o candidato. Regressão geral atual
passou em 14 verificações após os instrumentos de comparação: 302 Python, 155 API,
100 contratos TS (também no Python),
20 E2E e quatro testes do simulador; lint/tipos/build, restore e instalação limpa.
Fingerprint atual 7927d913436cd52cc7cbcf330ec01a845f31cf8e79cd58b5a5d931810d2a142f,
177 arquivos; demo:check --engineering retornou 0 e demo:check retornou 2.
Isso não aprova a percepção em geral. Avaliação de percepção, 30 min e apresentação
continuam pendentes. [Integração e resultados](RELATORIOS/INTEGRACAO_RTMO_ETAPA_08.md).

Histórico anterior da investigação (22/10), antes da integração:
Investigação da pose sobre a cadeira: máscara corporal do próprio Full não
resolveu o defeito, pois também incorporou parte da cadeira. Alternativa RTMO-s
executada em ambiente privado separado, CPU/ONNX Runtime, 210 inferências em seis
clipes de calibração. Comparação no segundo vídeo de sentar teve os mesmos pixels
e timestamps em 32/32 amostras. Fundador confirmou que o RTMO acompanha melhor as
pernas e deixa de ir para o pé traseiro da cadeira nessa cena. Média 126,49 ms,
P95 152,15 ms no conjunto; duas inferências acima de 200 ms. **Melhora visual
experimental confirmada; correção no worker operacional ainda pendente.** O RTMO
fornece score articular, não visibility/presence equivalentes ao MediaPipe:
integração exige contrato de qualidade explícito, regressão do motor e avaliação
independente. Full, contratos, gates e locks operacionais preservados. Ver
[investigação da cadeira](RELATORIOS/INVESTIGACAO_CADEIRA_ETAPA_08.md).

Dois novos vídeos de sentar recebidos, copiados por hash e decodificados:
correspondem exatamente a GMDCSA24 Subject 1/ADL/11.mp4 e 13.mp4. Mesma origem
de grupo já analisada, sem independência de sessão confirmada: confundidores de
calibração, sem contagem de novas categorias distintas. Fundador salvou o piso
do primeiro pela GUI: v1, dez pontos. Prévia poses-only aberta pausada a 0,5x
para revisão integral da cena e piso. Fundador confirmou piso correto e ausência
de pessoa no chão; anotação negativa registrada antes do teste temporal. Evaluate
real do primeiro passou, sem eventos: 9216 ms observados, 8624 ms elegíveis,
98 ms de cauda não observada. Ensaio curto de calibração, sem taxa geral de falsos
alertas estimada. Fundador salvou o piso do segundo, v1 com nove pontos;
prévia poses-only concluída. Fundador relatou pontos do esqueleto sobre a cadeira
ao sentar de lado. Diagnóstico das 32 observações: uma pose por amostra, 31/32
elegíveis tecnicamente, zero candidatas e zero emissões na reaplicação do motor
sem HTTP/outbox. Inspeção de quadros confirma projeção de parte dos pontos junto
à estrutura da cadeira; confiança não comprova localização correta. Depois,
fundador confirmou piso e cena negativa integral; evaluate real do segundo
terminou sem eventos, 6208 ms observados e 5808 ms elegíveis, cauda 98 ms.
Ambos os ensaios de sentar tiveram zero eventos, sem concluir eficácia geral
ou corrigir a associação de pontos à cadeira. São dois casos da mesma categoria
e grupo de origem, não avaliação independente completa. Etapa continua PARCIAL.
Comparação Full/Heavy
executada em 17 clipes de calibração/diagnóstico, mesmos
gates: 7/3 eventos, nenhum dos três perdidos recuperado. Heavy levou 62,43 ms por
inferência em média contra 27,21 ms do Full; não adotado. Qualidade da percepção
continua pendente. [Comparação](RELATORIOS/COMPARACAO_POSE_ETAPA_08.md).
Regressões de engenharia,
instalação e restore permanecem verificados. **Complemento com novos materiais:**
21 curtos do GMDCSA24 associados pelos bytes a participante/pasta/caminho exatos e
dois episódios de yoga verificados no Internet Archive; licenças registradas.
14 curtos em calibração produziram sete eventos; comparação 5/15 Hz preservou
os mesmos eventos/offsets. Sete curtos do Subject 1 ficaram separados para avaliação:
quatro posturas com janela suficiente na anotação provisória, uma detectada e três
perdidas; três posturas curtas/limítrofes adicionais continuam listadas. Anotação
e piso pelo assistente, com revisão humana pendente. 16.841 inferências em cerca de
56 min de yoga **REPLAY**, com motor de piso desabilitado durante a montagem com
cortes: não substitui 30 min LIVE nem mede falsos alertas. Full/gates/produção
preservados, nenhum peso treinado. 05.mp4/07.mp4 novos não são os históricos;
as cópias antigas foram recuperadas da fonte e verificadas pelo SHA-256, em caminhos
separados, sem sobrescrever os novos. [Materiais/resultados](RELATORIOS/MATERIAIS_ETAPA_08.md).

Revisão visual posterior do novo 03.mp4: fundador observou esqueleto acompanhando
o corpo, com oscilação em repouso, e piso a refinar; não aprovou definitivamente
a calibração. Inspeção da prévia completa: 11/13 amostras desde 3408 ms com baixa
confiança em joelho/tornozelo esquerdos; somente duas candidatas, ambas já dentro
do piso. Fundador remarcou a cópia privada pela GUI: versão 2, sete pontos, original
v1 preservado. Reaplicação das mesmas observações ao novo piso manteve duas
candidatas, onze inválidas e nenhum evento. Fundador confirmou explicitamente
o alinhamento visual do novo contorno. Diagnóstico com imagem idêntica repetida
teve pontos válidos estáveis após cinco inferências, mas joelho/tornozelo com
baixa confiança nas 30 amostras; não prova melhoria no vídeo. Revisão dos trechos
finais dos novos 05 e 07 também encontrou baixa visibilidade em joelho/tornozelo,
sem observação elegível. Na revisão do 05, fundador considerou o esqueleto
razoável, mas reprovou a ROI inicial por estar alta e incluir parede. Fundador
remarcou o 05 na cópia privada: versão 2, sete pontos, e confirmou visualmente
o alinhamento do novo contorno. Reaplicação das mesmas observações manteve 13/13
inválidas no trecho final e nenhum evento com ambos os pisos. Prévia do 05
encerrada pelo agente; prévia do 07 aberta pausada para a revisão restante.
Na revisão do 07, fundador considerou o acompanhamento corporal bom para MVP,
mas pediu remarcação do piso. Fundador salvou a versão 2 com oito pontos na
cópia privada do 07. Comparação das mesmas observações manteve 14/14 inválidas
no trecho final e nenhum evento com ambos os pisos. Prévia v2 aberta pausada,
a conferência foi concluída e o fundador confirmou o piso v2 do 07. Assim, os
pisos revisados dos três vídeos perdidos (03/05/07) estão confirmados. Nova
execução completa de inferência/motor com esses pisos, em filas exclusivas e
sem HTTP, terminou com zero eventos nos três. Manifesto de diagnóstico separado
classifica esta revisão como CALIBRATION, preservando a avaliação congelada;
nenhum ganho de detecção comprovado. Engenharia continua com check exit 0.
Visibilidade integral de
pernas/pés e início da postura não foram confirmados. Nenhuma mudança de detector/suavização
aplicada; etapa continua PARCIAL.

**Registro da rodada de engenharia anterior ao recebimento dos novos vídeos:**
instalação limpa e backup/restore isolados verificados. 266 Python, 145 API,
91 contratos TS e 18 E2E aprovados; locks/modelos/gates preservados. Seis arquivos
CALIBRATION reprocessados: um positivo aos 6000 ms, cinco sem evento; sem métricas
independentes de eficácia. Fundador informou que hoje não pode realizar ensaio
físico e precisa gravar novas cenas. Faltam avaliação anotada independente, LIVE
positivo com revisão humana, 30 min contínuos, teste offline e apresentação.
Nenhuma câmera foi aberta nesta etapa, nem alterada a rede global. Release candidata
local parcial; sem commit/push/tag/deploy. [Relatório 08](RELATORIOS/ETAPA_08.md),
[matriz final](RELATORIOS/VALIDACAO_MVP.md) e [passos para concluir](VALIDACAO_MANUAL_ETAPA_08.md).

**Histórico — 22/10/2026:** etapa 07 **CONCLUÍDA no escopo solicitado**.
Evidência mínima, JPEG pontual sintético, armazenamento privado, acesso/exclusão
por papel, auditoria, retenção e deduplicação após redação/purga verificados.
262 testes Python, 145 API, 91 contratos TS e 18 E2E aprovados; demonstração
sintética desktop adicional aprovada. Lint, tipos, build e instalações frozen
aprovados; OpenAPI regenerado. Migração aditiva aplicada em 15432, contagens de
cadastros/incidentes/recibos/auditoria preservadas. Webcam real permanece skeleton,
sem JPEG e sem nova captura. Limpeza automática API e purga de 30 dias não foram
ativadas no ambiente pessoal; os testes usaram recursos exclusivos e relógio
injetável. Commit e push autorizados pelo fundador em 22/10/2026; sem deploy; etapa 08 não iniciada. Veja [relatório 07](RELATORIOS/ETAPA_07.md)
e [roteiro 07](VALIDACAO_MANUAL_ETAPA_07.md).

**Histórico — 22/10/2026:** etapa 06 **CONCLUÍDA no escopo da bancada**.
Calibração WEBCAM v1 e pose no corpo conferidas pelo fundador. Sessão de 384
análises em 83,72 s, vazão global 4,59 análises/s, inferência média 25,34 ms;
sessão guiada posterior de 981 análises em 231,23 s terminou sem erro.
Fundador confirmou no painel LIVE → Pausada → retomada → Fonte encerrada,
e fechamento da janela. Frames novos e estados foram conferidos localmente e
no servidor. Recuperação/limites/duplicação verificados em recursos dedicados;
243 testes Python aprovados e 125 API/87 contratos TS anteriores preservados.
Pose falsa na estante, fluidez em 5 Hz e falta de evento LIVE positivo são
limitações/pendências da validação final do MVP. Commit/push autorizados pelo
fundador após a validação; sem deploy. Etapa 07 não iniciada.

**Histórico anterior — 21/10/2026:** etapa 06 parcial naquele momento, com captura
física e inferência em um frame, mas sem calibração. A abertura de calibração pela
IA retornou ValueError/CONFIG_OR_ENVIRONMENT_ERROR, sem causa identificada. O
fundador concluiu a calibração e uma sessão contínua em 22/10; o erro anterior não
reapareceu nessa execução, sem comprovar sua causa. A regressão API de 125 testes
e os testes de entrega/recuperação anteriores continuam registrados no relatório.

**Software implementado:** fundação, API, painel, simulador, contratos, FILE e WEBCAM;
motor temporal, SQLite com retomada/limites, envio/heartbeat independentes e
controles locais. **Modelo executado:** Lite/Full CPU/VIDEO em arquivos; Full
também em sessão física contínua, com pose no corpo conferida pelo fundador e
falso reconhecimento de estante relatado. Origem dos arquivos reais anteriores
declarada pelo fundador, sem verificação independente da internet; vídeo gerado
por IA permanece separado. **Câmera física:** índice 0 escolhido pelo fundador,
DSHOW, 640×480, prévia conferida; inventário Windows lista Positivo Theia Camera.
**Última etapa concluída:** 08, no escopo revisado da bancada em 24/10/2026;
limitações de percepção e alcance dos testes permanecem explícitas.

Este arquivo é a fonte de verdade de progresso. Os READMEs das etapas apresentam o plano; só atualizar para concluída quando os critérios tiverem evidência real.

| Etapa | Entrega | Status | Relatório / data |
| --- | --- | --- | --- |
| 00 | [Fundação do repositório e ambiente](../etapas/00_FUNDACAO/README.md) | CONCLUÍDA | [ETAPA_00](RELATORIOS/ETAPA_00.md) · 21/10/2026 |
| 01 | [Domínio, banco e acesso](../etapas/01_DOMINIO_E_ACESSO/README.md) | CONCLUÍDA | [ETAPA_01](RELATORIOS/ETAPA_01.md) · 21/10/2026 |
| 02 | [Eventos, incidentes e contratos](../etapas/02_EVENTOS_E_INCIDENTES/README.md) | CONCLUÍDA | [ETAPA_02](RELATORIOS/ETAPA_02.md) · 21/10/2026 |
| 03 | [Painel e primeira demonstração](../etapas/03_PAINEL_E_SIMULADOR/README.md) | CONCLUÍDA | [ETAPA_03](RELATORIOS/ETAPA_03.md) · 21/10/2026 |
| 04 | [Visão computacional em arquivo](../etapas/04_VISAO_EM_VIDEO/README.md) | CONCLUÍDA | [ETAPA_04](RELATORIOS/ETAPA_04.md) · 21/10/2026 |
| 05 | [Motor temporal e eventos de visão](../etapas/05_MOTOR_TEMPORAL/README.md) | CONCLUÍDA | [ETAPA_05](RELATORIOS/ETAPA_05.md) · 21/10/2026 |
| 06 | [Webcam, disponibilidade e recuperação](../etapas/06_WEBCAM_E_RESILIENCIA/README.md) | CONCLUÍDA · bancada | [ETAPA_06](RELATORIOS/ETAPA_06.md) · 22/10/2026 |
| 07 | [Evidência opcional, retenção e proteção](../etapas/07_EVIDENCIA_E_PROTECAO/README.md) | CONCLUÍDA | [ETAPA_07](RELATORIOS/ETAPA_07.md) · 22/10/2026 |
| 08 | [Validação final e entrega da demo](../etapas/08_VALIDACAO_E_ENTREGA/README.md) | CONCLUÍDA · escopo revisado da bancada D50/D51 | [ETAPA_08](RELATORIOS/ETAPA_08.md) · 24/10/2026 |
| 09 | [Câmera IP e verificação da KAP-S069](../etapas/09_CAMERA_IP_OPCIONAL/README.md) | NÃO INICIADA · opcional | — |

## Estados permitidos

`NÃO INICIADA`, `EM ANDAMENTO`, `PARCIAL`, `BLOQUEADA`, `CONCLUÍDA`. Para 09 também `DISPENSADA` se o fundador decidir não testar IP. Incompatibilidade comprovada da câmera pode concluir a investigação opcional; não equivale a suporte RTSP no aparelho.

## Registro do ambiente

| Item | Valor verificado |
| --- | --- |
| SO / arquitetura do computador de implementação | Windows 11 Pro, 10.0.26200, x64; PowerShell 5.1.26100.9711 |
| CPU / RAM / GPU | AMD Ryzen 5 5625U, 6 núcleos/12 threads; 15,4 GiB de RAM visível; AMD Radeon (TM) Graphics; sem teste de aceleração |
| Versões exatas Node / pnpm / Python / uv | 24.22.1 / 10.34.7 / 3.12.15 / 0.13.4; Node 22.21.1 e Python 3.13.7 preexistentes preservados |
| MediaPipe / OpenCV / bundle e hash | MediaPipe 1.1.1 e único opencv-contrib-python 5.0.0.93 (cv2 5.0.0); Tasks Lite float16/v1, SHA-256 59929e1d1ee95287735ddd833b19cf4ac46d29bc7afddbbf6753c459690d574a; inferência CPU real em sintético e em arquivo autorizado de pessoa; [inventário](RELATORIOS/DEPENDENCIAS_E_MODELOS.md) |
| Docker / banco | Desktop 4.57.0, Engine 29.1.3, Compose 5.0.1; PostgreSQL 17.11 saudável; TCP autenticado e volume persistente verificados; loopback 15432 nesta máquina (D15) |
| Persistência / acesso (01) | Prisma/client/adapter-pg 7.10.1, pg 8.23.1, Argon2 0.45.1; migração inicial aplicada em radar:15432 e banco vazio dedicado; 19 testes de integração aprovados |
| Eventos / contratos (02) | Migração 20261021000200_events_incidents aplicada em banco vazio exclusivo e radar:15432; 19 testes anteriores + 104 novos aprovados; contratos: 87 TS e 87 Python; roteiro PowerShell exercitado por HTTP real em banco isolado |
| Painel / demonstração (03) | Playwright 1.64.1/Chromium 156.0.8078.4; 16 E2E reais aprovados em desktop 1440×1000 e móvel 390×844; 123 regressões API e87 + 87 contratos preservadas; screenshots sintéticas privadas inspecionadas |
| Visão em arquivo (04) | Python 3.12.15/uv 0.13.4 preservados; PyYAML 6.0.3 novo, NumPy 2.5.4 mantido e declarado direto; 139 testes Python, incluindo 87 contratos, e 87 contratos TS aprovados; arquivo bancada-01: 530 frames/89 observações, mesma sequência em três velocidades; seleção do piso e conferência visual realizadas pelo fundador |
| Webcam e índice | Etapa 06 concluída para bancada: índice 0/DSHOW, 640×480, Full/piso v1. Probe inicial 10 FPS, sessão contínua de 384 análises e sessão guiada de 981 análises, controles conferidos no painel. Zero candidatos/eventos nos dois ensaios; pose falsa na estante relatada. 243 Python, 125 API/87 contratos TS; checks aprovados, sem comprovar evento LIVE positivo |
| Motor temporal (05) | Sem dependências novas/lock alterado; SQLite nativo; 226 testes Python e 124 API em PostgreSQL exclusivo; 87 contratos TS. Full oficial fixado por hash, 45 análises/40 elegíveis/32 candidatas em piso-f-07; evento aos 6000 ms, incidente REPLAY/TEST conferido. Evaluate sem espera/2× reproduziu o offset; EOF/reenvio sem duplicação |
| KAP-S069 / firmware / protocolo | Não confirmado; etapa 09 opcional |

## Pendências atuais

- **Percepção 08 após novos vídeos:** avaliação independente CAUCAFall executada
  com revisão humana e candidato congelado: três alvos detectados e uma perda,
  zero alertas nos oito ADL com cobertura limitada. Não aprova eficácia geral.
  O grupo antigo usado no desenvolvimento permanece CALIBRATION. Se houver novos
  ajustes usando estes resultados, registrar nova versão e sua classificação
  para desenvolvimento. Não pedir novamente os mesmos vídeos/confirmações.
  LIVE/revisão, offline e sessão curta nominal de 10 min verificados
  (D51). Novo trecho no chão sem alerta permanece possível perda/inconclusivo;
  não é gate positivo adicional comprovado. O teste original de 30 min não foi
  comprovado. Apresentação
  formal dispensada pelo fundador em D50, sem declarar que foi executada.

- **08 encerrada no escopo revisado:** [matriz final](RELATORIOS/VALIDACAO_MVP.md).
  Não exigir repetir a sessão física para encerrar esse escopo. Limitações e
  backlog no relatório 08. `demo:check --engineering` verifica engenharia;
  `demo:check` mantém exit 2 por lista manual fixa, não por leitura do aceite
  documental. Essa limitação do checker não representa aprovação automática.

- Nenhum critério obrigatório da etapa 07 pendente. JPEG funcional comprovado com
  pixels sintéticos sem pessoas, sem ativar snapshot real. Agendamento API default
  false e purga de metadados false são escolhas operacionais preservadas, não
  declaração de dados já apagados. Rodada explícita e job habilitado verificados
  em banco/diretório exclusivos; [roteiro 07](VALIDACAO_MANUAL_ETAPA_07.md).
- Na avaliação final da 08 permanecem limitações de percepção, incluindo estante,
  três perdas e fluidez em condições não verificadas. Evento LIVE positivo já
  comprovado na 08; a 07 não alterou detector.

- Nenhuma verificação obrigatória da etapa 00 pendente. Reprodução em [ambiente e comandos](08_AMBIENTE_E_COMANDOS.md).
- Nenhum critério obrigatório da etapa 01 pendente. Proprietário criado localmente pelo fundador e confirmado por contagem de OWNER ativo/auditoria, sem consulta de senha/hash. Login/configuração por PowerShell no [roteiro manual](VALIDACAO_MANUAL_ETAPA_01.md); a interface foi acrescentada na etapa 03.
- Nenhum critério obrigatório da etapa 02 pendente. Fluxo HTTP/PowerShell, transações, concorrência, ações, isolamento, classes de tempo, heartbeat e recuperação de avisos verificados; [relatório](RELATORIOS/ETAPA_02.md) e [roteiro manual](VALIDACAO_MANUAL_ETAPA_02.md). Nenhuma tela de incidentes, captura, inferência, snapshot ou comunicação externa implementada nesta etapa; retenção automática permanece na 07.
- Nenhum critério obrigatório da etapa 03 pendente. Painel/simulador com persistência real, retry/conflito, falha/expiração, RBAC, polling e layout verificados; [relatório](RELATORIOS/ETAPA_03.md) e [roteiro de apresentação](VALIDACAO_MANUAL_ETAPA_03.md). Inspeção visual em Chromium; móvel físico/outros navegadores e teclas interativas da CLI não foram verificados. Simulação comprova o fluxo de software, não IA ou câmera.
- Uso manual revelou falha de transporte após gravar o incidente: a API em modo watch reiniciou no mesmo intervalo. O comando do simulador deixou de recompilar contratos e ganhou retry limitado com envelope estável e erro de encerramento explícito. Quatro testes de transporte e um E2E real desktop aprovados após a correção; a execução original do fundador permaneceu parcial, sem confirmação de ENDED. O incidente persistido pode ser revisado normalmente; não foi substituído nem duplicado pelos testes.
- Monitorar compatibilidade dos plugins React/a11y antes de atualizar ESLint 9 (aviso de fim de suporte registrado no inventário).
- Nenhum critério obrigatório da etapa 04 pendente. O arquivo autorizado `bancada-01` terminou em três replays (sem espera, 2×, prévia 0,5×): 530 frames lidos, 89 analisados, 84 observações com qualidade suficiente e 5 de baixa confiança, sem fallback temporal. O fundador marcou o piso e confirmou o alinhamento da pose/região; [roteiro 04](VALIDACAO_MANUAL_ETAPA_04.md), [relatório 04](RELATORIOS/ETAPA_04.md). Isso não mede eficácia de queda; múltiplas pessoas reais não foram testadas. Aviso oficial do SDK sobre métricas de uso registrado; ausência total de tráfego nativo não foi comprovada e firewall foi preservado. A retenção do vídeo privado é manual, sem prazo automático configurado.
- Nenhuma verificação obrigatória da etapa 06 pendente no escopo solicitado.
  Fundador confirmou piso, pose, pausa, retomada e encerramento no painel.
  Para a validação final do MVP: investigar pose falsa na estante em ensaio
  negativo delimitado e medir eficácia com anotações, sem confundir zero eventos
  nestas sessões com rejeição garantida de objetos. Fluidez acompanha análise em 5 Hz.
  Morte abrupta do adaptador físico com heartbeat liberou o driver e resultou em
  OFFLINE após mais de 15 s; o teste não teve inferência nem conferência visual. Evento LIVE
  positivo não foi observado e permanece para a validação final do MVP.
  [Roteiro 06](VALIDACAO_MANUAL_ETAPA_06.md) e [relatório 06](RELATORIOS/ETAPA_06.md).
- A janela de calibração usa imagem parada para marcar o piso; isso foi
  esclarecido após o fundador esperar vídeo ao vivo. Título e instruções ajustados;
  o roteiro separa probe (movimento), calibrate (pontos) e run (análise).
  A interação não concluiu a calibração nem a validação física integrada.
- A tentativa posterior de abrir calibrate pela IA falhou com
  CONFIG_OR_ENVIRONMENT_ERROR (ValueError). Causa histórica ainda desconhecida;
  em 22/10 o fundador salvou a calibração v1 e executou o pipeline. Não afirmar
  correção da causa por não ter reaparecido nessa tentativa.
- Prévia preta posterior: fundador confirmou tampinha de privacidade fechada.
  Depois confirmou que conseguiu conferir o enquadramento ao vivo seguindo o
  roteiro em pé, com corpo inteiro/chão. Sem alteração de driver/backend/permissões.
  Depois salvou o piso e conferiu pose durante run. A prévia probe anterior
  não executava inferência; controles no painel confirmados posteriormente.
- As duas cenas adicionais fornecidas pelo fundador, deitar em vista lateral e
  pessoa deitada em vista de cima, foram calibradas e processadas. Nenhuma gerou
  evento: o modelo não sustentou pontos essenciais suficientes. Não há incidente
  positivo novo para conferir no painel; a baseline permanece experimental e a
  prova positiva da 05 ficou pendente naquela fase, antes do ensaio Full.
- A quarta filmagem real, `piso-d`, terminou com 78 observações, 58 elegíveis e
  zero candidatas/eventos. O fundador confirmou piso, orientação correta e pessoa
  deitada durante vários segundos na prévia local. Quadril no piso em 58/58,
  mas ângulo de tronco 0,16–51,46° (mínimo 60°) e razão altura/largura 1,02–2,06
  (máximo 1). É uma falha observada da baseline nessa cena, compatível com uma
  limitação de projeção em 2D; não é solucionada apenas remarcando o piso.
  Nenhum gate ou rotação foi alterado para forçar detecção. Não há anotação
  temporal completa para estimar taxas de eficácia.
- Os arquivos seguintes, `piso-e-05` e `piso-f-07`, foram descritos como filmagens
  reais encontradas na internet, sem URL/licença ou origem verificadas. Ambos
  receberam calibração manual e terminaram normalmente, com zero eventos:
  51 análises/15 elegíveis/zero candidatas no primeiro e
  45 análises/15 elegíveis/6 candidatas sem janela suficiente no segundo.
  Não houve ajuste de parâmetros nem envio de mídia; outboxes separadas.
  O fundador reviu as duas prévias e relatou esqueleto verde piscando/sumindo,
  reconhecível mas insatisfatório. A instabilidade visual é coerente com os
  pontos insuficientes medidos; precisa ser tratada antes da prova positiva.
- Nenhum critério obrigatório da etapa 05 pendente. A configuração validada é
  `.local/edge-piso-f-07-full.yaml`: um evento real, entregue ao incidente
  `6cfd7d88-ae34-4b48-ad5a-d592cbd020a9`. Fundador conferiu prévia e painel.
  Os resultados negativos acima pertencem aos ensaios anteriores e não foram
  apagados. Full não resolveu o enquadramento `piso-d` nem todos os casos de baixa
  visibilidade. Evaluate permanece CALIBRATION, sem anotações completas; eficácia
  não estimável. Retenção foi acrescentada na 07; agendamento API e purga do fundador continuam desligados. [Roteiro 05](VALIDACAO_MANUAL_ETAPA_05.md),
  [relatório 05](RELATORIOS/ETAPA_05.md) e [investigação](RELATORIOS/INVESTIGACAO_ETAPA_05.md).
- Manter KAP-S069 como extensão opcional até confirmar acesso ao stream.

## Histórico de avanço

Validação adicional da 05: o fundador marcou pisos separados para `piso-a`
(lateral) e `piso-b` (vista de cima). Ambos terminaram normalmente, sem evento;
modelo/política/gates preservados. Limitações e hashes no [relatório 05](RELATORIOS/ETAPA_05.md).

Novo ensaio `piso-d`: filmagem de câmera/celular confirmada pelo fundador, piso
marcado e prévia conferida. Pessoa deitada não detectada pelos critérios em 2D;
resultado desfavorável registrado, mantendo a etapa parcial.

| Data | Etapa/decisão | Evidência |
| --- | --- | --- |
| 21/10/2026 | Documentação de construção organizada; demo antes de parceiro | D01 em decisões; ainda não há código de produto |
| 21/10/2026 | Etapa 00 concluída; PostgreSQL em porta alternativa local (D15) | Instalações frozen inclusive em diretórios vazios; lint, typecheck, build, Ruff, imports Python, HTTP direto/proxy, captura Edge e persistência do volume; [relatório](RELATORIOS/ETAPA_00.md) |
| 21/10/2026 | Etapa 01 concluída: domínio/acesso, migração e proprietário local | 19 testes reais em PostgreSQL exclusivo; seed/CLI, sessões, papéis, FKs de tenant, rotação concorrente, falha/retomada do banco, logs e bootstrap real confirmado; [relatório](RELATORIOS/ETAPA_01.md) |
| 21/10/2026 | Etapa 02 concluída: contratos, eventos, incidentes, heartbeat e avisos locais | 123 testes API (19 anteriores + 104 novos), 87 TS e 87 Python; migração aditiva preservou um OWNER, um local, duas câmeras e volume da demo; [relatório](RELATORIOS/ETAPA_02.md) |
| 21/10/2026 | Etapa 03 concluída: painel responsivo e simulador bearer | 16 E2E desktop/móvel com PostgreSQL/API/web exclusivos, pose sintética/revisão/aviso persistentes e regressões aprovadas; [relatório](RELATORIOS/ETAPA_03.md) |
| 21/10/2026 | Etapa 04 concluída: FILE→Tasks CPU→observações/ROI/prévia/medidas | 139 testes Python, 87 TS, modelo real em sintético e em arquivo autorizado; três replays completos com sequência idêntica, piso e prévia conferidos pelo fundador; [relatório](RELATORIOS/ETAPA_04.md) |
| 21/10/2026 | Etapa 05 inicialmente parcial: motor/SQLite/checkpoints/transporte/evaluate | 185 Python, 124 API, 87 TS; seis filmagens sem evento com Lite. Resultados negativos preservados no relatório |
| 21/10/2026 | Etapa 05 concluída após investigação e seleção explícita do Full (D34) | 226 Python, 124 API, 87 TS; evento real aos 6000 ms, entrega/reenvio/EOF sem duplicação, prévia e incidente conferidos pelo fundador; [relatório](RELATORIOS/ETAPA_05.md) |
| 21/10/2026 | Etapa 06 parcial: webcam nativa, saúde, limites e recuperação | Índice 0/DSHOW físico, pausa/retomada e Full em frame real; 125 API exclusivos. Credencial salva pelo fundador e autenticada; piso indisponível impede calibração/conferência integrada. [Relatório](RELATORIOS/ETAPA_06.md) |
| 22/10/2026 | Etapa 06 concluída no escopo de captura/saúde/recuperação de bancada | Piso próprio, Full contínuo, 384 + 981 análises; fundador confirmou pausa/retomada/encerramento no painel. 243 Python e verificações anteriores preservadas; falso esqueleto de estante e evento LIVE positivo pendentes para validação final. [Relatório](RELATORIOS/ETAPA_06.md) |
| 22/10/2026 | Etapa 07 concluída: evidência opcional/retencão/proteção | JPEG sintético, permissões, exclusão, recuperação e relógio controlado; 262 Python, 145 API, 91 TS, 18 E2E e demo desktop. Migração preservou dados; JPEG real/purga pessoal não habilitados. [Relatório](RELATORIOS/ETAPA_07.md) |
| 22/10/2026 | Etapa 08 parcial: engenharia/reprodução/restore e candidata local | 266 Python, regressões preservadas, instalação limpa, restore seguro, seis CALIBRATION reavaliados. Gates físicos/coleta/offline/apresentação pendentes; [matriz](RELATORIOS/VALIDACAO_MVP.md) |

## Regra de atualização

Ao terminar uma etapa, incluir link relativo para seu relatório real, comandos/testes executados, pendências e próxima etapa elegível. Não apagar falhas históricas; registrar correção. Nunca marcar um teste físico como feito apenas porque existe um adaptador implementado.
