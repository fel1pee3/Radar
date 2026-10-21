# Ambiente do worker

Execute na raiz: `uv sync --project services/edge --frozen` e
`uv run --project services/edge --frozen radar-edge env`.
Lint: `pnpm lint:edge` (Ruff). Build do pacote: `uv build --project services/edge`.

O diagnóstico importa MediaPipe, MediaPipe Tasks PoseLandmarker e OpenCV reais,
registra versões e backends compilados e falha se houver múltiplos fornecedores de `cv2`.
Não abre câmera nem carrega modelo. Backends compilados não comprovam captura física.
`doctor`, calibração e execução de vídeo pertencem a etapas futuras.

Somente `opencv-contrib-python` é instalado: é dependência do MediaPipe e inclui GUI
para a futura prévia local. Não instalar `opencv-python` ou variantes headless junto dele.
