# 2026-08-17 — Gamificação de engajamento sai do produto

Decisão de Martinelle Santos. Estado dos itens: `ESTADO.csv` (UC-03, UC-10, UC-12
marcados `Descartado`). Este documento guarda o motivo, não o estado.

## O que saiu

| Item | O que era | Código removido |
|---|---|---|
| UC-10 | Mini-games e economia de moedas | `/games`, `/games/memory`, `/games/timed`, campo `coins` de `gamification.ts` |
| UC-03 | Ranking sincronizado | `/ranking`, tabela `leaderboard` |
| UC-12 | Desafios comunitários | `/community`, tabela `challenges` |

Também não foi implementado o mecanismo de "vidas" (hearts), que havia sido
levantado ao comparar o produto com o Duolingo.

## Por quê

O projeto passou a servir a um objetivo datado: a prova da CGU para AFFC —
Tecnologia da Informação, 110 questões, cortes de 12/16/16 e ≥60 na soma. O plano
de estudos que o acompanha é construído sobre **calibração**: registrar a confiança
antes de ver o gabarito e medir o gap contra o acerto, para achar onde a pessoa se
acha melhor do que é.

Os três itens removidos recompensam **volume** — cartões vistos, XP acumulado,
posição relativa. Volume é precisamente o sinal que a calibração existe para
desmentir: dá sensação de progresso sem evidência de acerto. Manter os dois no
mesmo produto é pôr o app para produzir a ilusão que a planilha tenta detectar.

O ranking tem um segundo problema, independente do primeiro: a posição relativa a
outro concurseiro não diz nada sobre o corte por bloco, que é absoluto. E o desafio
comunitário pressupõe uma comunidade que o projeto não tem.

## O que ficou de gamificação, e por quê

O `streak` (UC-11) continua — mas como **registro**, não como prêmio: serve para a
pessoa ver que faltou terça-feira, não para ganhar algo. XP e nível (UC-09) também
seguem, pelo mesmo critério.

## O que reabriria a decisão

Se o produto deixar de servir a uma prova com data e passar a ter mais de um
usuário — aí engajamento volta a ser um problema real, e ranking e desafio voltam
a ser respostas plausíveis para ele.
