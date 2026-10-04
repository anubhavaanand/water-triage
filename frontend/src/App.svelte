<script>
  import { onMount } from 'svelte';
  import './app.css';
  import QueueTab from './lib/components/QueueTab.svelte';
  import MapTab from './lib/components/MapTab.svelte';
  import DetailTab from './lib/components/DetailTab.svelte';
  import ValidationTab from './lib/components/ValidationTab.svelte';
  import OverviewTab from './lib/pages/Overview.svelte';
  import MethodologyTab from './lib/pages/Methodology.svelte';

  let activeTab = 'a';
  let dbStatus = 'checking'; // 'checking' | 'live' | 'offline'
  let theme = 'light';

  onMount(async () => {
    // Restore theme
    const savedTheme = localStorage.getItem('wt-theme');
    if (savedTheme) {
      theme = savedTheme;
      document.documentElement.setAttribute('data-theme', theme);
    }

    // Check Health
    async function checkHealth() {
      try {
        const res = await fetch('/api/health', { cache: 'no-store' });
        if (!res.ok) throw new Error('API unavailable');
        const data = await res.json();
        return data.status === 'healthy' ? 'live' : 'offline';
      } catch (e) {
        // Fallback to baked static health.json
        try {
          const res = await fetch(`${import.meta.env.BASE_URL}health.json`);
          const data = await res.json();
          return data.status === 'healthy' ? 'live' : 'offline';
        } catch (e2) {
          return 'offline';
        }
      }
    }
    
    dbStatus = await checkHealth();

    // Restore tab
    const saved = localStorage.getItem('wt-tab');
    if (['a','b','c','d', 'e', 'f'].includes(saved)) {
      activeTab = saved;
    }

    // Poll health every 30s
    const interval = setInterval(async () => {
      dbStatus = await checkHealth();
    }, 30000);

    return () => clearInterval(interval);
  });

  function setTab(tab) {
    activeTab = tab;
    localStorage.setItem('wt-tab', tab);
  }

  function toggleTheme() {
    theme = theme === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('wt-theme', theme);
  }
</script>

