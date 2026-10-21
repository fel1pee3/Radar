# Câmeras, celular e calibração

[Voltar ao README central](../README.md)

## Ordem de integração

| Fonte disponível | Uso no plano | Situação atual |
| --- | --- | --- |
| Vídeo gravado pelo celular | Primeiro material autorizado de replay | A gravar/selecionar pelo fundador |
| Webcam do notebook | Primeira entrada ao vivo obrigatória | Hardware informado; acesso ainda não testado |
| Celular ao vivo | Extensão futura, se fornecer protocolo compatível | Não necessário para v0.1 |
| Smart IP KAP-S069 | RTSP opcional após verificação no aparelho | Protocolo, firmware, app e credenciais não confirmados |

O projeto deve ser concluível com o notebook. Não comprar câmera, instalar app pago ou obter parceiro para desbloquear as etapas centrais.

## Vídeos do celular

Gravar com autorização, câmera estável, iluminação comum e piso visível. Transferir o arquivo localmente para `.local/videos/`. Não enviar para nuvem de IA. Respeitar orientação e metadados de rotação; o worker normaliza orientação antes da ROI e da inferência.

Usar movimentos cotidianos e pessoas já posicionadas no chão, sem quedas provocadas. Cenas de impacto real não são requisito. Cada arquivo deve ter um pequeno manifesto de autorização, cenário, pessoa pseudonimizada, sessão e intervalos anotados. O vídeo fica fora do Git; o manifesto público não contém nome civil.

## Webcam do notebook

1. Executar o worker Python no SO que acessa fisicamente a webcam.
2. Conferir permissão de câmera para aplicativo desktop e fechar aplicativos que ocupem o dispositivo.
3. Usar CLI de diagnóstico para abrir o índice explicitamente escolhido, mostrando FPS/resolução e uma prévia local opcional.
4. Posicionar o notebook com estabilidade e piso no campo de visão. Uma webcam frontal sobre a mesa pode não enxergar o chão; ajustar o ambiente sem comprar equipamento antes de testar.
5. Marcar ROI, registrar calibração e iniciar observação com uma pessoa.
6. Testar interrupção da captura e restauração. Se o SO exigir consentimento, o fundador executa essa ação.

Não presumir que a webcam está sempre no índice 0. O diagnóstico pode testar uma lista pequena explicitamente configurada de índices locais; não fazer varredura de rede. Se o hardware não estiver acessível à IA do VS Code, preparar o comando e marcar o teste físico como pendente.

## KAP-S069: o que sabemos e o que não sabemos

O fundador informou o modelo **KAP-S069**. Na pesquisa de 21/10/2026, não foi encontrada confirmação técnica suficiente, em documentação oficial acessível, de que sua unidade fornece RTSP/ONVIF. A página pública da marca não resolveu essa questão. Anúncios de varejo e nome “Smart IP” não comprovam firmware ou protocolo da unidade.

Não registrar como compatível até testar. Não inventar URL RTSP, porta, senha padrão ou app obrigatório. Modelos e revisões semelhantes podem variar.

### Checklist de compatibilidade, para a etapa opcional

1. O fundador consulta etiqueta/manual/app e registra marca exata, modelo, firmware, app e eventual opção de RTSP/ONVIF/acesso local. Não colocar senha ou foto com QR de acesso nos relatórios.
2. Identifica o IP local pelo app/roteador sob seu controle. Usa somente a câmera de sua propriedade e credenciais configuradas por ele.
3. Se houver RTSP documentado, testa a URI exata em cliente local confiável, sem expô-la em histórico de shell, screenshot ou log.
4. Se houver ONVIF confirmado, uma ferramenta local pode obter o perfil/URI com autenticação. A descoberta ONVIF automática não precisa ser implementada no MVP.
5. Verifica codec, resolução, FPS, latência e estabilidade. Testa primeiro H.264 se disponível; não prometer suporte a H.265 sem decoder compatível e benchmark.
6. Desliga PTZ/auto-tracking durante a calibração, mantém câmera fixa, faz teste de 30 minutos e reconexão controlada.
7. Registra resultado como `COMPATIBLE_TESTED`, `PARTIAL`, `INCOMPATIBLE` ou `UNVERIFIED`, com condições e data.

Se o aparelho só funcionar via serviço P2P/app proprietário, sem acesso documentado ao stream, interromper essa integração e manter webcam/replay. Não contornar autenticação, fazer engenharia reversa do serviço ou abrir a câmera à internet para adaptar o protótipo.

## Configuração local da fonte

O worker recebe `source.kind = FILE | WEBCAM | RTSP`, caminho/índice/URI correspondente e `cameraId`. Fonte `FILE` sempre gera modo `REPLAY`; `WEBCAM/RTSP` geram `LIVE`. O simulador TypeScript é separado e usa `SIMULATED`.

Guardar URI e credenciais em `.local/edge.env` ou arquivo privado referenciado por configuração. Não passar URI com senha em argumento de processo. Logs exibem identificador da câmera e URI redigida. Não enviar URI ao backend.

Um arquivo de calibração contém ID/versão, dimensão, orientação, ROI e parâmetros. Se a imagem mudar de relação de aspecto, invalidar e pedir recalibração. Mudança apenas de escala com mesma proporção pode reutilizar ROI normalizada, desde que o enquadramento não tenha mudado.

## Critérios de aceitação da fonte

Decodifica sem travar o processo, entrega timestamps utilizáveis, sustenta o teste de bancada, falha de forma visível, reconecta dentro da política e respeita o enquadramento. Compatibilidade de vídeo não significa que o detector de posturas funcione bem naquele ângulo. São duas validações diferentes.

Software sem equipe de instalação é uma direção de produto. Nesta fase, o fundador faz configuração e mede o esforço. O futuro onboarding remoto só pode ser prometido depois de repetir essas condições em equipamentos e redes diferentes.
