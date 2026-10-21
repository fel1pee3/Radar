# Etapa 08 — Validação final e entrega da demo

[Plano das etapas](../README.md) · [README central](../../README.md) · [Status](../../docs/STATUS.md)

**Estado inicial:** não iniciada. O estado atualizado deve estar em `docs/STATUS.md`.

## Objetivo

MVP de bancada v0.1 reproduzível, com roteiro de apresentação, resultados medidos e limites explícitos.

## Dependências

Etapas 00–07 concluídas; etapa 09 não é requisito.

## Leitura obrigatória

Além de `AGENTS.md`, README central e status:

- [01_PRODUTO_E_ESCOPO.md](../../docs/01_PRODUTO_E_ESCOPO.md)
- [03_CONTRATOS_E_DADOS.md](../../docs/03_CONTRATOS_E_DADOS.md)
- [05_CAMERAS_E_CALIBRACAO.md](../../docs/05_CAMERAS_E_CALIBRACAO.md)
- [06_SEGURANCA_E_DADOS.md](../../docs/06_SEGURANCA_E_DADOS.md)
- [07_VALIDACAO_E_DEMO.md](../../docs/07_VALIDACAO_E_DEMO.md)
- [08_AMBIENTE_E_COMANDOS.md](../../docs/08_AMBIENTE_E_COMANDOS.md)
- [09_DECISOES_E_FUTURO.md](../../docs/09_DECISOES_E_FUTURO.md)
- [10_FONTES_E_LICENCAS.md](../../docs/10_FONTES_E_LICENCAS.md)

## Áreas de trabalho

testes/avaliação, scripts de execução/verificação, correções de defeitos e documentação final; sem novas funcionalidades.

Os caminhos de aplicação são entregas a criar/adaptar, não arquivos já presentes neste pacote. Ajustes em etapas anteriores são permitidos quando necessários para integrar corretamente, com motivo no relatório.

## Atividades

1. Executar matriz de aceite e corrigir falhas concretas de contrato, segurança, perda/duplicação ou estado. Não trocar gates por mocks para obter verde.
2. Organizar vídeos/manifestos autorizados e separar calibração/avaliação por sessão. Documentar quantidade real disponível e quais condições não foram avaliadas.
3. Executar benchmark, replay anotado e teste físico ao vivo de pelo menos 30 min. Registrar falsos alertas, perdas, qualidade, CPU/RAM e FPS reais.
4. Reproduzir preparação em ambiente limpo separado quando possível: instalar pelos locks, iniciar banco, migrar, seed, API/web e worker. Não resetar o banco original para fazer esse teste.
5. Criar procedimento de backup/restore local com processos parados para consistência. Testar restauração em banco separado; excluir vídeo/snapshot do backup padrão e definir retenção do backup. Reaplicar expiração de pose/evidência após restore antes de liberar acesso.
6. Criar pnpm demo:check, roteiro de 5–7 min e troubleshooting com comandos efetivamente testados. Verificar execução sem internet após preparo.
7. Concluir docs/RELATORIOS/VALIDACAO_MVP.md e inventário de dependências/modelos. Atualizar README para distinguir o implementado do planejado e STATUS com evidência.
8. Preparar release local v0.1 sem publicar, fazer push, contatar parceiros ou vender automaticamente. Definir backlog após demo e pendências para futuro piloto.

## Critérios de conclusão

- [ ] Todos os gates da seção “Critérios da release local v0.1” estão atendidos ou a entrega fica explicitamente parcial.
- [ ] O fluxo via visão foi testado em arquivo e fonte ao vivo; simulador não é usado como evidência de percepção.
- [ ] Relatório tem denominadores, cenários, tempo não observável, falhas e limitações, sem números inventados.
- [ ] Execução limpa, recuperação e restore foram verificados com escopo real relatado.
- [ ] Fundador consegue apresentar a demo seguindo roteiro e sabe parar/retomar os processos.
- [ ] Nenhum requisito de parceiro, câmera IP específica ou serviço pago foi adicionado ao gate da bancada.
- [ ] `docs/STATUS.md` e `docs/RELATORIOS/ETAPA_08.md` refletem a situação real.

## Limites desta etapa

Não anunciar eficácia clínica, publicar site ou converter demo em monitoramento de terceiros. Não ampliar escopo para compensar resultados fracos.

## Entrega para o fundador

Demonstrar o objetivo desta etapa e fornecer comandos reais de reprodução. Separar verificado, parcialmente verificado e não executado. Usar o modelo em [relatórios](../../docs/RELATORIOS/README.md). Não concluir a etapa apenas porque arquivos foram criados ou o build passou.

## Prompt para o ChatGPT do VS Code

Copie o bloco inteiro com a pasta do projeto aberta. O prompt manda a IA ler este README e seus critérios, portanto não é necessário colar toda a documentação na conversa.

```text
Você está no repositório Radar de Acontecimentos. Implemente somente a ETAPA 08: Validação final e entrega da demo.

Antes de editar, leia:
- AGENTS.md
- README.md
- docs/STATUS.md
- etapas/08_VALIDACAO_E_ENTREGA/README.md
- docs/01_PRODUTO_E_ESCOPO.md
- docs/03_CONTRATOS_E_DADOS.md
- docs/05_CAMERAS_E_CALIBRACAO.md
- docs/06_SEGURANCA_E_DADOS.md
- docs/07_VALIDACAO_E_DEMO.md
- docs/08_AMBIENTE_E_COMANDOS.md
- docs/09_DECISOES_E_FUTURO.md
- docs/10_FONTES_E_LICENCAS.md

Faça um inventário do código existente e preserve alterações do fundador. Confirme as dependências desta etapa pelo código e pelos relatórios, sem presumir que já foram implementadas.

Foco desta entrega:
Finalize a v0.1 com evidência, não com novas funcionalidades. Reproduza, meça e documente a demonstração real. Se a baseline falhar no cenário mínimo ou houver risco técnico crítico, registre parcial e corrija; não esconda o resultado. A entrega é local e experimental.

Execute as atividades e os critérios de conclusão descritos no README desta etapa. Não pare só no plano: produza a implementação e execute as verificações pertinentes disponíveis. Resolva decisões rotineiras com a documentação. Se faltar uma ação física, credencial ou dado indispensável, prepare o restante e peça apenas a informação concreta que bloqueia a validação.

Use a stack e os contratos fixados. Não adicione funcionalidades de etapas posteriores, contas pagas, envio externo, deploy, publicação ou compras. Não invente testes, compatibilidade, medições ou resultados. Diferencie simulação, replay e câmera ao vivo.

Ao concluir, atualize docs/STATUS.md e crie/atualize docs/RELATORIOS/ETAPA_08.md. Relate arquivos alterados, comandos realmente executados, resultados, decisões, pendências e como reproduzir. Se houver requisito não verificado, marque parcial em vez de concluir. Não avance automaticamente para a próxima etapa.
```
