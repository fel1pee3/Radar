# Fechamento funcional — candidata corporal/contextual V4

Trabalho de 28–29/10/2026. **PARCIAL; MVP não aprovado.**
Referência inicial: `bd5714ddb4eea18eec8bef51430278ec20405495`, árvore limpa
no início. Nenhuma webcam aberta, treino, mudança de pesos, polígonos, credenciais,
banco de demonstração, commit, push ou deploy.

## Resultado que melhorou

A V4 produz evento nos **16/16 alvos conhecidos**, contra 12/16 da referência.
Recupera a emissão nos quatro casos obrigatórios sem excluir nenhum da matriz.
Isso não equivale a aprovação: dois alertas excedem o prazo registrado,
um alvo reprova por cobertura e quatro controles permanecem inconclusivos.
O resultado completo passa de **27/36 para 29/36**.

Nos quatro vídeos históricos de transição, POSSIBLE_FALL passa de **1/4 para 2/4**
na execução FILE. O restante continua PERSON_ON_FLOOR, sem forçar queda pela
terminação da cena ou nome do arquivo. No fluxo integrado, uma execução real
DirectML chegou a outbox, API, incidente, aviso local e revisão automatizada no
navegador. Não representa revisão humana do fundador.

## Referência, limites e preservação

Raiz privada, identificada por `.local/mvp-closure-current.json`:

`.local/detector-evolution/mvp-closure-2a8307a3-c7c4-4f04-b30c-da511e2a6b9b`

Contém `reference-source.zip`, hashes dos arquivos iniciais, 100 entradas originais
únicas preservadas, protocolo anterior, limites anteriores à inferência,
configurações, matrizes, observações e resultados novos. O congelamento final está
em `candidate-freeze.json`, `frozen-source/`, `protocol-final.json` e
`policy-final.json`.

Fingerprint do código congelado:
`b35255e37b3cfedd5cafc00d79363665be182e55e58fac04c473cf74f8f728f2`
(261 arquivos no cálculo; código sujo, não é um commit).
Pesos RTMO:
`d0703d40d19f3921da51ae725402d5fdae4d2478c7442072d3101bd396f370d8`.
Classificador:
`40d01401851f24cd8c815557970f0dcf42877707afbba38d521ebfa87bd5bd19`.
CPU continua padrão; DirectML permanece opt-in, onnxruntime-directml 1.23.0
isolado, AMD Radeon 1002:15E7, REFERENCE_4_SPIN + RTMO_ADAPTIVE_V3.
Windows 11, Python 3.12.15, Node 24.22.1, pnpm 10.34.7, uv 0.13.4.
Nenhuma mudança de driver, threads, precisão ou runtime nesta candidata.

Os limites foram registrados antes da comparação completa. Uma guarda adicional
exigindo ambos os quadris foi acrescentada para impedir confirmação com sinal de
quadril indefinido no contrato. A reaplicação do código final às **2.187 observações
reais salvas** encontrou zero diferenças de postura, elegibilidade, contexto,
candidatura e motivos; as 36 linhas temporais de eventos mantiveram tipos e horários.
Isso é auditoria de observações, não uma nova inferência. Correções posteriores
de rótulo de versão/escopo e formatação não mudam a decisão. Provas antigas não
foram reescritas para receber esses rótulos novos.

## Causas e implementação

