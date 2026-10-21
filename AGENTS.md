# Instruções para a IA de implementação

## Missão e ordem de leitura

Construir o MVP de bancada descrito neste repositório, uma etapa por solicitação do fundador. O pacote inicial é documentação; não alegue que módulos já existem.

Antes de editar, leia `README.md`, `docs/STATUS.md`, o README da etapa solicitada e as referências que ele indicar. Preserve alterações existentes e faça um inventário do repositório. As instruções atuais do fundador têm precedência; registre mudanças relevantes nos documentos.

## Autoridade das definições

1. Instrução atual do fundador.
2. `docs/09_DECISOES_E_FUTURO.md`: decisões e alterações de escopo.
3. `docs/03_CONTRATOS_E_DADOS.md`: contrato de dados, estados e endpoints.
4. `docs/04_MOTOR_DE_EVENTOS.md`: comportamento do detector.
5. Outros documentos de arquitetura, segurança, validação e README da etapa.

Se uma divergência for pequena, resolva-a de forma consistente e registre. Se mudar o uso pretendido, a arquitetura principal, o envio externo de dados ou exigir gasto, explique a decisão concreta ao fundador. Não reabra decisões já tomadas sem evidência de problema.

## Regras de execução

- Implemente somente a etapa pedida e ajustes necessários nas dependências anteriores. Não avance automaticamente para a seguinte.
- Produza código executável, migrações reais e instruções verificadas. Não substitua backend por mock permanente.
- Marque dados simulados, replay e câmera ao vivo de forma visível. Uma demo simulada nunca pode contar como teste de IA ou câmera.
- Não invente comandos executados, FPS, percentuais, testes, compatibilidade de equipamento ou resultados de licenças.
- Documente o ambiente real: SO, CPU, memória, versões, câmera testada e limitações. Pergunte somente o que não for observável e bloquear a tarefa.
- Use `pnpm` para TypeScript e `uv` para Python. Fixe dependências e preserve lockfiles. Confirme a compatibilidade antes de trocar uma família de versões.
- Não instale diferentes pacotes OpenCV que forneçam `cv2` no mesmo ambiente. Escolha a distribuição compatível com MediaPipe e com a prévia local.
- Mantenha nomes de código/contrato em inglês e documentação/interface em português brasileiro.
- Não adicione serviço pago, LLM por frame, treinamento automático, reconhecimento facial ou integração de mensagem externa.
- Não publique, faça deploy, envie dados ou mensagens a terceiros, compre hardware, crie conta ou faça commit/push sem instrução correspondente.
- Acesso de webcam pode exigir ação do sistema operacional. Não altere permissões globais ou firewall silenciosamente.
- Nunca grave senhas, URL RTSP com credenciais, vídeo pessoal, dumps ou pesos de modelos no Git.
- Nenhuma queda física deve ser provocada para satisfazer teste. Use fixtures sintéticas, vídeos autorizados e movimentos controlados seguros.
- Logs estruturados e erros compreensíveis; nunca mascarar falha de captura como “nenhuma ocorrência”.
- Teste riscos reais: contratos entre linguagens, duplicação, perda de conexão, transições, isolamento e regressão temporal. Não busque cobertura artificial por testes que repetem a implementação.
- Não remova um requisito ou reduza um teste só para declarar a etapa concluída.

## Conclusão de cada etapa

Atualize `docs/STATUS.md` e escreva `docs/RELATORIOS/ETAPA_XX.md` com objetivo, arquivos alterados, decisões, comandos realmente executados, resultados, pendências e instrução para reproduzir. Use o modelo em `docs/RELATORIOS/README.md`.

Se parte depender de hardware ou credencial indisponível, marque **parcial** ou **bloqueada**, detalhe o teste restante e preserve o trabalho útil. Um teste automatizado de adaptador não comprova câmera física.

Ao responder, explique o que passou, o que falhou e o que o fundador deve verificar. Não declare sucesso integral por haver código compilando. Não continue uma etapa posterior sem solicitação.
