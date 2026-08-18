# Administração de Dados — fundamentos, governança e o marco legal brasileiro

<!--
  Caderno de teste e de estudo do Cyanki. 30 cartões no formato Prompt Master.

  A ordem não é aleatória: com tamanho de subgrupo 10, os três blocos saem
  temáticos — 1) modelagem, 2) qualidade e governança, 3) LGPD e dados abertos.
  Importe em /notebooks/import e gere os subgrupos com tamanho 10.
-->

Tipo: CONCEITO
Q: Quais são os três níveis de modelagem de dados e o que cada um decide?
A: Conceitual — o que o negócio precisa representar, sem tecnologia (entidades, relacionamentos). Lógico — como isso vira estrutura (tabelas, chaves, atributos, tipos genéricos), ainda sem SGBD. Físico — como o SGBD escolhido armazena (tipos nativos, índices, particionamento, tablespaces).
Critérios:
- [ ] Nomeou os três níveis na ordem
- [ ] Disse o que sai de cada um (não só o nome)
- [ ] Deixou claro que só o físico depende do SGBD
Tags: modelagem, fundamentos

Tipo: CONCEITO
Q: No modelo entidade-relacionamento, o que distingue entidade, atributo e relacionamento?
A: Entidade é o objeto sobre o qual se guarda informação (Servidor, Processo). Atributo é a propriedade que a descreve (matrícula, data de posse). Relacionamento é a associação entre entidades (Servidor *lota-se em* Unidade) e pode ter atributos próprios.
Critérios:
- [ ] Deu exemplo de cada um
- [ ] Lembrou que relacionamento também pode ter atributo
Tags: modelagem, mer

Tipo: FATO
Q: O que acontece com um relacionamento N:N quando o modelo conceitual vira modelo lógico?
A: Vira uma tabela associativa própria, cuja chave primária é composta pelas chaves estrangeiras das duas entidades — mais os atributos do relacionamento, se houver.
Tags: modelagem, cardinalidade

Tipo: CONCEITO
Q: Qual a diferença entre chave candidata, chave primária e chave alternativa?
A: Candidata é todo conjunto mínimo de atributos que identifica unicamente a tupla. A escolhida para identificador oficial é a primária; as candidatas restantes são alternativas (implementadas com UNIQUE).
Critérios:
- [ ] Usou "mínimo" ao definir candidata
- [ ] Disse que alternativa vira UNIQUE
Tags: modelagem, chaves

Tipo: CONCEITO
Q: Quando usar chave substituta (surrogate) em vez de chave natural, e o que se perde?
A: Usa-se surrogate quando a chave natural é volátil, longa, composta ou de domínio externo (CPF, código de sistema legado). Perde-se a legibilidade e ganha-se um identificador sem significado — que ainda exige UNIQUE na chave natural, senão a tabela aceita duplicata lógica.
Critérios:
- [ ] Citou volatilidade ou tamanho como motivo
- [ ] Lembrou do UNIQUE na chave natural
Tags: modelagem, chaves

Tipo: PROCEDIMENTO
Q: Quais os passos para normalizar uma tabela até a 3FN?
A: 1) eliminar grupos repetitivos e atributos multivalorados, deixando valores atômicos (1FN); 2) identificar a chave primária e remover atributos que dependem só de parte dela (2FN); 3) remover atributos que dependem de outro atributo não-chave, movendo-os para tabela própria (3FN).
Critérios:
- [ ] Três passos na ordem
- [ ] Ligou cada passo à forma normal correspondente
Tags: modelagem, normalizacao

Tipo: FATO
Q: Defina 1FN, 2FN e 3FN em uma linha cada.
A: 1FN — todo atributo é atômico e não há grupo repetitivo. 2FN — está em 1FN e nenhum atributo não-chave depende parcialmente da chave primária composta. 3FN — está em 2FN e nenhum atributo não-chave depende transitivamente da chave.
Tags: normalizacao, formas-normais

Tipo: FATO
Q: O que a Forma Normal de Boyce-Codd (BCNF) exige além da 3FN?
A: Que todo determinante da relação seja superchave. A 3FN ainda admite anomalia quando há chaves candidatas sobrepostas; a BCNF fecha esse caso.
Tags: normalizacao, formas-normais

Tipo: CONCEITO
Q: Em que situação a desnormalização se justifica, e qual o preço?
A: Justifica-se quando leitura analítica repetida domina o uso e o custo do join é medido, não suposto — típico de data warehouse. O preço é redundância controlada: toda atualização passa a ter mais de um lugar para dar errado, e a consistência vira responsabilidade do processo de carga.
Critérios:
- [ ] Condicionou à medição, não ao palpite
- [ ] Nomeou a redundância e o risco de atualização
Tags: modelagem, desempenho

