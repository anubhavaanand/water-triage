<script>
    export let title = '';
    export let extraClass = '';
</script>

<div class="bg-white/5 border border-white/10 p-1 {extraClass}">
    <div class="bg-black/40 border border-white/5 h-full shadow-[inset_0_1px_1px_rgba(255,255,255,0.05)]">
        {#if title}
            <div class="border-b border-white/5 p-4 py-3 flex justify-between items-center">
                <h3 class="text-xs font-bold uppercase tracking-widest text-white/80">{title}</h3>
                <slot name="header-right"></slot>
            </div>
        {/if}
        <div class="p-4">
            <slot></slot>
        </div>
    </div>
</div>
