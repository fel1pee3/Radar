# Relatórios de implementação

[Status](../STATUS.md) · [Plano](../../etapas/README.md)

Os relatórios são criados durante a implementação. As etapas [00](ETAPA_00.md), [01](ETAPA_01.md) e [02](ETAPA_02.md) registram verificações reais e seus limites; o [inventário técnico](DEPENDENCIAS_E_MODELOS.md) registra as dependências selecionadas. Use `ETAPA_00.md` a `ETAPA_09.md`; o relatório final será `VALIDACAO_MVP.md`.

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
