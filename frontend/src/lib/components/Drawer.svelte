<script>
    let { sampleId, onClose } = $props();
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
        <div class="relative w-full md:w-[480px] lg:w-[520px] max-h-[90vh] overflow-y-auto bg-grid border-l border-phosphor/30 animate-[slideInRight_0.3s_ease-out]">
            <header class="flex items-center justify-between p-4 border-b border-phosphor/30 sticky top-0 bg-grid/95 backdrop-blur-sm z-10">
                <h2 id="drawer-title" class="text-lg font-bold uppercase tracking-tight">Sample Details</h2>
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
                <div class="flex items-center gap-4">
                    <div class="text-3xl font-bold text-aviation font-mono tabular-nums">{sampleId}</div>
                    <span class="text-[10px] uppercase tracking-widest text-phosphor/50 border border-phosphor/30 px-2 py-1">Live Telemetry</span>
                </div>

                <hr class="border-phosphor/20" />

                <div class="grid gap-4">
                    <div>
                        <div class="text-[10px] uppercase tracking-widest text-phosphor/50 mb-1">District / Village</div>
                        <div class="font-bold text-white/90 uppercase">Katihar, Bihar / Azamnagar</div>
                    </div>
                    <div>
                        <div class="text-[10px] uppercase tracking-widest text-phosphor/50 mb-1">Coordinates</div>
                        <div class="font-mono text-white/70 text-sm">25.5333° N, 87.5667° E</div>
                    </div>
                    <div>
                        <div class="text-[10px] uppercase tracking-widest text-phosphor/50 mb-1">Collection Date</div>
                        <div class="font-mono text-white/70 text-sm">2024-03-15 08:42 IST</div>
                    </div>
                    <div>
                        <div class="text-[10px] uppercase tracking-widest text-phosphor/50 mb-1">Risk Band</div>
                        <div class="inline-flex items-center gap-2">
                            <span class="text-2xl font-bold text-aviation font-mono tabular-nums">82.4</span>
                            <span class="text-[10px] uppercase tracking-widest font-bold text-aviation border border-aviation px-2 py-0.5">Critical</span>
                        </div>
                    </div>
                </div>

                <hr class="border-phosphor/20" />

                <div>
                    <div class="text-[10px] uppercase tracking-widest text-phosphor/50 mb-3">Scored Parameters (8/8)</div>
                    <div class="space-y-3">
                        <div class="grid grid-cols-12 gap-3 p-3 bg-crt/50 border border-phosphor/10">
                            <div class="col-span-4 text-white/70 uppercase text-xs tracking-wide">Iron (Fe)</div>
                            <div class="col-span-3 font-mono text-aviation tabular-nums">3.42 mg/L</div>
                            <div class="col-span-3 font-mono text-white/50 tabular-nums">BIS: 1.0</div>
                            <div class="col-span-2 text-right font-bold text-aviation">Sev: 0.94</div>
                        </div>
                        <div class="grid grid-cols-12 gap-3 p-3 bg-crt/50 border border-phosphor/10">
                            <div class="col-span-4 text-white/70 uppercase text-xs tracking-wide">Fluoride (F)</div>
                            <div class="col-span-3 font-mono text-white/80 tabular-nums">1.8 mg/L</div>
                            <div class="col-span-3 font-mono text-white/50 tabular-nums">BIS: 1.0</div>
                            <div class="col-span-2 text-right font-bold text-white/80">Sev: 0.45</div>
                        </div>
                        <div class="grid grid-cols-12 gap-3 p-3 bg-crt/50 border border-phosphor/10">
                            <div class="col-span-4 text-white/70 uppercase text-xs tracking-wide">Turbidity</div>
                            <div class="col-span-3 font-mono text-white/80 tabular-nums">12 NTU</div>
                            <div class="col-span-3 font-mono text-white/50 tabular-nums">BIS: 1.0</div>
                            <div class="col-span-2 text-right font-bold text-white/80">Sev: 0.38</div>
                        </div>
                        <div class="grid grid-cols-12 gap-3 p-3 bg-crt/50 border border-phosphor/10">
                            <div class="col-span-4 text-white/70 uppercase text-xs tracking-wide">TDS</div>
                            <div class="col-span-3 font-mono text-white/80 tabular-nums">890 mg/L</div>
                            <div class="col-span-3 font-mono text-white/50 tabular-nums">BIS: 500</div>
                            <div class="col-span-2 text-right font-bold text-white/80">Sev: 0.32</div>
                        </div>
                        <div class="grid grid-cols-12 gap-3 p-3 bg-crt/50 border border-phosphor/10">
                            <div class="col-span-4 text-white/70 uppercase text-xs tracking-wide">pH</div>
                            <div class="col-span-3 font-mono text-white/80 tabular-nums">7.2</div>
                            <div class="col-span-3 font-mono text-white/50 tabular-nums">BIS: 6.5-8.5</div>
                            <div class="col-span-2 text-right font-bold text-white/50">Sev: 0.08</div>
                        </div>
                        <div class="grid grid-cols-12 gap-3 p-3 bg-crt/50 border border-phosphor/10">
                            <div class="col-span-4 text-white/70 uppercase text-xs tracking-wide">Nitrate (NO3)</div>
                            <div class="col-span-3 font-mono text-white/80 tabular-nums">18 mg/L</div>
                            <div class="col-span-3 font-mono text-white/50 tabular-nums">BIS: 45</div>
                            <div class="col-span-2 text-right font-bold text-white/50">Sev: 0.12</div>
                        </div>
                        <div class="grid grid-cols-12 gap-3 p-3 bg-crt/50 border border-phosphor/10">
                            <div class="col-span-4 text-white/70 uppercase text-xs tracking-wide">Arsenic (As)</div>
                            <div class="col-span-3 font-mono text-white/80 tabular-nums">0.002 mg/L</div>
                            <div class="col-span-3 font-mono text-white/50 tabular-nums">BIS: 0.01</div>
                            <div class="col-span-2 text-right font-bold text-white/50">Sev: 0.04</div>
                        </div>
                        <div class="grid grid-cols-12 gap-3 p-3 bg-crt/50 border border-phosphor/10">
                            <div class="col-span-4 text-white/70 uppercase text-xs tracking-wide">E. coli</div>
                            <div class="col-span-3 font-mono text-white/80 tabular-nums">Negative</div>
                            <div class="col-span-3 font-mono text-white/50 tabular-nums">BIS: 0</div>
                            <div class="col-span-2 text-right font-bold text-white/50">Sev: 0.00</div>
                        </div>
                    </div>
                </div>

                <hr class="border-phosphor/20" />

                <div class="flex gap-3">
                    <TacticalButton 
                        variant="primary" 
                        class="flex-1"
                        onClick={() => { /* export action */ }}
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