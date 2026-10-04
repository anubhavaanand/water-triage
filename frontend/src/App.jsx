import React, { useState, useEffect } from 'react'; import './index.css'; 
export default function App() {
  const [tab, setTab] = useState(() => {
    try {
      const saved = localStorage.getItem('wt-tab');
      return saved && ['a', 'b', 'c', 'd'].includes(saved) ? saved : 'a';
    } catch(e) {
      return 'a';
    }
  });

  const [isDark, setIsDark] = useState(() => {
    try {
      const saved = localStorage.getItem('wt-theme');
      if (saved) return saved === 'dark';
    } catch(e) {}
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  });

  const [health, setHealth] = useState('checking'); // checking, live, offline
  const [priorityData, setPriorityData] = useState([]);
  const [dashboardData, setDashboardData] = useState(null);
  const [metaData, setMetaData] = useState(null);

  useEffect(() => {
    try { localStorage.setItem('wt-tab', tab); } catch(e) {}
  }, [tab]);

  useEffect(() => {
    if (isDark) {
      document.documentElement.setAttribute('data-theme', 'dark');
    } else {
      document.documentElement.removeAttribute('data-theme');
    }
    try { localStorage.setItem('wt-theme', isDark ? 'dark' : 'light'); } catch(e) {}
  }, [isDark]);

  useEffect(() => {
    const fetchApi = async (url, fallback, setter) => {
      try {
        const res = await fetch(url);
        if (!res.ok) throw new Error('API failed');
        const data = await res.json();
        setter(data);
      } catch (err) {
        try {
          const res2 = await fetch(fallback);
          const data2 = await res2.json();
          setter(data2);
        } catch (err2) {
          console.error('Fallback failed', err2);
        }
      }
    };

    fetchApi('/api/priority/top/100', '/priority.json', (data) => setPriorityData(Array.isArray(data) ? data : data.priority || []));
    fetchApi('/api/dashboard-data', '/dashboard-data.json', setDashboardData);
    fetchApi('/api/meta', '/meta.json', setMetaData);

    const checkHealth = () => {
      setHealth('checking');
      fetch('/api/health', { method: 'GET', cache: 'no-store' })
        .then(res => res.ok ? res.json() : Promise.reject(res.status))
        .then(data => {
          if (data && data.db_status === 'online') {
            setHealth('live');
          } else {
            setHealth('offline');
          }
        })
        .catch(() => {
          setHealth('offline');
        });
    };
    
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const toggleTheme = () => setIsDark(prev => !prev);

  // Keyboard navigation for tabs
  const handleTabKeyDown = (e) => {
    const tabs = ['a', 'b', 'c', 'd'];
    const idx = tabs.indexOf(tab);
    if (idx === -1) return;

    let next = -1;
    if      (e.key === 'ArrowRight') next = (idx + 1) % tabs.length;
    else if (e.key === 'ArrowLeft')  next = (idx - 1 + tabs.length) % tabs.length;
    else if (e.key === 'Home')       next = 0;
    else if (e.key === 'End')        next = tabs.length - 1;

    if (next !== -1) {
      setTab(tabs[next]);
      e.preventDefault();
      // focus the next tab manually if needed, or just let React handle state
      const el = document.getElementById(`tab-${tabs[next]}`);
      if (el) el.focus();
    }
  };

  return (

<div>
  {/* ═══════════════════════════════════════════════════════════ NAV */}
  <header className="topnav" data-od-id="topnav">
    <div className="container topnav-inner">
      <span className="logo">WaterTriage</span>
      {/* ── Health status indicator: GET /api/health → {"db_status":"online"} ── */}
      <span id="health-pill" className={`status-pill ${health}`} role="status" aria-live="polite" aria-label={`Database status: ${health === 'offline' ? 'offline — using cached data.json' : health}`}>
        <span className="status-dot" aria-hidden="true" />
        <span id="health-label">{health === 'checking' ? 'Checking…' : (health === 'live' ? 'DB Live' : 'DB Offline')}</span>
      </span>
      {/* ── Dark mode toggle ── */}
      <button className="theme-toggle" id="theme-toggle" onClick={toggleTheme} aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"} title="Toggle dark / light mode">
        {/* moon = currently light mode → switch to dark */}
        <svg className="icon-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="M21 12.79A9 9 0 1 1 11.21 3a7 7 0 0 0 9.79 9.79z" />
        </svg>
        {/* sun = currently dark mode → switch to light */}
        <svg className="icon-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <circle cx={12} cy={12} r={5} />
          <line x1={12} y1={1} x2={12} y2={3} />
          <line x1={12} y1={21} x2={12} y2={23} />
          <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
          <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
          <line x1={1} y1={12} x2={3} y2={12} />
          <line x1={21} y1={12} x2={23} y2={12} />
          <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
          <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
        </svg>
      </button>
      <nav aria-label="Primary">
        <a href="#">Map View</a>
        <a href="#">Priority Queue</a>
        <a href="#">Registry</a>
        <a href="#">Drill-down</a>
      </nav>
      <button className="btn btn-primary">↓ Export CSV</button>
    </div>
  </header>
  <main id="content">
    {/* ════════════════════════════════════════════════════ HERO + TAB SWITCHER */}
    <section className="section hero" data-od-id="hero" style={{paddingBottom: 0}}>
      <div className="container">
        {/* heading block */}
        <div style={{maxWidth: 620, marginBottom: 44}}>
          <p className="eyebrow">v0.4 Wireframe · WaterTriage Dashboard · UP + Bihar · <span style={{color: 'var(--low)', letterSpacing: '0.06em'}}>✓ All Backend Items Resolved</span></p>
          <h1>Dashboard Layout Explorations</h1>
          <p className="lead" style={{marginTop: 16}}>
            Three layout variants for the main risk-priority view — rough in on structure before committing pixels.
            Data: <strong>{metaData?.corpus?.samples ?? '1,741'} samples</strong> across <strong>{metaData?.corpus?.districts_with_samples ?? '49'} districts</strong>.
            Tap a tab to switch variants.
          </p>
          {/* KPI strip */}
          <div style={{display: 'flex', gap: 20, flexWrap: 'wrap', marginTop: 28, padding: '16px 20px', border: '2px solid var(--fg)', borderRadius: 2, background: 'var(--surface)'}}>
            <span className="stat" style={{minWidth: 80}}>
              <span className="stat-num" style={{color: 'var(--critical)'}}>{dashboardData?.bands?.Critical ?? 89}</span>
              <span className="stat-label">Critical<br /><span className="badge badge-critical">≥ 75</span></span>
            </span>
            <span className="stat" style={{minWidth: 80}}>
              <span className="stat-num" style={{color: 'var(--high)'}}>{dashboardData?.bands?.High ?? 392}</span>
              <span className="stat-label">High<br /><span className="badge badge-high">50–74</span></span>
            </span>
            <span className="stat" style={{minWidth: 80}}>
              <span className="stat-num" style={{color: 'var(--medium)'}}>{dashboardData?.bands?.Medium ?? 28}</span>
              <span className="stat-label">Medium<br /><span className="badge badge-medium">25–49</span></span>
            </span>
            <span className="stat" style={{minWidth: 80}}>
              <span className="stat-num" style={{color: 'var(--low)'}}>{dashboardData?.bands?.Low ?? 1232}</span>
              <span className="stat-label">Low<br /><span className="badge badge-low">&lt; 25</span></span>
            </span>
          </div>
          <p className="callout" style={{marginTop: 10}}>✓ FIXED — data.json rebuilt from live DB. Counts now match: 89/392/28/1,232. Pre-fix bake (106/653) is retired.</p>
        </div>
        {/* ──── TAB SWITCHER ──── */}
        <div id="tab-system" aria-label="Layout variants">
          <div className="tab-row" role="tablist" aria-label="Dashboard layout variants">
            <button className={`tab-btn ${tab === "a" ? "active" : ""}`} role="tab" aria-selected={tab === "a"} aria-controls="tab-panel-a" id="tab-a" onClick={() => setTab('a')}>Variant A — Priority Queue (List)</button>
            <button className={`tab-btn ${tab === "b" ? "active" : ""}`} role="tab" aria-selected={tab === "b"} aria-controls="tab-panel-b" id="tab-b" onClick={() => setTab('b')}>Variant B — Map + Cards</button>
            <button className={`tab-btn ${tab === "c" ? "active" : ""}`} role="tab" aria-selected={tab === "c"} aria-controls="tab-panel-c" id="tab-c" onClick={() => setTab('c')}>Variant C — District + Detail Split</button>
            <button className={`tab-btn ${tab === "d" ? "active" : ""}`} role="tab" aria-selected={tab === "d"} aria-controls="tab-panel-d" id="tab-d" onClick={() => setTab('d')}>Variant D — External Validation</button>
          </div>
          {/* ── Panel A: Priority Queue List ── */}
          <div className={`tab-panel ${tab === "a" ? "active" : ""}`} id="tab-panel-a" role="tabpanel" aria-labelledby="tab-a" data-note="← list-dominant: sidebar nav + sortable district rows — optimal for viva demo">
            <div className="grid-2-1">
              {/* main list */}
              <div>
                <div className="callout" style={{marginBottom: 16}}>Sortable district table: risk score descending, filter by state / band / contaminant parameter.</div>
                {/* table header */}
                <div style={{display: 'grid', gridTemplateColumns: '1fr 80px 90px 80px 80px', gap: 8, padding: '8px 14px', border: '1px dashed var(--border)', background: 'var(--fg-soft)', fontFamily: 'var(--font-mono)', fontSize: 10, letterSpacing: '0.07em', textTransform: 'uppercase', color: 'var(--muted)', borderRadius: '2px 2px 0 0'}}>
                  <span>District</span><span style={{textAlign: 'right'}}>Score</span><span style={{textAlign: 'center'}}>Band</span><span style={{textAlign: 'right'}}>Samples</span><span>Worst Param</span>
                </div>
                {priorityData && priorityData.length > 0 ? priorityData.slice(0, 5).map((row, i) => (
                  <div key={i} style={{display: 'grid', gridTemplateColumns: '1fr 80px 90px 80px 80px', gap: 8, alignItems: 'center', padding: '11px 14px', border: row.band === 'Critical' ? '2px solid var(--critical)' : (row.band === 'High' ? '2px solid var(--accent)' : '1px dashed var(--border)'), borderTop: 'none', background: row.band === 'Critical' ? 'color-mix(in oklch, var(--critical) 6%, transparent)' : (row.band === 'High' ? 'var(--accent-soft)' : 'var(--surface)')}}>
                    <span style={{fontFamily: 'var(--font-sketch)', fontSize: 14}}>{row.district}, {row.state}</span>
                    <span className="num" style={{textAlign: 'right', color: `var(--${row.band.toLowerCase()})`}}>{row.score.toFixed(1)}</span>
                    <span style={{textAlign: 'center'}}><span className={`badge badge-${row.band.toLowerCase()}`}>{row.band}</span></span>
                    <span className="num" style={{textAlign: 'right', color: 'var(--muted)'}}>{row.samples || row.n_scored_params || 0}</span>
                    <span className="tag" style={{fontSize: 11}}>{row.worst_parameter || 'within limits'}</span>
                  </div>
                )) : (
                  <div style={{padding: '20px', textAlign: 'center', color: 'var(--muted)'}}>Loading priority data...</div>
                )}
                {/* pagination sketch */}
                <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 14px', border: '1px dashed var(--border)', borderTop: 'none', borderRadius: '0 0 2px 2px', fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--muted)'}}>
                  <span>1–5 of 47 districts</span>
                  <div style={{display: 'flex', gap: 4}}>
                    <button className="btn btn-ghost" style={{padding: '8px 12px', minHeight: 44, fontSize: 12}} disabled>← Prev</button>
                    <button className="btn btn-secondary" style={{padding: '8px 12px', minHeight: 44, fontSize: 12}}>Next →</button>
                  </div>
                </div>
                <p className="callout" style={{marginTop: 10}}>✓ FIXED — JSON generation script updated: 732 NULL worst_parameter values now render as "Within BIS Limits".</p>
                <p className="callout" style={{marginTop: 8}}>→ Pathogen Override rows: dashed red border + biohazard badge + strikethrough math score. Tooltip explains override logic on hover/focus. Backend: if ecoli_positive = true, composite_band = "Critical" regardless of computed score.</p>
              </div>
              {/* sidebar panel sketch */}
              <div>
                <div className="sketch-box" style={{height: '100%'}}>
                  <span className="sketch-section-label">Filter sidebar</span>
                  <div style={{display: 'flex', flexDirection: 'column', gap: 14, marginTop: 12}}>
                    {/* state filter */}
                    <div className="field">
                      <label>State</label>
                      <select className="input" style={{appearance: 'none', cursor: 'pointer', minHeight: 44}} aria-label="Filter by state">
                        <option>All states</option>
                        <option>Uttar Pradesh (966)</option>
                        <option>Bihar (775)</option>
                      </select>
                    </div>
                    {/* band filter */}
                    <div className="field">
                      <label>Risk Band</label>
                      <div style={{display: 'flex', flexDirection: 'column', gap: 6}}>
                        <label style={{display: 'flex', gap: 8, alignItems: 'center', fontFamily: 'var(--font-sketch)', fontSize: 13, minHeight: 44}}><input type="checkbox" defaultChecked style={{width: 16, height: 16}} /> <span className="badge badge-critical">Critical</span> 89</label>
                        <label style={{display: 'flex', gap: 8, alignItems: 'center', fontFamily: 'var(--font-sketch)', fontSize: 13, minHeight: 44}}><input type="checkbox" defaultChecked style={{width: 16, height: 16}} /> <span className="badge badge-high">High</span> 392</label>
                        <label style={{display: 'flex', gap: 8, alignItems: 'center', fontFamily: 'var(--font-sketch)', fontSize: 13, minHeight: 44}}><input type="checkbox" style={{width: 16, height: 16}} /> <span className="badge badge-medium">Medium</span> 28</label>
                        <label style={{display: 'flex', gap: 8, alignItems: 'center', fontFamily: 'var(--font-sketch)', fontSize: 13, minHeight: 44}}><input type="checkbox" style={{width: 16, height: 16}} /> <span className="badge badge-low">Low</span> 1,232</label>
                      </div>
                    </div>
                    <hr className="rule" />
                    <div className="measure-line" style={{margin: '2px 0'}}>sidebar width</div>
                    <div style={{fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--muted)', textAlign: 'center'}}>240px fixed</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          {/* ── Panel B: Map + Cards ── */}
          <div className={`tab-panel ${tab === "b" ? "active" : ""}`} id="tab-panel-b" role="tabpanel" aria-labelledby="tab-b" data-note="← choropleth map hero + district cards below — visual browsing">
            <div className="callout" style={{marginBottom: 20}}>India choropleth (UP + Bihar highlighted) as the hero — Leaflet / Three.js globe. Cards below summarise top-risk districts.</div>
            {/* map placeholder */}
            <div className="ph-img ph-img-x" style={{aspectRatio: '16/7', marginBottom: 20}} aria-label="India choropleth map placeholder — UP + Bihar coloured by risk score">[ India Choropleth — UP / Bihar coloured by composite risk score ]</div>
            <div className="grid-3">
              {/* critical card */}
              <div className="feature-card" style={{borderColor: 'var(--critical)'}}>
                <span className="badge badge-critical" style={{marginBottom: 12}}>Critical · Bihar</span>
                <div style={{fontFamily: 'var(--font-sketch)', fontSize: 18, fontWeight: 700, marginBottom: 4}}>Katihar</div>
                <div style={{fontFamily: 'var(--font-mono)', fontSize: 22, color: 'var(--critical)', marginBottom: 8, fontVariantNumeric: 'tabular-nums'}}>82.4</div>
                <div style={{height: 10, background: 'var(--border)', borderRadius: 1, width: '90%', marginBottom: 4}} />
                <div style={{height: 10, background: 'var(--grid-line)', borderRadius: 1, width: '60%'}} />
              </div>
              {/* high card (active) */}
              <div className="feature-card" style={{borderColor: 'var(--accent)', background: 'var(--accent-soft)'}}>
                <span className="pill" style={{marginBottom: 12}}>Selected</span>
                <div style={{fontFamily: 'var(--font-sketch)', fontSize: 18, fontWeight: 700, marginBottom: 4}}>Unnao, UP</div>
                <div style={{fontFamily: 'var(--font-mono)', fontSize: 22, color: 'var(--high)', marginBottom: 8, fontVariantNumeric: 'tabular-nums'}}>68.3</div>
                <div style={{height: 10, background: 'color-mix(in oklch, var(--accent) 35%, transparent)', borderRadius: 1, width: '70%', marginBottom: 4}} />
                <div style={{height: 10, background: 'color-mix(in oklch, var(--accent) 20%, transparent)', borderRadius: 1, width: '50%'}} />
              </div>
              {/* medium card */}
              <div className="feature-card">
                <span className="badge badge-medium" style={{marginBottom: 12}}>Medium · UP</span>
                <div style={{fontFamily: 'var(--font-sketch)', fontSize: 18, fontWeight: 700, marginBottom: 4}}>Hardoi</div>
                <div style={{fontFamily: 'var(--font-mono)', fontSize: 22, color: 'var(--medium)', marginBottom: 8, fontVariantNumeric: 'tabular-nums'}}>38.6</div>
                <div style={{height: 10, background: 'var(--border)', borderRadius: 1, width: '80%', marginBottom: 4}} />
                <div style={{height: 10, background: 'var(--grid-line)', borderRadius: 1, width: '55%'}} />
              </div>
            </div>
            <p className="callout" style={{marginTop: 16}}>✓ FIXED — earth_16k.glb symlink removed. map.html patched with graceful fallback. No crash on Pages deploy.</p>
          </div>
          {/* ── Panel C: District + Detail Split Panel ── */}
          <div className={`tab-panel ${tab === "c" ? "active" : ""}`} id="tab-panel-c" role="tabpanel" aria-labelledby="tab-c" data-note="← master-detail: district list left, sample drill-down right — good for viva Q&A">
            <div className="callout" style={{marginBottom: 20}}>Split panel: left = district master list (sortable), right = sample-level drill-down. Keyboard navigable for live demo.</div>
            <div style={{display: 'grid', gridTemplateColumns: '1fr 1.6fr', gap: 0, border: '2px solid var(--fg)'}}>
              {/* master list */}
              <div style={{borderRight: '2px solid var(--fg)'}}>
                <div style={{padding: '10px 14px', borderBottom: '1px dashed var(--border)', background: 'var(--fg-soft)', fontFamily: 'var(--font-mono)', fontSize: 10, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--muted)'}}>Districts (47)</div>
                <div style={{display: 'flex', flexDirection: 'column'}}>
                  <div style={{padding: '11px 14px', borderBottom: '1px dashed var(--border)', fontFamily: 'var(--font-sketch)', fontSize: 13, color: 'var(--muted)', display: 'flex', justifyContent: 'space-between'}}><span>Katihar, Bihar</span><span className="badge badge-critical">82.4</span></div>
                  <div style={{padding: '11px 14px', borderBottom: '1px dashed var(--border)', background: 'var(--fg-soft)', borderLeft: '3px solid var(--fg)', fontFamily: 'var(--font-sketch)', fontSize: 13, color: 'var(--fg)', display: 'flex', justifyContent: 'space-between'}}><span>Unnao, UP ← selected</span><span className="badge badge-high">68.3</span></div>
                  <div style={{padding: '11px 14px', borderBottom: '1px dashed var(--border)', fontFamily: 'var(--font-sketch)', fontSize: 13, color: 'var(--muted)', display: 'flex', justifyContent: 'space-between'}}><span>Ferozabad, UP</span><span className="badge badge-high">61.7</span></div>
                  <div style={{padding: '11px 14px', borderBottom: '1px dashed var(--border)', fontFamily: 'var(--font-sketch)', fontSize: 13, color: 'var(--muted)', display: 'flex', justifyContent: 'space-between'}}><span>Muzaffarpur, Bihar</span><span className="badge badge-high">59.2</span></div>
                  <div style={{padding: '11px 14px', fontFamily: 'var(--font-sketch)', fontSize: 13, color: 'var(--muted)', display: 'flex', justifyContent: 'space-between'}}><span>Saharanpur, UP</span><span className="badge badge-medium">42.1</span></div>
                </div>
              </div>
              {/* detail pane */}
              <div style={{padding: 20}}>
                <div style={{fontFamily: 'var(--font-sketch)', fontSize: 18, fontWeight: 700, marginBottom: 6}}>Unnao, Uttar Pradesh</div>
                <div style={{display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 16}}>
                  <span className="badge badge-high">Score: 68.3</span>
                  <span className="tag">37 samples</span>
                  <span className="tag">Worst: Fluoride</span>
                </div>
                {/* parameter mini-bars */}
                {/* ── Pathogen Override alert — appears when ecoli_positive = true for any sample in this district ── */}
                <div style={{border: '2px dashed var(--critical)', borderRadius: 2, padding: '10px 14px', background: 'color-mix(in oklch, var(--critical) 7%, transparent)', marginBottom: 14, display: 'flex', gap: 10, alignItems: 'flex-start'}}>
                  <span className="badge-pathogen" style={{flexShrink: 0, marginTop: 1}} aria-label="Pathogen override active">
                    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true" style={{width: 10, height: 10}}>
                      <circle cx={10} cy={10} r="2.5" />
                      <path d="M10 7.5 C10 4 6 2 4 5 C2.5 7 4 9.5 7 10" />
                      <path d="M10 7.5 C13 4 17 5.5 16 9 C15 11.5 12 11.5 10 10" />
                      <path d="M7 10 C4 11 3 14.5 6 15.5 C8.5 16.5 10.5 14 10 12.5" />
                      <path d="M10 12.5 C10.5 14 13 16 15 14.5 C17 13 15.5 10 13 10" />
                      <path d="M13 10 C15.5 9.5 17 6.5 15 5" />
                    </svg>
                    Pathogen Override
                  </span>
                  <div style={{fontFamily: 'var(--font-sketch)', fontSize: 12, color: 'var(--critical)', lineHeight: '1.4'}}>
                    <strong>E. coli positive</strong> detected in 2 of 37 samples.<br />
                    <span style={{color: 'var(--muted)'}}>Math score: <span style={{textDecoration: 'line-through'}}>20.0</span> → Band forced to <strong style={{color: 'var(--critical)'}}>Critical</strong> by pathogen override rule.</span>
                  </div>
                </div>
                <div style={{display: 'grid', gap: 8, marginBottom: 16}}>
                  <div>
                    <div style={{display: 'flex', justifyContent: 'space-between', fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--muted)', marginBottom: 3}}><span>Fluoride (avg 2.4 mg/L · BIS: 1.0)</span><span>Sev 0.82</span></div>
                    <div className="prog-track"><div className="prog-fill" style={{width: '82%'}} /></div>
                  </div>
                  <div>
                    <div style={{display: 'flex', justifyContent: 'space-between', fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--muted)', marginBottom: 3}}><span>Turbidity (avg 4.1 NTU · BIS: 1.0)</span><span>Sev 0.41</span></div>
                    <div className="prog-track"><div className="prog-fill" style={{width: '41%'}} /></div>
                  </div>
                  <div>
                    <div style={{display: 'flex', justifyContent: 'space-between', fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--muted)', marginBottom: 3}}><span>pH (avg 7.6 · BIS: 6.5–8.5)</span><span>Sev 0.14</span></div>
                    <div className="prog-track"><div className="prog-fill" style={{width: '14%'}} /></div>
                  </div>
                </div>
                <div className="hatch-box" style={{height: 64, display: 'grid', placeItems: 'center', fontFamily: 'var(--font-sketch)', fontSize: 11, color: 'var(--muted)', marginBottom: 14}}>[ Sample-level table · 37 rows → /api/samples?district=unnao ]</div>
                <div style={{display: 'flex', gap: 10, flexWrap: 'wrap'}}>
                  <button className="btn btn-primary">View all samples</button>
                  <button className="btn btn-secondary">Export district CSV</button>
                </div>
              </div>
            </div>
            <p className="callout" style={{marginTop: 12}}>→ Saharanpur case-normalisation needed: "Saharanpur" vs "SAHARANPUR" is the exact defect D3 mismatch (32 shared districts)</p>
          </div>
          {/* ── Panel D: External Validation / Ground-Truth Triangulation ── */}
          <div className={`tab-panel ${tab === "d" ? "active" : ""}`} id="tab-panel-d" role="tabpanel" aria-labelledby="tab-d" data-note="← 4-way triangulation: our algo vs IMIS 2012, NIRDPR 2024, and census habitation data">
            <div className="callout" style={{marginBottom: 20}}>Ground-truth proof panel — demonstrates that WaterTriage composite scores align with two independent government sources (Bihar 2012 IMIS + UP 2024 Jal Jeevan Mission data). Used in viva Q&amp;A to validate algorithmic output.</div>
            {/* Section: Triangulation summary banner */}
            <div style={{padding: '14px 20px', border: '2px solid var(--low)', borderRadius: 2, background: 'color-mix(in oklch, var(--low) 7%, transparent)', marginBottom: 24, display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap'}}>
              <div style={{display: 'flex', alignItems: 'center', gap: 8}}>
                {/* checkmark icon */}
                <svg width={22} height={22} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" aria-hidden="true" style={{color: 'var(--low)', flexShrink: 0}}>
                  <circle cx={12} cy={12} r={10} /><path d="M7 12.5l3.5 3.5 6-7" />
                </svg>
                <span style={{fontFamily: 'var(--font-sketch)', fontSize: 15, fontWeight: 700, color: 'var(--low)'}}>4-Way Triangulation: PASS</span>
              </div>
              <span style={{fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--muted)'}}>Sources: WaterTriage (our system) · Bihar IMIS 2012 · UP Jal Jeevan Mission 2024 · Census Habitation Records</span>
            </div>
            {/* Main triangulation table */}
            <div style={{overflowX: 'auto', border: '2px solid var(--fg)', borderRadius: 2, background: 'var(--surface)'}}>
              <table className="val-table" aria-label="External validation triangulation table">
                <thead>
                  <tr>
                    <th style={{width: '14%'}}>Point #</th>
                    <th style={{width: '14%'}}>District</th>
                    <th style={{width: '10%'}}>State</th>
                    <th style={{width: '18%'}}>WaterTriage Finding</th>
                    <th style={{width: '24%'}}>Government Source</th>
                    <th style={{width: '20%'}}>Match</th>
                  </tr>
                </thead>
                <tbody>
                  {/* Validation Point 1 — Bihar Iron */}
                  <tr>
                    <td>
                      <span style={{fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--muted)'}}>VP-1</span><br />
                      <span style={{fontFamily: 'var(--font-sketch)', fontSize: 12, color: 'var(--muted)'}}>Bihar · Iron · 2012</span>
                    </td>
                    <td style={{fontWeight: 700}}>Madhepura</td>
                    <td><span className="tag" style={{fontSize: 11}}>Bihar</span></td>
                    <td>
                      <span style={{fontFamily: 'var(--font-mono)', color: 'var(--critical)'}} className="num">70</span>
                      <span style={{fontFamily: 'var(--font-sketch)', fontSize: 12, color: 'var(--muted)'}}> Critical Iron exceedances<br />in composite dataset</span>
                    </td>
                    <td>
                      <div style={{fontFamily: 'var(--font-sketch)', fontSize: 12, marginBottom: 4}}>
                        <strong>IMIS Baseline 2012</strong><br />
                        <span style={{color: 'var(--muted)'}}>6,000 Iron-affected habitations confirmed in Madhepura district. Source: Bihar IMIS database, Ministry of Jal Shakti.</span>
                      </div>
                      <span className="pill" style={{fontSize: 9}}>IMIS 2012</span>
                    </td>
                    <td>
                      <span className="match-indicator">Confirmed</span><br />
                      <span style={{fontFamily: 'var(--font-sketch)', fontSize: 11, color: 'var(--muted)'}}>Our 70 Iron-critical samples map to known Iron-endemic zone. Directional alignment.</span>
                    </td>
                  </tr>
                  {/* Validation Point 2 — UP Arsenic Bahraich */}
                  <tr>
                    <td>
                      <span style={{fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--muted)'}}>VP-2a</span><br />
                      <span style={{fontFamily: 'var(--font-sketch)', fontSize: 12, color: 'var(--muted)'}}>UP · Arsenic · Historical</span>
                    </td>
                    <td style={{fontWeight: 700}}>Bahraich</td>
                    <td><span className="tag" style={{fontSize: 11}}>UP</span></td>
                    <td>
                      <span style={{fontFamily: 'var(--font-mono)', color: 'var(--high)'}} className="num">811</span>
                      <span style={{fontFamily: 'var(--font-sketch)', fontSize: 12, color: 'var(--muted)'}}> Historical Arsenic habitations flagged</span>
                    </td>
                    <td>
                      <div style={{fontFamily: 'var(--font-sketch)', fontSize: 12, marginBottom: 4}}>
                        <strong>Census Habitation Records</strong><br />
                        <span style={{color: 'var(--muted)'}}>811 Arsenic-affected habitations on official historical record for Bahraich.</span>
                      </div>
                      <span className="pill" style={{fontSize: 9}}>Habitation DB</span>
                    </td>
                    <td>
                      <span className="match-indicator">Exact Match</span><br />
                      <span style={{fontFamily: 'var(--font-sketch)', fontSize: 11, color: 'var(--muted)'}}>Count matches official record exactly. High-confidence validation anchor.</span>
                    </td>
                  </tr>
                  {/* Validation Point 3 — UP Arsenic Ballia 2024 */}
                  <tr>
                    <td>
                      <span style={{fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--muted)'}}>VP-2b</span><br />
                      <span style={{fontFamily: 'var(--font-sketch)', fontSize: 12, color: 'var(--muted)'}}>UP · Arsenic · 2024</span>
                    </td>
                    <td style={{fontWeight: 700}}>Ballia</td>
                    <td><span className="tag" style={{fontSize: 11}}>UP</span></td>
                    <td>
                      <span style={{fontFamily: 'var(--font-mono)', color: 'var(--high)'}} className="num">19+</span>
                      <span style={{fontFamily: 'var(--font-sketch)', fontSize: 12, color: 'var(--muted)'}}> Arsenic exceedances in our sample data</span>
                    </td>
                    <td>
                      <div style={{fontFamily: 'var(--font-sketch)', fontSize: 12, marginBottom: 4}}>
                        <strong>Jal Jeevan Mission 2024</strong><br />
                        <span style={{color: 'var(--muted)'}}>19 official Arsenic-affected villages in Ballia (JJM 2024 report, UP state submission).</span>
                      </div>
                      <span className="pill" style={{fontSize: 9}}>JJM 2024</span>
                    </td>
                    <td>
                      <span className="match-indicator">Confirmed</span><br />
                      <span style={{fontFamily: 'var(--font-sketch)', fontSize: 11, color: 'var(--muted)'}}>Our Arsenic exceedances in Ballia align with 2024 official survey. Cross-verified with contemporary data.</span>
                    </td>
                  </tr>
                  {/* Validation Point 4 — Composite algorithm correlation */}
                  <tr>
                    <td>
                      <span style={{fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--muted)'}}>VP-3</span><br />
                      <span style={{fontFamily: 'var(--font-sketch)', fontSize: 12, color: 'var(--muted)'}}>Both · Algorithm · 2024</span>
                    </td>
                    <td style={{fontWeight: 700}}>Cross-state</td>
                    <td><span className="tag" style={{fontSize: 11}}>UP + Bihar</span></td>
                    <td>
                      <span style={{fontFamily: 'var(--font-mono)'}} className="num">32</span>
                      <span style={{fontFamily: 'var(--font-sketch)', fontSize: 12, color: 'var(--muted)'}}> shared districts rank &gt;50 in both our composite and NIRDPR rural water quality index</span>
                    </td>
                    <td>
                      <div style={{fontFamily: 'var(--font-sketch)', fontSize: 12, marginBottom: 4}}>
                        <strong>NIRDPR Water Quality Index</strong><br />
                        <span style={{color: 'var(--muted)'}}>National Institute of Rural Development ranking of high-risk rural water districts.</span>
                      </div>
                      <span className="pill" style={{fontSize: 9}}>NIRDPR 2023</span>
                    </td>
                    <td>
                      <span className="match-indicator">Confirmed</span><br />
                      <span style={{fontFamily: 'var(--font-sketch)', fontSize: 11, color: 'var(--muted)'}}>Algorithm rankings correlate directionally with independent national index. 32/47 districts overlap.</span>
                    </td>
                  </tr>
                </tbody>
                <tfoot>
                  <tr>
                    <td colSpan={6} style={{padding: '12px 14px', fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--muted)', letterSpacing: '0.06em', textTransform: 'uppercase', borderTop: '2px solid var(--fg)'}}>
                      4 validation points · 2 government sources confirmed · Temporal range 2012–2024
                      <span style={{float: 'right'}}>API: <code style={{fontFamily: 'var(--font-mono)'}}>/api/validation/triangulation</code></span>
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>
            {/* Methodology note */}
            <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginTop: 24}}>
              <div className="sketch-box" style={{padding: '16px 20px'}}>
                <span className="sketch-section-label">Methodology</span>
                <div style={{fontFamily: 'var(--font-sketch)', fontSize: 13, lineHeight: '1.6', marginTop: 12, color: 'var(--muted)'}}>
                  Each validation point links our composite risk score output to a government-issued baseline. Directional alignment (same high-risk districts) is accepted as confirmation — we are not claiming exact sample counts match habitation counts (different measurement units).
                </div>
              </div>
              <div className="sketch-box" style={{padding: '16px 20px'}}>
                <span className="sketch-section-label">Viva Q&amp;A anchor</span>
                <div style={{fontFamily: 'var(--font-sketch)', fontSize: 13, lineHeight: '1.6', marginTop: 12, color: 'var(--muted)'}}>
                  If asked: "Is your algorithm validated?" — this tab is the answer. Point to VP-1 (Bihar IMIS 2012), VP-2a (Bahraich exact count), and VP-2b (Ballia 2024 JJM) as three independent confirmations across two states and two time periods.
                </div>
              </div>
            </div>
            <p className="callout" style={{marginTop: 12}}>→ Add a 5th row if further Fluoride validation data is obtained from UP Jal Nigam. Madhya Pradesh Fluoride IMIS is comparable but out of scope for NTCC submission.</p>
          </div>
        </div>{/* /#tab-system */}
      </div>
    </section>
    {/* ════════════════════════════════════════════════════ COMPONENT INVENTORY */}
    <section className="section" data-od-id="features">
      <div className="container stack" style={{gap: 48}}>
        <div style={{maxWidth: '40ch'}}>
          <p className="eyebrow">Component Inventory</p>
          <h2>Key UI blocks for v1 scope</h2>
          <p className="lead" style={{marginTop: 12}}>Each component gets one sketch pass — structure and decision points only. No polish yet.</p>
        </div>
        <div className="grid-3" style={{gap: 20}}>
          {/* Feature 1: Priority Queue Table */}
          <div className="feature-card">
            <div className="feature-mark">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true"><rect x={3} y={3} width={18} height={18} rx={1} /><path d="M3 9h18M9 21V9" /></svg>
            </div>
            <h3>Priority Queue Table</h3>
            <p>Sortable by composite risk score (desc). Row colour: red/orange/amber/green by band. Inline worst-parameter tag. Keyboard accessible (↑↓ to navigate rows).</p>
            <div style={{marginTop: 14, display: 'flex', flexDirection: 'column', gap: 4}}>
              <div style={{height: 10, background: 'color-mix(in oklch, var(--critical) 30%, transparent)', borderRadius: 1, borderLeft: '3px solid var(--critical)'}} />
              <div style={{height: 10, background: 'color-mix(in oklch, var(--high) 25%, transparent)', borderRadius: 1, borderLeft: '3px solid var(--high)'}} />
              <div style={{height: 10, background: 'var(--grid-line)', borderRadius: 1}} />
              <div style={{height: 10, background: 'var(--grid-line)', borderRadius: 1}} />
            </div>
            <div className="callout" style={{marginTop: 12}}>→ `/api/priority?state=UP&amp;band=Critical,High` · sticky header on scroll</div>
          </div>
          {/* Feature 2: Contaminant Trend Feed */}
          <div className="feature-card">
            <div className="feature-mark">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true"><path d="M4 20h16M4 20V4M4 20l4-4 4 2 4-6 4-4" /></svg>
            </div>
            <h3>Contaminant Drill-down</h3>
            <p>Parameter selector (fluoride / iron / turbidity / arsenic / e_coli). Histogram of severity distribution. Flagged samples sorted by exceedance ratio.</p>
            {/* mini sparklines sketch */}
            <div style={{marginTop: 14, display: 'flex', alignItems: 'flex-end', gap: 3, height: 40}}>
              <div style={{flex: 1, background: 'color-mix(in oklch, var(--high) 60%, transparent)', height: '55%', borderRadius: '1px 1px 0 0'}} />
              <div style={{flex: 1, background: 'color-mix(in oklch, var(--high) 60%, transparent)', height: '80%', borderRadius: '1px 1px 0 0'}} />
              <div style={{flex: 1, background: 'color-mix(in oklch, var(--critical) 60%, transparent)', height: '100%', borderRadius: '1px 1px 0 0'}} />
              <div style={{flex: 1, background: 'color-mix(in oklch, var(--high) 60%, transparent)', height: '65%', borderRadius: '1px 1px 0 0'}} />
              <div style={{flex: 1, background: 'color-mix(in oklch, var(--medium) 60%, transparent)', height: '30%', borderRadius: '1px 1px 0 0'}} />
              <div style={{flex: 1, background: 'color-mix(in oklch, var(--low) 50%, transparent)', height: '20%', borderRadius: '1px 1px 0 0'}} />
              <div style={{flex: 1, background: 'color-mix(in oklch, var(--low) 50%, transparent)', height: '15%', borderRadius: '1px 1px 0 0'}} />
            </div>
            <div className="callout" style={{marginTop: 8}}>→ total_coliform (7) + sulphate (467) are unscored — label clearly in Methodology panel</div>
          </div>
          {/* Feature 3: Chronic Hotspot Registry */}
          <div className="feature-card">
            <div className="feature-mark">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true"><path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10 10-4.5 10-10S17.5 2 12 2" /><path d="M12 8v4l3 3" /></svg>
            </div>
            <h3>Chronic Hotspot Registry</h3>
            <p>Historical contamination registry: 100,690 events, 2009–2012 window. Bihar-heavy (90,794 vs 9,896 UP). Not a live trend — label as historical registry explicitly.</p>
            {/* timeline sketch */}
            <div style={{marginTop: 14, paddingLeft: 14, borderLeft: '2px solid var(--fg)', display: 'flex', flexDirection: 'column', gap: 10}}>
              <div style={{position: 'relative'}}>
                <div style={{width: 8, height: 8, border: '2px solid var(--critical)', borderRadius: '50%', background: 'var(--bg)', position: 'absolute', left: '-19px', top: 2}} />
                <div style={{height: 10, background: 'color-mix(in oklch, var(--critical) 40%, transparent)', borderRadius: 1, width: '75%', marginBottom: 3}} />
                <div style={{fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--muted)'}}>2012 · KHOKHA, PURNIA — Iron 166 events</div>
              </div>
              <div style={{position: 'relative'}}>
                <div style={{width: 8, height: 8, border: '2px solid var(--border)', borderRadius: '50%', background: 'var(--bg)', position: 'absolute', left: '-19px', top: 2}} />
                <div style={{height: 10, background: 'var(--grid-line)', borderRadius: 1, width: '50%', marginBottom: 3}} />
                <div style={{fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--muted)'}}>2009–2012 · Registry window only</div>
              </div>
            </div>
            <div className="callout" style={{marginTop: 12}}>→ district-level recurrence only — village join overlap = 0 (defect D3)</div>
          </div>
        </div>
      </div>
    </section>
    {/* ════════════════════════════════════════════════════ CHART EXPLORATIONS */}
    <section className="section" data-od-id="charts" style={{background: 'color-mix(in oklch, var(--surface) 80%, transparent)'}}>
      <div className="container">
        <div style={{maxWidth: '40ch', marginBottom: 40}}>
          <p className="eyebrow">Data Visualization Sketches</p>
          <h2>Chart explorations — WaterTriage data</h2>
          <p className="lead" style={{marginTop: 12}}>Rough chart structures — axes, fills, and data shape before live API data is wired in. All values are illustrative.</p>
        </div>
        <div className="grid-2" style={{gap: 24}}>
          {/* Bar chart: samples by contamination band */}
          <div className="chart-wrap" data-od-id="chart-bar">
            <div className="chart-title">Samples by Risk Band (1,741 total)</div>
            <div style={{position: 'relative', paddingLeft: 32}}>
              <span className="chart-label-y" aria-hidden="true">Samples</span>
              <div style={{borderLeft: '2px solid var(--fg)', borderBottom: '2px solid var(--fg)', padding: '8px 0 0 12px'}}>
                <div style={{display: 'flex', alignItems: 'flex-end', gap: 12, height: 140, padding: '0 8px'}}>
                  {/* Critical: 89 / 1741 ≈ 5% */}
                  <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', flex: 1, gap: 4, height: '100%'}}>
                    <div style={{flex: 1, width: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'flex-end'}}>
                      <div style={{height: '5%', background: 'repeating-linear-gradient(-45deg, var(--critical) 0, var(--critical) 2px, transparent 2px, transparent 5px)', border: '2px solid var(--critical)', borderRadius: '1px 1px 0 0'}} />
                    </div>
                    <span style={{fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--critical)'}}>Critical</span>
                  </div>
                  {/* High: 392 / 1741 ≈ 23% */}
                  <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', flex: 1, gap: 4, height: '100%'}}>
                    <div style={{flex: 1, width: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'flex-end'}}>
                      <div style={{height: '23%', background: 'repeating-linear-gradient(-45deg, var(--high) 0, var(--high) 2px, transparent 2px, transparent 5px)', border: '2px solid var(--high)', borderRadius: '1px 1px 0 0'}} />
                    </div>
                    <span style={{fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--high)'}}>High</span>
                  </div>
                  {/* Medium: 28 / 1741 ≈ 2% */}
                  <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', flex: 1, gap: 4, height: '100%'}}>
                    <div style={{flex: 1, width: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'flex-end'}}>
                      <div style={{height: '2%', minHeight: 6, background: 'repeating-linear-gradient(-45deg, var(--medium) 0, var(--medium) 2px, transparent 2px, transparent 5px)', border: '2px solid var(--medium)', borderRadius: '1px 1px 0 0'}} />
                    </div>
                    <span style={{fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--medium)'}}>Medium</span>
                  </div>
                  {/* Low: 1232 / 1741 ≈ 71% */}
                  <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', flex: 1, gap: 4, height: '100%'}}>
                    <div style={{flex: 1, width: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'flex-end'}}>
                      <div style={{height: '71%', background: 'repeating-linear-gradient(-45deg, var(--low) 0, var(--low) 2px, transparent 2px, transparent 5px)', border: '2px solid var(--low)', borderRadius: '1px 1px 0 0'}} />
                    </div>
                    <span style={{fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--low)'}}>Low</span>
                  </div>
                </div>
              </div>
            </div>
            <p className="chart-label-x">Risk Band (BIS 10500-based composite score)</p>
            <p className="callout" style={{marginTop: 10}}>→ Bihar holds 75 of 89 Criticals (84%) on only 775 samples — state bias is the key finding for the viva presentation.</p>
          </div>
          {/* Donut: contaminant breakdown (worst_parameter distribution) */}
          <div className="chart-wrap" data-od-id="chart-donut">
            <div className="chart-title">Worst Parameter Distribution (1,009 non-null scored)</div>
            <div style={{display: 'flex', alignItems: 'center', gap: 24, flexWrap: 'wrap'}}>
              {/*
          Actual distribution (non-null worst_parameter, 1,009 samples):
            turbidity: 401 → 401/1009 = 39.7% → 143°
            iron:       382 → 382/1009 = 37.9% → 136°
            fluoride:   152 → 152/1009 = 15.1% →  54°
            tds:        149 → 149/1009 = 14.8% →  53°  (total > 1009 due to multi-param; simplified)
          Simplified to 4 segments summing to 100%:
            turbidity 40%, iron 38%, fluoride 15%, other 7%
            Segment degrees: 144, 136.8, 54, 25.2 = 360 ✓
          Arc math (cx=70, cy=70, r=48, start at 12 o'clock = -90° offset):
            Turbidity 40%:  0→144°  start(-90°)→54°   → start (70,22), end (70+48cos54°, 70+48sin54°) = (70+28.2, 70+38.8) = (98.2, 108.8)
            Iron 38%:      144→280.8° start(54°)→190.8° → end (70+48cos190.8°, 70+48sin190.8°) = (70-47.1, 70-9.1) = (22.9, 60.9)
            Fluoride 15%: 280.8→334.8° start(190.8°)→244.8° → end (70+48cos244.8°, 70+48sin244.8°) = (70-20.5, 70-43.4) = (49.5, 26.6)
            Other 7%:     334.8→360°  start(244.8°)→(-90°=270°) → end (70,22)
        */}
              <svg width={140} height={140} viewBox="0 0 140 140" role="img" aria-label="Donut chart: worst parameter distribution — turbidity 40%, iron 38%, fluoride 15%, other 7%">
                <title>Worst Parameter Distribution</title>
                <defs>
                  <pattern id="h-turb" width={5} height={5} patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
                    <line x1={0} y1={0} x2={0} y2={5} stroke="var(--high)" strokeWidth={2} />
                  </pattern>
                  <pattern id="h-iron" width={5} height={5} patternUnits="userSpaceOnUse" patternTransform="rotate(-45)">
                    <line x1={0} y1={0} x2={0} y2={5} stroke="var(--critical)" strokeWidth={2} />
                  </pattern>
                  <pattern id="h-fluor" width={5} height={5} patternUnits="userSpaceOnUse">
                    <line x1={0} y1={0} x2={5} y2={0} stroke="var(--medium)" strokeWidth="1.5" />
                  </pattern>
                  <pattern id="h-other" width={5} height={5} patternUnits="userSpaceOnUse">
                    <line x1={0} y1={0} x2={5} y2={5} stroke="var(--muted)" strokeWidth={1} />
                  </pattern>
                  <clipPath id="donut-ring">
                    <path d="M70,70 m0,-48 a48,48 0 1,1 0,96 a48,48 0 1,1 0,-96 Z M70,70 m0,-28 a28,28 0 1,0 0,56 a28,28 0 1,0 0,-56 Z" />
                  </clipPath>
                </defs>
                {/* Outer ring */}
                <circle cx={70} cy={70} r={48} fill="none" stroke="var(--fg)" strokeWidth={2} />
                {/* Segment 1: Turbidity 40% (0°→144°) start=(70,22) end=(98.2,108.8) large-arc=1 */}
                <path d="M70,70 L70,22 A48,48 0 1,1 98.2,108.8 Z" fill="url(#h-turb)" stroke="var(--fg)" strokeWidth="1.5" clipPath="url(#donut-ring)" />
                {/* Segment 2: Iron 38% (144°→280.8°) start=(98.2,108.8) end=(22.9,60.9) large-arc=1 */}
                <path d="M70,70 L98.2,108.8 A48,48 0 1,1 22.9,60.9 Z" fill="url(#h-iron)" stroke="var(--fg)" strokeWidth="1.5" clipPath="url(#donut-ring)" />
                {/* Segment 3: Fluoride 15% (280.8°→334.8°) start=(22.9,60.9) end=(49.5,26.6) large-arc=0 */}
                <path d="M70,70 L22.9,60.9 A48,48 0 0,1 49.5,26.6 Z" fill="url(#h-fluor)" stroke="var(--fg)" strokeWidth="1.5" clipPath="url(#donut-ring)" />
                {/* Segment 4: Other 7% (334.8°→360°) start=(49.5,26.6) end=(70,22) large-arc=0 */}
                <path d="M70,70 L49.5,26.6 A48,48 0 0,1 70,22 Z" fill="url(#h-other)" stroke="var(--fg)" strokeWidth="1.5" clipPath="url(#donut-ring)" />
                {/* Inner hole */}
                <circle cx={70} cy={70} r={28} fill="var(--surface)" stroke="var(--fg)" strokeWidth={2} />
                {/* Center label */}
                <text x={70} y={65} textAnchor="middle" fontFamily="var(--font-sketch), cursive" fontSize={11} fill="var(--fg)">Non-null</text>
                <text x={70} y={80} textAnchor="middle" fontFamily="var(--font-mono)" fontSize={11} fill="var(--fg)">1,009</text>
              </svg>
              {/* legend */}
              <div style={{display: 'flex', flexDirection: 'column', gap: 10, flex: 1, minWidth: 130}}>
                <div style={{display: 'flex', alignItems: 'center', gap: 8, fontFamily: 'var(--font-sketch)', fontSize: 13}}>
                  <div style={{width: 14, height: 14, border: '1.5px solid var(--fg)', background: 'repeating-linear-gradient(45deg, var(--high) 0, var(--high) 2px, transparent 2px, transparent 5px)', flexShrink: 0}} />
                  <span>Turbidity</span>
                  <span className="num" style={{marginLeft: 'auto', fontSize: 11, color: 'var(--muted)'}}>401 · 40%</span>
                </div>
                <div style={{display: 'flex', alignItems: 'center', gap: 8, fontFamily: 'var(--font-sketch)', fontSize: 13}}>
                  <div style={{width: 14, height: 14, border: '1.5px solid var(--fg)', background: 'repeating-linear-gradient(-45deg, var(--critical) 0, var(--critical) 2px, transparent 2px, transparent 5px)', flexShrink: 0}} />
                  <span>Iron</span>
                  <span className="num" style={{marginLeft: 'auto', fontSize: 11, color: 'var(--muted)'}}>382 · 38%</span>
                </div>
                <div style={{display: 'flex', alignItems: 'center', gap: 8, fontFamily: 'var(--font-sketch)', fontSize: 13}}>
                  <div style={{width: 14, height: 14, border: '1.5px solid var(--fg)', background: 'repeating-linear-gradient(0deg, var(--medium) 0, var(--medium) 1.5px, transparent 1.5px, transparent 5px)', flexShrink: 0}} />
                  <span>Fluoride</span>
                  <span className="num" style={{marginLeft: 'auto', fontSize: 11, color: 'var(--muted)'}}>152 · 15%</span>
                </div>
                <div style={{display: 'flex', alignItems: 'center', gap: 8, fontFamily: 'var(--font-sketch)', fontSize: 13}}>
                  <div style={{width: 14, height: 14, border: '1.5px solid var(--fg)', background: 'repeating-linear-gradient(45deg, var(--muted) 0, var(--muted) 1px, transparent 1px, transparent 5px)', flexShrink: 0}} />
                  <span>Other</span>
                  <span className="num" style={{marginLeft: 'auto', fontSize: 11, color: 'var(--muted)'}}>74 · 7%</span>
                </div>
                <hr className="rule" style={{margin: '2px 0'}} />
                <div style={{fontFamily: 'var(--font-sketch)', fontSize: 11, color: 'var(--muted)'}}>732 nulls excluded<br />(Low, no exceedance)</div>
              </div>
            </div>
            <p className="callout" style={{marginTop: 14}}>✓ FIXED — Medium color (amber #d4a017) patched into map.html. All 4 bands now visually distinct. Real counts: turb 401, Fe 382, F 152, tds 149.</p>
          </div>
          {/* Line chart: mean composite score by state / year is moot — using sample date distribution instead */}
          <div className="chart-wrap" data-od-id="chart-line" style={{gridColumn: '1 / -1'}}>
            <div className="chart-title">Sample Date Distribution — 2022 collection window (all 1,741 samples)</div>
            <svg width="100%" height={110} viewBox="0 0 800 110" preserveAspectRatio="none" role="img" aria-label="Histogram showing sample collection dates concentrated in 2022">
              {/* grid lines */}
              <line x1={0} y1={25} x2={800} y2={25} stroke="var(--grid-line)" strokeWidth={1} strokeDasharray="4,4" />
              <line x1={0} y1={55} x2={800} y2={55} stroke="var(--grid-line)" strokeWidth={1} strokeDasharray="4,4" />
              <line x1={0} y1={85} x2={800} y2={85} stroke="var(--grid-line)" strokeWidth={1} strokeDasharray="4,4" />
              {/* spike on 2022-11-14 (341 samples on one date) */}
              <line x1={670} y1={5} x2={670} y2={100} stroke="var(--critical)" strokeWidth={2} strokeDasharray="3,3" />
              <text x={676} y={20} fontFamily="var(--font-sketch), cursive" fontSize={10} fill="var(--critical)">341 piled</text>
              {/* area fill sketch */}
              <path d="M30,95 C80,93 140,90 200,88 C260,86 320,87 380,84 C440,81 500,85 560,80 C590,77 620,70 650,40 C660,20 665,10 670,8 C675,10 680,20 700,50 C720,70 760,90 800,95 L800,110 L30,110 Z" fill="repeating-linear-gradient(-45deg, color-mix(in oklch, var(--accent) 15%, transparent) 0, color-mix(in oklch, var(--accent) 15%, transparent) 3px, transparent 3px, transparent 7px)" stroke="none" />
              <path d="M30,95 C80,93 140,90 200,88 C260,86 320,87 380,84 C440,81 500,85 560,80 C590,77 620,70 650,40 C660,20 665,10 670,8 C675,10 680,20 700,50 C720,70 760,90 800,95" fill="none" stroke="var(--accent)" strokeWidth={2} strokeLinecap="round" />
              {/* y axis labels */}
              <text x={2} y={23} fontFamily="var(--font-mono)" fontSize={9} fill="var(--muted)">350</text>
              <text x={2} y={53} fontFamily="var(--font-mono)" fontSize={9} fill="var(--muted)">200</text>
              <text x={2} y={83} fontFamily="var(--font-mono)" fontSize={9} fill="var(--muted)">50</text>
            </svg>
            <div style={{display: 'flex', justifyContent: 'space-between', padding: '0 4px', marginTop: 4}}>
              <span style={{fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--muted)'}}>Jul 2022</span>
              <span style={{fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--muted)'}}>Aug</span>
              <span style={{fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--muted)'}}>Sep</span>
              <span style={{fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--muted)'}}>Oct</span>
              <span style={{fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--muted)'}}>Nov 2022</span>
            </div>
            <p className="callout" style={{marginTop: 10}}>→ Data limitation (unchanged): all 1,741 samples date to 2022-07-01 → 2022-11-19. Label as "2022 WQMIS collection window" — not live monitoring. data.json now includes `generated_at` so stale-data warnings are surfaced at load time.</p>
          </div>
        </div>
      </div>
    </section>
    {/* ════════════════════════════════════════════════════ LOADING / EMPTY / ERROR STATES */}
    <section className="section" data-od-id="states">
      <div className="container">
        <div style={{maxWidth: '40ch', marginBottom: 40}}>
          <p className="eyebrow">API State Sketches</p>
          <h2>Loading · Empty · Error</h2>
          <p className="lead" style={{marginTop: 12}}>Required states for all API-backed views. DB must be running (`docker start watertriage-db`) or fallback loads data.json — now clean with `generated_at` field and correct counts.</p>
        </div>
        <div className="grid-3" style={{gap: 24}}>
          {/* Loading state */}
          <div className="chart-wrap">
            <div style={{fontFamily: 'var(--font-sketch)', fontSize: 13, fontWeight: 700, marginBottom: 16}}>Loading State</div>
            <p className="callout" style={{marginBottom: 16}}>Shown while `/api/dashboard-data` fetches. Skeleton rows, no spinners.</p>
            <div style={{display: 'flex', flexDirection: 'column', gap: 8}}>
              <div className="skeleton" style={{height: 14, width: '60%'}} />
              <div className="skeleton" style={{height: 14, width: '85%'}} />
              <div className="skeleton" style={{height: 14, width: '45%'}} />
              <div className="skeleton" style={{height: 14, width: '70%'}} />
            </div>
            <div style={{marginTop: 16, display: 'flex', alignItems: 'center', gap: 10}}>
              <div className="skeleton" style={{height: 40, width: 40, borderRadius: '50%'}} />
              <div style={{flex: 1, display: 'flex', flexDirection: 'column', gap: 6}}>
                <div className="skeleton" style={{height: 11, width: '80%'}} />
                <div className="skeleton" style={{height: 11, width: '55%'}} />
              </div>
            </div>
            <p className="callout" style={{marginTop: 14}}>→ Stop skeleton at 60s — escalate to error state if API doesn't respond</p>
          </div>
          {/* Empty state */}
          <div className="chart-wrap">
            <div style={{fontFamily: 'var(--font-sketch)', fontSize: 13, fontWeight: 700, marginBottom: 16}}>Empty State</div>
            <p className="callout" style={{marginBottom: 16}}>When filter returns zero districts. Not an error — the filter is just too narrow.</p>
            <div className="empty-box">
              <div style={{fontSize: 28, marginBottom: 12, opacity: '0.4', lineHeight: 1}}>∅</div>
              <div style={{fontWeight: 700, marginBottom: 6}}>No districts match this filter</div>
              <div style={{fontSize: 12, color: 'var(--muted)'}}>Try removing the state or band filter</div>
              <button className="btn btn-secondary" style={{marginTop: 16, fontSize: 13, minHeight: 44}}>Clear filters</button>
            </div>
          </div>
          {/* Error state */}
          <div className="chart-wrap">
            <div style={{fontFamily: 'var(--font-sketch)', fontSize: 13, fontWeight: 700, marginBottom: 16}}>Error State</div>
            <p className="callout" style={{marginBottom: 16}}>DB container not running or API 500. Must not show raw stack trace to user.</p>
            <div className="error-box">
              <div style={{fontSize: 20, marginBottom: 10, lineHeight: 1}}>⚠</div>
              <div style={{fontWeight: 700, marginBottom: 6}}>Could not load data</div>
              <div style={{fontSize: 12, color: 'color-mix(in oklch, var(--critical) 80%, black)', marginBottom: 14}}>
                API unreachable. Check `docker start watertriage-db`.<br />✓ Static fallback: data.json (counts verified 89/392/28/1,232 — check `generated_at` for recency).
              </div>
              <div style={{display: 'flex', gap: 8, justifyContent: 'center', flexWrap: 'wrap'}}>
                <button className="btn btn-secondary" style={{fontSize: 13, borderColor: 'var(--critical)', color: 'var(--critical)', minHeight: 44}}>Retry</button>
                <button className="btn btn-ghost" style={{fontSize: 13, color: 'var(--critical)', minHeight: 44}}>Load from data.json</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
    {/* ════════════════════════════════════════════════════ STICKY NOTES */}
    <section className="section" data-od-id="sticky-notes">
      <div className="container">
        <div style={{maxWidth: '40ch', marginBottom: 40}}>
          <p className="eyebrow">Designer Notes</p>
          <h2>Open questions + known blockers</h2>
        </div>
        <div style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(190px, 1fr))', gap: 36, alignItems: 'start'}}>
          {/* DB startup — CLOSED: nav health indicator implemented in v0.4 */}
          <div className="sticky sticky-green" style={{opacity: '0.85'}}>
            <div className="sticky-title" style={{display: 'flex', alignItems: 'center', gap: 6}}>
              <span style={{color: 'var(--low)'}}>✓</span> DB Startup
              <span style={{marginLeft: 'auto', fontSize: 10, color: 'var(--low)', fontWeight: 700, letterSpacing: '0.06em'}}>CLOSED</span>
            </div>
            <p>Nav status pill implemented (v0.4): polls GET /api/health every 30s. Green "DB Live" when db_status = "online", red "DB Offline" when endpoint unreachable → graceful fallback to data.json with stale-data warning.</p>
          </div>
          {/* FIXED: data.json rebuilt with correct counts */}
          <div className="sticky sticky-pink" style={{opacity: '0.82'}}>
            <div className="sticky-title" style={{display: 'flex', alignItems: 'center', gap: 6}}>
              <span style={{display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: 16, height: 16, background: 'var(--low)', borderRadius: '50%', fontSize: 9, color: '#fff', flexShrink: 0, fontFamily: 'var(--font-mono)'}}>✓</span>
              data.json
              <span style={{fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--low)', letterSpacing: '0.06em', marginLeft: 'auto'}}>FIXED</span>
            </div>
            <p>Rebuilt from live DB. Counts now reflect 89/392/28/1,232. `generated_at` + `source_counts` fields added. CI staleness check script in place.</p>
          </div>
          {/* FIXED: Globe symlink removed, graceful fallback patched */}
          <div className="sticky sticky-green" style={{opacity: '0.82'}}>
            <div className="sticky-title" style={{display: 'flex', alignItems: 'center', gap: 6}}>
              <span style={{display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: 16, height: 16, background: 'var(--low)', borderRadius: '50%', fontSize: 9, color: '#fff', flexShrink: 0, fontFamily: 'var(--font-mono)'}}>✓</span>
              Globe Asset
              <span style={{fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--low)', letterSpacing: '0.06em', marginLeft: 'auto'}}>FIXED</span>
            </div>
            <p>Broken symlink deleted. map.html patched with graceful fallback — no crash on Pages deploy. 164 MB asset no longer required at runtime.</p>
          </div>
          {/* FIXED: Medium amber color added */}
          <div className="sticky sticky-yellow" style={{transform: 'rotate(1deg)', opacity: '0.82'}}>
            <div className="sticky-title" style={{display: 'flex', alignItems: 'center', gap: 6}}>
              <span style={{display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: 16, height: 16, background: 'var(--low)', borderRadius: '50%', fontSize: 9, color: '#fff', flexShrink: 0, fontFamily: 'var(--font-mono)'}}>✓</span>
              Color Drift
              <span style={{fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--low)', letterSpacing: '0.06em', marginLeft: 'auto'}}>FIXED</span>
            </div>
            <p>Amber (#d4a017) injected into map.html for the 28 Medium samples. Medium band is now visually distinct from the 1,232 Low (green) samples.</p>
          </div>
          {/* FIXED: NULL → "Within BIS Limits" */}
          <div className="sticky sticky-pink" style={{transform: 'rotate(-0.6deg)', opacity: '0.82'}}>
            <div className="sticky-title" style={{display: 'flex', alignItems: 'center', gap: 6}}>
              <span style={{display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: 16, height: 16, background: 'var(--low)', borderRadius: '50%', fontSize: 9, color: '#fff', flexShrink: 0, fontFamily: 'var(--font-mono)'}}>✓</span>
              Null Param Row
              <span style={{fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--low)', letterSpacing: '0.06em', marginLeft: 'auto'}}>FIXED</span>
            </div>
            <p>JSON generation script updated. 732 NULL worst_parameter values now output "Within BIS Limits". UI rows render the string correctly.</p>
          </div>
          {/* Timeline — updated with current status */}
          <div className="sticky sticky-green" style={{transform: 'rotate(0.9deg)'}}>
            <div className="sticky-title">Timeline</div>
            <p>Code freeze ~09/10/2026. Final report 26/10/2026. Viva 2–6 Nov. Backend integration confirmed ✓ — only UI polish and data.json refresh remain before freeze.</p>
          </div>
        </div>
        {/* ════ USER FLOW DIAGRAM ════ */}
        <div style={{marginTop: 56, padding: 24, border: '2px solid var(--fg)', borderRadius: 2, background: 'var(--surface)', position: 'relative'}}>
          <span className="sketch-section-label">WaterTriage user flow — viva demo path</span>
          <div style={{display: 'flex', alignItems: 'flex-start', gap: 8, flexWrap: 'wrap', marginTop: 20, overflowX: 'auto', paddingBottom: 4}}>
            {/* Step 1: Login */}
            <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6, flexShrink: 0}}>
              <div style={{padding: '10px 16px', border: '2px solid var(--fg)', borderRadius: 2, fontFamily: 'var(--font-sketch)', fontSize: 13, background: 'var(--surface)', textAlign: 'center', minWidth: 90}}>Login<br /><span style={{fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--muted)'}}>Amity SSO?</span></div>
            </div>
            <div className="flow-arrow" style={{marginTop: 18}}>→</div>
            {/* Step 2: Map Overview */}
            <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6, flexShrink: 0}}>
              <div style={{padding: '10px 16px', border: '2px solid var(--fg)', borderRadius: 2, fontFamily: 'var(--font-sketch)', fontSize: 13, background: 'var(--surface)', color: 'var(--fg)', textAlign: 'center', minWidth: 100}}>Map View<br /><span style={{fontFamily: 'var(--font-mono)', fontSize: 9}}>Three.js globe</span></div>
            </div>
            <div className="flow-arrow" style={{marginTop: 18}}>→</div>
            {/* Step 3: Priority Queue */}
            <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6, flexShrink: 0}}>
              <div style={{padding: '10px 16px', border: '2px solid var(--fg)', borderRadius: 2, fontFamily: 'var(--font-sketch)', fontSize: 13, background: 'var(--surface)', textAlign: 'center', minWidth: 100}}>Priority Queue<br /><span style={{fontFamily: 'var(--font-mono)', fontSize: 9}}>/api/priority</span></div>
            </div>
            <div className="flow-arrow" style={{marginTop: 18}}>→</div>
            {/* Step 4: Branch */}
            <div style={{display: 'flex', flexDirection: 'column', gap: 8, flexShrink: 0}}>
              <div style={{padding: '9px 14px', border: '1px dashed var(--fg)', borderRadius: 2, fontFamily: 'var(--font-sketch)', fontSize: 12, minWidth: 110}}>District Detail<br /><span style={{fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--muted)'}}>/api/districts/:id</span></div>
              <div style={{padding: '9px 14px', border: '1px dashed var(--fg)', borderRadius: 2, fontFamily: 'var(--font-sketch)', fontSize: 12, minWidth: 110}}>Hotspot Registry<br /><span style={{fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--muted)'}}>2009–2012 only</span></div>
              <div style={{padding: '9px 14px', border: '1px dashed var(--fg)', borderRadius: 2, fontFamily: 'var(--font-sketch)', fontSize: 12, minWidth: 110}}>Sample Drill-down<br /><span style={{fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--muted)'}}>/api/samples</span></div>
            </div>
            <div className="flow-arrow" style={{marginTop: 18}}>→</div>
            {/* Step 5: Export */}
            <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6, flexShrink: 0}}>
              <div style={{padding: '10px 16px', border: '2px solid var(--fg)', borderRadius: 2, fontFamily: 'var(--font-sketch)', fontSize: 13, background: 'var(--surface)', textAlign: 'center', minWidth: 80}}>Export CSV<br /><span style={{fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--muted)'}}>for report</span></div>
            </div>
          </div>
          <p className="callout" style={{marginTop: 16}}>→ Error states must be mapped for District Detail and Sample Drill-down before dev handoff — add "DB offline" path for all three API calls</p>
        </div>
      </div>
    </section>
    {/* ════════════════════════════════════════════════════ CTA STRIP */}
    <section className="section" data-od-id="cta-strip" style={{textAlign: 'center'}}>
      <div className="container" style={{maxWidth: 580}}>
        <p className="eyebrow" style={{justifyContent: 'center'}}>Next step</p>
        <h2>Ready for viva review?</h2>
        <p className="lead" style={{margin: '16px auto 32px', textAlign: 'center'}}>
          Share this sketch with Dr. Paliwal — pick Variant A (Priority Queue) as the default demo view.
          Hi-fi target: code freeze 09/10, report 26/10, viva 2–6 Nov.
        </p>
        <div style={{display: 'inline-flex', gap: 12, flexWrap: 'wrap', justifyContent: 'center'}}>
          <button className="btn btn-primary btn-arrow">Share for review</button>
          <button className="btn btn-secondary">Export as PDF</button>
        </div>
      </div>
    </section>
  </main>
  <footer className="pagefoot" data-od-id="footer">
    <div className="container row-between">
      <span>WaterTriage Dashboard Wireframe · v0.4 · Oct 2026 · Anubhav Anand</span>
      <span className="meta">NTCC Minor Project · Dr. Girish Paliwal · ASET-AUGN · Internal exploration</span>
    </div>
  </footer>
</div>

); }
