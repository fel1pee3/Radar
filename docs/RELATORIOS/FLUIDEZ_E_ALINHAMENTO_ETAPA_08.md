# Investigação da fluidez e do alinhamento — etapa 08

23/10/2026, America/Sao_Paulo. **PARCIAL. Candidatos visuais não adotados no
worker operacional.** Sem webcam, treinamento, modelo novo, envio de vídeo,
mudança de política, credencial, calibração, outbox original, commit ou deploy.

## Conclusão

A prévia operacional permanece limitada à cadência de análise, cerca de 5 Hz.
Ela só chama `LocalPreview.show` após inferir um quadro. O RTMO-s neste adaptador
estima quadros independentemente, sem rastreamento temporal das articulações.
Isso separa duas limitações: cadência de exibição e qualidade da localização.
Aumentar a resolução não foi testado como solução e não foi presumido necessário.

Foi implementada uma comparação reproduzível com quadros intermediários e
acompanhamento por fluxo óptico. O vídeo fica mais contínuo, mas a auditoria
detectou perdas de segmentos. Uma segunda abordagem por vizinhança também não
resolveu o problema de forma consistente. **Nenhuma foi ativada na webcam ou
usada como evidência do detector. Não foi comprovada melhora geral de precisão.**

O próximo uso desses artefatos é revisar alinhamento e falhas em trechos concretos,
não aprovar uma substituição por aparência. Continuam faltando anotações
independentes de posição/visibilidade para medir precisão anatômica. Modelos
podem errar mesmo com score suficiente, como o Full havia feito na cadeira.

## Conferência humana e diagnóstico do piscar — complemento de 23/10

O fundador assistiu à comparação da cadeira 2 e confirmou maior fluidez à
direita. Não confirmou alinhamento anatômico: o esqueleto some/reaparece e
dificulta essa avaliação; também observou poucos traços verdes. Isso encerra
a pendência de assistir à comparação, mas **não aprova o candidato visual**.

Uma instrumentação privada observou o rastreador sem alterar seus resultados:
em todos os quadros dos seis clipes, pontos, cores e idade foram iguais aos
da classe original, executada em paralelo no mesmo processo. Observações
originais conservaram seus hashes. Não houve câmera, inferência ou HTTP.

Na cadeira 2, **32/32 âncoras têm os 12 pontos corporais aceitos para desenho**.
Isso não comprova que estejam na posição anatômica correta. Entre elas, 74/155
quadros perdem pelo menos um ponto: 191 pontos-quadro ausentes de 1860 possíveis.
Das ausências, 49 são reprovação somente pelo erro ida/volta, três combinam esse
erro e o fotométrico, e 139 são a permanência da ausência até a próxima âncora.
Contagens exclusivas por ponto-quadro; não são 191 articulações diferentes.
O código remove as linhas ligadas ao ponto e só o reintroduz na próxima âncora.
Essa é uma causa demonstrada do piscar **nesta comparação**, sem provar a causa
de todo desaparecimento na webcam ou em outros vídeos.

Há zero quadros totalmente sem linhas na cadeira 2: trata-se de segmentos
desaparecendo, mesmo quando a impressão visual é de o esqueleto apagar.
Nos seis clipes instrumentados, a origem também varia: `floor05` teve duas
âncoras sem pontos utilizáveis; `floor07`, quatro. Portanto, não se deve
atribuir toda falta de ponto ao acompanhamento visual.

Os poucos traços verdes decorrem da legenda implementada: na cadeira 2, 102
pontos-quadro foram classificados MODEL e 1951 FLOW. Até uma posição de âncora
ajustada é classificada FLOW; entre âncoras, toda posição acompanhada é ciano.
A cor não mede precisão e o predomínio de ciano não indica, sozinho, defeito.

