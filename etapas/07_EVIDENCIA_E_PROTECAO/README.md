# Etapa 07 — Evidência opcional, retenção e proteção

[Plano das etapas](../README.md) · [README central](../../README.md) · [Status](../../docs/STATUS.md)

**Estado inicial:** não iniciada. O estado atualizado deve estar em `docs/STATUS.md`.

## Objetivo

Controle completo de evidência mínima, snapshot opt-in e expiração, com acessos e exclusões auditados.

## Dependências

Etapa 06 concluída; pipeline e identidade estáveis.

## Leitura obrigatória

Além de `AGENTS.md`, README central e status:

- [03_CONTRATOS_E_DADOS.md](../../docs/03_CONTRATOS_E_DADOS.md)
- [06_SEGURANCA_E_DADOS.md](../../docs/06_SEGURANCA_E_DADOS.md)
- [07_VALIDACAO_E_DEMO.md](../../docs/07_VALIDACAO_E_DEMO.md)

## Áreas de trabalho

módulos Evidence/Audit, UI de evidência, envio opcional Python, jobs de retenção e testes de acesso.

Os caminhos de aplicação são entregas a criar/adaptar, não arquivos já presentes neste pacote. Ajustes em etapas anteriores são permitidos quando necessários para integrar corretamente, com motivo no relatório.

## Atividades

1. Consolidar EVIDENCE_MODE none/skeleton/snapshot. Default skeleton; snapshot só mediante escolha explícita do proprietário. Testes podem usar JPEG sintético sem pessoas.
2. Implementar envio opcional separado após ACK do evento, idempotência por hash, limite de tamanho/pixels, decodificação/reencodificação e remoção de EXIF. Não gravar continuamente.
3. Guardar arquivos em diretório privado e servi-los por autorização de tenant/incidente. Implementar estados ausente, expirado e indisponível no painel.
4. Implementar exclusão/expiração e limpeza idempotente conforme política. Remover pose de todas as cópias persistidas, inclusive payload do recibo, mantendo hash de deduplicação e marcador de redação; não alterar os fatos do evento.
5. Apagar snapshot local após ACK de imagem; expirar pendente sem perder evento. Limpar apenas outbox confirmada no prazo; jamais apagar pendentes por conveniência.
6. Rever logs, limites, cookie/Origin, rotação/revogação de credenciais e isolamento de imagens. Impedir path traversal e acesso por URL pública.
7. Testar tarefas de limpeza após reinício e atualizar documentação de retenção/backup. Não declarar conformidade legal por passar nos testes.

## Critérios de conclusão

- [ ] Modo padrão não captura/envia JPEG; snapshot opt-in funciona com imagem sintética e autorização registrada para qualquer imagem real.
- [ ] Imagem inválida, excessiva ou de outro tenant é rejeitada; endpoint não é público.
- [ ] Expiração elimina bytes/pontos das cópias aplicáveis, mas mantém incidente e deduplicação de reenvio.
- [ ] Excluir imagem é auditado e não encerra incidente; falha de upload não perde alerta.
- [ ] Busca em logs de teste não encontra segredos fictícios injetados.
- [ ] A configuração local continua restrita a loopback e não há envio a terceiros.
- [ ] `docs/STATUS.md` e `docs/RELATORIOS/ETAPA_07.md` refletem a situação real.

## Limites desta etapa

Não criar pipeline de vídeo na nuvem, reconhecimento facial, compliance genérico, classificação de pessoas ou integrações externas.

## Entrega para o fundador

Demonstrar o objetivo desta etapa e fornecer comandos reais de reprodução. Separar verificado, parcialmente verificado e não executado. Usar o modelo em [relatórios](../../docs/RELATORIOS/README.md). Não concluir a etapa apenas porque arquivos foram criados ou o build passou.

## Prompt para o ChatGPT do VS Code

Copie o bloco inteiro com a pasta do projeto aberta. O prompt manda a IA ler este README e seus critérios, portanto não é necessário colar toda a documentação na conversa.

```text
Você está no repositório Radar de Acontecimentos. Implemente somente a ETAPA 07: Evidência opcional, retenção e proteção.

Antes de editar, leia:
- AGENTS.md
- README.md
- docs/STATUS.md
- etapas/07_EVIDENCIA_E_PROTECAO/README.md
- docs/03_CONTRATOS_E_DADOS.md
- docs/06_SEGURANCA_E_DADOS.md
- docs/07_VALIDACAO_E_DEMO.md

Faça um inventário do código existente e preserve alterações do fundador. Confirme as dependências desta etapa pelo código e pelos relatórios, sem presumir que já foram implementadas.

Foco desta entrega:
Feche o tratamento de evidência e dados com defaults mínimos. A autorização de snapshot é uma escolha real do proprietário, nunca uma suposição da IA. Verifique todas as cópias de pose e imagem na retenção, preservando idempotência após redação.

Execute as atividades e os critérios de conclusão descritos no README desta etapa. Não pare só no plano: produza a implementação e execute as verificações pertinentes disponíveis. Resolva decisões rotineiras com a documentação. Se faltar uma ação física, credencial ou dado indispensável, prepare o restante e peça apenas a informação concreta que bloqueia a validação.

Use a stack e os contratos fixados. Não adicione funcionalidades de etapas posteriores, contas pagas, envio externo, deploy, publicação ou compras. Não invente testes, compatibilidade, medições ou resultados. Diferencie simulação, replay e câmera ao vivo.

Ao concluir, atualize docs/STATUS.md e crie/atualize docs/RELATORIOS/ETAPA_07.md. Relate arquivos alterados, comandos realmente executados, resultados, decisões, pendências e como reproduzir. Se houver requisito não verificado, marque parcial em vez de concluir. Não avance automaticamente para a próxima etapa.
```
