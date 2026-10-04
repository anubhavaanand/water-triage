<script>
    let { label = '', icon = '', onClick, variant = 'primary', disabled = false, className = '' } = $props();
</script>

<button
    onclick={onClick}
    disabled={disabled}
    class="
        inline-flex items-center gap-2
        px-4 py-2
        font-mono text-[11px] uppercase tracking-[0.1em] font-bold
        border border-solid
        transition-colors duration-50
        select-none
        disabled:opacity-30 disabled:cursor-not-allowed
        {className}
        {variant === 'primary' 
            ? 'bg-aviation text-crt text-[10px] hover:bg-aviation/80 hover:text-crt active:bg-aviation'
            : variant === 'secondary'
            ? 'bg-transparent text-phosphor border-phosphor/30 hover:bg-phosphor/10 hover:border-phosphor/50 active:bg-phosphor/20'
            : 'bg-transparent text-phosphor/60 border-transparent hover:text-phosphor hover:bg-phosphor/5 active:bg-phosphor/10'
        }
    "
    aria-disabled={disabled}
>
    {label}
    {#if icon}
        <span aria-hidden="true">{icon}</span>
    {/if}
</button>