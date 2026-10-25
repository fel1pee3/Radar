# Usar e validar o candidato de postura

**Experimental; não aprovado para seu cômodo.**
[Resultados](RELATORIOS/EVOLUCAO_DETECTOR_02.md).
[Reserva de 16 vídeos e candidato corporal V2](RELATORIOS/EVOLUCAO_DETECTOR_03.md).
[Resultado reservado: V2 não aprovado](RELATORIOS/EVOLUCAO_DETECTOR_04.md).
Comandos na raiz, com os materiais privados desta bancada; não abrem webcam.
Pesos e vídeos não estão no Git. Instalações novas precisam dos materiais e
artefato autorizados correspondentes.

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
