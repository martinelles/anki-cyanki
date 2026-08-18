/**
 * ISS-04: modelo e instruções de .md para quem cria ou importa um caderno.
 *
 * Fonte única do formato aceito por `parsePromptMasterCards` e por
 * `parseAndInjectNotebookFlashcards` (ambos em $lib/notebookParser).
 *
 * Regra que os dois parsers compartilham: "Q:" precisa estar na coluna 0.
 * É por isso que o bloco de exemplo dentro de NOTEBOOK_TEMPLATE está
 * indentado — indentado ele é documentação, alinhado à esquerda ele vira
 * cartão. Mexer na indentação do template cria cartões-fantasma em todo
 * caderno novo.
 */

/** Conteúdo inicial de um caderno recém-criado. */
export function notebookTemplate(title: string): string {
	return `# ${title}

<!--
  COMO ESCREVER SEUS FLASHCARDS

  Cada cartão começa com "Q:" na primeira coluna e termina na linha em
  branco seguinte. O bloco abaixo está indentado de propósito: assim ele
  vale como exemplo e não vira cartão. Copie, cole fora deste comentário
  e alinhe à esquerda.

    Tipo: CONCEITO
    Q: O que é o princípio da legalidade na Administração Pública?
    A: A Administração só pode agir quando a lei autoriza — ao contrário do particular, que pode tudo que a lei não proíbe.
    Critérios:
    - [ ] Explicou com palavras próprias
    - [ ] Contrastou com o regime do particular
    Tags: dir-administrativo, principios

  Tipo (opcional) — muda o intervalo de revisão:
    CONCEITO ....... entender e explicar
    FATO ........... lei seca, prazo, número
    PROCEDIMENTO ... passo a passo

  Critérios (opcional) — checklist que aparece no verso para você se
  autoavaliar antes de ver a nota.

  Tags (opcional) — separadas por vírgula.
-->

`;
}

/** Arquivo .md de exemplo oferecido para download na tela de importação. */
export const EXAMPLE_MD = `# Exemplo de importação — formato Prompt Master
<!-- Apague estes exemplos e escreva os seus. Um cartão por bloco, separados por uma linha em branco. -->

Tipo: CONCEITO
Q: O que é o princípio da legalidade na Administração Pública?
A: A Administração só pode agir quando a lei autoriza — ao contrário do particular, que pode tudo que a lei não proíbe.
Critérios:
- [ ] Explicou com palavras próprias
- [ ] Contrastou com o regime do particular
Tags: dir-administrativo, principios

Tipo: FATO
Q: Qual o prazo para a Administração anular ato do qual decorram efeitos favoráveis ao destinatário (Lei 9.784/1999)?
A: 5 anos, contados da data em que o ato foi praticado, salvo comprovada má-fé.
Tags: dir-administrativo, lei-9784, prazos

Tipo: PROCEDIMENTO
Q: Quais as fases da licitação na Lei 14.133/2021, em ordem?
A: 1) preparatória; 2) divulgação do edital; 3) apresentação de propostas e lances; 4) julgamento; 5) habilitação; 6) recursal; 7) homologação.
Critérios:
- [ ] Listou as 7 fases
- [ ] Colocou habilitação depois do julgamento
Tags: licitacoes, lei-14133

<!--
  Tipo (opcional) — CONCEITO, FATO ou PROCEDIMENTO; muda o intervalo de revisão.
  Critérios (opcional) — checklist de autoavaliação exibido no verso.
  Tags (opcional) — separadas por vírgula.

  Formato alternativo (Anki básico), um cartão por linha:
    Frente do cartão;Verso do cartão
-->
`;

/** Dispara o download de um texto como arquivo. Só roda no browser. */
export function downloadMarkdown(filename: string, content: string) {
	const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' });
	const url = URL.createObjectURL(blob);
	const a = document.createElement('a');
	a.href = url;
	a.download = filename;
	a.click();
	URL.revokeObjectURL(url);
}
