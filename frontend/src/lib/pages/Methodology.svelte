<script>
    import TacticalButton from '../components/TacticalButton.svelte';
    import DoppelrandCard from '../components/DoppelrandCard.svelte';
    export let navigate;
</script>

<header class="w-full flex justify-between items-end mb-12 relative z-10 border-b border-white/10 pb-4 max-w-5xl mx-auto mt-8">
    <div><h1 class="text-3xl md:text-5xl font-bold tracking-tighter uppercase">Methodology</h1></div>
    <div class="absolute -top-4 right-0"><TacticalButton label="RETURN TO HUB" onClick={() => navigate('home')} /></div>
</header>

<main class="flex-1 max-w-5xl mx-auto w-full relative z-10 animate-[fadeUpAnim_0.8s_cubic-bezier(0.32,0.72,0,1)_forwards]">
    <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div class="flex flex-col gap-6">
            <h2 class="text-xl font-bold text-aviation border-b border-white/10 pb-2">BIS IS 10500 Scoring Model</h2>
            <p class="text-sm text-white/70 leading-relaxed">The core algorithmic engine derives its severity model from the Bureau of Indian Standards (BIS IS 10500). Parameters are heavily weighted based on acute physiological hazard.</p>
            <DoppelrandCard>
                <ul class="text-sm space-y-3">
                    <li class="flex justify-between border-b border-white/5 pb-2"><span class="text-white/50">Arsenic</span> <span class="font-bold text-aviation">1.0</span></li>
                    <li class="flex justify-between border-b border-white/5 pb-2"><span class="text-white/50">E. coli</span> <span class="font-bold text-aviation">0.9</span></li>
                    <li class="flex justify-between border-b border-white/5 pb-2"><span class="text-white/50">Fluoride</span> <span class="font-bold text-white">0.8</span></li>
                    <li class="flex justify-between border-b border-white/5 pb-2"><span class="text-white/50">Nitrate</span> <span class="font-bold text-white">0.7</span></li>
                    <li class="flex justify-between border-b border-white/5 pb-2"><span class="text-white/50">Iron</span> <span class="font-bold text-white">0.4</span></li>
                    <li class="flex justify-between border-b border-white/5 pb-2"><span class="text-white/50">Turbidity / TDS</span> <span class="font-bold text-white/70">0.3</span></li>
                    <li class="flex justify-between"><span class="text-white/50">pH</span> <span class="font-bold text-white/70">0.2</span></li>
                </ul>
            </DoppelrandCard>
        </div>
        <div class="flex flex-col gap-6">
            <h2 class="text-xl font-bold text-white/80 border-b border-white/10 pb-2">Data Acquisition & Pipeline</h2>
            <p class="text-sm text-white/70 leading-relaxed">The backend relies on a highly-optimized, multi-threaded WQMIS crawler extracting live water quality laboratory reports across Uttar Pradesh and Bihar.</p>
            <DoppelrandCard extraClass="h-full">
                <div class="flex flex-col justify-center gap-4 text-center h-full">
                    <div class="text-3xl font-bold tracking-tighter">90,000+</div>
                    <div class="text-[10px] uppercase text-white/40 tracking-widest">Projected Sample Capacity</div>
                    <div class="w-full h-px bg-white/10 my-4 relative"><div class="absolute left-1/2 -translate-x-1/2 -top-2 bg-black px-2 text-[10px] text-aviation">ETL PIPELINE</div></div>
                    <div class="text-xs text-left text-white/60 space-y-2">
                        <p>▹ Continuous range enumeration across 1.5M IDs</p>
                        <p>▹ Exponential backoff & throttling protocols</p>
                        <p>▹ PostgreSQL district-level aggregation</p>
                    </div>
                </div>
            </DoppelrandCard>
        </div>
    </div>
</main>
