# Usar e validar o candidato de postura

**Experimental; não aprovado para seu cômodo.**
[Resultados](RELATORIOS/EVOLUCAO_DETECTOR_02.md).
[Reserva de 16 vídeos e candidato corporal V2](RELATORIOS/EVOLUCAO_DETECTOR_03.md).
[Resultado reservado: V2 não aprovado](RELATORIOS/EVOLUCAO_DETECTOR_04.md).
Comandos na raiz, com os materiais privados desta bancada; não abrem webcam.
Pesos e vídeos não estão no Git. Instalações novas precisam dos materiais e
artefato autorizados correspondentes.

## Auditoria de recuperação em arquivo — sem câmera

A investigação de estabilização não aprovou uma nova política para o worker.
A ROI foi mantida como experimento FILE isolado; os estimadores e configurações
existentes continuam preservados. [Resultados e regressões](RELATORIOS/ESTABILIZACAO_PERCEPTUAL_2026_10_26.md).
O auditor versionado reproduz os sete frames e suas alternativas:

```powershell
. ./scripts/activate.ps1
$saida = ".local/auditoria-rtmo-$([guid]::NewGuid())"
uv run --offline --project services/edge --frozen python scripts/validation/audit-rtmo-recovery.py --manifest .local/detector-evolution/stabilization-ce12cde8-31ee-4665-9727-c5f1da1111d5/seven-frame-manifest.json --output $saida --repeats 3
```

Exige os arquivos autorizados e pesos privados desta bancada. Rejeita webcam e
timestamp inexistente, sem aproximar um frame. Não abre banco/HTTP nem cria
incidente; as poses detalhadas ficam na saída privada. O manifesto e os limites
da análise estão no [diagnóstico](RELATORIOS/DIAGNOSTICO_RECUPERACAO_2026_10_26.md).
Uma alternativa contrafactual útil não é informação disponível antecipadamente
ao detector. Este comando não comprova aceite temporal ou desempenho ao vivo.

## Preferência adaptativa — experimental, não promovida

RTMO_PREFERRED_V2 acrescenta reaquisição começando por ORIGINAL, mantendo o V1 e
a referência. Continua opt-in e não autoriza migrar a configuração LIVE.
[Correção, comparação e limites restantes](RELATORIOS/REAQUISICAO_V2_2026_10_26.md).
O mesmo executor abaixo aceita `--recovery RTMO_PREFERRED_V2`, sempre com uma
saída nova. Nenhum ensaio físico é executado por esse comando.

RTMO_PREFERRED_V1 reduziu custo nos quatro cenários técnicos, mas perdeu cobertura
em quatro controles da regressão. Mantenha as configurações existentes; não há
novo ensaio de webcam preparado para este candidato.
[Resultados e diagnóstico](RELATORIOS/RECUPERACAO_ADAPTATIVA_2026_10_26.md).
Para reproduzir somente em arquivo, com saída privada nova:

```powershell
. ./scripts/activate.ps1
$saida = ".local/benchmarks/adaptive-$([guid]::NewGuid())"
uv run --offline --project services/edge --frozen python scripts/validation/benchmark-stream.py --config .local/detector-evolution/perception-dce2d01b-278b-4029-a405-974ffb0d00e9/candidate-final/intake16-03/comparison.yaml --output $saida --recovery RTMO_PREFERRED_V1
```

Para referência use `--recovery RTMO_ADAPTIVE_V3`, com outra saída. Ambos ficam
em REPLAY/TEST isolado, sem HTTP ou câmera física. A estratégia não guarda pose
antiga nem interpreta ausência de pose como ambiente vazio.

## Investigar cadência sem abrir a webcam — 26/10

As duas opções de CPU testadas não demonstraram ganho consistente. A referência
permanece `REFERENCE_4_SPIN`; nenhuma configuração de câmera foi migrada.
[Comparação, métricas e limitações](RELATORIOS/DESEMPENHO_TRANSMISSAO_2026_10_26.md).
Nesta rodada, use somente os arquivos existentes para reproduzir o diagnóstico:

```powershell
. ./scripts/activate.ps1
$saida = ".local/benchmarks/stream-$([guid]::NewGuid())"
uv run --offline --project services/edge --frozen python scripts/validation/benchmark-stream.py --config .local/detector-evolution/perception-dce2d01b-278b-4029-a405-974ffb0d00e9/candidate-final/yoga2-02/comparison.yaml --output $saida --runtime-profile REFERENCE_4_SPIN
```

