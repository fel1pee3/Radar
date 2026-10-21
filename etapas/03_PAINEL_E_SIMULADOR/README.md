# Etapa 03 — Painel e primeira demonstração

[Plano das etapas](../README.md) · [README central](../../README.md) · [Status](../../docs/STATUS.md)

**Estado inicial:** não iniciada. O estado atualizado deve estar em `docs/STATUS.md`.

## Objetivo

Primeira demo navegável: criar evento simulado, vê-lo no painel, reconhecer, revisar e encerrar.

## Dependências

Etapa 02 concluída; endpoints reais funcionando.

## Leitura obrigatória

Além de `AGENTS.md`, README central e status:

- [01_PRODUTO_E_ESCOPO.md](../../docs/01_PRODUTO_E_ESCOPO.md)
- [03_CONTRATOS_E_DADOS.md](../../docs/03_CONTRATOS_E_DADOS.md)
- [06_SEGURANCA_E_DADOS.md](../../docs/06_SEGURANCA_E_DADOS.md)
- [07_VALIDACAO_E_DEMO.md](../../docs/07_VALIDACAO_E_DEMO.md)
- [08_AMBIENTE_E_COMANDOS.md](../../docs/08_AMBIENTE_E_COMANDOS.md)

## Áreas de trabalho

apps/web, scripts/demo, tests/e2e e ajustes pontuais de contrato necessários, mantendo API como fonte de verdade.

Os caminhos de aplicação são entregas a criar/adaptar, não arquivos já presentes neste pacote. Ajustes em etapas anteriores são permitidos quando necessários para integrar corretamente, com motivo no relatório.

## Atividades

1. Construir login e navegação responsiva em português com sessão real. Configurar proxy /api para API local, cookies e Origin consistentes.
2. Construir visão geral de saúde, lista de incidentes e detalhe com sinais, versão, modo, atraso, revisão e histórico. Tratar carregamento, vazio, erro, reconexão e sessão expirada.
3. Implementar ações conforme estado e tratamento de 409. Mostrar quem registrou, horário e resultado. Não apresentar entrega simulada como SMS/WhatsApp enviado.
4. Criar configuração mínima de local/câmera e emissão de token com aviso de exibição única. URI privada e senha de câmera não entram nesse formulário.
5. Desenhar pose corporal quando presente; mostrar ausência de evidência sem inventar imagem. Snapshot ainda indisponível até 07.
6. Implementar polling de 2 s com interrupção apropriada quando a aba estiver inativa e retomada ao voltar. Avisos e status não podem ficar verdes quando a API falha.
7. Criar pnpm demo:simulate que usa bearer e endpoints reais, gera IDs válidos, mode SIMULATED e sequência reproduzível. Não inserir incidentes diretamente no banco. Enviar heartbeat de simulador enquanto ativo e ENDED ao terminar.
8. Criar roteiro e Playwright para login, evento via API, lista/detalhe, ação e histórico. Manter banner de MVP e marcador de simulação em todo contexto relevante.

## Critérios de conclusão

- [ ] O fluxo completo usa banco/API reais; mocks só em testes explicitamente isolados.
- [ ] Recarregar a página preserva estado e histórico.
- [ ] Lista/detalhe identificam SIMULATED; interface não afirma câmera física conectada por causa do simulador.
- [ ] Falha da API e sessão expirada produzem estados claros, sem descartar trabalho silenciosamente.
- [ ] E2E cobre reconhecimento e desfecho com autorização; layout funciona em desktop e largura móvel.
- [ ] `docs/STATUS.md` e `docs/RELATORIOS/ETAPA_03.md` refletem a situação real.

## Limites desta etapa

Não ligar modelo de visão, câmera ao vivo, serviço de mensagem ou aplicativo nativo. A demo desta etapa comprova fluxo, não IA.

## Entrega para o fundador

Demonstrar o objetivo desta etapa e fornecer comandos reais de reprodução. Separar verificado, parcialmente verificado e não executado. Usar o modelo em [relatórios](../../docs/RELATORIOS/README.md). Não concluir a etapa apenas porque arquivos foram criados ou o build passou.

## Prompt para o ChatGPT do VS Code

Copie o bloco inteiro com a pasta do projeto aberta. O prompt manda a IA ler este README e seus critérios, portanto não é necessário colar toda a documentação na conversa.

```text
Você está no repositório Radar de Acontecimentos. Implemente somente a ETAPA 03: Painel e primeira demonstração.

Antes de editar, leia:
- AGENTS.md
- README.md
- docs/STATUS.md
- etapas/03_PAINEL_E_SIMULADOR/README.md
- docs/01_PRODUTO_E_ESCOPO.md
- docs/03_CONTRATOS_E_DADOS.md
- docs/06_SEGURANCA_E_DADOS.md
- docs/07_VALIDACAO_E_DEMO.md
- docs/08_AMBIENTE_E_COMANDOS.md

Faça um inventário do código existente e preserve alterações do fundador. Confirme as dependências desta etapa pelo código e pelos relatórios, sem presumir que já foram implementadas.

Foco desta entrega:
Entregue uma demonstração apresentável do fluxo de incidentes com dados explicitamente simulados e integração real. Capriche em clareza operacional: fonte, atraso, evidência ausente, estado e histórico. Evite números decorativos de eficácia.

Execute as atividades e os critérios de conclusão descritos no README desta etapa. Não pare só no plano: produza a implementação e execute as verificações pertinentes disponíveis. Resolva decisões rotineiras com a documentação. Se faltar uma ação física, credencial ou dado indispensável, prepare o restante e peça apenas a informação concreta que bloqueia a validação.

Use a stack e os contratos fixados. Não adicione funcionalidades de etapas posteriores, contas pagas, envio externo, deploy, publicação ou compras. Não invente testes, compatibilidade, medições ou resultados. Diferencie simulação, replay e câmera ao vivo.

Ao concluir, atualize docs/STATUS.md e crie/atualize docs/RELATORIOS/ETAPA_03.md. Relate arquivos alterados, comandos realmente executados, resultados, decisões, pendências e como reproduzir. Se houver requisito não verificado, marque parcial em vez de concluir. Não avance automaticamente para a próxima etapa.
```
