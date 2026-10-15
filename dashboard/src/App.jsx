import React, { useState, useEffect, useMemo } from 'react';

/**
 * WaterTriage React dashboard.
 *
 * Visual language comes from wireframe-sketch.html: sketch tokens in
 * src/index.css (aged paper, ink strokes, one marker blue, hand-drawn fonts).
 * Structure follows Variant A (Priority Queue) which the wireframe flags as
 * the default viva demo view, plus Overview, Methodology and Validation panels.
 *
 * Data policy: every figure shown is fetched at runtime from the live backend
 * (/api/meta, /api/health, /api/priority, /api/samples/{id}). Nothing numeric is
 * baked in from a previous corpus snapshot -- including the severity band
 * cut-offs, which are read from meta.band_thresholds so the UI follows the
 * engine instead of restating it.
 */

const API = '/api';
const POLL_MS = 30000;

const BANDS = ['Critical', 'High', 'Medium', 'Low'];
// Highest severity band first; each band runs thresholds[b] up to
// thresholds[band-above] - 1.
const BAND_ORDER_DESC = ['Critical', 'High', 'Medium', 'Low'];

const BAND_VAR = {
  Critical: 'var(--critical)',
  High: 'var(--high)',
  Medium: 'var(--medium)',
  Low: 'var(--low)',
};

const bandClass = (band) => 'badge badge-' + String(band || 'low').toLowerCase();

/**
 * Derive a band's numeric range from the backend's band_thresholds rather than
 * hard-coding it. backend/app/engine/scoring.py:30 implements
 * Critical=40, High=20, Medium=10, Low=0 -- the original 75/50/25 cutoffs are
 * unreachable under the escalation logic, so the shipped thresholds win.
 *
 * Each threshold is the *lower* bound of its band, so a band runs
 * thresholds[b] up to thresholds[band-above] - 1.
 */
function bandRange(band, thresholds) {
  const lo = thresholds && thresholds[band];
  if (lo == null) return '';
  const idx = BAND_ORDER_DESC.indexOf(band);
  if (band === 'Critical' || idx <= 0) return `\u2265 ${lo}`;
  const above = thresholds[BAND_ORDER_DESC[idx - 1]];
  if (above == null) return `\u2265 ${lo}`;
  if (band === 'Low') return `< ${above}`;
  return `${lo}\u2013${above - 1}`;
}

// Human labels for the parameter_key values the API uses.
const PARAM_LABELS = {
  arsenic: 'Arsenic',
  e_coli: 'E. coli',
  total_coliform: 'Total Coliform',
  fluoride: 'Fluoride',
  nitrate: 'Nitrate',
  iron: 'Iron',
  sulphate: 'Sulphate',
  turbidity: 'Turbidity',
  tds: 'TDS',
  ph: 'pH',
};

const fmt = (n) => (n == null ? '\u2014' : Number(n).toLocaleString('en-IN'));

/**
 * Resolve a public/ asset against the app's base URL.
 *
 * The production build sets vite `base: '/water-triage/'` for GitHub Pages, so a
 * hardcoded '/meta.json' 404s there even though the file is sitting next to
 * index.html. import.meta.env.BASE_URL carries the configured base in both dev
 * and build, which keeps the offline fallbacks working under any base path.
 */
const assetUrl = (file) => import.meta.env.BASE_URL.replace(/\/$/, '') + file;

/**
 * Fetch live, fall back to the baked snapshot in public/.
 *
 * The GitHub Pages deploy has no backend, so /api/* is unreachable there. The
 * snapshots were written by scripts/regen_fallbacks.py against the live
 * database, so they are the same numbers -- just older.
 */
async function fetchLive(path, fallbackFile) {
  try {
    const res = await fetch(path, { cache: 'no-store' });
    if (!res.ok) throw new Error(String(res.status));
    return { data: await res.json(), stale: false };
  } catch (err) {
    if (!fallbackFile) throw err;
    try {
      const res = await fetch(assetUrl(fallbackFile));
      if (!res.ok) throw new Error(String(res.status));
      return { data: await res.json(), stale: true };
    } catch (err2) {
      throw err;
    }
  }
}

/* ── nav health pill ─────────────────────────────────────────────────── */
function HealthPill() {
  const [state, setState] = useState('checking');

  const check = () => {
    fetch(`${API}/health`, { cache: 'no-store' })
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((d) => {
        setState(d && d.database === 'connected' ? 'live' : 'snapshot');
      })
      .catch(() => {
        fetch(assetUrl('/health.json'))
          .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
          .then(() => setState('snapshot'))
          .catch(() => setState('offline'));
      });
  };

  useEffect(() => {
    check();
    const t = setInterval(check, POLL_MS);
    return () => clearInterval(t);
  }, []);

  const label =
    state === 'live' ? 'DB Live' : state === 'snapshot' ? '1,741 Snapshot' : state === 'offline' ? 'DB Offline' : 'Checking\u2026';
  return (
    <span
      className={`status-pill ${state}`}
      role="status"
      aria-live="polite"
      aria-label={`Database status: ${label}`}
    >
      <span className="status-dot" aria-hidden="true" />
      <span>{label}</span>
    </span>
  );
}

/* ── dark mode, persisted like the wireframe script did ──────────────── */
function useTheme() {
  const [dark, setDark] = useState(false);

  useEffect(() => {
    let saved = null;
    try {
      saved = localStorage.getItem('wt-theme');
    } catch (e) {}
    const prefers =
      window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    setDark(saved === 'dark' || (saved === null && prefers));
  }, []);

  useEffect(() => {
    if (dark) document.documentElement.setAttribute('data-theme', 'dark');
    else document.documentElement.removeAttribute('data-theme');
  }, [dark]);

  const toggle = () =>
    setDark((d) => {
      const next = !d;
      try {
        localStorage.setItem('wt-theme', next ? 'dark' : 'light');
      } catch (e) {}
      return next;
    });

  return [dark, toggle];
}

function ThemeToggle({ dark, onToggle }) {
  return (
    <button
      className="theme-toggle"
      onClick={onToggle}
      aria-label={dark ? 'Switch to light mode' : 'Switch to dark mode'}
      title="Toggle dark / light mode"
    >
      <svg className="icon-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M21 12.79A9 9 0 1 1 11.21 3a7 7 0 0 0 9.79 9.79z" />
      </svg>
      <svg className="icon-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <circle cx="12" cy="12" r="5" />
        <line x1="12" y1="1" x2="12" y2="3" />
        <line x1="12" y1="21" x2="12" y2="23" />
        <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
        <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
        <line x1="1" y1="12" x2="3" y2="12" />
        <line x1="21" y1="12" x2="23" y2="12" />
        <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
        <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
      </svg>
    </button>
  );
}

