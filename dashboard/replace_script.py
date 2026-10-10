import re

with open('src/App.jsx', 'r') as f:
    content = f.read()

# Replace KPI strip
kpi_replacement = """          {/* KPI strip */}
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
          </div>"""
content = re.sub(r"          {/\* KPI strip \*/}.*?          </div>", kpi_replacement, content, flags=re.DOTALL)

# Replace Priority Queue Tab Rows (Panel A)
queue_pattern = r"(                {/\* table header \*/}.*?<span>Worst Param</span>\n                </div>).*?(                {/\* pagination sketch \*/})"
queue_header = r"\1"
queue_footer = r"\2"

queue_replacement = queue_header + """
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
""" + queue_footer

content = re.sub(queue_pattern, queue_replacement, content, flags=re.DOTALL)

# Replace Validation Tab (Panel D)
vp_pattern = r"(                  {/\* Validation Point 1 — Bihar Iron \*/}.*?<td>)\n                      <span style={{fontFamily: 'var(--font-mono)', color: 'var(--critical)'}} className=\"num\">70</span>(.*?{/\* Validation Point 2 — UP Arsenic Bahraich \*/})"
content = re.sub(vp_pattern, r"\1\n                      <span style={{fontFamily: 'var(--font-mono)', color: 'var(--critical)'}} className=\"num\">{metaData?.critical_concentration?.total_critical ?? 70}</span>\2", content, flags=re.DOTALL)

# Write back
with open('src/App.jsx', 'w') as f:
    f.write(content)
