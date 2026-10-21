# Validação manual — etapa 03

Este roteiro demonstra interface, persistência e revisão com um evento artificial.
Não abre câmera, não executa modelo e não envia mensagem a um contato real.

## Preparar e iniciar

Na raiz, PowerShell:

```powershell
. ./scripts/activate.ps1
pnpm.cmd install --frozen-lockfile
pnpm.cmd setup:env
pnpm.cmd infra:up
pnpm.cmd db:generate
pnpm.cmd db:migrate
```

O proprietário já existente continua válido. Em uma instalação nova, execute
`pnpm.cmd setup:owner` para escolher suas credenciais localmente. O PostgreSQL
do projeto fica em 15432; não use o servidor preexistente de 5432 nem reset de banco.

Em um terminal:

```powershell
. ./scripts/activate.ps1
pnpm.cmd dev:api
```

Em outro:

```powershell
. ./scripts/activate.ps1
pnpm.cmd dev:web
```

Abra [o painel local](http://127.0.0.1:3000). Use `127.0.0.1` também na API;
não alterne com localhost. Entre com o proprietário. A tela consulta `/auth/me`
e usa o cookie HttpOnly pelo proxy; nenhuma senha/token de sessão vai ao localStorage.

## Preparar uma câmera exclusiva da simulação

1. Abra **Configuração**. Consulte o local existente ou crie um local com nome
   e fuso IANA, por exemplo America/Sao_Paulo.
2. Crie uma câmera com nome **Demonstração simulada**, tipo **Arquivo (FILE)**,
   vinculada ao local. Esse cadastro é lógico e não inicia captura.
3. Em **Fontes**, confira a indicação **Sem heartbeat**. Ela não deve aparecer
   como uma câmera física conectada.
4. Volte à configuração. Na câmera exclusiva, selecione **Emitir/rotacionar
   credencial**, leia o aviso e confirme. Isso revoga tokens anteriores dessa câmera.
5. Use **Copiar token** e transfira o segredo à configuração privada abaixo.
   O token não poderá ser consultado novamente. Não publique nem envie pelo chat.
   Após guardá-lo, selecione **Ocultei e guardei o token**.

Não use uma câmera de outro worker para este teste: a rotação pode revogar o
acesso dele. Credenciais já emitidas podem ser revogadas pela lista de metadados,
inclusive após recarregar a página. Essa lista não contém token ou hash.

## Configuração privada do simulador

No terceiro terminal, ainda na raiz:

```powershell
. ./scripts/activate.ps1
New-Item -ItemType Directory -Force .local | Out-Null
if (-not (Test-Path -LiteralPath .local/demo.json)) {
    Copy-Item -LiteralPath scripts/demo/config.example.json -Destination .local/demo.json
}
$radarDemo = Get-Content -LiteralPath .local/demo.json -Raw | ConvertFrom-Json
$radarDemo.cameraId = Read-Host 'UUID da camera exclusiva de demonstracao'
$radarPrivateToken = Read-Host 'Token de worker exibido no painel' -AsSecureString
$radarTokenPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($radarPrivateToken)
try {
    $radarDemo.deviceToken = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($radarTokenPointer)
    $radarDemo | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath .local/demo.json -Encoding UTF8
} finally {
    $radarDemo.deviceToken = $null
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($radarTokenPointer)
    $radarPrivateToken.Dispose()
}
$radarDemo = $null
```

O arquivo privado fica ignorado pelo Git. Ele precisa conter
`purpose: RADAR_SIMULATED_DEMO`, a URL local da API, o UUID e o bearer da câmera
exclusiva. O exemplo tem duração de 60 s e dez reenvios automáticos. O simulador
aceita configuração UTF-8 com ou sem BOM, inclusive a produzida pelo PowerShell 5.1.
Nunca copie o arquivo privado para o exemplo versionado.

## Apresentação do fluxo

No terminal de simulação:

```powershell
pnpm.cmd demo:simulate
```

Mantenha `dev:api` ativo antes de iniciar: ele já compila os contratos necessários.
O simulador não recompila esses arquivos, para não provocar reinício automático
da API durante o envio. Falhas de conexão e HTTP 502/503/504 têm até quatro
tentativas por requisição, sempre com o mesmo corpo e IDs. Credencial recusada
não é repetida automaticamente.

Ou com um arquivo privado alternativo dentro de `.local`:

```powershell
pnpm.cmd demo:simulate --config .local/demo.json
```

1. Mostre **MVP de demonstração** e explique que o modo **Simulado** comprova o
   fluxo de software. Não é detecção por IA.
2. Em **Fontes**, observe o heartbeat do simulador com a indicação de que não
   comprova câmera física. O simulador envia heartbeat a cada cinco segundos.
3. Em **Incidentes**, filtre por modo Simulado e câmera de demonstração. Abra o
   único registro criado por essa execução. Dez reenvios mantêm o mesmo incidente.
4. Mostre sinais, pose sintética, horários/fuso, classe Teste e versões. A pose
   está identificada como evidência simulada; não existe imagem de câmera.
5. Escolha **Reconhecimento**, depois **Revisão humana**, informe sua avaliação
   de teste e uma nota opcional. Registre as ações.
6. Escolha **Início de atendimento registrado**. Depois **Encerramento**, com
   revisão diferente de Não revisado e desfecho **Teste concluído**.
7. Recarregue. Estado, revisão, desfecho e histórico devem permanecer. Uma nota
   adicional é permitida no incidente final sem reabri-lo.
8. Abra **Avisos locais**: confira um aviso no canal SIMULATED, com modo e classe
   Teste. Ele não representa SMS, WhatsApp ou ajuda prestada.
9. Enquanto o simulador estiver ativo, digite `r` e Enter para reenviar o mesmo
   envelope. Digite `q` e Enter para encerrar normalmente; o prazo configurado
   também encerra a execução. O último heartbeat será ENDED e a fonte aparecerá
   como encerrada. Encerramento abrupto pode impedir esse envio e leva à indicação
   de informação desatualizada/offline após a janela do lease.

Para uma execução curta sem interação:

```powershell
pnpm.cmd demo:simulate --config .local/demo.json --once
```

Cada execução nova gera um episódio novo. Use `r` dentro da mesma execução para
demonstrar deduplicação do mesmo evento; iniciar o comando novamente cria outro
incidente de teste intencionalmente. Apenas IDs e resultados seguros aparecem no terminal.

Uma execução normal mostra uma resposta 201, dez respostas 200 com
`duplicate: true` e termina com `captureState: ENDED`, sem erro de comando.
Se houver perda da primeira resposta após a gravação, a repetição pode retornar
200 diretamente: o incidente continua único. `API_UNAVAILABLE` indica que as
quatro tentativas falharam; confira o terminal da API. Um incidente já visível
permanece salvo mesmo que o simulador falhe depois. `ENDED_NOT_CONFIRMED` significa
que o encerramento não pôde ser confirmado; não deve ser apresentado como término
normal. Não inicie outro comando apenas para continuar a revisão desse incidente.

## Conflitos, falhas e permissões

- Para demonstrar conflito, abra o mesmo incidente não final em duas abas.
  Uma mudança concorrente pode resultar em 409. A tela recarrega e exige que a
  pessoa confira o estado e prepare uma nova tentativa; não troca a versão e
  reenvia a ação automaticamente. O texto em edição é mantido.
- Se uma gravação não tiver resposta conclusiva, use **Reenviar mesma tentativa**.
  O actionId e o corpo ficam preservados em memória; a API resolve a repetição.
  Não recarregue/feche essa aba antes de resolver a tentativa.
- API indisponível preserva os dados anteriores identificados como desatualizados.
  Uma falha de consulta não equivale a lista vazia nem a fonte saudável.
- Ao expirar a sessão, os dados ficam ocultos. Login com a mesma conta recupera
  o rascunho ainda em memória; outra conta ou logout descarta esse estado local.
  Rascunhos não são salvos em armazenamento persistente do navegador.
- A aba oculta pausa consultas e a volta retoma as atualizações. Filtros ficam
  na URL; polling não limpa o formulário de revisão.
- Um OPERATOR pode consultar/revisar, mas não recebe configuração de OWNER nem
  pode executá-la pela API. Crie operador com `pnpm.cmd user:create-operator` se
  desejar repetir essa parte manualmente.

Não pare o banco da demonstração ou o PostgreSQL de 5432 para testar falhas.
A suíte abaixo faz essa verificação apenas em recursos próprios.

## Testes automatizados

```powershell
. ./scripts/activate.ps1
pnpm.cmd test:e2e:install
pnpm.cmd test:e2e
pnpm.cmd test:demo
pnpm.cmd test:api
pnpm.cmd test:contracts
pnpm.cmd lint
pnpm.cmd typecheck
pnpm.cmd build
```

Playwright instala Chromium localmente, sem abrir webcam. A suíte cria outro
PostgreSQL com volume descartável, API e web em portas efêmeras. O build usa
`.next-e2e`, preservando a saída normal da web e os processos da demonstração.
Fotos de tela e diagnósticos sintéticos ficam em `.local/etapa03/results`, fora
do Git. Não compartilhe esses arquivos sem revisão: uma falha durante emissão
de token pode deixar um segredo sintético de teste no diagnóstico local.

Consulte resultados e limites no [relatório 03](RELATORIOS/ETAPA_03.md).
