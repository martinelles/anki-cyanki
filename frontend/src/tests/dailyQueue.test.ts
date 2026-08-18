import { describe, it, expect, beforeEach } from 'vitest';
import 'fake-indexeddb/auto';
import { db, type Flashcard } from '$lib/db';
import {
    orderQueue,
    countSegments,
    getRecentErrorIds,
    getGroupInCourse,
    buildDailyQueue,
    SEGMENT_LIMIT,
    ERROR_WINDOW_MS,
    GROUP_IN_COURSE_MS,
} from '$lib/dailyQueue';

const DIA = 24 * 60 * 60 * 1000;

function card(id: string, createdAt = 0): Flashcard {
    return { id, front: `frente ${id}`, back: `verso ${id}`, tags: [], createdAt };
}

async function limpar() {
    await Promise.all([
        db.flashcards.clear(),
        db.reviewLogs.clear(),
        db.notebooks.clear(),
        db.notebookGroups.clear(),
        db.groupSessions.clear(),
    ]);
}

describe('ISS-07: fila única do dia', () => {
    beforeEach(limpar);

    describe('orderQueue', () => {
        it('segue a ordem vencidos → subgrupo → erros → novos', () => {
            const fila = orderQueue({
                vencidos: [card('v')],
                subgrupo: [card('s')],
                erros: [card('e')],
                novos: [card('n')],
            });
            expect(fila.map(f => f.card.id)).toEqual(['v', 's', 'e', 'n']);
            expect(fila.map(f => f.kind)).toEqual(['vencidos', 'subgrupo', 'erros', 'novos']);
        });

        // Um cartão vencido que também está no subgrupo em curso apareceria duas
        // vezes na sessão — o usuário leria isso como bug, não como reforço.
        it('não repete o mesmo cartão em dois segmentos', () => {
            const repetido = card('x');
            const fila = orderQueue({
                vencidos: [repetido],
                subgrupo: [repetido, card('s')],
                erros: [repetido],
                novos: [],
            });
            expect(fila.map(f => f.card.id)).toEqual(['x', 's']);
            expect(countSegments(fila)).toEqual({ vencidos: 1, subgrupo: 1, erros: 0, novos: 0 });
        });

        it('respeita o teto de cada segmento', () => {
            const muitos = Array.from({ length: 50 }, (_, i) => card(`n${i}`));
            const fila = orderQueue({ vencidos: [], subgrupo: [], erros: [], novos: muitos });
            expect(fila).toHaveLength(SEGMENT_LIMIT.novos);
        });

        it('devolve fila vazia quando não há nada a fazer', () => {
            expect(orderQueue({ vencidos: [], subgrupo: [], erros: [], novos: [] })).toEqual([]);
        });
    });

    describe('getRecentErrorIds', () => {
        const agora = 1_700_000_000_000;

        it('traz o cartão cuja última revisão foi um erro', async () => {
            await db.reviewLogs.add({ flashcardId: 'a', grade: 1, state: 1, reviewedAt: agora - DIA, synced: true });
            expect(await getRecentErrorIds(agora)).toEqual(['a']);
        });

        // Errar terça e acertar quarta não devolve o cartão para a fila: quem
        // manda é a revisão mais recente, não a pior.
        it('ignora o cartão que errou e depois reacertou', async () => {
            await db.reviewLogs.bulkAdd([
                { flashcardId: 'a', grade: 1, state: 1, reviewedAt: agora - 2 * DIA, synced: true },
                { flashcardId: 'a', grade: 3, state: 2, reviewedAt: agora - DIA, synced: true },
            ]);
            expect(await getRecentErrorIds(agora)).toEqual([]);
        });

        it('ignora erro mais velho que a janela de sete dias', async () => {
            await db.reviewLogs.add({
                flashcardId: 'a', grade: 1, state: 1,
                reviewedAt: agora - ERROR_WINDOW_MS - DIA, synced: true,
            });
            expect(await getRecentErrorIds(agora)).toEqual([]);
        });

        it('ordena do erro mais novo para o mais velho', async () => {
            await db.reviewLogs.bulkAdd([
                { flashcardId: 'velho', grade: 1, state: 1, reviewedAt: agora - 3 * DIA, synced: true },
                { flashcardId: 'novo', grade: 1, state: 1, reviewedAt: agora - DIA, synced: true },
            ]);
            expect(await getRecentErrorIds(agora)).toEqual(['novo', 'velho']);
        });
    });

    describe('getGroupInCourse', () => {
        const agora = 1_700_000_000_000;

        async function montarCaderno() {
            await db.notebooks.add({ id: 'nb', title: 'Direito', content: '', createdAt: 0, updatedAt: 0 });
            await db.notebookGroups.bulkAdd([1, 2, 3].map(i => ({
                id: `g${i}`, notebookId: 'nb', groupIndex: i,
                cardIds: [`c${i}`], cardCount: 1, groupSize: 1,
                shuffled: false, shuffleSeed: null, createdAt: 0, synced: true,
            })));
        }

        it('devolve null quando nenhum subgrupo foi estudado', async () => {
            await montarCaderno();
            expect(await getGroupInCourse(agora)).toBeNull();
        });

        it('repete o bloco cujo acerto ficou abaixo de 70%', async () => {
            await montarCaderno();
            await db.groupSessions.add({
                id: 's1', groupId: 'g1', notebookId: 'nb', score: 'D',
                accuracy: 0.5, totalCards: 10, correctCards: 5, studiedAt: agora - DIA, synced: true,
            });
            expect((await getGroupInCourse(agora))?.id).toBe('g1');
        });

        it('avança para o próximo bloco quando o anterior foi dominado', async () => {
            await montarCaderno();
            await db.groupSessions.add({
                id: 's1', groupId: 'g1', notebookId: 'nb', score: 'S',
                accuracy: 1, totalCards: 10, correctCards: 10, studiedAt: agora - DIA, synced: true,
            });
            expect((await getGroupInCourse(agora))?.id).toBe('g2');
        });

        it('devolve null quando todos os blocos foram dominados', async () => {
            await montarCaderno();
            await db.groupSessions.bulkAdd([1, 2, 3].map(i => ({
                id: `s${i}`, groupId: `g${i}`, notebookId: 'nb', score: 'S' as const,
                accuracy: 1, totalCards: 10, correctCards: 10, studiedAt: agora - i * 1000, synced: true,
            })));
            expect(await getGroupInCourse(agora)).toBeNull();
        });

        // Caderno largado há um mês não é "em curso" — é backlog, e backlog não
        // entra na fila do dia sem o usuário pedir.
        it('devolve null quando a última sessão é velha demais', async () => {
            await montarCaderno();
            await db.groupSessions.add({
                id: 's1', groupId: 'g1', notebookId: 'nb', score: 'D',
                accuracy: 0.5, totalCards: 10, correctCards: 5,
                studiedAt: agora - GROUP_IN_COURSE_MS - DIA, synced: true,
            });
            expect(await getGroupInCourse(agora)).toBeNull();
        });
    });

    describe('buildDailyQueue', () => {
        const agora = 1_700_000_000_000;

        // Cartão nunca revisado nasce com `due` no passado no FSRS. Sem o filtro
        // por histórico ele entraria como "vencido" e a fila mentiria o número.
        it('classifica cartão nunca revisado como novo, não como vencido', async () => {
            await db.flashcards.add(card('c1'));
            const fila = await buildDailyQueue(agora);
            expect(fila.counts).toEqual({ vencidos: 0, subgrupo: 0, erros: 0, novos: 1 });
            expect(fila.entries[0].kind).toBe('novos');
        });

        it('põe o vencido antes do novo', async () => {
            await db.flashcards.bulkAdd([card('velho', 0), card('inedito', 1)]);
            await db.reviewLogs.add({
                flashcardId: 'velho', grade: 1, state: 1,
                reviewedAt: agora - 30 * DIA, synced: true,
            });
            const fila = await buildDailyQueue(agora);
            expect(fila.entries.map(e => e.card.id)).toEqual(['velho', 'inedito']);
            expect(fila.entries.map(e => e.kind)).toEqual(['vencidos', 'novos']);
            expect(fila.total).toBe(2);
        });

        it('limita o bloco de novos por dia', async () => {
            await db.flashcards.bulkAdd(
                Array.from({ length: 20 }, (_, i) => card(`n${i}`, i))
            );
            const fila = await buildDailyQueue(agora);
            expect(fila.total).toBe(SEGMENT_LIMIT.novos);
        });

        it('devolve fila vazia sem cartões', async () => {
            const fila = await buildDailyQueue(agora);
            expect(fila.total).toBe(0);
            expect(fila.groupLabel).toBeNull();
        });
    });
});