Tipo: CONCEITO
Q: O que a integridade referencial garante, e o que ON DELETE CASCADE decide?
A: Garante que toda chave estrangeira aponte para uma linha existente na tabela referenciada. O ON DELETE decide a política quando o pai é apagado: CASCADE apaga os filhos, RESTRICT/NO ACTION impede a exclusão, SET NULL órfã a referência.
Critérios:
- [ ] Definiu integridade referencial
- [ ] Citou pelo menos duas políticas de ON DELETE
Tags: modelagem, integridade

Tipo: FATO
Q: Quantas e quais são as áreas de conhecimento do DAMA-DMBOK (2ª edição)?
A: Onze, com Governança de Dados no centro da roda: Arquitetura; Modelagem e Design; Armazenamento e Operações; Segurança; Integração e Interoperabilidade; Documentos e Conteúdo; Dados Mestres e de Referência; Data Warehousing e BI; Metadados; Qualidade de Dados.
Tags: governanca, dama

Tipo: CONCEITO
Q: Qual a diferença entre data owner, data steward e data custodian?
A: O owner responde pelo dado perante o negócio — define regra, criticidade e quem acessa. O steward cuida do dado no dia a dia: definição, qualidade, dicionário, resolução de divergência. O custodian é a área técnica que guarda e opera a infraestrutura, sem decidir sobre o conteúdo.
Critérios:
- [ ] Separou decisão (owner) de zeladoria (steward)
- [ ] Disse que custodian não decide sobre o conteúdo
Tags: governanca, papeis

Tipo: FATO
Q: Cite as dimensões clássicas de qualidade de dados.
A: Completude, unicidade (ausência de duplicata), consistência, validade (conformidade ao domínio), acurácia (aderência ao mundo real), integridade (referências íntegras) e tempestividade (atualidade).
Tags: qualidade, dimensoes

Tipo: PROCEDIMENTO
Q: Quais os passos de uma perfilagem (data profiling) de uma tabela desconhecida?
A: 1) contagem de linhas e de valores distintos por coluna; 2) taxa de nulo e de vazio por coluna; 3) domínio observado — mínimo, máximo, padrões, top valores; 4) candidatas a chave (colunas com distintos = linhas); 5) dependências e referências entre colunas e tabelas; 6) registro dos achados no dicionário, com data.
Critérios:
- [ ] Começou por volume e distintos
- [ ] Incluiu a busca por chave candidata
- [ ] Terminou registrando o achado
Tags: qualidade, profiling

Tipo: CONCEITO
Q: O que distingue metadado de negócio, técnico e operacional?
A: De negócio — o significado: definição do termo, regra, dono, criticidade. Técnico — a estrutura: tabela, coluna, tipo, chave, relacionamento. Operacional — a execução: quando a carga rodou, quantas linhas, quantas rejeições, quem acessou.
Critérios:
- [ ] Deu um exemplo de cada categoria
Tags: metadados, governanca

Tipo: CONCEITO
Q: O que um dicionário de dados precisa registrar para ser útil?
A: Por atributo: nome de negócio e nome físico, definição em uma frase, tipo e domínio de valores, obrigatoriedade, regra de derivação quando calculado, sistema de origem, dono e a data em que a definição foi conferida.
Critérios:
- [ ] Incluiu definição em linguagem de negócio
- [ ] Incluiu origem e dono
- [ ] Lembrou da data de conferência
Tags: metadados, dicionario

Tipo: CONCEITO
Q: Qual a diferença entre dicionário de dados e catálogo de dados?
A: O dicionário descreve o significado dos atributos de um sistema ou modelo. O catálogo é o inventário pesquisável dos conjuntos de dados da organização — onde estão, quem responde, como acessar, qual a linhagem — e costuma consumir vários dicionários.
Tags: metadados, catalogo

Tipo: CONCEITO
Q: O que é linhagem de dados e que pergunta ela responde que nenhum outro artefato responde?
A: É o rastro do dado da origem ao consumo, transformação a transformação. Responde "se esta coluna está errada, o que mais está errado e desde quando" — impacto para frente e causa para trás.
Critérios:
- [ ] Definiu como rastro origem → consumo
- [ ] Citou análise de impacto ou de causa
Tags: metadados, linhagem

Tipo: CONCEITO
Q: O que é MDM e o que é o golden record?
A: MDM (Master Data Management) é a disciplina que mantém uma versão única e confiável das entidades compartilhadas por vários sistemas — pessoa, órgão, fornecedor. O golden record é o registro consolidado resultante, montado por regras de sobrevivência que decidem qual fonte vence campo a campo.
Critérios:
- [ ] Restringiu MDM a dados mestres, não a todo dado
- [ ] Explicou que o golden record vem de regra, não de sorte
Tags: mdm, governanca

Tipo: FATO
Q: Qual a diferença entre ETL e ELT, e o que motiva a escolha?
A: No ETL a transformação acontece antes da carga, num motor próprio; no ELT o dado bruto é carregado primeiro e transformado dentro do destino. ELT ganha quando o destino tem poder de processamento elástico e se quer preservar o bruto; ETL ganha quando o dado não pode entrar no destino sem tratamento — sigilo, por exemplo.
Tags: integracao, etl