<div class="topnav" data-od-id="topnav">
  <div class="container topnav-inner">
    <span class="logo">WaterTriage</span>
    <!-- ── Health status indicator ── -->
    <span id="health-pill" class="status-pill {dbStatus}" role="status" aria-live="polite" aria-label="Database status: {dbStatus}">
      <span class="status-dot" aria-hidden="true"></span>
      <span id="health-label">
        {#if dbStatus === 'checking'}Checking…{:else if dbStatus === 'live'}DB Live{:else}DB Offline{/if}
      </span>
    </span>
    <!-- ── Dark mode toggle ── -->
    <button class="theme-toggle" id="theme-toggle" aria-label="Switch to {theme === 'light' ? 'dark' : 'light'} mode" onclick={toggleTheme}>
      <!-- moon = currently light mode → switch to dark -->
      <svg class="icon-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="M21 12.79A9 9 0 1 1 11.21 3a7 7 0 0 0 9.79 9.79z"/>
      </svg>
      <!-- sun = currently dark mode → switch to light -->
      <svg class="icon-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <circle cx="12" cy="12" r="5"/>
        <line x1="12" y1="1"  x2="12" y2="3"/>
        <line x1="12" y1="21" x2="12" y2="23"/>
        <line x1="4.22" y1="4.22"   x2="5.64" y2="5.64"/>
        <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
        <line x1="1"  y1="12" x2="3"  y2="12"/>
        <line x1="21" y1="12" x2="23" y2="12"/>
        <line x1="4.22" y1="19.78"  x2="5.64" y2="18.36"/>
        <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
      </svg>
    </button>

    <nav aria-label="Primary">
      <a href="#">Map View</a>
      <a href="#">Priority Queue</a>
      <a href="#">Registry</a>
      <a href="#">Drill-down</a>
    </nav>
    <button class="btn btn-primary">↓ Export CSV</button>
  </div>
</div>

<main id="content">
  <!-- ═══════════════════════════════════════════════════ HERO + TAB SWITCHER -->
  <section class="section hero" data-od-id="hero" style="padding-bottom: 0;">
    <div class="container">

      <!-- heading block -->
      <div style="max-width: 620px; margin-bottom: 44px;">
        <p class="eyebrow">v0.4 Wireframe · WaterTriage Dashboard · UP + Bihar · <span style="color: var(--color-low); letter-spacing: 0.06em;">✓ All Backend Items Resolved</span></p>
        <h1>Dashboard Layout Explorations</h1>
        <p class="lead" style="margin-top: 16px;">
          Three layout variants for the main risk-priority view — rough in on structure before committing pixels.
          Data: <strong>1,741 samples</strong> across <strong>47 districts</strong> (UP 28 / Bihar 19).
          Tap a tab to switch variants.
        </p>
        <!-- KPI strip -->
        <div style="display: flex; gap: 20px; flex-wrap: wrap; margin-top: 28px; padding: 16px 20px; border: 2px solid var(--color-fg); border-radius: 2px; background: var(--color-surface);">
          <span class="stat" style="min-width: 80px;">
            <span class="stat-num" style="color: var(--color-critical);">89</span>
            <span class="stat-label">Critical<br><span class="badge badge-critical">≥ 75</span></span>
          </span>
          <span class="stat" style="min-width: 80px;">
            <span class="stat-num" style="color: var(--color-high);">392</span>
            <span class="stat-label">High<br><span class="badge badge-high">50–74</span></span>
          </span>
          <span class="stat" style="min-width: 80px;">
            <span class="stat-num" style="color: var(--color-medium);">28</span>
            <span class="stat-label">Medium<br><span class="badge badge-medium">25–49</span></span>
          </span>
          <span class="stat" style="min-width: 80px;">
            <span class="stat-num" style="color: var(--color-low);">1,232</span>
            <span class="stat-label">Low<br><span class="badge badge-low">&lt; 25</span></span>
          </span>
        </div>
        <p class="callout" style="margin-top: 10px;">✓ FIXED — data.json rebuilt from live DB. Counts now match: 89/392/28/1,232. Pre-fix bake (106/653) is retired.</p>
      </div>

      <!-- ──── TAB SWITCHER ──── -->
      <div id="tab-system" aria-label="Layout variants">
        <div class="tab-row" role="tablist" aria-label="Dashboard layout variants">
          <button class="tab-btn" class:active={activeTab === 'a'} role="tab" aria-selected={activeTab === 'a'} aria-controls="tab-panel-a" id="tab-a" onclick={() => setTab('a')}>Variant A — Priority Queue (List)</button>
          <button class="tab-btn" class:active={activeTab === 'b'} role="tab" aria-selected={activeTab === 'b'} aria-controls="tab-panel-b" id="tab-b" onclick={() => setTab('b')}>Variant B — Map + Cards</button>
          <button class="tab-btn" class:active={activeTab === 'c'} role="tab" aria-selected={activeTab === 'c'} aria-controls="tab-panel-c" id="tab-c" onclick={() => setTab('c')}>Variant C — District + Detail Split</button>
          <button class="tab-btn" class:active={activeTab === 'd'} role="tab" aria-selected={activeTab === 'd'} aria-controls="tab-panel-d" id="tab-d" onclick={() => setTab('d')}>Variant D — External Validation</button>
          <button class="tab-btn" class:active={activeTab === 'e'} role="tab" aria-selected={activeTab === 'e'} aria-controls="tab-panel-e" id="tab-e" onclick={() => setTab('e')}>Variant E — Overview</button>
          <button class="tab-btn" class:active={activeTab === 'f'} role="tab" aria-selected={activeTab === 'f'} aria-controls="tab-panel-f" id="tab-f" onclick={() => setTab('f')}>Variant F — Methodology</button>
        </div>

        <!-- ── Panel A: Priority Queue List ── -->
        <div class="tab-panel" class:active={activeTab === 'a'} id="tab-panel-a" role="tabpanel" aria-labelledby="tab-a" data-note="← list-dominant: sidebar nav + sortable district rows — optimal for viva demo">
          {#if activeTab === 'a'}
            <QueueTab />
          {/if}
        </div>

        <!-- ── Panel B: Map + Cards ── -->
        <div class="tab-panel" class:active={activeTab === 'b'} id="tab-panel-b" role="tabpanel" aria-labelledby="tab-b" data-note="← spatial-first: choropleth left, district cards right — good for field ops">
          {#if activeTab === 'b'}
            <MapTab />
          {/if}
        </div>

        <!-- ── Panel C: District + Detail Split ── -->
        <div class="tab-panel" class:active={activeTab === 'c'} id="tab-panel-c" role="tabpanel" aria-labelledby="tab-c" data-note="← master-detail: select district left → parameter bars + pathogen alert right">
          {#if activeTab === 'c'}
            <DetailTab />
          {/if}
        </div>

        <!-- ── Panel D: External Validation ── -->
        <div class="tab-panel" class:active={activeTab === 'd'} id="tab-panel-d" role="tabpanel" aria-labelledby="tab-d" data-note="← 4-way triangulation table — WaterTriage vs IMIS 2012 / JJM 2024 / NIRDPR / Census">
          {#if activeTab === 'd'}
            <ValidationTab />
          {/if}
        </div>

        <!-- ── Panel E: Overview ── -->
        <div class="tab-panel" class:active={activeTab === 'e'} id="tab-panel-e" role="tabpanel" aria-labelledby="tab-e" data-note="← project overview, team, timeline">
          {#if activeTab === 'e'}
            <OverviewTab navigate={setTab} />
          {/if}
        </div>

        <!-- ── Panel F: Methodology ── -->
        <div class="tab-panel" class:active={activeTab === 'f'} id="tab-panel-f" role="tabpanel" aria-labelledby="tab-f" data-note="← BIS IS 10500 scoring model, weight matrix, data sources">
          {#if activeTab === 'f'}
            <MethodologyTab navigate={setTab} />
          {/if}
        </div>
      </div>
    </div>
  </section>
</main>

<footer class="footer pagefoot">
  <div class="row-between">
    <div class="footer-left">WaterTriage v0.4 · Anubhav Anand · Amity University</div>
    <div class="footer-right">NTCC Minor Project · B.Tech CSE</div>
  </div>
</footer>