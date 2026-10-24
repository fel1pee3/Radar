# Validação, métricas e roteiro de demonstração

[Voltar ao README central](../README.md)

## Três provas diferentes

1. **Engenharia:** o fluxo persiste, autoriza, deduplica, recupera falhas e registra ações.
2. **Percepção:** o modelo e as regras conseguem identificar as situações anotadas nas condições testadas.
3. **Valor assistencial/comercial:** alguém se beneficia, consegue responder e aceita o custo. Esta terceira prova fica para o piloto após a bancada.

Não misturar esses resultados. Gerar um incidente artificial não valida a visão. Um replay positivo não prova assistência em casa. Um usuário elogiar a demo não comprova compra.

## Conjunto inicial proposto

Meta de trabalho: 12 vídeos curtos autorizados, sendo 4 com pessoa posicionada no chão e 8 com atividades confundidoras, mais uma sessão nominal de 10 minutos de observação cotidiana para procurar avisos indevidos (D51, limite de 600 s do worker). A proposta original de 30 minutos não foi comprovada e foi revista expressamente pelo fundador. É uma amostra exploratória pequena, sem poder para estimar segurança clínica.

Separar sessões de calibração e avaliação. Se apenas o fundador participar, declarar que não houve avaliação em pessoas diferentes. Não exigir parceiro para reunir material inicial. Usar pessoas já deitadas, transições controladas e fixtures sintéticas para “trajetória rápida”; nunca provocar quedas físicas.

Confundidores: sentar, agachar, pegar objeto, ajoelhar, alongar, deitar voluntariamente, sair do quadro e oclusão parcial. Deitar no chão pode ser um acerto de postura e um falso alerta de necessidade de ajuda. Manter os dois rótulos no manifesto. Não etiquetar toda postura no chão como queda real.

Manifesto local: `videoId`, hash, autorização/retenção, `personPseudonym`, `sessionId`, `environmentId`, papel CALIBRATION/EVALUATION, FPS/duração, intervalos-alvo e confundidores. Usar identificadores, não nomes civis. Guardar mídia em `.local/`; versionar somente fixtures sintéticas e formatos.

## Matriz mínima de verificação

| Teste | Resultado esperado | Etapa |
| --- | --- | --- |
| Login, logout e expiração | Sessão correta e revogada | 01 |
| Acesso a outro tenant/câmera | Negado inclusive em imagem e ações | 01/02/07 |
| Contrato TS/Python | Mesmos exemplos aceitos/rejeitados | 02/05 |
| Reenviar evento 10 vezes | Um incidente, sem repetir aviso | 02 |
| Concorrência de reconhecimento | Uma versão vence; outra recebe conflito | 02 |
| Demonstração sem câmera | Fluxo completo identificado como simulado | 03 |
| Replay determinístico de fixtures | Mesmos episódios para mesma política | 05 |
| Variar FPS e velocidade do replay | Duração usa tempo de mídia, não velocidade do PC | 05 |
| Corpo parcial/múltiplas poses | Não gerar decisão confiante indevida | 05 |
| Mesmo episódio longo | Um candidato até rearmar | 05 |
| Parar API e reiniciar worker | Pendentes persistem e voltam sem duplicar | 06 |
| Evento atrasado ou relógio adiantado | Flag correta, sem aviso urgente novo | 06 |
| Desconectar fonte | Falha visível; não repetir último frame como novo | 06 |
| Fim de arquivo/pausa | Status apropriado, sem alarme técnico falso de desconexão | 06 |
| Snapshot opt-out/expirado | Sem captura não autorizada; acesso coerente | 07 |
| Instalação limpa e restore | Reproduzível, com segredos separados | 08 |

## Métricas e contagem

| Métrica | Definição |
| --- | --- |
| Recall exploratório | Episódios-alvo anotados detectados / episódios-alvo avaliados |
| Precisão exploratória | Alertas associados a um alvo / alertas avaliáveis |
| Falsos alertas por hora | Alertas sem alvo / horas de observação elegível, com tempo excluído reportado |
| Duplicações | Incidentes extras para o mesmo episódio anotado |
| Latência do detector | Tempo de mídia/monotônico do início anotado até emissão |
| Latência de transporte | Recebimento da API menos emissão, só para relógios coerentes |
| Latência do painel | Tempo entre persistência e exibição; considerar polling |
| Disponibilidade de captura | Tempo com frames utilizáveis / tempo esperado de execução |
| Elegibilidade da inferência | Tempo com condições da baseline satisfeitas / tempo analisado |
| Desempenho | FPS real, frames descartados, CPU, RAM, tamanho da outbox |

