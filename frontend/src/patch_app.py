import re

with open('App.svelte', 'r') as f:
    content = f.read()

imports = """
  import ValidationTab from './lib/components/ValidationTab.svelte';
  import OverviewTab from './lib/pages/Overview.svelte';
  import MethodologyTab from './lib/pages/Methodology.svelte';
"""
content = content.replace("  import ValidationTab from './lib/components/ValidationTab.svelte';", imports)

tabs = """
      <button class="tab-btn" class:active={activeTab === 'a'} on:click={() => setTab('a')}>Variant A: Priority Queue</button>
      <button class="tab-btn" class:active={activeTab === 'b'} on:click={() => setTab('b')}>Variant B: Map + Cards</button>
      <button class="tab-btn" class:active={activeTab === 'c'} on:click={() => setTab('c')}>Variant C: District Split</button>
      <button class="tab-btn" class:active={activeTab === 'd'} on:click={() => setTab('d')}>Variant D: External Validation</button>
      <button class="tab-btn" class:active={activeTab === 'e'} on:click={() => setTab('e')}>Variant E: Overview</button>
      <button class="tab-btn" class:active={activeTab === 'f'} on:click={() => setTab('f')}>Variant F: Methodology</button>
"""
content = re.sub(r'<button class="tab-btn".*?Variant D: External Validation</button>', tabs.strip(), content, flags=re.DOTALL)

panels = """
      {#if activeTab === 'd'}
        <ValidationTab />
      {/if}
      {#if activeTab === 'e'}
        <OverviewTab navigate={setTab} />
      {/if}
      {#if activeTab === 'f'}
        <MethodologyTab navigate={setTab} />
      {/if}
"""
content = re.sub(r'\{#if activeTab === \'d\'\}.*?\{/if\}', panels.strip(), content, flags=re.DOTALL)

with open('App.svelte', 'w') as f:
    f.write(content)
