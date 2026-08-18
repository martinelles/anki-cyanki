import { db, type Flashcard, type NotebookGroup } from '$lib/db';
import { getAllCardStates, Rating } from '$lib/fsrs';
import { getGroupsForNotebook, getValidCardsForGroup } from '$lib/notebookGroups';

/**
 * ISS-07: a fila única do dia.
 *
 * O produto tinha onze portas de entrada de estudo e nenhuma respondia "o que eu
 * faço agora". A fila responde: monta uma ordem só, sempre a mesma, e o painel
 * expõe um botão só. A ordem não é estética — é a ordem em que esquecer custa
 * mais caro:
 *
 *   1. vencidos  — o FSRS já disse que hoje é o limite; adiar aqui é perder o cartão
 *   2. subgrupo  — o bloco em curso, para não deixar caderno pela metade
 *   3. erros     — o que você errou na última semana e ainda não reacertou
 *   4. novos     — um bloco por dia, para a fila de amanhã não estourar
 *
 * Cada cartão aparece uma vez só, no primeiro segmento que o reivindicar.
 */

export type QueueSegmentKind = 'vencidos' | 'subgrupo' | 'erros' | 'novos';

export const SEGMENT_LABEL: Record<QueueSegmentKind, string> = {
    vencidos: 'Vencidos',
    subgrupo: 'Subgrupo em curso',
    erros: 'Erros recentes',
    novos: 'Novos',
};

/** Teto por segmento — a fila é o trabalho de uma sessão, não o backlog inteiro. */
export const SEGMENT_LIMIT: Record<QueueSegmentKind, number> = {
    vencidos: 20,
    subgrupo: 10,
    erros: 5,
    novos: 5,
};

/** Janela em que um erro ainda conta como "recente". */
export const ERROR_WINDOW_MS = 7 * 24 * 60 * 60 * 1000;

/** Depois disso, um subgrupo não está mais "em curso" — está abandonado. */
export const GROUP_IN_COURSE_MS = 14 * 24 * 60 * 60 * 1000;

/** Acerto a partir do qual o subgrupo é dado por vencido e a fila avança. */
export const GROUP_MASTERY = 0.85;

/** Acerto abaixo do qual vale repetir o mesmo subgrupo em vez de avançar. */
export const GROUP_REDO = 0.70;

export interface QueueEntry {
    card: Flashcard;
    kind: QueueSegmentKind;
}

export interface DailyQueue {
    entries: QueueEntry[];
    counts: Record<QueueSegmentKind, number>;
    total: number;
    /** Nome do subgrupo em curso, quando há um — ex.: "Direito Administrativo · bloco 3". */
    groupLabel: string | null;
}

/** Ingredientes da fila, já lidos do banco. Separado para poder ser testado sem Dexie. */
export interface QueueInput {
    /** Vencidos no FSRS, do mais atrasado para o menos. */
    vencidos: Flashcard[];
    /** Cartões do subgrupo em curso, na ordem do subgrupo. */
    subgrupo: Flashcard[];
    /** Cartões cuja última revisão foi um erro recente, do erro mais novo ao mais velho. */
    erros: Flashcard[];
    /** Cartões nunca revisados, do mais antigo ao mais novo. */
    novos: Flashcard[];
}

const ORDER: QueueSegmentKind[] = ['vencidos', 'subgrupo', 'erros', 'novos'];

/**
 * Ordena e deduplica os segmentos. Função pura: mesma entrada, mesma fila.
 */
export function orderQueue(input: QueueInput): QueueEntry[] {
    const entries: QueueEntry[] = [];
    const seen = new Set<string>();

    for (const kind of ORDER) {
        let taken = 0;
        for (const card of input[kind]) {
            if (taken >= SEGMENT_LIMIT[kind]) break;
            if (seen.has(card.id)) continue;
            seen.add(card.id);
            entries.push({ card, kind });
            taken++;
        }
    }

    return entries;
}

export function countSegments(entries: QueueEntry[]): Record<QueueSegmentKind, number> {
    const counts: Record<QueueSegmentKind, number> = { vencidos: 0, subgrupo: 0, erros: 0, novos: 0 };
    for (const e of entries) counts[e.kind]++;
    return counts;
}

