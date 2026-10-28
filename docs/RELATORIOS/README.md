# Relatórios de implementação

[Viabilidade RTMO/DirectML, 27/10](VIABILIDADE_RTMO_DIRECTML_2026_10_27.md):
GPU física comprovada, 60 análises, 45 transmissões e 72 regressões;
aceleração útil isolada, mesmo reconhecimento conhecido e falhas preservadas.
Configuração física curta preparada; nenhuma câmera aberta.
[Tabelas por transmissão](VIABILIDADE_RTMO_DIRECTML_STREAMS_2026_10_27.csv) ·
[Regressão por arquivo](VIABILIDADE_RTMO_DIRECTML_REGRESSAO_2026_10_27.csv).


[Referência parcial e localização, 27/10](REFERENCIA_PARCIAL_E_LOCALIZACAO_2026_10_27.md):
nove tornozelos conferidos, causas dos zero probes auditadas e cache RGB
reavaliado. YOLOX-m recupera dois alvos de localização, mas não é promovido
por falsos boxes/regressões e qualidade de pose insuficiente.
[Tabela por frame](REFERENCIA_PARCIAL_LOCALIZACAO_2026_10_27.csv).

[Continuidade e referência visual, 27/10](CONTINUIDADE_E_REFERENCIA_VISUAL_2026_10_27.md):
proteção antes/depois do commit e na entrega, testes de interrupção e auditoria
A/B nas quatro orientações. Entrada RGB da pose corrigida no experimento;
rótulos articulares provisórios, nenhuma promoção perceptual.
[448 comparações diagnósticas](CONTINUIDADE_VISUAL_AUDITORIA_2026_10_27.csv).

[Decisão limitada e retificação temporal](DECISAO_PERCEPCAO_2026_10_26.md):
725 s explicados, 240 resultados reavaliados, alternativas sem promoção.

[Estabilização perceptual, 26/10](ESTABILIZACAO_PERCEPTUAL_2026_10_26.md):
diagnóstico nativo dos sete frames, alternativas A/B/C e comparação completa
de referência/V1/V2/ROI isolada. [Detalhes e reprodução do diagnóstico](DIAGNOSTICO_RECUPERACAO_2026_10_26.md).

[Reaquisição canônica V2, 26/10](REAQUISICAO_V2_2026_10_26.md):
correção da prioridade de ORIGINAL, reprodução dos frames omitidos e comparação
com referência/V1 em oito cenários e nos 36 arquivos. Resultados e decisão de
elegibilidade física separados da aprovação de engenharia.

[Preferência adaptativa, 26/10](RECUPERACAO_ADAPTATIVA_2026_10_26.md):
24 transmissões e 36 regressões, economia de chamadas com quatro novos controles
inconclusivos. Candidato não promovido, referência mantida, sem teste físico novo.

[Processamento de transmissão, 26/10](DESEMPENHO_TRANSMISSAO_2026_10_26.md):
perfil por fase, reprodução técnica a 1× no agendamento LIVE e 36 comparações.
Sem ganho consistente nas duas opções de CPU; referência preservada, gargalo
aberto e nenhuma nova webcam executada.

[Ensaio físico de orientação, 26/10](ENSAIO_WEBCAM_ORIENTACAO_2026_10_26.md):
12 janelas auditadas, quatro incidentes/avisos entregues, insuficiência de
cobertura/cadência e limites de anotação humana. Aceite não aprovado; sem
alteração de parâmetros ou repetição automática.

[Recuperação de orientação, 26/10](PERCEPCAO_ORIENTACAO_V3_2026_10_26.md):
V3 reproduzido, perdas da sala localizadas, candidato sem treino comparado em
arquivos; desempenho e validação física ainda dependem do ensaio controlado.

Diagnóstico adicional: [dois vídeos de yoga, V3 congelado](TESTE_DOIS_VIDEOS_YOGA_V3_2026_10_25.md).
Detectou os dois dentro de 5 s; segundo ainda parcial por cobertura <80%.

[Status](../STATUS.md) · [Plano](../../etapas/README.md)

Os relatórios são criados durante a implementação. As etapas [00](ETAPA_00.md), [01](ETAPA_01.md), [02](ETAPA_02.md) e [03](ETAPA_03.md) registram verificações reais e seus limites; o [inventário técnico](DEPENDENCIAS_E_MODELOS.md) registra as dependências selecionadas. Use `ETAPA_00.md` a `ETAPA_09.md`; o relatório final será `VALIDACAO_MVP.md`.

A [etapa 04](ETAPA_04.md) registra visão em arquivo com modelo real, um vídeo
autorizado, piso selecionado pelo fundador e prévia conferida. Essa validação
comprova extração de poses naquele arquivo; não avalia detecção de quedas.

