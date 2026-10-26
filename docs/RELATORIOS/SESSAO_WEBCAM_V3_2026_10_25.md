# Webcam V3 — análise da sessão de 25/10/2026

**INSATISFATÓRIO PARA O ACEITE FÍSICO: três idas ao chão de 5–7 s relatadas, um alerta.**
Captura/entrega verificadas; duas tentativas sem novo alerta, causas individuais ainda em investigação.
Análise de registros existentes, sem reabrir câmera, alterar parâmetros ou executar treino.
Não substitui a [regressão em arquivo](EVOLUCAO_DETECTOR_05.md) nem aprova o detector.

## Sessão identificada

Comando informado pelo fundador:

```powershell
. ./scripts/activate.ps1
powershell -NoProfile -File scripts/validation/observe.ps1 -Config .local/detector-evolution/candidate-v3/webcam-short.yaml
```

Último monitor: `.local/etapa08/continuous-cf26651e-d20d-412c-b744-fc4c450fc470/`.
LIVE `97067015-119a-4f64-a773-ab9425bd4456`, diagnóstico
`a0df7175-227c-4b8e-93b9-164eb5b1511a`. Fonte webcam 0/DSHOW, 640×480,
RTMO-s, recuperação RTMO_ADAPTIVE_V2, classificador signed-body-mlp-v3-dev01,
política floor-rtmo-score-posture-multiclass-v3-dynamics01-adaptive2,
piso ab0094ef-eee7-478b-8304-bf96139c0d48-v3 e estabilização visual ligada.
Os hashes dos modelos são os mesmos da evolução 05.

O contexto SQLite foi retomado da tentativa anterior; os eventos foram filtrados
pelo runId desta captura. Não somamos as duas tentativas como sessão contínua.
Primeira tentativa `continuous-f1e6cae2…`: 17,98 s totais, 44 análises,
zero elegíveis, zero eventos; pose insuficiente em todas. Isso não demonstra
negativo correto. Motivo físico/enquadramento daquela tentativa não confirmado.

## Resultado técnico da última sessão

| Medida | Resultado |
| --- | --- |
| Estado / erros | ok, ENDED; worker-errors.log vazio |
| Tempo total do worker | 106,060 s, aproximadamente 1min46s |
| Intervalo observado entre análises | 102,469 s |
| Cobertura de captura segundo o motor | 94,750 s, 92,47% do intervalo observado |
| Tempo decisório elegível | 58,125 s, **56,72%** do intervalo observado |
| Análises / elegíveis / candidatas | 377 / 271 / 31 |
| Cadência da análise | 3,669/s no tempo observado |
| Atualizações da prévia | 3,664/s; não é FPS do monitor/driver |
| Inferência | média 208,32 ms; mínimo 112,58 e máximo 757,24 ms |
| Classificação de postura | média 0,335 ms; máximo 11,33 ms, separada da inferência |
| Intervalos >500 ms entre análises | 12, somando 7719 ms; máximo 797 ms |
| Captura | 2789 imagens adquiridas, 378 consumidas, 2411 sobrescritas no buffer recente |
| Reconexões / múltiplas poses | 0 / 0 |
| CPU do processo | 341,234 CPU-s; não uso global da máquina |
| Pico de memória do processo | 230,89 MiB |
| Pico somado dos processos monitorados | 339,60 MiB; pode contar páginas compartilhadas mais de uma vez |
| Diagnóstico / imagens | 380 registros completos, sem truncamento/falha; nenhum vídeo/JPEG gravado |
| Eventos / entrega | 1 PERSON_ON_FLOOR, DELIVERED, uma tentativa, ACK CURRENT |
| Encerramento | heartbeat final ENDED aceito, zero pendências |

As 2411 sobrescritas são comportamento do buffer de imagem mais recente;
não equivalem a 2411 falhas de captura. A cadência de análise ficou abaixo do
alvo de 5/s. Os 30 FPS nominais da câmera não comprovam 30 análises/s.
Captura e elegibilidade são somas conservadoras de intervalos com ambos os
extremos aceitos e lacuna ≤500 ms. Não são porcentagem de acurácia.

O limite configurado é 180 s, mas esta execução durou 106 s. ENDED não distingue
tecla Q, fechamento da janela ou comando de parada; não afirmar que completou
três minutos ou que o limite automático encerrou esta sessão.

## Alerta confirmado na API/banco

Em 25/10, horário America/Sao_Paulo:

- Início da evidência aceita: **19:38:53,013**.
- Detecção: **19:38:55,122**.
- Recebimento: **19:38:55,490**, 368 ms depois da detecção.
- Aviso local registrado: **19:38:55,866**.
- Incidente: `b1c438bc-ee52-4e13-ad9e-8e5d966a862a`.
- Evento: `19d4776a-9f7f-45bc-9108-0648118f88b6`.
- Pessoa no chão, LIVE/CURRENT, 2109 ms de evidência, fração válida 1 na janela,
  quadril dentro da região, sem descida rápida comprovada.
- Uma receipt, um aviso local SIMULATED, sem duplicação observada. Aviso marcado
  urgente localmente; **não houve comunicação externa a responsável**.

Conferência somente leitura no PostgreSQL da demonstração, 15432. Incidente OPEN,
UNREVIEWED, versão 1 e zero ações na consulta desta análise. Preservado o servidor
preexistente na 5432, credenciais, cadastros, eventos e filas.

Os 2109 ms medem a janela de evidência aceita, **não a latência desde que a pessoa
realmente deitou**. Esse início físico ainda não foi anotado pelo fundador.

## Observação e incerteza

