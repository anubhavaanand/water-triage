import React, { useState, useEffect, useMemo } from 'react';
import './index.css';

const BASE_URL = import.meta.env.BASE_URL || '/';

function withBase(path) {
  const clean = path.replace(/^\/+/, '');
  return `${BASE_URL.endsWith('/') ? BASE_URL : BASE_URL + '/'}${clean}`;
}

async function fetchWithFallback(apiPath, fallbackFile) {
  try {
    const res = await fetch(apiPath, { headers: { Accept: 'application/json' } });
    if (res.ok) {
      const ct = res.headers.get('content-type') || '';
      if (ct.includes('application/json')) {
        return { data: await res.json(), source: 'live' };
      }
    }
  } catch (_) {
    // Fallback to static snapshot in public/
  }
  const fbRes = await fetch(withBase(fallbackFile));
  if (!fbRes.ok) {
    throw new Error(`Failed to load ${apiPath} and fallback ${fallbackFile}`);
  }
  return { data: await fbRes.json(), source: 'snapshot' };
}

const BAND_COLORS = {
  Critical: 'var(--critical)',
  High: 'var(--high)',
  Medium: 'var(--medium)',
  Low: 'var(--low)',
};

const BAND_BADGE = {
  Critical: 'badge badge-critical',
  High: 'badge badge-high',
  Medium: 'badge badge-medium',
  Low: 'badge badge-low',
};

const PARAM_LABELS = {
  iron: 'Iron (Fe)',
  fluoride: 'Fluoride (F)',
  turbidity: 'Turbidity',
  tds: 'TDS',
  sulphate: 'Sulphate (SO4)',
  nitrate: 'Nitrate (NO3)',
  arsenic: 'Total Arsenic (As)',
  e_coli: 'E. coli',
  total_coliform: 'Total Coliform',
  ph: 'pH',
};

function PathogenBadge({ reason }) {
  return (
    <span className="has-tooltip" style={{ display: 'inline-flex', alignItems: 'center' }}>
      <span className="badge-pathogen" tabIndex={0}>
        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.6">
          <circle cx="8" cy="8" r="2.2" />
          <path d="M8 1.5C5.5 1.5 3.8 3.6 4.5 5.8M8 1.5C10.5 1.5 12.2 3.6 11.5 5.8" strokeLinecap="round" />
          <path d="M2.4 11.2C1.2 9 2.1 6.5 4.4 5.9M13.6 11.2C14.8 9 13.9 6.5 11.6 5.9" strokeLinecap="round" />
          <path d="M5.6 13.8C7 15 9 15 10.4 13.8" strokeLinecap="round" />
        </svg>
        Pathogen Override
      </span>
      <span className="tooltip" role="tooltip">
        {reason ||
          'BIS IS 10500 mandates 0 CFU/100 mL for E. coli & Total Coliform. Any detection forces Critical status regardless of weighted score.'}
      </span>
    </span>
  );
}

function ArsenicBadge({ reason }) {
  return (
    <span className="has-tooltip" style={{ display: 'inline-flex', alignItems: 'center' }}>
      <span
        className="badge-pathogen"
        tabIndex={0}
        style={{
          borderColor: 'var(--high)',
          color: 'var(--critical)',
          background: 'color-mix(in oklch, var(--high) 14%, transparent)',
        }}
      >
        <span>As</span> Arsenic Escalation
      </span>
      <span className="tooltip" role="tooltip">
        {reason ||
          'BIS IS 10500 Amendment 1 sets 0.01 mg/L for Total Arsenic with no relaxation. Severe village/habitation burden forces Critical status.'}
      </span>
    </span>
  );
}