Tipo: FATO
Q: Qual lei institui a LGPD, quando ela entrou em vigor e desde quando há sanção administrativa?
A: Lei 13.709/2018. Em vigor desde 18/09/2020; as sanções administrativas passaram a ser aplicáveis em 01/08/2021.
Tags: lgpd, marco-legal

Tipo: FATO
Q: O consentimento é a regra para tratar dado pessoal na LGPD?
A: Não. É uma das dez bases legais do art. 7º — ao lado de cumprimento de obrigação legal, execução de política pública, execução de contrato, exercício regular de direito, proteção da vida, tutela da saúde, legítimo interesse e proteção ao crédito. No setor público, a base usual é a execução de política pública, não o consentimento.
Critérios:
- [ ] Respondeu que não
- [ ] Citou pelo menos três outras bases
- [ ] Lembrou da base típica do setor público
Tags: lgpd, bases-legais

Tipo: FATO
Q: O que é dado pessoal sensível na LGPD?
A: Dado sobre origem racial ou étnica, convicção religiosa, opinião política, filiação a sindicato ou organização de caráter religioso, filosófico ou político, dado referente à saúde ou à vida sexual, e dado genético ou biométrico, quando vinculado a uma pessoa natural.
Tags: lgpd, definicoes

Tipo: CONCEITO
Q: Qual a diferença prática entre anonimização e pseudonimização?
A: Dado anonimizado perde a possibilidade de associação ao titular por meios razoáveis e, por isso, sai do alcance da LGPD — enquanto a anonimização for irreversível. Pseudonimizado apenas troca o identificador por um código cuja chave de reversão existe em outro lugar: continua sendo dado pessoal e continua sob a lei.
Critérios:
- [ ] Disse que pseudonimizado continua sendo dado pessoal
- [ ] Condicionou a saída do escopo à irreversibilidade
Tags: lgpd, anonimizacao

Tipo: FATO
Q: Quais direitos o titular pode exercer perante o controlador (art. 18 da LGPD)?
A: Confirmação da existência de tratamento; acesso; correção; anonimização, bloqueio ou eliminação de dado desnecessário ou tratado em desconformidade; portabilidade; eliminação do dado tratado com consentimento; informação sobre compartilhamento; informação sobre a possibilidade de negar consentimento; e revogação do consentimento.
Tags: lgpd, direitos-do-titular

Tipo: FATO
Q: Quem é o encarregado na LGPD e qual o papel da ANPD?
A: O encarregado (art. 41) é indicado pelo controlador para ser o canal de comunicação com titulares e com a autoridade. A ANPD é o órgão nacional responsável por zelar, orientar e fiscalizar o cumprimento da lei, além de aplicar sanções.
Tags: lgpd, governanca

Tipo: FATO
Q: Qual o prazo de resposta a um pedido de acesso à informação na Lei 12.527/2011?
A: Resposta imediata quando disponível; do contrário, até 20 dias, prorrogáveis por mais 10 mediante justificativa expressa ao requerente.
Tags: lai, marco-legal

Tipo: FATO
Q: O que o Decreto 8.777/2016 instituiu e qual instrumento ele exige de cada órgão?
A: Instituiu a Política de Dados Abertos do Poder Executivo federal e exige de cada órgão um Plano de Dados Abertos (PDA), que relaciona os conjuntos a serem abertos, o cronograma e os responsáveis.
Tags: dados-abertos, marco-legal

Tipo: CONCEITO
Q: O que mede a escala de cinco estrelas de dados abertos?
A: O grau de reutilização do dado publicado: ★ disponível na web sob licença aberta, em qualquer formato; ★★ estruturado e legível por máquina; ★★★ em formato não proprietário; ★★★★ com URIs identificando as coisas; ★★★★★ ligado a outros conjuntos de dados.
Critérios:
- [ ] Acertou a licença aberta como primeiro degrau
- [ ] Separou "estruturado" de "não proprietário"
Tags: dados-abertos, qualidade

Tipo: PROCEDIMENTO
Q: Quais os passos para publicar um conjunto de dados como dado aberto num órgão federal?
A: 1) inventariar e priorizar o conjunto no PDA; 2) classificar quanto a sigilo e a dado pessoal, decidindo o que sai, o que é anonimizado e o que não é publicado; 3) documentar metadados e dicionário; 4) escolher formato aberto e definir periodicidade de atualização; 5) publicar no portal e registrar no catálogo; 6) nomear o responsável pela manutenção e monitorar o uso.
Critérios:
- [ ] Colocou a triagem de sigilo antes da publicação
- [ ] Incluiu metadados e periodicidade
- [ ] Terminou com responsável nomeado
Tags: dados-abertos, procedimento
