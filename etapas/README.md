# Plano de implementação por etapas

[README central](../README.md) · [Status](../docs/STATUS.md) · [Modelo de relatório](../docs/RELATORIOS/README.md)

## Como executar

Uma solicitação ao ChatGPT do VS Code corresponde a uma etapa. Cada README contém seu próprio prompt completo. A IA deve ler os arquivos do repositório, implementar, verificar e relatar; não receber todo o produto de uma vez para construir sem checkpoints.

| Etapa | README e prompt | Situação no plano |
| --- | --- | --- |
| 00 | [Fundação do repositório e ambiente](00_FUNDACAO/README.md) | Obrigatória |
| 01 | [Domínio, banco e acesso](01_DOMINIO_E_ACESSO/README.md) | Obrigatória |
| 02 | [Eventos, incidentes e contratos](02_EVENTOS_E_INCIDENTES/README.md) | Obrigatória |
| 03 | [Painel e primeira demonstração](03_PAINEL_E_SIMULADOR/README.md) | Obrigatória |
| 04 | [Visão computacional em arquivo](04_VISAO_EM_VIDEO/README.md) | Obrigatória |
| 05 | [Motor temporal e eventos de visão](05_MOTOR_TEMPORAL/README.md) | Obrigatória |
| 06 | [Webcam, disponibilidade e recuperação](06_WEBCAM_E_RESILIENCIA/README.md) | Obrigatória |
| 07 | [Evidência opcional, retenção e proteção](07_EVIDENCIA_E_PROTECAO/README.md) | Obrigatória |
| 08 | [Validação final e entrega da demo](08_VALIDACAO_E_ENTREGA/README.md) | Obrigatória |
| 09 | [Câmera IP e verificação da KAP-S069](09_CAMERA_IP_OPCIONAL/README.md) | Opcional |

Sequência obrigatória: 00 a 08. A etapa 09 depende da 06 e pode ser feita depois da 08, sem bloquear a conclusão do MVP com webcam.

## Marcos para você ver progresso

| Após | O que mostrar | Como chamar honestamente |
| --- | --- | --- |
| 03 | Evento artificial percorrendo o painel e a revisão | Demonstração do fluxo |
| 05 | Vídeo autorizado analisado e gerando suspeita | Prova exploratória de percepção |
| 08 | Fonte ao vivo, incidentes, falhas e relatório | MVP de bancada v0.1 |
| 09 | Unidade IP com stream testado | Compatibilidade comprovada apenas nas condições registradas |

## Regras de avanço

Os critérios de cada README são o gate. Build funcionando é necessário, mas não substitui teste de domínio, captura física ou benchmark. Se uma verificação física não foi possível, marcar parcial e preparar os comandos para o fundador. A etapa IP pode terminar com incompatibilidade documentada; isso não altera o status das etapas obrigatórias.

Depois de cada etapa, leia o relatório e experimente a demonstração correspondente. Você pode trazer o relatório e os erros de volta a esta conversa para ajustar o próximo prompt. Não é necessário parceiro ou investidor para nenhum desses marcos de bancada.

## Prompt para retomar uma etapa interrompida

Substitua XX pelo número real e informe o caminho do README da etapa.

```text
Retome a ETAPA XX do Radar de Acontecimentos. Leia AGENTS.md, README.md,
docs/STATUS.md, o README dessa etapa em etapas/ e seu relatório existente
em docs/RELATORIOS/ETAPA_XX.md. Inspecione o código atual e o git status.
Continue apenas os itens pendentes e suas dependências necessárias.
Preserve trabalho existente. Não repita mudanças já verificadas sem motivo.
Execute as verificações pertinentes, registre resultados reais e atualize
status/relatório. Não avance para outra etapa automaticamente.
```

## Prompt para corrigir a entrega de uma etapa

```text
Revise e corrija a ETAPA XX do Radar de Acontecimentos antes de avançar.
Leia AGENTS.md, o README da etapa, os contratos aplicáveis e o relatório.
Compare os critérios de conclusão com o código e os resultados realmente
executados. Reproduza os erros que eu informar e investigue a causa.
Corrija o mínimo necessário, preserve funcionalidades existentes e
verifique os riscos afetados. Não reduza critérios para obter sucesso.
Atualize docs/STATUS.md e docs/RELATORIOS/ETAPA_XX.md com evidências.
Se faltar hardware ou credencial, diga exatamente qual teste ficou pendente.
```

## Quando mudar o plano

Só alterar stack, contratos, objetivo ou dependências das etapas por decisão registrada em `docs/09_DECISOES_E_FUTURO.md`, ou por instrução atual do fundador. Se um patch de biblioteca mudar, atualizar lock/inventário e verificar a integração afetada. Não introduzir uma arquitetura nova silenciosamente porque a IA encontrou um tutorial diferente.
