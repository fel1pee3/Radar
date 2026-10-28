# Demonstração experimental com DirectML

A opção GPU usa o worker, motor temporal, outbox, autenticação, API e painel
existentes. CPU permanece como padrão. A integração em arquivo foi comprovada;
a demonstração física completa desta opção ainda precisa ser executada.
O reconhecimento permanece experimental, com perdas históricas conhecidas.

Execute todos os comandos na raiz do RadarSoftware. Em **cada terminal novo**,
ative as ferramentas com `. ./scripts/activate.ps1`.

## Preparar e iniciar os serviços

Terminal 1:

```powershell
. ./scripts/activate.ps1
pnpm.cmd setup:env
pnpm.cmd infra:up
pnpm.cmd dev:api
```

O setup preserva os .env existentes. Não recrie banco, proprietário ou credencial.
A API usa http://127.0.0.1:3001/v1.

Terminal 2:

```powershell
. ./scripts/activate.ps1
pnpm.cmd dev:web
```

Abra http://127.0.0.1:3000 e entre com sua conta existente.
Em **Fontes**, localize a câmera de bancada com ID começando em `5be84234`.
A câmera física será aberta somente ao executar o worker abaixo.

## Executar o worker opt-in

A configuração desta entrega foi preparada sem captura em:

`.local/detector-evolution/directml-integration-757f4105-e1ad-46ca-8efb-995ad297eb3e/physical-demo/config.yaml`

Ela preserva webcam 0/DSHOW, geometria 640×480, piso versão 3, pesos,
classificador, qualidade e temporizadores do ensaio anterior. A entrega está
habilitada para a credencial já existente em `.local/webcam-device.json`.
A credencial foi conferida no banco local em transação READ ONLY: está ativa
e vinculada à câmera WEBCAM correta. Não houve envio HTTP, emissão ou rotação.
A integração automatizada usou outra credencial e outro banco, exclusivos de teste.

Terminal 3, **somente quando estiver pronto para abrir a câmera**:

```powershell
. ./scripts/activate.ps1
uv sync --project experiments/directml --frozen
$configGPU = (Get-Content .local/directml-demo-current.json -Raw | ConvertFrom-Json).config
uv run --project experiments/directml --frozen python scripts/run-edge.py run --config $configGPU
```

O launcher chama a CLI normal do worker dentro do ambiente DirectML isolado.
Não instale onnxruntime CPU nesse ambiente. O ambiente services/edge continua
com seu runtime CPU e suas configurações anteriores.

Esta configuração tem `model.executor: DIRECTML`, exige o adaptador AMD
verificado e falha com `DIRECTML_INITIALIZATION_FAILED` se não conseguir
inicializar. Não existe substituição silenciosa por CPU.

Nenhum vídeo ou snapshot é gravado por padrão. Sinais, pose do evento, traces
e SQLite ficam privados em .local; o evento e heartbeat seguem à API local.

## Sequência curta

1. Confira na prévia se o contorno ainda corresponde ao chão. Se o enquadramento
   mudou, encerre e recalibre antes de avaliar a detecção.
2. Fique em pé, inteiro no quadro, por aproximadamente cinco segundos.
3. Deite voluntariamente e com calma, mantendo o corpo inteiro visível, por
   15–20 segundos. Não provoque queda.
4. Levante com calma e fique em pé por pelo menos cinco segundos.

Você pode se afastar do computador durante a sequência: a execução encerra
automaticamente ao atingir o limite de **60 segundos desde o início do worker**,
incluindo inicialização. A análise em andamento e a liberação dos recursos podem
acrescentar alguns segundos ao fechamento. Q/Esc na prévia ou o controle stop também encerram; Ctrl+C
interrompe e preserva os pendentes. O último perfil é finalizado ao sair pela
prévia. O relatório distingue limite automático, saída da prévia e interrupção.

Um clique, contagem regressiva ou horário antes de caminhar até o piso não é
o início real da postura. Esta execução não grava vídeo: sem anotação precisa
do momento em que você já estava deitado, a latência humana permanecerá
inconclusiva. Os 2 s de persistência interna não são essa latência.

## Conferir o resultado e salvar sua revisão

Depois que a janela fechar:

1. Em **Fontes**, confira **Fonte encerrada**. Erros de autenticação ou captura
   precisam ser resolvidos; não interprete falta de incidente como teste negativo.
2. Em **Incidentes**, filtre pela câmera de bancada e abra o registro desta
   execução, conferindo horário, **Ao vivo**, modelo RTMO e sinais.
   A classificação de recebimento pode ser atual, atrasada ou incerta conforme
   a proteção de relógio/entrega; não deve ser trocada manualmente.
3. Escolha **Reconhecimento** e registre, se desejar.
4. Escolha **Revisão humana**, marque o que realmente observou e escreva, por
   exemplo: “Teste controlado: fiquei deitado no chão, sem queda”.
   Clique em **Registrar ação**.
5. Recarregue a página e confira a nova linha no **Histórico auditado**.
   Em **Avisos locais**, deve existir um aviso para o incidente.

A revisão automatizada dos testes de arquivo não é sua revisão. Um aviso local
não significa que uma mensagem externa foi enviada.

O relatório fica em `physical-demo/results/<UUID>/report.json`.
A outbox desta demonstração é nova e separada das provas anteriores.
Se você executar novamente, o fluxo normal preserva pendentes e episódios:
um episódio ainda ativo não deve gerar outro incidente só por reiniciar.
O período em pé permite o rearme existente; não apague o SQLite para repetir.

## Critérios e limites

Avaliaremos detecção durante a permanência no piso, emissão única por episódio,
entrega e aviso, revisão persistida, rearme, saída final, cadência, idade de
decisão e cobertura do horizonte inteiro. Mantidos: cobertura mínima 80%,
lacuna de observação 500 ms, idade máxima 2 s e persistência de 2 s.
Não se aprova removendo inicialização ou encerramento do denominador.

Continuam pendentes confiabilidade geral, anatomia precisa, outras orientações,
controles variados, latência humana sem marcadores e as quatro perdas históricas.
A câmera física com o novo fluxo GPU→painel ainda não foi executada nesta entrega.
O candidato não está aprovado para assistência real.

Para preparar outra configuração sem sobrescrever esta nem abrir a câmera:

```powershell
. ./scripts/activate.ps1
$prova = (Get-Content .local/detector-evolution/directml-current.json -Raw | ConvertFrom-Json).root
$destino = ".local/directml-demo-$([guid]::NewGuid())"
uv run --project experiments/directml --frozen python scripts/validation/prepare-directml-demo.py --base "$prova/physical-prepared/webcam-directml-60s.yaml" --credential .local/webcam-device.json --output $destino
```

O preparador confere o contexto e os arquivos locais, sem HTTP, captura ou rotação
de token. `run-edge.py run` é o comando que efetivamente abre a fonte.

[Resultados de integração e regressão](RELATORIOS/INTEGRACAO_DIRECTML_2026_10_28.md).
