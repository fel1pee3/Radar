# Relatórios de implementação

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

## Modelo de relatório de etapa

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
