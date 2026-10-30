# Runtime Python no Windows — diagnóstico e recuperação isolada

29/10/2026. O bloqueio identificado é **Smart App Control (SAC)**.
A execução foi recuperada em dois ambientes experimentais com uma distribuição
PSF assinada. Os ambientes Python 3.12 anteriores foram preservados; a recuperação
do runtime não aprova a candidata perceptual nem conclui o MVP.

## Causa comprovada

| Evidência local                                           | Resultado                                                           |
| --------------------------------------------------------- | ------------------------------------------------------------------- |
| Evento 3077, PolicyName                                   | VerifiedAndReputableDesktop                                         |
| PolicyGUID                                                | {0283ac0f-fff1-49ae-ada1-8a933130cad6}                              |
| PolicyID registrado                                       | 27555.1000.240208                                                   |
| Nível solicitado / validado no 3077                       | 2 / 1                                                               |
| Status                                                    | 0xC0E90002, saída do processo -1058471934                           |
| Evento 3089 com o mesmo ActivityID                        | TotalSignatureCount=0; ValidatedSigningLevel=0; VerificationError=0 |
| Registro VerifiedAndReputablePolicyState                  | 1                                                                   |
| Authenticode do python.exe e python312.dll usados pelo uv | NotSigned                                                           |
| CiTool -lp -json                                          | OperationResult=-2147024891, acesso negado ao inventário            |

