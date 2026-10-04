<script>
  import { onMount } from 'svelte';
  
  let priorityList = [];
  let kpi = {};
  let loading = true;
  let error = null;

  onMount(async () => {
    try {
      const res = await fetch('/data.json');
      if (res.ok) {
        const data = await res.json();
        priorityList = data.priority || [];
        kpi = data.kpi || {};
      } else {
        error = 'Failed to load data.json';
      }
    } catch (e) {
      error = e.message;
    } finally {
      loading = false;
    }
  });

  function getBandColor(band) {
    if (band === 'Critical') return 'var(--critical)';
    if (band === 'High') return 'var(--high)';
    if (band === 'Medium') return 'var(--medium, #d4a017)';
    return 'var(--low)';
  }
  
  function getBgColor(band, isPathogen) {
    if (isPathogen) return 'color-mix(in oklch, var(--critical) 7%, transparent)';
    if (band === 'Critical') return 'color-mix(in oklch, var(--critical) 6%, transparent)';
    return 'var(--surface)';
  }
</script>

<div aria-labelledby="tab-a" class="tab-panel active" data-note="← list-dominant: sidebar nav + sortable district rows — optimal for viva demo" id="tab-panel-a" role="tabpanel">
<div class="grid-2-1">
<!-- main list -->
<div>
<div class="callout" style="margin-bottom: 16px;">Sortable district table: risk score descending, filter by state / band / contaminant parameter.</div>
<!-- table header -->
<div style="display: grid; grid-template-columns: 1fr 80px 90px 80px 80px; gap: 8px; padding: 8px 14px; border: 1px dashed var(--border); background: var(--fg-soft); font-family: var(--font-mono); font-size: 10px; letter-spacing: 0.07em; text-transform: uppercase; color: var(--muted); border-radius: 2px 2px 0 0;">
<span>District</span><span style="text-align:right">Score</span><span style="text-align:center">Band</span><span style="text-align:right">Samples</span><span>Worst Param</span>
</div>

      {#if loading}
        <div style="padding: 20px; text-align: center; font-family: var(--font-mono); color: var(--muted);">Loading 1,741 samples...</div>
      {:else if error}
        <div style="padding: 20px; color: var(--critical);">{error}</div>
      {:else}
        {#each priorityList.slice(0, 50) as item}
          {@const isPathogen = item.band === 'Critical' && item.worst_parameter === 'E. coli'}
          {@const bandColor = getBandColor(item.band)}
          {@const bgColor = getBgColor(item.band, isPathogen)}
          
          <div aria-label={isPathogen ? "Pathogen override row" : ""} style="display: grid; grid-template-columns: 1fr 80px 90px 80px 80px; gap: 8px; align-items: center; padding: 11px 14px; border: {isPathogen ? '2px dashed var(--critical)' : '1px dashed var(--border)'}; border-top: none; background: {bgColor};">
            
            <span style="font-family: var(--font-sketch); font-size: 14px; display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
              {item.district}, {item.state}
              {#if isPathogen}
                <span class="has-tooltip" style="display:inline-block;">
                  <span aria-label="Pathogen override: E. coli detected, score overridden to Critical" class="badge-pathogen" role="img">
                    <svg aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8" viewbox="0 0 20 20" style="width: 14px; height: 14px;">
                      <circle cx="10" cy="10" r="2.5"></circle>
                      <path d="M10 7.5 C10 4 6 2 4 5 C2.5 7 4 9.5 7 10"></path>
                      <path d="M10 7.5 C13 4 17 5.5 16 9 C15 11.5 12 11.5 10 10"></path>
                      <path d="M7 10 C4 11 3 14.5 6 15.5 C8.5 16.5 10.5 14 10 12.5"></path>
                      <path d="M10 12.5 C10.5 14 13 16 15 14.5 C17 13 15.5 10 13 10"></path>
                      <path d="M13 10 C15.5 9.5 17 6.5 15 5"></path>
                    </svg>
                    Pathogen Override
                  </span>
                  <span class="tooltip">E. coli detected (test positive).<br/>Score overridden to <strong>Critical</strong> via pathogen flag.</span>
                </span>
              {/if}
            </span>
            
            <span class="num" style="text-align:right; color: {bandColor}; {isPathogen ? 'display:flex; align-items:center; gap:4px; justify-content:flex-end;' : ''}">
              {#if isPathogen}
                <span>—</span>
              {:else}
                {item.score.toFixed(1)}
              {/if}
            </span>
            
            <span style="text-align:center;">
              <span class="badge badge-{item.band.toLowerCase()}">{item.band}</span>
            </span>
            
            <span class="num" style="text-align:right; color: var(--muted);">1</span>
            
            {#if item.worst_parameter === 'Within BIS Limits'}
              <span style="font-family:var(--font-sketch); font-size:11px; color: var(--muted);">{item.worst_parameter}</span>
            {:else}
              <span class="tag" style="font-size:11px; {isPathogen ? 'color: var(--critical); border-color: var(--critical);' : ''}">{item.worst_parameter}</span>
            {/if}
            
          </div>
        {/each}
      {/if}

<!-- pagination sketch -->
<div style="display: flex; align-items: center; justify-content: space-between; padding: 10px 14px; border: 1px dashed var(--border); border-top: none; border-radius: 0 0 2px 2px; font-family: var(--font-mono); font-size: 11px; color: var(--muted);">
<span>1–5 of 47 districts</span>
<div style="display: flex; gap: 4px;">
<button class="btn btn-ghost" disabled="" style="padding: 4px 10px; min-height: 36px; font-size: 12px;">← Prev</button>
<button class="btn btn-secondary" style="padding: 4px 10px; min-height: 36px; font-size: 12px;">Next →</button>
</div>
</div>
<p class="callout" style="margin-top: 10px;">✓ FIXED — JSON generation script updated: 732 NULL worst_parameter values now render as "Within BIS Limits".</p>
<p class="callout" style="margin-top: 8px;">→ Pathogen Override rows: dashed red border + biohazard badge + strikethrough math score. Tooltip explains override logic on hover/focus. Backend: if ecoli_positive = true, composite_band = "Critical" regardless of computed score.</p>
</div>
<!-- sidebar panel sketch -->
<div>
<div class="sketch-box" style="height: 100%;">
<span class="sketch-section-label">Filter sidebar</span>
<div style="display: flex; flex-direction: column; gap: 14px; margin-top: 12px;">
<!-- state filter -->
<div class="field">
<label>State</label>
<select aria-label="Filter by state" class="input" style="appearance: none; cursor: pointer; min-height: 44px;">
<option>All states</option>
<option>Uttar Pradesh (966)</option>
<option>Bihar (775)</option>
</select>
</div>
<!-- band filter -->
<div class="field">
<label>Risk Band</label>
<div style="display: flex; flex-direction: column; gap: 6px;">
<label style="display: flex; gap: 8px; align-items: center; font-family: var(--font-sketch); font-size: 13px; min-height: 44px;"><input checked="" style="width:16px;height:16px;" type="checkbox"/> <span class="badge badge-critical">Critical</span> 89</label>
<label style="display: flex; gap: 8px; align-items: center; font-family: var(--font-sketch); font-size: 13px; min-height: 44px;"><input checked="" style="width:16px;height:16px;" type="checkbox"/> <span class="badge badge-high">High</span> 392</label>
<label style="display: flex; gap: 8px; align-items: center; font-family: var(--font-sketch); font-size: 13px; min-height: 44px;"><input style="width:16px;height:16px;" type="checkbox"/> <span class="badge badge-medium">Medium</span> 28</label>
<label style="display: flex; gap: 8px; align-items: center; font-family: var(--font-sketch); font-size: 13px; min-height: 44px;"><input style="width:16px;height:16px;" type="checkbox"/> <span class="badge badge-low">Low</span> 1,232</label>
</div>
</div>
<hr class="rule"/>
<div class="measure-line" style="margin: 2px 0;">sidebar width</div>
<div style="font-family: var(--font-mono); font-size: 10px; color: var(--muted); text-align: center;">240px fixed</div>
</div>
</div>
</div>
</div>
</div>
