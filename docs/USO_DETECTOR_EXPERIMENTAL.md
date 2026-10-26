# Usar e validar o candidato de postura

**Experimental; não aprovado para seu cômodo.**
[Resultados](RELATORIOS/EVOLUCAO_DETECTOR_02.md).
[Reserva de 16 vídeos e candidato corporal V2](RELATORIOS/EVOLUCAO_DETECTOR_03.md).
[Resultado reservado: V2 não aprovado](RELATORIOS/EVOLUCAO_DETECTOR_04.md).
Comandos na raiz, com os materiais privados desta bancada; não abrem webcam.
Pesos e vídeos não estão no Git. Instalações novas precisam dos materiais e
artefato autorizados correspondentes.

## Candidato atual V3 — 25/10/2026

[Resultado desta iteração](RELATORIOS/EVOLUCAO_DETECTOR_05.md): seis alvos e dez
negativos passaram na regressão conhecida. Ainda experimental: perdas históricas,
transições, nova avaliação reservada e teste no cômodo permanecem pendentes.
Os comandos abaixo usam os arquivos privados preparados nesta máquina.

Para iniciar o projeto depois de desligar o computador, na raiz:

```powershell
. ./scripts/activate.ps1
pnpm.cmd infra:up
```

Em dois terminais separados, ative `. ./scripts/activate.ps1` em cada um e execute
respectivamente `pnpm.cmd dev:api` e `pnpm.cmd dev:web`. PostgreSQL da demonstração
usa 15432; não mover para o servidor preexistente na 5432. Abra
`http://127.0.0.1:3000` com a conta existente. API/web já foram iniciados nesta
rodada: não abrir outra instância na mesma porta enquanto estiverem rodando.

Conferir o candidato sem abrir vídeo/câmera e repetir a regressão FILE:

```powershell
. ./scripts/activate.ps1
uv run --offline --project services/edge --frozen radar-edge posture-check --config .local/detector-evolution/candidate-v3/demo-file.yaml
uv run --offline --project services/edge --frozen radar-edge evaluate --manifest .local/detector-evolution/candidate-v3/regression16.json
```

Evaluate cria filas novas, não envia HTTP, não abre webcam nem janela. Esperado:
16 execuções ok/ENDED, seis alvos com PERSON_ON_FLOOR aos 2000 ms, dez negativos
PASS, zero alertas indevidos/duplicações. Conferir `primaryFloorAcceptance` e
`performance`; exit 0 sozinho apenas indica execução sem erro. O relatório
completo fica em `.local/evaluation/<id>/evaluation.json`. São dados de
desenvolvimento, não avaliação independente.

Para assistir ao replay sem alterar incidente ou fila:

```powershell
uv run --offline --project services/edge --frozen radar-edge run --config .local/detector-evolution/candidate-v3/demo-file.yaml --poses-only --preview-paused --replay-speed 1
```

Espaço inicia/pausa; Q/Esc fecha. A análise continua amostrada, não é promessa
de 30 FPS. O piso é o contexto fixo aprovado para esse arquivo.

O replay real já criou o incidente
`http://127.0.0.1:3000/incidentes/1d192fe1-b325-4ff8-907e-dee9007ce29e`,
Reprodução/Teste, PERSON_ON_FLOOR, 2000 ms. Revisão humana salva e conferida,
versão 2. É arquivo de dataset associado à câmera lógica FILE, sem filmagem
do cômodo. O aviso existente é local, canal SIMULATED.

```powershell
uv run --offline --project services/edge --frozen radar-edge outbox-status --config .local/detector-evolution/candidate-v3/demo-file.yaml
```

Esperado: um DELIVERED. Repetir a execução concluída preserva checkpoint;
`deliver` reusa o envelope imutável. Não editar eventId/SQLite para forçar novo
incidente. Credencial fica somente em `.local/demo-smart.json`, sem colar no chat.

Para reproduzir o treino, com as observações e anotações privadas existentes:

```powershell
$radarIteration = Get-Content .local/detector-evolution/improvement-current.json -Raw | ConvertFrom-Json
uv run --offline --project services/edge --frozen radar-edge posture-train --manifest (Join-Path $radarIteration.root 'multiclass-training.json') --output .local/detector-evolution/candidate-v3/posture-reproduction.json
Get-FileHash .local/detector-evolution/candidate-v3/posture-reproduction.json -Algorithm SHA256
```

Usar destino inexistente. SHA esperado:
`40d01401851f24cd8c815557970f0dcf42877707afbba38d521ebfa87bd5bd19`.
O treino é uma ação explícita, não ocorre no worker. Não incluir material
reservado nas entradas TRAIN/SELECTION. Hash igual comprova reprodução dos
pesos, não eficácia independente.

