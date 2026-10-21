# Etapa 01 — Domínio, banco e acesso

[Plano das etapas](../README.md) · [README central](../../README.md) · [Status](../../docs/STATUS.md)

**Estado inicial:** não iniciada. O estado atualizado deve estar em `docs/STATUS.md`.

## Objetivo

API autenticada com tenant de demonstração, proprietário, local, câmera lógica e credencial revogável do worker.

## Dependências

Etapa 00 concluída; PostgreSQL local disponível.

## Leitura obrigatória

Além de `AGENTS.md`, README central e status:

- [02_ARQUITETURA_E_STACK.md](../../docs/02_ARQUITETURA_E_STACK.md)
- [03_CONTRATOS_E_DADOS.md](../../docs/03_CONTRATOS_E_DADOS.md)
- [06_SEGURANCA_E_DADOS.md](../../docs/06_SEGURANCA_E_DADOS.md)
- [08_AMBIENTE_E_COMANDOS.md](../../docs/08_AMBIENTE_E_COMANDOS.md)

## Áreas de trabalho

apps/api, migrações Prisma, scripts de bootstrap, testes de integração e configuração privada de exemplo.

Os caminhos de aplicação são entregas a criar/adaptar, não arquivos já presentes neste pacote. Ajustes em etapas anteriores são permitidos quando necessários para integrar corretamente, com motivo no relatório.

## Atividades

1. Integrar Prisma ORM 7 ao PostgreSQL com gerador, adapter, configuração e ambiente próprios da versão escolhida. Testar runtime/build ESM, não apenas geração de arquivos.
2. Criar entidades Tenant, User, Session, Site, Camera, Device estável e DeviceCredential com relações consistentes de tenant. Rotacionar token não troca Device. Criar migrações versionadas; não usar db push como estratégia permanente.
3. Criar seed idempotente para o tenant/local e bootstrap do OWNER via variáveis privadas. Não incluir senha padrão no código, não sobrescrever senha existente e não apagar dados ao repetir.
4. Implementar login/logout/me, hash Argon2id, sessão opaca, cookie, expiração, verificação de Origin e limitação de tentativas. Sem cadastro público ou e-mail.
5. Implementar endpoints mínimos de locais/câmeras e emissão/rotação/revogação de token de device. Exibir segredo só na emissão; não permitir leitura posterior do token.
6. Implementar gates OWNER/OPERATOR, scoping de tenant e health/ready consultando realmente o banco. Separar bearer do worker de sessão de usuário.
7. Criar testes de integração com dois tenants artificiais e banco de teste isolado. Gerar OpenAPI inicial e documentar como criar operador por comando local, sem painel de equipe.

## Critérios de conclusão

- [ ] Migração em banco vazio e seed repetido não duplicam nem apagam dados.
- [ ] Login, logout, expiração, credencial inválida e mutação com origem externa têm resultados corretos.
- [ ] OPERATOR não cadastra câmera nem emite token; tenant A não acessa recursos de B.
- [ ] Token anterior revogado deixa de funcionar e nenhum log expõe segredo.
- [ ] Readiness retorna indisponível quando o PostgreSQL para.
- [ ] `docs/STATUS.md` e `docs/RELATORIOS/ETAPA_01.md` refletem a situação real.

## Limites desta etapa

Não construir onboarding SaaS, billing, convite por e-mail, autenticação social ou UI completa. Incidentes ficam para 02.

## Entrega para o fundador

Demonstrar o objetivo desta etapa e fornecer comandos reais de reprodução. Separar verificado, parcialmente verificado e não executado. Usar o modelo em [relatórios](../../docs/RELATORIOS/README.md). Não concluir a etapa apenas porque arquivos foram criados ou o build passou.

## Prompt para o ChatGPT do VS Code

Copie o bloco inteiro com a pasta do projeto aberta. O prompt manda a IA ler este README e seus critérios, portanto não é necessário colar toda a documentação na conversa.

```text
Você está no repositório Radar de Acontecimentos. Implemente somente a ETAPA 01: Domínio, banco e acesso.

Antes de editar, leia:
- AGENTS.md
- README.md
- docs/STATUS.md
- etapas/01_DOMINIO_E_ACESSO/README.md
- docs/02_ARQUITETURA_E_STACK.md
- docs/03_CONTRATOS_E_DADOS.md
- docs/06_SEGURANCA_E_DADOS.md
- docs/08_AMBIENTE_E_COMANDOS.md

Faça um inventário do código existente e preserve alterações do fundador. Confirme as dependências desta etapa pelo código e pelos relatórios, sem presumir que já foram implementadas.

Foco desta entrega:
Implemente identidade, domínio mínimo e provisionamento seguro do worker. Priorize migrações reais, seed idempotente, autorização e testes entre tenants. Preserve a exceção HTTP somente em loopback; não use JWT em localStorage.

Execute as atividades e os critérios de conclusão descritos no README desta etapa. Não pare só no plano: produza a implementação e execute as verificações pertinentes disponíveis. Resolva decisões rotineiras com a documentação. Se faltar uma ação física, credencial ou dado indispensável, prepare o restante e peça apenas a informação concreta que bloqueia a validação.

Use a stack e os contratos fixados. Não adicione funcionalidades de etapas posteriores, contas pagas, envio externo, deploy, publicação ou compras. Não invente testes, compatibilidade, medições ou resultados. Diferencie simulação, replay e câmera ao vivo.

Ao concluir, atualize docs/STATUS.md e crie/atualize docs/RELATORIOS/ETAPA_01.md. Relate arquivos alterados, comandos realmente executados, resultados, decisões, pendências e como reproduzir. Se houver requisito não verificado, marque parcial em vez de concluir. Não avance automaticamente para a próxima etapa.
```
