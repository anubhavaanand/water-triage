<script>
    import DoppelrandCard from './DoppelrandCard.svelte';
    export let items = []; // expects { id, district, state, score, parameters }
</script>

<DoppelrandCard title="Threat Intel Feed" extraClass="h-[calc(100vh-4rem)] w-96 flex-col">
    <div slot="header-right" class="text-xs text-white/50 animate-pulse flex items-center gap-2">
        <span class="w-1.5 h-1.5 rounded-full bg-aviation inline-block"></span>
        LIVE
    </div>
    
    <div class="overflow-y-auto h-full pr-2 space-y-2 pb-12 custom-scroll">
        {#each items as item (item.id)}
            <button 
                class="w-full text-left p-3 bg-white/5 border border-white/5 hover:bg-white/10 hover:border-white/20 transition-all cursor-pointer group"
                on:click={() => {/* dispatch select */}}
            >
                <div class="flex justify-between items-start mb-2">
                    <div>
                        <div class="text-sm font-bold text-white group-hover:text-aviation transition-colors">{item.district}</div>
                        <div class="text-[10px] text-white/40 uppercase">{item.state}</div>
                    </div>
                    <div class="text-xl font-bold {item.score >= 75 ? 'text-aviation' : 'text-orange-400'}">
                        {item.score}
                    </div>
                </div>
            </button>
        {/each}
        
        {#if items.length === 0}
            <div class="text-center text-white/30 text-xs py-8 uppercase tracking-widest">
                Waiting for telemetry...
            </div>
        {/if}
    </div>
</DoppelrandCard>

<style>
    .custom-scroll::-webkit-scrollbar { width: 4px; }
    .custom-scroll::-webkit-scrollbar-track { background: transparent; }
    .custom-scroll::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); }
</style>