| Caso | Bloqueio observado na referência | Correção/resultado V4 |
| --- | --- | --- |
| floor03 | 13 observações deitado rejeitadas pelo quadril fora da região | Contexto distribuído recupera evento em 5.216 ms; início 0 provisório preservado, prazo registrado reprovado |
| floor05 | 18 observações deitado fora da região; há classificação precoce durante ajoelhamento | Contexto corporal + temporal: evento em 4.816 ms; não tratar previsão precoce como início humano |
| floor07 | 17 observações deitado fora da região | Evento em 4.224 ms, mantendo articulações reais/polígono |
| controlled-lying | 56 observações fora da região; pernas elevadas confundem sentado/deitado | Contexto distribuído e ramo geométrico conservador; evento 8.200 ms, latência anotada 5.200 ms: ainda tarde |
| intake16-08 | Quatro NO_POSE e um UNKNOWN | 77,10% de cobertura; inconclusivo preservado |
| cauca-10 | 13 NO_POSE, quatro UNKNOWN e duas poses incompletas | 64,38%; inconclusivo preservado |
| cauca-12 | Sete NO_POSE e um UNKNOWN | 79,69%; inconclusivo preservado |
| chair08-01 | Dez UNKNOWN apesar de pessoa localizada | 64,42%; ambiguidade do classificador, não problema de transporte |
| cauca-03 | Perda contínua de pose durante a trajetória | Evento de chão, 79,23% de cobertura; transição e cobertura não aprovadas |

`body_context.py` separa suficiência corporal de projeção do quadril.
Aceita pelo menos seis essenciais atuais, ambos os quadris, três pontos de torso
e um lado anatômico completo, com qualidade nativa >=0,5 e geometria válida.
Não inventa a articulação ausente. O contexto pode vir do quadril projetado dentro
ou de três pontos observados, incluindo torso, distribuídos por pelo menos 25%
da diagonal corporal. Um ponto de torso em apoio/exclusão configurada veta a
confirmação de chão. `hipInFloorZone` continua relatando a projeção verdadeira.
Não é interseção de bounding box nem medição física de contato/altura.

Para torso reclinado com ambos os joelhos elevados, há um ramo geométrico explícito:
torso completo, ambos os joelhos acima do quadril por 0,1 da escala corporal,
ângulo >=60°, corpo suficiente e contexto compatível. Aplica-se somente a
UNKNOWN/SEATED e registra origem própria. Não altera scores aprendidos, não
treina com avaliação e não converte todo UNKNOWN em normal. É uma hipótese
desenvolvida em casos conhecidos, ainda sem generalização demonstrada.

`evidence_engine.py` passa a observar movimento também no primeiro segundo
da suspeita, em vez de parar ao primeiro LYING. POSTURE_DYNAMICS_V2 exige suporte
postural anterior de 400 ms, mudança observada em até 1.000 ms, rotação >=35°
e deslocamento normalizado >=0,3. Uma lacuna >500 ms elimina o histórico útil.
Não reconstrói movimento através da ausência de pose. Permanecem persistência
de 2.000 ms, fração válida 80%, cinco observações, rearme de 3.000 ms e proteção
de idade de 2 s. V1 e políticas anteriores continuam disponíveis.

A candidata é `MULTICLASS_CONTEXT_V4`, política
`floor-rtmo-score-posture-context-v4-dev01`, worker `edge-posture-context-v4`.
Configuração, fábrica, relatórios e confirmação explícita de contexto reconhecem
a versão. Transporte/outbox, autenticador, classificação de entrega e limiares
do estimador não foram substituídos.

Uma sondagem limitada de recuperação real testou rotações 90°/270° em quatro
frames problemáticos: **0/8 poses aceitas**. Resultado em
`quarter-turn-probe.json`. Não acrescentamos mais chamadas nem baixamos
confiança para transformar esse resultado em aprovação.

## Comparação funcional completa

| Medida | Referência | V4 |
| --- | ---: | ---: |
| Cenários no denominador | 36 | 36 |
| Alvos com evento | 12/16 | 16/16 |
| Alvos sem evento | 4 | 0 |
| Alvos com evento dentro do prazo registrado | 12 | 14 |
| Aprovações completas | 27/36 | 29/36 |
| Controles aprovados | 16/20 | 16/20 |
| Controles inconclusivos | 4/20 | 4/20 |
| Alertas nos controles | 0 | 0 |
| Duplicações | 0 | 0 |
| POSSIBLE_FALL nas quatro transições históricas | 1/4 | 2/4 |

