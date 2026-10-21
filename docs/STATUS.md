# Status de construção

**Última atualização:** 21/10/2026 — pacote de documentação preparado.

**Software implementado:** não. **Modelo executado:** não. **Câmeras testadas:** nenhuma. **Próxima etapa:** 00.

Este arquivo é a fonte de verdade de progresso. Os READMEs das etapas apresentam o plano; só atualizar para concluída quando os critérios tiverem evidência real.

| Etapa | Entrega | Status | Relatório / data |
| --- | --- | --- | --- |
| 00 | [Fundação do repositório e ambiente](../etapas/00_FUNDACAO/README.md) | NÃO INICIADA | — |
| 01 | [Domínio, banco e acesso](../etapas/01_DOMINIO_E_ACESSO/README.md) | NÃO INICIADA | — |
| 02 | [Eventos, incidentes e contratos](../etapas/02_EVENTOS_E_INCIDENTES/README.md) | NÃO INICIADA | — |
| 03 | [Painel e primeira demonstração](../etapas/03_PAINEL_E_SIMULADOR/README.md) | NÃO INICIADA | — |
| 04 | [Visão computacional em arquivo](../etapas/04_VISAO_EM_VIDEO/README.md) | NÃO INICIADA | — |
| 05 | [Motor temporal e eventos de visão](../etapas/05_MOTOR_TEMPORAL/README.md) | NÃO INICIADA | — |
| 06 | [Webcam, disponibilidade e recuperação](../etapas/06_WEBCAM_E_RESILIENCIA/README.md) | NÃO INICIADA | — |
| 07 | [Evidência opcional, retenção e proteção](../etapas/07_EVIDENCIA_E_PROTECAO/README.md) | NÃO INICIADA | — |
| 08 | [Validação final e entrega da demo](../etapas/08_VALIDACAO_E_ENTREGA/README.md) | NÃO INICIADA | — |
| 09 | [Câmera IP e verificação da KAP-S069](../etapas/09_CAMERA_IP_OPCIONAL/README.md) | NÃO INICIADA · opcional | — |

## Estados permitidos

`NÃO INICIADA`, `EM ANDAMENTO`, `PARCIAL`, `BLOQUEADA`, `CONCLUÍDA`. Para 09 também `DISPENSADA` se o fundador decidir não testar IP. Incompatibilidade comprovada da câmera pode concluir a investigação opcional; não equivale a suporte RTSP no aparelho.

## Registro do ambiente

| Item | Valor verificado |
| --- | --- |
| SO / arquitetura do computador de implementação | A verificar na etapa 00 |
| CPU / RAM / GPU | A verificar na etapa 00; GPU não obrigatória |
| Versões exatas Node / pnpm / Python / uv | A verificar e fixar na etapa 00 |
| MediaPipe / OpenCV / bundle e hash | Biblioteca na 00; modelo na 04 |
| Webcam e índice | Hardware informado; teste na 06 |
| KAP-S069 / firmware / protocolo | Não confirmado; etapa 09 opcional |

## Pendências atuais

- Iniciar implementação pela etapa 00.
- Preparar vídeos próprios/autorizados para a etapa 04.
- Executar testes físicos de webcam quando chegar à etapa 06.
- Manter KAP-S069 como extensão opcional até confirmar acesso ao stream.

## Histórico de avanço

| Data | Etapa/decisão | Evidência |
| --- | --- | --- |
| 21/10/2026 | Documentação de construção organizada; demo antes de parceiro | D01 em decisões; ainda não há código de produto |

## Regra de atualização

Ao terminar uma etapa, incluir link relativo para seu relatório real, comandos/testes executados, pendências e próxima etapa elegível. Não apagar falhas históricas; registrar correção. Nunca marcar um teste físico como feito apenas porque existe um adaptador implementado.
