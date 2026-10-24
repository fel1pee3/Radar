# CAUCAFall — avaliação reservada da etapa 08

23/10/2026, America/Sao_Paulo. **Primeira avaliação congelada executada: três
de quatro alvos detectados, uma perda, zero alertas nos oito ADL. Etapa 08
PARCIAL; percepção limitada, sem aprovação geral de eficácia.** Arquivos recebidos em
`.local/videos/Radar_CAUCAFall_12_Videos`, incluindo README, CSV, provenance.json
e duas imagens de conferência. Originais preservados, sem publicação/treinamento.

## Resultado da primeira avaliação congelada

O fundador confirmou novidade do material, as quatro cenas/faixas e os oito
confundidores antes da inferência. Sobre o piso, confirmou que os 12 estavam
bons, observando pequenos detalhes que poderiam ficar mais precisos. Isso foi
registrado como aprovação da proposta, sem alegar segmentação perfeita.
Registro vinculado aos hashes em human-review.json. Calibração executável criada
somente depois dessa resposta; nenhum ponto/limiar/modelo foi ajustado após
consultar as previsões.

Comando privado run-cauca-evaluation.py terminou exit 0. Todos os 12 pipelines
ok/ENDED: 2876 quadros decodificados, 722 analisados e 2154 pulados por amostragem.
Foram três eventos PERSON_ON_FLOOR, zero POSSIBLE_FALL, zero duplicações e
zero alertas fora dos alvos. As três emissões correspondem a três dos quatro
intervalos-alvo; o quarto é uma perda, não um inconclusivo apagado da contagem.
Resultados por kind e suplemento de postura coincidem nesta execução.

| Arquivo | Análises | Observado (ms) | Elegível (ms) | Resultado/offset de emissão |
| --- | ---: | ---: | ---: | --- |
| FallSittingS5.avi | 58 | 11400 | 10200 | Detectado, 5000 ms |
| FallBackwardsS7.avi | 63 | 12400 | 12400 | Detectado, 6800 ms |
| FallLeftS9.avi | 52 | 10200 | 8200 | Perdido, nenhum evento |
| FallLeftS10.avi | 53 | 10400 | 7800 | Detectado, 7000 ms |
| WalkS5.avi | 57 | 11200 | 11200 | Sem alerta |
| WalkS10.avi | 56 | 11000 | 9600 | Sem alerta |
| SitDownS5.avi | 65 | 12800 | 11200 | Sem alerta |
| SitDownS10.avi | 59 | 11600 | 8200 | Sem alerta |
| PickupobjectS5.avi | 68 | 13400 | 9000 | Sem alerta |
| PickupobjectS10.avi | 73 | 14400 | 7600 | Sem alerta |
| KneelS5.avi | 52 | 10200 | 7000 | Sem alerta |
| KneelS10.avi | 66 | 13000 | 5200 | Sem alerta |

Denominadores: quatro episódios-alvo, três detectados, um perdido; três alertas,
três associados a alvos. Nenhuma duplicação. Nos oito ADL: zero alertas em
69000 ms elegíveis de 97600 ms observados, com 1200 ms adicionais de caudas
sem amostra. Esse período é curto e tem cobertura incompleta; não é demonstração
de taxa geral nula de falsos alertas. Recall de queda real e necessidade de ajuda
não estimáveis. Nenhum rótulo POSSIBLE_FALL emitido nesta amostra.

No conjunto: 142000 ms observados e 107600 ms elegíveis, 34400 ms inelegíveis
para o algoritmo e 1800 ms de caudas não amostradas. Os 722 estados de inferência
foram 596 ONE_VALID_POSE, 110 NO_POSE e 16 LOW_CONFIDENCE. Motivos de
inelegibilidade podem se sobrepor; não somar suas contagens como pessoas/tempo.
As caudas e os períodos inelegíveis não foram descartados do relatório.

