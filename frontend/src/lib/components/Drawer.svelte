<script>
    import TacticalButton from './TacticalButton.svelte';
    
    let { sampleId, onClose } = $props();
    let sample = $state(null);
    let loading = $state(true);

    const LIMITS = {
        ph: { acceptable: 6.5, permissible: 8.5 },
        tds: { acceptable: 500.0, permissible: 2000.0 },
        fluoride: { acceptable: 1.0, permissible: 1.5 },
        arsenic: { acceptable: 0.01, permissible: 0.05 },
        nitrate: { acceptable: 45.0, permissible: 'None' },
        iron: { acceptable: 0.3, permissible: 'None' },
        turbidity: { acceptable: 1.0, permissible: 5.0 },
        e_coli: { acceptable: 0.0, permissible: 0.0 }
    };

    $effect(() => {
        if (sampleId) {
            loading = true;
            fetch(`http://localhost:8000/api/samples/${sampleId}`)
                .then(r => r.json())
                .then(data => {
                    sample = data;
                    loading = false;
                })
                .catch(err => {
                    console.error(err);
                    loading = false;
                });
        }
    });
</script>

{#if sampleId}
    <div class="fixed inset-0 z-50 flex justify-end">
        <!-- Backdrop -->
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" onclick={onClose} onkeydown={e => e.key === 'Escape' && onClose()} role="button" tabindex="0"></div>
        
        <!-- Panel -->
        <div class="relative w-full max-w-md h-full bg-[#0a0a0a] border-l border-white/10 p-6 flex flex-col shadow-2xl animate-[slideIn_0.3s_cubic-bezier(0.32,0.72,0,1)_forwards]">
            
            {#if loading}
                <div class="text-white/50 text-center mt-20 uppercase tracking-widest text-xs">Accessing record...</div>
            {:else if sample}
                <div class="flex justify-between items-start mb-8">
                    <div>
                        <div class="text-[10px] text-aviation uppercase tracking-widest mb-1">Sample ID {sample.id}</div>
                        <h2 class="text-2xl font-bold uppercase">{sample.district}</h2>
                        <div class="text-sm text-white/50">{sample.village !== 'Not available' ? sample.village : 'Unknown Village'}, {sample.state}</div>
                    </div>
                    <button onclick={onClose} class="text-white/50 hover:text-white uppercase text-xs tracking-widest cursor-pointer">Close ✕</button>
                </div>

                <div class="mb-6 flex items-center justify-between border-b border-white/10 pb-4">
                    <div>
                        <div class="text-[10px] uppercase text-white/50">Composite Risk</div>
                        <div class="text-3xl font-bold {sample.risk_score?.band === 'Critical' ? 'text-aviation' : 'text-white'}">
                            {sample.risk_score?.score.toFixed(2) || 'N/A'}
                        </div>
                    </div>
                    <div class="text-right">
                        <div class="text-[10px] uppercase text-white/50">Band</div>
                        <div class="text-lg font-bold uppercase {sample.risk_score?.band === 'Critical' ? 'text-aviation' : ''}">{sample.risk_score?.band || 'Unknown'}</div>
                    </div>
                </div>

                {#if sample.risk_score?.n_scored_params !== undefined}
                    <div class="mb-6 inline-block bg-white/5 border border-white/10 rounded px-2 py-1">
                        <span class="text-[10px] text-white/70 uppercase tracking-widest font-mono">
                            {sample.risk_score.n_scored_params} of 8 scored parameters
                        </span>
                    </div>
                {/if}

                <div class="flex-1 overflow-y-auto pr-2">
                    <h3 class="text-sm font-bold uppercase tracking-widest text-white/70 mb-4 border-b border-white/10 pb-2">Telemetry</h3>
                    
                    <div class="space-y-4">
                        {#each sample.readings as reading}
                            {@const limits = LIMITS[reading.parameter_key] || {}}
                            <div class="bg-white/5 border border-white/10 p-3 rounded flex flex-col gap-2">
                                <div class="flex justify-between items-center">
                                    <span class="font-bold uppercase text-sm">{reading.parameter_key.replace('_', ' ')}</span>
                                    <span class="font-mono text-lg {reading.value > limits.acceptable ? 'text-aviation' : 'text-white'}">
                                        {reading.value} <span class="text-xs text-white/50">{reading.unit || ''}</span>
                                    </span>
                                </div>
                                <div class="flex justify-between text-[10px] uppercase tracking-widest text-white/40 font-mono">
                                    <span>Acceptable: {limits.acceptable}</span>
                                    <span>Permissible: {limits.permissible}</span>
                                </div>
                            </div>
                        {/each}
                    </div>
                </div>
            {/if}
        </div>
    </div>
{/if}

<style>
    @keyframes slideIn {
        from { transform: translateX(100%); }
        to { transform: translateX(0); }
    }
</style>
