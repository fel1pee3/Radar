# Candidata de contexto V4 — uso e fechamento

28–29/10/2026. **Experimental, não aprovada como MVP.** CPU e V3 continuam disponíveis
sem mudança do padrão. A V4 usa os mesmos pesos RTMO, classificador e recuperação
ADAPTIVE_V3; muda contexto corporal e avaliação da trajetória. Os resultados
da matriz conhecida são desenvolvimento, não avaliação independente.

[Resultados e bloqueios](RELATORIOS/FECHAMENTO_CANDIDATA_V4_2026_10_28.md).

**Bloqueio atual de ambiente (29/10):** o Windows está recusando carregar
python312.dll nos dois ambientes. Não execute o ensaio físico agora.
O responsável pela política de segurança precisa verificar os eventos Code
Integrity 3033/3077 e autorizar legitimamente o Python do projeto; não desative
proteção global. Os comandos abaixo ficam preparados para depois da resolução.

## Iniciar serviços

Na raiz do projeto, em cada terminal novo, execute a ativação.

Terminal 1:

```powershell
. ./scripts/activate.ps1
pnpm.cmd setup:env
pnpm.cmd infra:up
pnpm.cmd dev:api
```

Terminal 2:

```powershell
. ./scripts/activate.ps1
pnpm.cmd dev:web
```

Entre com a conta existente em http://127.0.0.1:3000. Não recrie proprietário,
câmera, credencial nem banco.

## Configuração física preparada, sem execução nesta entrega

Há uma configuração **nova**, com limite nominal de 600 segundos, HTTP local
habilitado, evidência corporal e sem vídeo/snapshot. A configuração antiga
de 60 s e suas provas foram preservadas. O piso ainda precisa corresponder ao
enquadramento no momento do uso. Não use esta candidata como monitoramento assistencial.

Somente quando optar por abrir a webcam, em outro terminal:

```powershell
. ./scripts/activate.ps1
$rodada = (Get-Content .local/mvp-closure-current.json -Raw | ConvertFrom-Json).root -replace '\\', '/'
$configV4 = "$rodada/physical-600/config.yaml"
powershell -NoProfile -File scripts/validation/observe.ps1 -Config $configV4
```

O observador lê a configuração e seleciona `experiments/directml` explicitamente.
A leitura inicial pelo ambiente CPU apenas valida YAML; não abre a fonte nem executa
o modelo. DirectML indisponível resulta em erro explícito, sem fallback silencioso.
O launcher normal também pode ser usado, sem a medição adicional de recursos:

```powershell
uv run --project experiments/directml --frozen python scripts/run-edge.py run --config $configV4
```

Use apenas um dos dois comandos de execução por vez. Não abra duas capturas.
O timer inclui inicialização. A análise em andamento e o fechamento podem ultrapassar
ligeiramente 600 s. Q/Esc na prévia encerra antes; esse resultado não comprova
os dez minutos completos. Perfis e estado final devem ser conferidos no relatório.

## Roteiro e observação

1. Confira piso, móveis excluídos e corpo inteiro na prévia; enquadramento alterado
   exige nova calibração antes da avaliação.
2. Permaneça em pé. Deite voluntariamente, devagar e em área segura, sem provocar
   queda; permaneça no chão por 15–20 s.
3. Levante com calma e permaneça em pé por pelo menos cinco segundos para permitir
   o rearme. Complete a sessão com atividades comuns, incluindo sentar e caminhar.
4. Ao terminar, confira **Fonte encerrada**, abra o incidente pelo horário/câmera,
   verifique **Ao vivo** e registre sua **Revisão humana**, descrevendo o que ocorreu.
   Recarregue e confira a ação no histórico e o aviso em **Avisos locais**.

Um clique antes de caminhar até o chão não é o início da postura. Sem observador
independente registrando o momento em que a pessoa já estava deitada, a latência
humana fica inconclusiva. Não habilitamos gravação para obter essa marcação.
A persistência interna de 2 s não é a latência humana.

Não apague a outbox para repetir. O estado persistente evita duplicar o episódio;
o período em pé permite rearme. Relatórios ficam em
`$rodada/physical-600/results/<UUID>/report.json`, outbox em
`$rodada/physical-600/outbox.sqlite`, recursos em
`.local/etapa08/continuous-<UUID>/`. Esses dados são privados.

## Critérios e provas ainda necessárias

Aplicar ao horizonte inteiro: cobertura elegível >=80%, intervalo de observação
<=500 ms, idade de decisão <=2 s, alerta <=5 s do início humano anotado, um incidente
por episódio, rearme, nenhuma duplicação, aviso local e revisão persistida.
Separar captura de decisão; nos controles realmente vazios, usar disponibilidade
da captura e ausência de alertas, sem exigir pose inexistente.

O teste físico não corrige as reprovações em arquivos. Não o trate como próximo
passo suficiente para aprovar o MVP enquanto os bloqueios do relatório persistirem.

A recuperação/transporte tem testes automatizados, mas a nova versão precisa de
prova vinculada de indisponibilidade da API e retomada. Quando realizada, pare somente
a API da bancada, preserve o worker/outbox, reabra a API e confira um recibo/incidente/
aviso por episódio e pendentes zerados. Não derrube PostgreSQL nem remova volumes.
Para o teste sem internet, mantenha API, painel, banco e modelos locais disponíveis;
desconecte somente internet, execute um replay autorizado e confira o painel antes
de reconectar. Registre o que foi efetivamente feito, sem simular confirmação humana.

## Material reservado

Os 36 cenários medidos já foram usados em desenvolvimento. Clipes da mesma sessão
ou do mesmo participante não tornam uma avaliação independente. Os vídeos longos
de yoga e demais mídias antigas também já foram inspecionados/utilizados; não foram
reclassificados como reserva.

Para a avaliação final, faltam uma reserva nova de quatro cenas de pessoa já no chão
(em orientações variadas), oito atividades comuns/confundidoras e uma avaliação
separada das transições observadas. Registrar origem/autorização, hash, gravação,
participante, intervalo humano da postura e piso/apoios antes de rodar o candidato
congelado. Não provocar quedas: usar cenas autorizadas já existentes para transições.
Sem essa referência, não inferir a atividade real a partir das classes do detector.

## Verificador

```powershell
. ./scripts/activate.ps1
$rodada = (Get-Content .local/mvp-closure-current.json -Raw | ConvertFrom-Json).root
pnpm.cmd demo:check --evidence "$rodada/release-evidence.json" --engineering-evidence "$rodada/engineering.json"
```

Saídas: **0** escopo solicitado aprovado; **1** reprovação/falha;
**2** pendência ou prova desatualizada. `--engineering` avalia somente engenharia;
não aprova percepção nem a release funcional.

Os comprovantes são JSON locais com SHA-256, versão de código, configuração,
modelo, classificador, política e protocolo. Há estados APROVADO, REPROVADO,
PENDENTE, DESATUALIZADO e DISPENSADO. Apresentação formal está DISPENSADA por D50;
o teste histórico de 30 min que parou em 27min45s permanece registrado.
O checklist não inventa revisão humana ou usa testes unitários como prova perceptual.
[Formato das evidências](VALIDACAO_EVIDENCIAS.md).
