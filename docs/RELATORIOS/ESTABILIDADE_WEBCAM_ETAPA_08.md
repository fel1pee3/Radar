# Estabilidade e observações da webcam — etapa 08

23/10/2026. **PARCIAL**. Complemento do [relatório 08](ETAPA_08.md).

## O que foi observado

O fundador informou retrospectivamente que ficou principalmente sentado em uma
cadeira, com os pés apoiados em um banco, saiu do quadro por menos de um minuto
e não se deitou no chão. Relatou baixa fluidez, desaparecimento/reaparecimento de
pontos ou segmentos, desalinhamento com o corpo e piora em movimentos rápidos.
Não forneceu horários precisos dessas ocorrências. Não informou um novo caso
específico de pose em móvel nesta sessão; não presumir ausência desse problema.

A execução real durou 1665,64 s, com 7906 análises e nenhum evento. É um relato
de atividade confundidora sem emissão nesse intervalo, não uma prova de recall
ou aprovação dos 30 min. Não converter a ausência de alertas em eficácia geral.
Sem gravação de vídeo, não é possível rever o movimento original nem localizar
exatamente cada oscilação. A precisão da pose nesta cena não foi medida por
anotações de pontos. Não atribuir a falha à câmera sem comparação controlada.

## Fluidez e qualidade são problemas diferentes

A prévia LIVE atual chama `show` somente depois de cada inferência, no mesmo
laço limitado a 5 análises/s. Foram medidos 4,75 análises/s nesta sessão. O
adaptador adquiriu 49.646 frames, mas isso não significa que todos foram exibidos
ou analisados; o slot mais recente substitui frames intermediários de propósito.
Resolução utilizada 640 × 480. Modelo RTMO tem entrada 640 × 640 com letterbox.
Não houve comparação de resoluções; aumentar resolução não é correção comprovada.

RTMO neste adaptador estima cada frame sem rastreamento temporal de articulações.
Movimento rápido, sobreposição/oclusão de pernas e score abaixo do limiar podem
produzir pontos instáveis. A prévia só desenha pontos atuais utilizáveis; omite
segmentos quando uma extremidade é inelegível. O relato não permite distinguir
quanto foi movimento real, oscilação do estimador ou rejeição por qualidade.
Ponto desenhado com score suficiente também pode estar anatomicamente errado.

Não foi aplicado preenchimento de pontos ausentes, retenção de esqueleto antigo,
suavização do motor ou redução de gates para aparentar estabilidade. A correção
abaixo trata I/O e diagnóstico; **não corrige o esqueleto ou a cadência da prévia**.
Uma melhoria visual futura precisa medir atraso, alinhamento e desaparecimento
em vídeos conhecidos, mantendo a observação bruta no detector e declarando
qualquer desenho estimado/interpolado. Não ampliar a alegação de segurança.

Auditoria adicional, somente leitura, das observações já salvas dos dois clipes
de cadeira: no primeiro, os oito pontos essenciais eram desenháveis em 45/47
amostras Full e 47/47 RTMO; no segundo, 32/32 em ambos. Apesar disso, o fundador
já havia identificado desalinhamento do Full junto à cadeira no segundo clipe.
Isso mostra por que disponibilidade/score dos pontos, isoladamente, não aprova
alinhamento anatômico. Não mede jitter nem explica os frames da webcam que não
foram gravados. Resumo privado: `.local/etapa08/chair-point-availability.json`.
Sem nova inferência, mudança de limiar ou uso desses clipes como avaliação nova.

## Investigação sem webcam

O erro antigo foi `PROCESSING_ERROR`, sem tipo ou traceback. A causa histórica
continua indeterminada. No caminho periódico de status havia um `Path.replace`
sem tratamento de concorrência com o leitor do monitor PowerShell.

Reprodução real em diretório temporário do Windows: abrir `status.json` para
leitura e tentar substituí-lo gerou `PermissionError`, errno 13, winerror 5;
após fechar o leitor a substituição passou. Nesta máquina, permitir
FILE_SHARE_DELETE no leitor também não garantiu substituição do destino aberto
por `Path.replace`; a liberação do handle foi necessária. Testes cobrem ambas
as formas de compartilhamento. Essa reprodução prova um defeito possível do
código anterior, **não identifica retrospectivamente a exceção da sessão**.

