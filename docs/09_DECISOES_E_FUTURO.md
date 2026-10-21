# Decisões, evolução e relação com o dossiê

[Voltar ao README central](../README.md)

## Decisões em vigor — 21/10/2026

| ID | Decisão | Motivo e consequência |
| --- | --- | --- |
| D01 | Construir demonstração antes de procurar parceiro | Instrução atual do fundador substitui a ordem do dossiê |
| D02 | Fundador pode desenvolver sozinho | Sócio/investidor não são pré-requisitos técnicos; negócio não exige divisão societária para começar |
| D03 | Software primeiro, hardware existente | Webcam e arquivos permitem bancada; câmera própria é hipótese futura |
| D04 | Uma fonte/área/pessoa por vez | Limita custo e deixa falhas observáveis |
| D05 | Pessoa no chão/possível queda é o primeiro caso | Um fluxo concreto antes de múltiplos eventos de segurança |
| D06 | Modelo local de pose + regras | Usa base existente e permite medir limitações sem treinar do zero |
| D07 | Toda plataforma local na v0.1 | Demonstra sem serviço pago ou dependência operacional de internet |
| D08 | NestJS + Next.js + Python | Aproveita o repertório já descrito pelo fundador |
| D09 | PostgreSQL e SQLite; Redis adiado | Duas necessidades duráveis diferentes; fila de avisos simples no banco |
| D10 | Replay, depois webcam, depois IP opcional | Substitui RTSP como única porta de entrada do dossiê |
| D11 | Sem streaming web ou clip contínuo | Reduz armazenamento e exposição; pose e snapshot opt-in bastam para demonstrar |
| D12 | Avisos locais/simulados | Comunicação externa e SLA de atendimento precisam de validação própria |
| D13 | Isolamento preparado, um tenant na UI | Evita reescrever segurança sem construir administração SaaS completa |
| D14 | Regras e evidência versionadas | Permite avaliar mudanças sem reescrever o histórico |
| D15 | Porta do PostgreSQL do Compose configurável por `POSTGRES_PORT` | 21/10/2026, etapa 00: a instalação PostgreSQL existente ocupa 5432. Nesta máquina usar 15432 no `.env` privado; manter loopback e 5432 como padrão do exemplo. Não parar nem alterar o banco existente. Sem mudança de contratos HTTP. |

Manter aqui decisões novas com data, problema, alternativas consideradas, escolha e impacto nos contratos. Não reabrir tudo a cada prompt.

## O que permanece do dossiê

O caso de uso assistivo, o processamento local, o reconhecimento de concorrentes, o fluxo humano, a necessidade de medir falsos alertas e a evolução por evidências. O pacote atual define uma bancada mais acessível para começar; não apaga os requisitos de um futuro serviço real.

## Trajetória depois da v0.1

| Fase | Próxima prova | Condição de avanço |
| --- | --- | --- |
| Demo local | Tecnologia e fluxo reproduzíveis | Etapa 08 concluída e limites conhecidos |
| Apresentação a interessados | Problema relevante, resposta e orçamento | Conversas com demonstração concreta; sem prometer eficácia não medida |
| Piloto acompanhado | Funcionamento em outro ambiente | Escopo autorizado, responsáveis, protocolos de dados/atendimento e avaliação do uso pretendido |
| Primeira versão comercial | Instalação repetível e suporte viável | Desempenho adequado ao escopo, contrato, custos medidos e cliente disposto a pagar |
| Distribuição maior | Onboarding e manutenção sem trabalho artesanal excessivo | Lista de câmeras testadas, observabilidade e operação de suporte |
| Mais sensores/eventos | Ganho mensurável por caso de uso | Dataset, contrato, avaliação e riscos próprios para cada expansão |
| Hardware próprio | Vantagem sobre comprar equipamentos existentes | Demanda, capital, requisitos de hardware, cadeia de fornecimento e suporte justificam investimento |

Uma apresentação pode ser feita pelo próprio fundador; não implica compromisso de sociedade. Investimento é uma decisão de negócio posterior. Não há necessidade de oferecer participação para obter feedback de uma demo.

## O que pode se tornar um ativo da empresa

Compatibilidade realmente testada, implantação compreensível, avaliações reproduzíveis, dados autorizados com boa anotação, políticas temporais eficazes, integração à rotina de resposta e capacidade de suporte. Um dashboard ou um modelo público sozinho não garante defesa competitiva.

## Hipóteses que continuam abertas

Desempenho no notebook e em ambientes novos; acesso local da KAP-S069; aceitação de câmera e privacidade; taxa tolerável de falsos alertas; custo por instalação; disponibilidade de responsável para responder; disposição de pagar. O protótipo pode medir parte dessas hipóteses, não todas.

## Regra para evitar crescimento prematuro

Nova funcionalidade só entra no MVP se for necessária para demonstrar ou verificar o fluxo definido. Ideias de rua, áudio, identificação nominal, sensores novos, aplicativo, plataforma de parceiros ou câmera própria são registradas como backlog, não implementadas pela IA sem uma nova decisão.

Se o modelo de pose não servir, comparar outra base com licença compatível e manter o restante do produto. Se a KAP-S069 não expuser stream, manter webcam. Se o fluxo não gerar utilidade para interessados, rever o caso de uso antes de ampliar hardware e infraestrutura.
