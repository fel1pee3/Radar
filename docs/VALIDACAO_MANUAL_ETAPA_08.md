# Validação manual da etapa 08

**Fechamento — 24/10/2026:** etapa 08 concluída no escopo revisado da bancada
(D50/D51). Sessão continuous-4d4357f7… de 600,660 s encerrou normalmente, sem
reconexões/eventos, e o fundador confirmou fechamento automático/Fonte encerrada.
Não precisa repetir a sessão para encerrar esse escopo. A prévia analisou cerca
de 4,7 vezes/s; trecho no chão <10 s com corpo enquadrado não gerou alerta,
permanece possível perda/inconclusivo por falta de tempo exato/ROI confirmados.
[Resultados e limites](RELATORIOS/SESSAO_WEBCAM_10MIN_ETAPA_08.md).

Os procedimentos abaixo ficam como referência operacional. Estados de pendência
anteriores são históricos. Teste original de 30 min não comprovado; apresentação
formal dispensada D50. Não afirmar eficácia geral nem iniciar etapa 09 automaticamente.

## Histórico da preparação e comandos de reprodução

**24/10 — conflito resolvido após remarcação:** a fila ainda vinculada ao piso v2
bloqueou o início com a marcação v3 (SOURCE_CONFIG_CONFLICT). Reset auditado já
executado pelo agente, com backup/histórico preservados. Não precisa marcar de
novo nem repetir o reset agora: executar somente observe.ps1 com webcam-10min.yaml.
A tentativa encerrou após 2,23 s e zero análises; 10 min ainda não comprovados.

**D50 — apresentação formal dispensada pelo fundador.** Operação já exercitada
durante a construção; não exigir aprendizado ou sessão cronometrada. Roteiro
opcional, sem declarar apresentação executada. Referências históricas de
apresentação não são gate.

**D51 — situação atual:** por escolha explícita do fundador, o próximo ensaio
terá limite de 600 s do worker (10 min nominais), sem gravar vídeo. O timer inclui
abertura/modelo: tempo efetivo de captura/inferência será reportado separadamente.
O teste original de 30 min não foi comprovado; falha aos 27min45s preservada.
Uma sessão curta não comprova correção dessa falha tardia. Etapa 08 PARCIAL.
A configuração está preparada; não abrir a câmera automaticamente. Continuação
sem webcam reavaliou os dois clipes de cadeira já confirmados: 79 análises,
15424 ms elegíveis e zero eventos, CALIBRATION. Sem nova pergunta sobre essas
mesmas cenas e sem tratar essa amostra como avaliação independente.

CAUCAFall avaliado: fundador confirmou novidade, os 12 pisos e cenas/faixas
antes da inferência. Não repetir essas confirmações. Candidato congelado:
3/4 alvos detectados, uma perda, zero alertas nos oito ADL, sem duplicação.
Geometria projetada 2D explica o bloqueio no perdido, não corrigido nesta rodada.
Avaliação exploratória executada, sem aprovação de eficácia geral. Plano em
`.local/etapa08/current-evaluation-plan.json` e
[protocolo CAUCAFall](RELATORIOS/CAUCAFALL_ETAPA_08.md). Os materiais anteriores
continuam úteis para regressão, com as perdas preservadas.

Conferência anterior em “Radar - CAUCAFall - conferir piso e cenas” concluída;
pode reabrir pelo helper privado, sem contar como nova validação. O relatório
preserva confirmações, anotações, previsões e diagnóstico da perda.

Medição na velocidade real concluída em FILE, com inferência durante execução:
cerca de 5–7 desenhos/s no ensaio e estabilização de aproximadamente 0,3–0,4 ms.
Integração opcional no worker disponível, false por padrão, sem alterar alertas.
Para conferir com o vídeo/piso já preparados, sem webcam ou credencial:

```powershell
. ./scripts/activate.ps1
uv run --offline --project services/edge --frozen radar-edge run --config .local/etapa08/stabilized-worker-check/config.yaml --preview-paused
```

