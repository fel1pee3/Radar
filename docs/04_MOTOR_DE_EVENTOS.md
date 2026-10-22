# Motor temporal e baseline de visão

[Voltar ao README central](../README.md)

## O que a IA faz

MediaPipe estima pontos do corpo. Um módulo de regras temporais usa esses pontos para gerar uma suspeita. Não há treinamento de detector de quedas nem interpretação de intenção. O motor precisa ser uma função testável sobre observações, desacoplada de OpenCV, HTTP e banco.

Modelo inicial: Pose Landmarker **Lite**, MediaPipe Tasks. Pedir até duas poses para poder sinalizar múltiplas pessoas detectadas, mantendo a classificação restrita a uma pose válida. Desativar máscara de segmentação. Testar o custo real no notebook.

Resultado da investigação da etapa 05 (D34): o **Full float16/v1** foi comparado
e passou a ser uma opção explícita para a bancada. Lite permanece como padrão
das configurações anteriores. Ambos exigem bundle oficial com SHA-256 fixado,
duas poses e os mesmos gates; não há troca automática nem redução de qualidade.
O Full viabilizou o fluxo positivo em um arquivo, mas não resolveu todos os
enquadramentos. Veja [investigação 05](RELATORIOS/INVESTIGACAO_ETAPA_05.md).

Usar inicialmente `VIDEO`/`detect_for_video` com timestamps estritamente crescentes tanto para arquivo quanto para a sequência amostrada de webcam. É uma escolha síncrona para facilitar reprodutibilidade; não exige arquivo físico. Captura ao vivo e análise são desacopladas por buffer de um frame. `LIVE_STREAM` assíncrono só entra por decisão posterior motivada.

## Observação interna

Cada observação inclui `runId`, número do frame, timestamp monotônico/mídia, largura/altura, lista de poses, visibilidade de pontos, qualidade do frame, versão da calibração e duração da inferência. Não enviar observações contínuas à API.

Pontos essenciais: ombros e quadris para eixo do tronco; joelhos e tornozelos para extensão do corpo. É necessário haver evidência suficiente dos pontos usados. Não transformar landmarks ausentes em zeros. O `visibility` do modelo é usado como gate técnico e não como chance de emergência.

## Calibração inicial

O operador marca um polígono da região do piso em coordenadas normalizadas sobre um frame local, excluindo cama, sofá e regiões ocultas. O arquivo local inclui resolução/relação de aspecto, orientação e identificação da configuração. Não armazenar o frame de calibração por padrão.

Se a câmera mudar fisicamente, rotacionar, usar PTZ ou alterar proporção, recalibrar. O software detecta mudança de resolução/proporção quando possível; não prometer detectar qualquer deslocamento físico. Desligar auto-tracking/PTZ durante o teste da câmera IP.

## Sinais da baseline v0.1

Todos os valores abaixo são **pontos de partida experimentais para a bancada**, sujeitos a revisão no conjunto de calibração. Não são limiares clínicos, nem foram validados neste documento.

| Parâmetro | Inicial | Uso |
| --- | --- | --- |
| `targetAnalysisFps` | 5 | Taxa pretendida; medir taxa efetiva |
| `minLandmarkVisibility` | 0,5 | Exigir pontos essenciais visíveis |
| `minTorsoAngleDeg` | 60° em relação à vertical | Tronco aproximadamente horizontal |
| `maxBboxAspectRatio` | 1,0 (altura/largura) | Corpo com extensão predominantemente horizontal |
| `floorHoldMs` | 2.000 | Persistência mínima da postura candidata |
| `minValidPoseFraction` | 0,8 na janela | Qualidade temporal suficiente |
| `maxObservationGapMs` | 500 | Lacuna maior invalida continuidade da suspeita |
| `rapidDescentWindowMs` | 1.000 | Janela anterior à postura no chão |
| `minHipDescentNormalized` | 0,18 da altura da imagem | Deslocamento descendente de quadril para rótulo possível queda |
| `rearmHoldMs` | 3.000 | Tempo fora da postura candidata, com observação válida |

Corrigir proporção antes de calcular ângulo e bbox: `x * largura` e `y * altura`. Ângulo em coordenadas normalizadas sem considerar resolução distorce a medida. Bbox usa somente pontos corporais válidos; bbox degenerada ou corpo cortado invalida a observação.

Postura candidata exige simultaneamente: exatamente uma pose suficiente, centro dos quadris dentro do polígono de piso, tronco com ângulo mínimo e proporção corporal compatível. Usar janela temporal com cobertura ponderada por tempo, não número fixo de frames; exigir pelo menos 5 observações válidas na janela inicial. Uma observação válida com postura contrária zera a suspeita. Observações inválidas não contam como postura positiva e só toleram lacunas de até 500 ms. A janela precisa alcançar 2 s com pelo menos 80% de tempo coberto por observações válidas candidatas. Pontos esparsos não podem completar a janela apenas pela passagem do relógio.

