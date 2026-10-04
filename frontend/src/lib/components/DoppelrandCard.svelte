<script>
    let { children, extraClass = '', className = '' } = $props();
</script>

<div 
    class="
        relative
        border border-phosphor/30
        bg-grid/50
        p-4 md:p-6
        {extraClass}
        {className}
    "
    role="region"
>
    {@render children()}
</div>