Começa pausado: Espaço inicia, Q/Esc encerra. Esse ensaio calcula a pose durante
a reprodução; a cadência pode ser menor que a comparação pré-processada. Não é
repetição da avaliação do mesmo MP4 gerado, nem prova de 30 min de câmera.
[Resultados e comandos](RELATORIOS/EXECUCAO_REAL_E_PREVIA_ETAPA_08.md).

**Conferência concluída:** o fundador respondeu “Acompanha bem; movimento
aceitável”. Run 5f15051f… terminou ok/ENDED, 32 análises válidas, sem ausências
ou erro. A execução ficou inicialmente pausada por 1129,76 s; isso não é tempo
de observação contínua ou medida de FPS. Não repetir a mesma conferência.

O próximo ensaio físico já tem cópia privada preparada, sem abrir câmera:
`.local/etapa08/webcam-10min.yaml`. Estabilização ligada, RTMO-s,
cópia do piso existente, limite de 600 s, resultados/fila novos, sem JPEG. Modelo/hash e
estrutura da configuração/piso verificados. Credencial apenas conferida como
arquivo existente; autenticação e enquadramento atual ainda precisam de conferência.
Não mudar o notebook depois de conferir o piso. Se mudou o enquadramento desde
a calibração anterior, conferir/remarcar antes; não herdar silenciosamente uma
ROI que já não corresponde à imagem.

Primeiro conferir o enquadramento em movimento, sem iniciar o ensaio medido:

```powershell
. ./scripts/activate.ps1
uv run --offline --project services/edge --frozen radar-edge probe --config .local/etapa08/webcam-10min.yaml --seconds 30 --preview
```

Esse diagnóstico mostra a imagem, sem desenhar pose ou decidir eventos. Q/Esc
fecha antes. Só depois de posicionar e sair da frente do piso, se precisar
remarcar a cópia, executar:

```powershell
uv run --offline --project services/edge --frozen radar-edge calibrate --config .local/etapa08/webcam-10min.yaml --frame-ms 0
```

A calibração congela uma imagem para clicar; não é travamento da câmera.
Não mover o notebook após marcar. Fechar o diagnóstico/calibração antes do teste.

Se remarcar novamente depois de já ter iniciado o worker com esta fila, o piso
muda de versão e o checkpoint anterior não pode ser retomado. Com worker parado,
renovar explicitamente o contexto antes de observar (preserva eventos/histórico;
não apaga incidentes nem a SQLite):

```powershell
uv run --offline --project services/edge --frozen radar-edge reset-episode --config .local/etapa08/webcam-10min.yaml --reason floor-recalibrated-before-observation
```

Não executar esse reset em retomada normal sem mudança de configuração. Não
remover a proteção de conflito ou apagar a fila para evitar o erro. O reset
necessário para o piso v3 já foi realizado em 24/10, conforme nota inicial.

Quando o piso estiver conferido, com API/web iniciadas e câmera livre:

```powershell
. ./scripts/activate.ps1
powershell -NoProfile -File scripts/validation/observe.ps1 -Config .local/etapa08/webcam-10min.yaml
```

Este comando abre a webcam e encerra automaticamente por volta de 10 min.
Tentativa de 24/10 bloqueada antes da inferência, contexto renovado sem câmera;
sessão de 10 min ainda pendente. Observar atividades comuns e seguras,
sem pausa, reinício ou suspensão do notebook. Não precisa deitar novamente ou
conversar no chat durante a sessão. Q/Esc interrompe, se necessário; registrar
a interrupção sem declará-la ensaio completo. O agente confere aquecimento,
duração efetiva, intervalos sem pose, recursos, eventos, fila e motivo final.
Não aprovar apenas pelo relógio nem apresentar como validação de 30 min.

Frentes da validação e estado atual:

