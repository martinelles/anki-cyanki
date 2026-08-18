import { describe, it, expect } from 'vitest';
import { parsePromptMasterCards } from '$lib/notebookParser';
import { EXAMPLE_MD } from '$lib/markdownTemplate';

describe('parsePromptMasterCards', () => {
    // O corte era silencioso: o cartão entrava, com o checklist reduzido ao
    // primeiro item. Quem escreveu três critérios só descobria estudando.
    it('captura o checklist inteiro, não só o primeiro critério', () => {
        const md = [
            'Tipo: CONCEITO',
            'Q: Pergunta?',
            'A: Resposta.',
            'Critérios:',
            '- [ ] Primeiro',
            '- [ ] Segundo',
            '- [ ] Terceiro',
            'Tags: uma, outra',
        ].join('\n');

        const [card] = parsePromptMasterCards(md);
        expect(card.criteria.split('\n')).toHaveLength(3);
        expect(card.criteria).toContain('Terceiro');
    });

    it('captura o checklist inteiro também quando o cartão não tem Tags', () => {
        const md = 'Q: Pergunta?\nA: Resposta.\nCritérios:\n- [ ] Primeiro\n- [ ] Segundo';
        expect(parsePromptMasterCards(md)[0].criteria.split('\n')).toHaveLength(2);
    });

    it('preserva resposta de mais de uma linha', () => {
        const md = 'Q: Pergunta?\nA: Primeira linha\nSegunda linha\nTags: t';
        const [card] = parsePromptMasterCards(md);
        expect(card.back).toBe('Primeira linha\nSegunda linha');
    });

    it('lê o exemplo oferecido para download com os três cartões íntegros', () => {
        const cards = parsePromptMasterCards(EXAMPLE_MD);
        expect(cards).toHaveLength(3);
        expect(cards.map(c => c.type)).toEqual(['CONCEITO', 'FATO', 'PROCEDIMENTO']);
        expect(cards[0].criteria.split('\n')).toHaveLength(2);
        expect(cards[2].criteria.split('\n')).toHaveLength(2);
    });
});
