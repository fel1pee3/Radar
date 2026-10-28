# Prova isolada de RTMO com DirectML

**Integração funcional de 28/10:** a opção explícita `model.executor: DIRECTML`
agora faz parte da fábrica normal do worker. Use `scripts/run-edge.py` dentro
deste ambiente isolado para o fluxo com HTTP existente.
[Roteiro de API, painel e worker](../../docs/USO_DIRECTML_EXPERIMENTAL.md).
O runner curto `worker.py` e os benchmarks abaixo preservam seus guards e
continuam separados da demonstração com envio.

Este diretório seleciona outra sessão ONNX Runtime no processo experimental.
Pré-processamento, pós-processamento, coordenadas, recuperações V3,
classificador, contexto e motor temporal vêm do worker existente.
O worker normal e seu ambiente continuam usando CPU.

A prova usa Windows x64, Python 3.12.15 e exclusivamente
`onnxruntime-directml==1.23.0`. A CPU comparável roda no mesmo pacote/runtime;
a referência CPU 1.23.2 roda no ambiente anterior, sem instalar dois runtimes
no mesmo ambiente. O adaptador aceito é o AMD 1002:15E7 fisicamente verificado;
o Microsoft Basic Render Driver é rejeitado.

Na raiz do repositório:

```powershell
. ./scripts/activate.ps1
uv sync --project experiments/directml --frozen
```

Os vídeos, PNGs, configurações e pesos permanecem privados em `.local/`.
O ponteiro `.local/detector-evolution/directml-current.json` identifica os
protocolos e resultados desta rodada. Nenhum download implícito de modelo.

Para repetir a comparação pequena em uma pasta nova:

```powershell
$original = (Get-Content .local/detector-evolution/directml-current.json -Raw | ConvertFrom-Json).root
$novo = ".local/detector-evolution/directml-repeat-$([guid]::NewGuid())"
uv run --project experiments/directml --frozen python experiments/directml/run_micro.py --protocol "$original/micro-protocol.frozen.json" --output $novo
```

Isso executa cinco rodadas sequenciais com ordem alternada, coleta profiling
em uma execução separada e aplica o gate congelado. Não abra outra medição
durante a execução. O comando recusa sobrescrever a pasta de saída.
`run_micro.py` usa por padrão a CPU 1.23.2 existente em
`.local/pose-env-965d2e5d/.venv/Scripts/python.exe`; se esse ambiente não existir,
prepare-o separadamente com a versão exata, ou indique `--reference-python`.
Não instale `onnxruntime` dentro deste projeto DirectML.

Para medir um único FILE autorizado com transmissão a 1×:

```powershell
$saida = ".local/detector-evolution/directml-stream-$([guid]::NewGuid())"
uv run --project experiments/directml --frozen python experiments/directml/stream.py --backend directml --config .local/detector-evolution/perception-dce2d01b-278b-4029-a405-974ffb0d00e9/candidate-final/intake16-03/comparison.yaml --output $saida
```

`stream.py` rejeita webcam e usa o executor existente
`scripts/validation/benchmark-stream.py`. HTTP e snapshots são desabilitados,
o SQLite é novo e exclusivo e não há reuso de episódios de outra execução.
O relatório distingue o algoritmo REFERENCE_4_SPIN do executor experimental
efetivamente usado. `session.run` retorna NumPy na CPU; o decode original
consome as saídas antes da decisão. O profiling fica fora dos tempos comparados.

Os orquestradores `run_streams.py` e `run_functional.py` consomem os protocolos
privados congelados, conferem hashes e recusam sobrescrever resultados.
Para uma nova rodada, crie um protocolo com `outputRoot` novo; não apague ou
substitua as saídas históricas. A regressão em FILE sem ritmo real não comprova
desempenho LIVE nem corrige perdas históricas.

Testes sem câmera ou GPU:

```powershell
uv run --project services/edge --frozen pytest experiments/directml/tests -q
uv run --project services/edge --frozen ruff check --config services/edge/pyproject.toml experiments/directml
uv run --project services/edge --frozen ruff format --check --config services/edge/pyproject.toml experiments/directml
```

A decisão e os números medidos ficam no
[relatório](../../docs/RELATORIOS/VIABILIDADE_RTMO_DIRECTML_2026_10_27.md).


A prova favorável deixou uma configuração de 60 s somente preparada em
`physical-prepared/webcam-directml-60s.yaml`, sob o diretório privado da rodada.
O runner separado `worker.py` é a opção explícita para um futuro teste físico;
não foi executado. Mantém HTTP/imagens desligados e exige outbox nova e duração
limitada. O enquadramento deve continuar correspondendo à calibração existente.
Consulte o relatório antes de executar; o comando FILE acima continua sem câmera.

## Repetir o teste curto da webcam

A partir de 28/10, o worker cria uma sessão independente em
`physical-prepared/sessions/<UUID>/` a cada execução explícita. O mesmo comando
funciona novamente, preservando a outbox e os resultados de todas as tentativas.
A pasta da sessão é informada no terminal. Não apague a outbox anterior.

```powershell
. ./scripts/activate.ps1
$prova = (Get-Content .local/detector-evolution/directml-current.json -Raw | ConvertFrom-Json).root
uv run --project experiments/directml --frozen python experiments/directml/worker.py --config "$prova/physical-prepared/webcam-directml-60s.yaml"
```

Esse comando abre a câmera por até 60 s. Não grava vídeo/imagem nem entrega
incidentes ao painel. Q/Esc encerra antes. Confira o piso se mudar o enquadramento.
A correção foi testada sem abrir a câmera.
[Diagnóstico e preservação da tentativa anterior](../../docs/RELATORIOS/REPETICAO_WEBCAM_DIRECTML_2026_10_28.md).

## Análise da sessão física de 28/10

O fundador executou o teste posteriormente. Houve uma Pessoa no chão local e
rearme, mas o ensaio terminou manualmente em 56,31 s, teve cobertura insuficiente
no horizonte completo e ficou sem o último perfil de processamento.
HTTP continuou desligado. O resultado é parcial; não houve promoção do padrão.
[Análise e reprodução somente dos registros salvos](../../docs/RELATORIOS/ENSAIO_FISICO_DIRECTML_2026_10_28.md).
