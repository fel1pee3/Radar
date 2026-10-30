# Runtime Python 3.13 assinado — DirectML experimental

Ambiente separado com `onnxruntime-directml==1.23.0`, Python PSF 3.13.17 e
lockfile próprio. Preserva `experiments/directml` e a configuração normal do worker.
Não instale ONNX Runtime CPU/GPU concorrente aqui.

Prepare com `scripts/validation/prepare-python313.ps1`, na raiz. Consulte o
[diagnóstico Windows](../../docs/DIAGNOSTICO_RUNTIME_WINDOWS.md) para assinatura,
origem e a limitação de patch: 3.13.18 é mais novo; 3.13.17 não é anunciado como
última correção de segurança.

O launcher importa o código real do worker, sem reinstalá-lo:

```powershell
. ./scripts/activate.ps1
uv run --project experiments/python313-directml --frozen --no-python-downloads python scripts/run-edge.py run --config .local/CONFIGURACAO_FILE_AUTORIZADA.yaml
```

Use uma configuração existente autorizada. O comando acima é um modelo de uso,
não cria o arquivo. DirectML exige o adaptador verificado AMD 1002:15E7 e perfil
REFERENCE_4_SPIN; falha de inicialização é explícita. Provider disponível, sozinho,
não comprova execução na GPU: confira o perfil de operadores do relatório.

Recuperações opt-in aceitas no worker: RTMO_ADAPTIVE_V3 e RTMO_PREFERRED_V2.
A segunda permanece experimental e seus resultados devem ser avaliados junto
aos controles e à cobertura, além do custo. CPU continua padrão das configurações
normais. Nenhuma webcam é aberta pela preparação do ambiente.