A documentação da [Microsoft sobre compartilhamento de arquivos](https://learn.microsoft.com/windows/win32/api/fileapi/nf-fileapi-createfilea)
explica a relação entre handles e permissões de exclusão/rename; o
[rastreador oficial do Python](https://bugs.python.org/issue46003) registra as
limitações de `os.replace` em destinos abertos no Windows. O resultado local,
incluindo limites de FILE_SHARE_DELETE, foi verificado diretamente.

## Alteração e verificações

- `local_status.py`: publica JSON completo por temporário exclusivo; tenta de
  novo apenas em PermissionError Windows 5/32, no máximo cinco tentativas com
  quatro esperas de 20 ms. Falha permanente retorna LOCAL_STATUS_WRITE_ERROR.
  Não ignora indefinidamente erro de permissão/espaço ou mantém captura com
  diagnóstico aparentemente atualizado. Reporta a quantidade de retries usados.
- `live.py`: inclui tipo, códigos do SO e localização no código para falhas
  inesperadas/causa de I/O. Não registra texto bruto da exceção, caminhos,
  variáveis locais, token ou frame. Erro genérico/I/O de status continua ERROR,
  mas não recebe rótulo CAPTURE_ERROR sem evidência de falha da câmera.
- `observe.ps1`: leitura com handle curto, descarte explícito e compartilhamento
  ReadWrite/Delete; fecha o handle antes de interpretar JSON. Isso complementa
  as tentativas no escritor, não as substitui.
- Regressões: leitores reais Windows, disputa transitória, falha persistente,
  publicação sem JSON parcial, diagnóstico sem segredo e erro integrado do laço
  LIVE por adaptador sintético. Não contam como captura física nova.

Comandos executados nesta investigação:

```powershell
. ./scripts/activate.ps1
uv run --project services/edge --frozen pytest services/edge/tests/test_local_status.py services/edge/tests/test_live_health.py -q
$env:RADAR_TEST_GUI = '1'
uv run --project services/edge --frozen pytest services/edge/tests -q
pnpm.cmd lint:edge
git diff --check
```

Resultado: 14 testes direcionados passaram; suíte Python completa 289 passou,
sem skip nesta máquina. Ruff/lint e formato passaram; sintaxe de observe.ps1
validada com o parser PowerShell. `git diff --check` passou, com avisos de
normalização CRLF/LF existentes. A primeira versão de teste assumia que
FILE_SHARE_DELETE bastava; falhou na prova real e foi corrigida para testar a
semântica efetivamente observada, sem remover a reprodução do bloqueio.

Teste concorrente com PowerShell real também revelou que interpretar o JSON
antes de fechar o handle podia exceder as tentativas de 80 ms. Corrigida a ordem
para fechar o arquivo antes da interpretação: o ensaio passou com 1000 leituras
de JSON completo e 2906 publicações, 18 retries recuperados, em 16,27 s. Sem
câmera ou acesso ao banco. Comando real:
`uv run --project services/edge --frozen python .local/etapa08/stress-status.py`.
Resumo em `.local/etapa08/status-stress-latest.json`; falha inicial preservada
em `status-stress-a54b4189-cee2-4995-807a-6da083de3c5a`. O primeiro ensaio
mostrou que só adicionar compartilhamento/retries não bastava para o leitor;
não foi descartado como se a primeira correção tivesse passado.

Verificação preliminar `pnpm.cmd demo:verify`: 14 tarefas passaram, mas o ajuste
final do leitor foi feito durante a rodada. A guarda stable-source corretamente
recusou aprovação (exit 1); metadados preservados em
`.local/etapa08/engineering-status-reader-adjustment-<id>.json`.

Nova execução completa depois de fixar o código: `pnpm.cmd demo:verify` exit 0,
14 tarefas aprovadas, 289 Python sem skip, 155 API, 100 contratos TS e Python
(os Python incluídos nos 289), 20 E2E, quatro testes do simulador; frozen,
lint/tipos/build/imports, backup/restore e instalação limpa aprovados em
recursos exclusivos. Banco/volume da demonstração preservados. Evidência em
`.local/etapa08/engineering.json`, hash de 173 arquivos
`dbc52bbd34ff7d64f73db55f7aadc5d70ccd50c6306b160f2c11159f4383021b`.
`pnpm.cmd demo:check --engineering` exit 0 e `pnpm.cmd demo:check` exit 2 pelos
gates manuais pendentes; releaseReady false. A revisão RTMO anterior foi preservada
em `.local/etapa08/engineering-before-status-fix-<id>.json`. Não somar contagens
de rodadas nem atribuir a evidência antiga ao código alterado.

## Pendências

Nenhuma webcam foi reaberta nesta investigação. A sessão de 27 min permanece
não aprovada; os testes de I/O não completam os 30 min físicos e não comprovam
que toda causa do encerramento foi removida. Antes de qualquer nova solicitação
física, explicar o que mudou e combinar a participação do fundador. Permanecem
os limites de pose, as perdas conhecidas, avaliação independente, offline e
apresentação final. A revisão humana do incidente positivo foi posteriormente
confirmada pelo histórico do painel fornecido pelo fundador (versão 4);
o gate LIVE→incidente→revisão está atendido naquele ensaio curto.
