# Etapa 02 — Eventos, incidentes e contratos

[Plano das etapas](../README.md) · [README central](../../README.md) · [Status](../../docs/STATUS.md)

**Estado inicial:** não iniciada. O estado atualizado deve estar em `docs/STATUS.md`.

## Objetivo

Um evento autenticado vira um incidente persistido, revisável e idempotente, com auditoria e aviso local simulado.

## Dependências

Etapa 01 concluída; credencial de device e sessão disponíveis.

## Leitura obrigatória

Além de `AGENTS.md`, README central e status:

- [03_CONTRATOS_E_DADOS.md](../../docs/03_CONTRATOS_E_DADOS.md)
- [06_SEGURANCA_E_DADOS.md](../../docs/06_SEGURANCA_E_DADOS.md)
- [07_VALIDACAO_E_DEMO.md](../../docs/07_VALIDACAO_E_DEMO.md)

## Áreas de trabalho

packages/contracts, apps/api, validação Python dos exemplos, migrações e testes de integração.

Os caminhos de aplicação são entregas a criar/adaptar, não arquivos já presentes neste pacote. Ajustes em etapas anteriores são permitidos quando necessários para integrar corretamente, com motivo no relatório.

## Atividades

1. Materializar JSON Schemas v1 de evento, heartbeat e ação; exemplos válidos/inválidos, tipos TS e validação Python. Compartilhar fixtures e testar equivalência, sem importar código TS no Python.
2. Implementar tabelas/índices restantes do domínio conforme contratos. Registrar hash canônico do evento e unicidades no banco, não apenas checagem prévia em memória.
3. Implementar ingestão transacional com recibo, incidente, auditoria e intenção de aviso; respostas de novo/duplicado/conflito. Derivar tenant/device da credencial e conferir câmera.
4. Implementar classificação TEST/CURRENT/DELAYED/CLOCK_UNCERTAIN. Preservar horário original e não reclassificar urgência em reenvios.
5. Implementar heartbeat, exclusão de run concorrente, sequência e status derivados de recebimento. Relógio injetável nos testes.
6. Implementar listagem/paginação/detalhe de incidentes e ações com transições válidas, expectedVersion e actionId idempotente. Guardar revisão e desfecho separados.
7. Implementar intenção/entrega SIMULATED no PostgreSQL com processamento retomável. Uma intenção gera no máximo um registro de entrega; não conectar qualquer provedor externo.

## Critérios de conclusão

- [ ] Reenvio de um evento dez vezes, inclusive em concorrência, resulta em um incidente e um aviso lógico.
- [ ] Mesmo eventId com conteúdo diferente falha sem alterar evento original; episódio duplicado não produz segundo incidente.
- [ ] Ações concorrentes tratam versão; transições inválidas são rejeitadas; a mesma ação reenviada não repete auditoria.
- [ ] Payload inválido e câmera de outro tenant são rejeitados em TS/API/Python conforme fixtures.
- [ ] Atraso, relógio incoerente, heartbeat antigo e conflito de run passam nos testes determinísticos.
- [ ] Reinício do executor de avisos não perde intenção persistida nem duplica entrega simulada.
- [ ] `docs/STATUS.md` e `docs/RELATORIOS/ETAPA_02.md` refletem a situação real.

## Limites desta etapa

Não implementar processamento de imagem, envio real de notificação ou Redis. Não transformar dados de testes em prova de detecção.

## Entrega para o fundador

Demonstrar o objetivo desta etapa e fornecer comandos reais de reprodução. Separar verificado, parcialmente verificado e não executado. Usar o modelo em [relatórios](../../docs/RELATORIOS/README.md). Não concluir a etapa apenas porque arquivos foram criados ou o build passou.

## Prompt para o ChatGPT do VS Code

Copie o bloco inteiro com a pasta do projeto aberta. O prompt manda a IA ler este README e seus critérios, portanto não é necessário colar toda a documentação na conversa.

```text
Você está no repositório Radar de Acontecimentos. Implemente somente a ETAPA 02: Eventos, incidentes e contratos.

Antes de editar, leia:
- AGENTS.md
- README.md
- docs/STATUS.md
- etapas/02_EVENTOS_E_INCIDENTES/README.md
- docs/03_CONTRATOS_E_DADOS.md
- docs/06_SEGURANCA_E_DADOS.md
- docs/07_VALIDACAO_E_DEMO.md

Faça um inventário do código existente e preserve alterações do fundador. Confirme as dependências desta etapa pelo código e pelos relatórios, sem presumir que já foram implementadas.

Foco desta entrega:
Implemente exatamente os contratos e a máquina de estados documentados. Faça idempotência transacional e avisos simulados persistentes. A API deve funcionar por chamadas reais e testes, ainda sem câmera nem painel completo.

Execute as atividades e os critérios de conclusão descritos no README desta etapa. Não pare só no plano: produza a implementação e execute as verificações pertinentes disponíveis. Resolva decisões rotineiras com a documentação. Se faltar uma ação física, credencial ou dado indispensável, prepare o restante e peça apenas a informação concreta que bloqueia a validação.

Use a stack e os contratos fixados. Não adicione funcionalidades de etapas posteriores, contas pagas, envio externo, deploy, publicação ou compras. Não invente testes, compatibilidade, medições ou resultados. Diferencie simulação, replay e câmera ao vivo.

Ao concluir, atualize docs/STATUS.md e crie/atualize docs/RELATORIOS/ETAPA_02.md. Relate arquivos alterados, comandos realmente executados, resultados, decisões, pendências e como reproduzir. Se houver requisito não verificado, marque parcial em vez de concluir. Não avance automaticamente para a próxima etapa.
```
