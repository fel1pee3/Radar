# Operação, backup e restore locais

[Roteiro 08](VALIDACAO_MANUAL_ETAPA_08.md) · [Política de dados](06_SEGURANCA_E_DADOS.md).
Windows 11 x64, Node 24.22.1, pnpm 10.34.7, Python 3.12.15, uv 0.13.4,
Docker Desktop/Engine 29.1.3 e PostgreSQL 17.11. Comunicação somente em loopback.

## Iniciar, parar e retomar

Ative `. ./scripts/activate.ps1` em cada terminal. `pnpm.cmd infra:up` inicia o
banco na porta 15432, `pnpm.cmd db:migrate` aplica migrações aditivas. API e web:
`pnpm.cmd dev:api` e `pnpm.cmd dev:web`, separadamente. No navegador use
http://127.0.0.1:3000. Não misturar localhost e 127.0.0.1.

Após build, a alternativa é `pnpm.cmd --filter @radar/api start` e
`pnpm.cmd --filter @radar/web start`, também em terminais separados. Não manter
dev e start concorrendo pelas portas. Parar primeiro o worker com control stop
ou Q/Esc, esperar término, e depois Ctrl+C nos terminais web/API.
`pnpm.cmd infra:down` preserva volume; jamais usar `down -v` na bancada.
Retomar repetindo infra:up e os comandos dos processos. Arquivo operacional retoma
checkpoint/EOF; não começa novo incidente só porque o processo reiniciou.

## Preparação limpa verificada

```powershell
. ./scripts/activate.ps1
pnpm.cmd demo:install-check
```

Cria `.local/clean08-<id>` com snapshot dos arquivos versionáveis atuais, sem .env,
.local anterior, node_modules, .venv, credenciais, vídeos ou modelo. Instala pelos
dois locks, cria banco/volume/portas exclusivos, configura variáveis novas, compila,
migra, cria OWNER sintético e testa login pelo proxy. Obtém o Full oficial de novo,
verifica SHA e processa vídeo de pixels sintéticos com modelo real. Esse material
comprova infraestrutura, não percepção. Para percepção são necessários seus vídeos
autorizados e calibrações próprias, que não acompanham a distribuição.

Pré-requisitos externos explícitos: binários Node/pnpm/uv exatos no PATH ativado,
Docker com imagem postgres:17.11 disponível, internet para obter artefatos e Python
3.12.15 gerenciado pelo uv. Caches de pacotes podem ser reaproveitados; as árvores de
dependências/venv são novas. A cópia não inclui as ferramentas portáteis da bancada.
Logs e cópia são mantidos para inspeção; processos e volume de teste são removidos.
`clean-install.json` registra HEAD, código alterado e hash do conteúdo avaliado.
Não é teste de instalação num segundo computador nem de funcionamento offline.

## Backup PostgreSQL consistente

O padrão copia o **banco**, não imagens, modelos, logs, ferramentas ou vídeos.
O dump contém hashes de autenticação e poses ainda retidas: continua sensível e
não cifrado. Mantê-lo em `.local/backups`, com acesso restrito no Windows, fora
do Git e de sincronização pública. Prazo sete dias; remoção é manual. O manifesto
registra vencimento, e o restore recusa cópia vencida ou hash divergente.

Pare worker, web e API conforme acima; mantenha o PostgreSQL ligado. Então:

```powershell
. ./scripts/activate.ps1
pnpm.cmd backup:create --stopped
```

`--stopped` declara a parada coordenada; o script também recusa conexões de clientes
ativas no banco. Não detecta aplicações futuras que ainda não se conectaram: não
reiniciar processos durante a cópia. PostgreSQL usa pg_dump custom consistente;
não copia arquivos físicos do volume. O script só aceita containers Radar e
PostgreSQL 17.11, usa identidade/credenciais internamente sem imprimi-las e grava
`database.dump`/`backup.json` em diretório novo. Na 08 a cópia foi testada em dados
sintéticos exclusivos; **nenhum dump da conta pessoal foi criado**.

## Configuração, calibração e fila

Segredos de `.env` e credenciais do worker **não são copiados automaticamente**.
No restore de ensaio usam-se novos segredos/banco e credencial explicitamente
emitida no ambiente isolado. Para preservar configurações operacionais sob sua
responsabilidade, com processos parados, copie apenas arquivos conhecidos para
o diretório privado retornado pelo backup, mantendo o mesmo prazo de sete dias.
Não copiar diretórios inteiros nem mídia por conveniência. Exemplo de arquivos
sem token embutido (confira sua própria configuração):

