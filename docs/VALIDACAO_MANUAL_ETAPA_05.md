# Validação manual — etapa 05

Objetivo: arquivo → modelo real → motor temporal → SQLite → API → incidente REPLAY.
**Situação atual: CONCLUÍDA para a bancada.** O Full produziu um evento real em
`piso-f-07` aos 6000 ms e a API confirmou um incidente REPLAY/TEST, conferido pelo
fundador. Retomada e reenvio mantiveram o mesmo incidente. Prévia, sinais e
versões foram conferidos. Os ensaios negativos com Lite e os limites restantes
foram preservados no [relatório 05](RELATORIOS/ETAPA_05.md) e na
[investigação](RELATORIOS/INVESTIGACAO_ETAPA_05.md). Não é necessário provocar queda,
reenviar vídeo ou remarcar o piso para reproduzir a demonstração atual.

## 1. Iniciar dependências e aplicação

Na raiz, PowerShell:

```powershell
. ./scripts/activate.ps1
pnpm.cmd install --frozen-lockfile
uv sync --project services/edge --frozen
pnpm.cmd setup:env
pnpm.cmd infra:up
pnpm.cmd infra:status
```

Preserve o PostgreSQL externo em 5432. O projeto usa 15432; não use down -v/reset.
Não repita criação de proprietário ou rotação de token se já existem.

Em outro terminal, também na raiz:

```powershell
. ./scripts/activate.ps1
pnpm.cmd dev:api
```

Em outro terminal:

```powershell
. ./scripts/activate.ps1
pnpm.cmd dev:web
```

Abra `http://127.0.0.1:3000` e entre com o proprietário já cadastrado. Selecione
câmera lógica FILE. O painel não inicia câmera física nem processamento.

## 2. Demonstração validada com Full

Nesta máquina a configuração `.local/edge-piso-f-07-full.yaml` já referencia
o vídeo autorizado, a calibração manual correta e a credencial existente. Mantém
os mesmos gates floor-v0.1, num_poses=2, evidência skeleton e outbox própria.
Para rever localmente e conferir a confirmação de entrega:

```powershell
. ./scripts/activate.ps1
uv run --project services/edge --frozen radar-edge model-fetch --variant full
uv run --project services/edge --frozen radar-edge doctor --config .local/edge-piso-f-07-full.yaml
uv run --project services/edge --frozen radar-edge run --config .local/edge-piso-f-07-full.yaml --poses-only --preview-paused --replay-speed 0.5
uv run --project services/edge --frozen radar-edge outbox-status --config .local/edge-piso-f-07-full.yaml
```

A janela começa pausada e aparece acima das demais até iniciar. Clique nela e
pressione **Espaço**; Espaço também pausa/retoma, Q/Esc encerra. Pausa não muda o
tempo da cena nem faz o restante acelerar. Verde exige presença/visibilidade
suficientes daquele ponto atual; não comprova por si só pessoa no chão.
Esse comando poses-only não cria eventos nem altera o episódio existente.

Outbox-status deve mostrar **1 DELIVERED**, sem erro, com incidente
`6cfd7d88-ae34-4b48-ad5a-d592cbd020a9`. Abra
`http://127.0.0.1:3000/incidentes/6cfd7d88-ae34-4b48-ad5a-d592cbd020a9`.
Confira Reprodução/Teste, Possível pessoa no chão, offset **6000 ms**, duração
**2176 ms**, modelo `pose-landmarker-full-float16-v1`, política `floor-v0.1`,
calibração `74bfeb97-6767-4cd4-9eb7-531d17d54778-v1` e pose.
Essa conferência já foi realizada pelo fundador.

Para comprovar a retomada, execute o run normal:

```powershell
uv run --project services/edge --frozen radar-edge run --config .local/edge-piso-f-07-full.yaml --no-preview
uv run --project services/edge --frozen radar-edge outbox-status --config .local/edge-piso-f-07-full.yaml
uv run --project services/edge --frozen radar-edge evaluate --manifest .local/evaluation-full.json
uv run --project services/edge --frozen radar-edge evaluate --manifest .local/evaluation-full-positive.json --replay-speed 2
```

O arquivo já concluído retoma EOF: zero novas análises/eventos, mesmo runId e um
item entregue. Não use reset para verificar idempotência. Evaluate faz reanálise
intencional em outras outboxes, sem HTTP; seis arquivos terminam com um evento
somente no positivo. Replay 2× reproduz rótulo/offset/digest. Os manifestos têm
papel CALIBRATION e anotações incompletas; percentuais de eficácia seguem null.