function DistrictCartogram({ districts, selectedDistrict, onSelectDistrict, stateFilter }) {
  const upDistricts = useMemo(
    () =>
      districts
        .filter((d) => d.state === 'Uttar Pradesh')
        .sort((a, b) => a.district.localeCompare(b.district)),
    [districts]
  );
  const biharDistricts = useMemo(
    () =>
      districts
        .filter((d) => d.state === 'Bihar')
        .sort((a, b) => a.district.localeCompare(b.district)),
    [districts]
  );

  const renderGrid = (list, cols, title, subtitle) => {
    const tileW = 68;
    const tileH = 44;
    const gap = 6;
    const rows = Math.ceil(list.length / cols);
    const svgW = cols * (tileW + gap) + gap;
    const svgH = rows * (tileH + gap) + gap;

    return (
      <div className="sketch-box" style={{ padding: 18 }}>
        <div className="row-between" style={{ marginBottom: 12, flexWrap: 'wrap', gap: 8 }}>
          <div>
            <div className="eyebrow" style={{ marginBottom: 2 }}>{subtitle}</div>
            <h3 className="h3" style={{ fontSize: 17 }}>{title} ({list.length} Districts)</h3>
          </div>
          <div className="row" style={{ gap: 8, flexWrap: 'wrap' }}>
            {['Critical', 'High', 'Medium', 'Low'].map((b) => (
              <span key={b} className={BAND_BADGE[b]}>
                {b}: {list.filter((d) => d.band === b).length}
              </span>
            ))}
          </div>
        </div>
        <div style={{ overflowX: 'auto' }}>
          <svg
            viewBox={`0 0 ${svgW} ${svgH}`}
            style={{ width: '100%', height: 'auto', minWidth: Math.min(svgW, 560), display: 'block' }}
            role="img"
            aria-label={`${title} 100% District Risk Cartogram`}
          >
            {list.map((d, idx) => {
              const r = Math.floor(idx / cols);
              const c = idx % cols;
              const x = gap + c * (tileW + gap);
              const y = gap + r * (tileH + gap);
              const isSel =
                selectedDistrict &&
                selectedDistrict.district === d.district &&
                selectedDistrict.state === d.state;
              const bColor = BAND_COLORS[d.band] || 'var(--low)';
              const code = d.district
                .replace(/[^A-Za-z ]/g, '')
                .split(' ')
                .filter(Boolean)
                .map((w) => w[0])
                .join('')
                .slice(0, 3)
                .toUpperCase();
              const shortCode = code.length >= 2 ? code : d.district.slice(0, 3).toUpperCase();

              return (
                <g
                  key={`${d.state}-${d.district}`}
                  transform={`translate(${x}, ${y})`}
                  onClick={() => onSelectDistrict(d)}
                  style={{ cursor: 'pointer' }}
                >
                  <title>
                    {`${d.district} (${d.state}) — Rank #${d.rank} | Band: ${d.band} | Score: ${d.unified_score.toFixed(1)} | Worst: ${d.worst_parameter} | WQ6 Villages: ${d.wq6_villages.total_contaminated_villages} | Samples: ${d.sample_stats.total_samples}`}
                  </title>
                  <rect
                    width={tileW}
                    height={tileH}
                    rx={3}
                    fill={bColor}
                    fillOpacity={isSel ? 0.34 : 0.16}
                    stroke={isSel ? 'var(--fg)' : bColor}
                    strokeWidth={isSel ? 2.6 : d.is_pathogen_override ? 1.8 : 1.2}
                    strokeDasharray={d.is_pathogen_override ? '3 2' : undefined}
                  />
                  <text
                    x={6}
                    y={14}
                    fontFamily="var(--font-mono)"
                    fontSize="10"
                    fontWeight="700"
                    fill="var(--fg)"
                  >
                    {shortCode}
                  </text>
                  {d.is_pathogen_override && (
                    <text
                      x={tileW - 6}
                      y={13}
                      textAnchor="end"
                      fontFamily="var(--font-mono)"
                      fontSize="9"
                      fontWeight="700"
                      fill="var(--critical)"
                    >
                      ☣
                    </text>
                  )}
                  {!d.is_pathogen_override && d.is_arsenic_override && (
                    <text
                      x={tileW - 5}
                      y={13}
                      textAnchor="end"
                      fontFamily="var(--font-mono)"
                      fontSize="8"
                      fontWeight="700"
                      fill="var(--critical)"
                    >
                      As
                    </text>
                  )}
                  <text
                    x={6}
                    y={27}
                    fontFamily="var(--font-sketch)"
                    fontSize="8.5"
                    fill="var(--muted)"
                  >
                    {d.district.length > 9 ? d.district.slice(0, 8) + '…' : d.district}
                  </text>
                  <text
                    x={6}
                    y={39}
                    fontFamily="var(--font-mono)"
                    fontSize="9.5"
                    fontWeight="700"
                    fill={bColor}
                  >
                    {d.unified_score.toFixed(1)}
                  </text>
                  <text
                    x={tileW - 5}
                    y={39}
                    textAnchor="end"
                    fontFamily="var(--font-mono)"
                    fontSize="8"
                    fill="var(--muted)"
                  >
                    #{d.rank}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>
      </div>
    );
  };

  return (
    <div className="stack" style={{ gap: 20 }}>
      {(stateFilter === 'ALL' || stateFilter === 'Uttar Pradesh') &&
        renderGrid(upDistricts, 11, 'Uttar Pradesh District Risk Grid', '75 Canonical Districts · 18 Divisions')}
      {(stateFilter === 'ALL' || stateFilter === 'Bihar') &&
        renderGrid(biharDistricts, 10, 'Bihar District Risk Grid', '38 Canonical Districts · 9 Divisions')}
    </div>
  );
}

export default function App() {
  const [theme, setTheme] = useState(() => localStorage.getItem('wt-theme') || 'dark');
  const [activeTab, setActiveTab] = useState('A');
  // 'districts-113' | 'samples-enriched' | 'samples-frozen'
  const [datasetMode, setDatasetMode] = useState('districts-113');
  // For sample modes: 'v1' (1/n tested weight, 89 Crit) | 'v2' (1/6.0 total BIS weight, 3 Crit)
  const [sampleScoringModel, setSampleScoringModel] = useState('v1');

  const [healthMode, setHealthMode] = useState('checking');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [fullTriage, setFullTriage] = useState(null);
  const [dashboardData, setDashboardData] = useState(null);
  const [metaData, setMetaData] = useState(null);
  const [scoringParams, setScoringParams] = useState([]);
  const [validationData, setValidationData] = useState(null);

  // Filters
  const [stateFilter, setStateFilter] = useState('ALL');
  const [bandFilter, setBandFilter] = useState('ALL');
  const [paramFilter, setParamFilter] = useState('ALL');
  const [specialFilter, setSpecialFilter] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [page, setPage] = useState(1);
  const PAGE_SIZE = 25;

  // Selected items for Variant C split view
  const [selectedDistrictName, setSelectedDistrictName] = useState('Unnao');
  const [selectedSampleId, setSelectedSampleId] = useState(null);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('wt-theme', theme);
  }, [theme]);

  useEffect(() => {
    let cancelled = false;
    async function loadAll() {
      setLoading(true);
      setError(null);
      try {
        const [ftRes, ddRes, metaRes, spRes, valRes] = await Promise.all([
          fetchWithFallback('/api/districts/full-triage', 'full-113-triage.json'),
          fetchWithFallback('/api/dashboard-data', 'dashboard-data.json'),
          fetchWithFallback('/api/meta', 'meta.json'),
          fetchWithFallback('/api/scoring/parameters', 'scoring-parameters.json'),
          fetchWithFallback('/api/validation/cgwb', 'validation-cgwb.json'),
        ]);
        if (cancelled) return;
        setFullTriage(ftRes.data);
        setDashboardData(ddRes.data);
        setMetaData(metaRes.data);
        setScoringParams(Array.isArray(spRes.data) ? spRes.data : []);
        setValidationData(valRes.data);
        setHealthMode(ftRes.source === 'live' || ddRes.source === 'live' ? 'live' : 'snapshot');

        if (ftRes.data?.districts?.length > 0) {
          setSelectedDistrictName(ftRes.data.districts[0].district);
        }
        if (ddRes.data?.priority?.length > 0) {
          setSelectedSampleId(ddRes.data.priority[0].sample_id);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.message || 'Failed to load water quality triage data.');
          setHealthMode('offline');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    loadAll();
    return () => {
      cancelled = true;
    };
  }, []);

  // Filtered 113 districts
  const allDistricts = useMemo(() => fullTriage?.districts || [], [fullTriage]);

  const filteredDistricts = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    return allDistricts.filter((d) => {
      if (stateFilter !== 'ALL' && d.state !== stateFilter) return false;
      if (bandFilter !== 'ALL' && d.band !== bandFilter) return false;
      if (paramFilter !== 'ALL' && d.worst_parameter_key !== paramFilter) return false;
      if (specialFilter === 'PATHOGEN' && !d.is_pathogen_override) return false;
      if (specialFilter === 'ARSENIC' && !d.is_arsenic_override) return false;
      if (specialFilter === 'CHRONIC' && d.recurrence_verdict !== 'chronic-hotspot') return false;
      if (specialFilter === 'INFERRED' && (d.sample_stats?.lab_inferred_samples || 0) === 0) return false;
      if (q) {
        const hay = `${d.district} ${d.state} ${d.worst_parameter} ${d.recurrence_verdict}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });
  }, [allDistricts, stateFilter, bandFilter, paramFilter, specialFilter, searchQuery]);

  // Filtered 1,741 samples
  const allSamples = useMemo(() => {
    const rawList = dashboardData?.priority || [];
    return rawList.map((row) => {
      const useEnriched = datasetMode === 'samples-enriched';
      const dist = useEnriched
        ? row.inferred_district || row.district || 'Not available'
        : row.district || 'Not available';
      const vil = useEnriched
        ? row.extracted_location && row.extracted_location !== 'Not available'
          ? row.extracted_location
          : row.village || 'Not available'
        : row.village || 'Not available';
      const score =
        sampleScoringModel === 'v2' && typeof row.score_v2 === 'number'
          ? row.score_v2
          : Number(row.score || 0);
      const band =
        sampleScoringModel === 'v2' && row.band_v2 ? row.band_v2 : row.band || 'Low';
      const isInferred =
        useEnriched &&
        row.district === 'Not available' &&
        row.inferred_district &&
        row.inferred_district !== 'Not available';
      return {
        ...row,
        display_district: dist,
        display_village: vil,
        display_score: score,
        display_band: band,
        is_inferred: isInferred,
      };
    });
  }, [dashboardData, datasetMode, sampleScoringModel]);

  const filteredSamples = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    return allSamples.filter((s) => {
      if (stateFilter !== 'ALL' && s.state !== stateFilter) return false;
      if (bandFilter !== 'ALL' && s.display_band !== bandFilter) return false;
      if (paramFilter !== 'ALL' && (s.worst || '').toLowerCase() !== paramFilter) return false;
      if (specialFilter === 'PATHOGEN' && !s.is_pathogen_override) return false;
      if (specialFilter === 'INFERRED' && !s.is_inferred) return false;
      if (q) {
        const hay = `${s.display_village} ${s.display_district} ${s.state} ${s.ref} ${s.worst}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });
  }, [allSamples, stateFilter, bandFilter, paramFilter, specialFilter, searchQuery]);

  useEffect(() => {
    setPage(1);
  }, [datasetMode, sampleScoringModel, stateFilter, bandFilter, paramFilter, specialFilter, searchQuery]);

  const activeList = datasetMode === 'districts-113' ? filteredDistricts : filteredSamples;
  const totalPages = Math.max(1, Math.ceil(activeList.length / PAGE_SIZE));
  const pagedItems = useMemo(() => {
    const start = (page - 1) * PAGE_SIZE;
    return activeList.slice(start, start + PAGE_SIZE);
  }, [activeList, page]);

  const selectedDistrictObj = useMemo(() => {
    return (
      allDistricts.find((d) => d.district === selectedDistrictName) ||
      filteredDistricts[0] ||
      allDistricts[0] ||
      null
    );
  }, [allDistricts, filteredDistricts, selectedDistrictName]);

  const selectedSampleObj = useMemo(() => {
    const row =
      allSamples.find((s) => String(s.sample_id) === String(selectedSampleId)) ||
      filteredSamples[0] ||
      allSamples[0] ||
      null;
    if (!row) return null;
    const det = dashboardData?.details?.[String(row.sample_id)] || { readings: [] };
    return { ...row, details: det };
  }, [allSamples, filteredSamples, selectedSampleId, dashboardData]);

  function handleExportCsv() {
    if (datasetMode === 'districts-113') {
      const headers = [
        'Rank', 'District', 'State', 'Band', 'Unified_CRS', 'Raw_Math_Score',
        'Pathogen_Override', 'Arsenic_Override', 'Worst_Parameter', 'Recurrence_Verdict',
        'Total_Lab_Samples', 'Submitter_Samples', 'Lab_Inferred_Samples',
        'WQ6_Contaminated_Villages', 'WQ6_E_Coli', 'WQ6_Total_Coliform',
        'WQ6_Arsenic', 'WQ6_Fluoride', 'WQ6_Iron', 'IMIS_2009_2012_Events',
      ];
      const lines = [headers.join(',')];
      filteredDistricts.forEach((d) => {
        lines.push(
          [
            d.rank,
            `"${d.district}"`,
            `"${d.state}"`,
            d.band,
            d.unified_score,
            d.raw_math_score,
            d.is_pathogen_override,
            d.is_arsenic_override,
            `"${d.worst_parameter}"`,
            d.recurrence_verdict,
            d.sample_stats.total_samples,
            d.sample_stats.submitter_samples,
            d.sample_stats.lab_inferred_samples,
            d.wq6_villages.total_contaminated_villages,
            d.wq6_villages.E_coli,
            d.wq6_villages.Total_Coliform,
            d.wq6_villages.Total_Arsenic,
            d.wq6_villages.Fluoride,
            d.wq6_villages.Iron,
            d.imis_history.total_events,
          ].join(',')
        );
      });
      const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `watertriage_113_districts_${stateFilter.toLowerCase()}.csv`;
      a.click();
      URL.revokeObjectURL(url);
    } else {
      const headers = [
        'Rank', 'Sample_ID', 'WQMIS_Ref', 'Village_Location', 'District',
        'District_Source', 'State', 'Band', 'Score', 'Worst_Parameter',
        'Scored_Params', 'Collected_On',
      ];
      const lines = [headers.join(',')];
      filteredSamples.forEach((r, idx) => {
        lines.push(
          [
            idx + 1,
            r.sample_id,
            `"${r.ref || ''}"`,
            `"${(r.display_village || '').replace(/"/g, '""')}"`,
            `"${(r.display_district || '').replace(/"/g, '""')}"`,
            `"${r.district_resolution_source || 'submitter_address'}"`,
            `"${r.state || ''}"`,
            r.display_band,
            r.display_score,
            `"${r.worst || ''}"`,
            r.n_scored_params || '',
            `"${(r.date || '').slice(0, 10)}"`,
          ].join(',')
        );
      });
      const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `watertriage_samples_${datasetMode}_${sampleScoringModel}.csv`;
      a.click();
      URL.revokeObjectURL(url);
    }
  }

  const triageSummary = fullTriage?.summary || {
    total_districts: 113,
    up_districts: 75,
    bihar_districts: 38,
    bands: { Critical: 46, High: 27, Medium: 19, Low: 21 },
    pathogen_overrides: 32,
    arsenic_overrides: 13,
    resolved_lab_samples: 302,
    unassigned_lab_samples_total: 354,
    recovered_villages: 305,
    worst_parameter_distribution: [],
  };

  const sampleKpi = useMemo(() => {
    if (sampleScoringModel === 'v2') {
      return { samples: 1741, critical: 3, high: 54, medium: 125, low: 1559 };
    }
    return dashboardData?.kpi || { samples: 1741, critical: 89, high: 392, medium: 28, low: 1232 };
  }, [dashboardData, sampleScoringModel]);

  return (
    <div>
      {/* ─── TOP STICKY NAVIGATION ─── */}
      <header className="topnav">
        <div className="container topnav-inner">
          <a href="#top" className="logo">
            <span>WaterTriage · UP &amp; Bihar</span>
            <span className="pill" style={{ marginLeft: 4 }}>BIS IS 10500:2012</span>
          </a>

          <nav aria-label="Primary sections">
            <a href="#workspace" onClick={() => setActiveTab('A')}>Priority Queue</a>
            <a href="#workspace" onClick={() => setActiveTab('B')}>113-District Map</a>
            <a href="#workspace" onClick={() => setActiveTab('C')}>Master-Detail Split</a>
            <a href="#workspace" onClick={() => setActiveTab('D')}>Validation</a>
            <a href="#workspace" onClick={() => setActiveTab('overview')}>Overview</a>
            <a href="#workspace" onClick={() => setActiveTab('methodology')}>Methodology</a>
            <a href="#charts">Charts</a>
            <a href="#architecture">Architecture</a>
            <a href="#notes">Field Notes</a>
          </nav>

          <div className="row" style={{ gap: 10 }}>
            <div
              className={`status-pill ${healthMode}`}
              title={
                healthMode === 'live'
                  ? 'Connected to live FastAPI + PostgreSQL backend'
                  : 'Serving verified 113-district + 1,741-sample snapshot'
              }
            >
              <span className="status-dot" />
              <span>
                {healthMode === 'live'
                  ? 'API Live · 113 Dist.'
                  : healthMode === 'snapshot'
                  ? 'Verified Snapshot · 113 Dist.'
                  : 'Checking...'}
              </span>
            </div>

            <button
              type="button"
              className="theme-toggle"
              onClick={() => setTheme((t) => (t === 'dark' ? 'light' : 'dark'))}
              aria-label="Toggle dark and light paper theme"
              title="Switch paper/ink theme"
            >
              <svg className="icon-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
              </svg>
              <svg className="icon-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
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
          </div>
        </div>
      </header>

      <main id="top" className="container">
        {/* ─── HERO & DATASET MODE SWITCHER ─── */}
        <section className="section hero" style={{ paddingBlock: 'clamp(32px, 5vw, 56px)' }}>
          <div className="eyebrow">
            00 / Full-Coverage Multi-Tier Water Quality Risk Scoring · Uttar Pradesh (75) &amp; Bihar (38)
          </div>
          <h1 className="h1" style={{ marginBottom: 14 }}>
            Every District Scored. Every Pathogen Override Surfaced.
          </h1>
          <p className="lead" style={{ maxWidth: '78ch', marginBottom: 22 }}>
            Fuses <strong>1,741 JJM WQMIS laboratory reports</strong> (with{' '}
            <strong>302/354 unassigned samples resolved across 20 testing labs</strong> via the ASP.NET{' '}
            <code>Report_p</code> session handshake and <strong>305 village names recovered</strong>),{' '}
            <strong>all 113 official Form WQ6 district tables</strong> (75 UP + 38 Bihar across 16 parameters),{' '}
            <strong>100,690 historical IMIS contamination events</strong> (2009–2012 across 93 districts), and{' '}
            <strong>CGWB groundwater monitoring stations</strong> (2012–2021) into a unified BIS IS 10500:2012
            intervention queue.
          </p>

          {/* DATASET MODE SWITCHER BAR */}
          <div
            className="sketch-box"
            style={{
              padding: '14px 18px',
              marginBottom: 26,
              background: 'color-mix(in oklch, var(--accent) 7%, var(--surface))',
            }}
          >
            <div className="row-between" style={{ flexWrap: 'wrap', gap: 12 }}>
              <div>
                <div className="meta" style={{ fontWeight: 700, color: 'var(--fg)' }}>
                  ACTIVE SCORING ENGINE MODE
                </div>
                <div className="meta">
                  Switch between Full 113-District Multi-Tier Triage, Enriched 1,741 Lab Reports (302 Lab-IDs resolved), or Frozen WPR-12 Report Baseline:
                </div>
              </div>
              <div className="row" style={{ gap: 8, flexWrap: 'wrap' }}>
                <button
                  type="button"
                  className={`btn ${datasetMode === 'districts-113' ? 'btn-primary' : 'btn-secondary'}`}
                  style={{ padding: '8px 14px', minHeight: 38, fontSize: 11 }}
                  onClick={() => setDatasetMode('districts-113')}
                >
                  1. Full 113-District Triage (UP 75 + Bihar 38)
                </button>
                <button
                  type="button"
                  className={`btn ${datasetMode === 'samples-enriched' ? 'btn-primary' : 'btn-secondary'}`}
                  style={{ padding: '8px 14px', minHeight: 38, fontSize: 11 }}
                  onClick={() => setDatasetMode('samples-enriched')}
                >
                  2. Enriched Lab Queue (1,741 Samples · 97% Located)
                </button>
                <button
                  type="button"
                  className={`btn ${datasetMode === 'samples-frozen' ? 'btn-primary' : 'btn-secondary'}`}
                  style={{ padding: '8px 14px', minHeight: 38, fontSize: 11 }}
                  onClick={() => setDatasetMode('samples-frozen')}
                >
                  3. Frozen WPR-12 Baseline (1,741 Samples)
                </button>
              </div>
            </div>

            {datasetMode !== 'districts-113' && (
              <div
                className="row-between"
                style={{
                  marginTop: 12,
                  paddingTop: 10,
                  borderTop: '1px dashed var(--border)',
                  flexWrap: 'wrap',
                  gap: 10,
                }}
              >
                <span className="meta">
                  <strong>Sample Normalization Formula:</strong> Choose between Model v1 (<code>1/W_tested</code>,
                  75/50/25 bands → 89 Critical) and Model v2 (<code>1/6.0</code> fixed BIS weight, 40/20/10 bands → 3
                  Critical):
                </span>
                <div className="row" style={{ gap: 8 }}>
                  <button
                    type="button"
                    className={`btn ${sampleScoringModel === 'v1' ? 'btn-primary' : 'btn-secondary'}`}
                    style={{ padding: '5px 12px', minHeight: 32, fontSize: 10 }}
                    onClick={() => setSampleScoringModel('v1')}
                  >
                    Model v1 (1/n Tested · 89 Crit / 392 High)
                  </button>
                  <button
                    type="button"
                    className={`btn ${sampleScoringModel === 'v2' ? 'btn-primary' : 'btn-secondary'}`}
                    style={{ padding: '5px 12px', minHeight: 32, fontSize: 10 }}
                    onClick={() => setSampleScoringModel('v2')}
                  >
                    Model v2 (1/6.0 Fixed · 3 Crit / 54 High / 125 Med)
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* 4-COLUMN KPI STAT STRIP */}
          {datasetMode === 'districts-113' ? (
            <div className="grid-4">
              <div className="sketch-box stat">
                <span className="sketch-section-label">COVERAGE</span>
                <div className="stat-num num">
                  {triageSummary.total_districts}
                  <span className="stat-unit">dist</span>
                </div>
                <div className="stat-label">
                  75 Uttar Pradesh + 38 Bihar (100% Canonical District Coverage)
                </div>
              </div>
              <div className="sketch-box stat">
                <span className="sketch-section-label">ACUTE CRITICAL</span>
                <div className="stat-num num" style={{ color: 'var(--critical)' }}>
                  {triageSummary.bands.Critical}
                  <span className="stat-unit">
                    ({((triageSummary.bands.Critical / triageSummary.total_districts) * 100).toFixed(1)}%)
                  </span>
                </div>
                <div className="stat-label">
                  {triageSummary.pathogen_overrides} Pathogen Overrides (E. coli) + {triageSummary.arsenic_overrides}{' '}
                  Arsenic Escalations
                </div>
              </div>
              <div className="sketch-box stat">
                <span className="sketch-section-label">HIGH &amp; MEDIUM RISK</span>
                <div className="stat-num num" style={{ color: 'var(--high)' }}>
                  {triageSummary.bands.High}
                  <span className="stat-unit">high</span>
                </div>
                <div className="stat-label">
                  Plus {triageSummary.bands.Medium} Medium-band districts &amp; {triageSummary.bands.Low} Low-band
                  districts
                </div>
              </div>
              <div className="sketch-box stat">
                <span className="sketch-section-label">GAP RECOVERY</span>
                <div className="stat-num num" style={{ color: 'var(--accent)' }}>
                  302
                  <span className="stat-unit">/354</span>
                </div>
                <div className="stat-label">
                  85.3% Missing Lab Districts Solved (20 Labs) · 305 Villages Extracted
                </div>
              </div>
            </div>
          ) : (
            <div className="grid-4">
              <div className="sketch-box stat">
                <span className="sketch-section-label">SCORED LAB SAMPLES</span>
                <div className="stat-num num">{sampleKpi.samples.toLocaleString()}</div>
                <div className="stat-label">
                  966 Uttar Pradesh · 775 Bihar ·{' '}
                  {datasetMode === 'samples-enriched'
                    ? '1,689 (97.0%) District-Located'
                    : '1,387 (79.7%) Submitter-Located'}
                </div>
              </div>
              <div className="sketch-box stat">
                <span className="sketch-section-label">CRITICAL SAMPLES</span>
                <div className="stat-num num" style={{ color: 'var(--critical)' }}>
                  {sampleKpi.critical}
                  <span className="stat-unit">
                    ({((sampleKpi.critical / sampleKpi.samples) * 100).toFixed(1)}%)
                  </span>
                </div>
                <div className="stat-label">
                  {sampleScoringModel === 'v1'
                    ? 'Includes 70 Madhepura 1-param iron tests + Lucknow E. coli'
                    : 'Acute microbial breaches (Lucknow E. coli + Coliform)'}
                </div>
              </div>
              <div className="sketch-box stat">
                <span className="sketch-section-label">HIGH BAND SAMPLES</span>
                <div className="stat-num num" style={{ color: 'var(--high)' }}>
                  {sampleKpi.high}
                  <span className="stat-unit">
                    ({((sampleKpi.high / sampleKpi.samples) * 100).toFixed(1)}%)
                  </span>
                </div>
                <div className="stat-label">
                  Driven by Iron (&gt;0.3 mg/L), Fluoride (&gt;1.5 mg/L), &amp; Turbidity
                </div>
              </div>
              <div className="sketch-box stat">
                <span className="sketch-section-label">MEDIUM &amp; LOW</span>
                <div className="stat-num num" style={{ color: 'var(--low)' }}>
                  {(sampleKpi.medium + sampleKpi.low).toLocaleString()}
                </div>
                <div className="stat-label">
                  {sampleKpi.medium} Medium ({((sampleKpi.medium / sampleKpi.samples) * 100).toFixed(1)}%) ·{' '}
                  {sampleKpi.low.toLocaleString()} Low
                </div>
              </div>
            </div>
          )}
        </section>

        {/* ─── SECTION 01: 4-TAB INTERACTIVE TRIAGE WORKSPACE ─── */}
        <section id="workspace" className="section">
          <div className="row-between" style={{ marginBottom: 16, flexWrap: 'wrap', gap: 12 }}>
            <div>
              <div className="eyebrow" style={{ marginBottom: 4 }}>01 / Interactive Triage Workspace</div>
              <h2 className="h2">Four Coordinated Views of UP &amp; Bihar Water Risk</h2>
            </div>
            <div className="row" style={{ gap: 8, flexWrap: 'wrap' }}>
              <button type="button" className="btn btn-secondary" onClick={handleExportCsv}>
                Export Current View CSV ({activeList.length} rows)
              </button>
            </div>
          </div>

          <div className="tab-row" role="tablist" aria-label="Triage workspace views">
            <button
              type="button"
              role="tab"
              aria-selected={activeTab === 'A'}
              className={`tab-btn ${activeTab === 'A' ? 'active' : ''}`}
              onClick={() => setActiveTab('A')}
            >
              Variant A — Priority Queue ({activeList.length})
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={activeTab === 'B'}
              className={`tab-btn ${activeTab === 'B' ? 'active' : ''}`}
              onClick={() => setActiveTab('B')}
            >
              Variant B — 113-District Map + Cards
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={activeTab === 'C'}
              className={`tab-btn ${activeTab === 'C' ? 'active' : ''}`}
              onClick={() => setActiveTab('C')}
            >
              Variant C — District + Detail Split
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={activeTab === 'D'}
              className={`tab-btn ${activeTab === 'D' ? 'active' : ''}`}
              onClick={() => setActiveTab('D')}
            >
              Variant D — External Validation
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={activeTab === 'overview'}
              className={`tab-btn ${activeTab === 'overview' ? 'active' : ''}`}
              onClick={() => setActiveTab('overview')}
            >
              Overview &amp; Sensitivity
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={activeTab === 'methodology'}
              className={`tab-btn ${activeTab === 'methodology' ? 'active' : ''}`}
              onClick={() => setActiveTab('methodology')}
            >
              Methodology &amp; Limitations
            </button>
          </div>

          {/* SHARED FILTER BAR FOR TABS A, B, C */}
          {['A', 'B', 'C'].includes(activeTab) && (
            <div
              style={{
                borderLeft: '2px solid var(--fg)',
                borderRight: '2px solid var(--fg)',
                borderBottom: '1px dashed var(--border)',
                background: 'var(--surface)',
                padding: '16px 24px',
              }}
            >
              <div className="grid-4" style={{ gap: 12 }}>
                <div className="field">
                  <label htmlFor="f-state">State Filter</label>
                  <select
                    id="f-state"
                    className="input"
                    value={stateFilter}
                    onChange={(e) => setStateFilter(e.target.value)}
                  >
                    <option value="ALL">All States (UP 75 + Bihar 38)</option>
                    <option value="Uttar Pradesh">Uttar Pradesh (75 Districts / 966 Samples)</option>
                    <option value="Bihar">Bihar (38 Districts / 775 Samples)</option>
                  </select>
                </div>

                <div className="field">
                  <label htmlFor="f-band">Risk Band</label>
                  <select
                    id="f-band"
                    className="input"
                    value={bandFilter}
                    onChange={(e) => setBandFilter(e.target.value)}
                  >
                    <option value="ALL">All Risk Bands</option>
                    <option value="Critical">Critical (≥ 40 or Acute Override)</option>
                    <option value="High">High (20 – 39.9)</option>
                    <option value="Medium">Medium (10 – 19.9)</option>
                    <option value="Low">Low (&lt; 10)</option>
                  </select>
                </div>

                <div className="field">
                  <label htmlFor="f-special">Hazard / Attribution Filter</label>
                  <select
                    id="f-special"
                    className="input"
                    value={specialFilter}
                    onChange={(e) => setSpecialFilter(e.target.value)}
                  >
                    <option value="ALL">All Records</option>
                    <option value="PATHOGEN">☣ Pathogen Override Only (E. coli / Coliform)</option>
                    {datasetMode === 'districts-113' && (
                      <option value="ARSENIC">As Arsenic Escalation Only (13 Districts)</option>
                    )}
                    {datasetMode === 'districts-113' && (
                      <option value="CHRONIC">Chronic Hotspot Recurrence Only</option>
                    )}
                    <option value="INFERRED">ASP.NET Lab-ID Resolved Districts Only</option>
                  </select>
                </div>

                <div className="field">
                  <label htmlFor="f-search">Search District / Village / Sample ID</label>
                  <input
                    id="f-search"
                    type="text"
                    className="input"
                    placeholder="e.g. Unnao, Rae Bareli, L405, Samastipur..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                  />
                </div>
              </div>
            </div>
          )}

          {loading && (
            <div className="tab-panel active">
              <div className="skeleton" style={{ height: 260 }} />
            </div>
          )}

          {error && (
            <div className="tab-panel active">
              <div className="error-box">{error}</div>
            </div>
          )}

          {/* ─── TAB A: PRIORITY QUEUE (LIST) ─── */}
          {!loading && !error && activeTab === 'A' && (
            <div
              className="tab-panel active"
              data-note=" Ranked by BIS 10500 composite severity; Pathogen Overrides pinned to Critical"
            >
              {datasetMode === 'districts-113' ? (
                <>
                  <div className="row-between" style={{ marginBottom: 14, flexWrap: 'wrap', gap: 10 }}>
                    <span className="meta">
                      Showing <strong>{ pagedItems.length }</strong> of{' '}
                      <strong>{filteredDistricts.length}</strong> scored canonical districts (Page {page} of{' '}
                      {totalPages})
                    </span>
                    <span className="meta">
                      <strong>32</strong> Pathogen Overrides (☣) · <strong>13</strong> Arsenic Escalations (As) ·{' '}
                      <strong>113/113</strong> Districts Scored
                    </span>
                  </div>

                  <div style={{ overflowX: 'auto' }}>
                    <table className="ds-table">
                      <thead>
                        <tr>
                          <th>Rank</th>
                          <th>District</th>
                          <th>State</th>
                          <th className="num-col">Unified CRS</th>
                          <th>Risk Band &amp; Override</th>
                          <th>Primary Driver</th>
                          <th className="num-col">WQ6 Villages</th>
                          <th className="num-col">Lab Samples</th>
                          <th>IMIS Recurrence</th>
                          <th />
                        </tr>
                      </thead>
                      <tbody>
                        {pagedItems.map((d) => (
                          <tr
                            key={`${d.state}-${d.district}`}
                            style={
                              d.is_pathogen_override
                                ? {
                                    borderLeft: '3px dashed var(--critical)',
                                    background: 'color-mix(in oklch, var(--critical) 5%, transparent)',
                                  }
                                : d.is_arsenic_override
                                ? {
                                    borderLeft: '3px dashed var(--high)',
                                    background: 'color-mix(in oklch, var(--high) 4%, transparent)',
                                  }
                                : undefined
                            }
                          >
                            <td className="num">#{d.rank}</td>
                            <td style={{ fontWeight: 700 }}>{d.district}</td>
                            <td>{d.state}</td>
                            <td className="num-col">
                              {(d.is_pathogen_override || d.is_arsenic_override) &&
                              d.raw_math_score < d.unified_score ? (
                                <span>
                                  <span
                                    style={{
                                      textDecoration: 'line-through',
                                      color: 'var(--muted)',
                                      fontSize: 11,
                                      marginRight: 6,
                                    }}
                                    title={`Pre-escalation math score: ${d.raw_math_score}`}
                                  >
                                    {d.raw_math_score.toFixed(1)}
                                  </span>
                                  <strong style={{ color: 'var(--critical)' }}>
                                    {d.unified_score.toFixed(1)}
                                  </strong>
                                </span>
                              ) : (
                                <strong>{d.unified_score.toFixed(1)}</strong>
                              )}
                            </td>
                            <td>
                              <div className="row" style={{ gap: 6, flexWrap: 'wrap' }}>
                                <span className={BAND_BADGE[d.band] || 'badge'}>{d.band}</span>
                                {d.is_pathogen_override && <PathogenBadge reason={d.override_reason} />}
                                {d.is_arsenic_override && <ArsenicBadge reason={d.override_reason} />}
                              </div>
                            </td>
                            <td>
                              <span className="pill">{d.worst_parameter}</span>
                            </td>
                            <td className="num-col">
                              <strong>{d.wq6_villages.total_contaminated_villages.toLocaleString()}</strong>
                              {d.wq6_villages.E_coli > 0 && (
                                <span className="meta" style={{ display: 'block', color: 'var(--critical)' }}>
                                  {d.wq6_villages.E_coli} E. coli · {d.wq6_villages.Total_Coliform} TC
                                </span>
                              )}
                            </td>
                            <td className="num-col">
                              {d.sample_stats.total_samples}
                              {d.sample_stats.lab_inferred_samples > 0 && (
                                <span
                                  className="meta"
                                  style={{ display: 'block', color: 'var(--accent)' }}
                                  title="Resolved via ASP.NET Session Cookie Lab-ID Probe"
                                >
                                  +{d.sample_stats.lab_inferred_samples} Lab-ID
                                </span>
                              )}
                            </td>
                            <td>
                              <span
                                className="tag"
                                style={{
                                  borderColor:
                                    d.recurrence_verdict === 'chronic-hotspot'
                                      ? 'var(--critical)'
                                      : 'var(--border)',
                                  color:
                                    d.recurrence_verdict === 'chronic-hotspot'
                                      ? 'var(--critical)'
                                      : 'var(--muted)',
                                }}
                              >
                                {d.recurrence_verdict} ({d.imis_history.total_events.toLocaleString()})
                              </span>
                            </td>
                            <td style={{ textAlign: 'right' }}>
                              <button
                                type="button"
                                className="btn btn-ghost"
                                style={{ padding: '4px 10px', minHeight: 32, fontSize: 11 }}
                                onClick={() => {
                                  setSelectedDistrictName(d.district);
                                  setActiveTab('C');
                                }}
                              >
                                Inspect →
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </>
              ) : (
                <>
                  <div className="row-between" style={{ marginBottom: 14, flexWrap: 'wrap', gap: 10 }}>
                    <span className="meta">
                      Showing <strong>{pagedItems.length}</strong> of{' '}
                      <strong>{filteredSamples.length.toLocaleString()}</strong> scored WQMIS lab samples (Page {page}{' '}
                      of {totalPages})
                    </span>
                    <span className="meta">
                      Mode:{' '}
                      <strong>
                        {datasetMode === 'samples-enriched'
                          ? 'Enriched (302/354 Lab-ID Districts + 305 Villages Active)'
                          : 'Frozen WPR-12 Report Snapshot'}
                      </strong>{' '}
                      · Formula: <strong>{sampleScoringModel.toUpperCase()}</strong>
                    </span>
                  </div>

                  <div style={{ overflowX: 'auto' }}>
                    <table className="ds-table">
                      <thead>
                        <tr>
                          <th>#</th>
                          <th>WQMIS Sample Ref</th>
                          <th>Village / Extracted Location</th>
                          <th>District</th>
                          <th>State</th>
                          <th className="num-col">CRS ({sampleScoringModel.toUpperCase()})</th>
                          <th>Band &amp; Override</th>
                          <th>Worst Parameter</th>
                          <th className="num-col">Params</th>
                          <th>Collected</th>
                          <th />
                        </tr>
                      </thead>
                      <tbody>
                        {pagedItems.map((s, idx) => (
                          <tr
                            key={s.sample_id}
                            style={
                              s.is_pathogen_override
                                ? {
                                    borderLeft: '3px dashed var(--critical)',
                                    background: 'color-mix(in oklch, var(--critical) 5%, transparent)',
                                  }
                                : undefined
                            }
                          >
                            <td className="num">{(page - 1) * PAGE_SIZE + idx + 1}</td>
                            <td className="num" style={{ fontSize: 12 }}>{s.ref}</td>
                            <td>
                              {s.display_village}
                              {datasetMode === 'samples-enriched' &&
                                s.village === 'Not available' &&
                                s.display_village !== 'Not available' && (
                                  <span
                                    className="tag"
                                    style={{ marginLeft: 6, color: 'var(--accent)', borderColor: 'var(--accent)' }}
                                  >
                                    +source
                                  </span>
                                )}
                            </td>
                            <td>
                              <strong>{s.display_district}</strong>
                              {s.is_inferred && (
                                <span
                                  className="tag"
                                  style={{ marginLeft: 6, color: 'var(--accent)', borderColor: 'var(--accent)' }}
                                  title={`Resolved via ${s.district_resolution_source}`}
                                >
                                  Lab-ID
                                </span>
                              )}
                            </td>
                            <td>{s.state}</td>
                            <td className="num-col">
                              <strong>{Number(s.display_score).toFixed(2)}</strong>
                            </td>
                            <td>
                              <div className="row" style={{ gap: 6, flexWrap: 'wrap' }}>
                                <span className={BAND_BADGE[s.display_band] || 'badge'}>{s.display_band}</span>
                                {s.is_pathogen_override && <PathogenBadge />}
                              </div>
                            </td>
                            <td>
                              <span className="pill">{PARAM_LABELS[s.worst] || s.worst}</span>
                            </td>
                            <td className="num-col">{s.n_scored_params || '—'}</td>
                            <td className="num">{(s.date || '').slice(0, 10)}</td>
                            <td style={{ textAlign: 'right' }}>
                              <button
                                type="button"
                                className="btn btn-ghost"
                                style={{ padding: '4px 10px', minHeight: 32, fontSize: 11 }}
                                onClick={() => {
                                  setSelectedSampleId(s.sample_id);
                                  setActiveTab('C');
                                }}
                              >
                                Readings →
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </>
              )}

              {/* PAGINATION */}
              <div className="row-between" style={{ marginTop: 18, flexWrap: 'wrap', gap: 10 }}>
                <span className="meta">
                  Page {page} of {totalPages} ({activeList.length} total matching records)
                </span>
                <div className="row" style={{ gap: 8 }}>
                  <button
                    type="button"
                    className="btn btn-secondary"
                    style={{ padding: '6px 14px', minHeight: 34, fontSize: 11 }}
                    disabled={page <= 1}
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                  >
                    ← Prev
                  </button>
                  <button
                    type="button"
                    className="btn btn-secondary"
                    style={{ padding: '6px 14px', minHeight: 34, fontSize: 11 }}
                    disabled={page >= totalPages}
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  >
                    Next →
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* ─── TAB B: 113-DISTRICT INTERACTIVE MAP + TOP-RISK CARDS ─── */}
          {!loading && !error && activeTab === 'B' && (
            <div
              className="tab-panel active"
              data-note=" Interactive 113-district SVG cartogram + top-risk district cards"
            >
              <div className="row-between" style={{ marginBottom: 16, flexWrap: 'wrap', gap: 12 }}>
                <div>
                  <h3 className="h3">
                    Interactive 113-District UP &amp; Bihar Risk Cartogram (Click Any District Tile to Inspect)
                  </h3>
                  <p className="meta" style={{ marginTop: 4 }}>
                    Tiles show 3-letter district code, Unified BIS Risk Score, rank (#1–#113), <strong>☣</strong> for
                    Pathogen Override (32 districts), and <strong>As</strong> for Arsenic Escalation (13 districts).
                  </p>
                </div>
                {selectedDistrictObj && (
                  <div className="row" style={{ gap: 10, flexWrap: 'wrap' }}>
                    <span className="pill">
                      Selected: {selectedDistrictObj.district} ({selectedDistrictObj.state}) · Score{' '}
                      {selectedDistrictObj.unified_score.toFixed(1)}
                    </span>
                    <button
                      type="button"
                      className="btn btn-primary"
                      style={{ padding: '6px 14px', minHeight: 34, fontSize: 11 }}
                      onClick={() => setActiveTab('C')}
                    >
                      Open Full District Dossier →
                    </button>
                  </div>
                )}
              </div>

              <DistrictCartogram
                districts={filteredDistricts.length > 0 ? filteredDistricts : allDistricts}
                selectedDistrict={selectedDistrictObj}
                onSelectDistrict={(d) => setSelectedDistrictName(d.district)}
                stateFilter={stateFilter}
              />

              {/* TOP 3 FEATURE CARDS BELOW MAP (RESTORED FROM OPEN_DESIGN_PROJECT) */}
              <div style={{ marginTop: 28 }}>
                <div className="eyebrow" style={{ marginBottom: 10 }}>
                  Top-Priority Intervention Districts (Current Filter)
                </div>
                <div className="grid-3">
                  {(filteredDistricts.length > 0 ? filteredDistricts : allDistricts).slice(0, 3).map((d) => (
                    <div key={d.district} className="feature-card">
                      <div className="row-between" style={{ marginBottom: 8 }}>
                        <span className={BAND_BADGE[d.band]}>{d.band} · #{d.rank}</span>
                        {d.is_pathogen_override && <PathogenBadge reason={d.override_reason} />}
                        {d.is_arsenic_override && <ArsenicBadge reason={d.override_reason} />}
                      </div>
                      <h3 className="h3">
                        {d.district} <span className="meta">({d.state})</span>
                      </h3>
                      <p style={{ marginTop: 6, marginBottom: 12 }}>
                        Worst driver: <strong>{d.worst_parameter}</strong> ·{' '}
                        <strong>{d.wq6_villages.total_contaminated_villages.toLocaleString()}</strong> WQ6 contaminated
                        villages · <strong>{d.imis_history.total_events.toLocaleString()}</strong> IMIS events (
                        {d.recurrence_verdict}).
                      </p>
                      <div style={{ marginBottom: 12 }}>
                        <div className="row-between meta" style={{ marginBottom: 4 }}>
                          <span>Unified BIS Risk Score</span>
                          <span className="num" style={{ fontWeight: 700, color: BAND_COLORS[d.band] }}>
                            {d.unified_score.toFixed(1)} / 100
                          </span>
                        </div>
                        <div className="prog-track">
                          <div className="prog-fill" style={{ width: `${Math.min(100, d.unified_score)}%` }} />
                        </div>
                      </div>
                      <button
                        type="button"
                        className="btn btn-secondary"
                        style={{ width: '100%', padding: '8px 12px', minHeight: 36, fontSize: 11 }}
                        onClick={() => {
                          setSelectedDistrictName(d.district);
                          setActiveTab('C');
                        }}
                      >
                        Inspect {d.district} Dossier →
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* ─── TAB C: MASTER-DETAIL SPLIT VIEW ─── */}
          {!loading && !error && activeTab === 'C' && (
            <div
              className="tab-panel active"
              data-note=" Master list on left; 4-tier BIS 10500 breakdown on right"
            >
              {datasetMode === 'districts-113' ? (
                <div className="grid-1-2">
                  {/* LEFT: 113-DISTRICT MASTER LIST */}
                  <div
                    className="sketch-box"
                    style={{ padding: 0, maxHeight: 680, overflowY: 'auto' }}
                    role="listbox"
                    aria-label="113 Scored Districts Master List"
                  >
                    <div
                      style={{
                        padding: '12px 16px',
                        borderBottom: '2px solid var(--fg)',
                        position: 'sticky',
                        top: 0,
                        background: 'var(--surface)',
                        zIndex: 2,
                      }}
                    >
                      <div className="meta" style={{ fontWeight: 700, color: 'var(--fg)' }}>
                        SCORED DISTRICTS ({filteredDistricts.length} / 113)
                      </div>
                      <div className="meta">Click any district to inspect all 4 data tiers</div>
                    </div>
                    {filteredDistricts.map((d) => {
                      const active = selectedDistrictObj && selectedDistrictObj.district === d.district;
                      return (
                        <div
                          key={`${d.state}-${d.district}`}
                          role="option"
                          aria-selected={active}
                          tabIndex={0}
                          onClick={() => setSelectedDistrictName(d.district)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter' || e.key === ' ') {
                              e.preventDefault();
                              setSelectedDistrictName(d.district);
                            }
                          }}
                          style={{
                            padding: '11px 16px',
                            borderBottom: '1px dashed var(--border)',
                            cursor: 'pointer',
                            background: active ? 'var(--accent-soft)' : 'transparent',
                            borderLeft: active
                              ? '4px solid var(--accent)'
                              : d.is_pathogen_override
                              ? '3px dashed var(--critical)'
                              : '4px solid transparent',
                          }}
                        >
                          <div className="row-between">
                            <div>
                              <span className="num meta" style={{ marginRight: 6 }}>#{d.rank}</span>
                              <strong style={{ fontSize: 14 }}>{d.district}</strong>
                              {d.is_pathogen_override && (
                                <span style={{ color: 'var(--critical)', marginLeft: 5 }} title="Pathogen Override">
                                  ☣
                                </span>
                              )}
                            </div>
                            <span className={BAND_BADGE[d.band]}>{d.unified_score.toFixed(1)}</span>
                          </div>
                          <div className="row-between meta" style={{ marginTop: 4 }}>
                            <span>{d.state} · {d.worst_parameter}</span>
                            <span>{d.wq6_villages.total_contaminated_villages} WQ6 vil.</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  {/* RIGHT: 4-TIER DISTRICT RISK DOSSIER */}
                  {selectedDistrictObj ? (
                    <div className="sketch-box">
                      <span className="sketch-section-label">
                        4-TIER DISTRICT DOSSIER · RANK #{selectedDistrictObj.rank} OF 113
                      </span>
                      <div className="row-between" style={{ flexWrap: 'wrap', gap: 12, marginBottom: 14 }}>
                        <div>
                          <div className="eyebrow" style={{ marginBottom: 4 }}>
                            {selectedDistrictObj.state} · Recurrence: {selectedDistrictObj.recurrence_verdict}
                          </div>
                          <h3 className="h2" style={{ fontSize: 28 }}>{selectedDistrictObj.district} District</h3>
                        </div>
                        <div style={{ textAlign: 'right' }}>
                          <div
                            className="num"
                            style={{
                              fontSize: 34,
                              fontWeight: 700,
                              color: BAND_COLORS[selectedDistrictObj.band],
                              lineHeight: 1,
                            }}
                          >
                            {selectedDistrictObj.unified_score.toFixed(1)}
                            <span style={{ fontSize: 14, color: 'var(--muted)', marginLeft: 4 }}>/ 100</span>
                          </div>
                          <div className="row" style={{ gap: 6, justifyContent: 'flex-end', marginTop: 6 }}>
                            <span className={BAND_BADGE[selectedDistrictObj.band]}>
                              {selectedDistrictObj.band} Band
                            </span>
                            {selectedDistrictObj.is_pathogen_override && (
                              <PathogenBadge reason={selectedDistrictObj.override_reason} />
                            )}
                            {selectedDistrictObj.is_arsenic_override && (
                              <ArsenicBadge reason={selectedDistrictObj.override_reason} />
                            )}
                          </div>
                        </div>
                      </div>

                      {(selectedDistrictObj.is_pathogen_override || selectedDistrictObj.is_arsenic_override) && (
                        <div
                          style={{
                            border: '1.5px dashed var(--critical)',
                            background: 'color-mix(in oklch, var(--critical) 8%, transparent)',
                            padding: '10px 14px',
                            marginBottom: 16,
                            borderRadius: 2,
                          }}
                        >
                          <div className="meta" style={{ color: 'var(--critical)', fontWeight: 700 }}>
                            ⚠ ACUTE HAZARD ESCALATION ACTIVE (RAW MATH SCORE:{' '}
                            <span style={{ textDecoration: 'line-through' }}>
                              {selectedDistrictObj.raw_math_score.toFixed(2)}
                            </span>{' '}
                            → ESCALATED TO {selectedDistrictObj.unified_score.toFixed(1)} CRITICAL)
                          </div>
                          <div className="meta" style={{ marginTop: 3 }}>
                            {selectedDistrictObj.override_reason}
                          </div>
                        </div>
                      )}

                      {/* 4-TIER EVIDENCE SUMMARY BOXES */}
                      <div className="grid-4" style={{ gap: 10, marginBottom: 20 }}>
                        <div className="hatch-box-light" style={{ padding: 10 }}>
                          <div className="meta">TIER 1 · WQMIS SAMPLES</div>
                          <div className="num" style={{ fontSize: 20, fontWeight: 700 }}>
                            {selectedDistrictObj.sample_stats.total_samples}
                          </div>
                          <div className="meta">
                            {selectedDistrictObj.sample_stats.submitter_samples} named +{' '}
                            {selectedDistrictObj.sample_stats.lab_inferred_samples} Lab-ID
                          </div>
                        </div>
                        <div className="hatch-box-light" style={{ padding: 10 }}>
                          <div className="meta">TIER 2 · WQ6 VILLAGES</div>
                          <div className="num" style={{ fontSize: 20, fontWeight: 700 }}>
                            {selectedDistrictObj.wq6_villages.total_contaminated_villages.toLocaleString()}
                          </div>
                          <div className="meta">
                            WQ6 CRS: {selectedDistrictObj.tier_scores.wq6_crs.toFixed(1)} / 100
                          </div>
                        </div>
                        <div className="hatch-box-light" style={{ padding: 10 }}>
                          <div className="meta">TIER 3 · IMIS 2009–12</div>
                          <div className="num" style={{ fontSize: 20, fontWeight: 700 }}>
                            {selectedDistrictObj.imis_history.total_events.toLocaleString()}
                          </div>
                          <div className="meta">
                            Bonus: +{selectedDistrictObj.tier_scores.imis_bonus.toFixed(1)} pts
                          </div>
                        </div>
                        <div className="hatch-box-light" style={{ padding: 10 }}>
                          <div className="meta">TIER 4 · CGWB STATIONS</div>
                          <div className="num" style={{ fontSize: 20, fontWeight: 700 }}>
                            {selectedDistrictObj.cgwb_stations.station_years}
                          </div>
                          <div className="meta">
                            Mean pH: {selectedDistrictObj.cgwb_stations.mean_ph ?? 'N/A'}
                          </div>
                        </div>
                      </div>

                      {/* 10-PARAMETER BIS 10500 SEVERITY BREAKDOWN */}
                      <h4 className="h3" style={{ fontSize: 15, marginBottom: 10 }}>
                        10-Parameter BIS IS 10500:2012 Severity Profile
                      </h4>
                      <div className="stack" style={{ gap: 10, marginBottom: 22 }}>
                        {selectedDistrictObj.parameter_breakdown.map((p) => (
                          <div key={p.key}>
                            <div className="row-between meta" style={{ marginBottom: 3 }}>
                              <span>
                                <strong style={{ color: 'var(--fg)' }}>{p.label}</strong> (w={p.weight}, limit:{' '}
                                {p.acceptable} {p.unit !== 'none' ? p.unit : ''})
                              </span>
                              <span className="num">
                                WQ6: <strong>{p.wq6_villages}</strong> vil. | Lab Exc:{' '}
                                <strong>{p.sample_exceedances}</strong>/{p.sample_tested}
                                {p.max_sample_value !== null ? ` (max ${p.max_sample_value})` : ''} | IMIS:{' '}
                                <strong>{p.imis_events}</strong> → <strong>{p.severity_pct}%</strong>
                              </span>
                            </div>
                            <div className="prog-track">
                              <div
                                className="prog-fill"
                                style={{
                                  width: `${Math.min(100, p.severity_pct)}%`,
                                  background:
                                    p.severity_pct >= 75
                                      ? 'var(--critical)'
                                      : p.severity_pct >= 35
                                      ? 'var(--high)'
                                      : undefined,
                                }}
                              />
                            </div>
                          </div>
                        ))}
                      </div>

                      {/* TOP INDIVIDUAL SAMPLES IN THIS DISTRICT */}
                      <h4 className="h3" style={{ fontSize: 15, marginBottom: 8 }}>
                        Individual WQMIS Laboratory Reports in {selectedDistrictObj.district} (
                        {selectedDistrictObj.sample_stats.total_samples} Total)
                      </h4>
                      {selectedDistrictObj.sample_stats.top_samples.length > 0 ? (
                        <div style={{ overflowX: 'auto' }}>
                          <table className="ds-table">
                            <thead>
                              <tr>
                                <th>WQMIS Sample Ref</th>
                                <th>Location / Village</th>
                                <th>Attribution</th>
                                <th className="num-col">CRS (v1)</th>
                                <th className="num-col">CRS (v2)</th>
                                <th>Worst Param</th>
                                <th>Collected</th>
                              </tr>
                            </thead>
                            <tbody>
                              {selectedDistrictObj.sample_stats.top_samples.map((ts) => (
                                <tr key={ts.ref}>
                                  <td className="num" style={{ fontSize: 12 }}>{ts.ref}</td>
                                  <td>{ts.village}</td>
                                  <td>
                                    <span className="tag">
                                      {ts.is_inferred_district ? 'ASP.NET Lab-ID Probe' : 'Submitter Address'}
                                    </span>
                                  </td>
                                  <td className="num-col">{ts.score_v1.toFixed(1)} ({ts.band_v1})</td>
                                  <td className="num-col">{ts.score_v2.toFixed(1)} ({ts.band_v2})</td>
                                  <td>{PARAM_LABELS[ts.worst] || ts.worst}</td>
                                  <td className="num">{ts.date}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      ) : (
                        <div className="callout">
                          0 individual lab reports in the 2022 crawl slice (s_id 1000000..1026000) for{' '}
                          {selectedDistrictObj.district}; district risk score ({selectedDistrictObj.unified_score.toFixed(1)})
                          is computed directly from official Form WQ6 village census (
                          {selectedDistrictObj.wq6_villages.total_contaminated_villages} contaminated villages) and
                          IMIS 2009–2012 historical registry ({selectedDistrictObj.imis_history.total_events} events).
                        </div>
                      )}
                    </div>
                  ) : null}
                </div>
              ) : (
                /* SAMPLE-LEVEL MASTER-DETAIL SPLIT */
                <div className="grid-1-2">
                  <div className="sketch-box" style={{ padding: 0, maxHeight: 640, overflowY: 'auto' }}>
                    <div
                      style={{
                        padding: '12px 16px',
                        borderBottom: '2px solid var(--fg)',
                        position: 'sticky',
                        top: 0,
                        background: 'var(--surface)',
                      }}
                    >
                      <div className="meta" style={{ fontWeight: 700, color: 'var(--fg)' }}>
                        LAB SAMPLE QUEUE (TOP 60 SHOWN)
                      </div>
                    </div>
                    {filteredSamples.slice(0, 60).map((s) => {
                      const active = selectedSampleObj && String(selectedSampleObj.sample_id) === String(s.sample_id);
                      return (
                        <div
                          key={s.sample_id}
                          onClick={() => setSelectedSampleId(s.sample_id)}
                          style={{
                            padding: '10px 16px',
                            borderBottom: '1px dashed var(--border)',
                            cursor: 'pointer',
                            background: active ? 'var(--accent-soft)' : 'transparent',
                            borderLeft: active ? '4px solid var(--accent)' : '4px solid transparent',
                          }}
                        >
                          <div className="row-between">
                            <strong style={{ fontSize: 13 }}>{s.display_district}</strong>
                            <span className={BAND_BADGE[s.display_band]}>
                              {Number(s.display_score).toFixed(1)}
                            </span>
                          </div>
                          <div className="row-between meta" style={{ marginTop: 3 }}>
                            <span>{s.ref}</span>
                            <span>{PARAM_LABELS[s.worst] || s.worst}</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  {selectedSampleObj && (
                    <div className="sketch-box">
                      <span className="sketch-section-label">PER-SAMPLE BIS READING BREAKDOWN</span>
                      <div className="row-between" style={{ marginBottom: 14, flexWrap: 'wrap', gap: 10 }}>
                        <div>
                          <div className="eyebrow" style={{ marginBottom: 4 }}>
                            WQMIS Ref: {selectedSampleObj.ref} · Collected: {(selectedSampleObj.date || '').slice(0, 10)}
                          </div>
                          <h3 className="h2" style={{ fontSize: 24 }}>
                            {selectedSampleObj.display_village} ({selectedSampleObj.display_district},{' '}
                            {selectedSampleObj.state})
                          </h3>
                        </div>
                        <span className={BAND_BADGE[selectedSampleObj.display_band]}>
                          {selectedSampleObj.display_band} · CRS {Number(selectedSampleObj.display_score).toFixed(2)}
                        </span>
                      </div>

                      <div style={{ overflowX: 'auto' }}>
                        <table className="ds-table">
                          <thead>
                            <tr>
                              <th>Parameter</th>
                              <th className="num-col">Measured Value</th>
                              <th className="num-col">BIS Acceptable</th>
                              <th className="num-col">BIS Permissible</th>
                              <th>Unit</th>
                              <th>Status</th>
                            </tr>
                          </thead>
                          <tbody>
                            {(selectedSampleObj.details?.readings || []).map((rdg, i) => {
                              const acc = rdg.acceptable;
                              const val = rdg.value;
                              const breached =
                                rdg.parameter_key === 'ph'
                                  ? val < 6.5 || val > 8.5
                                  : acc !== null && acc !== undefined
                                  ? val > acc
                                  : false;
                              return (
                                <tr key={`${rdg.parameter_key}-${i}`}>
                                  <td>
                                    <strong>{PARAM_LABELS[rdg.parameter_key] || rdg.parameter_key}</strong>
                                  </td>
                                  <td className="num-col">
                                    <strong>{val}</strong>
                                  </td>
                                  <td className="num-col">{acc ?? '—'}</td>
                                  <td className="num-col">{rdg.permissible ?? 'No relaxation'}</td>
                                  <td>{rdg.unit}</td>
                                  <td>
                                    <span className={breached ? 'badge badge-critical' : 'badge badge-low'}>
                                      {breached ? 'EXCEEDS BIS' : 'WITHIN LIMIT'}
                                    </span>
                                  </td>
                                </tr>
                              );
                            })}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* ─── TAB D: EXTERNAL VALIDATION & 4-WAY TRIANGULATION ─── */}
          {!loading && !error && activeTab === 'D' && (
            <div
              className="tab-panel active"
              data-note=" 4-Way Ground-Truth Triangulation across WQMIS, WQ6, IMIS, and CGWB"
            >
              {/* GREEN PASS BANNER */}
              <div
                style={{
                  border: '2px solid var(--low)',
                  background: 'color-mix(in oklch, var(--low) 10%, transparent)',
                  padding: '16px 20px',
                  borderRadius: 2,
                  marginBottom: 24,
                }}
              >
                <div className="row-between" style={{ flexWrap: 'wrap', gap: 12 }}>
                  <div>
                    <div className="eyebrow" style={{ color: 'var(--low)', marginBottom: 4 }}>
                      GROUND-TRUTH VALIDATION VERDICT: PASS
                    </div>
                    <h3 className="h3" style={{ color: 'var(--fg)' }}>
                      4-Way Cross-Dataset Triangulation Confirmed Across All 113 Canonical Districts
                    </h3>
                  </div>
                  <div className="row" style={{ gap: 10, flexWrap: 'wrap' }}>
                    <span className="badge badge-low">113 / 113 WQ6 Districts</span>
                    <span className="badge badge-low">93 / 93 IMIS Districts Mapped</span>
                    <span className="badge badge-low">302 / 354 Lab-IDs Resolved</span>
                  </div>
                </div>
              </div>

              {/* VP-1..VP-4 TRIANGULATION TABLE */}
              <h3 className="h3" style={{ marginBottom: 10 }}>
                Primary Ground-Truth Triangulation Points (VP-1 through VP-4)
              </h3>
              <div style={{ overflowX: 'auto', marginBottom: 28 }}>
                <table className="val-table">
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>District &amp; State</th>
                      <th>Target Parameter</th>
                      <th>WaterTriage / WQMIS Finding</th>
                      <th>External Official Ground Truth (WQ6 + IMIS + CGWB)</th>
                      <th>Triangulation Verdict</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(fullTriage?.triangulation || []).map((vp) => (
                      <tr key={vp.id}>
                        <td className="num" style={{ fontWeight: 700 }}>{vp.id}</td>
                        <td>
                          <strong>{vp.district}</strong>
                          <span className="meta" style={{ display: 'block' }}>{vp.state}</span>
                        </td>
                        <td>
                          <span className="pill">{vp.parameter}</span>
                        </td>
                        <td>{vp.wqmis_finding}</td>
                        <td>{vp.external_finding}</td>
                        <td>
                          <span className="match-indicator">{vp.verdict}</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* CGWB STATE-YEAR PH TABLE */}
              <div className="grid-2">
                <div>
                  <h3 className="h3" style={{ marginBottom: 10 }}>
                    CGWB Groundwater Monitoring Archive (2012–2021, 17 State-Year Rows)
                  </h3>
                  <div style={{ overflowX: 'auto', maxHeight: 360 }}>
                    <table className="val-table">
                      <thead>
                        <tr>
                          <th>State</th>
                          <th className="num-col">Year</th>
                          <th className="num-col">CGWB Stations</th>
                          <th className="num-col">pH Out of 6.5–8.5</th>
                          <th className="num-col">Exceed %</th>
                        </tr>
                      </thead>
                      <tbody>
                        {(validationData?.ph || []).map((r, i) => (
                          <tr key={`${r.state}-${r.year}-${i}`}>
                            <td>{r.state}</td>
                            <td className="num-col">{r.year}</td>
                            <td className="num-col">{r.readings}</td>
                            <td className="num-col">{r.exceeded}</td>
                            <td className="num-col">{r.exceed_pct}%</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                <div>
                  <h3 className="h3" style={{ marginBottom: 10 }}>
                    113-District Official WQ6 Contaminated Village Summary
                  </h3>
                  <div style={{ overflowX: 'auto', maxHeight: 360 }}>
                    <table className="val-table">
                      <thead>
                        <tr>
                          <th>BIS Parameter</th>
                          <th className="num-col">UP Villages (75 Dist.)</th>
                          <th className="num-col">Bihar Villages (38 Dist.)</th>
                          <th className="num-col">Combined Villages</th>
                          <th className="num-col">Affected Districts</th>
                        </tr>
                      </thead>
                      <tbody>
                        {[
                          ['Iron', 'Iron (Fe > 0.3 mg/L)'],
                          ['Turbidity', 'Turbidity (> 5 NTU)'],
                          ['Fluoride', 'Fluoride (F > 1.5 mg/L)'],
                          ['Total_Arsenic', 'Total Arsenic (> 0.01 mg/L)'],
                          ['Total_Coliform', 'Total Coliform (> 0 MPN)'],
                          ['E_coli', 'E. coli (> 0 CFU/100mL)'],
                          ['TDS', 'TDS (> 2000 mg/L)'],
                          ['Nitrate', 'Nitrate (> 45 mg/L)'],
                          ['pH', 'pH (< 6.5 or > 8.5)'],
                          ['Sulphate', 'Sulphate (> 400 mg/L)'],
                        ].map(([col, label]) => {
                          const upV =
                            validationData?.wq6_summary?.['Uttar Pradesh']?.contaminated_villages_by_parameter?.[col] ||
                            0;
                          const brV =
                            validationData?.wq6_summary?.Bihar?.contaminated_villages_by_parameter?.[col] || 0;
                          const upD =
                            validationData?.wq6_summary?.['Uttar Pradesh']?.affected_districts_by_parameter?.[col] || 0;
                          const brD =
                            validationData?.wq6_summary?.Bihar?.affected_districts_by_parameter?.[col] || 0;
                          return (
                            <tr key={col}>
                              <td>
                                <strong>{label}</strong>
                              </td>
                              <td className="num-col">{upV.toLocaleString()}</td>
                              <td className="num-col">{brV.toLocaleString()}</td>
                              <td className="num-col">
                                <strong>{(upV + brV).toLocaleString()}</strong>
                              </td>
                              <td className="num-col">
                                {upD + brD} ({upD} UP + {brD} BR)
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </div>
          )}
          {/* ─── TAB E: OVERVIEW & SENSITIVITY AUDIT (PRESERVED FROM DASHBOARD/SRC/APP.JSX) ─── */}
          {!loading && !error && activeTab === 'overview' && (
            <div
              className="tab-panel active"
              id="panel-overview"
              data-note=" Corpus KPIs, Fe=1.0 mg/L sensitivity rerun, and state comparison from /api/meta"
            >
              <div className="stack" style={{ gap: 'var(--gap-lg)' }}>
                <div className="grid-2">
                  <div className="sketch-box">
                    <span className="sketch-section-label">1,741-Sample Corpus Band Distribution (Model v1)</span>
                    <div className="stack" style={{ gap: 10, marginTop: 12 }}>
                      {['Critical', 'High', 'Medium', 'Low'].map((b) => {
                        const cnt = (metaData?.bands || {})[b] ?? 0;
                        const pct = ((cnt / (metaData?.corpus?.samples || 1741)) * 100).toFixed(1);
                        return (
                          <div key={b}>
                            <div className="row-between meta" style={{ marginBottom: 4 }}>
                              <span style={{ color: BAND_COLORS[b], fontWeight: 700 }}>{b}</span>
                              <span className="num">{cnt.toLocaleString()} samples ({pct}%)</span>
                            </div>
                            <div className="prog-track">
                              <div className="prog-fill" style={{ width: `${pct}%`, background: BAND_COLORS[b] }} />
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  <div className="sketch-box">
                    <span className="sketch-section-label">Critical Concentration &amp; Coverage Audit</span>
                    <div className="stack" style={{ gap: 10, marginTop: 12 }}>
                      <p style={{ fontFamily: 'var(--font-sketch)', fontSize: 15 }}>
                        {metaData?.critical_concentration
                          ? `${metaData.critical_concentration.district} — ${metaData.critical_concentration.total_critical} critical samples, ${metaData.critical_concentration.single_parameter_iron_critical} of them single-parameter iron (0.318–0.478 mg/L).`
                          : 'Madhepura — 89 critical samples, 70 of them single-parameter iron.'}
                      </p>
                      <p className="callout">
                        Raw submitter addresses populate village names in {metaData?.corpus?.village_name_coverage_pct ?? 1.21}% of samples (21/1,741) and leave 354 districts as "Not available". Non-destructive enrichment (<code>close_data_gaps.py</code>) recovers 305 villages (17.52%) and resolves 302/354 unassigned districts (85.3%) across 20 testing labs.
                      </p>
                    </div>
                  </div>
                </div>

                <div className="sketch-box">
                  <span className="sketch-section-label">Sensitivity Run — Iron Limit Re-set to 1.0 mg/L</span>
                  <p className="callout" style={{ margin: '12px 0 16px' }}>
                    876 raw WQMIS iron rows print an older 1.0 mg/L acceptable limit; primary scoring enforces the stricter 0.3 mg/L limit from BIS IS 10500:2012 Table 2 (xii). This sensitivity rerun quantifies how far the bands move under a 1.0 mg/L iron threshold.
                  </p>
                  <div style={{ overflowX: 'auto' }}>
                    <table className="ds-table">
                      <thead>
                        <tr>
                          <th>State</th>
                          <th className="num-col">Samples</th>
                          <th className="num-col">Primary Mean CRS (Fe 0.3)</th>
                          <th className="num-col">Rerun Mean CRS (Fe 1.0)</th>
                          <th className="num-col">Rerun Median</th>
                          <th className="num-col">Rerun Critical</th>
                        </tr>
                      </thead>
                      <tbody>
                        {(metaData?.state_comparison || []).map((s) => {
                          const rs = metaData?.sensitivity?.iron_1_0?.state_stats?.[s.state] || {};
                          return (
                            <tr key={s.state}>
                              <td><strong>{s.state}</strong></td>
                              <td className="num-col">{s.samples?.toLocaleString()}</td>
                              <td className="num-col">{s.mean_crs != null ? s.mean_crs.toFixed(2) : '—'}</td>
                              <td className="num-col">{rs.mean != null ? rs.mean.toFixed(2) : '—'}</td>
                              <td className="num-col">{rs.median != null ? rs.median.toFixed(2) : '—'}</td>
                              <td className="num-col">{rs.critical ?? '—'}</td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                  {metaData?.sensitivity?.iron_1_0?.bands && (
                    <p className="callout" style={{ marginTop: 12 }}>
                      Corpus-wide Fe=1.0 mg/L rerun bands: Critical {metaData.sensitivity.iron_1_0.bands.Critical} · High {metaData.sensitivity.iron_1_0.bands.High} · Medium {metaData.sensitivity.iron_1_0.bands.Medium} · Low {metaData.sensitivity.iron_1_0.bands.Low} (No-floor 10-param recomputation: 3 Critical · 41 High · 108 Medium · 1,589 Low; UP mean 9.95*).
                    </p>
                  )}
                </div>

                <div className="sketch-box">
                  <span className="sketch-section-label">State Comparison &amp; Top Exceedance Parameters (/api/meta)</span>
                  <div className="grid-2" style={{ marginTop: 12 }}>
                    <div style={{ overflowX: 'auto' }}>
                      <table className="ds-table">
                        <thead>
                          <tr>
                            <th>State</th>
                            <th className="num-col">Samples</th>
                            <th className="num-col">Critical</th>
                            <th className="num-col">High</th>
                            <th className="num-col">Medium</th>
                            <th className="num-col">Low</th>
                          </tr>
                        </thead>
                        <tbody>
                          {(metaData?.state_comparison || []).map((s) => (
                            <tr key={s.state}>
                              <td><strong>{s.state}</strong></td>
                              <td className="num-col">{s.samples?.toLocaleString()}</td>
                              <td className="num-col">{s.bands?.Critical ?? 0}</td>
                              <td className="num-col">{s.bands?.High ?? 0}</td>
                              <td className="num-col">{s.bands?.Medium ?? 0}</td>
                              <td className="num-col">{s.bands?.Low ?? 0}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>

                    <div style={{ overflowX: 'auto', maxHeight: 280 }}>
                      <table className="ds-table">
                        <thead>
                          <tr>
                            <th>State</th>
                            <th>Parameter</th>
                            <th className="num-col">Tested</th>
                            <th className="num-col">Exceeding BIS</th>
                          </tr>
                        </thead>
                        <tbody>
                          {(metaData?.top_parameters || []).slice(0, 12).map((p, idx) => (
                            <tr key={`${p.state}-${p.parameter_key}-${idx}`}>
                              <td>{p.state}</td>
                              <td><strong>{PARAM_LABELS[p.parameter_key] || p.parameter_key}</strong></td>
                              <td className="num-col">{p.tested?.toLocaleString()}</td>
                              <td className="num-col">{p.exceeding?.toLocaleString()}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ─── TAB F: METHODOLOGY & LIMITATIONS (PRESERVED FROM DASHBOARD/SRC/APP.JSX) ─── */}
          {!loading && !error && activeTab === 'methodology' && (
            <div
              className="tab-panel active"
              id="panel-methodology"
              data-note=" Provenance, BIS 10500 scoring model, band thresholds, and API-reported limitations"
            >
              <div className="stack" style={{ gap: 'var(--gap-lg)' }}>
                <div className="sketch-box">
                  <span className="sketch-section-label">Corpus Extraction &amp; Provenance</span>
                  <div className="stack" style={{ marginTop: 12 }}>
                    <p style={{ fontFamily: 'var(--font-sketch)', fontSize: 14 }}>
                      WQMIS lab reports were crawled in batches between 23 Aug and 20 Sep 2026 across 1,822 internal IDs (1,741 valid UP &amp; Bihar reports with 6,792 readings; 81 empty shells skipped). Collection window for scored samples: {metaData?.corpus?.sample_years ? metaData.corpus.sample_years.join('–') : '2022'}. Historical IMIS registry window: {metaData?.corpus?.registry_years ? metaData.corpus.registry_years.join('–') : '2009–2012'} (100,690 deduplicated events across 14,006 villages in 93 districts). Official Form WQ6 village census: 2024–2026 across all 113 canonical districts (75 UP + 38 Bihar).
                    </p>
                    <p className="meta">
                      git commit {metaData?.git_commit || '27bcc0e'} · generated {metaData?.generated_at || '2026-10-15'}
                    </p>
                  </div>
                </div>

                <div className="sketch-box">
                  <span className="sketch-section-label">API-Reported Audit Limitations (/api/meta)</span>
                  <ul className="stack" style={{ lineHeight: 1.6, marginTop: 12, listStyle: 'none', padding: 0 }}>
                    {(metaData?.limitations || []).map((lim) => (
                      <li key={lim.id} style={{ borderBottom: '1px dashed var(--border)', paddingBottom: 12 }}>
                        <div className="row-between" style={{ alignItems: 'baseline', flexWrap: 'wrap' }}>
                          <strong style={{ fontFamily: 'var(--font-sketch)' }}>{lim.title}</strong>
                          <span className={`badge badge-${lim.status === 'open' ? 'high' : 'low'}`}>
                            {lim.status}
                          </span>
                        </div>
                        <div style={{ color: 'var(--muted)', fontFamily: 'var(--font-sketch)', fontSize: 13, marginTop: 4 }}>
                          {lim.detail}
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="grid-2">
                  <div className="sketch-box">
                    <span className="sketch-section-label">Severity Band Cut-Offs</span>
                    <div className="stack" style={{ marginTop: 12 }}>
                      <p className="callout">
                        Model v2 normalizes against total possible BIS weight (6.0) with 40 / 20 / 10 band cut-offs; Model v1 normalizes against tested weight with 75 / 50 / 25 cut-offs.
                      </p>
                      <table className="ds-table">
                        <thead>
                          <tr>
                            <th>Band</th>
                            <th>Model v2 Cut-Off (1/6.0)</th>
                            <th>Model v1 Cut-Off (1/n)</th>
                            <th className="num-col">113-Dist. Count</th>
                            <th className="num-col">1,741-Sample (v1)</th>
                          </tr>
                        </thead>
                        <tbody>
                          {[
                            ['Critical', '≥ 40 (or Acute Override)', '≥ 75 (or Full Breach)', triageSummary.bands.Critical, (metaData?.bands || {}).Critical ?? 89],
                            ['High', '20 – 39.9', '50 – 74.9', triageSummary.bands.High, (metaData?.bands || {}).High ?? 392],
                            ['Medium', '10 – 19.9', '25 – 49.9', triageSummary.bands.Medium, (metaData?.bands || {}).Medium ?? 28],
                            ['Low', '< 10', '< 25', triageSummary.bands.Low, (metaData?.bands || {}).Low ?? 1232],
                          ].map(([b, c2, c1, dCnt, sCnt]) => (
                            <tr key={b}>
                              <td><span className={BAND_BADGE[b]}>{b}</span></td>
                              <td className="num">{c2}</td>
                              <td className="num">{c1}</td>
                              <td className="num-col"><strong>{dCnt}</strong></td>
                              <td className="num-col">{sCnt.toLocaleString()}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  <div className="sketch-box">
                    <span className="sketch-section-label">Escalation Rules</span>
                    <div className="stack" style={{ marginTop: 12, gap: 10 }}>
                      {(metaData?.scoring?.escalation_rules || []).map((r, i) => (
                        <p key={i} className="callout">
                          {r.rule} → floor: <strong>{r.bands_floor}</strong>
                        </p>
                      ))}
                      <p className="callout">
                        <strong>District Multi-Tier Pathogen &amp; Arsenic Override:</strong> Any district with confirmed E. coli village contamination in Form WQ6 (31 districts: 26 UP + 5 Bihar) or lab samples (Lucknow) is escalated to Critical with a Pathogen Override badge; districts with ≥10 WQ6 Arsenic villages or ≥100 IMIS Arsenic habitations (13 districts) are escalated to Critical.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </section>

        {/* ─── SECTION 02: RESTORED CHART EXPLORATIONS (#charts) ─── */}
        <section id="charts" className="section">
          <div className="eyebrow">02 / Data Visualization &amp; Distribution Charts</div>
          <h2 className="h2" style={{ marginBottom: 20 }}>
            Risk Band Breakdown, SVG Hatch Donut &amp; Collection Timeline
          </h2>

          <div className="grid-3">
            {/* CHART 1: RISK BAND BAR CHART */}
            <div className="chart-wrap">
              <div className="chart-title">1. 113 Districts by BIS Risk Band</div>
              <div className="stack" style={{ gap: 12, paddingLeft: 10 }}>
                {['Critical', 'High', 'Medium', 'Low'].map((b) => {
                  const cnt = triageSummary.bands[b] || 0;
                  const pct = ((cnt / 113) * 100).toFixed(1);
                  return (
                    <div key={b}>
                      <div className="row-between meta" style={{ marginBottom: 4 }}>
                        <span style={{ color: BAND_COLORS[b], fontWeight: 700 }}>{b}</span>
                        <span className="num">
                          {cnt} dist ({pct}%)
                        </span>
                      </div>
                      <div className="prog-track" style={{ height: 16 }}>
                        <div
                          className="prog-fill"
                          style={{
                            width: `${pct}%`,
                            background: BAND_COLORS[b],
                          }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
              <div className="chart-label-x" style={{ marginTop: 14 }}>
                UP (75): 32 Crit · 18 High · 13 Med · 12 Low | Bihar (38): 14 Crit · 9 High · 6 Med · 9 Low
              </div>
            </div>

            {/* CHART 2: SVG HATCH-PATTERN DONUT CHART (FROM OPEN_DESIGN_PROJECT) */}
            <div className="chart-wrap">
              <div className="chart-title">2. Worst Driving Parameter (113 Dist.)</div>
              <div className="row" style={{ justifyContent: 'center', gap: 18, flexWrap: 'wrap' }}>
                <svg width="150" height="150" viewBox="0 0 160 160" role="img" aria-label="Worst Parameter Donut">
                  <defs>
                    <pattern id="h-ecoli" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
                      <line x1="0" y1="0" x2="0" y2="6" stroke="var(--critical)" strokeWidth="2.5" />
                    </pattern>
                    <pattern id="h-fe" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(-45)">
                      <line x1="0" y1="0" x2="0" y2="6" stroke="var(--high)" strokeWidth="2.2" />
                    </pattern>
                    <pattern id="h-as" width="6" height="6" patternUnits="userSpaceOnUse">
                      <line x1="0" y1="0" x2="6" y2="0" stroke="var(--accent)" strokeWidth="2" />
                      <line x1="0" y1="0" x2="0" y2="6" stroke="var(--accent)" strokeWidth="2" />
                    </pattern>
                    <pattern id="h-fl" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(30)">
                      <line x1="0" y1="0" x2="0" y2="6" stroke="var(--medium)" strokeWidth="2.2" />
                    </pattern>
                  </defs>
                  <circle cx="80" cy="80" r="54" fill="none" stroke="var(--border)" strokeWidth="24" />
                  <circle
                    cx="80"
                    cy="80"
                    r="54"
                    fill="none"
                    stroke="url(#h-ecoli)"
                    strokeWidth="24"
                    strokeDasharray="115 224"
                    strokeDashoffset="0"
                  />
                  <circle
                    cx="80"
                    cy="80"
                    r="54"
                    fill="none"
                    stroke="url(#h-fe)"
                    strokeWidth="24"
                    strokeDasharray="78 261"
                    strokeDashoffset="-115"
                  />
                  <circle
                    cx="80"
                    cy="80"
                    r="54"
                    fill="none"
                    stroke="url(#h-as)"
                    strokeWidth="24"
                    strokeDasharray="62 277"
                    strokeDashoffset="-193"
                  />
                  <circle
                    cx="80"
                    cy="80"
                    r="54"
                    fill="none"
                    stroke="url(#h-fl)"
                    strokeWidth="24"
                    strokeDasharray="52 287"
                    strokeDashoffset="-255"
                  />
                  <circle cx="80" cy="80" r="42" fill="var(--surface)" stroke="var(--fg)" strokeWidth="1.5" />
                  <text x="80" y="77" textAnchor="middle" fontFamily="var(--font-mono)" fontSize="14" fontWeight="700" fill="var(--fg)">
                    107/113
                  </text>
                  <text x="80" y="92" textAnchor="middle" fontFamily="var(--font-mono)" fontSize="8.5" fill="var(--muted)">
                    ACTIVE
                  </text>
                </svg>

                <div className="stack" style={{ gap: 6 }}>
                  {(triageSummary.worst_parameter_distribution || []).slice(0, 6).map((item) => (
                    <div key={item.parameter} className="row" style={{ gap: 8, fontSize: 12 }}>
                      <span className="num" style={{ fontWeight: 700, minWidth: 24 }}>{item.districts}</span>
                      <span>{item.parameter}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="chart-label-x">
                6 districts (Hapur, Kasganj, Shamli, Muzaffarpur, Sheohar, Siwan) pass all 16 WQ6 parameters
              </div>
            </div>

            {/* CHART 3: 2022 COLLECTION WINDOW AREA CHART */}
            <div className="chart-wrap">
              <div className="chart-title">3. 2022 Lab Crawl Collection Timeline</div>
              <svg viewBox="0 0 320 150" style={{ width: '100%', height: 'auto' }} role="img" aria-label="2022 Sample Timeline">
                <line x1="36" y1="20" x2="36" y2="120" stroke="var(--fg)" strokeWidth="1.5" />
                <line x1="36" y1="120" x2="300" y2="120" stroke="var(--fg)" strokeWidth="1.5" />
                <polygon
                  points="50,120 50,108 110,94 170,76 230,26 290,82 290,120"
                  fill="var(--accent-soft)"
                />
                <polyline
                  points="50,108 110,94 170,76 230,26 290,82"
                  fill="none"
                  stroke="var(--accent)"
                  strokeWidth="2.5"
                />
                {(fullTriage?.collection_timeline || []).map((pt, i) => {
                  const xs = [50, 110, 170, 230, 290];
                  const maxS = Math.max(
                    1,
                    ...((fullTriage?.collection_timeline || []).map((x) => x.samples))
                  );
                  const y = 115 - Math.round((pt.samples / maxS) * 88);
                  const x = xs[i] || 50;
                  return (
                    <g key={pt.month}>
                      <circle cx={x} cy={y} r="4" fill="var(--surface)" stroke="var(--fg)" strokeWidth="2" />
                      <text x={x} y={y - 8} textAnchor="middle" fontFamily="var(--font-mono)" fontSize="9.5" fill="var(--fg)">
                        {pt.samples}
                      </text>
                      <text x={x} y="136" textAnchor="middle" fontFamily="var(--font-mono)" fontSize="9" fill="var(--muted)">
                        {pt.label.split(' ')[0]}
                      </text>
                    </g>
                  );
                })}
              </svg>
              <div className="chart-label-x">
                Jul – Nov 2022 JJM WQMIS Lab Crawl (1,741 Active UP &amp; Bihar Reports)
              </div>
            </div>
          </div>
        </section>

        {/* ─── SECTION 03: 4-TIER ARCHITECTURE & BIS WEIGHTS (#architecture) ─── */}
        <section id="architecture" className="section">
          <div className="eyebrow">03 / System Architecture &amp; BIS IS 10500:2012 Engine</div>
          <h2 className="h2" style={{ marginBottom: 20 }}>
            Four-Tier Data Pipeline &amp; Non-Destructive Gap Recovery
          </h2>

          <div className="grid-4" style={{ marginBottom: 28 }}>
            <div className="feature-card">
              <div className="feature-mark num">01</div>
              <h3>WQMIS Crawler v2</h3>
              <p>
                Bootstraps ASP.NET session cookies via <code>/WQMIS/Report/Report_p</code>, decrypts AES-128-CBC{' '}
                <code>s_id</code> tokens, parses <code>.lab-address-panel</code> fallback districts (solving 302/354
                missing districts across 20 labs), and extracts 305 village locations.
              </p>
            </div>
            <div className="feature-card">
              <div className="feature-mark num">02</div>
              <h3>113-District WQ6 Census</h3>
              <p>
                Fixes the <code>data[3:]</code> header slice bug to retain S.No. 1–3 districts (Agra, Aligarh, Ambedkar
                Nagar, Araria, Arwal, Aurangabad), achieving 100% coverage across 75 UP + 38 Bihar = 113 districts.
              </p>
            </div>
            <div className="feature-card">
              <div className="feature-mark num">03</div>
              <h3>IMIS &amp; CGWB Fusion</h3>
              <p>
                Maps all 93 historical IMIS 2009–2012 districts (100,690 deduplicated events, including Bhojpur,
                Kushinagar, and Amroha) and 17 CGWB 2012–2021 state-year groundwater series.
              </p>
            </div>
            <div className="feature-card">
              <div className="feature-mark num">04</div>
              <h3>BIS 10500 Risk Engine</h3>
              <p>
                Computes both Sample-Level CRS (Model v1 <code>1/n</code> &amp; Model v2 <code>1/6.0</code>) and
                Unified 113-District CRS with Zero-Tolerance Pathogen Override (32 districts) and Arsenic Escalation
                (13 districts).
              </p>
            </div>
          </div>

          <div className="sketch-box">
            <span className="sketch-section-label">BIS IS 10500:2012 PARAMETER WEIGHTS (TOTAL = 6.0)</span>
            <div style={{ overflowX: 'auto' }}>
              <table className="ds-table">
                <thead>
                  <tr>
                    <th>Parameter</th>
                    <th>Key</th>
                    <th className="num-col">BIS Acceptable</th>
                    <th className="num-col">BIS Permissible</th>
                    <th>Unit</th>
                    <th className="num-col">Weight</th>
                    <th>Scoring Strategy &amp; Escalation Rule</th>
                  </tr>
                </thead>
                <tbody>
                  {scoringParams.map((sp) => (
                    <tr key={sp.key}>
                      <td>
                        <strong>{sp.label}</strong>
                      </td>
                      <td className="num">{sp.key}</td>
                      <td className="num-col">{sp.acceptable}</td>
                      <td className="num-col">{sp.permissible ?? 'No relaxation'}</td>
                      <td>{sp.unit}</td>
                      <td className="num-col">
                        <strong>{sp.weight.toFixed(1)}</strong>
                      </td>
                      <td>
                        <span className="tag">{sp.strategy}</span>
                        {['arsenic', 'e_coli', 'total_coliform'].includes(sp.key) && (
                          <span className="badge badge-critical" style={{ marginLeft: 8 }}>
                            Acute Critical Escalation
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>

        {/* ─── SECTION 04: FIELD NOTES & AUDIT LEDGER (#notes) ─── */}
        <section id="notes" className="section">
          <div className="eyebrow">04 / Engineering Field Notes &amp; Audit Ledger</div>
          <h2 className="h2" style={{ marginBottom: 24 }}>
            Why Multi-Tier Triage &amp; Total-Weight Normalization Matter
          </h2>

          <div className="grid-3">
            <div className="sticky sticky-yellow">
              <div className="sticky-title">NOTE 01 // PANEL COVERAGE BIAS (MODEL V1 VS V2)</div>
              <p>
                In Model v1 (dividing by tested weight <code>W_tested</code>), 70 of 89 Critical samples (78.7%) are
                single-parameter iron tests in Madhepura (0.318–0.478 mg/L), scoring <code>0.4/0.4 × 100 = 100</code>.
                Dividing by fixed total BIS weight <code>6.0</code> (Model v2) scores them at <code>6.67</code> (Low)
                and reverses state means to UP (4.72) &gt; Bihar (2.32).
              </p>
            </div>

            <div className="sticky sticky-pink">
              <div className="sticky-title">NOTE 02 // 32 PATHOGEN OVERRIDES (0 CFU/100mL)</div>
              <p>
                Only Lucknow had non-zero E. coli in the 2022 crawl (<code>U691097L158S1903</code> = 20 CFU/100mL,{' '}
                <code>U695845L158S3099</code> = 8 CFU/100mL). Integrating the 113-district Form WQ6 tables reveals 31
                districts (26 UP + 5 Bihar, 133 villages) with confirmed E. coli contamination, triggering BIS IS 10500
                Zero-Tolerance Critical Overrides.
              </p>
            </div>

            <div className="sticky sticky-green">
              <div className="sticky-title">NOTE 03 // SESSION HANDSHAKE &amp; L405 RAE BARELI</div>
              <p>
                Direct requests to <code>final_report_print</code> return HTTP 500 without an{' '}
                <code>ASP.NET_SessionId</code> cookie from <code>/WQMIS/Report/Report_p</code>. Our 2-step session
                probe resolves 20 single-district labs (302/354 samples = 85.3%), proving peak fluoride 12.60 &amp;
                3.29 mg/L in Lab L405 belong to Rae Bareli while Agra’s max is 1.58 mg/L.
              </p>
            </div>
          </div>
        </section>
      </main>

      <footer className="pagefoot">
        <div className="container row-between">
          <div>
            <strong>WaterTriage</strong> · BIS IS 10500:2012 Multi-Tier Water Quality Risk Scoring &amp; Triage System
          </div>
          <div className="meta">
            Anubhav Anand — submitted as final year (7th sem) Minor Project , ASET, Amity University Uttar Pradesh
          </div>
        </div>
      </footer>
    </div>
  );
}
