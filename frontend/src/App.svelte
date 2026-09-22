<script>
    import WebGLRadar from './lib/components/WebGLRadar.svelte';
    import ThreatFeed from './lib/components/ThreatFeed.svelte';
    import DoppelrandCard from './lib/components/DoppelrandCard.svelte';
    import TacticalButton from './lib/components/TacticalButton.svelte';

    let dummyItems = [
        { id: 1, district: 'PATNA', state: 'BIHAR', score: 82.5 },
        { id: 2, district: 'LUCKNOW', state: 'UTTAR PRADESH', score: 45.0 }
    ];
</script>

<div class="noise-overlay"></div>
<div class="scanlines"></div>

<main class="relative z-10 w-full min-h-screen p-4 text-white selection:bg-aviation selection:text-white flex gap-4 pointer-events-none">
    
    <!-- UI Layer -->
    <div class="w-96 pointer-events-auto">
        <ThreatFeed items={dummyItems} />
    </div>

    <!-- Map Layer -->
    <div class="flex-1 rounded border border-white/10 relative overflow-hidden pointer-events-auto">
        <WebGLRadar />
    </div>

</main>
