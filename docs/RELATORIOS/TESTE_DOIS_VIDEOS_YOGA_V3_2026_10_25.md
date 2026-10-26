# Dois vídeos de pessoa já no chão — diagnóstico congelado V3

Data: **25/10/2026, America/Sao_Paulo**. Resultado: primeiro vídeo atende aos
critérios do ensaio; segundo **PARCIAL**, por cobertura 79,75% abaixo de 80%.
Detecção nos dois dentro de 5 s, sem concluir aprovação do MVP ou da webcam.

## Materiais e identidade

Pasta fornecida pelo fundador: `.local/videos/Radar_2_Videos_Pessoa_No_Chao/`.
README, JSON de procedência, prévia e hashes foram lidos antes de executar IA.
Hashes recalculados conferem com o pacote:

| Arquivo | Duração / frames / resolução | SHA-256 |
| --- | --- | --- |
| 01_casa_deitada_lateral_25s.mp4 | 25,025 s; 750 frames; 854×480; 29,97 FPS | f6f18ba27740284bf8fbf6c59eab52c8417ee0f1091b30e81fce76800963487c |
| 02_sala_deitada_corpo_inteiro_16s.mp4 | 16 s; 400 frames; 640×360; 25 FPS | d6317f319558a04f40f1af7a53df9bd42037a63736a950388ae23fa44bdd4935 |

