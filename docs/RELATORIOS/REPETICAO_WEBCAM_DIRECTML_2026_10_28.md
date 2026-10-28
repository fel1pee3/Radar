# Repetição do teste curto DirectML — 28/10/2026

## Problema observado

O fundador executou o teste físico de 60 s e pediu outra tentativa, considerando
a primeira inadequada. Foi encontrado um relatório LIVE com status ok,
captureState ENDED e erro nulo na sessão
`90c91667-7596-4871-aaf9-f8f3b446d71f`, sob `physical-prepared/results/`.
Isso confirma encerramento técnico; não aprova cena, pose, desempenho ou detecção.

A configuração apontava sempre para a mesma outbox SQLite. Após a primeira
execução, o guard de proteção contra reuso de episódio rejeitava o comando.
Nenhum arquivo anterior deve ser apagado para permitir outra tentativa.

## Correção

`experiments/directml/worker.py` usa a configuração indicada como base e cria
`physical-prepared/sessions/<UUID>/` em cada execução explícita, com:

- Outbox nova, diagnósticos e relatório separados.
- Cópia da configuração efetivamente usada e procedência em session.json.
- Mesmos parâmetros de captura, modelo, classificador, calibração, qualidade,
  preview e temporizadores; somente os dois caminhos de saída são substituídos.
- Verificação dos guards antes da preparação e nova validação da outbox final.
  Colisão de diretório causa erro; não há truncamento, retomada ou remoção.

O comando informa a nova pasta antes de começar e o caminho do relatório ao
terminar. A configuração base continua intacta e pode ser usada novamente.
A entrega HTTP e as imagens continuam desligadas.

Arquivos alterados: worker.py, testes de repetição, README do experimento,
STATUS e índice de relatórios. Não houve mudança do worker normal, modelo,
pesos, classificador ou dos resultados de CPU/GPU anteriores.

## Verificação executada

```powershell
. ./scripts/activate.ps1
uv run --project services/edge --frozen pytest experiments/directml/tests/test_prepared_worker.py experiments/directml/tests/test_repeat_worker.py -q
uv run --project services/edge --frozen pytest experiments/directml/tests -q
uv run --project services/edge --frozen ruff check --config services/edge/pyproject.toml experiments/directml
uv run --project services/edge --frozen ruff format --check --config services/edge/pyproject.toml experiments/directml
git diff --check
```

Sete testes focados e 25 do experimento passaram; lint e formatação passaram.
Os testes verificam duas execuções independentes, preservação dos arquivos e
parâmetros originais, colisão de UUID, guards e o fluxo de execute com LIVE
simulado. Não são evidência física de webcam ou GPU.

A configuração privada real também foi carregada, clonada e validada,
sem executar run_live ou carregar modelo. Sete arquivos originais tiveram
hashes registrados antes da alteração e conferidos ao fim, incluindo outbox,
configuração, trace e relatório. Nenhum foi sobrescrito.
A preparação de conferência ficou em
`physical-prepared/sessions/15803273-e9c9-4fab-b63d-a374056ad27b/`;
contém somente configuração/procedência e nenhuma observação física.

## Comando para a nova tentativa do fundador

Na raiz do projeto, com a janela da tentativa anterior fechada:

```powershell
. ./scripts/activate.ps1
$prova = (Get-Content .local/detector-evolution/directml-current.json -Raw | ConvertFrom-Json).root
uv run --project experiments/directml --frozen python experiments/directml/worker.py --config "$prova/physical-prepared/webcam-directml-60s.yaml"
```

O mesmo comando pode ser usado em outras tentativas. A câmera abre somente
quando esse comando é executado; Q/Esc encerra antes do limite configurado.
Os arquivos são diagnósticos locais, sem gravação de vídeo ou entrega ao painel.
Se o enquadramento mudar, a calibração de piso existente precisa ser conferida.

## Limites

Nenhuma câmera foi aberta pelo assistente nesta correção, nenhuma tentativa
foi repetida automaticamente e nenhum resultado anterior foi apagado.
A nova tentativa física e sua avaliação continuam por fazer.
As falhas perceptuais e os limites da prova DirectML permanecem registrados.
Sem commit, push ou aprovação do MVP nesta correção.