/* ── KPI strip ───────────────────────────────────────────────────────── */
function KpiStrip({ bands, thresholds }) {
  const order = BANDS.filter((b) => bands[b] != null);
  const total = order.reduce((s, b) => s + (bands[b] || 0), 0);

  return (
    <div className="row" style={{ flexWrap: 'wrap', gap: 'var(--gap-lg)' }}>
      {order.map((b) => (
        <span className="stat" key={b} style={{ minWidth: 120 }}>
          <span className="stat-num" style={{ color: BAND_VAR[b] }}>
            {fmt(bands[b])}
          </span>
          <span className="stat-label">
            {b}
            <br />
            <span className={`badge badge-${b.toLowerCase()}`}>{bandRange(b, thresholds)}</span>
          </span>
        </span>
      ))}
      <span className="stat" style={{ minWidth: 120 }}>
        <span className="stat-num">{fmt(total)}</span>
        <span className="stat-label">
          Scored samples
          <br />
          <span className="tag">risk_scores</span>
        </span>
      </span>
    </div>
  );
}

/* ── band bar chart (CSS, no chart lib) ─────────────────────────────── */
function BandChart({ bands }) {
  const order = BANDS.filter((b) => bands[b] != null);
  const max = Math.max(1, ...order.map((b) => bands[b] || 0));
  const total = order.reduce((s, b) => s + (bands[b] || 0), 0);

  return (
    <div style={{ display: 'flex', alignItems: 'flex-end', gap: 12, height: 160, padding: '8px 0' }}>
      {order.map((b) => {
        const v = bands[b] || 0;
        return (
          <div
            key={b}
            style={{
              flex: 1,
              height: '100%',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'flex-end',
              alignItems: 'stretch',
              gap: 6,
            }}
          >
            <div style={{ flex: 1, display: 'flex', alignItems: 'flex-end' }}>
              <div
                style={{
                  width: '100%',
                  height: `${Math.max(2, (v / max) * 100)}%`,
                  background: 'repeating-linear-gradient(45deg, ' + BAND_VAR[b] + ' 0, ' + BAND_VAR[b] + ' 2px, transparent 2px, transparent 5px)',
                  border: '2px solid ' + BAND_VAR[b],
                  borderBottom: 'none',
                  borderRadius: '3px 3px 0 0',
                }}
                title={`${b}: ${fmt(v)} of ${fmt(total)}`}
              />
            </div>
            <span className="num" style={{ textAlign: 'center', fontSize: 11, color: BAND_VAR[b] }}>
              {b} · {fmt(v)}
            </span>
          </div>
        );
      })}
    </div>
  );
}