| Trabalho | Agente | Fundador | Evidência para encerrar |
| --- | --- | --- | --- |
| Percepção e separação dos vídeos | Executado/documentado CAUCAFall congelado | Novidade/piso/cenas/faixas já confirmados | 3/4 alvos, zero alertas nos oito ADL; perda e cobertura limitada explícitas, sem eficácia geral aprovada |
| Ensaio físico curto D51 | Acompanhar processo, conferir métricas/erros/fila | Disponibilizar webcam/cena por cerca de 10 min; registrar o que aconteceu, sem deitar | Limite de 600 s do worker, encerramento normal, duração efetiva/aquecimento separados e falhas/períodos não observáveis quantificados; não comprova 30 min |
| Apresentação formal | Roteiro opcional preservado | Dispensada pelo fundador (D50) | Não executada; operação já exercitada durante desenvolvimento |

LIVE positivo/revisão, offline e os checks de engenharia já estão comprovados
nos limites descritos nos relatórios. Não exigem repetição para este fechamento.

## Histórico anterior ao ensaio cadenciado e à integração

Conferência da estabilização já feita: fundador relatou boa fluidez e
acompanhamento, sem partes desaparecendo, com tremor menor e pequenas oscilações
residuais na cadeira 2. Não repetir essa pergunta como se ainda pendente. Próximo
passo técnico é medir a execução na velocidade real; replay pré-processado não
comprova FPS LIVE. Não abrir outra sessão física automaticamente.

O fundador já conferiu a pose real por quadro da cadeira 2: visível e acompanha
bem melhor com fluidez, ainda tremendo em repouso. Comparação privada do filtro:
`.local/etapa08/preview-stabilization.ps1`. Esquerda: bruto verde; direita:
mesmos pontos atuais estabilizados em ciano. Sem fluxo óptico, preenchimento de
ausências, alteração de alertas ou prova de FPS LIVE. Espaço reproduz, R repete,
Q/Esc fecha; começa pausada. Alinhamento da versão anterior já foi conferido;
a pergunta posterior sobre tremor também já foi respondida, conforme registro acima.
[Medições e limites](RELATORIOS/QUADRO_A_QUADRO_ETAPA_08.md).

O fundador já assistiu à comparação da cadeira 2: confirmou fluidez maior,
mas o piscar impediu confirmar alinhamento. Não pedir que repita essa mesma
conferência como se estivesse pendente. Instrumentação confirmou perdas entre
âncoras; nova alternativa privada piorou o conjunto e não foi ativada. Os
traços verdes esparsos são parte da legenda MODEL/FLOW, não medida de precisão.

Investigação técnica dos vídeos existente concluída nesta rodada: candidatos
visuais comparados em 20 clipes; ambos ainda perdem segmentos e não foram
adotados no worker. Não declarar que o esqueleto foi corrigido. Para localizar
falhas na comparação privada, sem webcam:

```powershell
. ./scripts/activate.ps1
powershell -NoProfile -File .local/etapa08/preview-flow.ps1
```

Começa pausada; Espaço reproduz, R repete, Q/Esc encerra. Esquerda: prévia por
quadros analisados; direita: candidato visual com pontos estimados em ciano.
São análises gravadas, sem benchmark LIVE ou novos eventos. Revisão visual serve
para diagnosticar, não para aprovar automaticamente a integração.
[Resultados e provas](RELATORIOS/FLUIDEZ_E_ALINHAMENTO_ETAPA_08.md).

## Sequência atual para concluir, sem repetir provas já feitas

Referência: prompt original do fundador da etapa 08 e critérios de release em
`07_VALIDACAO_E_DEMO.md`. LIVE→incidente→revisão e replay/API/painel offline
foram comprovados. Não solicitar novamente a mesma postura ou replay para
validar esses percursos. Combinações offline não exercitadas ficam descritas
como limites de escopo; não acrescentar novos gates independentes ao prompt.

1. Melhoria visual nesta rodada concluída para FILE: opção integrada, medidas e
   regressões aprovadas, acompanhamento/cadência conferidos pelo fundador.
   Observações brutas/gates preservados. Não equivale a validação geral LIVE.
   A investigação de status corrigiu um defeito reproduzido de I/O; não comprovou
   a causa histórica da interrupção. Evitar prolongar ajustes só nesta cadeira.
