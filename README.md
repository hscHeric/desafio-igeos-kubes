# Desafio Igeos Kubes

Neste desafio, você vai preparar o ambiente de uma pequena aplicação de mensagens. Queremos conhecer sua capacidade de aprender, conectar serviços, investigar problemas e explicar suas decisões.

## O cenário

Uma pessoa escreve uma mensagem na interface do produtor. O backend publica essa mensagem no Kafka. O backend consumidor recebe a mensagem e a grava no PostgreSQL. A interface do consumidor consulta esse backend e exibe as mensagens armazenadas.

O código das quatro aplicações está disponível neste repositório. Os dois backends usam **Python e FastAPI**; os dois frontends usam **React com TypeScript**. Seu trabalho será preparar os Dockerfiles e o ambiente de execução, incluindo a configuração do Nginx.

| Aplicação | Responsabilidade |
| --- | --- |
| Frontend produtor | Formulário para enviar mensagens e mostrar o resultado da publicação |
| Backend produtor | Receber requisições HTTP e publicar mensagens no Kafka |
| Backend consumidor | Consumir o Kafka, persistir mensagens e oferecer uma API de consulta |
| Frontend consumidor | Consultar a API e listar as mensagens persistidas |

O Nginx será o ponto de entrada HTTP para as duas interfaces e suas APIs. O navegador não acessa Kafka ou PostgreSQL diretamente. O produtor não grava diretamente no banco: queremos exercitar o caminho completo.

## Documentação das aplicações

Cada aplicação tem um `README.md` público dentro de sua própria pasta:

| Pasta | Documentação de deploy |
| --- | --- |
| [apps/producer-api](apps/producer-api/README.md) | Instalação e execução do backend FastAPI, configuração Kafka, preparação do tópico, API de publicação e endpoints de saúde |
| [apps/consumer-api](apps/consumer-api/README.md) | Instalação e execução do backend FastAPI, configuração Kafka/PostgreSQL, preparação do banco, API de consulta e endpoints de saúde |
| [apps/producer-web](apps/producer-web/README.md) | Instalação, desenvolvimento, build e comunicação com a API produtora |
| [apps/consumer-web](apps/consumer-web/README.md) | Instalação, desenvolvimento, build e comunicação com a API consumidora |

Esses documentos informam pré-requisitos, comandos, portas, variáveis de ambiente, valores padrão e formas de verificar o funcionamento. Nos frontends, também explicam quais configurações são aplicadas durante o build. Use este enunciado e a documentação de cada aplicação para preparar sua solução.

## Sua tarefa

1. Criar um **Dockerfile para cada uma das quatro aplicações**.
2. Criar um **Docker Compose** que construa as aplicações e execute também Kafka, PostgreSQL e Nginx.
3. Configurar o **Kafka** para permitir a comunicação entre produtor e consumidor.
4. Configurar o **Nginx** para disponibilizar as interfaces em `/producer/` e `/consumer/`, e encaminhar as APIs em `/api/producer/` e `/api/consumer/`, no mesmo endereço HTTP.
5. Configurar rede, variáveis de ambiente e **persistência do Kafka e do PostgreSQL**. Fornecer um `.env.example` com valores fictícios e documentar como criar o `.env` local.
6. Garantir que o ambiente possa ser iniciado a partir de um clone limpo, seguindo sua documentação, com `docker compose up --build`. A preparação de tópico e banco deve estar automatizada, sem comandos manuais dentro de containers.
7. Documentar como iniciar, verificar, parar e recriar os serviços preservando os dados, além de como apagar os dados intencionalmente.

Somente a porta HTTP do Nginx precisa estar publicada no host. As demais conexões devem funcionar pela rede interna do Compose. Escolha uma porta HTTP livre e informe o endereço de acesso.

Considere a disponibilidade dos serviços na inicialização: um processo iniciado pode ainda não estar pronto para receber conexões. Explique como sua solução lida com isso.

Você pode ajustar o código fornecido se encontrar um problema ou precisar de uma adaptação. Documente a necessidade e preserve o fluxo descrito. Não é necessário criar novas funcionalidades de produto.

## Como verificar sua entrega

Inclua os comandos utilizados e evidências curtas de que os cenários abaixo funcionam:

