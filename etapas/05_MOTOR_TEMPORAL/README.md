# Etapa 05 — Motor temporal e eventos de visão

[Plano das etapas](../README.md) · [README central](../../README.md) · [Status](../../docs/STATUS.md)

**Estado inicial:** não iniciada. O estado atualizado deve estar em `docs/STATUS.md`.

## Objetivo

Um vídeo processado gera episódio, evento persistido na outbox e incidente no painel, com explicação dos sinais.

## Dependências

Etapa 04 concluída; contrato de ingestão da 02 e painel da 03 disponíveis.

## Leitura obrigatória

Além de `AGENTS.md`, README central e status:

- [03_CONTRATOS_E_DADOS.md](../../docs/03_CONTRATOS_E_DADOS.md)
- [04_MOTOR_DE_EVENTOS.md](../../docs/04_MOTOR_DE_EVENTOS.md)
- [07_VALIDACAO_E_DEMO.md](../../docs/07_VALIDACAO_E_DEMO.md)

## Áreas de trabalho

services/edge (features, engine, outbox, delivery, evaluation), fixtures e relatórios.

Os caminhos de aplicação são entregas a criar/adaptar, não arquivos já presentes neste pacote. Ajustes em etapas anteriores são permitidos quando necessários para integrar corretamente, com motivo no relatório.

## Atividades

1. Implementar features com correção de proporção e validação de landmarks. Parametrizar limiares iniciais e registrar policyVersion/calibrationVersion.
2. Implementar estados OBSERVING/SUSPECTED/ACTIVE/REARMING como núcleo puro com relógio fornecido pelas observações. Tempo, cobertura válida e lacunas determinam persistência; não contar apenas frames.
3. Criar um evento por episódio. Usar PERSON_ON_FLOOR sem trajetória suficiente; POSSIBLE_FALL somente com a descida observada e a condição persistente de piso.
4. Implementar SQLite e transação atômica de episódio ativo + evento de outbox. Restaurar episódio ativo no reinício sem reutilizar relógio monotônico anterior.
5. Criar entrega HTTP básica a partir da outbox, com mesmo eventId em reenvio e ACK após persistência. Mode REPLAY para arquivos; não adulterar para LIVE para disparar avisos.
6. Associar pose/sinais de evidência de um instante e versões; respeitar EVIDENCE_MODE none/skeleton. Enviar somente metadados do evento.
7. Criar CLI evaluate e relatório de episódios comparado ao manifesto. Usar fixtures sintéticas para trajetórias e vídeos reais autorizados para observar limitações.

## Critérios de conclusão

- [ ] Fixtures cobrem candidato breve, candidato persistente, descida sem postura de chão, rearmamento, lacuna, múltiplas poses e postura prolongada.
- [ ] Variar FPS e velocidade do replay não troca duração de cena por duração de processamento.
- [ ] Reiniciar com episódio ativo não cria segundo incidente para a mesma cena; após rearmar, uma situação nova cria outro.
- [ ] Um arquivo real autorizado produz ao menos um evento pela análise, ou a etapa fica parcial com causa registrada.
- [ ] Painel mostra evento como REPLAY, sinais e versões. Um comando simulador não conta para este teste.
- [ ] Resultados de confundidores e limitações aparecem no relatório, inclusive quando desfavoráveis.
- [ ] `docs/STATUS.md` e `docs/RELATORIOS/ETAPA_05.md` refletem a situação real.

## Limites desta etapa

Não usar LLM/VLM para decidir emergência, não treinar em feedback automático e não afirmar detecção clínica. Resiliência completa e webcam ficam para 06.

## Entrega para o fundador

Demonstrar o objetivo desta etapa e fornecer comandos reais de reprodução. Separar verificado, parcialmente verificado e não executado. Usar o modelo em [relatórios](../../docs/RELATORIOS/README.md). Não concluir a etapa apenas porque arquivos foram criados ou o build passou.

## Prompt para o ChatGPT do VS Code

Copie o bloco inteiro com a pasta do projeto aberta. O prompt manda a IA ler este README e seus critérios, portanto não é necessário colar toda a documentação na conversa.

```text
Você está no repositório Radar de Acontecimentos. Implemente somente a ETAPA 05: Motor temporal e eventos de visão.

Antes de editar, leia:
- AGENTS.md
- README.md
- docs/STATUS.md
- etapas/05_MOTOR_TEMPORAL/README.md
- docs/03_CONTRATOS_E_DADOS.md
- docs/04_MOTOR_DE_EVENTOS.md
- docs/07_VALIDACAO_E_DEMO.md

Faça um inventário do código existente e preserve alterações do fundador. Confirme as dependências desta etapa pelo código e pelos relatórios, sem presumir que já foram implementadas.

Foco desta entrega:
Construa o motor temporal puro e ligue-o ao pipeline de arquivo, SQLite e API. Preserve distinção entre episódio local e incidente humano. Teste deduplicação e rearmamento; explique os sinais e falhas sem apresentar scores como probabilidade de socorro necessário.

Execute as atividades e os critérios de conclusão descritos no README desta etapa. Não pare só no plano: produza a implementação e execute as verificações pertinentes disponíveis. Resolva decisões rotineiras com a documentação. Se faltar uma ação física, credencial ou dado indispensável, prepare o restante e peça apenas a informação concreta que bloqueia a validação.

Use a stack e os contratos fixados. Não adicione funcionalidades de etapas posteriores, contas pagas, envio externo, deploy, publicação ou compras. Não invente testes, compatibilidade, medições ou resultados. Diferencie simulação, replay e câmera ao vivo.

Ao concluir, atualize docs/STATUS.md e crie/atualize docs/RELATORIOS/ETAPA_05.md. Relate arquivos alterados, comandos realmente executados, resultados, decisões, pendências e como reproduzir. Se houver requisito não verificado, marque parcial em vez de concluir. Não avance automaticamente para a próxima etapa.
```