Em outra máquina, os arquivos privados não vêm pelo Git. Configure fonte
autorizada, câmera/credencial, piso e outbox próprios seguindo o exemplo. Full
exige os dois campos abaixo; não aponte o Full para o arquivo de pesos Lite:

```yaml
model:
  variant: full
  path: .local/models/pose_landmarker_full.task
```

Trocar o modelo muda o fingerprint: em outbox já usada requer reset técnico
explícito com worker parado ou outra outbox. O comando não troca modelos sozinho.
Um arquivo de outra perspectiva pode continuar sem evento; não há garantia de
detecção geral. Lite e seus resultados anteriores permanecem reproduzíveis.

## 3. Configuração anterior com Lite

Nesta máquina já existe `.local/edge-events.yaml`: fonte/calibração da 04,
events.enabled=true, SQLite em `.local/etapa05/vision.sqlite`, evidence skeleton,
delivery habilitada com referência ao arquivo privado de credencial existente.
`.local/edge.yaml` e `.local/calibration.json` foram preservados.

Em outra máquina, copie `services/edge/edge.example.yaml` apenas se o arquivo
privado ainda não existir; configure fonte autorizada, câmera e calibração reais,
habilite events e delivery. `credentialFile` deve apontar para JSON privado com
`apiUrl`, `cameraId`, `deviceToken`. Alternativa: EDGE_API_URL/EDGE_DEVICE_TOKEN no
ambiente local; não passe token em argumento nem no chat. API URL deve ser loopback
com sufixo /v1. Sem token, deixe delivery.enabled=false para persistir localmente.

```powershell
. ./scripts/activate.ps1
uv run --project services/edge --frozen radar-edge doctor --config .local/edge-events.yaml
uv run --project services/edge --frozen radar-edge run --config .local/edge-events.yaml --no-preview
uv run --project services/edge --frozen radar-edge outbox-status --config .local/edge-events.yaml
```

Se o arquivo já terminou, run retoma EOF com zero novas observações. Isso é
proteção contra repetição, não falha. Para assistir/extrair poses novamente sem
criar uma nova análise de eventos:

```powershell
uv run --project services/edge --frozen radar-edge run --config .local/edge-events.yaml --poses-only --preview --replay-speed 0.5
```

## 4. Ensaios anteriores e preparação de outra fonte

Os dois arquivos adicionais já têm configurações, calibrações selecionadas pelo
fundador e outboxes separadas: `.local/edge-piso-a.yaml` (lateral) e
`.local/edge-piso-b.yaml` (vista de cima). Ambos foram processados por completo;
run normal retoma EOF. Para reproduzir a avaliação sem modificar suas execuções:

```powershell
uv run --project services/edge --frozen radar-edge evaluate --manifest .local/evaluation-pisos.json
```

Esse diagnóstico mantém annotationsComplete=false: não fornece percentuais de
eficácia. Os gates de qualidade impediram a prova positiva nessas duas cenas.
Para ver pose/ROI localmente sem emitir eventos ou alterar checkpoints:

```powershell
uv run --project services/edge --frozen radar-edge run --config .local/edge-piso-a.yaml --poses-only --preview --replay-speed 0.5
```

Use arquivo autorizado, câmera parada, boa luz, piso e corpo inteiro visíveis.
Uma pessoa já deitada no piso por 5–10 s serve; não grave queda física. Não marque
cama/sofá como piso. Se o enquadramento mudar, faça outra calibração.

O ensaio real mais recente está em `.local/edge-piso-d.yaml`, já calibrado e
processado integralmente. Não é preciso repetir sua marcação: o quadril passou
no gate do piso em 58/58 observações elegíveis. Os limites de ângulo e proporção
são relativos à imagem e falharam para a postura deitada confirmada pelo fundador.
Boa luz/corpo visível não garantem disparo nessa perspectiva. A regra atual
precisa ser avaliada quanto ao enquadramento antes de pedir mais gravações;
qualquer revisão deve ter justificativa e versão próprias, sem ajustar somente
para fazer este arquivo passar. Para rever a pose sem alterar episódios:

