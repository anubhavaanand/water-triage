<script>
    import DoppelrandCard from '../components/DoppelrandCard.svelte';
    import TacticalButton from '../components/TacticalButton.svelte';
    export let navigate; // function to change page
</script>

<main class="flex flex-col justify-center max-w-7xl mx-auto w-full relative z-10 py-24 animate-[fadeUpAnim_0.8s_cubic-bezier(0.32,0.72,0,1)_forwards]">
    <div class="grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
        
        <div class="flex flex-col gap-6">
            <div class="text-[10px] text-aviation uppercase tracking-[0.2em] font-bold flex items-center gap-2">
                <span class="w-2 h-2 rounded-full bg-aviation animate-pulse"></span>
                Terminal // Access Granted
            </div>
            
            <h1 class="text-5xl md:text-7xl font-bold tracking-tighter uppercase leading-none">
                Water<br><span class="text-white/40">Triage</span>
            </h1>
            
            <p class="text-white/60 max-w-[45ch] text-sm md:text-base leading-relaxed">
                A data-driven water quality risk scoring and intervention prioritization system for Uttar Pradesh and Bihar. Analyzing <span class="text-white font-bold">1,741</span> historical samples and fetching live geospatial telemetry.
            </p>

            <div class="flex gap-4 mt-4">
                <TacticalButton label="LAUNCH RADAR" icon="↘" onClick={() => navigate('radar')} />
            </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            
            <button on:click={() => navigate('methodology')} class="text-left group cursor-pointer block h-48 border-none bg-transparent p-0">
                <DoppelrandCard extraClass="h-full transition-colors duration-500 group-hover:bg-white/5">
                    <div class="flex flex-col justify-between h-full">
                        <div class="text-xs uppercase tracking-widest text-white/40 group-hover:text-white/80 transition-colors">01 // Architecture</div>
                        <div>
                            <h3 class="text-xl font-bold mb-2">Methodology</h3>
                            <p class="text-[10px] text-white/50">BIS IS 10500 Scoring Model</p>
                        </div>
                    </div>
                </DoppelrandCard>
            </button>

            <button on:click={() => navigate('findings')} class="text-left group cursor-pointer block h-48 border-none bg-transparent p-0">
                <DoppelrandCard extraClass="h-full transition-colors duration-500 group-hover:bg-white/5">
                    <div class="flex flex-col justify-between h-full">
                        <div class="text-xs uppercase tracking-widest text-white/40 group-hover:text-white/80 transition-colors">02 // Analytics</div>
                        <div>
                            <h3 class="text-xl font-bold mb-2">Findings</h3>
                            <p class="text-[10px] text-white/50">Canonical State Matrix</p>
                        </div>
                    </div>
                </DoppelrandCard>
            </button>
            
            <div class="md:col-span-2 h-32">
                <DoppelrandCard extraClass="h-full bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAiIGhlaWdodD0iMjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGNpcmNsZSBjeD0iMSIgY3k9IjEiIHI9IjEiIGZpbGw9InJnYmEoMjU1LDI1NSwyNTUsMC4wNSkiLz48L3N2Zz4=')]">
                    <div class="flex justify-between items-center h-full">
                        <div>
                            <h4 class="text-sm font-bold text-white/80">PROJECT MAINTAINER</h4>
                            <p class="text-xs text-aviation mt-1">Anubhav Anand (A41105223039)</p>
                        </div>
                        <div class="text-right">
                            <h4 class="text-sm font-bold text-white/80">FACULTY GUIDE</h4>
                            <p class="text-xs text-aviation mt-1">Dr. Girish Paliwal</p>
                        </div>
                    </div>
                </DoppelrandCard>
            </div>
        </div>
    </div>
</main>
