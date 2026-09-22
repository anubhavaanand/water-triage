<script>
    import TacticalButton from '../components/TacticalButton.svelte';
    import DoppelrandCard from '../components/DoppelrandCard.svelte';
    export let navigate;
</script>

<header class="w-full flex justify-between items-end mb-12 relative z-10 border-b border-white/10 pb-4 max-w-6xl mx-auto mt-8">
    <div><h1 class="text-3xl md:text-5xl font-bold tracking-tighter uppercase">Findings</h1></div>
    <div class="absolute -top-4 right-0"><TacticalButton label="RETURN TO HUB" onClick={() => navigate('home')} /></div>
</header>

<main class="flex-1 max-w-6xl mx-auto w-full relative z-10 animate-[fadeUpAnim_0.8s_cubic-bezier(0.32,0.72,0,1)_forwards] flex flex-col gap-8">
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <DoppelrandCard><div class="text-center"><div class="text-2xl font-bold">1,741</div><div class="text-[10px] text-white/50 uppercase">Scored Samples</div></div></DoppelrandCard>
        <DoppelrandCard><div class="text-center"><div class="text-2xl font-bold text-aviation">89</div><div class="text-[10px] text-white/50 uppercase">Critical (≥75)</div></div></DoppelrandCard>
        <DoppelrandCard><div class="text-center"><div class="text-2xl font-bold text-white/80">392</div><div class="text-[10px] text-white/50 uppercase">High (50-74)</div></div></DoppelrandCard>
        <DoppelrandCard><div class="text-center"><div class="text-2xl font-bold text-white/40">100,690</div><div class="text-[10px] text-white/50 uppercase">Historical Events</div></div></DoppelrandCard>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-8 mt-8">
        <DoppelrandCard>
            <h2 class="text-2xl font-bold mb-6 flex justify-between border-b border-white/10 pb-2">Uttar Pradesh <span class="text-white/40">N=966</span></h2>
            <div class="space-y-6">
                <div><div class="text-[10px] uppercase text-white/50 mb-1">Mean Composite Risk Score</div><div class="text-4xl font-bold">12.68</div></div>
                <div><div class="text-[10px] uppercase text-white/50 mb-1">Fluoride Max</div><div class="text-2xl font-bold text-aviation">12.60 mg/L</div><p class="text-[10px] mt-1 text-white/40">Strongest single finding in the corpus.</p></div>
            </div>
        </DoppelrandCard>
        <DoppelrandCard>
            <h2 class="text-2xl font-bold mb-6 flex justify-between border-b border-white/10 pb-2">Bihar <span class="text-white/40">N=775</span></h2>
            <div class="space-y-6">
                <div><div class="text-[10px] uppercase text-white/50 mb-1">Mean Composite Risk Score</div><div class="text-4xl font-bold text-aviation">18.36</div><p class="text-[10px] mt-1 text-aviation/80">Significantly higher aggregate risk than UP.</p></div>
                <div><div class="text-[10px] uppercase text-white/50 mb-1">Chronic Historical Record</div><div class="text-2xl font-bold">Khokha (Purnia)</div><p class="text-[10px] mt-1 text-white/40">166 historical Iron events across 2009-2012.</p></div>
            </div>
        </DoppelrandCard>
    </div>
</main>
