# Validação manual — etapa 06

Execução nativa no Windows, na raiz do repositório. Uma fonte por vez. Preserve
as configurações, calibrações e outboxes dos arquivos da etapa 05.
Este roteiro não significa que todas as ações já foram executadas: consulte o
[relatório](RELATORIOS/ETAPA_06.md) para a evidência e as pendências atuais.

Etapa 06 concluída para bancada em 22/10/2026: fundador confirmou piso, pose no
corpo e estados LIVE/Pausada/retomada/Fonte encerrada. Recuperação e limites têm
testes dedicados. Isso não conclui a validação final do MVP nem comprova evento
LIVE positivo; pose falsa em estante e fluidez ainda precisam de avaliação.

## Preparação e diagnóstico

### Retomar depois de desligar o computador

Abra o Docker Desktop e aguarde o mecanismo iniciar. Abra a pasta RadarSoftware
no VS Code; todos os comandos abaixo partem da raiz. Configurações e dependências
permanecem depois de reiniciar: não refaça proprietário, cadastros, seed ou token.

Terminal 1, banco:

```powershell
. ./scripts/activate.ps1
pnpm.cmd infra:up
pnpm.cmd infra:status
```

Continue quando postgres estiver saudável. No mesmo terminal, inicie a API e
deixe-o aberto:

```powershell
pnpm.cmd dev:api
```

Terminal 2, painel; deixe-o aberto também:

```powershell
. ./scripts/activate.ps1
pnpm.cmd dev:web
```

Abra `http://127.0.0.1:3000` e entre com sua conta existente. Use esse endereço
durante a sessão. API: `http://127.0.0.1:3001/v1/health/live`.

Terminal 3, webcam:

```powershell
. ./scripts/activate.ps1
uv run --project services/edge --frozen radar-edge probe --config .local/edge-webcam.yaml --seconds 60 --preview
```

Abra a tampinha e confira enquadramento/iluminação; Q fecha. Depois siga
**Piso e execução física** abaixo, um comando por vez. Na sessão de 21/10,
calibrate retornou ValueError/CONFIG_OR_ENVIRONMENT_ERROR; causa não identificada.
Em 22/10 o fundador salvou o piso v1 e executou uma sessão contínua com sucesso.
Se a falha reaparecer, pare nessa etapa e informe o erro do terminal. Não execute run com
calibração ausente ou invente pontos para passar.

Terminal 4 será usado nos controles enquanto run estiver ativo: ative
`. ./scripts/activate.ps1` e use pause/resume/reconnect/stop separadamente,
conferindo o painel entre eles. O YAML atual desta bancada encerra run após 600 s
(dez minutos para o teste guiado); o exemplo público mantém 120 s;
se atingir esse tempo antes da verificação, inicie outra sessão depois da primeira
encerrar. Não abra duas capturas ao mesmo tempo.

Na configuração normal final, reconnectAttempts=3 e outbox é
`.local/edge-webcam/outbox-live.sqlite`. YAML/SQLite anteriores dos ensaios foram
preservados. O arquivo de configuração e os comandos continuam com o mesmo nome.

Para encerrar, pare primeiro o worker; depois Ctrl+C nos terminais de web/API.
O banco pode permanecer no Docker. Para pará-lo preservando o volume, use
`pnpm.cmd infra:down`; não acrescente `-v`.

Ative as ferramentas em cada terminal. API e web devem continuar nos terminais
próprios, em `127.0.0.1:3001` e `127.0.0.1:3000`; banco em `15432`.

```powershell
. ./scripts/activate.ps1
uv sync --project services/edge --frozen
```

Para preparar outra máquina, copie o exemplo somente se o destino não existir:

```powershell
if (-not (Test-Path .local/edge-webcam.yaml)) {
    Copy-Item services/edge/webcam.example.yaml .local/edge-webcam.yaml
}
notepad .local/edge-webcam.yaml
```

Preencha o UUID da câmera lógica WEBCAM, selecione um índice explicitamente e
confirme `authorized: true`. O índice 0 desta bancada foi escolhido pelo fundador;
não é garantia de identificar a webcam em outra máquina. DSHOW é o backend
testado; MSMF é opção explícita, sem fallback silencioso ou varredura.