```powershell
# Substitua <id> pelo diretório realmente criado; não execute literalmente.
Copy-Item -LiteralPath .local/edge-webcam.yaml -Destination .local/backups/<id>/edge-webcam.yaml
Copy-Item -LiteralPath .local/calibration-webcam.json -Destination .local/backups/<id>/calibration-webcam.json
uv run --project services/edge --frozen radar-edge backup-outbox --config .local/edge-webcam.yaml --output .local/backups/<id>/outbox.sqlite
```

Backup da fila usa SQLite backup API com locks de câmera/outbox, preserva evento
pendente e checkpoint ACTIVE, elimina JPEG da cópia e consolida WAL antes de
fechar. Não altera a fila original. Metadados pendentes continuam imutáveis,
inclusive sua evidência corporal, até resolução: exceção operacional documentada
na política de dados. Não declara apagamento forense. Havendo token/URL com senha
em configuração, essa cópia passa a exigir a mesma proteção de segredo.

## Restore sempre isolado

Compile a API e restaure **somente um backup local confiável**:

```powershell
pnpm.cmd --filter @radar/api build
pnpm.cmd backup:restore --backup .local/backups/<id>
```

Não há argumento para sobrescrever banco original. Cria `radar-restore-<uuid>`,
volume novo e porta loopback efêmera. Antes de abrir qualquer HTTP:

- revoga todas as sessões e credenciais de device restauradas;
- desabilita autorização de snapshot e expectativa de câmera ativa, limpa heartbeat;
- marca imagem ausente EXPIRED (preserva DELETED), zera referências e bytes;
- redige pose/recibo com mais de sete dias usando horários originais;
- audita RESTORE_SANITIZED e aplica a rotina completa de retenção no banco novo.

O ambiente não inicia API/web/worker automaticamente. A URL e o caminho privado
ficam em `.local/restores/<uuid>/restore-private.json`, sem aparecer na saída.
Antes de acesso intencional, migrar com esse DATABASE_URL por ambiente privado,
iniciar API em porta diferente com LOCAL_DATA_DIR isolado e WEB_ORIGIN apropriada.
Não apontar a configuração web/API original para ele. O teste reproduzível abaixo
encapsula isso sem pedir senha/token reais:

```powershell
pnpm.cmd test:backup
```

Verifica tabelas/relações, migrações, readiness, login, rejeição de sessão/bearer
antigos, 410 para imagem, redação de pose e deduplicação com nova credencial emitida
intencionalmente. Remove somente containers/volumes que o teste criou.

Para restaurar uma cópia da outbox, sempre em destino novo:

```powershell
uv run --project services/edge --frozen radar-edge restore-outbox --input .local/backups/<id>/outbox.sqlite --output .local/restores/<uuid>/outbox.sqlite
```

Não aponta a uma API nem entrega eventos. Em configuração restaurada, mantenha
`source.authorized: false` e `events.delivery.enabled: false`, retire credentialFile
e ajuste todos os caminhos antes de rodar. Só reabilitar fonte/entrega após conferir
hashes, sessão, calibração e emitir nova credencial no ambiente desejado. Não usar
o bearer original para “facilitar” o ensaio. Não copiar WAL/SHM avulsos de fila ativa.

O backup não é cifrado, não salva papéis globais do cluster, não testa perda física
do disco e não apaga cópias externas. O teste usa banco sintético, não restauração
de dados pessoais. Fonte primária: [pg_dump 17](https://www.postgresql.org/docs/17/app-pgdump.html),
[pg_restore 17](https://www.postgresql.org/docs/17/app-pgrestore.html) e
[SQLite backup Python 3.12](https://docs.python.org/3.12/library/sqlite3.html#sqlite3.Connection.backup).

## Problemas efetivamente encontrados

| Sintoma | Ação |
| --- | --- |
| pnpm.cmd não reconhecido | Executar activate.ps1 nesse terminal |
| Banco não sobe/porta ocupada | Abrir Docker Desktop; manter projeto 15432 e PostgreSQL existente 5432 |
| Tela preta na webcam | Conferir tampa física, luz e outro programa usando a câmera |
| Calibração parece congelada | Imagem parada é intencional; marcar piso e Enter, ou Q para sair |
| API reinicia durante comando | Evitar recompilar contratos/builds durante a apresentação; usar build/start |
| Next falha em useContext no build limpo | NODE_ENV do build web deve ser production; separado do ambiente HTTP local da API |
| Restore falha logo após criar container | Esperar PostgreSQL responder em TCP, não somente o socket temporário de inicialização |
| JPEG removido da tabela mas bytes ainda na cópia SQLite | Consolidar WAL/fechar conexão; rotina entregue faz isso, testado com sentinela sintética |
| demo:check retorna 2 | Engenharia passou, mas gates físicos/manuais continuam pendentes; ler matriz |
| Backup recusa clientes | Parar workers/API/web antes; não matar conexões do fundador automaticamente |