A Microsoft identifica esse nome/GUID como política inbox do
[Smart App Control](https://learn.microsoft.com/en-us/windows/security/application-security/application-control/app-control-for-business/operations/inbox-appcontrol-policies).
Os eventos de bloqueio e assinatura foram relacionados pelo ActivityID, conforme
o [procedimento oficial de diagnóstico](https://learn.microsoft.com/en-us/windows/security/application-security/application-control/app-control-for-business/operations/appcontrol-debugging-and-troubleshooting).
Não há evidência de que uma empresa administre a máquina ou de quem ativou a política.

O valor VerificationError=0 com zero assinaturas não significa assinatura válida.
A ausência de assinatura também não demonstra corrupção. O SHA-256 plano
do python312.dll do evento corresponde ao arquivo atual:
90a28a195c89d19055ef57718325854c95dd6228f5706af2b263b2a6bd2fa395.
O campo SHA256 Hash do Code Integrity pode ter outra semântica; a comparação
de bytes usa SHA256 Flat Hash.

O caminho CPU aponta ao runtime uv cpython-3.12.15-windows-x86_64-none.
O home do ambiente DirectML usa o alias cpython-3.12-windows-x86_64-none,
resolvido para os mesmos bytes 3.12.15. Executável e DLL tinham assinatura ausente.
A auditoria também registra os executáveis dos venvs e seus pyvenv.cfg.

O SAC não oferece uma exceção individual suportada para um aplicativo bloqueado.
A [orientação oficial](https://support.microsoft.com/en-us/windows/security/threat-malware-protection/smart-app-control-frequently-asked-questions)
recomenda software assinado/confiável. Nenhuma proteção, política ou exclusão
foi alterada; arquivos não foram renomeados para escapar da verificação.

## Distribuição alternativa verificada

Foi escolhida a distribuição Windows x64 normal do Python Install Manager:
[Python 3.13.17](https://www.python.org/downloads/release/python-31317/),
publicada pela Python Software Foundation. Ela é distinta do pacote embeddable.

- Manifesto: [windows-3.13.17.json](https://www.python.org/ftp/python/3.13.17/windows-3.13.17.json).
- Pacote: [python-3.13.17-amd64.zip](https://www.python.org/ftp/python/3.13.17/python-3.13.17-amd64.zip).
- SHA-256 do ZIP: b26ca4b4ee51e157836049934d2b8eabd55939be296f3130254251b6df96ec2f.
- python.exe: 7c2fc2b303a4ee3cc14cc17b47bc6e8bca98c78792edd123b846a560da44b203.
- python313.dll: 26026530507a7389e7892ce130e7c1753b32a2df03ec3721d45ad8c1705d40eb.
- Exe e DLL: versão 3.13.17, Authenticode Valid, signatária Python Software Foundation.

A validação antecedeu a primeira execução. Não houve substituição isolada de DLL.
O runtime completo foi extraído numa pasta privada nova e executou com SAC ativo.
Não houve instalação global, alteração de PATH/registro ou substituição dos venvs antigos.

**Limitação de atualização:** [Python 3.13.18](https://www.python.org/downloads/release/python-31318/)
já existe como distribuição somente de código-fonte, com correções posteriores.
A 3.13.17 é a distribuição Windows assinada verificada nesta prova; não é a revisão
de segurança mais recente da série. Essa lacuna permanece registrada. O runtime
continua uma opção experimental explícita, não uma migração silenciosa.

## Compatibilidade e execução comprovada

Os projetos originais exigem Python >=3.12,<3.13. Permanecem intactos.
As cópias experimentais exigem >=3.13,<3.14 e fixam 3.13.17 em .python-version:

| Ambiente         | Projeto                        | Runtime ONNX permitido      |
| ---------------- | ------------------------------ | --------------------------- |
| CPU experimental | experiments/python313-cpu      | onnxruntime 1.23.2          |
| GPU experimental | experiments/python313-directml | onnxruntime-directml 1.23.0 |

Foram mantidos NumPy 2.5.4, OpenCV contrib 5.0.0.93, MediaPipe 1.1.1 no ambiente
CPU e os pins de contratos/transporte. Os metadados PyPI indicam wheels Windows
CPython 3.13, abi3 ou py3, conforme o pacote; essa indicação foi seguida de imports
nativos reais. Existe somente uma distribuição que fornece cv2 em cada ambiente
e somente uma distribuição ONNX Runtime em cada ambiente.

A recuperação comprovou Python e imports em ambos; operações NumPy/OpenCV
executaram, e o modelo RTMO foi inicializado no ambiente DirectML.
Dois FILE autorizados passaram pelo worker: intake16-03 gerou um evento e
chair08-02 não gerou alerta. A prova com profiling de operadores mostrou
computação DmlExecutionProvider, com auxiliares CPU. Isso é mais forte que
apenas enumerar providers disponíveis. Esses dois casos não substituem a
comparação completa, a avaliação independente ou um ensaio físico.

As provas privadas estão na rodada indicada por .local/runtime-recovery-current.json:
runtime-binaries.json, events-correlated.json, ci-registry.json,
runtime-selection.json, signed-runtime.json, wheel-compatibility-pypi.json,
imports-cpu.json, imports-directml.json e native-profiled-summary.json.
A prova FILE inicial sem profiling foi preservada; não foi usada sozinha para
afirmar computação na GPU.

## Auditoria reproduzível sem Python

Na raiz, em PowerShell:

```powershell
$auditoria = ".local/runtime-audit-$([guid]::NewGuid())"
powershell -NoProfile -File scripts/validation/audit-python-runtime.ps1 -Output $auditoria
```

O script não executa Python. Registra versões, SHA-256, Authenticode,
pyvenv.cfg, links/junctions, eventos 3033/3077 e os 3089 correlacionados.
Consulta o registro SAC e tenta CiTool somente em leitura. Ausência de eventos
não é teste de funcionamento do runtime.

Use -Since e -Until para consultar uma janela histórica. Comprovação desta rodada:

```powershell
powershell -NoProfile -File scripts/validation/audit-python-runtime.ps1 -Output .local/runtime-audit-NOVO -Since "2026-10-29T10:45:00" -Until "2026-10-29T12:00:00"
```

NOVO deve ser substituído por um destino ainda inexistente.
O inventário CiTool negado não impede a coleta das outras provas. Se for
indispensável listar todas as políticas, a ação administrativa exata é abrir
PowerShell **como administrador** e executar somente:

```powershell
CiTool.exe -lp -json
```

Esse comando apenas lista políticas. Não é necessário removê-las para usar
a alternativa assinada. A atribuição do bloqueio ao SAC já tem evidência
local e correspondência oficial; não depende de presumir gestão empresarial.

## Preparação reproduzível dos ambientes isolados

Para uma máquina sem os ambientes experimentais, o preparador usa destino novo,
confere manifesto e hash do ZIP, limita extração à pasta privada, verifica versão,
bytes e assinaturas PSF antes de executar e sincroniza os lockfiles:

```powershell
powershell -NoProfile -File scripts/validation/prepare-python313.ps1
```

Os downloads, runtime e comprovante ficam sob uma pasta nova de .local.
Os venvs experimentais são criados somente nos dois projetos Python 3.13.
O script chama uv local 0.13.4 com --frozen, --python explícito e
--no-python-downloads, sem solicitar um runtime managed não assinado.

Nesta máquina o runtime já existe. Para reutilizá-lo:

```powershell
$rodadaRuntime = (Get-Content .local/runtime-recovery-current.json -Raw | ConvertFrom-Json).root
$runtimeAssinado = (Get-Content "$rodadaRuntime/runtime-selection.json" -Raw | ConvertFrom-Json).root
powershell -NoProfile -File scripts/validation/prepare-python313.ps1 -ExistingRuntime $runtimeAssinado
```

Um venv já existente que aponte a outro runtime é preservado e causa erro explícito.
Use o runtime correspondente; o preparador não o substitui automaticamente.
-ExistingRuntime também confere hashes/versão/assinaturas do conjunto fixado.
-SkipSync permite validar somente o runtime já existente e sua execução.

O recibo preparation.json informa exatamente o que foi executado. Uma validação
com SkipSync não declara que a instalação completa foi repetida. Os comandos
de worker e o resultado funcional vigente ficam no relatório central da candidata.

## Verificações desta implementação

| Verificação executada                         | Resultado                                                                                       |
| --------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| Parser PowerShell dos dois scripts            | Dois arquivos sem erro de sintaxe                                                               |
| Auditoria readonly na janela 10:45–12:00      | 16 eventos, oito correlações, quatro ambientes; SAC confirmado                                  |
| CiTool capturado pelo auditor                 | OperationResult=-2147024891; AccessDenied registrado                                            |
| Preparador -ExistingRuntime -SkipSync         | Hashes/assinaturas/versão verificados; Python executou; saída 0                                 |
| Primeiro teste do preparador                  | Falhou por quoting PowerShell do argumento -c; corrigido, prova anterior preservada             |
| Destino já existente / caminho fora de .local | Ambos recusados com exit 1; recibo anterior manteve o mesmo SHA-256; nada criado fora de .local |
| Download/sync pelo preparador novo            | Não repetido; download verificado e sync já haviam sido executados na recuperação               |

Auditoria final do script:
.local/runtime-audit-script-97194d53-95a7-4a64-b9ab-eace65ed8cfc/audit.json.
Preparação final validada:
.local/runtime-prepare-script-c7e6b5ec-a67d-4292-8e17-7f3fcfaee3cc/preparation.json.
As provas anteriores permanecem nas respectivas pastas; nenhum vídeo foi capturado.