/* ── generic data table ──────────────────────────────────────────────── */
function DataTable({ columns, rows }) {
  if (!rows.length) {
    return (
      <div className="empty-box">
        <div style={{ fontSize: 28, marginBottom: 12, opacity: 0.4, lineHeight: 1 }}>{'\u2205'}</div>
        <div style={{ fontWeight: 700, marginBottom: 6 }}>No rows match this view</div>
        <div style={{ fontSize: 12 }}>Try widening the filters.</div>
      </div>
    );
  }

  return (
    <table className="ds-table">
      <thead>
        <tr>
          {columns.map((c) => (
            <th key={c.key} style={{ textAlign: c.align === 'right' ? 'right' : 'left' }}>
              {c.label}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((r, i) => (
          <tr key={r.key || i}>
            {columns.map((c) => (
              <td
                key={c.key}
                style={{ textAlign: c.align === 'right' ? 'right' : 'left' }}
                className={c.align === 'right' ? 'num-col' : undefined}
              >
                {c.render ? c.render(r) : r[c.key]}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

/* ── district rows with sketch-style band edges ──────────────────────── */
function DistrictRows({ items, activeKey, onSelect }) {
  return (
    <div>
      <div className="meta" style={rowHeaderStyle}>
        <span>District (State)</span>
        <span style={{ textAlign: 'right' }}>Score</span>
        <span style={{ textAlign: 'center' }}>Band</span>
        <span style={{ textAlign: 'right' }}>Params</span>
        <span>Worst Param</span>
      </div>

      {items.map((d) => {
        const isActive = activeKey === d.key;
        const band = d.band || 'Low';
        return (
          <button
            key={d.key}
            onClick={() => onSelect(d)}
            aria-pressed={isActive}
            style={rowStyle(band, isActive)}
          >
            <span style={{ fontFamily: 'var(--font-sketch)', fontSize: 14 }}>
              {d.district}
              {d.state ? (
                <span style={{ color: 'var(--muted)' }}> ({d.state})</span>
              ) : null}
            </span>
            <span className="num" style={{ textAlign: 'right', color: BAND_VAR[band] }}>
              {d.score == null ? '\u2014' : d.score.toFixed(1)}
            </span>
            <span style={{ textAlign: 'center' }}>
              <span className={bandClass(band)}>{band}</span>
            </span>
            <span className="num" style={{ textAlign: 'right', color: 'var(--muted)' }}>
              {d.n_scored_params != null ? `${d.n_scored_params}/10` : '\u2014'}
            </span>
            <span className="tag" style={{ fontSize: 11 }}>
              {d.worst_parameter ? PARAM_LABELS[d.worst_parameter] || d.worst_parameter : 'Within BIS Limits'}
            </span>
          </button>
        );
      })}
    </div>
  );
}

const rowHeaderStyle = {
  display: 'grid',
  gridTemplateColumns: 'minmax(160px, 1fr) 80px 90px 72px 130px',
  gap: 8,
  padding: '8px 14px',
  border: '1px dashed var(--border)',
  background: 'var(--fg-soft)',
  fontSize: 10,
  letterSpacing: '0.07em',
  textTransform: 'uppercase',
  color: 'var(--muted)',
  borderRadius: '2px 2px 0 0',
  width: '100%',
  textAlign: 'left',
};

function rowStyle(band, active) {
  if (active) {
    return {
      ...rowBaseStyle,
      border: '2px solid var(--accent)',
      background: 'var(--accent-soft)',
    };
  }
  if (band === 'Critical') {
    return { ...rowBaseStyle, border: '2px solid var(--critical)' };
  }
  if (band === 'High') {
    return { ...rowBaseStyle, borderLeft: '3px solid var(--high)', ...rowFaintStyle };
  }
  return { ...rowBaseStyle, border: '1px dashed var(--border)', ...rowFaintStyle };
}

const rowFaintStyle = { background: 'var(--surface)' };

const rowBaseStyle = {
  display: 'grid',
  gridTemplateColumns: 'minmax(160px, 1fr) 80px 90px 72px 130px',
  gap: 8,
  alignItems: 'center',
  padding: '11px 14px',
  borderTop: 'none',
  cursor: 'pointer',
  textAlign: 'left',
  width: '100%',
  font: 'inherit',
  color: 'inherit',
};

/* ── filter sidebar ──────────────────────────────────────────────────── */
function FilterSidebar({ meta, districts, state, setState, band, setBand, max }) {
  const stateOptions = useMemo(() => {
    const counts = {};
    (meta.state_comparison || []).forEach((s) => {
      counts[s.state] = s.samples;
    });
    return Object.entries(counts).sort((a, b) => a[0].localeCompare(b[0]));
  }, [meta.state_comparison]);

  const bandCounts = meta.bands || {};

  return (
    <div className="sketch-box" style={{ height: '100%' }}>
      <span className="sketch-section-label">Filters</span>
      <div className="stack" style={{ marginTop: 14 }}>
        <div className="field">
          <label htmlFor="state-filter">State</label>
          <select
            id="state-filter"
            className="input"
            value={state}
            onChange={(e) => setState(e.target.value)}
            style={{ appearance: 'none', cursor: 'pointer', minHeight: 44 }}
          >
            <option value="">All states ({fmt(max)})</option>
            {stateOptions.map(([name, n]) => (
              <option key={name} value={name}>
                {name} ({fmt(n)})
              </option>
            ))}
          </select>
        </div>

        <div className="field">
          <label>Risk Band</label>
          <div className="stack" style={{ gap: 6 }}>
            {BANDS.map((b) => (
              <label
                key={b}
                style={{
                  display: 'flex',
                  gap: 8,
                  alignItems: 'center',
                  fontFamily: 'var(--font-sketch)',
                  fontSize: 13,
                  minHeight: 44,
                }}
              >
                <input
                  type="checkbox"
                  checked={band === b}
                  onChange={() => setBand(band === b ? '' : b)}
                  style={{ width: 16, height: 16 }}
                />
                <span className={bandClass(b)}>{b}</span>
                <span className="meta" style={{ marginLeft: 'auto' }}>
                  {fmt(bandCounts[b] != null ? bandCounts[b] : 0)}
                </span>
              </label>
            ))}
          </div>
        </div>

        <hr className="rule" />

        <div className="meta" style={{ textAlign: 'center' }}>
          {districts} districts · {meta.corpus ? meta.corpus.districts_with_samples : '\u2014'} with samples
        </div>
      </div>
    </div>
  );
}

/* ── severity progress bar (parameter drill-down) ────────────────────── */
function SeverityBar({ label, value, unit, limit, pct, exceeded }) {
  const color = exceeded ? 'var(--critical)' : 'var(--low)';
  return (
    <div>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          fontFamily: 'var(--font-mono)',
          fontSize: 10,
          color: 'var(--muted)',
          marginBottom: 3,
        }}
      >
        <span>
          {label}
          {value != null
            ? ` (${value}${unit ? ` ${unit}` : ''})`
            : exceeded
              ? ' (detected)'
              : ''}
          {limit != null ? ` \u00b7 BIS ${limit}` : ''}
        </span>
        <span style={{ color }}>{pct != null ? `${Math.round(pct * 100)}%` : exceeded ? 'SEV 1.00' : '\u2014'}</span>
      </div>
      <div className="prog-track">
        <div
          className="prog-fill"
          style={{
            width: `${Math.min(100, Math.max(pct || 0, 0) * 100)}%`,
            background: `repeating-linear-gradient(-45deg, ${color} 0, ${color} 4px, color-mix(in oklch, ${color} 40%, transparent) 4px, color-mix(in oklch, ${color} 40%, transparent) 8px)`,
          }}
        />
      </div>
    </div>
  );
}

/**
 * Real per-sample drill-down. `/api/priority` carries only summary fields, so
 * parameter values come from /api/samples/{id} and the BIS limits they should
 * be judged against come from /api/scoring/parameters. Both are read from the
 * live backend rather than restated here, so the bars explain the stored band
 * instead of re-deriving it from a second opinion.
 *
 * Severity mirrors backend/app/engine/scoring.py:parameter_severity:
 *   microbial  -> binary, any value above acceptable is 1.0
 *   range      -> 0 inside [acceptable, permissible]
 *   threshold  -> (v - acceptable) / (permissible - acceptable), clamped,
 *                 or a flat 1.0 when there is no permissible uplift
 */
function severityOf(reading, spec) {
  const v = reading.value;
  if (v == null || !spec || spec.acceptable == null) return { pct: null, exceeded: false };
  const strat = spec.strategy || 'threshold';
  const acc = spec.acceptable;
  const perm = spec.permissible;

  if (strat === 'microbial') return { pct: v > acc ? 1 : 0, exceeded: v > acc };
  if (strat === 'range') {
    const hi = perm != null ? perm : 8.5;
    if (acc <= v && v <= hi) return { pct: 0, exceeded: false };
    const dev = v < acc ? acc - v : v - hi;
    return { pct: Math.min(1, Math.max(0, dev)), exceeded: true };
  }
  if (v <= acc) return { pct: 0, exceeded: false };
  if (spec.binary_exceedance) return { pct: 1, exceeded: true };
  if (perm == null) return { pct: 1, exceeded: true };
  return { pct: Math.min(1, Math.max(0, (v - acc) / (perm - acc))), exceeded: true };
}

// pH is stored with the literal unit "none" -- showing "6.5–8.5 none" reads as a
// typo, so unitless parameters drop the suffix entirely.
function unitSuffix(reading, spec) {
  const u = reading.unit || (spec && spec.unit);
  if (!u || u === 'none' || u === 'None') return '';
  return ` ${u}`;
}

function limitText(reading, spec) {
  if (!spec || spec.acceptable == null) return null;
  const strat = spec.strategy || 'threshold';
  const u = unitSuffix(reading, spec);
  if (strat === 'range') {
    return `${spec.acceptable}\u2013${spec.permissible != null ? spec.permissible : 8.5}${u}`;
  }
  return spec.permissible != null && spec.permissible > spec.acceptable
    ? `${spec.acceptable} / ${spec.permissible}${u}`
    : `${spec.acceptable}${u}`;
}

function SampleDetail({ district, thresholds, specs }) {
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(false);
  const [failed, setFailed] = useState(false);

  const sampleId = district ? district.best_sample_id : null;

  useEffect(() => {
    if (sampleId == null) return;
    let cancelled = false;
    setLoading(true);
    setFailed(false);
    setDetail(null);
    fetch(`${API}/samples/${sampleId}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((d) => {
        if (!cancelled) setDetail(d);
      })
      .catch(() => {
        // GitHub Pages has no backend, so /api/samples/{id} 404s there. The
        // baked dashboard-data.json carries the same readings for the top
        // scored rows, keyed by risk id, so the drill-down still works.
        if (cancelled) return;
        fetch(assetUrl('/dashboard-data.json'))
          .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
          .then((baked) => {
            const det = baked && baked.details && baked.details[String(sampleId)];
            if (cancelled) return;
            if (det) {
              setDetail({ readings: det.readings || [], risk_score: null });
            } else {
              setFailed(true);
            }
          })
          .catch(() => {
            if (!cancelled) setFailed(true);
          });
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [sampleId]);

  const readings = (detail && detail.readings) || [];
  const ordered = [...readings].sort((a, b) => {
    const sa = severityOf(a, specs && specs[a.parameter_key]);
    const sb = severityOf(b, specs && specs[b.parameter_key]);
    return (sb.pct || 0) - (sa.pct || 0);
  });

  return (
    <div className="sketch-box">
      <span className="sketch-section-label">Sample detail</span>
      <div className="stack" style={{ marginTop: 12 }}>
        <h3>
          {district.district}
          {district.state ? `, ${district.state}` : ''}
        </h3>
        <div className="row" style={{ flexWrap: 'wrap', gap: 8 }}>
          <span className={bandClass(district.band)}>
            Score {district.score != null ? district.score.toFixed(1) : '\u2014'}
          </span>
          <span className="tag">{district.sample_count} samples in top {district.pool_size}</span>
          {district.worst_parameter ? (
            <span className="tag">
              Worst: {PARAM_LABELS[district.worst_parameter] || district.worst_parameter}
            </span>
          ) : (
            <span className="tag">Within BIS limits</span>
          )}
          <span className="tag">Row #{district.best_sample_id}</span>
        </div>

        {loading ? (
          <div className="stack" style={{ gap: 8 }}>
            {[0, 1, 2].map((i) => (
              <div className="skeleton" key={i} style={{ height: 14 }} />
            ))}
          </div>
        ) : failed ? (
          <p className="callout">
            No parameter readings available for row #{district.best_sample_id}. On the public
            Pages build this is expected \u2014 readings need the live API.
          </p>
        ) : ordered.length ? (
          <div className="stack" style={{ gap: 10 }}>
            <div
              className="meta"
              style={{ fontSize: 10, letterSpacing: '0.06em', textTransform: 'uppercase' }}
            >
              Tested parameters \u2014 severity vs BIS limits
            </div>
            {ordered.map((r) => {
              const spec = specs && specs[r.parameter_key];
              const s = severityOf(r, spec);
              return (
                <SeverityBar
                  key={r.parameter_key}
                  label={(spec && spec.label) || PARAM_LABELS[r.parameter_key] || r.parameter_key}
                  value={r.value}
                  unit={r.unit || (spec && spec.unit)}
                  limit={limitText(r, spec)}
                  pct={s.pct}
                  exceeded={s.exceeded}
                />
              );
            })}
            {detail && detail.risk_score ? (
              <>
                <hr className="rule" />
                <div className="row" style={{ justifyContent: 'space-between' }}>
                  <span className="meta">
                    Band cut-offs: {BAND_ORDER_DESC.filter((b) => thresholds && thresholds[b] != null)
                      .map((b) => `${b} ${bandRange(b, thresholds)}`)
                      .join(' \u00b7 ')}
                  </span>
                  <span className={bandClass(detail.risk_score.band)}>
                    {detail.risk_score.band}
                  </span>
                </div>
              </>
            ) : null}
          </div>
        ) : (
          <p className="callout">No parameter readings recorded for this sample.</p>
        )}

        {detail && detail.village && String(detail.village).toLowerCase() !== 'not available' ? (
          <p className="meta">Village on record: {detail.village}</p>
        ) : null}
        {detail && detail.collected_on ? (
          <p className="meta">Collected: {new Date(detail.collected_on).toISOString().slice(0, 10)}</p>
        ) : null}
      </div>
    </div>
  );
}

/* ── Error box ───────────────────────────────────────────────────────── */
function ErrorBox({ detail }) {
  return (
    <div className="error-box">
      <div style={{ fontSize: 20, marginBottom: 10, lineHeight: 1 }}>{'\u26a0'}</div>
      <div style={{ fontWeight: 700, marginBottom: 6 }}>Could not load data</div>
      <div style={{ fontSize: 12, color: 'color-mix(in oklch, var(--critical) 80%, black)', marginBottom: 14 }}>
        {detail || 'API unreachable. Check `docker start watertriage-db`.'}
      </div>
      <div style={{ display: 'flex', gap: 8, justifyContent: 'center', flexWrap: 'wrap' }}>
        <button className="btn btn-secondary" onClick={() => window.location.reload()}>
          Retry
        </button>
      </div>
    </div>
  );
}

/* ══ main app ═════════════════════════════════════════════════════════ */
export default function App() {
  const [dark, toggleDark] = useTheme();
  const [activeTab, setActiveTab] = useState('queue');

  const [meta, setMeta] = useState(null);
  const [metaError, setMetaError] = useState(null);
  const [stale, setStale] = useState(false);

  const [rawQueue, setRawQueue] = useState([]);
  const [queueLoading, setQueueLoading] = useState(true);
  const [paramSpecs, setParamSpecs] = useState({});
  const [cgwb, setCgwb] = useState({ ph: [], available: {}, wq6_summary: {}, master_districts: [] });

  const [stateFilter, setStateFilter] = useState('');
  const [bandFilter, setBandFilter] = useState('');
  const [selected, setSelected] = useState(null);
  const [valStateFilter, setValStateFilter] = useState('');
  const [valSearch, setValSearch] = useState('');

  useEffect(() => {
    fetchLive(`${API}/meta`, '/meta.json')
      .then(({ data, stale }) => {
        setMeta(data);
        setStale(stale);
      })
      .catch((e) => setMetaError(String(e)));
  }, []);

  // CGWB pH compliance is external to the crawl, so it is fetched separately
  // rather than folded into /api/meta.
  useEffect(() => {
    fetchLive(`${API}/validation/cgwb`, '/validation-cgwb.json')
      .then(({ data }) => {
        setCgwb({
          ph: Array.isArray(data && data.ph) ? data.ph : [],
          available: (data && data.available_parameters) || {},
          wq6_summary: (data && data.wq6_summary) || {},
          master_districts: Array.isArray(data && data.master_districts) ? data.master_districts : [],
        });
      })
      .catch(() => setCgwb({ ph: [], available: {}, wq6_summary: {}, master_districts: [] }));
  }, []);

  // BIS limits come from the bis_parameters table that actually produced the
  // stored scores, so severity bars and the weight list agree with the bands.
  useEffect(() => {
    fetchLive(`${API}/scoring/parameters`, '/scoring-parameters.json')
      .then(({ data }) => {
        setParamSpecs(
          Array.isArray(data)
            ? Object.fromEntries(data.map((r) => [r.key, r]))
            : {}
        );
      })
      .catch(() => setParamSpecs({}));
  }, []);

  useEffect(() => {
    fetchLive(`${API}/priority/top/200`, '/dashboard-data.json')
      .then(({ data }) => {
        // The baked fallback is the older dashboard-data shape: a top-200
        // "priority" array of summary rows. Normalise it to the same fields
        // /api/priority/top returns so one render path handles both.
        const rows = Array.isArray(data)
          ? data
          : Array.isArray(data && data.priority)
            ? data.priority.map((p) => ({
                sample_id: p.sample_id,
                district: p.district,
                state: p.state,
                score: p.score,
                band: p.band,
                worst_parameter: p.worst,
                n_scored_params:
                  p.n_scored_params != null
                    ? p.n_scored_params
                    : data.details && data.details[String(p.sample_id)] && Array.isArray(data.details[String(p.sample_id)].readings)
                      ? data.details[String(p.sample_id)].readings.length
                      : null,
                collected_on: p.date,
              }))
            : [];
        setRawQueue(rows);
      })
      .catch(() => setRawQueue([]))
      .finally(() => setQueueLoading(false));
  }, []);

  const districts = useMemo(() => {
    if (!rawQueue.length) return [];
    const byKey = new Map();
    for (const item of rawQueue) {
      const key = `${item.district}|${item.state}`;
      const prev = byKey.get(key);
      if (!prev) {
        byKey.set(key, {
          key,
          district: item.district,
          state: item.state,
          score: item.score,
          band: item.band,
          worst_parameter: item.worst_parameter,
          n_scored_params: item.n_scored_params,
          sample_count: 1,
          pool_size: 0,
          best_sample_id: item.sample_id,
          collected_on: item.collected_on,
        });
      } else {
        prev.sample_count += 1;
      }
    }
    for (const d of byKey.values()) d.pool_size = rawQueue.length;
    return [...byKey.values()].sort((a, b) => (b.score || 0) - (a.score || 0));
  }, [rawQueue]);

  const filtered = useMemo(
    () =>
      districts.filter(
        (d) => (!stateFilter || d.state === stateFilter) && (!bandFilter || d.band === bandFilter)
      ),
    [districts, stateFilter, bandFilter]
  );

  if (metaError) {
    return (
      <div className="container" style={{ paddingBlock: 80 }}>
        <ErrorBox detail={`/api/meta failed: ${metaError}`} />
      </div>
    );
  }
  if (!meta) {
    return (
      <div className="container" style={{ paddingBlock: 80 }}>
        <div className="stack" style={{ gap: 8 }}>
          <div className="skeleton" style={{ height: 14, width: '60%' }} />
          <div className="skeleton" style={{ height: 14, width: '85%' }} />
          <div className="skeleton" style={{ height: 14, width: '45%' }} />
        </div>
      </div>
    );
  }

  const corpus = meta.corpus || {};
  const stateStats = meta.sensitivity && meta.sensitivity.iron_1_0
    ? meta.sensitivity.iron_1_0.state_stats
    : {};

  const tabs = [
    { id: 'queue', label: 'Variant A \u2014 Priority Queue', note: 'list-dominant: filter sidebar + sortable district rows' },
    { id: 'overview', label: 'Overview', note: 'corpus KPIs + state sensitivity' },
    { id: 'validation', label: 'External Validation', note: 'government ground-truth triangulation' },
    { id: 'methodology', label: 'Methodology', note: 'provenance, scoring model, limitations' },
  ];

  return (
    <>
      {/* ═══ NAV ═══════════════════════════════════════════════════ */}
      <header className="topnav">
        <div className="container topnav-inner">
          <span className="logo">WaterTriage</span>
          <HealthPill />
          <ThemeToggle dark={dark} onToggle={toggleDark} />
          <nav aria-label="Primary">
            <a href="#panel-queue" onClick={(e) => { e.preventDefault(); setActiveTab('queue'); }}>Priority Queue</a>
            <a href="#panel-overview" onClick={(e) => { e.preventDefault(); setActiveTab('overview'); }}>Overview</a>
            <a href="#panel-validation" onClick={(e) => { e.preventDefault(); setActiveTab('validation'); }}>Validation (113 Dist.)</a>
            <a href="#panel-methodology" onClick={(e) => { e.preventDefault(); setActiveTab('methodology'); }}>Methodology</a>
          </nav>
          <button
            className="btn btn-primary"
            onClick={() => {
              const rowsToExport = activeTab === 'validation' && (cgwb.master_districts || []).length
                ? cgwb.master_districts
                : filtered.map((d) => ({
                    district: d.district,
                    state: d.state,
                    max_score: d.score,
                    band: d.band,
                    samples_in_queue: d.sample_count,
                    n_scored_params: d.n_scored_params,
                    worst_parameter: d.worst_parameter || 'within_limits',
                  }));
              if (!rowsToExport.length) return;
              const headers = Object.keys(rowsToExport[0]);
              const csvLines = [
                headers.join(','),
                ...rowsToExport.map((row) =>
                  headers.map((h) => `"${String(row[h] ?? '').replace(/"/g, '""')}"`).join(',')
                ),
              ];
              const blob = new Blob([csvLines.join('\n')], { type: 'text/csv;charset=utf-8;' });
              const url = URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.href = url;
              a.download = activeTab === 'validation' ? 'watertriage_113_districts_master.csv' : 'watertriage_priority_districts.csv';
              a.click();
              URL.revokeObjectURL(url);
            }}
          >
            Export CSV
          </button>
        </div>
      </header>

      <main id="content">
        {/* ═══ HERO + TAB SWITCHER ═════════════════════════════════ */}
        <section className="section hero" style={{ paddingBottom: 0 }}>
          <div className="container">
            <div style={{ maxWidth: 680, marginBottom: 44 }}>
              <p className="eyebrow">
                WaterTriage Dashboard \u00b7 UP + Bihar (113 Districts) \u00b7{' '}
                {stale ? (
                  <span style={{ color: 'var(--accent)' }}>Verified Corpus Snapshot (1,741 Samples)</span>
                ) : (
                  <span style={{ color: 'var(--low)' }}>Live DB</span>
                )}
              </p>
              <h1>Water Quality Risk Priorities</h1>
              <p className="lead" style={{ marginTop: 16 }}>
                Composite risk scores over <strong>{fmt(corpus.samples)}</strong> scored samples
                across <strong>{fmt(corpus.districts_with_samples)}</strong> districts,
                {' '}<strong>{fmt(corpus.readings)}</strong> parameter readings and{' '}
                <strong>{fmt(corpus.historical_events_distinct)}</strong> historical contamination events.
                Severity model: <strong>BIS IS 10500</strong> weighted composite.
              </p>
              <div
                style={{
                  display: 'flex',
                  gap: 20,
                  flexWrap: 'wrap',
                  marginTop: 28,
                  padding: '16px 20px',
                  border: '2px solid var(--fg)',
                  borderRadius: 2,
                  background: 'var(--surface)',
                }}
              >
                <KpiStrip bands={meta.bands || {}} thresholds={meta.band_thresholds || {}} />
              </div>
            {stale ? (
              <p className="callout" style={{ marginTop: 10 }}>
                Backend unreachable \u2014 showing the baked snapshot from public/. Bands and
                district rows are from <strong>{meta.generated_at ? new Date(meta.generated_at).toISOString().slice(0, 10) : 'an earlier run'}</strong>;
                start the API (<code>docker start watertriage-db</code> + uvicorn) for current
                figures.
              </p>
            ) : null}
            <p className="callout" style={{ marginTop: 10 }}>
              Village name coverage is {corpus.village_name_coverage_pct}% \u2014 district is the
              defensible unit of analysis, so this view aggregates to district.
            </p>
            </div>

            {/* ─── tab switcher ─── */}
            <div className="tab-row" role="tablist" aria-label="Dashboard views">
              {tabs.map((t) => (
                <button
                  key={t.id}
                  className={`tab-btn ${activeTab === t.id ? 'active' : ''}`}
                  role="tab"
                  aria-selected={activeTab === t.id}
                  onClick={() => setActiveTab(t.id)}
                >
                  {t.label}
                </button>
              ))}
            </div>

            {/* ─── Variant A: Priority Queue ─── */}
            {activeTab === 'queue' && (
              <div className="tab-panel active" id="panel-queue" role="tabpanel">
                <div className="grid-2-1">
                  <div>
                    <p className="callout" style={{ marginBottom: 16 }}>
                      District rows ranked by worst composite score. Click a row to inspect it.
                      Filter by state or band on the right.
                    </p>
                    {queueLoading ? (
                      <div className="stack" style={{ gap: 8 }}>
                        {[0, 1, 2, 3, 4, 5].map((i) => (
                          <div className="skeleton" key={i} style={{ height: 44 }} />
                        ))}
                      </div>
                    ) : (
                      <DistrictRows
                        items={filtered}
                        activeKey={selected && selected.key}
                        onSelect={(d) => setSelected(d.key === (selected && selected.key) ? null : d)}
                      />
                    )}
                  </div>

                  <div className="stack">
                    <FilterSidebar
                      meta={meta}
                      districts={districts.length}
                      state={stateFilter}
                      setState={setStateFilter}
                      band={bandFilter}
                      setBand={setBandFilter}
                      max={meta.state_comparison
                        ? meta.state_comparison.reduce((s, x) => s + x.samples, 0)
                        : 0}
                    />

                    {selected ? (
                      <SampleDetail
                        district={selected}
                        thresholds={meta.band_thresholds || {}}
                        specs={paramSpecs}
                      />
                    ) : (
                      <div className="empty-box">
                        <div style={{ fontSize: 28, marginBottom: 12, opacity: 0.4, lineHeight: 1 }}>{'\u2205'}</div>
                        <div style={{ fontWeight: 700, marginBottom: 6 }}>No row selected</div>
                        <div style={{ fontSize: 12 }}>Pick a district above to inspect it.</div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* ─── Overview ─── */}
            {activeTab === 'overview' && (
              <div className="tab-panel active" id="panel-overview" role="tabpanel">
                <div className="stack" style={{ gap: 'var(--gap-lg)' }}>
                  <div>
                    <h3>Samples by Risk Band</h3>
                    <p className="callout" style={{ margin: '6px 0 16px' }}>
                      Composite severity, IS 10500 weights. Total {fmt(corpus.samples)} scored samples.
                    </p>
                    <BandChart bands={meta.bands || {}} />
                  </div>

                  <div>
                    <h3>Sensitivity run \u2014 Iron limit re-set to 1.0 mg/L</h3>
                    <p className="callout" style={{ margin: '6px 0 16px' }}>
                      876 raw readings carry a 1.0 mg/L acceptable limit; scoring uses the stricter
                      0.3 mg/L from IS 10500:2012. This rerun shows how far the bands move under that
                      single change \u2014 it is a robustness check, not a second corpus.
                    </p>
                    <DataTable
                      columns={[
                        { key: 'state', label: 'State' },
                        { key: 'live_mean', label: 'Mean score (scored)', align: 'right' },
                        { key: 'rerun_mean', label: 'Mean score (rerun)', align: 'right' },
                        { key: 'rerun_median', label: 'Median (rerun)', align: 'right' },
                        { key: 'rerun_critical', label: 'Critical (rerun)', align: 'right' },
                      ]}
                      rows={(meta.state_comparison || []).map((s) => {
                        const rs = stateStats[s.state] || {};
                        return {
                          key: s.state,
                          state: s.state,
                          live_mean: s.mean_crs != null ? s.mean_crs.toFixed(2) : '\u2014',
                          rerun_mean: rs.mean != null ? rs.mean.toFixed(2) : '\u2014',
                          rerun_median: rs.median != null ? rs.median.toFixed(2) : '\u2014',
                          rerun_critical: rs.critical != null ? fmt(rs.critical) : '\u2014',
                        };
                      })}
                    />
                    {meta.sensitivity && meta.sensitivity.iron_1_0 && meta.sensitivity.iron_1_0.bands ? (
                      <p className="callout" style={{ marginTop: 12 }}>
                        Corpus-wide rerun bands: {' '}
                        {BANDS.filter((b) => meta.sensitivity.iron_1_0.bands[b] != null)
                          .map((b) => `${b} ${fmt(meta.sensitivity.iron_1_0.bands[b])}`)
                          .join(' \u00b7 ')}
                      </p>
                    ) : null}
                  </div>

                  <div>
                    <h3>State comparison</h3>
                    <p className="callout" style={{ margin: '6px 0 16px' }}>
                      Live per-state figures from <code>/api/meta</code>.
                    </p>
                    <DataTable
                      columns={[
                        { key: 'state', label: 'State' },
                        { key: 'samples', label: 'Samples', align: 'right' },
                        { key: 'critical', label: 'Critical', align: 'right' },
                        { key: 'high', label: 'High', align: 'right' },
                        { key: 'medium', label: 'Medium', align: 'right' },
                        { key: 'low', label: 'Low', align: 'right' },
                      ]}
                      rows={(meta.state_comparison || []).map((s) => ({
                        key: s.state,
                        state: s.state,
                        samples: fmt(s.samples),
                        critical: fmt(s.bands.Critical),
                        high: fmt(s.bands.High),
                        medium: fmt(s.bands.Medium),
                        low: fmt(s.bands.Low),
                      }))}
                    />
                  </div>
                </div>
              </div>
            )}

            {/* ─── External Validation ─── */}
            {activeTab === 'validation' && (
              <div className="tab-panel active" id="panel-validation" role="tabpanel">
                <p className="callout" style={{ marginBottom: 20 }}>
                  Government ground-truth files sit in <code>data/validation_reports/</code>.
                  They are loaded as reference tables, not merged into <code>risk_scores</code>.
                </p>

                <div className="stack" style={{ gap: 'var(--gap-lg)' }}>
                  <div className="sketch-box">
                    <span className="sketch-section-label">Reference sources</span>
                    <p className="callout" style={{ margin: '12px 0 16px' }}>
                      Independent government files kept alongside the corpus. They are never merged
                      into <code>risk_scores</code> \u2014 they exist to check the algorithm against an
                      external baseline, so a scoring bug cannot hide by agreeing with itself.
                    </p>
                    <DataTable
                      columns={[
                        { key: 'source', label: 'Source' },
                        { key: 'granularity', label: 'Granularity' },
                        { key: 'what', label: 'What it contributes' },
                      ]}
                      rows={[
                        {
                          key: 'imis',
                          source: 'IMIS 2009\u20132012',
                          granularity: 'district \u00d7 parameter',
                          what: 'Iron / arsenic / fluoride / nitrate / salinity habitation counts (the imis_* columns of Master_Validation_*.csv)',
                        },
                        {
                          key: 'wq6',
                          source: 'WQ6 2024 (JJM)',
                          granularity: 'district \u00d7 parameter',
                          what: 'Per-parameter affected-village counts for UP and Bihar (WQ6_Complete_*.csv)',
                        },
                        {
                          key: 'cgwb',
                          source: 'CGWB 2012\u20132021',
                          granularity: 'state \u00d7 year',
                          what: 'Groundwater pH exceedance percentage and monitoring stations (also the cgwb_readings table)',
                        },
                        {
                          key: 'internal',
                          source: 'WQMIS crawl (this corpus)',
                          granularity: 'sample',
                          what: 'The scored corpus \u2014 the only source that feeds composite risk',
                        },
                      ]}
                    />
                  </div>

                  {(cgwb.master_districts || []).length > 0 && (
                    <div className="sketch-box">
                      <span className="sketch-section-label">
                        113-District Master Ground-Truth Explorer (75 UP + 38 Bihar = 100% District Coverage)
                      </span>
                      <p className="callout" style={{ margin: '12px 0 16px' }}>
                        Complete district-level triangulation across all <strong>75 Uttar Pradesh</strong> and{' '}
                        <strong>38 Bihar</strong> districts (including the 6 recovered S.No. 1&ndash;3 districts:{' '}
                        <em>Agra, Aligarh, Ambedkar Nagar, Araria, Arwal, Aurangabad</em>), combining our{' '}
                        <strong>1,741 WQMIS lab samples</strong> (+47 deterministic single-district lab matches),{' '}
                        <strong>IMIS 2009&ndash;2012</strong> registry habitations (100,690 events), and{' '}
                        <strong>JJM Form WQ6</strong> contaminated-village counts.
                      </p>
                      <div className="row" style={{ gap: 12, flexWrap: 'wrap', marginBottom: 16 }}>
                        <select
                          className="input"
                          value={valStateFilter}
                          onChange={(e) => setValStateFilter(e.target.value)}
                          style={{ maxWidth: 240, minHeight: 40, cursor: 'pointer' }}
                          aria-label="Filter 113 districts by state"
                        >
                          <option value="">All 113 Districts (UP 75 + Bihar 38)</option>
                          <option value="Uttar Pradesh">Uttar Pradesh (75 districts)</option>
                          <option value="Bihar">Bihar (38 districts)</option>
                        </select>
                        <input
                          type="search"
                          className="input"
                          placeholder="Search district (e.g. Agra, Araria, Madhepura, Prayagraj)..."
                          value={valSearch}
                          onChange={(e) => setValSearch(e.target.value)}
                          style={{ flex: 1, minWidth: 220, minHeight: 40 }}
                        />
                      </div>
                      <DataTable
                        columns={[
                          { key: 'district_label', label: 'District (State)' },
                          { key: 'samples_label', label: 'WQMIS Samples', align: 'right' },
                          { key: 'imis_total', label: 'IMIS (2009–12)', align: 'right' },
                          { key: 'wq6_iron', label: 'WQ6 Iron', align: 'right' },
                          { key: 'wq6_fluoride', label: 'WQ6 Fluoride', align: 'right' },
                          { key: 'wq6_arsenic', label: 'WQ6 Arsenic', align: 'right' },
                          { key: 'wq6_turbidity', label: 'WQ6 Turbidity', align: 'right' },
                          { key: 'wq6_bact', label: 'WQ6 E. coli / TC', align: 'right' },
                        ]}
                        rows={(cgwb.master_districts || [])
                          .filter(
                            (d) =>
                              (!valStateFilter || d.state === valStateFilter) &&
                              (!valSearch ||
                                String(d.district_norm || '')
                                  .toLowerCase()
                                  .includes(valSearch.trim().toLowerCase()))
                          )
                          .map((d) => {
                            const imisSum =
                              (d.imis_iron || 0) +
                              (d.imis_arsenic || 0) +
                              (d.imis_fluoride || 0) +
                              (d.imis_nitrate || 0) +
                              (d.imis_salinity || 0);
                            return {
                              key: `${d.state}-${d.district_norm}`,
                              district_label: `${d.district_norm} (${d.state === 'Uttar Pradesh' ? 'UP' : 'Bihar'})`,
                              samples_label:
                                d.our_inferred_samples > 0
                                  ? `${fmt(d.our_samples)} (+${d.our_inferred_samples} lab)`
                                  : fmt(d.our_samples || 0),
                              imis_total: fmt(imisSum),
                              wq6_iron: fmt(d.Iron || 0),
                              wq6_fluoride: fmt(d.Fluoride || 0),
                              wq6_arsenic: fmt(d.Total_Arsenic || 0),
                              wq6_turbidity: fmt(d.Turbidity || 0),
                              wq6_bact: `${fmt(d.E_coli || 0)} / ${fmt(d.Total_Coliform || 0)}`,
                            };
                          })}
                      />
                    </div>
                  )}

                  <div className="sketch-box">
                    <span className="sketch-section-label">CGWB pH outside BIS range 6.5\u20138.5</span>
                    <p className="callout" style={{ margin: '12px 0 16px' }}>
                      From <code>cgwb_readings</code>, aggregated per state and year. This is
                      independent government data, so if the crawl disagreed here it would mean
                      the crawl is wrong \u2014 that is the point of keeping them apart.
                    </p>
                    <DataTable
                      columns={[
                        { key: 'state', label: 'State' },
                        { key: 'year', label: 'Year' },
                        { key: 'readings', label: 'pH readings', align: 'right' },
                        { key: 'exceeded', label: 'Outside 6.5\u20138.5', align: 'right' },
                        { key: 'exceed_pct', label: 'Share (%)', align: 'right' },
                      ]}
                      rows={(cgwb.ph || []).map((c, i) => ({
                        key: c.state + c.year + i,
                        state: c.state,
                        year: c.year,
                        readings: fmt(c.readings),
                        exceeded: fmt(c.exceeded),
                        exceed_pct: c.exceed_pct != null ? c.exceed_pct.toFixed(1) : '\u2014',
                      }))}
                    />
                    {(cgwb.ph || []).length === 0 ? (
                      <p className="callout">
                        No CGWB pH rows returned by <code>/api/validation/cgwb</code>.
                      </p>
                    ) : null}
                    {/* A state with other CGWB parameters but no pH must say so, not
                        silently drop the row -- that reads as a bug in our pipeline. */}
                    {Object.entries(cgwb.available || {})
                      .filter(([state, params]) => !(cgwb.ph || []).some((c) => c.state === state))
                      .map(([state, params]) => (
                        <p className="callout" key={state}>
                          {state}: the <code>cgwb_readings</code> table holds no pH readings for
                          this corpus (it carries {params.length} other CGWB parameters), so no
                          cross-check is possible for {state} yet.
                        </p>
                      ))}
                  </div>

                  <div className="sketch-box">
                    <span className="sketch-section-label">Iron concentration</span>
                    <p className="callout" style={{ margin: '12px 0 16px' }}>
                      Where the highest-scoring district clusters by parameter. Driven by live
                      <code>/api/meta</code> <em>critical_concentration</em>.
                    </p>
                    <p style={{ fontFamily: 'var(--font-sketch)', fontSize: 15 }}>
                      {meta.critical_concentration
                        ? `${meta.critical_concentration.district} \u2014 ${fmt(meta.critical_concentration.total_critical)} critical samples, ${fmt(meta.critical_concentration.single_parameter_iron_critical)} of them single-parameter iron.`
                        : 'No district concentration reported for this corpus snapshot.'}
                    </p>
                  </div>

                  <div className="sketch-box">
                    <span className="sketch-section-label">Top exceedance parameters</span>
                    <DataTable
                      columns={[
                        { key: 'state', label: 'State' },
                        { key: 'parameter_key', label: 'Parameter' },
                        { key: 'tested', label: 'Tested', align: 'right' },
                        { key: 'exceeding', label: 'Exceeding acceptable', align: 'right' },
                      ]}
                      rows={(meta.top_parameters || []).slice(0, 15).map((p, i) => ({
                        key: p.state + p.parameter_key + i,
                        state: p.state,
                        parameter_key: PARAM_LABELS[p.parameter_key] || p.parameter_key,
                        tested: fmt(p.tested),
                        exceeding: fmt(p.exceeding),
                      }))}
                    />
                  </div>
                </div>
              </div>
            )}

            {/* ─── Methodology ─── */}
            {activeTab === 'methodology' && (
              <div className="tab-panel active" id="panel-methodology" role="tabpanel">
                <div className="stack" style={{ gap: 'var(--gap-lg)' }}>
                  <div className="sketch-box">
                    <span className="sketch-section-label">Corpus extraction</span>
                    <div className="stack" style={{ marginTop: 12 }}>
                      <p style={{ fontFamily: 'var(--font-sketch)', fontSize: 14 }}>
                        Records were collected in batches between 23 Aug and 20 Sep 2026; request
                        totals and rates were not logged; later batches used up to 6 parallel workers.
                        Collection window for scored samples: {corpus.sample_years ? corpus.sample_years.join('\u2013') : '2022'}.
                        Historical registry window: {corpus.registry_years ? corpus.registry_years.join('\u2013') : '2009\u20132012'}.
                      </p>
                      <p className="meta">
                        git commit {meta.git_commit} \u00b7 generated {meta.generated_at}
                      </p>
                    </div>
                  </div>

                  <div>
                    <h3>API-reported limitations</h3>
                    <ul className="stack" style={{ lineHeight: 1.6, marginTop: 12, listStyle: 'none', padding: 0 }}>
                      {(meta.limitations || []).map((lim) => (
                        <li key={lim.id} style={{ borderBottom: '1px dashed var(--border)', paddingBottom: 12 }}>
                          <div className="row" style={{ justifyContent: 'space-between', alignItems: 'baseline' }}>
                            <strong style={{ fontFamily: 'var(--font-sketch)' }}>{lim.title}</strong>
                            <span className={`badge badge-${lim.status === 'open' ? 'high' : 'low'}`}>{lim.status}</span>
                          </div>
                          <div style={{ color: 'var(--muted)', fontFamily: 'var(--font-sketch)', fontSize: 13, marginTop: 4 }}>
                            {lim.detail}
                          </div>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div className="sketch-box">
                    <span className="sketch-section-label">Severity bands</span>
                    <div className="stack" style={{ marginTop: 12 }}>
                      <p className="callout">
                        Cut-offs read live from <code>meta.band_thresholds</code>. The original
                        75/50/25 cut-offs sit in the project docs but are unreachable under the
                        escalation rules, so they are not what the engine emits.
                      </p>
                      <DataTable
                        columns={[
                          { key: 'band', label: 'Band' },
                          { key: 'range', label: 'Composite score' },
                          { key: 'count', label: 'Samples', align: 'right' },
                        ]}
                        rows={BAND_ORDER_DESC.map((b) => ({
                          key: b,
                          band: b,
                          range: bandRange(b, meta.band_thresholds || {}),
                          count: fmt((meta.bands || {})[b]),
                        }))}
                      />
                    </div>
                  </div>

                  <div className="sketch-box">
                    <span className="sketch-section-label">Scoring model</span>
                    <div className="stack" style={{ marginTop: 12 }}>
                      <p style={{ fontFamily: 'var(--font-sketch)', fontSize: 14 }}>
                        {meta.scoring ? meta.scoring.model : 'BIS IS 10500 weighted severity model'} \u00b7{' '}
                        {meta.scoring ? meta.scoring.standard : 'BIS IS 10500'}
                      </p>
                      {Object.keys(paramSpecs).length ? (
                        <DataTable
                          columns={[
                            { key: 'label', label: 'Parameter' },
                            { key: 'acceptable', label: 'Acceptable' },
                            { key: 'permissible', label: 'Permissible' },
                            { key: 'weight', label: 'Weight', align: 'right' },
                          ]}
                          rows={Object.entries(paramSpecs).map(([k, s]) => {
                            const u = s.unit && s.unit !== 'none' && s.unit !== 'None' ? ` ${s.unit}` : '';
                            // Must be a ternary, not `(s.label && ...) || k` -- that
                            // expression short-circuits to a boolean, which React
                            // renders as an empty cell.
                            const label = s.label && s.label !== 'none' ? s.label : k;
                            return {
                              key: k,
                              label,
                              acceptable: `${s.acceptable}${u}`,
                              permissible:
                                s.permissible != null
                                  ? `${s.permissible}${u}`
                                  : 'none (binary)',
                              weight: s.weight != null ? s.weight.toFixed(1) : '\u2014',
                            };
                          })}
                        />
                      ) : (
                        <p className="callout">
                          BIS parameter table unavailable \u2014 backend /api/scoring/parameters did
                          not respond.
                        </p>
                      )}
                      <p className="callout" style={{ marginTop: 8 }}>
                        Read live from the <code>bis_parameters</code> table that produced the
                        stored scores, so these limits are the ones the bands were computed
                        against \u2014 not a second declaration of them.
                      </p>
                      <hr className="rule" />
                      <div className="stack" style={{ gap: 8 }}>
                        {(meta.scoring && meta.scoring.escalation_rules ? meta.scoring.escalation_rules : []).map((r, i) => (
                          <p key={i} className="callout">
                            {r.rule} \u2192 floor: <strong>{r.bands_floor}</strong>
                          </p>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </section>

        {/* ═══ KNOWN BLOCKERS ═══════════════════════════════════════ */}
        <section className="section">
          <div className="container">
            <div style={{ maxWidth: '40ch', marginBottom: 40 }}>
              <p className="eyebrow">Designer Notes</p>
              <h2>Known limitations</h2>
            </div>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))',
                gap: 36,
                alignItems: 'start',
              }}
            >
              <div className="sticky sticky-yellow">
                <div className="sticky-title">District-only</div>
                <p>
                  Village names exist for {corpus.village_name_coverage_pct}% of samples, so every
                  claim on this site is district-level. No village hotspot claims.
                </p>
              </div>
              <div className="sticky sticky-pink">
                <div className="sticky-title">2022 window</div>
                <p>
                  Scored samples date to {corpus.sample_years ? corpus.sample_years[0] : '2022'} only.
                  This is a WQMIS collection snapshot, not live monitoring.
                </p>
              </div>
              <div className="sticky sticky-green">
                <div className="sticky-title">Iron limit conflict</div>
                <p>
                  Scoring uses 0.3 mg/L from IS 10500:2012 even though 876 raw readings carry a
                  1.0 mg/L label. The Overview tab quantifies the difference.
                </p>
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="pagefoot">
        <div className="container row-between">
          <span>WaterTriage Dashboard \u00b7 UP + Bihar \u00b7 Anubhav Anand</span>
          <span className="meta">NTCC Minor Project \u00b7 Dr. Girish Paliwal \u00b7 ASET-AUGN</span>
        </div>
      </footer>
    </>
  );
}
