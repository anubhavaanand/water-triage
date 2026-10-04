<div aria-labelledby="tab-c" class="tab-panel active" data-note="← master-detail: district list left, sample drill-down right — good for viva Q&amp;A" id="tab-panel-c" role="tabpanel">
<div class="callout" style="margin-bottom: 20px;">Split panel: left = district master list (sortable), right = sample-level drill-down. Keyboard navigable for live demo.</div>
<div style="display: grid; grid-template-columns: 1fr 1.6fr; gap: 0; border: 2px solid var(--fg);">
<!-- master list -->
<div style="border-right: 2px solid var(--fg);">
<div style="padding: 10px 14px; border-bottom: 1px dashed var(--border); background: var(--fg-soft); font-family: var(--font-mono); font-size: 10px; letter-spacing: 0.08em; text-transform: uppercase; color: var(--muted);">Districts (47)</div>
<div style="display: flex; flex-direction: column;">
<div style="padding: 11px 14px; border-bottom: 1px dashed var(--border); font-family: var(--font-sketch); font-size: 13px; color: var(--muted); display: flex; justify-content: space-between;"><span>Katihar, Bihar</span><span class="badge badge-critical">82.4</span></div>
<div style="padding: 11px 14px; border-bottom: 1px dashed var(--border); background: var(--accent-soft); border-left: 3px solid var(--accent); font-family: var(--font-sketch); font-size: 13px; color: var(--fg); display: flex; justify-content: space-between;"><span>Unnao, UP ← selected</span><span class="badge badge-high">68.3</span></div>
<div style="padding: 11px 14px; border-bottom: 1px dashed var(--border); font-family: var(--font-sketch); font-size: 13px; color: var(--muted); display: flex; justify-content: space-between;"><span>Ferozabad, UP</span><span class="badge badge-high">61.7</span></div>
<div style="padding: 11px 14px; border-bottom: 1px dashed var(--border); font-family: var(--font-sketch); font-size: 13px; color: var(--muted); display: flex; justify-content: space-between;"><span>Muzaffarpur, Bihar</span><span class="badge badge-high">59.2</span></div>
<div style="padding: 11px 14px; font-family: var(--font-sketch); font-size: 13px; color: var(--muted); display: flex; justify-content: space-between;"><span>Saharanpur, UP</span><span class="badge badge-medium">42.1</span></div>
</div>
</div>
<!-- detail pane -->
<div style="padding: 20px;">
<div style="font-family: var(--font-sketch); font-size: 18px; font-weight: 700; margin-bottom: 6px;">Unnao, Uttar Pradesh</div>
<div style="display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 16px;">
<span class="badge badge-high">Score: 68.3</span>
<span class="tag">37 samples</span>
<span class="tag">Worst: Fluoride</span>
</div>
<!-- parameter mini-bars -->
<!-- ── Pathogen Override alert — appears when ecoli_positive = true for any sample in this district ── -->
<div style="border: 2px dashed var(--critical); border-radius: 2px; padding: 10px 14px; background: color-mix(in oklch, var(--critical) 7%, transparent); margin-bottom: 14px; display: flex; gap: 10px; align-items: flex-start;">
<span aria-label="Pathogen override active" class="badge-pathogen" style="flex-shrink:0; margin-top:1px;">
<svg aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8" style="width:10px;height:10px;" viewbox="0 0 20 20">
<circle cx="10" cy="10" r="2.5"></circle>
<path d="M10 7.5 C10 4 6 2 4 5 C2.5 7 4 9.5 7 10"></path>
<path d="M10 7.5 C13 4 17 5.5 16 9 C15 11.5 12 11.5 10 10"></path>
<path d="M7 10 C4 11 3 14.5 6 15.5 C8.5 16.5 10.5 14 10 12.5"></path>
<path d="M10 12.5 C10.5 14 13 16 15 14.5 C17 13 15.5 10 13 10"></path>
<path d="M13 10 C15.5 9.5 17 6.5 15 5"></path>
</svg>
                    Pathogen Override
                  </span>
<div style="font-family: var(--font-sketch); font-size: 12px; color: var(--critical); line-height: 1.4;">
<strong>E. coli positive</strong> detected in 2 of 37 samples.<br/>
<span style="color: var(--muted);">Math score: <span style="text-decoration:line-through;">20.0</span> → Band forced to <strong style="color:var(--critical);">Critical</strong> by pathogen override rule.</span>
</div>
</div>
<div style="display: grid; gap: 8px; margin-bottom: 16px;">
<div>
<div style="display:flex; justify-content:space-between; font-family:var(--font-mono); font-size:10px; color:var(--muted); margin-bottom:3px;"><span>Fluoride (avg 2.4 mg/L · BIS: 1.0)</span><span>Sev 0.82</span></div>
<div class="prog-track"><div class="prog-fill" style="width: 82%;"></div></div>
</div>
<div>
<div style="display:flex; justify-content:space-between; font-family:var(--font-mono); font-size:10px; color:var(--muted); margin-bottom:3px;"><span>Turbidity (avg 4.1 NTU · BIS: 1.0)</span><span>Sev 0.41</span></div>
<div class="prog-track"><div class="prog-fill" style="width: 41%;"></div></div>
</div>
<div>
<div style="display:flex; justify-content:space-between; font-family:var(--font-mono); font-size:10px; color:var(--muted); margin-bottom:3px;"><span>pH (avg 7.6 · BIS: 6.5–8.5)</span><span>Sev 0.14</span></div>
<div class="prog-track"><div class="prog-fill" style="width: 14%;"></div></div>
</div>
</div>
<div class="hatch-box" style="height: 64px; display:grid; place-items:center; font-family:var(--font-sketch); font-size:11px; color:var(--muted); margin-bottom:14px;">[ Sample-level table · 37 rows → /api/samples?district=unnao ]</div>
<div style="display: flex; gap: 10px; flex-wrap: wrap;">
<button class="btn btn-primary">View all samples</button>
<button class="btn btn-secondary">Export district CSV</button>
</div>
</div>
</div>
<p class="callout" style="margin-top: 12px;">→ Saharanpur case-normalisation needed: "Saharanpur" vs "SAHARANPUR" is the exact defect D3 mismatch (32 shared districts)</p>
</div>