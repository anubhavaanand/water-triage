<script>
    import TacticalButton from '../components/TacticalButton.svelte';
    import Drawer from '../components/Drawer.svelte';
    
    let { navigate } = $props();
    let items = $state([]);
    let loading = $state(true);
    let selectedSampleId = $state(null);

    $effect(() => {
        fetch('http://localhost:8000/api/priority/top/100')
            .then(r => r.json())
            .then(data => {
                items = data;
                loading = false;
            })
            .catch(err => {
                console.error(err);
                loading = false;
            });
    });

    function openDrawer(id) {
        selectedSampleId = id;
    }
</script>

<header class="w-full flex justify-between items-end mb-8 relative z-10 border-b border-white/10 pb-4 max-w-6xl mx-auto mt-8">
    <div><h1 class="text-3xl md:text-5xl font-bold tracking-tighter uppercase">Priority Queue</h1></div>
    <div class="absolute -top-4 right-0"><TacticalButton label="RETURN TO HUB" onClick={() => navigate('home')} /></div>
</header>

<main class="flex-1 max-w-6xl mx-auto w-full relative z-10 animate-[fadeUpAnim_0.8s_cubic-bezier(0.32,0.72,0,1)_forwards]">
    {#if loading}
        <div class="text-white/50 text-center mt-20 uppercase tracking-widest text-xs">Initializing queue...</div>
    {:else}
        <div class="border border-white/10 bg-white/5 overflow-hidden">
            <div class="grid grid-cols-12 gap-4 p-4 border-b border-white/10 text-xs font-bold uppercase tracking-widest text-white/50">
                <div class="col-span-1">Rank</div>
                <div class="col-span-3">Location</div>
                <div class="col-span-3">Coverage</div>
                <div class="col-span-2">Worst Param</div>
                <div class="col-span-2 text-right">Score</div>
                <div class="col-span-1 text-right">Band</div>
            </div>
            
            <div class="max-h-[70vh] overflow-y-auto">
                {#each items as item}
                    <button 
                        class="w-full text-left grid grid-cols-12 gap-4 p-4 border-b border-white/5 hover:bg-white/10 transition-colors cursor-pointer items-center group"
                        onclick={() => openDrawer(item.sample_id)}
                    >
                        <div class="col-span-1 font-mono text-white/70">#{item.rank}</div>
                        <div class="col-span-3">
                            <div class="font-bold uppercase truncate">{item.district}</div>
                            <div class="text-[10px] text-white/50 truncate uppercase">{item.village !== 'Not available' ? item.village : item.state}</div>
                        </div>
                        <div class="col-span-3">
                            <span class="inline-block bg-white/10 border border-white/20 rounded px-2 py-0.5 text-[9px] text-white/70 uppercase tracking-widest font-mono group-hover:bg-white/20 transition-colors">
                                {item.n_scored_params} of 8 scored parameters
                            </span>
                        </div>
                        <div class="col-span-2 uppercase text-xs font-bold {item.worst_parameter ? 'text-white/80' : 'text-white/30'}">
                            {item.worst_parameter ? item.worst_parameter.replace('_', ' ') : 'N/A'}
                        </div>
                        <div class="col-span-2 text-right font-mono text-lg {item.band === 'Critical' ? 'text-aviation font-bold' : 'text-white/80'}">
                            {item.score.toFixed(1)}
                        </div>
                        <div class="col-span-1 text-right">
                            <span class="text-[10px] uppercase font-bold px-1.5 py-0.5 rounded border {item.band === 'Critical' ? 'border-aviation text-aviation' : item.band === 'High' ? 'border-orange-500 text-orange-500' : 'border-white/20 text-white/50'}">
                                {item.band}
                            </span>
                        </div>
                    </button>
                {/each}
            </div>
        </div>
    {/if}
</main>

<Drawer sampleId={selectedSampleId} onClose={() => selectedSampleId = null} />
