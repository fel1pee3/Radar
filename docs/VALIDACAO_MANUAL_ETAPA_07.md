# Validação manual — etapa 07

Execute na raiz do RadarSoftware, em PowerShell. Não é necessário filmar alguém,
recalibrar o chão ou provocar uma queda. A demonstração desta etapa usa somente
um retângulo verde sintético; não comprova percepção ou câmera física.

## 1. Conferir o padrão sem JPEG

```powershell
. ./scripts/activate.ps1
uv run --project services/edge --frozen radar-edge evidence-status --config .local/edge-webcam.yaml
```

Nesta bancada foi verificado `mode: skeleton`, `jpegEnabled: false`,
`snapshotAuthorized: false`, `sourceOpened: false`, `databaseOpened: false`.
O comando só lê a configuração; não abre câmera, arquivo de vídeo ou SQLite.
`EVIDENCE_MODE`, se definido no terminal, tem precedência sobre o YAML.

Teste dos dois modos sem imagem, sem usar a webcam:

```powershell
uv run --project services/edge --frozen pytest services/edge/tests/test_evidence.py -q
```

Os testes proíbem chamar o codificador JPEG em none/skeleton e verificam o SQLite.
`none` omite pontos do envelope e da exportação diagnóstica; `skeleton` permite
somente pontos corporais. Os frames de análise continuam apenas em memória.

## 2. Demonstrar snapshot sintético com isolamento

Abra o Docker Desktop e aguarde o mecanismo iniciar. Depois:

```powershell
. ./scripts/activate.ps1
pnpm.cmd install --frozen-lockfile
uv sync --project services/edge --frozen
pnpm.cmd demo:evidence
```

Esse comando executa automaticamente o fluxo no Chromium de teste. Cria banco,
volume, portas, API, web, usuários e credencial exclusivos; autoriza snapshot
somente na câmera sintética e remove os processos/container próprios ao terminar.
Não usa sua webcam, sua conta nem os incidentes da demonstração principal.
É uma demonstração automatizada, não uma sessão persistente para login manual.
Se faltar o navegador, execute uma vez `pnpm.cmd test:e2e:install` e repita.

Resultado esperado: `1 passed`. A captura de tela da interface com JPEG sintético
fica privada em `.local/etapa07/screenshots/desktop-snapshot.png`. Pode abri-la:

```powershell
Invoke-Item .local/etapa07/screenshots/desktop-snapshot.png
```

## 3. Conferir leitura e permissões

O fluxo anterior abre o detalhe como OWNER, carrega a imagem pelo endpoint
protegido, provoca HTTP 503 e confere a mensagem de indisponibilidade temporária.
Também simula vencimento do prazo com polling fora e confere remoção da imagem
carregada em memória. Depois troca para OPERATOR: pode ler, mas não recebe o botão de excluir.
Não confunde erro de rede com ausência definitiva.

A suíte de API verifica também ausência/expiração/revogação de sessão, bearer de
device em leitura humana, outro tenant/câmera, Origin ausente/externa, JPEG inválido,
metadados EXIF, excesso de bytes/dimensões/pixels e path traversal:

```powershell
pnpm.cmd test:api
```

Ela só aceita seu harness isolado; não execute `test:integration` diretamente
contra o banco da bancada. O relógio dos testes é injetado; não altere o Windows.

## 4. Excluir e conferir auditoria

`demo:evidence` clica em **Excluir imagem**, confere a explicação de que o incidente
não será encerrado e clica em **Confirmar exclusão da imagem**. Verifica o estado
excluído, o desaparecimento da imagem, o registro `SNAPSHOT_DELETED`, HTTP 410 em
reenvio e a possibilidade de reconhecer o incidente depois da exclusão.

Na demonstração principal, imagens continuam desabilitadas e não aparecerão
somente por instalar esta etapa. Reinicie API/web para carregar o código atual:

Terminal 1:

```powershell
. ./scripts/activate.ps1
pnpm.cmd infra:up
pnpm.cmd db:migrate
pnpm.cmd dev:api
```

Terminal 2:

```powershell
. ./scripts/activate.ps1
pnpm.cmd dev:web
```

Abra http://127.0.0.1:3000 com sua conta existente. Em Configuração, cada câmera
mostra sua preferência. Não selecione imagem pontual para filmagem real apenas
para repetir a demonstração sintética. Em incidentes antigos, o estado esperado
é **Imagem desabilitada para este evento**; o esqueleto anterior continua válido.

## 5. Reproduzir retenção e recuperação

```powershell
pnpm.cmd test:api
uv run --project services/edge --frozen pytest services/edge/tests/test_evidence.py -q
```

São verificados: imagem 24 h; pose/recibo detalhado 7 dias; outbox confirmada
7 dias; purga opt-in de incidentes/auditoria 30 dias; recibos mínimos 90 dias;
logs técnicos 7 dias e tamanho; limpeza idempotente; inicialização com job
habilitado; falhas de disco/banco e retomada. O teste Python → API real perde o
ACK da imagem e inicia outro processo para conferir reenvio e remoção local.
Não é necessário esperar dias nem manipular a data do computador.

## 6. Conferir fila local e deduplicação

Com o worker parado, é possível consultar sua fila sem imprimir payload/token:

```powershell
uv run --project services/edge --frozen radar-edge outbox-status --config .local/edge-webcam.yaml
```

`snapshots` lista estado, tentativas, código e quantidade de bytes, sem imagem.
Pendentes de metadados são imutáveis; não apague SQLite para corrigir erro.
O formato SQLite passa de v1 para v2 de forma aditiva ao abrir a outbox, preservando
execução, episódio e eventos. Para imagens, somente ACK válido elimina bytes.

Os comandos seguintes são operacionais e **aplicam a política aos dados reais
configurados**. Não foram executados no banco/outbox do fundador nesta etapa.
Use-os somente quando desejar essa limpeza:

```powershell
pnpm.cmd retention:run
uv run --project services/edge --frozen radar-edge cleanup --config .local/edge-webcam.yaml
```

`retention:run` requer a API compilada (`pnpm.cmd --filter @radar/api build`) e lê
seu `.env` privado. Remove visuais expirados, reconcilia arquivos e aplica a purga
de 30 dias somente aos tenants cujo OWNER a habilitou. `cleanup` remove somente
metadados confirmados antigos, imagens expiradas e diagnósticos conhecidos;
preserva os envelopes pendentes, fonte, modelo, calibração e estado do episódio.

## Ativação consciente da limpeza e do snapshot real

A limpeza automática da API está **desligada por padrão** para não limpar os dados
existentes automaticamente. `RETENTION_JOBS_ENABLED=true` no `.env` privado da API,
seguido de reinício, executa a rotina na inicialização e a cada 60 s. Desligada,
os arquivos não são apagados automaticamente; a leitura de JPEG expirado continua
bloqueada. A rotina explícita acima continua disponível. A preferência de purga de
30 dias é independente e fica desabilitada até confirmação OWNER em Configuração.

Para snapshot real, em uma solicitação futura consciente: o OWNER escolhe imagem
pontual na câmera e confirma autorização; o worker precisa de cópia privada de
configuração com `events.evidenceMode: snapshot` e `events.snapshotAuthorized: true`.
Trocar modo exige outra outbox ou reset explícito do episódio; não sobrescrever
uma configuração/fila validada. Autorização de fonte não equivale à de guardar JPEG.
Esta implementação não habilitou esse uso nos seus vídeos ou webcam.

Limites, cópias de dados e backup em [segurança e retenção](06_SEGURANCA_E_DADOS.md).
