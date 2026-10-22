# Status de construção

**Última atualização — 22/10/2026:** etapa 07 **CONCLUÍDA no escopo solicitado**.
Evidência mínima, JPEG pontual sintético, armazenamento privado, acesso/exclusão
por papel, auditoria, retenção e deduplicação após redação/purga verificados.
262 testes Python, 145 API, 91 contratos TS e 18 E2E aprovados; demonstração
sintética desktop adicional aprovada. Lint, tipos, build e instalações frozen
aprovados; OpenAPI regenerado. Migração aditiva aplicada em 15432, contagens de
cadastros/incidentes/recibos/auditoria preservadas. Webcam real permanece skeleton,
sem JPEG e sem nova captura. Limpeza automática API e purga de 30 dias não foram
ativadas no ambiente pessoal; os testes usaram recursos exclusivos e relógio
injetável. Commit e push autorizados pelo fundador em 22/10/2026; sem deploy; etapa 08 não iniciada. Veja [relatório 07](RELATORIOS/ETAPA_07.md)
e [roteiro 07](VALIDACAO_MANUAL_ETAPA_07.md).

**Histórico — 22/10/2026:** etapa 06 **CONCLUÍDA no escopo da bancada**.
Calibração WEBCAM v1 e pose no corpo conferidas pelo fundador. Sessão de 384
análises em 83,72 s, vazão global 4,59 análises/s, inferência média 25,34 ms;
sessão guiada posterior de 981 análises em 231,23 s terminou sem erro.
Fundador confirmou no painel LIVE → Pausada → retomada → Fonte encerrada,
e fechamento da janela. Frames novos e estados foram conferidos localmente e
no servidor. Recuperação/limites/duplicação verificados em recursos dedicados;
243 testes Python aprovados e 125 API/87 contratos TS anteriores preservados.
Pose falsa na estante, fluidez em 5 Hz e falta de evento LIVE positivo são
limitações/pendências da validação final do MVP. Commit/push autorizados pelo
fundador após a validação; sem deploy. Etapa 07 não iniciada.

**Histórico anterior — 21/10/2026:** etapa 06 parcial naquele momento, com captura
física e inferência em um frame, mas sem calibração. A abertura de calibração pela
IA retornou ValueError/CONFIG_OR_ENVIRONMENT_ERROR, sem causa identificada. O
fundador concluiu a calibração e uma sessão contínua em 22/10; o erro anterior não
reapareceu nessa execução, sem comprovar sua causa. A regressão API de 125 testes
e os testes de entrega/recuperação anteriores continuam registrados no relatório.

**Software implementado:** fundação, API, painel, simulador, contratos, FILE e WEBCAM;
motor temporal, SQLite com retomada/limites, envio/heartbeat independentes e
controles locais. **Modelo executado:** Lite/Full CPU/VIDEO em arquivos; Full
também em sessão física contínua, com pose no corpo conferida pelo fundador e
falso reconhecimento de estante relatado. Origem dos arquivos reais anteriores
declarada pelo fundador, sem verificação independente da internet; vídeo gerado
por IA permanece separado. **Câmera física:** índice 0 escolhido pelo fundador,
DSHOW, 640×480, prévia conferida; inventário Windows lista Positivo Theia Camera.
**Última etapa concluída:** 07; 08 elegível somente por nova solicitação.

Este arquivo é a fonte de verdade de progresso. Os READMEs das etapas apresentam o plano; só atualizar para concluída quando os critérios tiverem evidência real.