Denominador zero deve aparecer “não estimável”, nunca 100%. Inconclusivos e tempo sem visibilidade ficam separados, sem serem apagados do total observado. Comparar eventos e intervalos, não frames aleatórios. Associar no máximo um alerta a cada intervalo-alvo, usando janela/tolerância definida antes da avaliação e mostrando duplicações separadamente.

Para esta bancada, a correspondência temporal usa emissão dentro do intervalo-alvo anotado ou até 2 s após seu fim; intervalos devem durar o suficiente para a janela do motor. Registrar a regra no relatório e não alterá-la depois de ver os resultados. Resultados de “pessoa no chão” e “possível queda” são apresentados separadamente; sem quedas reais anotadas não existe recall de quedas reais.

Revisar também períodos sem alertas para localizar perdas. Não apresentar intervalos de confiança ou percentuais excessivamente precisos em amostra minúscula sem método apropriado. Guardar contagens absolutas e cenários.

## Critérios da release local v0.1

- Etapas 00–07 concluídas com evidência; testes determinísticos de acesso, idempotência, estados e recuperação passam.
- Pelo menos um arquivo autorizado e um teste físico de webcam percorrem visão → motor → incidente → revisão, sem injetar o evento por botão no percurso de visão.
- Um cenário de postura-alvo e um confundidor são demonstrados e seus resultados documentados. Se o confundidor dispara, mostrar isso e registrar a limitação; não alegar que o detector distingue necessidade de ajuda.
- Ensaio curto contínuo de bancada com limite de 600 s do worker (10 min nominais, D51), encerramento normal e sem perda silenciosa de eventos. Medir separadamente aquecimento, captura/inferência efetivas, recursos, avisos indevidos, períodos inelegíveis e interrupções. O timer inclui abertura/modelo; não equivale a 600 s de frames úteis. O teste original de 30 min não foi comprovado, e passar o ensaio curto não resolve a falha histórica aos 27min45s.
- Relatório completo de percepção, inclusive falhas, e ambiente reproduzível com dependências/modelo fixados.
- Demo roda sem internet depois de instalar dependências e obter o modelo. Documentar exceções verificadas.
- Problema crítico de acesso indevido, perda de evento ou classificação apoiada em frames antigos impede liberar a demo como pronta. Corrigir antes de concluir.

O gate libera **uma demonstração técnica experimental**. Não aprova piloto assistencial, desempenho em casas desconhecidas ou alegações de prevenção. Se a baseline não produzir sequer o fluxo real controlado, registrar parcial e corrigir a visão; não usar simulador para declarar a release pronta.

## Roteiro opcional de apresentação de 5–7 minutos

Atualização de 23/10/2026: por decisão do fundador (D50), a apresentação formal
cronometrada não é requisito de conclusão nem uma etapa de aprendizado.
O roteiro abaixo permanece opcional. Evidências operacionais durante o
desenvolvimento são preservadas; não registrar apresentação como executada.
Critérios técnicos e avaliação permanecem; a duração física atual segue D51
(10 min nominais), sem comprovação do teste original de 30 min.

1. Abrir painel, indicar “MVP de demonstração” e explicar o caso de uso em uma frase.
2. Mostrar câmera, calibração e estado de observação.
3. Reproduzir um vídeo autorizado de pessoa já no chão, com fonte marcada como replay; mostrar surgimento automático do incidente.
4. Mostrar sinais, pose, horário e versão; reconhecer e registrar desfecho de teste.
5. Mostrar a webcam ao vivo e uma atividade comum segura. Não fazer queda para impressionar.
6. Interromper a fonte de forma controlada e mostrar indicação de falha; restaurar.
7. Mostrar métricas, uma limitação conhecida e o que será avaliado no próximo piloto.

Para demonstrar recuperação da API, usar roteiro separado e curto, com pausa e reenvio de evento. Expor token, IP privado completo ou imagem de pessoa sem autorização não faz parte da apresentação.

## Relatório final

Criar `docs/RELATORIOS/VALIDACAO_MVP.md` com commit/versões, hardware, fontes, cenas, modelo/política/calibração, contagens, horas válidas/inválidas, falhas, latências e decisão. Dados fictícios usados em layout devem ser rotulados. Linkar evidência técnica privada local quando necessário, sem commitar mídia pessoal.
