import { describe, it, expect } from 'vitest';
import { notebookTemplate, EXAMPLE_MD } from '$lib/markdownTemplate';
import { parsePromptMasterCards, parseAndInjectNotebookFlashcards } from '$lib/notebookParser';

describe('ISS-04: modelo de markdown', () => {
    describe('notebookTemplate', () => {
        it('mantém o título do caderno', () => {
            expect(notebookTemplate('Direito Administrativo')).toContain('# Direito Administrativo');
        });

        // O exemplo dentro do template está indentado justamente para não ser
        // reconhecido como cartão. Sem isso, todo caderno novo nasce com um
        // flashcard-fantasma sobre o princípio da legalidade.
        it('não gera cartão pelo parser de importação', () => {
            expect(parsePromptMasterCards(notebookTemplate('Caderno novo'))).toHaveLength(0);
        });

        it('não gera cartão pelo parser do editor de cadernos', async () => {
            const { extractedCards, hasNewInjections } =
                await parseAndInjectNotebookFlashcards(notebookTemplate('Caderno novo'));
            expect(extractedCards).toHaveLength(0);
            expect(hasNewInjections).toBe(false);
        });
    });

    describe('EXAMPLE_MD', () => {
        const cards = parsePromptMasterCards(EXAMPLE_MD);

        it('produz os três cartões de exemplo', () => {
            expect(cards).toHaveLength(3);
        });

        it('cobre os três tipos de cartão', () => {
            expect(cards.map(c => c.type)).toEqual(['CONCEITO', 'FATO', 'PROCEDIMENTO']);
        });

        it('extrai critérios e tags', () => {
            expect(cards[0].criteria).toContain('- [ ] Explicou com palavras próprias');
            expect(cards[0].tags).toEqual(['dir-administrativo', 'principios']);
            expect(cards[1].criteria).toBe('');
        });

        it('não é confundido com o formato Anki básico pela tela de importação', () => {
            // Mesma heurística de notebooks/import/+page.svelte
            const isAnkiBasic = !EXAMPLE_MD.includes('Q:') && EXAMPLE_MD.includes(';');
            expect(isAnkiBasic).toBe(false);
        });
    });
});