| Etapa | Entrega | Status | Relatório / data |
| --- | --- | --- | --- |
| 00 | [Fundação do repositório e ambiente](../etapas/00_FUNDACAO/README.md) | CONCLUÍDA | [ETAPA_00](RELATORIOS/ETAPA_00.md) · 21/10/2026 |
| 01 | [Domínio, banco e acesso](../etapas/01_DOMINIO_E_ACESSO/README.md) | CONCLUÍDA | [ETAPA_01](RELATORIOS/ETAPA_01.md) · 21/10/2026 |
| 02 | [Eventos, incidentes e contratos](../etapas/02_EVENTOS_E_INCIDENTES/README.md) | CONCLUÍDA | [ETAPA_02](RELATORIOS/ETAPA_02.md) · 21/10/2026 |
| 03 | [Painel e primeira demonstração](../etapas/03_PAINEL_E_SIMULADOR/README.md) | CONCLUÍDA | [ETAPA_03](RELATORIOS/ETAPA_03.md) · 21/10/2026 |
| 04 | [Visão computacional em arquivo](../etapas/04_VISAO_EM_VIDEO/README.md) | CONCLUÍDA | [ETAPA_04](RELATORIOS/ETAPA_04.md) · 21/10/2026 |
| 05 | [Motor temporal e eventos de visão](../etapas/05_MOTOR_TEMPORAL/README.md) | CONCLUÍDA | [ETAPA_05](RELATORIOS/ETAPA_05.md) · 21/10/2026 |
| 06 | [Webcam, disponibilidade e recuperação](../etapas/06_WEBCAM_E_RESILIENCIA/README.md) | CONCLUÍDA · bancada | [ETAPA_06](RELATORIOS/ETAPA_06.md) · 22/10/2026 |
| 07 | [Evidência opcional, retenção e proteção](../etapas/07_EVIDENCIA_E_PROTECAO/README.md) | CONCLUÍDA | [ETAPA_07](RELATORIOS/ETAPA_07.md) · 22/10/2026 |
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
| MediaPipe / OpenCV / bundle e hash | MediaPipe 1.1.1 e único opencv-contrib-python 5.0.0.93 (cv2 5.0.0); Tasks Lite float16/v1, SHA-256 59929e1d1ee95287735ddd833b19cf4ac46d29bc7afddbbf6753c459690d574a; inferência CPU real em sintético e em arquivo autorizado de pessoa; [inventário](RELATORIOS/DEPENDENCIAS_E_MODELOS.md) |
| Docker / banco | Desktop 4.57.0, Engine 29.1.3, Compose 5.0.1; PostgreSQL 17.11 saudável; TCP autenticado e volume persistente verificados; loopback 15432 nesta máquina (D15) |
| Persistência / acesso (01) | Prisma/client/adapter-pg 7.10.1, pg 8.23.1, Argon2 0.45.1; migração inicial aplicada em radar:15432 e banco vazio dedicado; 19 testes de integração aprovados |
| Eventos / contratos (02) | Migração 20261021000200_events_incidents aplicada em banco vazio exclusivo e radar:15432; 19 testes anteriores + 104 novos aprovados; contratos: 87 TS e 87 Python; roteiro PowerShell exercitado por HTTP real em banco isolado |
| Painel / demonstração (03) | Playwright 1.64.1/Chromium 156.0.8078.4; 16 E2E reais aprovados em desktop 1440×1000 e móvel 390×844; 123 regressões API e87 + 87 contratos preservadas; screenshots sintéticas privadas inspecionadas |
| Visão em arquivo (04) | Python 3.12.15/uv 0.13.4 preservados; PyYAML 6.0.3 novo, NumPy 2.5.4 mantido e declarado direto; 139 testes Python, incluindo 87 contratos, e 87 contratos TS aprovados; arquivo bancada-01: 530 frames/89 observações, mesma sequência em três velocidades; seleção do piso e conferência visual realizadas pelo fundador |
| Webcam e índice | Etapa 06 concluída para bancada: índice 0/DSHOW, 640×480, Full/piso v1. Probe inicial 10 FPS, sessão contínua de 384 análises e sessão guiada de 981 análises, controles conferidos no painel. Zero candidatos/eventos nos dois ensaios; pose falsa na estante relatada. 243 Python, 125 API/87 contratos TS; checks aprovados, sem comprovar evento LIVE positivo |
| Motor temporal (05) | Sem dependências novas/lock alterado; SQLite nativo; 226 testes Python e 124 API em PostgreSQL exclusivo; 87 contratos TS. Full oficial fixado por hash, 45 análises/40 elegíveis/32 candidatas em piso-f-07; evento aos 6000 ms, incidente REPLAY/TEST conferido. Evaluate sem espera/2× reproduziu o offset; EOF/reenvio sem duplicação |
| KAP-S069 / firmware / protocolo | Não confirmado; etapa 09 opcional |