A [etapa 05](ETAPA_05.md) registra motor temporal, outbox, retomada e integração
real. Após os ensaios negativos iniciais, a comparação Lite/Full produziu um
incidente REPLAY derivado de filmagem real, conferido pelo fundador; concluída
para bancada, com limitações na [investigação](INVESTIGACAO_ETAPA_05.md).

A [etapa 06](ETAPA_06.md) registra webcam nativa, piso/Full contínuo,
pausa/retomada/encerramento conferidos pelo fundador e recuperação controlada.
Concluída para bancada em 22/10, com falso esqueleto de estante, fluidez e
evento LIVE positivo ainda tratados como limites da validação final do MVP.

A [etapa 07](ETAPA_07.md) registra JPEG sintético opcional, acesso/exclusão auditados,
retencão e proteção com relógio controlado e recursos exclusivos. Concluída sem
habilitar JPEG real, agendamento de limpeza ou purga pessoal. Limitações de
percepção da 06 continuam para a validação final da 08.

## Modelo de relatório de etapa

A evolução solicitada após a 08 tem estado próprio: [diagnóstico](EVOLUCAO_DETECTOR_01.md)
e [classificador/motor/comparação](EVOLUCAO_DETECTOR_02.md). Candidato experimental
parcial, sem substituir o fechamento histórico ou iniciar a etapa 09.
[Recebimento dos 16 vídeos e candidato corporal V2](EVOLUCAO_DETECTOR_03.md)
registra procedência, independência limitada e correção dos contornos.
[Primeira avaliação dos 16 arquivos](EVOLUCAO_DETECTOR_04.md): baseline/V2
2/6 alvos; V2 sem melhora global e não aprovado, seis negativos inconclusivos.
[Incremento 05](EVOLUCAO_DETECTOR_05.md): V3 recupera 6/6 em desenvolvimento,
resolve os dez negativos daquele lote e verifica o fluxo até revisão humana;
transições, perdas históricas, avaliação reservada e webcam ainda limitam o aceite.

A [etapa 08](ETAPA_08.md) registra validação de engenharia, instalação limpa,
backup/restore e candidata local, com [matriz final](VALIDACAO_MVP.md).
**Concluída no escopo revisado da bancada (D50/D51), 24/10:** sessão física de
600,660 s auditada e encerramento confirmado pelo fundador; tempo elegível e
lacunas separados. [Resultados e possível perda no trecho no chão sem alerta](SESSAO_WEBCAM_10MIN_ETAPA_08.md).
Teste original de 30 min
não comprovado; falha histórica preservada. Apresentação formal dispensada pelo fundador
(D50), sem declarar sua execução. Avaliação independente
CAUCAFall executada: 3/4 alvos, uma perda e zero alertas nos oito ADL, com
cobertura limitada. [Resultados e limites](CAUCAFALL_ETAPA_08.md).
LIVE positivo/revisão e replay/serviços offline comprovados na 08.
Não confundir fechamento da demonstração técnica com eficácia geral ou liberação
assistencial/comercial. O checker não consome o aceite manual e mantém sua lista
original fixa; sem aprovação automática alegada.

O [complemento dos materiais 08](MATERIAIS_ETAPA_08.md) registra fontes, hashes,
licenças, ensaios dos 23 novos vídeos e recuperação dos dois históricos. A avaliação
reservada é provisória e desfavorável; não há melhora de precisão comprovada nem
aprovação física obtida com os vídeos longos.

Copiar a estrutura abaixo e preencher com fatos. Não deixar “passou” sem dizer o que foi executado.

```markdown
# Etapa XX — nome

Data:
Status: CONCLUÍDA / PARCIAL / BLOQUEADA
Ambiente: SO, runtime, versões e hardware relevante
Revisão/commit local, se existir:

## Resultado entregue

O que funciona e qual objetivo atende.

## Arquivos e decisões

Caminhos alterados, migrações, dependências fixadas e decisões relevantes.

## Verificações reais

| Comando/ação | Resultado observado | Evidência/limitação |
| --- | --- | --- |
| ... | ... | ... |

## Critérios da etapa

| Critério | Verificado / pendente | Evidência |
| --- | --- | --- |
| ... | ... | ... |

## Como reproduzir

Passos e comandos reais, sem segredos.

## Falhas, limites e pendências

O que não foi executado, por quê e como verificar. Não usar zero para métrica não medida.

## Próxima etapa elegível

Número e condições de avanço; não implementar automaticamente.
```

## Dados que não entram no relatório versionado

Credenciais, URLs RTSP autenticadas, vídeo pessoal, rostos sem autorização, dados de pacientes, dumps do banco e arquivos de configuração privada. Resultados numéricos devem ter contexto e denominador. Um link para mídia privada pode existir em anotação local, sem publicar o conteúdo no Git.