```powershell
uv run --project services/edge --frozen radar-edge run --config .local/edge-piso-d.yaml --poses-only --preview --replay-speed 0.5
uv run --project services/edge --frozen radar-edge outbox-status --config .local/edge-piso-d.yaml
```

O resultado esperado deste arquivo com floor-v0.1 é zero eventos; isso registra
a falha observada, sem comprovar detecção correta da pessoa deitada.

Outros dois arquivos da internet, descritos pelo fundador como filmagens reais,
estão em `.local/edge-piso-e-05.yaml` e `.local/edge-piso-f-07.yaml`, com piso
selecionado por ele e outboxes separadas. Terminaram sem evento: 51 análises e
zero candidatas no primeiro; 45 análises e seis candidatas sem continuidade
suficiente no segundo. A origem/licença não foi verificada independentemente.
Use os mesmos comandos de prévia acima, substituindo somente o arquivo de
configuração, para conferir pose/piso sem alterar episódios.
As prévias dos dois foram repetidas; o fundador relatou esqueleto piscando e
sumindo, apesar de reconhecível. Esse resultado insatisfatório está registrado,
sem substituir pontos ausentes por uma pose inventada ou declarar a etapa pronta.

Foi preparada `.local/edge-positive.yaml` para `.local/videos/piso.mp4`, com
calibração separada. Depois de disponibilizar o vídeo, confirme autorização em
source.authorized e o caminho no arquivo privado. Preserve a calibração anterior.

```powershell
notepad .local/edge-positive.yaml
uv run --project services/edge --frozen radar-edge doctor --config .local/edge-positive.yaml
uv run --project services/edge --frozen radar-edge calibrate --config .local/edge-positive.yaml --frame-ms 1000
```

Na janela, marque 3 ou mais vértices contornando o piso utilizável; Enter salva.
Botão direito desfaz, C limpa, Q/Esc cancela. O programa não escolhe piso sozinho.
Esses comandos são para o caminho hipotético preparado antes da investigação;
não foram usados na demonstração Full e não são uma pendência atual. Não use
essa configuração sem disponibilizar/autorizar de fato sua fonte.

Com worker parado, a troca de fonte/calibração na mesma outbox exige reset auditado:

```powershell
uv run --project services/edge --frozen radar-edge reset-episode --config .local/edge-positive.yaml --reason positive_file_validation
uv run --project services/edge --frozen radar-edge run --config .local/edge-positive.yaml --preview --replay-speed 1
uv run --project services/edge --frozen radar-edge outbox-status --config .local/edge-positive.yaml
```

O reset preserva eventos e pendências, encerra apenas o episódio **local** e cria
nova execução intencional. Não fecha incidente humano. Q/Esc interrompe prévia.
Parâmetros estão centralizados em policy.py; mudar parâmetro exige outra versão.
Não os reduza apenas para obter um alerta.

## 5. Conferir incidente e evidência

Há também um ensaio **sintético gerado por IA**, confirmado pelo fundador:
`.local/edge-piso-c-ai.yaml`. Ele gerou um PERSON_ON_FLOOR no offset 6417 ms e o
salvou em SQLite. Delivery está desabilitada: PENDING com zero tentativas é o
estado esperado, sem incidente correspondente no painel. Não conta como prova
em filmagem real; essa demonstração foi realizada depois com Full, na seção 2.

```powershell
uv run --project services/edge --frozen radar-edge outbox-status --config .local/edge-piso-c-ai.yaml
uv run --project services/edge --frozen radar-edge evaluate --manifest .local/evaluation-piso-c-ai.json
```

Evaluate mantém material SYNTHETIC, executa modelo/motor em outbox isolada e não
publica HTTP. A retomada normal do arquivo concluído já foi conferida: mesmo
evento persistido, sem reanalisar a cena nem criar outro episódio.

Após evento real, outbox-status deve mostrar DELIVERED e a confirmação com
incidentId/eventId/deliveryClass TEST. Abra:
`http://127.0.0.1:3000/incidentes`, filtre modo **Reprodução** e a câmera utilizada.
Confira no detalhe:

- REPLAY/Reprodução e Teste; nunca Ao vivo ou aviso urgente.
- PERSON_ON_FLOOR/Possível pessoa no chão, ou POSSIBLE_FALL apenas com trajetória.
- Duração no piso, ângulo, razão corporal, quadril no piso e fração válida.
- Worker edge-temporal-v1, modelo pose-landmarker-lite-float16-v1,
  política floor-v0.1 e ID/versão real da calibração.
