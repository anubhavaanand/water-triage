<script>
    export let href = null;
    export let onClick = null;
    export let label = "ACTION";
    export let icon = "→";
    export let variant = "primary"; // primary or alert
    
    $: bgBase = variant === 'alert' ? 'bg-aviation/10' : 'bg-white/5';
    $: borderBase = variant === 'alert' ? 'border-aviation/30' : 'border-white/20';
    $: textBase = variant === 'alert' ? 'text-aviation' : 'text-[#EAEAEA]';
    $: bgHover = variant === 'alert' ? 'group-hover:bg-aviation/20' : 'group-hover:bg-white/10';
    $: iconBg = variant === 'alert' ? 'bg-aviation/20' : 'bg-white/10';
    $: iconHover = variant === 'alert' ? 'group-hover:bg-aviation/30' : 'group-hover:bg-white/20';
</script>

<svelte:element this={href ? 'a' : 'button'} 
    href={href} 
    on:click={onClick}
    class="group inline-flex items-center border {borderBase} {bgBase} {textBase} pl-6 pr-2 py-2 text-xs uppercase tracking-[0.1em] cursor-pointer transition-all duration-400 ease-[cubic-bezier(0.32,0.72,0,1)] hover:scale-[0.98] no-underline">
    
    <span class="font-bold relative">
        {label}
        <!-- Glitch effect could go here via a slot or class -->
    </span>
    
    <span class="flex items-center justify-center w-8 h-8 {iconBg} {iconHover} ml-4 transition-all duration-400 ease-[cubic-bezier(0.32,0.72,0,1)] group-hover:translate-x-1">
        {icon}
    </span>
</svelte:element>