O comando usa inferência real, entrega frames a 1× e exercita o mesmo agendamento
LIVE com buffer de frame recente. Registra `REPLAY`/transmissão técnica, sem HTTP,
snapshot, credencial ou abertura de dispositivo. `--preview` mostra o arquivo;
não é vídeo previamente inferido. A pasta de saída deve ser nova e fica privada.
O resumo distingue lacunas, idades, cobertura, eventos e custos. Ficar sem alerta
com cobertura insuficiente permanece inconclusivo. Os casos conhecidos não
constituem avaliação independente.

`complete: true` confirma que o arquivo terminou; não significa aprovação da
detecção. A cobertura e o prazo de cada alvo continuam sendo critérios separados.

O roteiro físico abaixo fica preservado como histórico. Sem ganho consistente
nesta rodada, não há novo candidato aprovado que justifique repetir os 12 minutos.

## Ensaio controlado preparado em 26/10 — recuperação de orientação

**Ensaio executado e auditado:** sessão `10347778…` não aprovou o aceite.
Marcadores incluíram preparação/retorno; algumas tentativas foram incompletas
ou curtas, sem identificação de quais. Há cobertura insuficiente e revisões
pendentes. [Auditoria e dados por cena](RELATORIOS/ENSAIO_WEBCAM_ORIENTACAO_2026_10_26.md).
Roteiro preservado para referência; nenhuma repetição foi iniciada pelo auditor.

A sequência desta seção pertence ao ensaio anterior. O roteiro de três minutos abaixo
fica preservado como referência; não executar as duas sessões juntas.
O candidato `RTMO_ADAPTIVE_V3` mantém o classificador V3 e acrescenta uma tentativa
de orientação em frames atuais com proposta horizontal e oito essenciais com
score suficiente. O V3 anterior continua disponível como `RTMO_ADAPTIVE_V2`.
[Diagnóstico, comparação e limitações](RELATORIOS/PERCEPCAO_ORIENTACAO_V3_2026_10_26.md).
Não houve treino nos dois vídeos de yoga; eles agora são desenvolvimento/regressão.

**Sua presença só é necessária a partir da conferência da câmera.** Não execute
o ensaio ainda se não tiver como marcar os instantes reais: outra pessoa pode
operar os botões, ou você pode usar um teclado já disponível ao alcance, mantendo
o notebook imóvel. Não é necessário conversar no chat enquanto fica no chão.
Horário de instrução/contagem regressiva não será tratado como início da postura.
Sem marcação confiável, a latência da tentativa fica inconclusiva.

1. Na raiz, inicie os serviços, preservando seu banco e proprietário:

   ```powershell
   . ./scripts/activate.ps1
   pnpm.cmd infra:up
   ```

   Em outros dois terminais, ative o ambiente em cada um e execute `pnpm.cmd dev:api`
   e `pnpm.cmd dev:web`. Se já estiverem ativos, use as instâncias existentes.
   Abra `http://127.0.0.1:3000`, entre com sua conta e deixe Incidentes/Fontes disponíveis.
   O PostgreSQL da demonstração permanece na 15432; não alterar o serviço na 5432.

2. Quando estiver pronto, confira a lente descoberta, câmera fixa e corpo inteiro.
   Este comando abre somente a prévia da webcam, sem inferência/eventos:

   ```powershell
   uv run --offline --project services/edge --frozen radar-edge probe --config .local/detector-evolution/candidate-orientation/webcam-controlled.yaml --seconds 60 --preview
   ```

   Feche com Q/Esc. A configuração usa índice 0/DSHOW, 640×480 e os mesmos modelos,
   credencial e uma **cópia idêntica** da calibração anterior. A compatibilidade
   digital passou; isso não confirma que o notebook continua na mesma posição.
   Confira o contorno na prévia do ensaio antes de marcar a primeira cena.

   **Somente se o enquadramento mudou ou o piso está incorreto**, deixe o chão
   livre, feche o worker e execute:

   ```powershell
   uv run --offline --project services/edge --frozen radar-edge calibrate --config .local/detector-evolution/candidate-orientation/webcam-controlled.yaml
   uv run --offline --project services/edge --frozen python scripts/validation/confirm-posture-context.py --config .local/detector-evolution/candidate-orientation/webcam-controlled.yaml --confirmed
   ```

   A calibração mostra imagem parada de propósito. Marque somente o chão, em
   ordem, e Enter. A cópia preserva o piso original. Confirme o contexto somente
   depois de conferir a marcação; não ajustar o piso para cada postura.

