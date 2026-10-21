# Etapa 09 — Câmera IP e verificação da KAP-S069

[Plano das etapas](../README.md) · [README central](../../README.md) · [Status](../../docs/STATUS.md)

**Estado inicial:** não iniciada. O estado atualizado deve estar em `docs/STATUS.md`.

## Objetivo

Adaptador RTSP testado e resultado honesto de compatibilidade da unidade KAP-S069, se houver acesso documentado.

## Dependências

Etapa 06 concluída; acesso local e documentação/credenciais da câmera fornecidos pelo proprietário. É opcional e não bloqueia 08.

## Leitura obrigatória

Além de `AGENTS.md`, README central e status:

- [02_ARQUITETURA_E_STACK.md](../../docs/02_ARQUITETURA_E_STACK.md)
- [03_CONTRATOS_E_DADOS.md](../../docs/03_CONTRATOS_E_DADOS.md)
- [05_CAMERAS_E_CALIBRACAO.md](../../docs/05_CAMERAS_E_CALIBRACAO.md)
- [06_SEGURANCA_E_DADOS.md](../../docs/06_SEGURANCA_E_DADOS.md)
- [07_VALIDACAO_E_DEMO.md](../../docs/07_VALIDACAO_E_DEMO.md)

## Áreas de trabalho

adaptador RTSP em services/edge, diagnóstico e relatório de compatibilidade; não alterar núcleo do detector para acomodar segredo/protocolo proprietário.

Os caminhos de aplicação são entregas a criar/adaptar, não arquivos já presentes neste pacote. Ajustes em etapas anteriores são permitidos quando necessários para integrar corretamente, com motivo no relatório.

## Atividades

1. Conferir manual/etiqueta/app/firmware e acesso local com o fundador. Consultar documentação oficial específica quando disponível. Não presumir ONVIF/RTSP por anúncio comercial.
2. Adicionar FrameSource RTSP com URI lida de arquivo privado, timeout e reconexão limitados, reaproveitando buffer, inferência, outbox e heartbeat já existentes.
3. Usar stream de teste local autorizado para validar o adaptador antes de atribuir compatibilidade ao aparelho. Não fazer varredura ampla de rede, tentar senhas padrão ou abrir portas do roteador.
4. Quando houver URI fornecida/documentada, testar decoder, codec, FPS e estabilidade da unidade. Manter PTZ/auto-tracking desligado durante ROI fixa.
5. Executar teste de 30 min e recuperação após interrupção permitida. Registrar latência observada, qualidade, firmware e limitações sem expor endereço com senha.
6. Classificar a unidade como COMPATIBLE_TESTED, PARTIAL, INCOMPATIBLE ou UNVERIFIED. Se apenas P2P proprietário sem stream acessível, encerrar a tentativa e manter a demo de webcam.

## Critérios de conclusão

- [ ] Adaptador validado com fonte autorizada e sem segredos nos logs.
- [ ] Compatibilidade da KAP-S069 só é declarada se a unidade foi realmente testada; vídeo genérico RTSP não conta.
- [ ] Falhas de rede não bloqueiam indefinidamente a captura ou criam crescimento ilimitado.
- [ ] Mudança de enquadramento exige recalibração; acesso a stream e qualidade de detecção são relatados separadamente.
- [ ] O MVP principal continua funcionando com webcam se a IP for incompatível.
- [ ] `docs/STATUS.md` e `docs/RELATORIOS/ETAPA_09.md` refletem a situação real.

## Limites desta etapa

Não implementar engenharia reversa P2P, descoberta universal ONVIF, firmware customizado, bypass de autenticação ou linha própria de câmeras.

## Entrega para o fundador

Demonstrar o objetivo desta etapa e fornecer comandos reais de reprodução. Separar verificado, parcialmente verificado e não executado. Usar o modelo em [relatórios](../../docs/RELATORIOS/README.md). Não concluir a etapa apenas porque arquivos foram criados ou o build passou.

## Prompt para o ChatGPT do VS Code

Copie o bloco inteiro com a pasta do projeto aberta. O prompt manda a IA ler este README e seus critérios, portanto não é necessário colar toda a documentação na conversa.

```text
Você está no repositório Radar de Acontecimentos. Implemente somente a ETAPA 09: Câmera IP e verificação da KAP-S069.

Antes de editar, leia:
- AGENTS.md
- README.md
- docs/STATUS.md
- etapas/09_CAMERA_IP_OPCIONAL/README.md
- docs/02_ARQUITETURA_E_STACK.md
- docs/03_CONTRATOS_E_DADOS.md
- docs/05_CAMERAS_E_CALIBRACAO.md
- docs/06_SEGURANCA_E_DADOS.md
- docs/07_VALIDACAO_E_DEMO.md

Faça um inventário do código existente e preserve alterações do fundador. Confirme as dependências desta etapa pelo código e pelos relatórios, sem presumir que já foram implementadas.

Foco desta entrega:
Faça a integração RTSP como extensão opcional. Separe capacidade do adaptador da compatibilidade comprovada da minha KAP-S069. Não invente URI, porta, senha ou suporte ONVIF. Se faltar acesso documentado, registre a limitação e preserve o caminho de webcam.

Execute as atividades e os critérios de conclusão descritos no README desta etapa. Não pare só no plano: produza a implementação e execute as verificações pertinentes disponíveis. Resolva decisões rotineiras com a documentação. Se faltar uma ação física, credencial ou dado indispensável, prepare o restante e peça apenas a informação concreta que bloqueia a validação.

Use a stack e os contratos fixados. Não adicione funcionalidades de etapas posteriores, contas pagas, envio externo, deploy, publicação ou compras. Não invente testes, compatibilidade, medições ou resultados. Diferencie simulação, replay e câmera ao vivo.

Ao concluir, atualize docs/STATUS.md e crie/atualize docs/RELATORIOS/ETAPA_09.md. Relate arquivos alterados, comandos realmente executados, resultados, decisões, pendências e como reproduzir. Se houver requisito não verificado, marque parcial em vez de concluir. Não avance automaticamente para a próxima etapa.
```