Fontes declaradas: NCTV, [Yoga With Ginny — Episode 022](https://archive.org/details/Yoga_With_Ginny_-_Episode_022),
trecho 10:05–10:30, e [Episode 131](https://archive.org/details/Yoga_With_Ginny_-_Episode_131),
55:02–55:18. As duas respostas oficiais de metadados foram consultadas por HTTP
local; nomes/MD5/tamanhos dos MP4s completos coincidem com o JSON fornecido.
As páginas não abriram no navegador de pesquisa; usou-se a API oficial
[022](https://archive.org/metadata/Yoga_With_Ginny_-_Episode_022) e
[131](https://archive.org/metadata/Yoga_With_Ginny_-_Episode_131).
Os MP4s completos de origem não foram baixados nem comparados byte a byte aos
recortes recodificados. Não alegar autenticação forense dos recortes.

As fontes não informaram licenseurl/rights nas respostas consultadas.
Uso nesta rodada: teste privado dos arquivos fornecidos, sem treino,
redistribuição, publicação ou pressuposição de direitos comerciais.
Mesma apresentadora segundo os materiais; duas gravações/ambientes e episódios,
não duas pessoas independentes. Datas de publicação não são tratadas como datas
exatas de gravação. Sem validação final reservada de quatro alvos/oito negativos.

Ambos foram decodificados integralmente sem erros ou fallback temporal. Inspeção
de imagens originais ao longo dos recortes e notas fornecidas mostram uma pessoa
já deitada no tapete/piso durante todo o arquivo. No primeiro, cabeça apoiada;
no segundo há pequenos movimentos. Nenhuma transição de queda é anotada.
Exercício voluntário no piso satisfaz o alvo postural, não prova acidente ou mal-estar.

## Protocolo antes das previsões

Código congelado de 197 arquivos:
`27aa36e4c2d0b13c9a0fc3b00d900db67ab25da6bd3ece59393620bfe2bdf467`,
HEAD `3c7ba42cf50a698c784e911795703259eb73ecdc`, alterações prévias preservadas.
RTMO-s SHA `d0703d40d19f3921da51ae725402d5fdae4d2478c7442072d3101bd396f370d8`.
V3 `signed-body-mlp-v3-dev01`, SHA
`40d01401851f24cd8c815557970f0dcf42877707afbba38d521ebfa87bd5bd19`.

Comparação de seis execuções FILE completas, em sequência:

- Referência geométrica: floor-rtmo-score-v0.1, RTMO original.
- V2: LINEAR_BODY_V2, floor-rtmo-score-posture-body-v2, RTMO original.
- V3 atual: MULTICLASS_BODY_V3, recuperação RTMO_ADAPTIVE_V2 e política
  floor-rtmo-score-posture-multiclass-v3-dynamics01-adaptive2.

Os polígonos de cada novo ambiente foram preparados por inspeção manual das
imagens originais, **antes de executar o estimador**, e congelados por SHA em
`protocol-before-predictions.json`. Não são segmentação automática de piso,
nem marcação da pessoa, nem medição física de contato/altura. As três versões
receberam a mesma geometria e o mesmo polígono de cada arquivo, sem exclusões
adicionais. Operador registrado como CODEX_MANUAL_ORIGINAL_IMAGE_REVIEW_BEFORE_INFERENCE; não foi alegada
aprovação dos contornos pelo fundador. Resultado condicionado a esses contextos
de diagnóstico; webcam e sua calibração não foram modificadas.

Critérios fixados: alvo PERSON_ON_FLOOR desde o início observável 0 ms até o fim,
tempo real anterior ao arquivo desconhecido; persistência 2000 ms, prazo de
5000 ms, cobertura decisória ≥80%, sem duplicação e sem POSSIBLE_FALL injustificado.
Nenhum alvo removido, trecho excluído, limiar relaxado ou polígono alterado depois
das previsões. Papel: diagnóstico congelado; os arquivos não entraram no treino.

## Resultados individuais

| Vídeo | Referência | V2 | V3 | Cobertura V3 | Aceite V3 neste ensaio |
| --- | ---: | ---: | ---: | ---: | --- |
| Casa, 25 s | 2002 ms | 2002 ms | **2002 ms** | **100%** | Atende |
| Sala, 16 s | 12400 ms | 12400 ms | **4000 ms** | **79,7468%** | **Parcial: abaixo de 80%** |

As seis execuções concluíram status ok/ENDED. Dois alvos, dois detectados em
cada versão, zero perdas totais; referência/V2 têm um alerta tardio, enquanto
V3 tem os dois dentro do prazo. Não confundir detectado com aprovado: o segundo
falha no gate de cobertura, mesmo com latência adequada. Não arredondar 79,75%
para 80% nem usar a média dos dois vídeos para esconder essa insuficiência.

Cada execução gerou exatamente um PERSON_ON_FLOOR: seis envelopes em seis filas
distintas. Não houve POSSIBLE_FALL, duplicação ou aviso de erro de captura. As
seis saídas respeitaram o contrato compartilhado e ficaram PENDING localmente,
com zero tentativas HTTP e zero snapshots. Não são seis incidentes novos no painel.
Não há negativos neste lote, portanto não estimar falsos positivos por silêncio.

Tempos de mídia não dependem do replay acelerado. No primeiro, a amostragem de
29,97 FPS produz emissão aos 2002 ms; no segundo, 4000 ms. A latência parte de
0 ms anotado, não do primeiro frame que o estimador passou a aceitar.
Intervalos observados: 24825/15800 ms; caudas não amostradas 200,025/200 ms.
Na sala, elegíveis 12600 de 15800 ms; a captura permaneceu saudável no intervalo
amostrado. Cobertura é conservadora, com ambos os extremos elegíveis e gap ≤500 ms.

## Diagnóstico da instabilidade no segundo vídeo

Referência/V2: 33 de 80 análises NO_POSE e 47 com pose suficiente. Ambas
classificaram a postura candidata quando havia pose, mas só completaram a
persistência aos 12,4 s. Cobertura decisória 48,10%.

V3: **69 LYING, 11 NO_POSE**. Sem erros de classe observados nas 69 poses
aceitas e sem rejeição pelo piso. Original resolveu 47 análises; o recorte
da proposta de pessoa recuperou outras 22. Nas 11 restantes, as tentativas de
recorte/inversão/recorte central não atingiram o score de detecção >0,7:
melhor proposta por análise entre aproximadamente 0,493 e 0,698.

Ausências em 1400, 1600, 1800, 2200, 7400, 7600, 7800, 8800, 9000, 9200 e
9800 ms. Elas explicam a fragmentação da evidência sem transformar NO_POSE em
ambiente vazio. A pessoa aparece deitada nas imagens originais; é falha de
localização/percepção nesses instantes. Há contraluz e vestimenta escura,
hipóteses visuais, sem comprovar isoladamente qual delas causou a rejeição.

Este material fornece uma regressão reproduzível para investigar a percepção,
sem pedir outra sessão física a cada ajuste. A próxima comparação específica
deve atacar essas 11 ausências com localização/recorte ou outro estimador
compatível, mantendo coordenadas, qualidade, tempo e regressões. Não diminuir
o limiar apenas para aceitar propostas abaixo de 0,7. Não fazer treino nesses
vídeos enquanto os direitos correspondentes não estiverem estabelecidos.

## Custo observado

Mesma máquina/ambiente da evolução 05, CPU e dependências preservadas.

| Vídeo / versão | Parede | CPU-s | Inferência média |
| --- | ---: | ---: | ---: |
| Casa / referência | 15,969 s | 64,125 | 105,913 ms |
| Casa / V2 | 15,897 s | 64,875 | 105,755 ms |
| Casa / V3 | 15,896 s | 64,672 | 104,693 ms |
| Sala / referência | 10,061 s | 39,344 | 111,809 ms |
| Sala / V2 | 9,943 s | 38,844 | 112,549 ms |
| Sala / V3 | 16,141 s | 61,891 | 181,403 ms |

205 análises por versão; 615 no comparativo. O custo adicional do V3 na sala
acompanha as tentativas extras de recuperação. No primeiro, todas as 125 análises
foram resolvidas na inferência original. Classificação V3: médias 0,427/0,297 ms,
separadas da inferência. Leitura/decodificação total V3: 1350,7/141,2 ms.
Prévia desligada: não medir fluidez de exibição ou FPS de webcam por esses tempos.

## Verificações e reprodução

Diretório privado:
`.local/detector-evolution/intake-yoga2-28d772c1-8d1f-4d84-bdf0-cc3a0587d34d/`.
Ponteiro `.local/detector-evolution/yoga2-current.json`.
Contém inventário, protocolo anterior à previsão, calibrações/configurações,
traces/observações, relatórios originais, seis SQLite, resultados, resumo e auditoria.

| Comando realmente executado | Resultado |
| --- | --- |
| Get-FileHash dos dois MP4s, leitura do pacote, git status | SHA/estrutura e alterações existentes preservados |
| python .local/detector-evolution/intake-two-yoga.py | 1150 frames decodificados, metadados/horários conferidos, fontes públicas consultadas |
| python .local/detector-evolution/show-yoga2-originals.py | revisão amostrada de imagens originais sem estimador |
| python .local/detector-evolution/prepare-yoga2-tests.py | seis configurações, alvos/critérios/contextos congelados antes da inferência |
| python .local/detector-evolution/run-yoga2-tests.py | seis FILE reais, 84,06 s totais do helper, resultados acima |
| python .local/detector-evolution/audit-yoga2-tests.py | seis contratos/envelopes válidos, filas completas, zero HTTP/JPEG, hashes preservados |
| Reabertura das duas configurações V3 concluídas durante a auditoria | mesmo evento, zero eventos novos e zero duplicação |

Prefixo dos helpers: `uv run --offline --project services/edge --frozen`.
O primeiro wrapper de inspeção precisou corrigir a leitura do JSON após a
mensagem do activate.ps1; o inventário já havia sido salvo e nenhum ensaio de
inferência foi reexecutado para mascarar resultado.

Para repetir V3 usando o avaliador existente, com filas novas e HTTP desligado:

```powershell
. ./scripts/activate.ps1
$radarYoga = Get-Content .local/detector-evolution/yoga2-current.json -Raw | ConvertFrom-Json
uv run --offline --project services/edge --frozen radar-edge evaluate --manifest (Join-Path $radarYoga.root 'v3-manifest.json')
```

Manifestos baseline-manifest.json e body-v2-manifest.json permitem repetir as
referências nas mesmas condições. Papel CALIBRATION no esquema existente indica
uso de diagnóstico/desenvolvimento, não autorização para treino ou teste reservado.
Os três manifestos foram validados com Manifest/guard_candidate_evaluation sem
abrir fontes; agregados e protocolo tiveram hashes registrados em result-freeze.json.

Para assistir sem alterar fila ou criar outro evento:

```powershell
uv run --offline --project services/edge --frozen radar-edge run --config (Join-Path $radarYoga.root 'yoga2-02/v3.yaml') --poses-only --preview-paused --replay-speed 1
```

Espaço inicia/pausa; Q/Esc encerra. Nenhuma prévia/webcam foi aberta nesta rodada.

## Limites e estado

Dois exemplos de uma apresentadora, já deitada, sem negativos ou transições.
Não avaliam generalização entre pessoas, quedas, mal-estar, o cômodo do fundador
ou os três episódios da sua sessão LIVE. A cobertura do segundo ainda falha;
o resultado da webcam continua insatisfatório. Não houve ajuste para esses
vídeos, novo treino, dependência, alteração de lockfile ou mudança de modelo.
Não foram refeitas as suítes de software da evolução 05: código executável
permaneceu igual; os testes desta rodada são os seis FILE e as verificações
de contratos/persistência/retomada descritas. Sem commit, push ou deploy.
