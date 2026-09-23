<script>
    import { onMount } from 'svelte';
    import WebGLRadar from './lib/components/WebGLRadar.svelte';
    import ThreatFeed from './lib/components/ThreatFeed.svelte';
    import Landing from './lib/pages/Landing.svelte';
    import Methodology from './lib/pages/Methodology.svelte';
    import Findings from './lib/pages/Findings.svelte';

    let currentPage = 'home'; // home, radar, methodology, findings

    function navigate(page) {
        if (document.startViewTransition) {
            document.startViewTransition(() => {
                currentPage = page;
            });
        } else {
            currentPage = page;
        }
    }

    let feedItems = [
        // Dummy items shown briefly until the API loads
        { id: 1, district: 'CONNECTING...', state: 'SYSTEM', score: 0.0 }
    ];

    onMount(() => {
        const handleDataLoaded = (e) => {
            if (e.detail && e.detail.priority) {
                feedItems = e.detail.priority;
            }
        };
        window.addEventListener('triage-data-loaded', handleDataLoaded);
        return () => window.removeEventListener('triage-data-loaded', handleDataLoaded);
    });
</script>

<div class="noise-overlay"></div>
<div class="scanlines"></div>

{#if currentPage === 'home'}
    <Landing {navigate} />
{:else if currentPage === 'methodology'}
    <Methodology {navigate} />
{:else if currentPage === 'findings'}
    <Findings {navigate} />
{:else if currentPage === 'radar'}
    <main class="relative z-10 w-full min-h-screen p-4 text-white selection:bg-aviation selection:text-white flex flex-col pointer-events-none">
        
        <header class="w-full flex justify-between items-end mb-4 relative z-10 pb-2 pointer-events-auto">
            <div><h1 class="text-2xl font-bold tracking-tighter uppercase">Command Center</h1></div>
            <div class="absolute -top-1 right-0"><button on:click={() => navigate('home')} class="border border-white/20 bg-white/5 text-xs py-1 px-4 uppercase hover:bg-white/10 cursor-pointer">Return</button></div>
        </header>

        <div class="flex flex-1 gap-4 overflow-hidden">
            <div class="w-96 pointer-events-auto h-full">
                <ThreatFeed items={feedItems} />
            </div>
            <div class="flex-1 rounded border border-white/10 relative overflow-hidden pointer-events-auto h-full">
                <WebGLRadar />
            </div>
        </div>
    </main>
{/if}

<style>
    /* View Transitions for SPA routing */
    ::view-transition-old(root) { animation: 0.4s ease-in both fade-out; }
    ::view-transition-new(root) { animation: 0.6s cubic-bezier(0.32,0.72,0,1) both slide-fade-in; }
    @keyframes fade-out { to { opacity: 0; } }
    @keyframes slide-fade-in { from { opacity: 0; transform: translateY(20px); } }
</style>
