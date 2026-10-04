
import React, { useState, useEffect } from 'react';

export default function App() {
  const [activeTab, setActiveTab] = useState('Overview');
  const [meta, setMeta] = useState(null);
  const [queue, setQueue] = useState([]);
  const [selectedSample, setSelectedSample] = useState(null);
  
  useEffect(() => {
    fetch('/api/meta')
      .then(r => r.json())
      .then(data => setMeta(data))
      .catch(e => console.error(e));
      
    fetch('/api/priority/top/100')
      .then(r => r.json())
      .then(data => setQueue(data))
      .catch(e => console.error(e));
  }, []);

  if (!meta) return <div style={{padding: 40}}>Loading WaterTriage Dashboard...</div>;

  return (
    <div style={{ fontFamily: 'sans-serif', maxWidth: 1200, margin: '0 auto', padding: '20px' }}>
      {/* Header */}
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '2px solid #ccc', paddingBottom: 10, marginBottom: 20 }}>
        <div>
          <h1 style={{ margin: 0 }}>WaterTriage</h1>
          <p style={{ margin: '5px 0 0 0', color: '#666' }}>A Data-Driven Water Quality Risk Scoring System</p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ background: '#4caf50', color: '#fff', padding: '4px 8px', borderRadius: 4, fontWeight: 'bold', fontSize: 12 }}>
            DB LIVE
          </div>
          <div style={{ fontSize: 12, color: '#666' }}>
            {meta.corpus.samples} Samples | {meta.corpus.historical_events_distinct} Historical Records
          </div>
        </div>
      </header>
      
      {/* Navigation */}
      <nav style={{ display: 'flex', gap: 10, marginBottom: 20 }}>
        {['Overview', 'Queue', 'Methodology'].map(tab => (
          <button 
            key={tab}
            onClick={() => { setActiveTab(tab); setSelectedSample(null); }}
            style={{
              padding: '8px 16px', 
              background: activeTab === tab ? '#0056b3' : '#eee',
              color: activeTab === tab ? '#fff' : '#000',
              border: 'none',
              borderRadius: 4,
              cursor: 'pointer'
            }}
          >
            {tab}
          </button>
        ))}
      </nav>
      
      {/* Content */}
      <main>
        {activeTab === 'Overview' && (
          <div>
            <h2>Dashboard Overview</h2>
            <div style={{ display: 'flex', gap: 20, marginBottom: 30 }}>
              <div style={{ flex: 1, padding: 20, background: '#f8d7da', border: '1px solid #f5c6cb', borderRadius: 4 }}>
                <h3 style={{ margin: '0 0 10px 0', color: '#721c24' }}>Critical</h3>
                <div style={{ fontSize: 32, fontWeight: 'bold' }}>{meta.bands.Critical}</div>
              </div>
              <div style={{ flex: 1, padding: 20, background: '#fff3cd', border: '1px solid #ffeeba', borderRadius: 4 }}>
                <h3 style={{ margin: '0 0 10px 0', color: '#856404' }}>High</h3>
                <div style={{ fontSize: 32, fontWeight: 'bold' }}>{meta.bands.High}</div>
              </div>
              <div style={{ flex: 1, padding: 20, background: '#d1ecf1', border: '1px solid #bee5eb', borderRadius: 4 }}>
                <h3 style={{ margin: '0 0 10px 0', color: '#0c5460' }}>Medium</h3>
                <div style={{ fontSize: 32, fontWeight: 'bold' }}>{meta.bands.Medium}</div>
              </div>
              <div style={{ flex: 1, padding: 20, background: '#d4edda', border: '1px solid #c3e6cb', borderRadius: 4 }}>
                <h3 style={{ margin: '0 0 10px 0', color: '#155724' }}>Low</h3>
                <div style={{ fontSize: 32, fontWeight: 'bold' }}>{meta.bands.Low}</div>
              </div>
            </div>
            
            <h3>External Consistency (Exploratory)</h3>
            <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: 30, border: '1px solid #ddd' }}>
                <thead>
                  <tr style={{ background: '#eee' }}>
                    <th style={{ padding: 8, border: '1px solid #ddd', textAlign: 'left' }}>Parameter</th>
                    <th style={{ padding: 8, border: '1px solid #ddd', textAlign: 'left' }}>Dataset</th>
                    <th style={{ padding: 8, border: '1px solid #ddd', textAlign: 'left' }}>n (Districts)</th>
                    <th style={{ padding: 8, border: '1px solid #ddd', textAlign: 'left' }}>Spearman ρ</th>
                    <th style={{ padding: 8, border: '1px solid #ddd', textAlign: 'left' }}>p-value</th>
                  </tr>
                </thead>
                <tbody>
                  <tr><td style={{ padding: 8, border: '1px solid #ddd' }}>Iron</td><td style={{ padding: 8, border: '1px solid #ddd' }}>POOLED</td><td style={{ padding: 8, border: '1px solid #ddd' }}>26</td><td style={{ padding: 8, border: '1px solid #ddd' }}>0.548</td><td style={{ padding: 8, border: '1px solid #ddd' }}>0.004</td></tr>
                  <tr><td style={{ padding: 8, border: '1px solid #ddd' }}>Iron</td><td style={{ padding: 8, border: '1px solid #ddd' }}>POOLED (excl Madhepura)</td><td style={{ padding: 8, border: '1px solid #ddd' }}>25</td><td style={{ padding: 8, border: '1px solid #ddd' }}>0.493</td><td style={{ padding: 8, border: '1px solid #ddd' }}>0.012</td></tr>
                  <tr><td style={{ padding: 8, border: '1px solid #ddd' }}>Fluoride</td><td style={{ padding: 8, border: '1px solid #ddd' }}>POOLED</td><td style={{ padding: 8, border: '1px solid #ddd' }}>29</td><td style={{ padding: 8, border: '1px solid #ddd' }}>0.223</td><td style={{ padding: 8, border: '1px solid #ddd' }}>0.246</td></tr>
                  <tr><td style={{ padding: 8, border: '1px solid #ddd' }}>Fluoride</td><td style={{ padding: 8, border: '1px solid #ddd' }}>Uttar Pradesh</td><td style={{ padding: 8, border: '1px solid #ddd' }}>22</td><td style={{ padding: 8, border: '1px solid #ddd' }}>0.426</td><td style={{ padding: 8, border: '1px solid #ddd' }}>0.004</td></tr>
                </tbody>
            </table>

            <h3>SENSITIVITY RUN (Iron = 1.0 mg/L)</h3>
            <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: 30, border: '1px solid #ddd' }}>
                <thead>
                  <tr style={{ background: '#eee' }}>
                    <th style={{ padding: 8, border: '1px solid #ddd', textAlign: 'left' }}>State</th>
                    <th style={{ padding: 8, border: '1px solid #ddd', textAlign: 'left' }}>Critical</th>
                    <th style={{ padding: 8, border: '1px solid #ddd', textAlign: 'left' }}>High</th>
                    <th style={{ padding: 8, border: '1px solid #ddd', textAlign: 'left' }}>Medium</th>
                    <th style={{ padding: 8, border: '1px solid #ddd', textAlign: 'left' }}>Low</th>
                    <th style={{ padding: 8, border: '1px solid #ddd', textAlign: 'left' }}>Mean Score</th>
                  </tr>
                </thead>
                <tbody>
                  <tr><td style={{ padding: 8, border: '1px solid #ddd' }}>Bihar</td><td style={{ padding: 8, border: '1px solid #ddd' }}>0</td><td style={{ padding: 8, border: '1px solid #ddd' }}>0</td><td style={{ padding: 8, border: '1px solid #ddd' }}>1</td><td style={{ padding: 8, border: '1px solid #ddd' }}>774</td><td style={{ padding: 8, border: '1px solid #ddd' }}>{meta.sensitivity?.iron_1_0?.state_stats?.Bihar?.mean || 0}</td></tr>
                  <tr><td style={{ padding: 8, border: '1px solid #ddd' }}>Uttar Pradesh</td><td style={{ padding: 8, border: '1px solid #ddd' }}>5</td><td style={{ padding: 8, border: '1px solid #ddd' }}>139</td><td style={{ padding: 8, border: '1px solid #ddd' }}>29</td><td style={{ padding: 8, border: '1px solid #ddd' }}>793</td><td style={{ padding: 8, border: '1px solid #ddd' }}>{meta.sensitivity?.iron_1_0?.state_stats?.['Uttar Pradesh']?.mean || 0}</td></tr>
                </tbody>
            </table>
          </div>
        )}
        
        {activeTab === 'Queue' && (
          <div style={{ display: 'flex', gap: 20 }}>
            <div style={{ flex: 1 }}>
                <h2>Priority Intervention Queue</h2>
                <table style={{ width: '100%', borderCollapse: 'collapse', border: '1px solid #ddd' }}>
                  <thead>
                    <tr style={{ background: '#f5f5f5' }}>
                      <th style={{ padding: 10, textAlign: 'left', borderBottom: '2px solid #ccc' }}>ID</th>
                      <th style={{ padding: 10, textAlign: 'left', borderBottom: '2px solid #ccc' }}>District (State)</th>
                      <th style={{ padding: 10, textAlign: 'left', borderBottom: '2px solid #ccc' }}>Worst Param</th>
                      <th style={{ padding: 10, textAlign: 'center', borderBottom: '2px solid #ccc' }}>Tested Params</th>
                      <th style={{ padding: 10, textAlign: 'right', borderBottom: '2px solid #ccc' }}>Score</th>
                    </tr>
                  </thead>
                  <tbody>
                    {queue.slice(0, 15).map(q => (
                      <tr 
                        key={q.sample_id} 
                        style={{ 
                          borderBottom: '1px solid #eee', 
                          background: selectedSample?.sample_id === q.sample_id ? '#eef7ff' : '#fff',
                          cursor: 'pointer'
                        }}
                        onClick={() => setSelectedSample(q)}
                      >
                        <td style={{ padding: 10, fontFamily: 'monospace' }}>#{q.sample_id}</td>
                        <td style={{ padding: 10 }}>{q.district} ({q.state})</td>
                        <td style={{ padding: 10 }}>{q.worst_parameter || 'N/A'}</td>
                        <td style={{ padding: 10, textAlign: 'center' }}>
                            <span style={{ background: '#eee', padding: '2px 8px', borderRadius: 12, fontSize: 12 }}>
                                {q.n_scored_params} / 8
                            </span>
                        </td>
                        <td style={{ padding: 10, textAlign: 'right', fontWeight: 'bold' }}>{q.score.toFixed(1)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
            </div>
            
            {/* Sample Drawer / Detail */}
            {selectedSample && (
                <div style={{ width: 350, borderLeft: '1px solid #ddd', paddingLeft: 20 }}>
                    <h3>Sample Details</h3>
                    <div style={{ marginBottom: 10 }}><strong>ID:</strong> #{selectedSample.sample_id}</div>
                    <div style={{ marginBottom: 10 }}><strong>State:</strong> {selectedSample.state}</div>
                    <div style={{ marginBottom: 10 }}><strong>District:</strong> {selectedSample.district}</div>
                    <div style={{ marginBottom: 10 }}><strong>Score:</strong> {selectedSample.score.toFixed(1)}</div>
                    <div style={{ marginBottom: 10 }}><strong>Band:</strong> {selectedSample.band}</div>
                    <div style={{ marginBottom: 10 }}><strong>Worst Parameter:</strong> {selectedSample.worst_parameter || 'N/A'}</div>
                    <div style={{ marginBottom: 10 }}><strong>Parameters Tested:</strong> {selectedSample.n_scored_params}</div>
                    <button 
                        onClick={() => setSelectedSample(null)}
                        style={{ marginTop: 20, padding: '6px 12px', cursor: 'pointer' }}
                    >
                        Close Drawer
                    </button>
                </div>
            )}
          </div>
        )}
        
        {activeTab === 'Methodology' && (
          <div>
            <h2>Data Provenance & Limitations</h2>
            <div style={{ background: '#f8f9fa', padding: 20, borderRadius: 4, border: '1px solid #ddd', marginBottom: 30 }}>
                <p><strong>Corpus Extraction:</strong> Records were collected in batches between 23 Aug and 20 Sep 2026; request totals and rates were not logged; later batches used up to 6 parallel workers.</p>
                <p><strong>Total Samples Analyzed:</strong> {meta.corpus.samples}</p>
            </div>
            
            <h3>API Reported Limitations</h3>
            <ul style={{ lineHeight: '1.6' }}>
                {meta.limitations?.map(lim => (
                    <li key={lim.id}>
                        <strong>{lim.title}:</strong> {lim.detail}
                    </li>
                ))}
            </ul>
          </div>
        )}
      </main>
    </div>
  );
}
