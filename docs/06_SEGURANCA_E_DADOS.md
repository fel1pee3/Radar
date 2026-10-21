# Segurança, privacidade e retenção

[Voltar ao README central](../README.md)

Aplicar estas medidas proporcionalmente à bancada. Não é necessário constituir empresa ou conseguir parceiro para desenvolver com dados sintéticos e material próprio autorizado. Antes de uso assistencial com terceiros, avaliar finalidade, responsabilidades e exigências aplicáveis; este pacote não certifica conformidade regulatória.

## Identidades e permissões

| Identidade | Pode | Não pode |
| --- | --- | --- |
| `OWNER` | Configurar local/câmera, emitir/revogar token, revisar incidentes e excluir snapshots | Acessar outro tenant |
| `OPERATOR` | Ver incidentes/evidências autorizadas e registrar ações | Emitir token, alterar câmera ou excluir evidência |
| Device | Enviar eventos, heartbeat e snapshot da câmera vinculada | Fazer login humano, ler incidentes ou enviar para outra câmera |

Sem cadastro público, convite ou recuperação de senha por e-mail nesta versão. Bootstrap local cria um proprietário a partir de segredo informado pelo fundador. Seed não contém senha padrão pública e não reseta senha em toda execução. Uma conta de operador pode ser criada via comando local explícito; não construir gestão completa de equipe.

Senha com Argon2id. Sessão opaca aleatória, guardada com hash no PostgreSQL, expiração inicial de 8 h e revogação no logout. Cookie HttpOnly, SameSite=Lax e Path=/; Secure obrigatório fora da exceção de desenvolvimento restrita a loopback HTTP. Não guardar token humano em localStorage.

Para mutações com cookie, verificar `Origin` exato da interface; rejeitar origem externa ou ausente. API e proxy devem preservar essa informação. Testar tentativa CSRF. Rotas de device usam bearer e não dependem de cookie. CORS não é mecanismo de autenticação.

Token do worker é aleatório, individual, mostrado uma vez e armazenado em hash na API. Rotação revoga o anterior explicitamente. Guardar no computador em arquivo ignorado pelo Git, com permissões locais adequadas. Não usar token humano como segredo de dispositivo.

## Isolamento e exposição

Toda consulta a incidente, câmera, evento, imagem e auditoria é filtrada pelo tenant validado. Testes com dois tenants verificam leitura, alteração, referência cruzada e evidência. A existência de `tenantId` na tabela não prova isolamento.

No MVP, UI/API/PostgreSQL escutam loopback. Não abrir portas de roteador, túneis públicos ou câmera à internet. Operação em outra máquina/LAN não é automaticamente equivalente: exige TLS, controle de acesso e configuração específica. Não desabilitar verificação de certificado para “resolver” conexão.

Nunca confiar em caminhos de arquivo recebidos do navegador. O servidor não abre URI RTSP informada pelo painel; o worker local lê sua própria configuração. Isso reduz a superfície de SSRF. Login recebe limitação de tentativas, tamanho de corpo e mensagens que não revelam existência de usuário.

## Minimização

- Áudio desativado e não processado.
- Sem reconhecimento facial, nomes das pessoas observadas ou perfil individual de comportamento.
- Sem gravação contínua da webcam.
- Pose de evidência somente em evento; omitir landmarks faciais. Pose, horário e contexto ainda podem ser dados identificáveis; não chamar de anonimização garantida.
- Modelo e inferência rodam localmente. Pacotes/modelo são baixados no preparo; depois, a demonstração básica não precisa de internet.
- Vídeos de avaliação ficam privados no computador e fora do Git. Ter autorização para ver um vídeo não autoriza automaticamente publicação ou treinamento futuro.

## Evidência JPEG opcional

Default `EVIDENCE_MODE=skeleton`; alternativas `none` e `snapshot`. `none` envia somente sinais/metadados; `skeleton` inclui pontos corporais; `snapshot` também pode anexar uma imagem do evento.

Habilitar snapshot exige configuração local e confirmação do proprietário de que a captura está autorizada. A preferência fica registrada sem dados pessoais desnecessários. Nenhuma chamada de IA pode ativar o modo por conta própria apenas para melhorar a apresentação.

Upload após evento aceito, no máximo um JPEG de até 2 MiB por incidente, referenciado pelo eventId, maior lado até 1280 px. Validar bytes reais, decodificar, limitar pixels e reencodar sem EXIF. Não aceitar SVG, caminho arbitrário ou tipo declarado sem validação. Usar nome opaco e diretório privado fora da árvore pública web. Mesmo hash repetido é idempotente; tentativa de substituir conteúdo retorna conflito. Uma segunda chave de evento deduplicada no mesmo episódio não autoriza outra imagem.

O backend serve a imagem por endpoint autenticado, `Cache-Control: no-store`, sem URL pública permanente. Auditar acesso/exclusão. Falha, ausência ou expiração de imagem não impede revisão do incidente nem é tratada como ausência de ocorrência.

## Política inicial de retenção de bancada

| Dado | Prazo inicial | Comportamento |
| --- | --- | --- |
| Frames de processamento | Apenas memória | Descartados após processamento; buffer limitado |
| Snapshot na API | 24 h após recebimento | Apagar arquivo; preservar marcador de expiração |
| Snapshot pendente no worker | Até 24 h após criação | Expirar imagem sem apagar evento de metadados |
| Pose de evidência | 7 dias após recebimento | Remover lista de pontos, manter sinais mínimos |
| Metadados de incidentes e auditoria | 30 dias | Purga explícita configurada de demo, respeitando vínculos |
| Chaves/hash de recibos de deduplicação | 90 dias | Sem pose/imagem/payload; reenvio após purga não recria incidente |
| Outbox já confirmada | 7 dias | Limpar itens enviados; pendentes não expiram silenciosamente |
| Logs técnicos | 7 dias e limite de tamanho | Rotacionar e eliminar segredos/payloads |
| Vídeos fonte da avaliação | Definido no manifesto local | Não copiar automaticamente para relatórios ou backup |

São defaults de desenvolvimento, não justificativa legal universal. O programa deve indicar expiração/purga e aplicar limpeza idempotente, inclusive após reinício. A purga de 30 dias exige habilitação explícita do proprietário; se desabilitada, informar a retenção efetiva sem fingir que os dados foram apagados. Redação do payload preserva somente o hash original necessário à deduplicação. Retenção de backups também precisa considerar dados visuais; para a demo, backup padrão exclui imagens e vídeos, permanece privado e expira em 7 dias. Não restaurar automaticamente mídia já expirada.

## Auditoria e logs

Auditoria registra login relevante, criação/revogação de credencial, ação de incidente, alteração de configuração e acesso/exclusão de snapshot. Não armazenar senha/token/URL privada/corpo de imagem ou copiar todo payload nos logs.

Logs técnicos usam IDs correlacionáveis e códigos de erro. Não imprimir header Authorization, DSN de banco com senha ou string RTSP completa, inclusive em traceback de biblioteca. Injetar segredos fictícios nos testes e verificar que foram redigidos.

## Antes de sair da bancada

Reavaliar uso pretendido e alegações do produto, base de tratamento dos dados, responsabilidades de atendimento, aceite dos participantes, requisitos da LGPD e eventual enquadramento sanitário. Uso real precisa de responsável e processo de resposta. Não tratar “MVP” ou “bem-estar” como dispensa automática. Isso é um gate do piloto com terceiros; não altera a decisão de construir a demonstração agora.