3. Sem abrir câmera, o preflight reproduzível é:

   ```powershell
   uv run --offline --project services/edge --frozen python scripts/validation/physical-session.py --config .local/detector-evolution/candidate-orientation/webcam-controlled.yaml --check
   ```

   Quando a câmera estiver posicionada, o operador preparado e você pronto para
   participar, inicie **uma única sessão**, limitada a 12 minutos:

   ```powershell
   uv run --offline --project services/edge --frozen python scripts/validation/physical-session.py --config .local/detector-evolution/candidate-orientation/webcam-controlled.yaml --start
   ```

   Abre a webcam e uma janela para marcar as cenas, sem vídeo bruto/snapshot.
   O comando verifica a API, usa fila nova por sessão e preserva a credencial,
   a configuração-base e os ensaios anteriores. Não há repetição nem extensão
   automática. Q/Esc na janela da câmera encerra antes se necessário.

4. O operador observa a cena real e clica **Marcar início/fim REAL da cena**,
   ou usa Enter com essa janela em foco. Marque início quando a pessoa terminar
   de chegar à postura; marque fim antes de ela sair. Informe depois se a
   marcação atrasou ou houve erro. O botão não pausa a captura.

   A ordem é: lateral duas vezes; pés para a câmera duas vezes; cabeça para a
   câmera duas vezes; cadeira; ajoelhar; pegar objeto; caminhar; cômodo vazio;
   retorno caminhando. Permaneça aproximadamente 10 s em cada postura no chão,
   com chegada voluntária, lenta e segura. Entre tentativas, levante com calma
   e fique em pé por 20 s. A política ainda exige 3 s contínuos de recuperação
   observada: esperar 20 s não comprova que o modelo conseguiu observá-la.
   Nos controles, marque pelo menos 15 s; nenhuma queda deve ser provocada.

   O programa grava marcadores humanos UTC/monotônicos separados das previsões.
   Não usar o instante em que apareceu um alerta como início da situação-alvo.
   Tentativa perdida/incompleta permanece no relatório; outra execução será
   uma repetição identificada, sem substituir a primeira.

5. Confira os incidentes e os avisos locais. O botão **Vi um novo incidente no
   painel** registra a hora da conferência visual, incluindo reação humana;
   não é cronômetro automático de renderização. Nos incidentes, registre a revisão
   adequada, com nota “Ensaio controlado de orientação, tentativa [número]”.
   Verifique que a nova linha permaneceu no Histórico auditado após recarregar.

   Pelo contrato atual, webcam é **Ao vivo**, em geral entrega **Atual**; não
   falsificar `REPLAY/TEST` para chamar a sessão de teste. Sua natureza controlada
   fica no protocolo e na nota de revisão. O canal SIMULATED do aviso é local;
   não representa mensagem externa ou socorro. Entrega atrasada/incerta deve ser
   reportada como tal.

6. Ao encerrar, a janela deve fechar e Fontes mostrar Fonte encerrada. Guarde o
   diretório `.local/detector-evolution/physical-sessions/<id>` impresso no terminal.
   Contém configuração, protocolo, marcadores, erros e relatório do worker.
   Não envie credencial, senha ou arquivos privados ao chat.

**Critérios definidos antes da sessão:** seis tentativas mantidas no denominador;
PERSON_ON_FLOOR em até 5000 ms desde cada início humano, cobertura temporal ≥80%
em cada tentativa e nenhum episódio duplicado. Reportar rearme bloqueado como
falha/limitação, sem remover a tentativa. Nos controles, zero alertas indevidos
e cobertura decisória ≥80%; no vazio confirmado por humano, cobertura de captura
≥80%, sem inferir vazio a partir de NO_POSE. Medir as lacunas e os frames com
idade >2000 ms rejeitados pelo worker. A inferência cara pode impedir a cadência
necessária; não aprovar desempenho por FPS de arquivo. Para o painel, propõe-se
entrega/exibição em até 5 s após a decisão; sem marcador de exibição, esse tempo
fica não verificado. Revisão precisa estar persistida. Qualquer POSSIBLE_FALL
exige examinar a transição real observada; postura deitada sozinha não a sustenta.
Esse ensaio não aprova reserva independente, operação prolongada, novo teste
offline ou reconhecimento geral de quedas.

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
106 s de worker e cobertura decisória de 56,72%. Fundador relatou três idas ao
chão de 5–7 s, em pé entre elas e piso correto: um alerta para três tentativas,
resultado insatisfatório. Faltam tempos exatos; não reconstruir essas tentativas
pelas próprias previsões. [Análise](RELATORIOS/SESSAO_WEBCAM_V3_2026_10_25.md).
O roteiro abaixo é histórico. Para a nova sessão, use somente o roteiro
controlado de 12 minutos acima.

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
