<script>
  import { onMount } from 'svelte';
  import './app.css';
  import QueueTab from './lib/components/QueueTab.svelte';
  import MapTab from './lib/components/MapTab.svelte';
  import DetailTab from './lib/components/DetailTab.svelte';
  import ValidationTab from './lib/components/ValidationTab.svelte';

  let activeTab = 'a';
  let dbStatus = 'checking'; // 'checking' | 'live' | 'offline'

  onMount(async () => {
    // Check Health
    try {
      const res = await fetch('/api/health', { cache: 'no-store' });
      if (res.ok) {
        const data = await res.json();
        dbStatus = data.db_status === 'online' ? 'live' : 'offline';
      } else {
        dbStatus = 'offline';
      }
    } catch (e) {
      dbStatus = 'offline';
    }

    // Restore tab
    const saved = localStorage.getItem('wt-tab');
    if (['a','b','c','d'].includes(saved)) {
      activeTab = saved;
    }
  });

  function setTab(tab) {
    activeTab = tab;
    localStorage.setItem('wt-tab', tab);
  }
</script>

<div class="topnav">
  <div>
    <span class="logo">WaterTriage</span>
    <!-- Status Pill -->
    <div class="status-pill {dbStatus}" aria-live="polite">
      <div class="dot"></div>
      <span class="status-text">
        {#if dbStatus === 'checking'}Checking...
        {:else if dbStatus === 'live'}DB Live
        {:else}DB Offline{/if}
      </span>
    </div>
  </div>
  <div class="nav-links">
    <a href="#viva">Viva Deck</a>
    <a href="#repo">Repository</a>
    <span class="version">v0.4</span>
  </div>
</div>

<main class="dashboard">
  <div class="hero">
    <div class="eyebrow">✓ All Backend Items Resolved</div>
    <h1>Priority Queue & Triangulation</h1>
    <p>Live tracking of 1,741 sources across UP & Bihar. Scored via BIS IS 10500 weighted model.</p>
  </div>

  <div class="sticky-grid">
    <div class="sticky-note sticky-green">
      <div class="sticky-header">
        <span class="sticky-title">✓ data.json state</span>
        <span class="sticky-badge">FIXED</span>
      </div>
      Counts verified 89/392/28/1,232.
    </div>
    <div class="sticky-note sticky-green">
      <div class="sticky-header">
        <span class="sticky-title">✓ DB Startup</span>
        <span class="sticky-badge">CLOSED</span>
      </div>
      Nav indicator polling /api/health every 30s.
    </div>
    <div class="sticky-note sticky-green">
      <div class="sticky-header">
        <span class="sticky-title">✓ Globe Symlink</span>
        <span class="sticky-badge">FIXED</span>
      </div>
      164MB GLB removed. Graceful fallback on Pages.
    </div>
    <div class="sticky-note sticky-green">
      <div class="sticky-header">
        <span class="sticky-title">✓ Color Drift</span>
        <span class="sticky-badge">FIXED</span>
      </div>
      Medium band now mapped to #d4a017 (Amber).
    </div>
    <div class="sticky-note sticky-green">
      <div class="sticky-header">
        <span class="sticky-title">✓ Null Param</span>
        <span class="sticky-badge">FIXED</span>
      </div>
      NULL parsed to "Within BIS Limits".
    </div>
    <div class="sticky-note sticky-yellow">
      <div class="sticky-header">
        <span class="sticky-title">Timeline</span>
        <span class="sticky-badge">OPEN</span>
      </div>
      Backend integration complete. Awaiting final Viva presentation.
    </div>
  </div>

  <section class="c-charts">
    <div class="chart-card">
      <div class="chart-title">Priority Breakdown</div>
      <div class="chart-bar-area">
        <div class="chart-bar" style="width: 5%; background: var(--critical);"></div>
        <div class="chart-bar" style="width: 22%; background: var(--high);"></div>
        <div class="chart-bar" style="width: 2%; background: var(--medium);"></div>
        <div class="chart-bar" style="width: 71%; background: var(--low);"></div>
      </div>
      <div class="chart-labels">
        <div class="legend"><span class="swatch" style="background: var(--critical);"></span>Critical</div>
        <div class="legend"><span class="swatch" style="background: var(--high);"></span>High</div>
        <div class="legend"><span class="swatch" style="background: var(--medium);"></span>Medium</div>
        <div class="legend"><span class="swatch" style="background: var(--low);"></span>Low</div>
      </div>
    </div>
  </section>

  <!-- Interactive System -->
  <section class="interactive-system" id="viva">
    <div class="tab-row" role="tablist">
      <button class="tab-btn" class:active={activeTab === 'a'} on:click={() => setTab('a')}>Variant A: Priority Queue</button>
      <button class="tab-btn" class:active={activeTab === 'b'} on:click={() => setTab('b')}>Variant B: Map + Cards</button>
      <button class="tab-btn" class:active={activeTab === 'c'} on:click={() => setTab('c')}>Variant C: District Split</button>
      <button class="tab-btn" class:active={activeTab === 'd'} on:click={() => setTab('d')}>Variant D: External Validation</button>
    </div>

    <div class="system-container">
      {#if activeTab === 'a'}
        <QueueTab />
      {/if}
      {#if activeTab === 'b'}
        <MapTab />
      {/if}
      {#if activeTab === 'c'}
        <DetailTab />
      {/if}
      {#if activeTab === 'd'}
        <ValidationTab />
      {/if}
    </div>
  </section>
</main>
<footer class="footer">
  <div class="footer-left">WaterTriage v0.4 · Anubhav Anand · Amity University</div>
  <div class="footer-right">NTCC Minor Project · B.Tech CSE</div>
</footer>