/**
 * Qual subgrupo está "em curso": o caderno estudado mais recentemente decide, e
 * dentro dele vale repetir o bloco mal pontuado antes de abrir o próximo.
 * Devolve `null` quando não há caderno recente ou quando todos os blocos já foram
 * dominados.
 */
export async function getGroupInCourse(now = Date.now()): Promise<NotebookGroup | null> {
    const sessions = await db.groupSessions.orderBy('studiedAt').reverse().toArray();
    const last = sessions[0];
    if (!last || now - last.studiedAt > GROUP_IN_COURSE_MS) return null;

    const groups = await getGroupsForNotebook(last.notebookId);
    if (groups.length === 0) return null;

    // Bloco mal pontuado se repete antes de a fila avançar.
    if (last.accuracy < GROUP_REDO) {
        return groups.find(g => g.id === last.groupId) ?? null;
    }

    const bestAccuracy = new Map<string, number>();
    for (const s of sessions) {
        bestAccuracy.set(s.groupId, Math.max(bestAccuracy.get(s.groupId) ?? 0, s.accuracy));
    }

    // Primeiro bloco ainda não dominado, na ordem do caderno (nunca estudado conta como 0).
    return groups.find(g => (bestAccuracy.get(g.id) ?? 0) < GROUP_MASTERY) ?? null;
}

/**
 * Cartões cuja **última** revisão foi um erro dentro da janela. Errar terça e
 * acertar quarta não devolve o cartão para a fila — quem manda é a revisão mais
 * recente, não a pior.
 */
export async function getRecentErrorIds(now = Date.now()): Promise<string[]> {
    const logs = await db.reviewLogs.orderBy('reviewedAt').toArray();
    const latest = new Map<string, { grade: number; reviewedAt: number }>();
    for (const log of logs) {
        latest.set(log.flashcardId, { grade: log.grade, reviewedAt: log.reviewedAt });
    }

    return [...latest.entries()]
        .filter(([, l]) => l.grade === Rating.Again && now - l.reviewedAt <= ERROR_WINDOW_MS)
        .sort((a, b) => b[1].reviewedAt - a[1].reviewedAt)
        .map(([id]) => id);
}

/**
 * Monta a fila do dia a partir do banco local. É o que o painel e o /study leem.
 */
export async function buildDailyQueue(now = Date.now()): Promise<DailyQueue> {
    const [allCards, states, reviewedIdsRaw, errorIds, group] = await Promise.all([
        db.flashcards.toArray(),
        getAllCardStates(),
        db.reviewLogs.orderBy('flashcardId').uniqueKeys(),
        getRecentErrorIds(now),
        getGroupInCourse(now),
    ]);

    const byId = new Map(allCards.map(c => [c.id, c]));
    const reviewed = new Set(reviewedIdsRaw as string[]);
    const pick = (ids: string[]): Flashcard[] =>
        ids.map(id => byId.get(id)).filter((c): c is Flashcard => c !== undefined);

    // Cartão nunca revisado nasce vencido no FSRS; ele é "novo", não "vencido".
    const vencidos = allCards
        .filter(c => reviewed.has(c.id) && (states.get(c.id)?.due.getTime() ?? Infinity) <= now)
        .sort((a, b) =>
            (states.get(a.id)?.due.getTime() ?? 0) - (states.get(b.id)?.due.getTime() ?? 0)
        );

    const subgrupo = group ? await getValidCardsForGroup(group) : [];

    const novos = allCards
        .filter(c => !reviewed.has(c.id))
        .sort((a, b) => a.createdAt - b.createdAt);

    const entries = orderQueue({ vencidos, subgrupo, erros: pick(errorIds), novos });

    let groupLabel: string | null = null;
    if (group) {
        const notebook = await db.notebooks.get(group.notebookId);
        groupLabel = `${notebook?.title ?? 'Caderno'} · bloco ${group.groupIndex}`;
    }

    return { entries, counts: countSegments(entries), total: entries.length, groupLabel };
}