```powershell
uv run --project services/edge --frozen radar-edge probe --config .local/edge-webcam.yaml --seconds 5 --preview
uv run --project services/edge --frozen radar-edge doctor --config .local/edge-webcam.yaml
```

Probe abre/libera o dispositivo e mede aquisição/consumo sem carregar o modelo.
Doctor executa Full em um frame físico; zero poses significa que nenhuma pose
foi encontrada naquele frame, sem comprovar ausência de pessoas. Q/Esc encerra
a prévia. Não há gravação dos frames. Feche outros aplicativos que usem a webcam;
confira tampa física e permissões de câmera para aplicativos desktop no Windows
se a abertura falhar. O driver pode não distinguir ocupado/permissão/índice:
o diagnóstico informa as causas possíveis, sem inventar uma identificação.

## Credencial sem digitação

Em **Configuração**, escolha a câmera WEBCAM pelo ID, emita sua credencial e
mantenha a tela aberta. Não use token de login nem de uma câmera FILE. Nesta
bancada o ID é `5be84234-7b00-4e87-85e8-b0e68f7c2a6d`.

Execute primeiro:

```powershell
powershell -NoProfile -File scripts/setup-worker.ps1 -CameraId 5be84234-7b00-4e87-85e8-b0e68f7c2a6d -FromClipboard
```

Depois clique em **Copiar** no painel. O script aguarda até dois minutos e salva
automaticamente `.local/webcam-device.json`. Não precisa colar no terminal nem
pressionar Enter. `status: ok` confirma somente o salvamento; a autenticação deve
ser conferida na API. O arquivo existente é preservado, nunca sobrescrito
silenciosamente. O modo sem `-FromClipboard` continua com entrada oculta.
Não envie token pelo chat, nem o execute como comando.

No YAML privado, habilite `events.delivery.enabled: true` depois da conferência
da credencial. Revogação mantém itens AUTH_BLOCKED; após atualizar a configuração
privada, use `deliver --resume-auth` explicitamente. Para trocar um arquivo de
credencial existente, use outro `-OutputFile` dentro de `.local` e ajuste
`credentialFile` no YAML; o script preserva o anterior.

## Piso e execução física

Posicione a câmera fixa com chão visível, boa luz e espaço seguro. Não provoque
queda. Mudança de posição exige nova calibração, mesmo mantendo resolução.

Para conferir o enquadramento com vídeo em movimento antes de calibrar, use
somente este comando. Ele mostra a webcam por até 60 segundos, sem inferência,
sem precisar de piso e sem salvar uma calibração:

```powershell
uv run --project services/edge --frozen radar-edge probe --config .local/edge-webcam.yaml --seconds 60 --preview
```

Q/Esc fecha. Aguarde o terminal voltar antes de executar o próximo comando.
A calibração abaixo usa **uma imagem parada**, permitindo clicar com precisão;
isso é esperado, não é a prévia ao vivo. Posicione a câmera antes de abrir essa
janela. Se precisar mudar a posição, cancele com Q e abra a calibração novamente.
Não marque a pessoa ou a parede como piso se o chão estiver fora da imagem.

Execute primeiro a calibração, sozinha:

Se já salvou `.local/calibration-webcam.json` e o notebook/enquadramento não
mudaram, pode reutilizar esse piso e ir diretamente a run. A calibração v1 desta
bancada foi salva e conferida em 22/10; não precisa repeti-la para testar pausa.

```powershell
uv run --project services/edge --frozen radar-edge calibrate --config .local/edge-webcam.yaml --frame-ms 0
```

Na calibração, clique em pelo menos três pontos em ordem contornando somente
o chão; Enter salva. A calibração registra câmera, índice, geometria e versão.
Não reutilize o polígono de `07.mp4`. Depois de salvar com sucesso, execute:

```powershell
uv run --project services/edge --frozen radar-edge run --config .local/edge-webcam.yaml --preview
```

Durante a execução, confira a prévia LIVE,
o piso e as poses. Em `/fontes`, a câmera deve mostrar modo ao vivo e a saúde
derivada dos heartbeats. Sem pose é um motivo de inferência, não diagnóstico de
ambiente vazio. Baixa luz, baixo FPS e congelamento são heurísticas.