Latência a partir dos inícios anotados: 1000, 1800 e 4000 ms. Onsets têm incerteza
de até 500 ms; valores não medem socorro ou exibição no painel. Sem HTTP/ingestão,
latência de transporte/painel não foi medida neste ensaio. Os três eventos ficaram
em SQLite local de avaliação; não foram criados três incidentes no banco pessoal.

Tempo de parede acumulado dos 12 pipelines 137,92 s; CPU acumulada 529,22 s,
média ponderada de inferência 168,26 ms. CPU equivale a 383,72% de um núcleo,
incluindo threads nativas; não 383% da máquina. Pico de working set de vida do
processo compartilhado 249430016 bytes, não soma de picos por vídeo. Método:
process_time/perf_counter e GetProcessMemoryInfo do pipeline. Replay sem espera,
com carga do notebook; não é medição de FPS ou continuidade da webcam.

Resultado primário preservado em
`.local/evaluation/590d9698-a97c-4adc-b212-0fe28db0d1ee/evaluation.json`, SHA-256
`7351c230f945fdbcf6340b68129d147c123b0a6b5a3401f3f4a114f7041a01d0`.
summary.json, métricas oficiais, suplemento declarado previamente e ponteiro
estão no diretório de intake. Revalidação de hashes/política/fonte e resumo:
summarize-cauca-evaluation.py exit 0; source hash a2b76fa3… preservado.

## Investigação da perda, sem mudar a avaliação

Diagnóstico posterior somente de FallLeftS9.avi, mesma configuração geométrica,
modelo e política, sem motor/eventos/HTTP/GUI. Exportou observações brutas para
explicar a falha; não é uma 13ª amostra independente. Reproduziu as 52 análises
e a mesma distribuição dos estados da primeira avaliação.

Durante o alvo de 3000–10350 ms: 37 observações, 36 elegíveis, uma inelegível,
zero candidatas. Quadril dentro do piso em 36/36 elegíveis. Ângulo do tronco
na imagem 26,24–41,73° (regra exige >=60°), razão altura/largura 1,06–1,97
(regra exige <=1). Os dois gates geométricos recusaram a postura mesmo com
pontos suficientes e quadril na ROI. Compatível com limitação de projeção em
2D nesse enquadramento; não é corrigida por apenas suavizar o esqueleto ou
afirmar que o chão foi marcado novamente.

audit-cauca-miss.py exit 0; miss-diagnostic-summary.json e trace privado.
Nenhuma correção de eficácia foi comprovada ou incorporada nesta rodada.
As três perdas históricas de calibração também permanecem. Qualquer ajuste
posterior de modelo/regra que use este resultado exige nova versão e separação
do material de desenvolvimento da próxima avaliação independente.

## Reprodução e estado de encerramento

Para uma repetição intencional, usando o mesmo candidato e novas filas de
avaliação, sem webcam ou API:

```powershell
. ./scripts/activate.ps1
uv run --offline --project services/edge --frozen radar-edge evaluate --manifest .local/etapa08/caucafall-intake-cc77ef23-f567-4091-9d33-27c43bd9355e/manifest-reviewed.json
```

Não conta como novos vídeos/sessões. O helper privado run-cauca-evaluation.py
agora detecta resultado existente e retorna ALREADY_COMPLETED sem inferir de
novo; essa proteção foi exercitada, exit 0, source hash preservado. O guard
anterior retornou exit 2 enquanto a revisão humana estava ausente.

A avaliação exploratória foi realizada e documentada com resultado desfavorável
preservado. Não aprova detector sem falhas, casas desconhecidas ou uso assistencial.
Fechamento de 24/10: ensaio físico curto D51 executado/revisado, 600,660 s,
encerramento normal confirmado pelo fundador. Etapa 08 concluída no escopo
revisado da bancada; [relatório físico e possível perda no chão sem alerta](SESSAO_WEBCAM_10MIN_ETAPA_08.md).
O teste original de 30 min
não foi comprovado; a falha aos 27min45s permanece. Apresentação formal
dispensada pelo fundador em D50, sem
registrá-la como executada; percepção mantém esta limitação conhecida.
Sem commit/push/deploy ou avanço para a etapa 09.

