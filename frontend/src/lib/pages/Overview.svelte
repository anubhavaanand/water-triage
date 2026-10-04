<script>
    import TacticalButton from '../components/TacticalButton.svelte';
    import DoppelrandCard from '../components/DoppelrandCard.svelte';
    
    let { navigate } = $props();
    let meta = $state(null);
    let loading = $state(true);
    let error = $state(null);

    $effect(() => {
        fetch('http://localhost:8000/api/meta')
            .then(r => r.json())
            .then(data => {
                meta = data;
                loading = false;
            })
            .catch(err => {
                error = err.message;
                loading = false;
            });
    });
</script>

<header class="w-full flex justify-between items-end mb-12 relative z-10 border-b border-white/10 pb-4 max-w-6xl mx-auto mt-8">
    <div><h1 class="text-3xl md:text-5xl font-bold tracking-tighter uppercase">Overview</h1></div>
    <div class="absolute -top-4 right-0"><TacticalButton label="RETURN TO HUB" onClick={() => navigate('home')} /></div>
</header>

<main class="flex-1 max-w-6xl mx-auto w-full relative z-10 animate-[fadeUpAnim_0.8s_cubic-bezier(0.32,0.72,0,1)_forwards] flex flex-col gap-8">
    {#if loading}
        <div class="text-white/50 text-center uppercase tracking-widest text-xs">Initializing telemetry...</div>
    {:else if error}
        <div class="text-red-500 text-center uppercase tracking-widest text-xs">Error: {error}</div>
    {:else}
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
            <DoppelrandCard>
                <div class="text-center">
                    <div class="text-2xl font-bold">{meta.corpus.samples.toLocaleString()}</div>
                    <div class="text-[10px] text-white/50 uppercase">Scored Samples</div>
                </div>
            </DoppelrandCard>
            <DoppelrandCard>
                <div class="text-center">
                    <div class="text-2xl font-bold text-aviation">{meta.bands.Critical}</div>
                    <div class="text-[10px] text-white/50 uppercase">Critical (≥75)</div>
                </div>
            </DoppelrandCard>
            <DoppelrandCard>
                <div class="text-center">
                    <div class="text-2xl font-bold text-white/80">{meta.bands.High}</div>
                    <div class="text-[10px] text-white/50 uppercase">High (50-74)</div>
                </div>
            </DoppelrandCard>
            <DoppelrandCard>
                <div class="text-center">
                    <div class="text-2xl font-bold text-white/40">{meta.corpus.historical_events_distinct.toLocaleString()}</div>
                    <div class="text-[10px] text-white/50 uppercase">Historical Events</div>
                </div>
            </DoppelrandCard>
        </div>
        
        <div class="text-center mt-2 text-aviation/80 text-xs font-mono uppercase tracking-wide border border-aviation/20 bg-aviation/5 p-3 rounded">
            70 of 89 Critical samples are single-parameter iron results from one district
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-8 mt-8">
            {#each meta.state_comparison as stateData}
                <DoppelrandCard>
                    <h2 class="text-2xl font-bold mb-6 flex justify-between border-b border-white/10 pb-2">{stateData.state} <span class="text-white/40">N={stateData.samples}</span></h2>
                    <div class="space-y-6">
                        <div>
                            <div class="text-[10px] uppercase text-white/50 mb-1">Mean Composite Risk Score</div>
                            <div class="text-4xl font-bold {stateData.mean_crs > 15 ? 'text-aviation' : ''}">{stateData.mean_crs.toFixed(2)}</div>
                        </div>
                        <div>
                            <div class="text-[10px] uppercase text-white/50 mb-1">Critical Samples</div>
                            <div class="text-2xl font-bold">{stateData.critical_count}</div>
                            <p class="text-[10px] mt-1 text-white/40">{(stateData.critical_share_of_all_critical * 100).toFixed(1)}% of all critical samples.</p>
                        </div>
                    </div>
                </DoppelrandCard>
            {/each}
        </div>
    {/if}
</main>
