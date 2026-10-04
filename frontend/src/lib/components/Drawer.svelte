<script>
    import { onMount } from 'svelte';
    import TacticalButton from './TacticalButton.svelte';

    let { sampleId, onClose } = $props();

    let sample = $state(null);
    let loading = $state(true);
    let error = $state(null);

    $effect(() => {
        if (!sampleId) return;
        loading = true;
        error = null;
        
        fetch(`/api/samples/${sampleId}`)
            .then(r => r.ok ? r.json() : Promise.reject('Not found'))
            .catch(() => 
                // Fallback: find in baked samples.json
                fetch(`${import.meta.env.BASE_URL}samples.json`)
                    .then(r => r.json())
                    .then(all => {
                        const found = all.find(s => s.id === sampleId);
                        if (!found) throw new Error('Sample not found');
                        // Need to fetch details for this sample
                        return fetch(`/api/samples/${sampleId}`).then(r => r.json()).catch(() => found);
                    })
            )
            .then(data => { sample = data; })
            .catch(e => { error = String(e); })
            .finally(() => { loading = false; });
    });

    function formatDate(dateStr) {
        if (!dateStr) return 'Unknown';
        const d = new Date(dateStr);
        return d.toLocaleDateString('en-IN', { 
            year: 'numeric', month: 'short', day: 'numeric', 
            hour: '2-digit', minute: '2-digit' 
        }) + ' IST';
    }

    function getSeverity(parameter_key, value) {
        // Simplified severity calculation based on BIS limits
        const limits = {
            'arsenic': 0.01,
            'fluoride': 1.0,
            'iron': 1.0,
            'nitrate': 45,
            'tds': 500,
            'turbidity': 1,
            'ph': 8.5,
            'e_coli': 0,
            'total_coliform': 0
        };
        const limit = limits[parameter_key.toLowerCase()];
        if (!limit || value === null || value === undefined) return 0;
        if (parameter_key.toLowerCase() === 'ph') {
            return Math.max(0, Math.min(1, Math.abs(value - 7.5) / 2.5));
        }
        if (parameter_key.toLowerCase() === 'e_coli' || parameter_key.toLowerCase() === 'total_coliform') {
            return value > 0 ? 1 : 0;
        }
        return Math.min(1, value / limit);
    }
</script>

