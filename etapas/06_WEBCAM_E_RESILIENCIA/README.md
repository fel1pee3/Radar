# Etapa 06 — Webcam, disponibilidade e recuperação

[Plano das etapas](../README.md) · [README central](../../README.md) · [Status](../../docs/STATUS.md)

**Estado inicial:** não iniciada. O estado atualizado deve estar em `docs/STATUS.md`.

## Objetivo

Pipeline ao vivo com webcam, saúde visível, buffer limitado, fila persistente e recuperação comprovada.

## Dependências

Etapa 05 concluída; webcam acessível no computador do fundador para o teste físico.

## Leitura obrigatória

Além de `AGENTS.md`, README central e status:

- [02_ARQUITETURA_E_STACK.md](../../docs/02_ARQUITETURA_E_STACK.md)
- [03_CONTRATOS_E_DADOS.md](../../docs/03_CONTRATOS_E_DADOS.md)
- [04_MOTOR_DE_EVENTOS.md](../../docs/04_MOTOR_DE_EVENTOS.md)
- [05_CAMERAS_E_CALIBRACAO.md](../../docs/05_CAMERAS_E_CALIBRACAO.md)
- [07_VALIDACAO_E_DEMO.md](../../docs/07_VALIDACAO_E_DEMO.md)
- [08_AMBIENTE_E_COMANDOS.md](../../docs/08_AMBIENTE_E_COMANDOS.md)

## Áreas de trabalho

services/edge, saúde na API/web, testes de falhas e documentação de execução física.

Os caminhos de aplicação são entregas a criar/adaptar, não arquivos já presentes neste pacote. Ajustes em etapas anteriores são permitidos quando necessários para integrar corretamente, com motivo no relatório.

## Atividades

1. Adicionar WEBCAM ao FrameSource, índice explícito, relógio monotônico e captura separada da análise por buffer do frame mais recente. Implementar probe e diagnóstico do dispositivo.
2. Executar Python no host; documentar permissões e conflitos de acesso. Não contornar limitações de webcam no WSL fingindo entrada real.
3. Implementar heartbeat Python atual a cada 5 s, mudanças de estado, encerramento limpo, conflito de run e status no painel. Não enfileirar heartbeat histórico.
4. Implementar flags de captura/frame timeout/FPS/baixa luz/congelamento suspeito e motivo de inferência inelegível. Não repetir frame antigo como observação nova.
5. Completar envio resiliente: timeouts, backoff com jitter, ACK idempotente, erros permanentes/revogação, limite de outbox e limpeza apenas de confirmados. SQLite fica privado.
6. Testar API indisponível, reinício do worker, retorno do backend, credencial revogada, relógio incoerente e eventos atrasados. Registrar situação local mesmo quando a API está fora.
7. Validar webcam e enquadramento físico; realizar cenário seguro de postura no chão apenas se viável. Não provocar queda. Registrar dados do hardware e indicadores medidos.

## Critérios de conclusão

- [ ] Teste físico de webcam está realizado e relatado; se a IA não tem acesso, deixar etapa parcial até o fundador executar.
- [ ] Interromper captura e worker produz estados corretos; não aparecem falsos “tudo normal”.
- [ ] Parar API durante emissão, reiniciar worker e restaurar API preserva evento e não duplica incidente/aviso.
- [ ] Reenvio atrasado mantém horários e não gera urgência nova; fila com erro permanente tem diagnóstico.
- [ ] Não há crescimento ilimitado de frames/outbox nem segredos em logs.
- [ ] Teste ao vivo e simulação estão rotulados de forma diferente.
- [ ] `docs/STATUS.md` e `docs/RELATORIOS/ETAPA_06.md` refletem a situação real.

## Limites desta etapa

Não integrar KAP-S069 nesta etapa obrigatória, não abrir rede externa, não comprar hardware e não prometer funcionamento 24h.

## Entrega para o fundador

Demonstrar o objetivo desta etapa e fornecer comandos reais de reprodução. Separar verificado, parcialmente verificado e não executado. Usar o modelo em [relatórios](../../docs/RELATORIOS/README.md). Não concluir a etapa apenas porque arquivos foram criados ou o build passou.

## Prompt para o ChatGPT do VS Code

Copie o bloco inteiro com a pasta do projeto aberta. O prompt manda a IA ler este README e seus critérios, portanto não é necessário colar toda a documentação na conversa.

```text
Você está no repositório Radar de Acontecimentos. Implemente somente a ETAPA 06: Webcam, disponibilidade e recuperação.

Antes de editar, leia:
- AGENTS.md
- README.md
- docs/STATUS.md
- etapas/06_WEBCAM_E_RESILIENCIA/README.md
- docs/02_ARQUITETURA_E_STACK.md
- docs/03_CONTRATOS_E_DADOS.md
- docs/04_MOTOR_DE_EVENTOS.md
- docs/05_CAMERAS_E_CALIBRACAO.md
- docs/07_VALIDACAO_E_DEMO.md
- docs/08_AMBIENTE_E_COMANDOS.md

Faça um inventário do código existente e preserve alterações do fundador. Confirme as dependências desta etapa pelo código e pelos relatórios, sem presumir que já foram implementadas.

Foco desta entrega:
Leve o pipeline à webcam real e torne as falhas observáveis. Priorize recuperação sem perda/duplicação e honestidade do estado de cobertura. Prepare ações físicas claras para o fundador quando forem indispensáveis e registre quais foram realmente realizadas.

Execute as atividades e os critérios de conclusão descritos no README desta etapa. Não pare só no plano: produza a implementação e execute as verificações pertinentes disponíveis. Resolva decisões rotineiras com a documentação. Se faltar uma ação física, credencial ou dado indispensável, prepare o restante e peça apenas a informação concreta que bloqueia a validação.

Use a stack e os contratos fixados. Não adicione funcionalidades de etapas posteriores, contas pagas, envio externo, deploy, publicação ou compras. Não invente testes, compatibilidade, medições ou resultados. Diferencie simulação, replay e câmera ao vivo.

Ao concluir, atualize docs/STATUS.md e crie/atualize docs/RELATORIOS/ETAPA_06.md. Relate arquivos alterados, comandos realmente executados, resultados, decisões, pendências e como reproduzir. Se houver requisito não verificado, marque parcial em vez de concluir. Não avance automaticamente para a próxima etapa.
```