| Cenário | Resultado esperado |
| --- | --- |
| Construção e primeira inicialização | Após a preparação documentada, o Compose constrói e inicia o ambiente sem ajustes manuais nos containers |
| Acesso pelo Nginx | As duas interfaces e as duas APIs respondem pelo endereço HTTP documentado |
| Envio de uma mensagem | O produtor confirma a publicação; a mesma mensagem aparece na interface do consumidor após o processamento |
| Consumidor temporariamente parado | Mensagens publicadas nesse período aparecem quando o consumidor volta, dentro da retenção configurada |
| Recriação do ambiente | Após `docker compose down` e nova inicialização, sem remover volumes, mensagens já armazenadas continuam disponíveis |
| Kafka recriado com mensagens pendentes | Com o consumidor parado, publique uma mensagem, recrie o ambiente preservando os volumes e confirme o processamento ao retomá-lo |
| Diagnóstico | A documentação mostra como consultar o estado dos serviços e os logs para investigar uma falha |

Uma publicação confirmada significa que o Kafka aceitou a mensagem; a gravação no banco acontece depois. Não exigimos processamento instantâneo. Use um prazo de verificação documentado e razoável para sua máquina.

Não use `docker compose down -v` nos testes de preservação: essa opção remove os volumes gerenciados pelo Compose. Identifique claramente os comandos que apagam dados na sua documentação.

## Entrega

Disponibilize sua solução em um repositório privado acessível à equipe avaliadora e envie o link pelo mesmo canal que você recebeu o desafio.

Inclua:

- Os quatro Dockerfiles, o Compose, a configuração do Nginx e o `.env.example`.
- Um `SOLUTION.md` com pré-requisitos, comandos, endereços, variáveis, decisões e limitações conhecidas.
- Evidências do fluxo completo e da persistência: saídas de comandos, capturas de tela ou um vídeo curto são suficientes.
- Uma estimativa do tempo dedicado, dificuldades encontradas e o que você priorizaria se tivesse mais tempo.

Não publique credenciais reais, tokens, arquivos `.env`, dumps com dados pessoais ou dependências instaladas.

## Tempo e avaliação

Você terá até **23h59 do dia 20/09/2026** para enviar sua solução. A apresentação terá duração de **25 minutos**, em uma entrevista a ser agendada posteriormente conforme a disponibilidade.

Não exigimos cloud, domínio, Kubernetes, alta disponibilidade ou contratação de serviços. A solução deve funcionar localmente. Informe os recursos da máquina usada e qualquer limitação de memória ou arquitetura que você encontrar.

## Extras opcionais

Escolha apenas o que fizer sentido para você. Para cada extra, descreva o problema resolvido, como demonstrá-lo e suas limitações.

| Extra | Uma demonstração útil |
| --- | --- |
| Agregação de logs | Consultar os logs de vários serviços em um lugar e acompanhar uma mensagem pelo identificador |
| Métricas e painel | Exibir requisições, erros e atraso do consumidor; explicar o que uma métrica revela |
| Alertas | Simular uma indisponibilidade e mostrar um alerta, incluindo sua recuperação |
| Backup e restauração do PostgreSQL | Automatizar um backup e restaurá-lo em um banco separado, comprovando a recuperação das mensagens |
| Retenção e reprocessamento no Kafka | Explicar o período de retenção e demonstrar a releitura de eventos sem duplicar registros persistidos |
| Recuperação do Kafka — avançado | Propor e testar uma estratégia que considere eventos, metadados e offsets, deixando claro o que pode ou não ser recuperado |
| Integração contínua | Validar a configuração, construir imagens e executar uma verificação do fluxo completo em CI |
| Segurança dos containers | Reduzir privilégios, limitar permissões e analisar vulnerabilidades das imagens, explicando os resultados |
| Recursos e desempenho | Medir uso de CPU/memória ou aplicar uma carga pequena e justificar limites de recursos |

Persistir dados em um volume e replicar eventos não equivalem, por si só, a ter um backup recuperável. Para o extra de backup, valorizamos a demonstração de restauração. Recuperação de Kafka é um tema mais avançado; não esperamos uma solução de produção de uma pessoa candidata a estágio.

## Uso de IA e LLMs

**É permitido usar LLMs e ferramentas de inteligência artificial para resolver qualquer parte do desafio. Isso não é um problema e não reduz sua avaliação.** Você também pode consultar documentação, tutoriais e exemplos públicos.

A responsabilidade pela entrega continua sendo sua: execute a solução, confira o que foi gerado e esteja preparado para explicar as decisões e investigar uma falha. Uma solução gerada com IA e compreendida por você é uma entrega válida.

Se usar IA, conte brevemente no `SOLUTION.md` quais ferramentas utilizou, em que ajudaram e como você verificou o resultado. Não pedimos histórico de conversas nem prompts privados. Avaliamos o resultado e sua compreensão, sem tentar inferir autoria pelo estilo do código.