Predições: 94 ajoelhado/abaixado, 76 sentado, 70 em pé/caminhando, 33 deitado,
27 postura indeterminada, 20 pose insuficiente e 57 sem pose detectada.
São predições do modelo, não descrição confirmada das atividades realizadas.
Os motivos duplicados NO_POSE/MISSING_ESSENTIAL_LANDMARK nas mesmas 57 análises
não devem ser somados como 114 falhas independentes.

A primeira janela positiva vai de **48,422 a 52,406 s** desde a primeira análise;
o evento saiu em 50,531 s. Uma segunda região de predições LYING ocorre entre
**91,547 e 96,203 s**, intercalada com ajoelhado/abaixado e ausência de pose.
Ela não completou a confirmação temporal de um segundo evento. Sem conhecer
o que aconteceu nesse trecho, não classificá-lo como perda nem como acerto.

O fundador informou depois da análise inicial que **deitou aproximadamente três
vezes enquanto aparecia na câmera** e confirmou que a marcação do piso estava
correta. Há um alerta para três tentativas relatadas. São duas possíveis perdas,
sem publicar recall 1/3 antes de confirmar duração, separação e rearme dos episódios.
Foi solicitado quanto tempo ficou em cada posição, se ficou em pé por ≥3 s entre
elas e se mudou a orientação. Não foi pedido para repetir a sessão.

Resposta posterior do fundador: ficou deitado **aproximadamente 5–7 s em cada
tentativa e em pé entre elas**. A duração relatada no chão supera a referência
de 2 s; não atribuir a falta de alerta simplesmente a uma permanência curta.
O tempo em pé e os inícios de cada tentativa não foram quantificados. A sessão
não demonstra os três episódios esperados: um alerta para três tentativas,
duas sem alerta separado. Não alegar precisão/recall estatístico de 33% com
tempos recordados depois das previsões; o resultado funcional é insatisfatório.

Auditoria temporal adicional: primeiro evento em 50,531 s, tentativa de rearme
a partir de 52,578 s, interrompida por incerteza/lacunas. O motor só voltou a
OBSERVING em **71,141 s**. Se alguma tentativa física ocorreu nesse intervalo,
a supressão de novo episódio pode ter influenciado; não atribuir tudo à regra
sem conhecer os tempos físicos. Aos 91,547 s o motor já estava disponível,
mas as predições positivas fragmentadas e a ausência de pose quebraram a janela.
O simples recebimento do primeiro alerta não comprova observação das outras duas idas.

Persistem 106 análises inelegíveis: ausência de pose, descritor insuficiente,
postura incerta ou corpo deitado fora da região. A observação global de 56,72%
é insuficiente para declarar cobertura integral da sessão. Não aplicar uma
métrica de negativos sem antes separar presença, ausência e atividades por
anotação humana; períodos em que o usuário saiu podem ter outro denominador.

Não há filmagem salva para rever a cena; decisões/pontos não permitem confirmar
chão versus cadeira/rede por si sós. Foram solicitadas ao fundador atividades,
durações aproximadas, enquadramento/piso e falhas percebidas. Três idas ao chão
e piso correto foram confirmados; os tempos ainda estão pendentes. São anotações
posteriores ao teste exploratório, não ground truth independente congelado antes
das previsões.

Atualização: durações aproximadas no chão e postura em pé entre as tentativas
foram confirmadas; permanecem desconhecidos os tempos exatos e a duração em pé.
Recibo separado em `.local/detector-evolution/webcam-v3-cf26651e-founder-feedback.json`,
sem reescrever previsões ou registros originais da sessão.

## Próximo passo

1. Confirmar o que aconteceu perto de 50 s e entre 1min30s–1min36s, sem repetir
   fisicamente o teste só para responder. Determinar se o alerta correspondeu
   a pessoa no chão e se houve outra situação-alvo perdida.
2. Abrir o incidente no painel e registrar revisão humana correspondente:
   Postura no chão confirmada, Falso positivo ou Inconclusivo, conforme a cena.
   Não registrar queda quando só foi observada permanência no chão.
3. Relacionar os intervalos observáveis às classes/gaps e preparar a correção
   específica ou o próximo ensaio curto. Manter os requisitos e resultados
   adversos; não reduzir a persistência/qualidade para fazer o teste passar.

Para investigar reconhecimento no cômodo, o próximo material útil é um vídeo
local autorizado e reproduzível, pois observe não gravou a imagem desta sessão.
Com ele será possível comparar imagem, pontos e classe nas três orientações,
sem exigir repetidas sessões LIVE a cada mudança. Preparar a sequência antes
de iniciar; câmera fixa, corpo inteiro/piso, posturas controladas sem queda.
Manter a calibração se a posição da câmera não mudou. A gravação depende de
ação explícita do fundador; nenhuma câmera/gravação foi iniciada por esta análise.

## Comandos desta análise

- Leituras de AGENTS/README/status/roteiro, git status e monitores privados.
- `uv run --offline --project services/edge --frozen python .local/detector-evolution/analyze-latest-v3-webcam.py`:
  métricas, fases, eventos SQLite em modo somente leitura e hashes dos registros.
  Conversão local de horário corrigida no helper após indisponibilidade de tzdata;
  sem instalar dependência ou alterar o detector.
- `node --env-file=apps/api/.env .local/detector-evolution/check-live-v3-session.mjs`:
  incidente/receipt/aviso/revisão consultados em 15432, sem expor credenciais.
- `uv run --offline --project services/edge --frozen python .local/detector-evolution/audit-v3-live-temporal.py`:
  transições, rearme aos 71,141 s e fragmentação da segunda janela auditados.

Auditorias privadas em `.local/detector-evolution/webcam-v3-audit-cf26651e-d20d-412c-b744-fc4c450fc470.json`
e `webcam-v3-cf26651e-api-audit.json`. Código/modelos/lockfiles preservados;
nenhuma câmera aberta, commit, push, deploy ou treino nesta análise.