{#if sampleId}
    <div 
        class="fixed inset-0 z-50 flex items-end md:items-center justify-end"
        role="dialog"
        aria-modal="true"
        aria-labelledby="drawer-title"
    >
        <!-- Backdrop -->
        <div 
            class="fixed inset-0 bg-crt/80 backdrop-blur-sm"
            onclick={onClose}
            aria-hidden="true"
        ></div>

        <!-- Drawer Panel -->
        <div class="relative w-full md:w-[480px] lg:w-[520px] max-h-[90vh] overflow-y-auto bg-grid border-l border-phosphor/30 animate-[slideInRight_0.3s_ease_out]">
            <header class="flex items-center justify-between p-4 border-b border-phosphor/30 sticky top-0 bg-grid/95 backdrop-blur-sm z-10">
                <h2 id="drawer-title" class="text-lg font-bold uppercase tracking-tight">
                    {sample ? `Sample ${sample.id}` : 'Sample Details'}
                </h2>
                <button 
                    onclick={onClose}
                    class="p-1 text-phosphor/60 hover:text-phosphor hover:bg-phosphor/10 transition-colors"
                    aria-label="Close drawer"
                >
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                        <path d="M18 6L6 18M6 6l12 12"></path>
                    </svg>
                </button>
            </header>

            <div class="p-4 space-y-6">
                {#if loading}
                    <div class="flex items-center justify-center h-64">
                        <div class="text-phosphor/60 font-mono">Loading telemetry<span class="cursor-blink">_</span></div>
                    </div>
                {:else if error}
                    <div class="text-aviation text-center py-8">
                        <div class="text-lg font-bold mb-2">[ ERROR ]</div>
                        <div class="text-phosphor/60">{error}</div>
                        <button onclick={onClose} class="tactical-btn mt-4">Close</button>
                    </div>
                {:else if sample}
                    <div class="flex items-center gap-4">
                        <div class="text-3xl font-bold text-aviation font-mono tabular-nums">{sample.id}</div>
                        <span class="text-[10px] uppercase tracking-widest text-phosphor/50 border border-phosphor/30 px-2 py-1">
                            {sample.risk_score ? 'Live Telemetry' : 'Cached'}
                        </span>
                    </div>

                    <hr class="border-phosphor/20" />

                    <div class="grid gap-4">
                        <div>
                            <div class="text-[10px] uppercase tracking-widest text-phosphor/50 mb-1">District / Village</div>
                            <div class="font-bold text-white/90 uppercase">
                                {sample.district}, {sample.state} / {sample.village}
                            </div>
                        </div>
                        <div>
                            <div class="text-[10px] uppercase tracking-widest text-phosphor/50 mb-1">Collection Date</div>
                            <div class="font-mono text-white/70 text-sm">{formatDate(sample.collected_on)}</div>
                        </div>
                        <div>
                            <div class="text-[10px] uppercase tracking-widest text-phosphor/50 mb-1">WQMIS Reference</div>
                            <div class="font-mono text-white/70 text-sm">{sample.wqmis_ref || 'N/A'}</div>
                        </div>
                        {#if sample.risk_score}
                            <div>
                                <div class="text-[10px] uppercase tracking-widest text-phosphor/50 mb-1">Risk Band</div>
                                <div class="inline-flex items-center gap-2">
                                    <span class="text-2xl font-bold text-aviation font-mono tabular-nums">{sample.risk_score.score.toFixed(1)}</span>
                                    <span class="text-[10px] uppercase tracking-widest font-bold text-aviation border border-aviation px-2 py-0.5">{sample.risk_score.band}</span>
                                </div>
                            </div>
                        {/if}
                    </div>

                    <hr class="border-phosphor/20" />

                    <div>
                        <div class="text-[10px] uppercase tracking-widest text-phosphor/50 mb-3">
                            Scored Parameters ({sample.readings?.length || 0})
                        </div>
                        <div class="space-y-3">
                            {#each sample.readings as reading}
                                {@const sev = getSeverity(reading.parameter_key, reading.value)}
                                {@const bandColor = sev > 0.75 ? 'text-aviation' : sev > 0.5 ? 'text-amber-400' : sev > 0.25 ? 'text-yellow-400' : 'text-green-400'}
                                <div class="grid grid-cols-12 gap-3 p-3 bg-crt/50 border border-phosphor/10">
                                    <div class="col-span-4 text-white/70 uppercase text-xs tracking-wide">{reading.parameter_key}</div>
                                    <div class="col-span-3 font-mono {bandColor} tabular-nums">
                                        {reading.value !== null && reading.value !== undefined ? reading.value.toLocaleString() : '—'}
                                        {reading.unit ? ` ${reading.unit}` : ''}
                                    </div>
                                    <div class="col-span-3 font-mono text-white/50 tabular-nums">
                                        {reading.parameter_key === 'ph' ? 'BIS: 6.5-8.5' : reading.parameter_key === 'e_coli' || reading.parameter_key === 'total_coliform' ? 'BIS: 0' : 'BIS: See limits'}
                                    </div>
                                    <div class="col-span-2 text-right font-bold {bandColor}">Sev: {sev.toFixed(2)}</div>
                                </div>
                            {/each}
                        </div>
                    </div>

                    <hr class="border-phosphor/20" />

                    <div class="flex gap-3">
                        <TacticalButton 
                            variant="primary" 
                            class="flex-1"
                            onClick={() => { 
                                const blob = new Blob([JSON.stringify(sample, null, 2)], {type: 'application/json'});
                                const url = URL.createObjectURL(blob);
                                const a = document.createElement('a');
                                a.href = url;
                                a.download = `sample-${sample.id}.json`;
                                a.click();
                                URL.revokeObjectURL(url);
                            }}
                        >
                            Export JSON
                        </TacticalButton>
                        <TacticalButton 
                            variant="secondary" 
                            class="flex-1"
                            onClick={onClose}
                        >
                            Close
                        </TacticalButton>
                    </div>
                {/if}
            </div>
        </div>
    </div>
{/if}

<style>
    @keyframes slideInRight {
        from {
            opacity: 0;
            transform: translateX(100%);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
</style>