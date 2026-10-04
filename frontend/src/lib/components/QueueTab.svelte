<div aria-labelledby="tab-a" class="tab-panel active" data-note="← list-dominant: sidebar nav + sortable district rows — optimal for viva demo" id="tab-panel-a" role="tabpanel">
<div class="grid-2-1">
<!-- main list -->
<div>
<div class="callout" style="margin-bottom: 16px;">Sortable district table: risk score descending, filter by state / band / contaminant parameter.</div>
<!-- table header -->
<div style="display: grid; grid-template-columns: 1fr 80px 90px 80px 80px; gap: 8px; padding: 8px 14px; border: 1px dashed var(--border); background: var(--fg-soft); font-family: var(--font-mono); font-size: 10px; letter-spacing: 0.07em; text-transform: uppercase; color: var(--muted); border-radius: 2px 2px 0 0;">
<span>District</span><span style="text-align:right">Score</span><span style="text-align:center">Band</span><span style="text-align:right">Samples</span><span>Worst Param</span>
</div>
<!-- row 1 — critical -->
<div style="display: grid; grid-template-columns: 1fr 80px 90px 80px 80px; gap: 8px; align-items: center; padding: 11px 14px; border: 2px solid var(--critical); border-top: none; background: color-mix(in oklch, var(--critical) 6%, transparent);">
<span style="font-family: var(--font-sketch); font-size: 14px;">Katihar, Bihar</span>
<span class="num" style="text-align:right; color: var(--critical);">82.4</span>
<span style="text-align:center;"><span class="badge badge-critical">Critical</span></span>
<span class="num" style="text-align:right; color: var(--muted);">24</span>
<span class="tag" style="font-size:11px;">Iron</span>
</div>
<!-- row 2 — critical -->
<div style="display: grid; grid-template-columns: 1fr 80px 90px 80px 80px; gap: 8px; align-items: center; padding: 11px 14px; border: 1px dashed var(--border); border-top: none; background: var(--surface);">
<span style="font-family: var(--font-sketch); font-size: 14px;">Purnia, Bihar</span>
<span class="num" style="text-align:right; color: var(--critical);">79.1</span>
<span style="text-align:center;"><span class="badge badge-critical">Critical</span></span>
<span class="num" style="text-align:right; color: var(--muted);">18</span>
<span class="tag" style="font-size:11px;">Iron</span>
</div>
<!-- row 2b — PATHOGEN OVERRIDE: low math score but E.coli positive → forced Critical -->
<div aria-label="Pathogen override row" style="display: grid; grid-template-columns: 1fr 80px 90px 80px 80px; gap: 8px; align-items: center; padding: 11px 14px; border: 2px dashed var(--critical); border-top: none; background: color-mix(in oklch, var(--critical) 7%, transparent);">
<span style="font-family: var(--font-sketch); font-size: 14px; display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
                    Gopalganj, Bihar
                    <!-- biohazard badge with tooltip -->
<span class="has-tooltip" style="display:inline-block;">
<span aria-label="Pathogen override: E. coli detected, score overridden to Critical" class="badge-pathogen" role="img">
<!-- biohazard icon (simplified SVG) -->
<svg aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8" viewbox="0 0 20 20">
<circle cx="10" cy="10" r="2.5"></circle>
<path d="M10 7.5 C10 4 6 2 4 5 C2.5 7 4 9.5 7 10"></path>
<path d="M10 7.5 C13 4 17 5.5 16 9 C15 11.5 12 11.5 10 10"></path>
<path d="M7 10 C4 11 3 14.5 6 15.5 C8.5 16.5 10.5 14 10 12.5"></path>
<path d="M10 12.5 C10.5 14 13 16 15 14.5 C17 13 15.5 10 13 10"></path>
<path d="M13 10 C15.5 9.5 17 6.5 15 5"></path>
</svg>
                        Pathogen Override
                      </span>
<span class="tooltip">E. coli detected (test positive).<br/>Math score was 20.0 → Low, but backend overrides band to <strong>Critical</strong> via pathogen flag. Score shown is overridden composite.</span>
</span>
</span>
<span class="num" style="text-align:right; color: var(--critical); display:flex; align-items:center; gap:4px; justify-content:flex-end;">
<span style="text-decoration: line-through; color: var(--muted); font-size:10px;">20.0</span>
<span>—</span>
</span>
<span style="text-align:center;"><span class="badge badge-critical">Critical</span></span>
<span class="num" style="text-align:right; color: var(--muted);">9</span>
<span class="tag" style="font-size:11px; color: var(--critical); border-color: var(--critical);">E. coli</span>
</div>
<!-- row 3 — high (active selection) -->
<div style="display: grid; grid-template-columns: 1fr 80px 90px 80px 80px; gap: 8px; align-items: center; padding: 11px 14px; border: 2px solid var(--accent); border-top: none; background: var(--accent-soft);">
<span style="font-family: var(--font-sketch); font-size: 14px; color: var(--accent);">Unnao, UP ← selected</span>
<span class="num" style="text-align:right; color: var(--high);">68.3</span>
<span style="text-align:center;"><span class="badge badge-high">High</span></span>
<span class="num" style="text-align:right; color: var(--muted);">37</span>
<span class="tag" style="font-size:11px;">Fluoride</span>
</div>
<!-- row 4 -->
<div style="display: grid; grid-template-columns: 1fr 80px 90px 80px 80px; gap: 8px; align-items: center; padding: 11px 14px; border: 1px dashed var(--border); border-top: none; background: var(--surface);">
<span style="font-family: var(--font-sketch); font-size: 14px;">Ferozabad, UP</span>
<span class="num" style="text-align:right; color: var(--high);">61.7</span>
<span style="text-align:center;"><span class="badge badge-high">High</span></span>
<span class="num" style="text-align:right; color: var(--muted);">29</span>
<span class="tag" style="font-size:11px;">Fluoride</span>
</div>
<!-- row 5 — null worst_param note -->
<div style="display: grid; grid-template-columns: 1fr 80px 90px 80px 80px; gap: 8px; align-items: center; padding: 11px 14px; border: 1px dashed var(--border); border-top: none; background: var(--surface);">
<span style="font-family: var(--font-sketch); font-size: 14px;">Ballia, UP</span>
<span class="num" style="text-align:right; color: var(--low);">12.0</span>
<span style="text-align:center;"><span class="badge badge-low">Low</span></span>
<span class="num" style="text-align:right; color: var(--muted);">41</span>
<span style="font-family:var(--font-sketch); font-size:11px; color: var(--muted);">within limits</span>
</div>
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