## Pausa, retorno e encerramento

Em outro terminal ativado, com o worker ainda em execução:

```powershell
uv run --project services/edge --frozen radar-edge control --config .local/edge-webcam.yaml --action pause
```

Em `/fontes`, confira **Pausada** na câmera de ID começando com `5be84234`.
A prévia fica parada com indicador de pausa, mas a janela continua respondendo.
Só depois execute:

```powershell
uv run --project services/edge --frozen radar-edge control --config .local/edge-webcam.yaml --action resume
```

Confira que a imagem e o recebimento de heartbeat voltaram. O estado pode indicar
degradação se a qualidade estiver insuficiente; observe o motivo. Para testar uma
reabertura deliberada, execute separadamente e confira o retorno:

```powershell
uv run --project services/edge --frozen radar-edge control --config .local/edge-webcam.yaml --action reconnect
```

Para encerrar e conferir **Fonte encerrada**:

```powershell
uv run --project services/edge --frozen radar-edge control --config .local/edge-webcam.yaml --action stop
```

Confira PAUSED no painel antes de retomar. Pausa libera o driver e mantém a posse
local do worker; retomada/reconnect reabrem somente o índice configurado. Os
comandos são solicitações locais, não confirmação de que existe um worker ativo.
Q/Esc ou Ctrl+C também encerram. O exemplo limita o ensaio a 120 segundos;
o YAML privado desta bancada foi ampliado para 600 s no teste guiado.
Ajuste esse limite privado para conseguir observar cada transição.

O estado final ENDED é enviado se a API estiver acessível. Para fim de arquivo,
o painel mostra SOURCE_ENDED. Morte abrupta não consegue enviar estado final:
a ausência de heartbeat torna a fonte OFFLINE após mais de 15 segundos. Não mate
processos por nome; um teste de morte abrupta deve identificar somente o PID do
worker criado para esse ensaio. O filho de captura monitora a morte do pai e sai.

Saúde local fica em `.local/edge-control/<cameraId>-status.json` e o relatório
final em `.local/results/edge/<id>/report.json`. São metadados privados, sem frame
ou token. Não use um arquivo de status antigo como confirmação de worker ativo:
verifique a data de modificação e o recebimento no servidor.

## Falhas de entrega e testes isolados

O teste reproduzível de API indisponível/retorno, restart, ACK perdido, revogação,
erro permanente e relógio usa PostgreSQL/API/credenciais exclusivos:

```powershell
pnpm.cmd test:api
uv run --project services/edge --frozen pytest services/edge/tests/test_webcam.py services/edge/tests/test_live_health.py -q
```

As poses LIVE do harness são fixtures sintéticas de contrato, sem abrir câmera;
não representam detecção ao vivo. O harness encerra sua própria API, emite e
persiste, inicia outro processo Python e restaura a API, conferindo eventId e
payload. Não interrompe API, banco ou credencial do fundador.

Na operação física, se a API cair, a captura continua até o limite local; a fila
e os motivos de falha aparecem localmente. Após restaurar a API, o worker entrega
pendentes; para entrega manual com o worker parado:

```powershell
uv run --project services/edge --frozen radar-edge outbox-status --config .local/edge-webcam.yaml
uv run --project services/edge --frozen radar-edge deliver --config .local/edge-webcam.yaml
```

Não apague SQLite para resolver falha. Pendentes/permanentes nunca são purgados.
Confirmados com mais de sete dias só podem perder seu payload se o episódio já
estiver fechado/resetado; chaves e estado técnico permanecem. Limite padrão de
10.000 itens ou 100 MiB (banco/WAL/SHM, com reserva antes de inferir), timeout HTTP
5 s, backoff 1–30 s com jitter; Retry-After pode alongar até 300 s.

Eventos atrasados conservam horários e recebem DELAYED/CLOCK_UNCERTAIN conforme
a API, sem nova urgência. Replay continua REPLAY/TEST. Evento LIVE positivo por
visão, se não observado, permanece como pendência para a validação final do MVP.