Foi testada uma terceira alternativa privada: calcular o deslocamento da
última imagem analisada diretamente para a imagem atual, permitindo nova
tentativa após uma falha intermediária. Mesmos limites de 250 ms, ida/volta
1,5 px, erro fotométrico 20 e sem carregar pontos rejeitados pela âncora atual.
O uso de duas imagens e os retornos status/err seguem a
[API oficial do OpenCV](https://docs.opencv.org/4.13.0/dc/d6b/group__video__track.html).
É hipótese experimental; a API não garante acompanhamento de articulações.

| Método | Pontos-quadro retidos / 42111 potenciais | Quadros intermediários com perdas / 3805 | Cadeira 2 com perdas / 155 |
| --- | --- | --- | --- |
| Sequencial anterior | 39409 | 1094 | 74 |
| Diretamente da última âncora | 37041 | 1380 | 87 |

Executados os mesmos 20 clipes/4581 quadros CALIBRATION. Zero pontos fora do
conjunto aceito na última âncora, expirados ou não finitos mostrados em ambos.
Isso verifica limites de estado; não determina localização correta do corpo.
O candidato direto piorou o conjunto e a cadeira 2: **não adotado**. Não se
reduziram limiares nem se mantiveram coordenadas congeladas para esconder perdas.
Não foi gerada outra prévia para pedir aprovação de um resultado já desfavorável.

Comandos adicionais realmente executados, todos exit 0:

```powershell
. ./scripts/activate.ps1
uv run --offline --project services/edge --frozen python .local/etapa08/diagnose-flow-flicker.py
uv run --offline --project services/edge --frozen python .local/etapa08/measure-anchor-flow.py
uv run --offline --project services/edge --frozen pytest services/edge/tests/test_visual_tracking.py services/edge/tests/test_preview_comparison.py -q
git diff --check
```

Diagnóstico: seis clipes, sem divergência da instrumentação. Comparação: 20
clipes; 13 regressões direcionadas passaram em 0,43 s. Nenhum código operacional
ou dependência foi alterado nesta rodada; a verificação geral de 302 testes
da rodada anterior continua identificada pelo mesmo fingerprint. O novo
experimento permanece somente em `.local`, sem integração ou aprovação LIVE.

Artefatos privados:

- `flicker-diagnosis-a6e64093-99cf-4058-9ec0-c4db8ce303ea/`: resumos e motivos
  por ponto/quadro; `flicker-diagnosis-latest.json` aponta para o diretório.
- `anchor-flow-3870b1a2-6527-49ba-8349-4a568a253841/summary.json`: comparação
  dos 20 clipes; `anchor-flow-latest.json` aponta para o diretório.
- `diagnose-flow-flicker.py`, `anchor-flow.py`, `measure-anchor-flow.py`:
  scripts privados de reprodução, sem mídia incorporada.

## Pesquisa e hipótese original

O [tutorial oficial do OpenCV](https://github.com/opencv/opencv/blob/5.x/doc/tutorials/others/optical_flow.markdown)
descreve o acompanhamento de pontos entre imagens com Lucas–Kanade. A hipótese
testada foi acompanhar brevemente somente os pontos corporais já aceitos pelo
modelo, validando ida/volta e erro fotométrico. Não há novo reconhecimento de
pessoa entre âncoras; tecido, fundo e móveis podem produzir deslocamentos ambíguos.

Também foi consultado o [1€ filter dos autores](https://github.com/casiez/OneEuroFilter/blob/main/README.md),
que combina redução de oscilação com resposta adaptativa à velocidade. Não foi
implementado nesta rodada nem tratado como correção de articulação errada ou
oculta. Não foram baixados novos pesos nem usadas tabelas de outros equipamentos
para atribuir desempenho ao notebook.

## Implementação de validação

- `services/edge/src/radar_edge/visual_tracking.py`: candidato isolado de fluxo
  piramidal esparso. Produz `VisualPoints`, sem confidence/visibility e sem
  capacidade de produzir eventos. Não é importado pelos laços FILE/LIVE normais.
- `scripts/validation/compare-preview.py`: aceita apenas FILE autorizado,
  confere hashes do vídeo/modelo, câmera, tempo, pixels e calibração de cada
  quadro analisado. Usa observações já gravadas, sem nova inferência ou HTTP.
  Não permite WEBCAM. Renderiza lado a lado a prévia por quadros analisados e
  uma estimativa visual nos quadros intermediários. Vídeos/imagens só em `.local`.
- Dois arquivos de regressão cobrem movimento conhecido, ausência/baixa confiança,
  múltiplas poses, troca de fonte, expiração, mudança de geometria/relógio,
  limites de ajuste, preservação do dado bruto e rejeição de fonte/relatório errado.

Verde representa coordenada atual do modelo no seu próprio quadro. Ciano é
estimativa visual, explicitamente fora do detector. Não foi inventado score para
ponto acompanhado. Uma âncora atual que rejeita/omite um ponto o remove de imediato.
Pontos ausentes não são preenchidos, e não sobrevivem à indicação de múltiplas poses.

Parâmetros experimentais: no máximo 250 ms desde a última âncora, erro ida/volta
até 1,5 px, erro fotométrico até 20, janela 21×21/3 níveis, pré-processamento
Gaussian 5×5 sigma 0,8 somente no cálculo visual. Âncoras só são ajustadas quando
a diferença é até 8 px; ajuste final limitado a 4 px (tolerância de ponto flutuante).
Erros maiores usam a observação atual. Mudanças de fonte/geometria/tempo limpam
o estado. Memória de tempos limitada às últimas 1024 chamadas.

Há uma mistura limitada de posição prevista/corrente para reduzir oscilação;
ela é sempre rotulada como estimativa visual, nunca como nova observação real.
Isso não determina se a pessoa precisa de ajuda e pode manter erro anatômico
da âncora. Não resolve a perda de pose no estimador ou a geometria quadril/ROI.

## Material e resultados

Foram reutilizados os **20 clipes CALIBRATION** da comparação nativa anterior,
incluindo as duas cadeiras, os três perdidos no piso e o positivo histórico.
Não são cenas novas nem avaliação independente. Hashes/caminhos de origem
permanecem nos relatórios anteriores; pixels/tempos de todas as 776 âncoras
foram conferidos. Nenhum novo evento foi enviado ou criado por esta ferramenta.

Total: 4581 quadros decodificados, 776 âncoras, 3805 quadros intermediários.
Cadência da mídia entre 29,66 e 29,89 quadros/s. No segundo vídeo de cadeira:
187 quadros/6,272 s, com 32 âncoras; cadências 29,66 e 4,94 por segundo.
Isso é **replay a partir de análises já disponíveis**, não comprova que o
pipeline de webcam consiga mostrar/inferir essa quantidade de quadros em tempo real.
O laço operacional continua síncrono e não foi substituído.

Tempo médio do cálculo de fluxo por clipe: 1,52–1,90 ms no ensaio final,
OpenCV com duas threads neste processo de pesquisa. Exclui inferência e
transporte, não representa latência LIVE nem consumo de CPU do sistema inteiro.
Seis vídeos comparativos foram reabertos e decodificados até o fim; contagens
277/187/176/174/153/269 coincidiram com os quadros renderizados.

### Auditoria de pontos intermediários

| Método | Pontos-quadro acompanhados / potencialmente disponíveis pela última âncora | Quadros intermediários com pelo menos uma perda / 3805 |
| --- | --- | --- |
| Fluxo por ponto, sigma 0,8 | 39409 / 42111 | 1094 / 3805 |
| Mediana de vizinhança de nove amostras | 38933 / 42111 | 1100 / 3805 |

Esses denominadores medem disponibilidade visual em relação à âncora anterior,
**não são recall, precisão anatômica ou número de pessoas corretamente seguidas**.
Os quadros sem pontos elegíveis na âncora não entram como pontos potenciais.
Em ambos: zero pontos carregados após rejeição da âncora e zero pontos exibidos
depois do limite de 250 ms; isso testa regras de estado, não ausência de pontos
em móveis. O segundo método exigiu ao menos cinco amostras consistentes ao redor
da articulação; ainda assim piorou a disponibilidade nas duas cadeiras.
Exemplos: cadeira 2 teve perdas em 74/155 quadros intermediários no primeiro
método e 83/155 no segundo. Esse resultado impede declarar que a queixa de
segmentos desaparecendo foi corrigida. Candidato por vizinhança permanece privado.

### Movimento sintético com posição conhecida

90 quadros por cenário, imagens texturizadas de 320×240; não são poses humanas.

| Cenário | Quadros acompanhados / 90 | RMSE quadro anterior mantido (px) | RMSE acompanhado (px) |
| --- | --- | --- | --- |
| Estático, ruído sintético nas âncoras | 90 | 3,11 | 2,65 |
| Translação, sem pré-processamento | 59 | 5,75 no total; 4,02 nos mesmos 59 quadros | 2,50 nos 59 quadros |
| Translação, sigma 0,8 | 90 | 5,75 | 2,64 |

O teste inicial sem blur perdeu 31 quadros e foi preservado. Comparar RMSE
entre conjuntos de quadros diferentes seria enganoso; por isso há denominador
e baseline correspondente aos mesmos 59 quadros. O pré-processamento recuperou
esse cenário sintético, mas não eliminou as perdas nos vídeos reais. Não foi
medido erro de posição em pixels de pessoas com ground truth independente.

## Comandos realmente executados e artefatos

```powershell
. ./scripts/activate.ps1
uv run --project services/edge --frozen python .local/etapa08/run-flow-comparison.py
uv run --project services/edge --frozen python .local/etapa08/measure-flow-synthetic.py
uv run --project services/edge --frozen python .local/etapa08/audit-flow.py
uv run --project services/edge --frozen python .local/etapa08/run-patch-comparison.py
uv run --project services/edge --frozen pytest services/edge/tests/test_visual_tracking.py services/edge/tests/test_preview_comparison.py -q
$env:RADAR_TEST_GUI = '1'
uv run --project services/edge --frozen pytest services/edge/tests -q
pnpm.cmd demo:verify
pnpm.cmd demo:check --engineering
pnpm.cmd demo:check
git diff --check
```

Resultados: comparação final 20/20 executada, hashes das observações preservados;
13 testes direcionados e 302 Python completos aprovados, sem skip. Variante
privada por vizinhança também passou nos oito testes de ciclo de vida; isso não
compensa sua pior disponibilidade nos vídeos. Ruff foi executado também sobre
o script Python em `scripts/validation`, além de `services/edge`.

`demo:verify`: exit 0, 14 tarefas, incluindo 302 Python, 155 API, 100 contratos TS,
20 E2E, quatro testes do simulador, frozen, lint/tipos/build/imports, backup/restore
e instalação limpa isolados. Código avaliado, 177 arquivos:
`7927d913436cd52cc7cbcf330ec01a845f31cf8e79cd58b5a5d931810d2a142f`.
`demo:check --engineering` exit 0; `demo:check` exit 2 pelos gates manuais.
Evidência anterior preservada em `engineering-before-flow-<id>.json`.

Também executada a interface CLI pública com `--config` da cadeira 2,
`--report` correspondente, `--output` novo e `--video`; exit 0. Argumentos
exatos em `.local/etapa08/flow-cli-check-latest.json`. A primeira chamada revelou
que o campo do relatório era `model.id`, não `modelId`; corrigido e coberto por
testes de identidade do modelo/vídeo/câmera. Não foi falha do worker operacional.

Artefatos finais privados:

- `.local/etapa08/flow-comparison-7fde9b9b-44a0-4b47-9d40-676fbe6d55c1/`:
  20 relatórios, imagens e seis comparações MP4.
- `flow-point-audit-single.json`, `flow-point-audit-patch.json`:
  auditorias por clipe, com perdas incluídas.
- `flow-synthetic-measurements.json`, `flow-video-check.json`:
  movimento conhecido e verificação dos vídeos gerados.
- `patch-flow-comparison-35ba80a9-bf15-462d-9ac9-14abf58e035f/`:
  variante alternativa mantida separada, não adotada.
- `pose-fluidity-baseline-latest.json`: cópias da implementação e evidência
  anteriores para comparação. Nenhum arquivo original foi substituído.

## Como conferir a comparação

Na raiz, com as ferramentas ativadas:

```powershell
. ./scripts/activate.ps1
powershell -NoProfile -File .local/etapa08/preview-flow.ps1
```

Abre somente um vídeo privado já gerado, começando pausado. Espaço reproduz,
R repete e Q/Esc encerra. Esquerda: quadros analisados da prévia anterior;
direita: candidato visual com ciano. A finalidade é localizar falhas, não
pedir aprovação de segurança ou de integração. `-Case chair01` e os casos
`floor03`, `floor05`, `floor07`, `legacy07` permitem conferir outros trechos.

A comparação da cadeira 2 foi aberta pelo agente com esse helper em processo
oculto de lançamento; janela nativa `Radar - comparacao fluidez - REPLAY experimental`
confirmada, iniciando pausada. Logs em `viewer.log`/`viewer-errors.log` no diretório
final e registro em `.local/etapa08/flow-preview-launch.json`. A abertura da
janela, isoladamente, não equivale à revisão humana. O fundador posteriormente
confirmou maior fluidez, com piscar que impede confirmar alinhamento; diagnóstico
e decisão de não adotar registrados no complemento acima.

Para gerar outra comparação, usar o script público com `--config`, `--report`,
`--output` novo dentro de `.local` e, se desejado, `--video`. Sem `--show` não
abre janela; nunca aceita fonte WEBCAM.

## O que não foi resolvido

Desaparecimento e erro anatômico na estimativa real, três perdas no piso,
avaliação independente, prova contínua de 30 min e apresentação final continuam
pendentes. Não há nova captura, novo incidente real, treino, elevação automática
de FPS de análise ou liberação da etapa. Ativar o acompanhamento na webcam
exigiria separar exibição da inferência, medir atraso real e comprovar que
não associa o esqueleto a outro quadro/pessoa; essa mudança não foi feita.