## Pendências atuais

- Nenhum critério obrigatório da etapa 07 pendente. JPEG funcional comprovado com
  pixels sintéticos sem pessoas, sem ativar snapshot real. Agendamento API default
  false e purga de metadados false são escolhas operacionais preservadas, não
  declaração de dados já apagados. Rodada explícita e job habilitado verificados
  em banco/diretório exclusivos; [roteiro 07](VALIDACAO_MANUAL_ETAPA_07.md).
- Na avaliação final da 08 permanecem as limitações anteriores de percepção,
  incluindo estante, fluidez e evento LIVE positivo. A 07 não alterou detector.

- Nenhuma verificação obrigatória da etapa 00 pendente. Reprodução em [ambiente e comandos](08_AMBIENTE_E_COMANDOS.md).
- Nenhum critério obrigatório da etapa 01 pendente. Proprietário criado localmente pelo fundador e confirmado por contagem de OWNER ativo/auditoria, sem consulta de senha/hash. Login/configuração por PowerShell no [roteiro manual](VALIDACAO_MANUAL_ETAPA_01.md); a interface foi acrescentada na etapa 03.
- Nenhum critério obrigatório da etapa 02 pendente. Fluxo HTTP/PowerShell, transações, concorrência, ações, isolamento, classes de tempo, heartbeat e recuperação de avisos verificados; [relatório](RELATORIOS/ETAPA_02.md) e [roteiro manual](VALIDACAO_MANUAL_ETAPA_02.md). Nenhuma tela de incidentes, captura, inferência, snapshot ou comunicação externa implementada nesta etapa; retenção automática permanece na 07.
- Nenhum critério obrigatório da etapa 03 pendente. Painel/simulador com persistência real, retry/conflito, falha/expiração, RBAC, polling e layout verificados; [relatório](RELATORIOS/ETAPA_03.md) e [roteiro de apresentação](VALIDACAO_MANUAL_ETAPA_03.md). Inspeção visual em Chromium; móvel físico/outros navegadores e teclas interativas da CLI não foram verificados. Simulação comprova o fluxo de software, não IA ou câmera.
- Uso manual revelou falha de transporte após gravar o incidente: a API em modo watch reiniciou no mesmo intervalo. O comando do simulador deixou de recompilar contratos e ganhou retry limitado com envelope estável e erro de encerramento explícito. Quatro testes de transporte e um E2E real desktop aprovados após a correção; a execução original do fundador permaneceu parcial, sem confirmação de ENDED. O incidente persistido pode ser revisado normalmente; não foi substituído nem duplicado pelos testes.
- Monitorar compatibilidade dos plugins React/a11y antes de atualizar ESLint 9 (aviso de fim de suporte registrado no inventário).
- Nenhum critério obrigatório da etapa 04 pendente. O arquivo autorizado `bancada-01` terminou em três replays (sem espera, 2×, prévia 0,5×): 530 frames lidos, 89 analisados, 84 observações com qualidade suficiente e 5 de baixa confiança, sem fallback temporal. O fundador marcou o piso e confirmou o alinhamento da pose/região; [roteiro 04](VALIDACAO_MANUAL_ETAPA_04.md), [relatório 04](RELATORIOS/ETAPA_04.md). Isso não mede eficácia de queda; múltiplas pessoas reais não foram testadas. Aviso oficial do SDK sobre métricas de uso registrado; ausência total de tráfego nativo não foi comprovada e firewall foi preservado. A retenção do vídeo privado é manual, sem prazo automático configurado.
- Nenhuma verificação obrigatória da etapa 06 pendente no escopo solicitado.
  Fundador confirmou piso, pose, pausa, retomada e encerramento no painel.
  Para a validação final do MVP: investigar pose falsa na estante em ensaio
  negativo delimitado e medir eficácia com anotações, sem confundir zero eventos
  nestas sessões com rejeição garantida de objetos. Fluidez acompanha análise em 5 Hz.
  Morte abrupta do adaptador físico com heartbeat liberou o driver e resultou em
  OFFLINE após mais de 15 s; o teste não teve inferência nem conferência visual. Evento LIVE
  positivo não foi observado e permanece para a validação final do MVP.
  [Roteiro 06](VALIDACAO_MANUAL_ETAPA_06.md) e [relatório 06](RELATORIOS/ETAPA_06.md).