[Tabela dos 36 cenários](FECHAMENTO_CANDIDATA_V4_REGRESSAO_2026_10_28.csv).
A V4 emite 12 PERSON_ON_FLOOR e quatro POSSIBLE_FALL. Dois destes últimos
são floor05/floor07, sem avaliação independente da trajetória; não somá-los
aos dois acertos de transição CAUCA. A política indica suspeita observada,
não acidente, intenção ou diagnóstico.

Os quatro casos antes perdidos continuam no relatório e as provas de suas perdas
anteriores permanecem intactas. Nos floor03/05/07, o início 0 herdado é provisório:
não foi deslocado para o momento em que o modelo aceitou a pose. O prazo
de controlled-lying continua reprovado. Os dois controles anotados vazios
(intake16-14/15) têm captura de 99,82%/97,94%, sem alertas; não exigimos pose
inexistente nem apagamos a cobertura decisória zero.

## Ritmo real: resultado limitado e erro de preparação preservado

Foram executadas 40 transmissões técnicas FILE a 1×, dez cenários, duas repetições,
ordem alternada, sem HTTP, prévia ou câmera. **A comparação pareada não é válida:**
as configurações históricas da referência selecionavam CPU antes da antiga
substituição experimental de fábrica. Esta rodada inicial executou V3 na CPU
1.23.0 e V4 em DirectML 1.23.0. Isso foi identificado nos metadados efetivos;
não atribuir diferença de custo à correção de contexto.

[Tabela diagnóstica, com essa limitação](FECHAMENTO_CANDIDATA_V4_STREAMS_2026_10_28.csv).
Ela preserva chamadas, processamento, cadência, idade, lacunas, cobertura,
eventos e recursos. Os 20 resultados DirectML da candidata continuam observações
válidas da candidata isoladamente:

- 14 eventos nos 14 ensaios positivos, zero nos seis controles.
- Somente **6/20** atendem simultaneamente timing e cobertura desta tabela.
- Média das médias de processamento: 200,4 ms; maior pico: 709,9 ms.
- Treze lacunas de decisão >500 ms, somadas nas vinte execuções.
- floor03/07 não alcançam 80%; cauca-10 e chair08-01 continuam limitados;
  o vazio reprova critérios operacionais, não por exigir pose.
- Os rótulos POSSIBLE_FALL variam com amostragem; cauca-04 tornou-se
  PERSON_ON_FLOOR nas duas transmissões. A melhora FILE não comprova queda em LIVE.

A referência CPU teve 0/20 nos mesmos critérios, quatro eventos, média das médias
263,4 ms e 88 lacunas; **não é uma comparação GPU V3 × GPU V4**.
Recursos medem processo, não potência GPU; memória de pico inclui inicialização
e páginas compartilhadas. Inicialização e caudas constam dos registros; não se
removeu trecho difícil para aprovar. Latências de transmissão precisam considerar
`readyFromOriginMs`, não somente o offset do arquivo.

O comparador foi corrigido para preparar clones com DIRECTML nos dois lados e
verificar o executor realmente inicializado após cada execução. A repetição em
`streams-gpu-paired` foi tentada em 29/10, mas **não iniciou** pelo bloqueio
do Python descrito abaixo. Não há resultado pareado corrigido nem ganho de
desempenho da V4 demonstrado nesta entrega.

## Integração real e verificações de software

Prova isolada em
`.local/directml-integration-e2e/ccb91e15-e466-4ef8-90d7-00dedaf5f29d/verification.json`.

Positivo intake16-03: 74 decisões, um PERSON_ON_FLOOR; controle chair08-02:
32 decisões, zero eventos. Perfis completos, captura/heartbeat ENDED, zero
pendentes. Profiling ORT comprovou computação DML em ambos, com auxiliares CPU.
Um incidente REPLAY/TEST, um aviso; reenvio retornou duplicate=true sem duplicar
recibo/incidente. Revisão **AUTOMATIZADA DE TESTE**, versão 2, recuperada após reload.
ID de teste: `6a33b750-fd3c-420b-9914-981181ac2369`; banco exclusivo removido
pelo encerramento do teste, sem alteração da demonstração.

