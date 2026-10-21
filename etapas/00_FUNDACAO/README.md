# Etapa 00 — Fundação do repositório e ambiente

[Plano das etapas](../README.md) · [README central](../../README.md) · [Status](../../docs/STATUS.md)

**Estado inicial:** não iniciada. O estado atualizado deve estar em `docs/STATUS.md`.

## Objetivo

Monorepo mínimo que inicia web/API, sobe PostgreSQL e prepara o ambiente Python com versões registradas.

## Dependências

Documentação deste pacote; nenhum parceiro ou equipamento adicional.

## Leitura obrigatória

Além de `AGENTS.md`, README central e status:

- [02_ARQUITETURA_E_STACK.md](../../docs/02_ARQUITETURA_E_STACK.md)
- [08_AMBIENTE_E_COMANDOS.md](../../docs/08_AMBIENTE_E_COMANDOS.md)
- [10_FONTES_E_LICENCAS.md](../../docs/10_FONTES_E_LICENCAS.md)

## Áreas de trabalho

Raiz do workspace, apps/web, apps/api, services/edge, packages/contracts, infra, scripts e documentação de ambiente.

Os caminhos de aplicação são entregas a criar/adaptar, não arquivos já presentes neste pacote. Ajustes em etapas anteriores são permitidos quando necessários para integrar corretamente, com motivo no relatório.

## Atividades

1. Inventariar arquivos existentes, SO, arquitetura, Node, pnpm, Python, uv e Docker. Preservar trabalho prévio. Registrar recursos do notebook que forem observáveis; perguntar apenas se um dado bloquear a instalação.
2. Criar workspace pnpm para web/API/contracts e projeto Python separado com uv. Fixar as famílias previstas, resolver patches estáveis e salvar locks. Configurar TypeScript strict, ESLint/formatter e Ruff.
3. Criar Next.js com tela simples de estrutura do projeto e NestJS com GET /v1/health/live. A readiness de banco entra na próxima etapa; não simular conexão que ainda não existe.
4. Criar Compose de PostgreSQL 17 com credenciais privadas, healthcheck, volume e porta somente loopback. Criar scripts infra:up/infra:down sem apagar volume.
5. Configurar dev:api, dev:web, lint, typecheck e build. Preparar configuração da API ESM e documentar limites do workspace. Não gerar um framework genérico de serviços.
6. Criar o pacote Python radar_edge, comando mínimo de diagnóstico de versão e ambiente. Instalar a combinação compatível de MediaPipe/OpenCV e verificar import no SO real, sem baixar modelo nem alegar inferência.
7. Criar exemplos de ambiente sem segredos e .gitignore para .local, vídeos, modelos, dumps, .env, node_modules e ambientes virtuais. Criar relatório de dependências/versões inicial.

## Critérios de conclusão

- [ ] Instalação JS e Python reproduzível a partir dos locks criados.
- [ ] Web abre; /v1/health/live responde; PostgreSQL fica saudável.
- [ ] Build, lint e typecheck passam nos pacotes criados; import de MediaPipe e cv2 funciona ou há bloqueio real documentado.
- [ ] Nenhuma senha padrão pública, mídia pessoal ou artefato de modelo foi adicionado ao repositório.
- [ ] `docs/STATUS.md` e `docs/RELATORIOS/ETAPA_00.md` refletem a situação real.

## Limites desta etapa

Não implementar login, banco de domínio, detector, pipeline de eventos ou uma interface completa. Não iniciar a etapa 01.

## Entrega para o fundador

Demonstrar o objetivo desta etapa e fornecer comandos reais de reprodução. Separar verificado, parcialmente verificado e não executado. Usar o modelo em [relatórios](../../docs/RELATORIOS/README.md). Não concluir a etapa apenas porque arquivos foram criados ou o build passou.

## Prompt para o ChatGPT do VS Code

Copie o bloco inteiro com a pasta do projeto aberta. O prompt manda a IA ler este README e seus critérios, portanto não é necessário colar toda a documentação na conversa.

```text
Você está no repositório Radar de Acontecimentos. Implemente somente a ETAPA 00: Fundação do repositório e ambiente.

Antes de editar, leia:
- AGENTS.md
- README.md
- docs/STATUS.md
- etapas/00_FUNDACAO/README.md
- docs/02_ARQUITETURA_E_STACK.md
- docs/08_AMBIENTE_E_COMANDOS.md
- docs/10_FONTES_E_LICENCAS.md

Faça um inventário do código existente e preserve alterações do fundador. Confirme as dependências desta etapa pelo código e pelos relatórios, sem presumir que já foram implementadas.

Foco desta entrega:
Prepare o monorepo, o ambiente local e os comandos mínimos. Valide cedo a instalação real de MediaPipe/OpenCV no SO, mas não implemente o detector. Registre versões fixadas e restrições; nada de serviços pagos ou deploy.

Execute as atividades e os critérios de conclusão descritos no README desta etapa. Não pare só no plano: produza a implementação e execute as verificações pertinentes disponíveis. Resolva decisões rotineiras com a documentação. Se faltar uma ação física, credencial ou dado indispensável, prepare o restante e peça apenas a informação concreta que bloqueia a validação.

Use a stack e os contratos fixados. Não adicione funcionalidades de etapas posteriores, contas pagas, envio externo, deploy, publicação ou compras. Não invente testes, compatibilidade, medições ou resultados. Diferencie simulação, replay e câmera ao vivo.

Ao concluir, atualize docs/STATUS.md e crie/atualize docs/RELATORIOS/ETAPA_00.md. Relate arquivos alterados, comandos realmente executados, resultados, decisões, pendências e como reproduzir. Se houver requisito não verificado, marque parcial em vez de concluir. Não avance automaticamente para a próxima etapa.
```
