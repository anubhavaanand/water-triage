<script>
    let { navigate } = $props();
    let meta = $state(null);

    $effect(() => {
        fetch('/api/meta')
            .then(r => r.ok ? r.json() : Promise.reject())
            .catch(() => fetch(`${import.meta.env.BASE_URL}meta.json`).then(r => r.json()))
            .then(data => meta = data)
            .catch(err => console.error(err));
    });
</script>

<div class="section" style="padding-top: 0;">
  <div class="container">
    <header class="row-between" style="margin-bottom: var(--gap-xl); padding-bottom: var(--gap-lg); border-bottom: 2px solid var(--color-fg);">
      <h1 class="h1">Methodology</h1>
      <button class="btn btn-ghost btn-arrow" onclick={() => navigate('a')}>Back to Queue</button>
    </header>

    <div class="grid-2" style="margin-bottom: var(--gap-xl);">
      <div class="sketch-box">
        <h2 class="h3" style="margin-bottom: var(--gap-sm); border-bottom: 1px dashed var(--color-border); padding-bottom: var(--gap-sm); color: var(--color-accent);">
          BIS IS 10500 Scoring Model
        </h2>
        <p class="lead" style="margin-bottom: var(--gap-md); font-size: 14px;">The core algorithmic engine derives its severity model from the Bureau of Indian Standards (BIS IS 10500). Parameters are heavily weighted based on acute physiological hazard.</p>
        <div class="sketch-box" style="padding: 16px;">
          <ul style="font-family: var(--font-sketch); font-size: 13px; line-height: 2.2; list-style: none; padding: 0; margin: 0;">
            <li style="display: flex; justify-content: space-between; border-bottom: 1px dashed var(--color-border); padding-bottom: 8px;">
              <span>Arsenic</span>
              <span style="font-family: var(--font-mono); font-weight: 700; color: var(--color-critical);">1.0</span>
            </li>
            <li style="display: flex; justify-content: space-between; border-bottom: 1px dashed var(--color-border); padding-bottom: 8px;">
              <span>E. coli</span>
              <span style="font-family: var(--font-mono); font-weight: 700; color: var(--color-critical);">0.9</span>
            </li>
            <li style="display: flex; justify-content: space-between; border-bottom: 1px dashed var(--color-border); padding-bottom: 8px;">
              <span>Fluoride</span>
              <span style="font-family: var(--font-mono); font-weight: 700; color: var(--color-fg);">0.8</span>
            </li>
            <li style="display: flex; justify-content: space-between; border-bottom: 1px dashed var(--color-border); padding-bottom: 8px;">
              <span>Nitrate</span>
              <span style="font-family: var(--font-mono); font-weight: 700; color: var(--color-fg);">0.7</span>
            </li>
            <li style="display: flex; justify-content: space-between; border-bottom: 1px dashed var(--color-border); padding-bottom: 8px;">
              <span>Iron</span>
              <span style="font-family: var(--font-mono); font-weight: 700; color: var(--color-fg);">0.4</span>
            </li>
            <li style="display: flex; justify-content: space-between; border-bottom: 1px dashed var(--color-border); padding-bottom: 8px;">
              <span>Turbidity / TDS</span>
              <span style="font-family: var(--font-mono); font-weight: 700; color: var(--color-muted);">0.3</span>
            </li>
            <li style="display: flex; justify-content: space-between;">
              <span>pH</span>
              <span style="font-family: var(--font-mono); font-weight: 700; color: var(--color-muted);">0.2</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="sketch-box">
        <h2 class="h3" style="margin-bottom: var(--gap-sm); border-bottom: 1px dashed var(--color-border); padding-bottom: var(--gap-sm);">
          Data Acquisition & Pipeline
        </h2>
        <p class="lead" style="margin-bottom: var(--gap-md); font-size: 14px;">The backend relies on a highly-optimized WQMIS crawler extracting live water quality laboratory reports across Uttar Pradesh and Bihar.</p>
        <div class="sketch-box" style="padding: 24px; text-align: center;">
          <div class="stat">
            <span class="stat-num" style="color: var(--color-fg);">90,000+</span>
            <div class="stat-label" style="font-family: var(--font-mono); text-transform: uppercase; letter-spacing: 0.1em; font-size: 10px;">Projected Sample Capacity</div>
          </div>
          <div class="measure-line" style="margin: var(--gap-md) 0;"></div>
          <div style="font-family: var(--font-sketch); font-size: 12px; line-height: 2; color: var(--color-muted); text-align: left;">
            <div>▹ Continuous range enumeration across 1.5M IDs</div>
            <div>▹ Exponential backoff & throttling protocols</div>
            <div>▹ PostgreSQL district-level aggregation</div>
          </div>
        </div>
      </div>
    </div>

    {#if meta && meta.limitations}
      <h2 class="h2" style="margin-bottom: var(--gap-lg); border-bottom: 1px dashed var(--color-border); padding-bottom: var(--gap-sm);">
        Known Limitations
      </h2>
      <div class="grid-2">
        {#each meta.limitations as lim}
          <div class="sketch-box">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: var(--gap-sm);">
              <h3 class="h3" style="font-size: 16px;">{lim.title}</h3>
              <span class="pill" style="font-size: 8px; {lim.status === 'open' ? 'color: var(--color-critical); border-color: var(--color-critical); background: color-mix(in oklch, var(--color-critical) 14%, transparent);' : 'color: var(--color-low); border-color: var(--color-low); background: color-mix(in oklch, var(--color-low) 14%, transparent);'}">
                {lim.status.toUpperCase()}
              </span>
            </div>
            <p style="font-family: var(--font-sketch); font-size: 12px; line-height: 1.6; color: var(--color-muted);">{lim.detail}</p>
          </div>
        {/each}
      </div>
    {/if}
  </div>
</div>