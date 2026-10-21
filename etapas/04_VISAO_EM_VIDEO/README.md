# Etapa 04 — Visão computacional em arquivo

[Plano das etapas](../README.md) · [README central](../../README.md) · [Status](../../docs/STATUS.md)

**Estado inicial:** não iniciada. O estado atualizado deve estar em `docs/STATUS.md`.

## Objetivo

O worker lê vídeo, respeita o tempo da mídia, estima poses e permite calibrar uma região de piso, sem emitir suspeitas ainda.

## Dependências

Etapa 03 concluída; Python compatível e ao menos um vídeo autorizado disponível para teste real.

## Leitura obrigatória

Além de `AGENTS.md`, README central e status:

- [02_ARQUITETURA_E_STACK.md](../../docs/02_ARQUITETURA_E_STACK.md)
- [04_MOTOR_DE_EVENTOS.md](../../docs/04_MOTOR_DE_EVENTOS.md)
- [05_CAMERAS_E_CALIBRACAO.md](../../docs/05_CAMERAS_E_CALIBRACAO.md)
- [07_VALIDACAO_E_DEMO.md](../../docs/07_VALIDACAO_E_DEMO.md)
- [08_AMBIENTE_E_COMANDOS.md](../../docs/08_AMBIENTE_E_COMANDOS.md)
- [10_FONTES_E_LICENCAS.md](../../docs/10_FONTES_E_LICENCAS.md)

## Áreas de trabalho

services/edge, documentação de modelo/ambiente e configurações de exemplo sem mídia pessoal.

Os caminhos de aplicação são entregas a criar/adaptar, não arquivos já presentes neste pacote. Ajustes em etapas anteriores são permitidos quando necessários para integrar corretamente, com motivo no relatório.

## Atividades

1. Criar interfaces de FrameSource, PoseEstimator e Observation. Implementar FILE primeiro, normalizando rotação/proporção e fim normal de arquivo.
2. Obter bundle oficial MediaPipe Pose Landmarker Lite com origem/termos registrados, calcular hash e mantê-lo em .local/models. Não commitar pesos. Registrar versões de dependências e artefatos.
3. Implementar MediaPipe Tasks em modo VIDEO com timestamps crescentes e num_poses=2, sem máscara. Respeitar largura máxima inicial de 640 px e proporção.
4. Criar CLI doctor/run/calibrate conforme o documento de comandos. Calibração produz arquivo versionado com ROI normalizada e orientação, sem salvar frame por padrão.
5. Criar prévia local opcional com pose/ROI e teclas de encerramento. Se não houver GUI acessível, permitir configuração manual validada e pedir apenas a ação física necessária ao fundador.
6. Medir FPS de análise, tempo de inferência e memória disponíveis. Saída detalhada de observações deve ser opt-in e privada; não mandar frames/poses contínuos à API.
7. Validar timestamps, orientação, múltiplas poses detectadas, corpo parcial e fim do arquivo. Capturar mensagens de erro compreensíveis, sem inventar inferência caso modelo/arquivo falhe.

## Critérios de conclusão

- [ ] Um arquivo autorizado foi processado de verdade com poses, ou o relatório marca explicitamente a validação real pendente.
- [ ] Replays em velocidades diferentes conservam timestamps e sequências de observação coerentes.
- [ ] ROI inválida ou orientação incompatível impede processamento classificador posterior.
- [ ] Não há incidente criado nesta etapa, upload contínuo ou pesos/vídeos adicionados ao Git.
- [ ] Relatório identifica máquina, modelo/hash, biblioteca e medidas realmente obtidas.
- [ ] `docs/STATUS.md` e `docs/RELATORIOS/ETAPA_04.md` refletem a situação real.

## Limites desta etapa

Não declarar que MediaPipe detecta queda. Não implementar motor temporal, treinamento, webcam ou otimização GPU nesta etapa.

## Entrega para o fundador

Demonstrar o objetivo desta etapa e fornecer comandos reais de reprodução. Separar verificado, parcialmente verificado e não executado. Usar o modelo em [relatórios](../../docs/RELATORIOS/README.md). Não concluir a etapa apenas porque arquivos foram criados ou o build passou.

## Prompt para o ChatGPT do VS Code

Copie o bloco inteiro com a pasta do projeto aberta. O prompt manda a IA ler este README e seus critérios, portanto não é necessário colar toda a documentação na conversa.

```text
Você está no repositório Radar de Acontecimentos. Implemente somente a ETAPA 04: Visão computacional em arquivo.

Antes de editar, leia:
- AGENTS.md
- README.md
- docs/STATUS.md
- etapas/04_VISAO_EM_VIDEO/README.md
- docs/02_ARQUITETURA_E_STACK.md
- docs/04_MOTOR_DE_EVENTOS.md
- docs/05_CAMERAS_E_CALIBRACAO.md
- docs/07_VALIDACAO_E_DEMO.md
- docs/08_AMBIENTE_E_COMANDOS.md
- docs/10_FONTES_E_LICENCAS.md

Faça um inventário do código existente e preserve alterações do fundador. Confirme as dependências desta etapa pelo código e pelos relatórios, sem presumir que já foram implementadas.

Foco desta entrega:
Implemente a base real de visão em arquivo, com calibração e tempo de mídia correto. O resultado desta etapa são observações e medidas, não decisões de queda. Se faltar vídeo autorizado, prepare o caminho e deixe o teste marcado como pendente; não substitua por um resultado fictício.

Execute as atividades e os critérios de conclusão descritos no README desta etapa. Não pare só no plano: produza a implementação e execute as verificações pertinentes disponíveis. Resolva decisões rotineiras com a documentação. Se faltar uma ação física, credencial ou dado indispensável, prepare o restante e peça apenas a informação concreta que bloqueia a validação.

Use a stack e os contratos fixados. Não adicione funcionalidades de etapas posteriores, contas pagas, envio externo, deploy, publicação ou compras. Não invente testes, compatibilidade, medições ou resultados. Diferencie simulação, replay e câmera ao vivo.

Ao concluir, atualize docs/STATUS.md e crie/atualize docs/RELATORIOS/ETAPA_04.md. Relate arquivos alterados, comandos realmente executados, resultados, decisões, pendências e como reproduzir. Se houver requisito não verificado, marque parcial em vez de concluir. Não avance automaticamente para a próxima etapa.
```