Verificações finais executadas: `pnpm.cmd demo:check --engineering` exit 0,
verificador da fonte congelada exit 0, `git -c core.safecrlf=false diff --check`
exit 0 e auditoria Python da ordem protocolo→resposta humana→calibração, hashes
e denominadores exit 0. Arquivos privados confirmados ignorados pelo Git.
Os 14 checks completos anteriores continuam vinculados ao mesmo SHA de código;
não foram refeitos ou somados como novos testes nesta avaliação de dados.

As seções seguintes registram o protocolo e a preparação anteriores à execução.

## Procedência e escopo

Fonte primária consultada: [CAUCAFall V4, DOI 10.17632/7w7fccy7ky.4](https://data.mendeley.com/datasets/7w7fccy7ky/4),
publicada em 12/07/2022 por Jose Camilo Eraso, Elena Muñoz, Mariela Muñoz e
Jesus Pinto. A página declara CC BY 4.0 e descreve quedas encenadas e atividades
cotidianas. [V5](https://data.mendeley.com/datasets/7w7fccy7ky/5) é outra revisão,
de 18/03/2025; não atribuir os bytes V4 automaticamente à V5. Nenhuma licença
comercial específica do modelo RTMO foi resolvida por esta licença dos vídeos.

O fundador confirmou: “Sim, são novos para o Radar”, em resposta à pergunta
sobre uso anterior em ajustes/seleção, inclusive em outro chat. Não há registro
prévio encontrado de CAUCAFall no desenvolvimento deste projeto. Hashes não
coincidem com os 29 MP4 antigos da pasta de vídeos. Independência dos ajustes
do projeto, sem alegar 12 pessoas, ambientes ou sessões distintas.

São quatro identificadores de participantes na fonte, mesma sala/câmera, datas
de aquisição desconhecidas. Agrupamento conservador único de sessão desconhecida.
Quatro cenas-alvo e oito ADL atendem a quantidade documental proposta; os oito
ADL cobrem quatro atividades em dois participantes, não oito tipos diferentes.
Alongamento, deitar voluntário, saída/oclusão dedicadas e agachar isoladamente
não foram cobertos como categorias independentes neste pacote.

## Integridade e decodificação

Os 12 SHA-256 e tamanhos correspondem ao CSV e provenance.json recebidos.
Decodificação integral: **2876 quadros, 143800 ms, 720×480, 20 quadros/s** em
todos os arquivos, timestamps estritamente crescentes. Não são Full HD. Todos
os hashes são distintos. CRC do ZIP original é alegação do pacote recebido;
não foi revalidada nesta execução nem houve download do ZIP inteiro.

O prefixo dos caminhos originais abaixo é
`Dataset CAUCAFall/CAUCAFall/`; os arquivos locais estão nas subpastas
`01_pessoa_no_chao` ou `02_atividades_comuns` da pasta recebida.

| ID | Caminho exato após o prefixo na distribuição | Duração (s) | SHA-256 |
| --- | --- | ---: | --- |
| cauca-01 | Subject.5/Fall sitting/FallSittingS5.avi | 11,45 | bd2df0f8c185335fa71811d947e5dbbed572c6af4d959d3e9dca59671af47222 |
| cauca-02 | Subject.7/Fall backwards/FallBackwardsS7.avi | 12,60 | c7534882a8ce13ea796bc70230afcb76ab344e753ee29915ba79717954083938 |
| cauca-03 | Subject.9/Fall left/FallLeftS9.avi | 10,35 | c4fa50b461e4e2cf1a511ce6925fdc03c44de0a54ba2505cc0cf451a7e9b6da3 |
| cauca-04 | Subject.10/Fall left/FallLeftS10.avi | 10,60 | 75b35738c8fc821ed8fdca773790cb3b35a4c8e47d882f0f93499229dc97e7a4 |
| cauca-05 | Subject.5/Walk/WalkS5.avi | 11,30 | 0aa4741cfb9523fca778f0bc06739c832fe70089b37d0b0b9968e97ee9c61555 |
| cauca-06 | Subject.10/Walk/WalkS10.avi | 11,20 | 709bd4c4b4f320079d8cbe2e15915c27ba53005cbdc572dbde2bef732e81c5c9 |
| cauca-07 | Subject.5/Sit down/SitDownS5.avi | 13,00 | 150230d34b5e3822eab4350e14e404f7736a894c16840138e41255fb16b4f21a |
| cauca-08 | Subject.10/Sit down/SitDownS10.avi | 11,70 | 7b50d78ea70228e6dd123a467b8d77a38b691c7b8516123ddfce5353d2cb9f32 |
| cauca-09 | Subject.5/Pick up object/PickupobjectS5.avi | 13,55 | 60512bf30f1da6e46accd087eea35af32d57984dd1c5e7e326b7b259bfb14b1c |
| cauca-10 | Subject.10/Pick up object/PickupobjectS10.avi | 14,60 | 7d0ef1fccb87f752252bceda2ae9e648dde933efd56b338767a3a7ab7f2e3726 |
| cauca-11 | Subject.5/Kneel/KneelS5.avi | 10,40 | 0f73541402f4d432f5ad5808d9fba188d66dde8bc8ac130c8b79149c3b9a5a55 |
| cauca-12 | Subject.10/Kneel/KneelS10.avi | 13,05 | 0bfd527d1930a1fd7faad1076c1cde187eb1f858bf74f80d4aa9b7e8fc501194 |

## Congelamento anterior à primeira previsão

HEAD 68ac3d60418ecc6b272990f6c48a14c62918ed13, árvore com alterações da etapa 08,
179 arquivos, SHA de conteúdo
`a2b76fa33449fac7a438efa10e5470580b6310a6b12530d62bf33790b8aeb991`.
Mesma revisão dos 14 checks de engenharia aprovados; não foram repetidos como
se houvesse alteração do produto. Modelo RTMO-s e política floor-rtmo-score-v0.1,
5 análises/s, limiares/geometria/persistência anteriores preservados. SHA do ONNX
conferido: `d0703d40d19f3921da51ae725402d5fdae4d2478c7442072d3101bd396f370d8`.

Congelamento em `.local/etapa08/cauca-source-freeze.json`. Alteração do código,
modelo, manifesto ou piso impede o helper de tratar a execução como o mesmo
protocolo. Não selecionar outra configuração com base no resultado destes vídeos.
Se forem usados em ajustes futuros, registrar a nova utilização como calibração.

Protocolo e artefatos privados em
`.local/etapa08/caucafall-intake-cc77ef23-f567-4091-9d33-27c43bd9355e/`:
intake.json, protocolo antes da inferência, manifesto rascunho, proposta do piso,
configurações exclusivas, quadros brutos a cada 500 ms e vídeo de revisão.

## Anotação antes das previsões

Propostas visuais de PERSON_ON_FLOOR: cauca-01 de 4000–11450 ms; cauca-02 de
5000–12600 ms; cauca-03 de 3000–10350 ms; cauca-04 de 3000–10600 ms.
Incerteza de início de até 500 ms. Os oito ADL têm intervalo completo sem pessoa
deitada. Eram propostas pendentes; o fundador confirmou as cenas/faixas e o piso
antes da execução, conforme registro no início deste relatório.

O contorno de piso proposto foi selecionado visualmente antes da inferência,
excluindo parede, mesa e cômoda; não foi inferido por pose, ampliado após perdas
ou registrado como calibração aprovada durante a proposta. Compartilhamento
entre os 12 foi conferido pelo fundador. A calibração executável só foi criada
após essa confirmação, com os mesmos pontos do protocolo.

Regra oficial: mesmo kind, emissão no alvo ou até 2 s após seu fim, um match por
alvo, duplicações separadas. **Suplemento declarado antes da execução:** contar
PERSON_ON_FLOOR e POSSIBLE_FALL como candidatos à mesma postura no chão, com a
mesma tolerância, apresentando os resultados adicionais separados dos resultados
oficiais por kind. Não substituir silenciosamente as métricas oficiais.

Não há ground truth de acidente real, necessidade de ajuda ou rótulo específico
POSSIBLE_FALL do Radar. Nome da pasta “fall” não cria essa anotação. Recall de
acidente real/necessidade de ajuda permanece não estimável. Predições e períodos
sem alerta serão examinados após fixar as anotações.

## Revisão humana preparada

Vídeo privado de revisão contém os 12 clipes completos e cartões de identificação:
3116 quadros decodificados na verificação, 155,8 s, sem modelo, esqueleto, HTTP
ou webcam. Mostra imagem bruta, proposta de piso e intervalos. Janela aberta
pausada, “Radar - CAUCAFall - conferir piso e cenas”, PID 20328 na abertura.
Helper PowerShell validado, stderr vazio. Espaço inicia; R repete; Q/Esc fecha.

```powershell
powershell -NoProfile -File .local/etapa08/review-caucafall.ps1
```

Conferências solicitadas: piso adequado nos 12 e correspondência das quatro
faixas-alvo/oito cenas comuns. **Ambas confirmadas pelo fundador antes da inferência.**
O helper da avaliação verifica registro explícito vinculado aos hashes antes
de calibrar ou inferir. Não executou o detector para escolher os vídeos.

## Comandos executados e limites

- `node .local/etapa08/freeze-cauca-source.mjs`: exit 0, identidade registrada.
- `uv run --offline --project services/edge --frozen python .local/etapa08/intake-caucafall.py`:
  exit 0, integridade/decodificação e imagens brutas, sem estimador.
- `prepare-cauca-review.py`: criou clipes/configs/rascunho; falhou ao serializar
  Policy como Pydantic. Corrigido para Policy.to_dict e finalização executada
  separadamente (exit 0), preservando os arquivos e sem inferência. Revisão final
  decodificada integralmente, 3116 quadros.
- `uv run --offline --project services/edge --frozen python .local/etapa08/run-cauca-evaluation.py --prepare-only`:
  exit 2 esperado, AWAITING_HUMAN_REVIEW; código/modelo/hashes conferidos,
  detector e motor não executados. Confirmação de exit 2 pelo LASTEXITCODE.
- Busca inicial ampla de diretórios interrompida ao localizar a pasta; primeira
  tentativa Node inline falhou por aspas do PowerShell. Módulo .mjs corrigiu a
  chamada. Nenhum desses erros alterou o produto ou resultados anteriores.

A preparação não tinha resultado de percepção. Após a revisão humana foi
executado o helper sem --prepare-only, com evaluate/outboxes novas, REPLAY,
sem entrega HTTP, JPEG ou alteração do banco original. Resultados atuais no
início deste relatório. Atualização de 24/10: ensaio físico D51 executado/revisado,
com limitações no relatório da sessão; 30 min originais não comprovados e
apresentação dispensada por D50.

## Relato sobre a prévia anterior

O fundador confirmou fluidez e acompanhamento no 20.mp4, mas relatou piscar.
O arquivo de observações registra 60 NO_POSE em 342 quadros, espalhados por
29 intervalos. São ausências da estimativa bruta, não apenas tremor visual.
O filtro preserva ausência de pontos; nenhum limiar foi reduzido. Isso não foi
declarado corrigido. Feedback/intervalos privados em
`another-stabilized-preview-aecfc57c-dcf7-4854-b2f6-1ec8b161d1e5/human-feedback-and-absence.json`.