Uma descida rápida exige quadris válidos antes e depois, mesma continuidade da pose, fonte sem mudança de configuração e deslocamento descendente no intervalo. Ela só muda o rótulo para `POSSIBLE_FALL` **depois** de satisfazer a persistência no chão. Sem trajetória suficiente, usar `PERSON_ON_FLOOR`.

Essa regra pode confundir alongamento, deitar voluntariamente ou perspectiva. O polígono não mede altura real em 3D. Registrar esse limite e os confundidores; não ocultá-los com linguagem de certeza.

O ângulo e a proporção são relativos aos eixos da imagem. Pessoa deitada na
direção da profundidade pode projetar tronco vertical e caixa alta, falhando na
regra mesmo com quadril dentro do piso e pontos suficientes; isso foi observado
em `piso-d`. Para floor-v0.1, o enquadramento precisa permitir a projeção corporal
predominantemente horizontal prevista nos gates. Não se declara suporte a toda
vista superior/diagonal. Uma homografia do piso ou world landmarks centrados no
quadril não fornecem automaticamente gravidade/altura física para resolver isso.
Não girar a imagem ou deslocar ROI apenas para forçar alerta. Uma política que
amplie esse domínio exigirá versão própria, calibração e avaliação separadas.

## Máquina local por câmera

| Estado | Entrada | Saída/comportamento |
| --- | --- | --- |
| `OBSERVING` | Captura e configuração válidas | Ao iniciar postura candidata, ir a `SUSPECTED` |
| `SUSPECTED` | Janela candidata em andamento | Se critérios completarem, persistir episódio/evento e ir a `ACTIVE`; se perder continuidade, voltar a observar |
| `ACTIVE` | Evento já criado | Nenhum novo evento para a mesma situação; manter episódio mesmo se envio falhar |
| `REARMING` | Postura deixa de ser candidata de forma observável | Após 3 s válidos, fechar episódio local e voltar a observar; se postura voltar antes, retornar a `ACTIVE` |

Qualidade insuficiente congela o episódio `ACTIVE`, mas não conta tempo para rearmar. Em `SUSPECTED`, lacuna acima de 500 ms zera a suspeita. Sair do enquadramento não comprova recuperação e não encerra o incidente. A v0.1 pode exigir reset manual explícito do episódio local após saída prolongada; registrar reset com motivo e nova execução. Não repetir alerta continuamente porque a pessoa permaneceu no chão.

Persistir `episodeId`, `eventId`, estado ativo e evento na mesma transação SQLite. Em reinício, restaurar episódio ativo para evitar duplicação da mesma cena; não reutilizar relógio monotônico da execução anterior. Reiniciar a janela de rearmamento. Trocar a fonte/calibração exige parar a execução e iniciar uma nova configuração, com histórico do reset.

O fechamento do episódio local habilita detectar uma nova situação. O fechamento do incidente na API é uma ação humana independente. Não bloquear nova situação só porque o incidente anterior continua aberto.

## Captura e qualidade

- Arquivo: ler timestamps da mídia; verificar monotonicidade. Se necessário, usar índice/FPS validado, registrando o fallback. Não usar velocidade do CPU como tempo da cena.
- Webcam: relógio monotônico do host; capturar o frame mais recente. Não repetir a última imagem como se fosse nova após erro de leitura.
- Terminar arquivo gera `ENDED`, não “câmera offline inesperada”. Pausa solicitada gera `PAUSED`.
- FPS abaixo do necessário, baixa iluminação e repetição suspeita são flags. “Imagem possivelmente congelada” é uma heurística: cena parada ou pessoa imóvel também pode produzir frames semelhantes.
- O teste determinístico de congelamento injeta frames/timestamps repetidos. No equipamento real, medir falsos avisos dessa heurística. Não afirmar detecção universal de obstrução.
- Duas poses, corpo cortado, baixa visibilidade ou ausência de ROI impedem classificar aquela janela. Registrar motivo de indisponibilidade da observação, sem inventar resultado negativo.

Defaults técnicos de qualidade, também experimentais: FRAME_TIMEOUT após 2 s sem frame novo; LOW_FPS abaixo de 2 análises/s por 5 s; LOW_LIGHT com luminância média abaixo de 25/255 por 2 s; POSSIBLE_FROZEN após 10 s de frames decodificados byte a byte idênticos. Essas condições tornam novas janelas inelegíveis. Registrar períodos de aquecimento/fim de arquivo separadamente e não aplicar limiar de FPS de relógio civil ao replay acelerado. Permitir ajustar os limiares com versão registrada; medir falsos avisos em cena estática e iluminação real.

## Avaliação e evolução

Separar captura, estimativa de pose, extração de features, regras, persistência e transporte. A primeira avaliação pode mostrar que MediaPipe não basta nas condições pretendidas. Nesse caso, manter o fluxo e comparar outro modelo via interface, com licença e regressão documentadas.

Feedback de operador não atualiza parâmetros automaticamente. Revisar, criar nova versão de política e reexecutar cenários separados da calibração. Não ajustar no conjunto final e reapresentá-lo como teste independente. IDs de modelo/política/calibração devem permitir reproduzir cada resultado.
