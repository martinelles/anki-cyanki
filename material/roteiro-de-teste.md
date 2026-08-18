# Roteiro de teste — fila única do dia (ISS-07)

Escrito em 2026-08-17, contra o código desta branch. A massa de teste é
[caderno-administracao-de-dados.md](caderno-administracao-de-dados.md): 30 cartões
reais, então testar o app e estudar são o mesmo movimento.

O que este roteiro cobre: importação, a fila do dia no painel, a sessão de estudo,
subgrupos e as bordas. O que ele **não** cobre: comunidade, metas, jogos e ranking —
telas que a fila não tocou.

---

## 0. Preparar

| # | Fazer | Esperado |
|---|---|---|
| 0.1 | `docker compose up` na raiz (o `.env` já existe) | Três serviços de pé; sem exceção de conexão no log do backend |
| 0.2 | Abrir http://localhost:5174 | Tela de login em português |
| 0.3 | Criar conta e entrar | Cai no painel, com a fila vazia |

Se quiser começar do zero em qualquer ponto: DevTools → Application → IndexedDB →
apagar `cyanki_db`, e recarregar. O estado do estudo é local.

---

## 1. Importar o caderno

| # | Fazer | Esperado |
|---|---|---|
| 1.1 | Cadernos → Importar → escolher `material/caderno-administracao-de-dados.md` | Pré-visualização com **30 cartões** |
| 1.2 | Conferir a pré-visualização | Todos com Tipo (14 CONCEITO, 13 FATO, 3 PROCEDIMENTO); **17** com checklist de critérios |
| 1.3 | Abrir um cartão com checklist de 3 itens (o primeiro do caderno) | Os **três** critérios aparecem — o parser truncava no primeiro item até hoje |
| 1.4 | Confirmar a importação | Caderno criado; 30 cartões na Memória Global (painel, "Cartões globais") |

---

## 2. A fila do dia — o coração do ISS-07

| # | Fazer | Esperado |
|---|---|---|
| 2.1 | Ir ao painel | Faixa **"Fila de hoje"** no topo, antes de qualquer outra coisa |
| 2.2 | Ler o número | **5 cartões**, com o selo "5 novos" — não 30. O bloco de novos por dia tem teto |
| 2.3 | Contar os botões de estudo do painel | **Um** só: "Continuar →" |
| 2.4 | Clicar em Continuar | Vai para a sessão de estudo; cabeçalho escrito **"Novos"**; progresso `0 / 5` |
| 2.5 | Responder os 5 — erre dois de propósito (nota *Again*) | Ao acabar o quinto, o cabeçalho vira "Prática Extra" |
| 2.6 | Sair e voltar ao painel | A fila remonta sozinha: selos de **vencidos** (os que você errou) **+ novos** (os 5 seguintes) |
| 2.7 | Entrar de novo e conferir a ordem | Os vencidos vêm **antes** dos novos, sempre |

---

## 3. Subgrupos em curso

| # | Fazer | Esperado |
|---|---|---|
| 3.1 | Abrir o caderno importado → gerar subgrupos com tamanho **10** | 3 blocos; a divisão sai temática (modelagem / governança / marco legal) |
| 3.2 | Estudar o bloco 1 errando a maioria (acerto abaixo de 70%) | Painel passa a mostrar o selo "subgrupo" e a linha *Subgrupo em curso: … · bloco 1* |
| 3.3 | Refazer o bloco 1 acertando quase tudo (85% ou mais) | O painel avança para o **bloco 2** |
| 3.4 | Continuar → sessão de estudo | Depois dos vencidos, entram os cartões do bloco 2, com o nome do bloco no cabeçalho |

---

## 4. Bordas

| # | Fazer | Esperado |
|---|---|---|
| 4.1 | Zerar a fila (responder tudo) | Faixa vira **"Tudo em dia 🏆"** e o botão vira "Prática extra" |
| 4.2 | Entrar numa prática ou caderno e sair no meio | Aparece o cartão **"Sessão avulsa em aberto"**, com botão **"Retomar"** — e o "Continuar" segue sendo o único da fila |
| 4.3 | Estudar pela fila e voltar ao painel | O cartão "Sessão avulsa" **não** aparece: a fila não se anuncia duas vezes |
| 4.4 | Desligar a rede, estudar, religar | As revisões entram e sincronizam depois; nada se perde |
| 4.5 | Recarregar a página no meio de uma sessão | A fila é remontada; o progresso reinicia, as revisões já dadas continuam contadas |

---

## Comportamento esperado que parece bug — não abra issue

- **Cartão errado volta como "vencido", não como "erro recente".** O FSRS marca o
  vencimento em minutos, e vencido tem prioridade sobre erro. O selo "erros recentes"
  só aparece quando há mais de 20 vencidos: aí ele puxa para cima o que você errou na
  semana e que ficaria fora do corte.
- **A fila nunca passa de 40 cartões** (20 vencidos + 10 do subgrupo + 5 erros + 5 novos).
  É sessão, não backlog.
- **Um cartão que se encaixa em dois segmentos aparece uma vez só**, no primeiro deles.
- **Caderno parado há mais de 14 dias sai da fila.** Deixa de ser "em curso" e vira
  backlog; volta pela tela do caderno, não pelo "Continuar".

## Defeitos já conhecidos — não reabra

- **UC-34**: o multiplicador de intervalo por tipo não persiste. Um FATO e um CONCEITO
  respondidos juntos vencem no mesmo dia, embora a tela do cartão mostre o tipo.
- **ISS-02, ISS-05, ISS-06**: mensagens de erro da chave Gemini e as duas telas de
  simulados, todas em aberto.

## Onde anotar o que quebrar

Linha nova no `ESTADO.csv` — id `ISS-08` em diante, `frente` = "Issues do GitHub",
`evidencia` = o que você viu e em que tela, `data_conferido` = a data do teste. Depois,
`python scripts/gerar_visoes.py` na mesma sessão. Nada de anotar em prosa solta: o CSV
é a fonte.

---

## Como usar o caderno para estudar de verdade

O teste acaba; o caderno fica. A rotina que a fila assume:

1. **Uma sessão por dia, pelo "Continuar"** — não pelo menu lateral. Se a fila estiver
   vazia, o dia está fechado; prática extra é opcional, não dívida.
2. **Ligue o modo criterioso** (botão no cabeçalho da sessão). Os 17 cartões com
   checklist existem para você se autoavaliar *antes* de virar a resposta — sem isso,
   os cartões de PROCEDIMENTO viram leitura passiva.
3. **Seja honesta no *Again***. A fila do dia seguinte é construída pela sua nota; nota
   inflada vira revisão que não acontece.
4. **Cinco novos por dia** é o teto de propósito: 30 cartões entram em seis dias e as
   revisões se distribuem, em vez de estourarem todas numa terça.