2. Relatório de percepção CAUCAFall executado: 4 alvos/8 ADL, três acertos, uma
   perda e zero alertas nos ADL com cobertura limitada. As condições/duração e
   lacunas estão registradas. Não exigir novamente o material ou anotações já
   confirmados. Caso este conjunto passe a orientar ajustes, registrar sua nova
   utilização para desenvolvimento e separar uma futura avaliação do candidato
   ajustado. Resultados históricos preservados.
3. Executar/revisar a sessão curta nominal de 10 min, conforme D51. O ensaio
   original de 30 min falhou aos 27m45s e continua não comprovado; não somar
   sessões nem afirmar correção da falha tardia. Não iniciar automaticamente.
   Conferir enquadramento/piso antes; não requer pessoa deitada ou conversa no
   chat. Usar a configuração webcam-10min.yaml e revisar os registros completos.
4. Após o ensaio contínuo, fechar matriz/relatórios/release local somente com
   os critérios técnicos comprovados e limites explícitos. Apresentação formal
   dispensada por D50; não pedir novamente. Etapa 09 não integra este aceite.

Melhoria do desenho, isoladamente, não aprova a percepção; erro conhecido pode
permanecer explicitamente limitado numa demo experimental. Não prometer ausência
de falhas nem transformar perfeição visual em requisito novo sem evidência.

Atualizado: 23/10/2026. **PARCIAL**. Engenharia, instalação e restore foram
reverificados após a integração RTMO. No registro inicial de 22/10 o fundador
estava indisponível para o ensaio físico e precisava gravar novas cenas. Aguardar
confirmação atual de posicionamento antes de abrir a webcam; o código não
substitui a participação física nem a revisão da cena.

Atualização da sessão física: RTMO produziu um incidente no ensaio curto, que
o fundador conferiu no painel. A sessão longa posterior encerrou com erro aos
27 min 45,64 s, abaixo de 30 min, sem alertas. Fundador relatou ficar sentado
com pés apoiados, uma saída do quadro inferior a um minuto e nenhuma postura
deitada; também relatou oscilações e baixa fluidez da pose. O teste contínuo
continua não aprovado. Investigação sem câmera corrigiu uma disputa reproduzida
de leitura/publicação de status no Windows e adicionou diagnóstico seguro;
não prova a causa histórica nem resolve o acompanhamento da pose. Não repetir
automaticamente a sessão física. [Resultados e verificações](RELATORIOS/ESTABILIDADE_WEBCAM_ETAPA_08.md).

Revisão humana do incidente LIVE confirmada: histórico fornecido pelo fundador
mostra reconhecimento e Postura no chão confirmada até a versão 4, com nota
de teste controlado sem queda. Esse ponto está atendido; não solicitar nova
postura ou nova revisão para comprovar o mesmo percurso. Revisão equivalente
repetida é outra ação auditada do mesmo incidente, sem duplicação do incidente.

Configuração RTMO preparada, sem abrir câmera: `.local/etapa08/webcam-rtmo.yaml`.
Reutiliza a webcam índice 0 e a câmera lógica já escolhidas, com calibração copiada
para revisão e outbox/resultados separados. Original `.local/edge-webcam.yaml`
preservado. Limite de 90 s no primeiro ensaio, esqueleto/none conforme escolha
anterior, JPEG desabilitado. Preparação não comprova posicionamento, credencial
válida, imagem, evento LIVE ou integração com o painel nesta sessão.

Quando o fundador confirmar a área segura/corpo inteiro, o agente prepara API/web,
confere o piso e conduz um ensaio curto antes de pedir 30 min. Não exigir que
o fundador fique no chão operando terminal nem provoque queda. Modelo e política
experimentais, com três perdas conhecidas preservadas; teste físico não apaga
essas limitações. Detalhes em [integração RTMO](RELATORIOS/INTEGRACAO_RTMO_ETAPA_08.md).

