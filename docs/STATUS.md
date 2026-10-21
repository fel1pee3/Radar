# Status de construção

**Última atualização:** 21/10/2026 — etapa 02 implementada e verificada; proprietário, configurações e volume anteriores preservados.

**Software implementado:** fundação, domínio/acesso e API de eventos/incidentes/heartbeat/avisos simulados, com contratos TS/Python. **Modelo executado:** não. **Câmeras físicas testadas:** nenhuma. **Próxima etapa elegível:** 03, somente mediante nova solicitação.

Este arquivo é a fonte de verdade de progresso. Os READMEs das etapas apresentam o plano; só atualizar para concluída quando os critérios tiverem evidência real.

| Etapa | Entrega | Status | Relatório / data |
| --- | --- | --- | --- |
| 00 | [Fundação do repositório e ambiente](../etapas/00_FUNDACAO/README.md) | CONCLUÍDA | [ETAPA_00](RELATORIOS/ETAPA_00.md) · 21/10/2026 |
| 01 | [Domínio, banco e acesso](../etapas/01_DOMINIO_E_ACESSO/README.md) | CONCLUÍDA | [ETAPA_01](RELATORIOS/ETAPA_01.md) · 21/10/2026 |
| 02 | [Eventos, incidentes e contratos](../etapas/02_EVENTOS_E_INCIDENTES/README.md) | CONCLUÍDA | [ETAPA_02](RELATORIOS/ETAPA_02.md) · 21/10/2026 |
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
| SO / arquitetura do computador de implementação | Windows 11 Pro, 10.0.26200, x64; PowerShell 5.1.26100.9711 |
| CPU / RAM / GPU | AMD Ryzen 5 5625U, 6 núcleos/12 threads; 15,4 GiB de RAM visível; AMD Radeon (TM) Graphics; sem teste de aceleração |
| Versões exatas Node / pnpm / Python / uv | 24.22.1 / 10.34.7 / 3.12.15 / 0.13.4; Node 22.21.1 e Python 3.13.7 preexistentes preservados |
| MediaPipe / OpenCV / bundle e hash | MediaPipe 1.1.1 e opencv-contrib-python 5.0.0.93 (cv2 5.0.0), imports reais aprovados; nenhum modelo obtido; [inventário](RELATORIOS/DEPENDENCIAS_E_MODELOS.md) |
| Docker / banco | Desktop 4.57.0, Engine 29.1.3, Compose 5.0.1; PostgreSQL 17.11 saudável; TCP autenticado e volume persistente verificados; loopback 15432 nesta máquina (D15) |
| Persistência / acesso (01) | Prisma/client/adapter-pg 7.10.1, pg 8.23.1, Argon2 0.45.1; migração inicial aplicada em radar:15432 e banco vazio dedicado; 19 testes de integração aprovados |
| Eventos / contratos (02) | Migração 20261021000200_events_incidents aplicada em banco vazio exclusivo e radar:15432; 19 testes anteriores + 104 novos aprovados; contratos: 87 TS e 87 Python; roteiro PowerShell exercitado por HTTP real em banco isolado |
| Webcam e índice | Não consultados nem abertos na 00; teste físico na 06 |
| KAP-S069 / firmware / protocolo | Não confirmado; etapa 09 opcional |

## Pendências atuais

- Nenhuma verificação obrigatória da etapa 00 pendente. Reprodução em [ambiente e comandos](08_AMBIENTE_E_COMANDOS.md).
- Nenhum critério obrigatório da etapa 01 pendente. Proprietário criado localmente pelo fundador e confirmado por contagem de OWNER ativo/auditoria, sem consulta de senha/hash. Login/configuração por PowerShell no [roteiro manual](VALIDACAO_MANUAL_ETAPA_01.md); web permanece mínima.
- Nenhum critério obrigatório da etapa 02 pendente. Fluxo HTTP/PowerShell, transações, concorrência, ações, isolamento, classes de tempo, heartbeat e recuperação de avisos verificados; [relatório](RELATORIOS/ETAPA_02.md) e [roteiro manual](VALIDACAO_MANUAL_ETAPA_02.md). Nenhuma tela de incidentes, captura, inferência, snapshot ou comunicação externa implementada nesta etapa; retenção automática permanece na 07.
- Monitorar compatibilidade dos plugins React/a11y antes de atualizar ESLint 9 (aviso de fim de suporte registrado no inventário).
- Preparar vídeos próprios/autorizados para a etapa 04.
- Executar testes físicos de webcam quando chegar à etapa 06.
- Manter KAP-S069 como extensão opcional até confirmar acesso ao stream.

## Histórico de avanço

| Data | Etapa/decisão | Evidência |
| --- | --- | --- |
| 21/10/2026 | Documentação de construção organizada; demo antes de parceiro | D01 em decisões; ainda não há código de produto |
| 21/10/2026 | Etapa 00 concluída; PostgreSQL em porta alternativa local (D15) | Instalações frozen inclusive em diretórios vazios; lint, typecheck, build, Ruff, imports Python, HTTP direto/proxy, captura Edge e persistência do volume; [relatório](RELATORIOS/ETAPA_00.md) |
| 21/10/2026 | Etapa 01 concluída: domínio/acesso, migração e proprietário local | 19 testes reais em PostgreSQL exclusivo; seed/CLI, sessões, papéis, FKs de tenant, rotação concorrente, falha/retomada do banco, logs e bootstrap real confirmado; [relatório](RELATORIOS/ETAPA_01.md) |
| 21/10/2026 | Etapa 02 concluída: contratos, eventos, incidentes, heartbeat e avisos locais | 123 testes API (19 anteriores + 104 novos), 87 TS e 87 Python; migração aditiva preservou um OWNER, um local, duas câmeras e volume da demo; [relatório](RELATORIOS/ETAPA_02.md) |

## Regra de atualização

Ao terminar uma etapa, incluir link relativo para seu relatório real, comandos/testes executados, pendências e próxima etapa elegível. Não apagar falhas históricas; registrar correção. Nunca marcar um teste físico como feito apenas porque existe um adaptador implementado.