## Sessão física V3 — roteiro e primeiro ensaio

Primeiro ensaio executado pelo fundador em 25/10: um alerta LIVE entregue,
106 s de worker e cobertura decisória de 56,72%; conferência das atividades
e revisão humana ainda pendentes. [Análise](RELATORIOS/SESSAO_WEBCAM_V3_2026_10_25.md).
O roteiro abaixo permanece para novas sessões combinadas; não repetir antes
de concluir a anotação desta execução.

Configuração `.local/detector-evolution/candidate-v3/webcam-short.yaml`: índice 0,
DSHOW, mesma calibração histórica, limite de 180 s, outbox nova, diagnóstico
privado, sem gravação de vídeo/snapshot. Modelo e contexto passaram posture-check
sem abrir câmera. Isso não confirma o enquadramento físico atual.

1. Quando estiver disponível, posicione o notebook estável, lente descoberta,
   piso e corpo inteiro visíveis. Primeiro confira movimento/enquadramento;
   este comando abre a webcam somente quando você o executar:

   ```powershell
   uv run --offline --project services/edge --frozen radar-edge probe --config .local/detector-evolution/candidate-v3/webcam-short.yaml --seconds 30 --preview
   ```

2. Se a câmera permaneceu na mesma posição e a região está correta, preserve
   a calibração. Se mudou, feche a prévia com Q, deixe a área do chão livre e
   execute somente a calibração. A imagem fica parada intencionalmente para
   marcar o piso uma vez por posição de câmera:

   ```powershell
   uv run --offline --project services/edge --frozen radar-edge calibrate --config .local/detector-evolution/candidate-v3/webcam-short.yaml
   ```

   Marque o chão em ordem, excluindo apoios, e Enter. Não marque outra região
   para cada postura. Depois de conferir a marcação, confirme explicitamente
   o arquivo e prepare uma fila nova; o comando preserva configuração/fila
   anteriores e não abre câmera nem certifica o enquadramento sozinho:

   ```powershell
   uv run --offline --project services/edge --frozen python scripts/validation/confirm-posture-context.py --config .local/detector-evolution/candidate-v3/webcam-short.yaml --confirmed
   uv run --offline --project services/edge --frozen radar-edge posture-check --config .local/detector-evolution/candidate-v3/webcam-short.yaml
   ```

3. Combine a sequência antes de iniciar. Use movimentos seguros: já deitado
   em três orientações, 8–10 s em cada, com intervalo em pé de pelo menos 3 s
   para rearme; passagem voluntária lenta ao chão; cadeira; ajoelhar/pegar
   objeto; sofá/rede se visíveis; sair e retornar ao quadro. Não provocar queda.
   Não precisa conversar no chat enquanto executa a sequência.

   ```powershell
   powershell -NoProfile -File scripts/validation/observe.ps1 -Config .local/detector-evolution/candidate-v3/webcam-short.yaml
   ```

4. O limite é três minutos; Q/Esc encerra antes. Anote aproximadamente a hora
   de cada postura, ausências e travamentos. Esperado: alerta de permanência
   em até 5 s desde cada início observável sustentado, nenhum alerta nos
   controles, abstenção explícita durante oclusão e Fonte encerrada ao terminar.
   Passagem voluntária não é ground truth de queda. Se a cena/pose não estiver
   observável, o resultado é inconclusivo, sem declará-lo acerto.

5. Confira incidentes, avisos locais e histórico; registre revisão humana.
   Guarde o caminho de medições impresso pelo observe. O experimento físico
   ainda precisa ser analisado; não concluir por haver apenas esqueleto fluido.

Para reserva posterior: pelo menos quatro alvos novos já no chão e oito
atividades comuns, 10–20 s cada, gravações/sessões não usadas em ajustes. Incluir
orientações e apoios relevantes; reservar também transições encenadas autorizadas
e controles. Os 16 e CAUCAFall desta rodada não podem voltar a ser reserva.

## Instruções históricas do candidato V1

## Conferir sem abrir fonte

```powershell
. ./scripts/activate.ps1
uv run --project services/edge --frozen radar-edge posture-check --config .local/detector-evolution/candidate-01/demo-file.yaml
```

Esperado: status ok, LINEAR_CONTEXT_V1, sourceKind FILE, sourceOpened false,
databaseOpened false e functionalMvpApproved false. Confere modelo, artefato,
instalação e calibração; não comprova detecção. Não trocar hashes para contornar
erro de contexto ou transportar um modelo de outro cômodo.

## Rodar o arquivo preparado

```powershell
uv run --project services/edge --frozen radar-edge run --config .local/detector-evolution/candidate-01/demo-file.yaml --no-preview
uv run --project services/edge --frozen radar-edge outbox-status --config .local/detector-evolution/candidate-01/demo-file.yaml
```

