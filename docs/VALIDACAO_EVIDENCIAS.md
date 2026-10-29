# Evidências do verificador de entrega

O checker é um leitor de comprovantes locais, não uma certificação independente.
Ele confere identidade e integridade dos arquivos e aplica critérios aos resultados
extraídos dos logs. Um operador não deve escrever resultados desejados: cada
medida precisa ter origem identificada em uma execução/anotação real. Hash não
comprova honestidade da anotação e não substitui revisão humana.

## Identidade e integridade

`pnpm.cmd demo:check --evidence <indice.json> --engineering-evidence <engenharia.json>`
lê o índice indicado. Sem argumentos, usa `.local/release-evidence.json` e o
comprovante legado `.local/etapa08/engineering.json`. Não sobrescreve arquivos.

O índice tem `subjectFiles`: caminhos de `configuration`, `model`,
`classifier`, `policy` e `protocol`. O checker calcula seus SHA-256 atuais
e o fingerprint do código por `sourceIdentity()` (código, contratos, testes,
manifests e locks; documentação não entra). Arquivo ausente impede aprovação.

`evidence` referencia por caminho e SHA-256 os comprovantes de:
`regression`, `transitions`, `independent`, `physical`, `offline` e
`recovery`. Cada comprovante tem:

- `schemaVersion: 1`, `kind`, `subject` com os seis hashes atuais;
- `artifacts: [{ path, sha256 }]` dos registros originais;
- `measurements` extraídas desses registros, com denominadores e anotações
  mantidos nos artefatos. Não usar previsões como referência humana.

Os campos aceitos e seus limites estão em
`scripts/validation/release-evidence.mjs`; seus testes exemplificam rejeição de
prova ausente, versão alterada, arquivo adulterado e revisão automatizada.
Não copiar os exemplos sintéticos dos testes para um comprovante real.

O protocolo congelado deve enumerar todas as configurações da matriz, hashes,
papel dos dados e limitações das anotações. A configuração física e a matriz
não compartilham resultados por coincidência de nome: o comprovante precisa
explicar os vínculos e as diferenças de fonte/identidade.

## Engenharia

O comprovante contém `checks`, uma entrada por comando exigido. Resultados
legados só valem para o fingerprint integral original. A forma nova pode incluir
`inputs: [{path, sha256}]`, `log: {path, sha256}`, `exitCode`,
`command` e `reusedFrom`. O escopo dos inputs precisa cobrir dependências
e código realmente exercitados; não basta escolher um arquivo que não mudou.

Provas antigas não são apagadas. Se não houver vínculo verificável do componente
atual, ficam DESATUALIZADAS. Não se repete instalação limpa/backup para cada
ajuste perceptual; o relatório pode comprovar testes pertinentes e ainda manter
o gate abrangente de engenharia pendente/desatualizado. Isso não autoriza chamar
a release inteira de aprovada.

## Gates funcionais

- Regressão: todos os 36 casos, incluindo as quatro perdas históricas, concluídos
  e aprovados pelos critérios registrados. Inconclusivo não passa.
- Transições: pelo menos quatro transições anotadas, rótulos sustentados,
  confundidores revisados, sem rótulos indevidos. Não basta terminar no chão.
- Independente: reserva congelada, separação por hash, gravação e participante,
  pelo menos quatro alvos e oito controles, sem perdas, duplicações ou controles
  inconclusivos; prazo e cobertura vigentes.
- Físico: LIVE nominal de 600 s, encerramento automático, cobertura nos horizontes
  previsto e executado, perfil completo, episódio/rearme e revisão humana
  efetivamente salva. Sem início humano anotado, a latência não é aprovada.
- Offline: confirmação humana de internet desconectada, replay entregue e painel
  conferido antes da reconexão.
- Recuperação: indisponibilidade da API e reinício exercitados, pendentes entregues,
  reenvio idempotente, um incidente/aviso e fila zerada.

A apresentação formal é DISPENSADA por D50. O teste original de 30 minutos que
não foi completado permanece no histórico; os 600 s não apagam essa falha.

## Resultados

APROVADO = prova compatível atende aos critérios; REPROVADO = falha medida,
comprovante inválido ou integridade quebrada; PENDENTE = prova ainda ausente;
DESATUALIZADO = versão/configuração diferente; DISPENSADO = requisito dispensado
explicitamente, não executado.

`engineeringReady` e `functionalReady` são separados.
`releaseReady` exige ambos, nunca é fixado em true.
Exit 0 aprova o escopo solicitado; exit 1 indica falha; exit 2 indica pendência
ou prova desatualizada. Em `--engineering`, exit 0 não aprova percepção.