| Comando/ação realmente executado | Resultado |
| --- | --- |
| `uv run --project experiments/directml --frozen python scripts/validation/run-candidate-regression.py --protocol <raiz>/matrix-protocol.json` | 36 inferências FILE completas; 29 aprovações |
| `uv run --project experiments/directml --frozen python scripts/validation/compare-candidate-streams.py --candidate-root <raiz> --reference-root .local/detector-evolution/directml-integration-757f4105-e1ad-46ca-8efb-995ad297eb3e --output <raiz>/streams-final` | 40 completas; comparação invalidada por executor desigual, provas preservadas |
| Mesmo comando com saída `streams-gpu-paired` após correção | Não iniciou: Python bloqueado pelo Windows |
| `uv run --project services/edge --frozen pytest services/edge/tests experiments/directml/tests -q` | Primeira consolidada 503 pass/1 skip; após novos testes, 510 pass/1 falha de fixture/1 skip |
| `uv run --project services/edge --frozen pytest services/edge/tests/test_body_context_v4.py services/edge/tests/test_worker_operation.py services/edge/tests/test_posture_context.py -q` | 19 passaram após corrigir a fixture de escala: calibração precisava acompanhar a geometria |
| `node --test scripts/validation/release-evidence.test.mjs` | 7 passaram |
| `pnpm.cmd test:contracts` | 104 TypeScript e 104 Python passaram |
| `pnpm.cmd test:api` | 161 passaram em PostgreSQL exclusivo |
| `pnpm.cmd test:e2e --grep 'DirectML real FILE' --project desktop`, RADAR_DIRECTML_PROTOCOL apontando à matriz V4 | 1 passou; build API/contratos/Next e integração real |
| `pnpm.cmd typecheck` | Passou |
| `pnpm.cmd lint` | Primeira falhou por formatação; corrigida, repetição passou |
| `pnpm.cmd lint:edge` | Passou; Ruff final direto: 100 arquivos formatados e check aprovado |
| Preparador `prepare-directml-demo.py` com base V4 e `--duration 600` | Configuração nova preparada; câmera/HTTP não executados |
| `read-api.mjs` anterior com novo nome de saída | DATABASE_READ_UNAVAILABLE; nenhuma revisão humana confirmada agora |
| `pnpm.cmd demo:check --evidence <raiz>/release-evidence.json --engineering-evidence <raiz>/engineering.json` | Exit 1, releaseReady=false por provas reprovadas/pendentes |
| Parser PowerShell de `observe.ps1` e `git diff --check` | Sem erros de sintaxe/whitespace |

`<raiz>` é somente abreviação do caminho privado completo acima, não argumento
literal usado. Logs preservados em `python-tests.log`, `python-final.log`,
`python-correction.log`, `checker-tests.log`, `contracts.log`, `api.log`,
`e2e.log`, `lint.log`, `lint-final.log`, `typecheck.log`, `edge-lint.log`.
A falha da fixture não foi escondida: os 19 testes afetados passaram após a
correção; a suíte inteira não foi repetida sem necessidade. Não dizer que uma
nova suíte integral passou após o bloqueio do Windows.

## Bloqueio novo do ambiente, 29/10

O Python CPU e DirectML passaram a encerrar com **-1058471934 (0xC0E90002)**
antes de executar `print`. Eventos Windows Code Integrity **3033/3077**,
às 11:02–11:03 de 29/10, identificam:

`C:\Users\VAIOFE16-Felipe\AppData\Roaming\uv\python\cpython-3.12.15-windows-x86_64-none\python312.dll`

O registro afirma que a DLL não satisfaz a política de assinatura
`{0283ac0f-fff1-49ae-ada1-8a933130cad6}`. Evidência salva em
`windows-code-integrity-block.json`. Causa comprovada: recusa de carregamento
pela política do Windows. Não foi determinado quem alterou/aplicou a política
nem qual produto administrativo a controla. Não atribuir isso ao modelo ou GPU.