É o FallLeftS9 usado no desenvolvimento. HTTP desligado: candidato fica na
SQLite privada, sem aparecer automaticamente no painel. Primeira execução
completa do ensaio: PERSON_ON_FLOOR aos 6800 ms, 3800 ms após início anotado.
Repetir execução concluída preserva checkpoint e não deve criar outro evento.
Nenhuma imagem é gravada.

Para somente assistir, sem alterar a fila:

```powershell
uv run --project services/edge --frozen radar-edge run --config .local/detector-evolution/candidate-01/demo-file.yaml --poses-only --preview-paused --replay-speed 1
```

Espaço inicia/pausa, Q/Esc encerra. Desenho estabilizado é visual; o motor usa
pontos reais. Prévia não mede precisão. Diagnósticos ficam no outputDirectory
privado, com limites e retenção explícitos.

## Reproduzir o ajuste

```powershell
uv run --project services/edge --frozen radar-edge posture-train --manifest .local/detector-evolution/candidate-01/training-manifest.json --output .local/detector-evolution/candidate-01/posture-nova-reproducao.json
```

Destino novo obrigatório. As duas execuções verificadas geraram bytes idênticos,
SHA 154196a21b4c567f1bc1d3654f7a9527b20dc222a213b66ecf3803da3dc7ed04.
Somente TRAIN é aberto para ajuste; seleção/reserva não entram no treino.
Manifesto registra permissões, fontes, hashes e grupos. Não há treino automático
durante run. Não treinar material sem procedência/permissão verificada.

## Próxima coleta, quando você puder

Câmera fixa, mesmo enquadramento, corpo inteiro visível e boa luz. Região 2D
confirmada; cadeira/cama/rede que se sobrepõem ao chão na imagem exigem exclusão
ou outro enquadramento. O polígono não comprova contato físico com o piso.

Separar desenvolvimento e reserva por sessões inteiras. Para desenvolvimento:
pessoa já deitada em três orientações, transição voluntária segura, cadeira,
rede se visível, ajoelhar, pegar objeto, ambiente vazio e perda temporária de
observação. Não provocar queda. Anotar intervalos antes de consultar previsões.
Depois selecionar/congelar o candidato do seu cômodo e avaliar pelo menos quatro
alvos e oito negativos novos. Repetir a mesma pessoa em outra sessão é possível,
declarando avaliação por sessão, sem alegar generalização entre pessoas.

Webcam será iniciada por você depois dos arquivos, com roteiro preparado. Não
há teste físico solicitado agora, nem repetição da apresentação ou dos 30 minutos
históricos. Validação inclui entrega à API, painel, revisão humana e ausência de
duplicação. Avisos atuais são registros locais simulados/atualização visual do
painel; não há aviso externo ao celular.

## Conferir os novos 16 vídeos

Os 16 já foram conferidos pelo fundador e avaliados na versão congelada:
2/6 alvos em baseline/V2, quatro perdas e seis negativos inconclusivos na V2.
Não iniciar outro ciclo de marcações para ajustar esse resultado. Para rever
somente o vídeo original com as regiões, sem webcam ou treino:

```powershell
. ./scripts/activate.ps1
uv run --offline --project services/edge --frozen python .local/detector-evolution/review-intake16-context.py
```

Espaço inicia/pausa, R repete, Q/Esc fecha. Após a avaliação, a revisão é somente
consulta: C não modifica as marcações congeladas.
Amarelo é região do piso; vermelho, exclusão de apoio. Os intervalos dos seis
positivos e os dez negativos já estão registrados. O preparador de
avaliação verifica os recibos/hashes; não muda confirmação automaticamente.

O candidato V2 usa 29 atributos corporais, sem os seis absolutos da imagem,
ajustado somente no CAUCAFall antigo. Continua experimental, com piso/contexto
confirmados e política própria; não é aprovação do novo cômodo. Para conferir
seus hashes e contexto no **arquivo antigo de teste**, sem abrir vídeo:

```powershell
$radarBodyCheck = Get-Content .local/detector-evolution/candidate-body-v2/file-check-pointer.json -Raw | ConvertFrom-Json
uv run --offline --project services/edge --frozen radar-edge posture-check --config (Join-Path $radarBodyCheck.root 'config.yaml')
```

Esperado: LINEAR_BODY_V2, symmetric-body-shape-29-v1, sourceOpened=false,
databaseOpened=false e functionalMvpApproved=false. V1 e suas restrições
permanecem disponíveis nos comandos anteriores. Não apontar a configuração V1
para novos cômodos nem trocar hashes para ignorar a vinculação de instalação.
