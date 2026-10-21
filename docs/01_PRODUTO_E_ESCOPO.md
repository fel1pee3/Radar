# Produto e escopo da v0.1

[Voltar ao README central](../README.md)

## Proposta

Software que transforma vídeo autorizado em **suspeitas de acontecimentos observáveis** e permite acompanhar sua revisão. O primeiro caso de uso é perceber uma pessoa possivelmente no chão e oferecer ao operador uma oportunidade de verificar a situação.

Quem desenvolve e demonstra agora: Felipe, sozinho. Usuário da bancada: o próprio desenvolvedor ou adulto voluntário informado. Usuário operacional futuro: familiar, cuidador ou equipe responsável. Comprador futuro a validar: operador de cuidado, serviço de assistência ou família com necessidade específica. Não há cliente, contrato ou eficácia presumidos.

O diferencial que vamos investigar é a combinação de instalação compreensível em equipamentos compatíveis, processamento local, aviso explicável, indicação de cobertura e fluxo auditável. Estes recursos têm concorrentes; não estamos alegando invenção inédita ou superioridade antes de medir.

## Três modos claramente separados

| Modo | Origem | O que comprova |
| --- | --- | --- |
| `SIMULATED` | CLI publica evento artificial | Backend, painel e revisão |
| `REPLAY` | Worker analisa arquivo autorizado | Pipeline de visão e regras naquele vídeo |
| `LIVE` | Webcam; RTSP quando validado | Funcionamento ao vivo naquela configuração |

Todos pertencem a um **MVP de demonstração**. Mesmo `LIVE` não significa serviço de emergência em produção. O modo acompanha evento, tela de detalhe, lista, aviso e relatório. Testes e dados reais não são agregados na mesma métrica sem distinção.

## Jornadas obrigatórias

### J1 — Preparar

Proprietário faz login, usa um local de demonstração, cadastra uma câmera lógica e cria credencial de worker. Configura a fonte no computador local. Realiza calibração do piso e registra versão. Credenciais de câmera não são cadastradas no painel.

### J2 — Observar

Worker abre a fonte, verifica se consegue obter frames, estima poses e informa qualidade. Uma janela local opcional permite ajustar enquadramento. A prévia de vídeo fica no computador; o painel não recebe streaming contínuo.

### J3 — Detectar e rever

Uma postura compatível persiste durante a janela definida. O worker salva um candidato na outbox antes de enviá-lo. A API cria um incidente `OPEN`. O painel mostra o horário original, atraso, fonte e sinais. O operador reconhece, registra avaliação e encerra ou descarta. O retorno à postura em pé não encerra automaticamente o incidente humano.

### J4 — Ver falhas

Ao interromper a fonte ou o worker, o painel sinaliza falha/ausência de heartbeat. Se a API parar, o worker preserva eventos. Quando ela voltar, os dados reaparecem sem duplicação. O operador consegue distinguir um evento atrasado de um atual.

### J5 — Demonstrar e medir

Executar cenário positivo de postura no chão, atividades confundidoras e perda de fonte. Mostrar o histórico e as limitações. Exportar resultados agregados de avaliação, sem incluir imagens pessoais por padrão.

## Requisitos e rastreabilidade

| ID | Requisito | Etapa principal | Evidência de conclusão |
| --- | --- | --- | --- |
| R01 | Uma pessoa/área/fonte ativa | 04–06 | Configuração e relatório de cenário |
| R02 | Login e autorização | 01 | Sessão, logout e testes de acesso |
| R03 | Fonte e credencial separadas | 01/06 | Token revogável e segredo local |
| R04 | Evento e incidente distintos | 02 | Contrato e transação de ingestão |
| R05 | Idempotência e auditoria | 02 | Reenvio sem duplicar e histórico de ações |
| R06 | Painel completo com simulação | 03 | Fluxo demonstrável em navegador |
| R07 | Poses reais em arquivo | 04 | Replay e benchmark no computador real |
| R08 | Regras temporais por episódio | 05 | Fixtures temporais e vídeos avaliados |
| R09 | Webcam e qualidade da fonte | 06 | Teste físico e estados no painel |
| R10 | Persistência offline | 06 | Reinício e reenvio comprovados |
| R11 | Evidência mínima e retenção | 07 | Acesso autenticado e expiração |
| R12 | Relatório e demo repetível | 08 | Instalação reproduzida e matriz de aceite |
| R13 | RTSP/câmera IP | 09 opcional | Teste real ou incompatibilidade documentada |

## Qualidade exigida e limites

- Resposta do painel via polling a cada 2 segundos, com indicação quando a API está indisponível. Não pressupor entrega de atualização em tempo real garantida.
- Um episódio produz um incidente, mesmo com reenvio de rede. Esta garantia pode ser testada de forma determinística.
- Desempenho de visão é medido em CPU no notebook real. Resolução inicial de processamento: largura máxima de 640 pixels, proporção preservada, alvo inicial de 5 análises/s. São parâmetros de engenharia a avaliar, não especificações comerciais.
- Não há meta inventada de “99% de acurácia”. O relatório distingue acertos, perdas, falsos alertas, tempo não observável e casos inconclusivos.
- O MVP precisa de pelo menos um cenário controlado que realmente percorra câmera/vídeo → pose → motor → API → painel. Um botão “criar alerta” não satisfaz esse requisito.

## Não objetivos

Não reconhecer nominalmente pessoas, estimar caráter/intenção, atribuir probabilidade clínica, fazer diagnóstico, medir sinais vitais, monitorar banheiro, contar com pessoas vulneráveis como cobaias ou substituir observação profissional. Não há disparo automático a emergência, polícia ou contatos reais nesta versão.

Também não entram streaming remoto de todas as câmeras, aplicativo nativo, assinatura/cobrança, onboarding de vários clientes, detecção geral de violência e treinamento com vídeo de terceiros. O banco pode preparar isolamento por tenant sem construir um SaaS completo.

## História de demonstração

“Conecto uma fonte compatível, delimito a área, vejo se o sistema está observando, recebo uma suspeita explicável e registro o desfecho. Também consigo ver quando ele não consegue observar.”

Uma boa apresentação inclui uma falha conhecida e um falso positivo analisado. A confiança virá da clareza sobre o comportamento e da evolução medida.