- Offset do frame de emissão/evidência. Horários são virtuais do replay,
  não a data original de gravação.
- Skeleton mostra só corpo. EVIDENCE_MODE=none ou events.evidenceMode=none envia
  pose vazia; o painel deve informar ausência de pose, sem desenho inventado.

O painel existente desenha um esquema normalizado; use a prévia local para
conferir alinhamento com o vídeo real. Visibilidade/fração não são probabilidades
de queda ou de necessidade de socorro. Deitar voluntariamente pode disparar.
Esta etapa não produz heartbeat; o estado das Fontes pode continuar mostrando
o último estado anterior/sem comunicação. Isso não comprova webcam ativa.

## 6. Idempotência e retomada

Em outro terminal ativo, tente iniciar o mesmo worker: deve retornar WORKER_LOCKED,
inclusive com outra outbox para a mesma câmera. Não apague arquivo de lock para
forçar concorrência. O teste automatizado já exercita esse bloqueio.

Após encerrar o worker, repita run com a **mesma** configuração e outbox. Deve
retomar checkpoint/runId ou EOF, mantendo eventId/episodeId e sem novo incidente
para o trecho já analisado. A retomada pode decodificar e aquecer o rastreador no
prefixo, mas não decide novamente nele. Rearmamento precisa de 3 s válidos novos.

```powershell
uv run --project services/edge --frozen radar-edge run --config .local/edge-positive.yaml --no-preview
uv run --project services/edge --frozen radar-edge deliver --config .local/edge-positive.yaml
uv run --project services/edge --frozen radar-edge outbox-status --config .local/edge-positive.yaml
```

PENDING usa backoff de 1–60 s (Retry-After numérico pode elevar a 300 s); deliver
respeita a próxima tentativa. Não apague outbox nem mude payload/eventId para
repetir envio. 401/403 suspende entrega. Corrija o arquivo privado da credencial
e então use `deliver --resume-auth`; não rotacione automaticamente. PERMANENT_ERROR
com HTTP_409/410/422 exige investigar conflito/expiração/validação; não entra em
retry infinito. outbox-status exibe códigos e até 100 confirmações recentes.

O teste de timeout **após commit da API** roda em ambiente exclusivo, sem parar
o banco da demonstração:

```powershell
pnpm.cmd test:api
```

## 7. Avaliação por episódios

Há `.local/evaluation.json` preparado com hash do arquivo anterior e
annotationsComplete=false. O comando reprocessa em outbox isolada, sem HTTP e sem
alterar checkpoint principal. A mesma cena em novas avaliações não é uma retomada
operacional. Para material novo, use `services/edge/evaluation.example.json` como
formato: registre hash, autorização, retenção, pseudônimos, papel, origem,
FPS/duração, intervalos-alvo e exclusões. Não envie mídia pelo chat.

```powershell
uv run --project services/edge --frozen radar-edge evaluate --manifest .local/evaluation.json
uv run --project services/edge --frozen radar-edge evaluate --manifest .local/evaluation.json --replay-speed 2
```

Correspondência: mesmo kind, emissão no alvo ou até 2 s após o fim; um acerto por
alvo, extras como duplicações. Targets exigem duração mínima de 2 s. Excluídos e
inconclusivos ficam separados. `null` significa não estimável, inclusive quando
faltam anotações completas; zero eventos não prova eficácia de um vídeo negativo.
Os relatórios são UTF-8 em `.local/evaluation/<id>/evaluation.json`. Redirecionar
stdout com `>` no PowerShell 5.1 cria UTF-16; prefira o reportPath emitido pela CLI.

## 8. Regressões e limites

```powershell
$env:RADAR_TEST_GUI = '1'
uv run --project services/edge --frozen pytest -q
Remove-Item Env:RADAR_TEST_GUI
pnpm.cmd test:contracts
pnpm.cmd test:api
pnpm.cmd lint
pnpm.cmd lint:edge
pnpm.cmd check:edge
uv build --project services/edge
```

Retenção automática não foi implementada na 05: histórico SQLite e mídia
permanecem sob gestão local. Vídeos/modelos/configurações/SQLite não entram no Git.
Ressalva de métricas nativas MediaPipe permanece no inventário; ausência de tráfego
do SDK não foi auditada. Sem webcam/RTSP/snapshot/integração externa nesta etapa.