Depois desse registro inicial chegaram 21 curtos e dois vídeos longos. Foram
processados e associados às fontes, conforme o
[relatório dos novos materiais](RELATORIOS/MATERIAIS_ETAPA_08.md). A avaliação
reservada revelou perdas; piso e anotações feitos pelo assistente precisam de
revisão humana, e faltam confundidores anotados. Os longos foram replay e não
substituem os 30 minutos físicos abaixo. Os antigos 05/07 foram recuperados por
hash em caminhos próprios; não usar suas configurações nos novos arquivos de
mesmo nome.

[Resultado e matriz](RELATORIOS/VALIDACAO_MVP.md) · [Operação e backup](OPERACAO_E_BACKUP.md)
· [Apresentação](ROTEIRO_APRESENTACAO.md).

## 1. Retomar o projeto depois de desligar o computador

Abra o Docker Desktop e aguarde o banco ficar disponível. No terminal da raiz:

```powershell
. ./scripts/activate.ps1
pnpm.cmd infra:up
pnpm.cmd db:migrate
pnpm.cmd dev:api
```

Deixe esse terminal aberto. Em outro terminal na mesma raiz:

```powershell
. ./scripts/activate.ps1
pnpm.cmd dev:web
```

Abra http://127.0.0.1:3000 e use a conta existente. Não executar setup:owner de
novo, copiar tokens para o chat ou resetar banco. Cada novo terminal precisa de
activate.ps1. Use sempre 127.0.0.1 no navegador e na configuração de origem.

## 2. Verificação automática sem câmera

Em um terceiro terminal:

```powershell
. ./scripts/activate.ps1
pnpm.cmd demo:verify
pnpm.cmd demo:check --engineering
pnpm.cmd demo:check
```

`demo:verify` executa instalações frozen, lint/tipos/build, imports, contratos,
simulador, Python, API, navegador, restore e instalação limpa. Logs e comandos
ficam em `.local/etapa08/engineering.json` e `verify-*.log`. Exige Docker e os
binários exatos ativados. Não usa câmera nem reseta a demonstração. Pode consumir
alguns minutos e espaço para a cópia limpa. Builds podem reiniciar a API em watch;
faça a verificação antes da apresentação e com o worker parado.

`demo:check --engineering` retorna 0 somente com pré-requisitos e resultados desta
revisão aprovados. `demo:check` retorna **2 enquanto os gates manuais estiverem
pendentes**; código 1 indica falha ou ausência de evidência de engenharia. Ele não
transforma câmera, eficácia ou meia hora de observação em aprovadas. Fonte alterada
invalida o registro. O hash exclui documentação e next-env.d.ts gerado, normaliza
CRLF/LF e inclui código, testes, manifests e locks. O HEAD sozinho não identifica
o código alterado ainda sem commit.

A lista manual impressa pelo checker é genérica e ainda cita apresentação e
30 min do plano original, além de percursos já verificados. Não é uma leitura
das decisões D50/D51 ou das confirmações humanas. Para o estado manual atual,
consultar o início deste roteiro, STATUS e matriz. Nenhuma sessão física é
aprovada automaticamente pelo comando.

## 3. Preparação anterior com Full, mantida como referência

Para a continuação atual, usar a cópia RTMO preparada no início deste documento.
Ela tem uma cópia própria do piso, preservando a calibração anterior. Se o
enquadramento mudou, a remarcação deve ocorrer nessa cópia, antes do ensaio:

```powershell
uv run --offline --project services/edge --frozen radar-edge calibrate --config .local/etapa08/webcam-final-stabilized.yaml --frame-ms 0
```

Esse comando abre a câmera e ainda não foi executado nesta retomada. A captura
para marcar é parada; não é necessário estar na imagem. Preparação Full anterior:

Configuração e credencial anteriores são preservadas. A preparação cria uma
configuração separada, uma fila própria e uma cópia da calibração existente:

```powershell
. ./scripts/activate.ps1
uv run --project services/edge --frozen python scripts/validation/prepare.py
```

Resultado esperado: `status: ok`, `cameraOpened: false`. Rodar novamente preserva
os arquivos já preparados. Configuração nova: `.local/etapa08/webcam.yaml`, Full,
skeleton, sem JPEG, índice/backend herdados da configuração autorizada. Não houve
rotação automática da credencial anterior; se revogada, salve a nova pelo mecanismo
de clipboard descrito no roteiro 06, sem enviá-la pelo chat.

