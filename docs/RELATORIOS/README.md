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

A [etapa 07](ETAPA_07.md) registra JPEG sintético opcional, acesso/exclusão auditados,
retencão e proteção com relógio controlado e recursos exclusivos. Concluída sem
habilitar JPEG real, agendamento de limpeza ou purga pessoal. Limitações de
percepção da 06 continuam para a validação final da 08.

## Modelo de relatório de etapa

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
