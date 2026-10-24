# Roteiro opcional de apresentação local de 5–7 minutos

**Apresentação formal DISPENSADA pelo fundador em 23/10/2026 (D50).**
Este roteiro permanece como referência opcional para uso futuro, sem bloquear
a etapa 08 ou exigir aprendizado. Não registrar sua execução como realizada.
Etapa 08 encerrada no escopo revisado da demo experimental; conferir [matriz](RELATORIOS/VALIDACAO_MVP.md) e
[roteiro operacional](VALIDACAO_MANUAL_ETAPA_08.md). Nenhum envio externo.

Preparar antes: Docker, API/web em execução, usuário existente, Full/piso validados,
arquivo autorizado com entrega operacional pronta e uma sessão independente para
novo replay. Não recompilar durante a apresentação. Abrir painel e relatório de
resultados. Ocultar credenciais; não projetar terminal com segredos nem mídia de
terceiros sem autorização. O arquivo 07 é calibração conhecida, não teste independente.

| Tempo | Ação | O que explicar/verificar |
| --- | --- | --- |
| 0:00–0:40 | Abrir visão geral | “MVP experimental local que gera uma suspeita de pessoa no chão para revisão humana.” Sem garantia de assistência |
| 0:40–1:20 | Fontes e configuração | Câmera lógica, piso selecionado e saúde; cadastro não inicia captura e ONLINE não garante cobertura |
| 1:20–2:30 | Executar replay autorizado | run na configuração FILE preparada; aguardar incidente automático REPLAY/TEST. Mostrar offset, Full, política e piso |
| 2:30–3:30 | Abrir detalhe e registrar revisão | Explicar sinais e pose; reconhecer, revisar e encerrar com TEST_COMPLETED. Registrar pessoa no chão sem afirmar acidente |
| 3:30–4:40 | Webcam com atividade segura | Mostrar imagem local/pose e fonte LIVE no painel. O evento LIVE positivo deve ter sido validado antes; não improvisar queda |
| 4:40–5:40 | Pausar/retomar/encerrar | Control pause/resume/stop em comandos separados; conferir imagem nova e mudanças no painel |
| 5:40–6:40 | Resultados e limitação | Mostrar contagens/denominadores reais. Expor perda por perspectiva e pose falsa em estante; necessidade de ajuda não é inferida |

Comandos de replay, controles e encerramento estão no roteiro 08. Se houver erro,
mostrar estado e relatório: não substituir por simulador sem identificar a troca.
O simulador é útil para explicar o backend, mas não valida câmera/visão.

## Recuperação da API — ensaio separado

Manter esse ensaio fora dos sete minutos. A verificação reproduzível é
`pnpm.cmd test:api`, com banco/API/workers exclusivos, falha de rede e ACK perdido.
O teste preserva IDs, envelopes, pendentes e um incidente por episódio.

Se demonstrar fisicamente depois: encerrar somente a API própria, manter o worker,
observar pendência, reiniciar a API e conferir entrega única/horários originais.
Não parar o banco 5432, matar processos por nome ou apagar a fila. Esse ensaio
interrompe continuidade, portanto não integra os 30 minutos de observação contínua.

## Backlog após a demonstração — não implementado

1. **P0:** completar gates físicos/offline e coleta/anotação independente da 08.
2. **P1:** investigar falsos reconhecimentos na estante com negativos anotados e
   perdas por projeção; qualquer nova política exige calibração/versionamento e
   avaliação separada, preservando resultados da floor-v0.1.
3. **P1:** medir fluidez/custo da prévia e reduzir esforço da configuração por
   evidência de uso, sem esconder períodos de baixa qualidade.
4. **P2:** repetir em outro ambiente/equipamento e avaliar resposta humana/valor
   assistencial e comercial com escopo e responsabilidades próprios.
5. **Opcional:** etapa 09/câmera IP, somente por solicitação; não bloqueia bancada.

Sensores novos, configuração inteligente, comunicação com contatos, serviços pagos
e ampliação de eventos permanecem visão futura. Nenhuma dessas ideias foi usada
para compensar pendências da validação atual.