- A janela de calibração usa imagem parada para marcar o piso; isso foi
  esclarecido após o fundador esperar vídeo ao vivo. Título e instruções ajustados;
  o roteiro separa probe (movimento), calibrate (pontos) e run (análise).
  A interação não concluiu a calibração nem a validação física integrada.
- A tentativa posterior de abrir calibrate pela IA falhou com
  CONFIG_OR_ENVIRONMENT_ERROR (ValueError). Causa histórica ainda desconhecida;
  em 22/10 o fundador salvou a calibração v1 e executou o pipeline. Não afirmar
  correção da causa por não ter reaparecido nessa tentativa.
- Prévia preta posterior: fundador confirmou tampinha de privacidade fechada.
  Depois confirmou que conseguiu conferir o enquadramento ao vivo seguindo o
  roteiro em pé, com corpo inteiro/chão. Sem alteração de driver/backend/permissões.
  Depois salvou o piso e conferiu pose durante run. A prévia probe anterior
  não executava inferência; controles no painel confirmados posteriormente.
- As duas cenas adicionais fornecidas pelo fundador, deitar em vista lateral e
  pessoa deitada em vista de cima, foram calibradas e processadas. Nenhuma gerou
  evento: o modelo não sustentou pontos essenciais suficientes. Não há incidente
  positivo novo para conferir no painel; a baseline permanece experimental e a
  prova positiva da 05 ficou pendente naquela fase, antes do ensaio Full.
- A quarta filmagem real, `piso-d`, terminou com 78 observações, 58 elegíveis e
  zero candidatas/eventos. O fundador confirmou piso, orientação correta e pessoa
  deitada durante vários segundos na prévia local. Quadril no piso em 58/58,
  mas ângulo de tronco 0,16–51,46° (mínimo 60°) e razão altura/largura 1,02–2,06
  (máximo 1). É uma falha observada da baseline nessa cena, compatível com uma
  limitação de projeção em 2D; não é solucionada apenas remarcando o piso.
  Nenhum gate ou rotação foi alterado para forçar detecção. Não há anotação
  temporal completa para estimar taxas de eficácia.
- Os arquivos seguintes, `piso-e-05` e `piso-f-07`, foram descritos como filmagens
  reais encontradas na internet, sem URL/licença ou origem verificadas. Ambos
  receberam calibração manual e terminaram normalmente, com zero eventos:
  51 análises/15 elegíveis/zero candidatas no primeiro e
  45 análises/15 elegíveis/6 candidatas sem janela suficiente no segundo.
  Não houve ajuste de parâmetros nem envio de mídia; outboxes separadas.
  O fundador reviu as duas prévias e relatou esqueleto verde piscando/sumindo,
  reconhecível mas insatisfatório. A instabilidade visual é coerente com os
  pontos insuficientes medidos; precisa ser tratada antes da prova positiva.
- Nenhum critério obrigatório da etapa 05 pendente. A configuração validada é
  `.local/edge-piso-f-07-full.yaml`: um evento real, entregue ao incidente
  `6cfd7d88-ae34-4b48-ad5a-d592cbd020a9`. Fundador conferiu prévia e painel.
  Os resultados negativos acima pertencem aos ensaios anteriores e não foram
  apagados. Full não resolveu o enquadramento `piso-d` nem todos os casos de baixa
  visibilidade. Evaluate permanece CALIBRATION, sem anotações completas; eficácia
  não estimável. Retenção foi acrescentada na 07; agendamento API e purga do fundador continuam desligados. [Roteiro 05](VALIDACAO_MANUAL_ETAPA_05.md),
  [relatório 05](RELATORIOS/ETAPA_05.md) e [investigação](RELATORIOS/INVESTIGACAO_ETAPA_05.md).
- Manter KAP-S069 como extensão opcional até confirmar acesso ao stream.

## Histórico de avanço

Validação adicional da 05: o fundador marcou pisos separados para `piso-a`
(lateral) e `piso-b` (vista de cima). Ambos terminaram normalmente, sem evento;
modelo/política/gates preservados. Limitações e hashes no [relatório 05](RELATORIOS/ETAPA_05.md).

