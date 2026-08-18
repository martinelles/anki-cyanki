<script lang="ts">
    import { onMount } from 'svelte';
    import { session } from '$lib/authStore';
    import { PUBLIC_API_URL } from '$env/static/public';

    interface Convite {
        code: string;
        created_at: string;
        expires_at: string | null;
        used_at: string | null;
    }

    let convites: Convite[] = [];
    let carregando = true;
    let gerando = false;
    let erro = '';
    let copiado = '';

    function cabecalho() {
        return { 'Content-Type': 'application/json', Authorization: `Bearer ${$session.token}` };
    }

    async function carregar() {
        carregando = true;
        erro = '';
        try {
            const res = await fetch(`${PUBLIC_API_URL}/auth/invites`, { headers: cabecalho() });
            if (!res.ok) throw new Error('Não foi possível carregar os convites.');
            convites = await res.json();
        } catch (e: any) {
            erro = e.message;
        } finally {
            carregando = false;
        }
    }

    async function gerar() {
        gerando = true;
        erro = '';
        try {
            const res = await fetch(`${PUBLIC_API_URL}/auth/invites`, {
                method: 'POST',
                headers: cabecalho()
            });
            if (!res.ok) throw new Error('Não foi possível gerar o convite.');
            convites = [await res.json(), ...convites];
        } catch (e: any) {
            erro = e.message;
        } finally {
            gerando = false;
        }
    }

    async function copiar(code: string) {
        await navigator.clipboard.writeText(code);
        copiado = code;
        setTimeout(() => (copiado = ''), 2000);
    }

    function situacao(c: Convite): string {
        if (c.used_at) return `Usado em ${new Date(c.used_at).toLocaleDateString('pt-BR')}`;
        if (c.expires_at && new Date(c.expires_at) < new Date()) return 'Vencido';
        if (c.expires_at) return `Vale até ${new Date(c.expires_at).toLocaleDateString('pt-BR')}`;
        return 'Disponível';
    }

    function disponivel(c: Convite): boolean {
        return !c.used_at && (!c.expires_at || new Date(c.expires_at) >= new Date());
    }

    onMount(carregar);
</script>

<div class="max-w-2xl mx-auto p-6 space-y-6">
    <header>
        <h1 class="text-2xl font-extrabold text-neutral-800 dark:text-neutral-100">Convites</h1>
        <p class="text-sm text-neutral-500 dark:text-neutral-400 mt-1">
            O cadastro é fechado: só cria conta quem receber um código seu. Cada código vale
            uma vez e vence em 7 dias.
        </p>
    </header>

    {#if erro}
        <div class="bg-red-50 text-red-600 p-3 rounded-lg text-sm border border-red-100 dark:bg-red-900/20 dark:border-red-800/50">
            {erro}
        </div>
    {/if}

    <button
        on:click={gerar}
        disabled={gerando}
        class="w-full py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-lg shadow-md transition-all active:scale-[0.98] disabled:opacity-70"
    >
        {gerando ? 'Gerando...' : 'Gerar novo convite'}
    </button>

    {#if carregando}
        <p class="text-sm text-neutral-500 dark:text-neutral-400">Carregando...</p>
    {:else if convites.length === 0}
        <p class="text-sm text-neutral-500 dark:text-neutral-400">Nenhum convite gerado ainda.</p>
    {:else}
        <ul class="space-y-2">
            {#each convites as convite (convite.code)}
                <li class="flex items-center justify-between gap-3 p-4 rounded-xl bg-neutral-50 dark:bg-neutral-800/50 border border-neutral-200 dark:border-neutral-700">
                    <div class="min-w-0">
                        <p class="font-mono text-sm text-neutral-800 dark:text-neutral-100 truncate">{convite.code}</p>
                        <p class="text-xs text-neutral-500 dark:text-neutral-400 mt-0.5">{situacao(convite)}</p>
                    </div>
                    {#if disponivel(convite)}
                        <button
                            on:click={() => copiar(convite.code)}
                            class="shrink-0 px-4 py-2 rounded-xl border border-neutral-200 dark:border-neutral-700 text-sm font-semibold text-neutral-600 dark:text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-700 transition-colors"
                        >
                            {copiado === convite.code ? 'Copiado' : 'Copiar'}
                        </button>
                    {/if}
                </li>
            {/each}
        </ul>
    {/if}
</div>