Não alteramos segurança, não contornamos a política e não substituímos Python/
ambientes para ocultar o problema. A próxima ação de ambiente é o responsável
pela política do Windows verificar esses eventos e autorizar legitimamente a
distribuição Python usada pelo projeto. Não desative proteção globalmente.
Depois da resolução, verificar nos dois ambientes:

```powershell
. ./scripts/activate.ps1
uv run --project services/edge --frozen python -c "import sys; print(sys.version)"
uv run --project experiments/directml --frozen python -c "import sys; print(sys.version)"
```

Só então retomar a comparação pareada corrigida. O código está preparado;
a execução corrigida permanece pendente, não aprovada.

## Verificador e operação

O checker passou a ler comprovantes/hash/versão em vez de manter gates fixos.
Distingue APROVADO, REPROVADO, PENDENTE, DESATUALIZADO e DISPENSADO; calcula
engenharia e funcional separadamente. D50 dispensa apresentação; D51 mantém
600 s nominais. A falha antiga aos 27min45s continua registrada.

Resultado atual: regressão e transições REPROVADAS; independente, físico,
offline e recuperação da nova candidata PENDENTES; apresentação DISPENSADA.
Engenharia tem verificações pertinentes aprovadas, provas abrangentes antigas
DESATUALIZADAS e ambiente Python REPROVADO pelo bloqueio atual. Não repetimos
instalação limpa/backup por cada ajuste e não fabricamos vínculo com a versão nova.

`observe.ps1` agora seleciona ambiente pelo executor configurado.
O preparador aceita 60 ou 600 s, preserva a configuração anterior e aumenta
somente a quota limitada de diagnósticos para a sessão longa (50 MiB por arquivo,
100 MiB por diretório, 10.000 registros). Não muda qualidade, cadência ou timers.
Nenhum vídeo/snapshot habilitado. Configuração pronta em
`<raiz>/physical-600/config.yaml`; não foi executada.

[Comandos completos de API, painel, candidata e revisão](../USO_CANDIDATA_V4.md) ·
[Formato dos comprovantes](../VALIDACAO_EVIDENCIAS.md).

A revisão humana anterior permanece sem confirmação atual: última prova
READ ONLY bem-sucedida dizia UNREVIEWED para
`3f8db408-fbb1-4286-ad75-be8e9a3ce57a`.
A nova consulta falhou; não presumir que ainda está ausente nem que foi salva.
Quando a bancada estiver disponível, conferir esse incidente pelo histórico.

## Dados novos e decisão de continuidade

Inventário privado: 59 arquivos locais; 36 hashes correspondem à matriz.
Nenhum lote foi certificado como reserva nova por hash, gravação e participante.
CAUCAFall, os 16 clipes e recortes de yoga já participaram de desenvolvimento;
os outros arquivos não ganharam o rótulo de independentes por estarem fora da matriz.

Faltam uma reserva nova de quatro cenas-alvo e oito atividades comuns, com
intervalos humanos e procedência, mais avaliação separada de transições.
O roteiro físico de 600 s, revisão do fundador e confirmação offline dependem
da participação humana, mas **não são as únicas pendências**.

Ainda há trabalho técnico: a comparação GPU pareada está bloqueada; cobertura
de pose falha em controles, duas transições não têm evidência suficiente e
controlled-lying ultrapassa o prazo. A tentativa contextual corrigiu rejeições
indevidas do quadril; as rotações extras não recuperaram os frames sondados.
A ausência de articulações durante a trajetória não pode ser corrigida
prolongando evidência ou nomeando o vídeo como queda. A classificação de cadeira
segue ambígua mesmo com pessoa localizada. Esses são bloqueios perceptuais
específicos, não problemas de entrega ao painel.

Não promover V4 nem avançar automaticamente para modelo diferente ou novo
ensaio físico. Primeiro desbloquear o Python pela via legítima e concluir
a comparação corrigida; depois decidir a próxima correção sobre as causas
remanescentes, preservando estas falhas. O MVP funcional solicitado permanece
**não concluído**, apesar da melhora real de detecção nos arquivos.