Novo ensaio `piso-d`: filmagem de câmera/celular confirmada pelo fundador, piso
marcado e prévia conferida. Pessoa deitada não detectada pelos critérios em 2D;
resultado desfavorável registrado, mantendo a etapa parcial.

| Data | Etapa/decisão | Evidência |
| --- | --- | --- |
| 21/10/2026 | Documentação de construção organizada; demo antes de parceiro | D01 em decisões; ainda não há código de produto |
| 21/10/2026 | Etapa 00 concluída; PostgreSQL em porta alternativa local (D15) | Instalações frozen inclusive em diretórios vazios; lint, typecheck, build, Ruff, imports Python, HTTP direto/proxy, captura Edge e persistência do volume; [relatório](RELATORIOS/ETAPA_00.md) |
| 21/10/2026 | Etapa 01 concluída: domínio/acesso, migração e proprietário local | 19 testes reais em PostgreSQL exclusivo; seed/CLI, sessões, papéis, FKs de tenant, rotação concorrente, falha/retomada do banco, logs e bootstrap real confirmado; [relatório](RELATORIOS/ETAPA_01.md) |
| 21/10/2026 | Etapa 02 concluída: contratos, eventos, incidentes, heartbeat e avisos locais | 123 testes API (19 anteriores + 104 novos), 87 TS e 87 Python; migração aditiva preservou um OWNER, um local, duas câmeras e volume da demo; [relatório](RELATORIOS/ETAPA_02.md) |
| 21/10/2026 | Etapa 03 concluída: painel responsivo e simulador bearer | 16 E2E desktop/móvel com PostgreSQL/API/web exclusivos, pose sintética/revisão/aviso persistentes e regressões aprovadas; [relatório](RELATORIOS/ETAPA_03.md) |
| 21/10/2026 | Etapa 04 concluída: FILE→Tasks CPU→observações/ROI/prévia/medidas | 139 testes Python, 87 TS, modelo real em sintético e em arquivo autorizado; três replays completos com sequência idêntica, piso e prévia conferidos pelo fundador; [relatório](RELATORIOS/ETAPA_04.md) |
| 21/10/2026 | Etapa 05 inicialmente parcial: motor/SQLite/checkpoints/transporte/evaluate | 185 Python, 124 API, 87 TS; seis filmagens sem evento com Lite. Resultados negativos preservados no relatório |
| 21/10/2026 | Etapa 05 concluída após investigação e seleção explícita do Full (D34) | 226 Python, 124 API, 87 TS; evento real aos 6000 ms, entrega/reenvio/EOF sem duplicação, prévia e incidente conferidos pelo fundador; [relatório](RELATORIOS/ETAPA_05.md) |
| 21/10/2026 | Etapa 06 parcial: webcam nativa, saúde, limites e recuperação | Índice 0/DSHOW físico, pausa/retomada e Full em frame real; 125 API exclusivos. Credencial salva pelo fundador e autenticada; piso indisponível impede calibração/conferência integrada. [Relatório](RELATORIOS/ETAPA_06.md) |
| 22/10/2026 | Etapa 06 concluída no escopo de captura/saúde/recuperação de bancada | Piso próprio, Full contínuo, 384 + 981 análises; fundador confirmou pausa/retomada/encerramento no painel. 243 Python e verificações anteriores preservadas; falso esqueleto de estante e evento LIVE positivo pendentes para validação final. [Relatório](RELATORIOS/ETAPA_06.md) |
| 22/10/2026 | Etapa 07 concluída: evidência opcional/retencão/proteção | JPEG sintético, permissões, exclusão, recuperação e relógio controlado; 262 Python, 145 API, 91 TS, 18 E2E e demo desktop. Migração preservou dados; JPEG real/purga pessoal não habilitados. [Relatório](RELATORIOS/ETAPA_07.md) |

## Regra de atualização

Ao terminar uma etapa, incluir link relativo para seu relatório real, comandos/testes executados, pendências e próxima etapa elegível. Não apagar falhas históricas; registrar correção. Nunca marcar um teste físico como feito apenas porque existe um adaptador implementado.