Posicione o notebook com estabilidade, tampa da lente aberta, boa iluminação,
corpo inteiro e uma região do chão visíveis. Feche outros programas que usam a câmera.
Se o enquadramento mudou, marque o piso novamente **nesta cópia**:

```powershell
uv run --project services/edge --frozen radar-edge calibrate --config .local/etapa08/webcam.yaml --frame-ms 0
```

A imagem fica parada para marcar o piso. Clique em pelo menos três pontos em
ordem, sem repetir o primeiro; exclua cama/sofá/estante e pressione Enter. Q cancela.
Não execute o próximo comando enquanto a janela de calibração estiver aberta.

## 4. Sessão contínua; evento LIVE já verificado

Com API e web ligados, execute:

```powershell
powershell -NoProfile -File scripts/validation/observe.ps1 -Config .local/etapa08/webcam-10min.yaml
```

O comando abre a prévia real e coleta recursos de uv/Python/filho de captura em
`.local/etapa08/continuous-<id>/resources.jsonl`. A configuração limita a sessão
a 600 s do worker (D51), incluindo abertura/modelo. Conferir tempo efetivo de
captura/inferência e aquecimento separadamente, sem pausa/reinício. Não aprovar
por apenas deixar o terminal aberto. Quantificar períodos sem condições elegíveis.

Faça atividades comuns e seguras; não precisa conversar no chat durante o
teste nem deitar no chão. O positivo já percorreu LIVE→incidente→revisão no
incidente 4e6f8c4b-d366-4787-8f31-645fee7988c5. O ensaio curto verifica
continuidade/qualidade e procura avisos indevidos; não precisa repetir esse
positivo. Registre horários de atividades, saída do quadro e interrupções em
anotação local. A sessão anterior terminou em 27m45s e não aprovou continuidade.

Em Fontes deve aparecer modo Ao vivo; ONLINE não prova pose válida. Se ninguém
fica no chão, a ausência de alertas é o resultado esperado, não uma perda. Um
alerta nessa cena deve ser revisto e registrado como possível aviso indevido.
Não provocar postura-alvo para concluir esta sessão. Esqueleto visível sozinho
não aprova o motor; não baixar gates para conseguir verde.

Ao terminar, usar o reportPath emitido no `worker.json` do monitor para localizar
o relatório na pasta results da preparação webcam-10min; conferir recursos,
fila, incidentes e estado final Fonte encerrada. Revisar períodos **sem alerta**
também é necessário. O monitor não grava vídeo, portanto anotações/conferência
humana são indispensáveis. A conclusão vale para o ensaio curto, não para 30 min.

## 5. Pausa, retomada, interrupção e fila

Controles já conferidos na 06; comandos abaixo são referência para diagnóstico,
sem exigir repetir a aprovação. Usar **sessão separada** do ensaio contínuo D51.
Em outro terminal ativado, execute um comando por vez e confira o painel:

```powershell
uv run --project services/edge --frozen radar-edge control --config .local/etapa08/webcam-10min.yaml --action pause
uv run --project services/edge --frozen radar-edge control --config .local/etapa08/webcam-10min.yaml --action resume
uv run --project services/edge --frozen radar-edge control --config .local/etapa08/webcam-10min.yaml --action reconnect
uv run --project services/edge --frozen radar-edge control --config .local/etapa08/webcam-10min.yaml --action stop
```

Expectativas: Pausada → imagem nova/execução → reabertura controlada → Fonte
encerrada. Ir até o teclado é permitido; a pausa não exige estar deitado. Q/Esc
também encerra. Fechar abruptamente o processo não equivale a ENDED: sem heartbeat,
o painel deve indicar indisponibilidade depois de mais de 15 s.

Com worker parado:

```powershell
uv run --project services/edge --frozen radar-edge outbox-status --config .local/etapa08/webcam-10min.yaml
uv run --project services/edge --frozen radar-edge deliver --config .local/etapa08/webcam-10min.yaml
```

