# Runtime Python 3.13 assinado — CPU experimental

Ambiente separado, preparado para investigar o bloqueio do Python 3.12 pelo
Smart App Control. Não substitui `services/edge` nem altera proteções do Windows.
O código continua em `services/edge/src`; este projeto fixa somente as dependências.

Preparação verificável, na raiz:

```powershell
. ./scripts/activate.ps1
powershell -NoProfile -File scripts/validation/prepare-python313.ps1
```

O preparador verifica procedência, SHA-256 e assinatura PSF antes de executar.
Usa Python 3.13.17, último binário Windows verificado nesta rodada; 3.13.18 é mais
novo e não foi apresentado como instalado. Essa diferença de patch permanece uma
limitação do ambiente experimental. Os ambientes e lockfiles 3.12 são preservados.

```powershell
uv run --project experiments/python313-cpu --frozen --no-python-downloads python scripts/run-edge.py env
$env:PYTHONPATH = Join-Path (Get-Location) 'services/edge/src'
uv run --project experiments/python313-cpu --frozen --no-python-downloads pytest services/edge/tests -q
```

CPU e DirectML têm ambientes distintos. Não instale outra distribuição ONNX Runtime
neste ambiente. [Diagnóstico e recuperação](../../docs/DIAGNOSTICO_RUNTIME_WINDOWS.md).