Não apagar a SQLite para resolver erros. Pendências/autenticação/erro permanente
devem ser tratados explicitamente. O ensaio automatizado `pnpm.cmd test:api`
verifica queda da API, reinício, ACK perdido e deduplicação em recursos exclusivos;
é teste de engenharia com poses sintéticas, separado da prova física LIVE.

## 6. Novas cenas e anotação

Plano privado em `.local/etapa08/collection-plan.json`: 4 cenas seguras de pessoa
já no chão e 8 confundidores (sentar, agachar, ajoelhar, pegar objeto, alongar,
deitar voluntariamente, oclusão e saída do quadro). Podem ser do próprio fundador;
não há exigência de parceiro nem de pessoas diferentes. Gravar 10–20 s por cena,
identificando quando são da mesma sessão/ambiente. Não atribuir independência a
recortes, repetições ou velocidades diferentes. Não usar os sete vídeos anteriores
como novas amostras; um é gerado por IA.

Anotar antes de avaliar: autorização/origem, hash, pessoa pseudonimizada, sessão,
ambiente, duração/FPS reais, início/fim da postura, confundidores e intervalos não
observáveis com motivo. Não inventar URL/licença dos vídeos da internet existentes.
Use `services/edge/evaluation.example.json` como formato para
`.local/etapa08/evaluation.json`; novos campos opcionais origin, authorizationNote,
confounders e reason permitem documentar a coleta. Use role EVALUATION somente
para sessões não usadas para ajustes. Modelo/política fixados antes da análise.

Cada arquivo exige configuração FILE e piso selecionado nele, com outbox própria;
não reutilizar o piso da webcam em outro ângulo. Compare hash por
`Get-FileHash -Algorithm SHA256 .local/videos/<arquivo>.mp4`. Fonte FILE continua
REPLAY/TEST. Depois de revisar integralmente também os períodos sem alerta:

```powershell
uv run --project services/edge --frozen radar-edge evaluate --manifest .local/etapa08/evaluation.json
```

O comando usa filas novas e não envia HTTP. Para a apresentação, execute o run
operacional da configuração FILE autorizada, com entrega explícita, e registre
revisão humana no incidente. Reiniciar a mesma execução não deve duplicar; novo
ensaio intencional requer reset auditado ou uma outbox de sessão nova.

## 7. Teste sem internet

**Replay e serviços executados em 23/10.** O fundador confirmou desconexão e
conferência no painel antes de reconectar; API/proxy HTTP 200 e evento entregue
como REPLAY/TEST ao incidente cbf11212-8a99-444c-89a3-051284628d04. Registros
em `.local/etapa08/offline-check-865f2042-8e8a-4218-8e51-f73d10f6b7ce/`.
Não repetir esse replay como nova evidência; marcador preserva a sessão original.
Continuam não exercitados webcam offline, novo login, ação humana e reenvio
durante desconexão. Instalar dependências/modelo não conta como teste offline.
Em uma sessão combinada, iniciar API/web e preparar os arquivos; o próprio
fundador desconecta Wi-Fi/cabo externo pela interface do Windows, mantendo Docker
e loopback. Nenhuma interface/firewall foi alterada pela IA.

Sem usar install/model-fetch, conferir login, `/api/health/ready`, executar o
replay completo com Full, entrega/reenvio/revisão e depois webcam. Registrar hora
da desconexão/retorno e o teste externo falhando, além dos locais funcionando:

```powershell
Invoke-RestMethod http://127.0.0.1:3001/v1/health/ready
Invoke-RestMethod http://127.0.0.1:3000/api/health/ready
```

Reconectar depois para continuar a conversa. Esse método demonstra operação sem
acesso externo nas condições testadas; não é auditoria de tentativas de telemetria
do SDK nem prova universal de ausência de tráfego. Registrar exceções reais.

## Encerramento

Atualizar a matriz e os relatórios somente após conferir os artefatos e as ações
humanas acima. `demo:check` mantém os gates manuais pendentes; não há atalho por
simulador para declará-los aprovados. A release local preparada permanece candidata.
