import React, { useState, useEffect, useCallback, useRef } from 'react';
import './App.css';

const API = 'http://localhost:8000/api';

// ── Stable user ID (localStorage) ────────────────────────
const USER_ID = (() => {
  let id = localStorage.getItem('saf_uid');
  if (!id) { id = Math.random().toString(36).slice(2, 10); localStorage.setItem('saf_uid', id); }
  return id;
})();

const VERDICT = {
  BUY:   { emoji: '✅', label: 'BUY',   color: '#22c55e' },
  RISKY: { emoji: '⚠️', label: 'RISKY', color: '#f59e0b' },
  SKIP:  { emoji: '❌', label: 'SKIP',  color: '#ef4444' },
};

const pct = v => `${Math.round((v || 0) * 100)}%`;
const usd = v => `$${(v || 0).toFixed(2)}`;

// ── Sparkline ─────────────────────────────────────────────
function Sparkline({ data = [], width = 64, height = 24 }) {
  if (!data || data.length < 2) return <span className="no-spark">–</span>;
  const prices = data.map(d => d.ebay_price || d.price).filter(Boolean);
  if (prices.length < 2) return <span className="no-spark">–</span>;
  const min = Math.min(...prices), max = Math.max(...prices), range = max - min || 1;
  const pts = prices.map((p, i) => {
    const x = (i / (prices.length - 1)) * width;
    const y = height - ((p - min) / range) * (height - 4) - 2;
    return `${x},${y}`;
  }).join(' ');
  const rising = prices[prices.length - 1] >= prices[0];
  return (
    <svg width={width} height={height}>
      <polyline points={pts} fill="none" stroke={rising ? '#22c55e' : '#ef4444'}
        strokeWidth="1.5" strokeLinejoin="round" />
    </svg>
  );
}

// ── Score Bar ─────────────────────────────────────────────
function Bar({ value, color }) {
  return (
    <div className="bar-t">
      <div className="bar-f" style={{ width: pct(Math.min(value || 0, 1)), background: color }} />
    </div>
  );
}

// ── Price History Modal ───────────────────────────────────
function HistoryModal({ product, onClose }) {
  const [data, setData] = useState(null);
  useEffect(() => {
    fetch(`${API}/price-history/${product.id}`)
      .then(r => r.json()).then(setData)
      .catch(() => setData({ history: [], trend: {} }));
  }, [product.id]);

  const dir  = data?.trend?.direction || 'stable';
  const icon = { rising: '📈', falling: '📉', stable: '➡️' }[dir] || '❓';
  const chg  = data?.trend?.change_pct || 0;

  return (
    <div className="overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <div className="modal-top">
          <h3>📊 Price History</h3>
          <button className="x-btn" onClick={onClose}>✕</button>
        </div>
        <p className="modal-prod">{product.title}</p>
        {!data ? <div className="m-spin"><div className="spin" /></div> : (
          <>
            <div className="trend-row">
              <span>{icon} {dir}</span>
              <span style={{ color: chg >= 0 ? '#22c55e' : '#ef4444', fontWeight: 700 }}>
                {chg >= 0 ? '+' : ''}{chg}%
              </span>
              <span className="t-stab">· {data.trend?.stability || 'stable'}</span>
            </div>
            <div className="mini-stats">
              {[['Min', usd(data.trend?.min_price)],
                ['Avg', usd(data.trend?.avg_price)],
                ['Max', usd(data.trend?.max_price)],
                ['Points', data.trend?.data_points || data.history?.length || 0],
              ].map(([l, v]) => (
                <div key={l} className="mini-s"><span>{l}</span><strong>{v}</strong></div>
              ))}
            </div>
            {data.history?.length > 0 ? (
              <div className="h-table">
                <div className="h-head"><span>Date</span><span>Price</span><span>Profit</span><span>Score</span></div>
                {data.history.slice(-12).reverse().map((h, i) => (
                  <div key={i} className="h-row">
                    <span>{(h.recorded_at || '').slice(0, 16)}</span>
                    <span>{usd(h.ebay_price)}</span>
                    <span style={{ color: h.profit >= 5 ? '#22c55e' : '#94a3b8' }}>+{usd(h.profit)}</span>
                    <span>{pct(h.final_score)}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="no-history">No snapshots yet — appears after next update.</p>
            )}
          </>
        )}
      </div>
    </div>
  );
}

// ── Product Card ──────────────────────────────────────────
function ProductCard({ p }) {
  const [showHist, setShowHist] = useState(false);
  const [history,  setHistory]  = useState([]);
  const v = VERDICT[p.verdict] || VERDICT.SKIP;
  const img = p.image_url || `https://picsum.photos/seed/${p.id?.slice(-5)}/320/210`;
  const profitC = p.profit >= 10 ? '#22c55e' : p.profit >= 4 ? '#f59e0b' : '#ef4444';

  useEffect(() => {
    fetch(`${API}/price-history/${p.id}`)
      .then(r => r.json())
      .then(d => setHistory(d.history || []))
      .catch(() => {});
  }, [p.id]);

  return (
    <>
      <article className={`card ${p.verdict === 'BUY' ? 'card-hot' : ''}`}>
        <div className="card-img">
          <img src={img} alt={p.title} loading="lazy"
            onError={e => { e.target.src = `https://picsum.photos/320/210?r=${Math.random()}`; }} />
          <div className="v-badge" style={{ color: v.color, borderColor: v.color, background: `${v.color}18` }}>
            {v.emoji} {v.label}
          </div>
          {p.risk_flag && p.risk_flag !== 'none' && (
            <div className="risk-tag">⚠ {p.risk_flag.replace(/_/g, ' ')}</div>
          )}
        </div>

        <div className="card-body">
          <p className="c-title">{p.title}</p>

          <div className="c-money">
            <div><span>Sell</span><b>{usd(p.ebay_price)}</b></div>
            <div><span>Cost</span><b>{usd(p.estimated_cost)}</b></div>
            <div><span>Profit</span><b style={{ color: profitC, fontSize: 15 }}>{usd(p.profit)}</b></div>
            <div><span>Margin</span><b>{p.profit_margin?.toFixed(0) || 0}%</b></div>
          </div>

          <div className="c-bars">
            {[['Demand', p.demand_score, '#22c55e'],
              ['Trend',  p.trend_score,  '#3b82f6'],
              ['Score',  p.final_score,  '#f59e0b'],
            ].map(([l, val, c]) => (
              <div key={l} className="c-bar-row">
                <span>{l}</span><Bar value={val} color={c} /><span>{pct(val)}</span>
              </div>
            ))}
          </div>

          <div className="c-foot">
            <div className="c-meta">
              <span>⭐ {p.rating?.toFixed(1) || '–'}</span>
              <span>💬 {p.reviews_count || 0}</span>
              <span>👥 {p.seller_count || 1}</span>
            </div>
            <button className="hist-btn" onClick={() => setShowHist(true)}>
              <Sparkline data={history} /> 📊
            </button>
          </div>

          <a href={p.ebay_url || '#'} target="_blank" rel="noreferrer" className="ebay-btn">
            View on eBay →
          </a>
        </div>
      </article>
      {showHist && <HistoryModal product={p} onClose={() => setShowHist(false)} />}
    </>
  );
}

// ── Search Suggestions Dropdown ───────────────────────────
function SuggestionsDropdown({ suggestions, history, onSelect }) {
  if (!suggestions.length && !history.length) return null;
  return (
    <div className="suggestions-box">
      {history.length > 0 && (
        <>
          <div className="sug-label">🕐 Recent</div>
          {history.slice(0, 3).map((h, i) => (
            <button key={i} className="sug-item" onClick={() => onSelect(h.query)}>
              {h.query}
              <span className="sug-count">{h.result_count} results</span>
            </button>
          ))}
        </>
      )}
      {suggestions.length > 0 && (
        <>
          <div className="sug-label">🔥 Popular</div>
          {suggestions.slice(0, 5).map((s, i) => (
            <button key={i} className="sug-item" onClick={() => onSelect(s.query)}>
              {s.query}
              <span className="sug-count">{s.count} searches</span>
            </button>
          ))}
        </>
      )}
    </div>
  );
}

// ── Main App ──────────────────────────────────────────────
export default function App() {
  const [products,     setProducts]     = useState([]);
  const [stats,        setStats]        = useState({});
  const [query,        setQuery]        = useState('');
  const [filter,       setFilter]       = useState('');
  const [loading,      setLoading]      = useState(false);
  const [tab,          setTab]          = useState('deals');
  const [toast,        setToast]        = useState('');
  const [suggestions,  setSuggestions]  = useState([]);
  const [userHistory,  setUserHistory]  = useState([]);
  const [showSug,      setShowSug]      = useState(false);
  const [limitInfo,    setLimitInfo]    = useState('');
  const [source,       setSource]       = useState('');
  const searchRef = useRef();

  const showToast = msg => { setToast(msg); setTimeout(() => setToast(''), 3500); };

  // ── Fetchers ──────────────────────────────────────────
  const fetchDeals = useCallback(async () => {
    setLoading(true);
    try { const r = await fetch(`${API}/deals?limit=60`); setProducts((await r.json()).deals || []); }
    catch { setProducts([]); }
    setLoading(false);
  }, []);

  const fetchTop = useCallback(async () => {
    setLoading(true);
    try { const r = await fetch(`${API}/top-today`); setProducts((await r.json()).deals || []); }
    catch { setProducts([]); }
    setLoading(false);
  }, []);

  const fetchStats = useCallback(async () => {
    try { const r = await fetch(`${API}/stats`); setStats(await r.json()); } catch {}
  }, []);

  const fetchSuggestions = useCallback(async () => {
    try {
      const [sug, hist] = await Promise.all([
        fetch(`${API}/suggestions`).then(r => r.json()),
        fetch(`${API}/history?user_id=${USER_ID}`).then(r => r.json()),
      ]);
      setSuggestions(sug.suggestions || []);
      setUserHistory(hist.history || []);
    } catch {}
  }, []);

  // ── Search ────────────────────────────────────────────
  const handleSearch = async (e, overrideQuery, forceRefresh = false) => {
    e?.preventDefault();
    const q = overrideQuery || query;
    if (!q.trim()) return;
    setShowSug(false);
    setTab('search');
    setLoading(true);
    setSource('');

    try {
      // refresh=false by default → cache first, API only if miss
      const r = await fetch(
        `${API}/search?q=${encodeURIComponent(q)}&user_id=${USER_ID}&refresh=${forceRefresh}`
      );

      if (r.status === 429) {
        const err = await r.json();
        showToast('🚫 ' + err.detail);
        setLoading(false);
        return;
      }

      const d = await r.json();
      setProducts(d.products || []);
      setLimitInfo(d.limit_info || '');
      setSource(d.source === 'cache' ? '⚡ Cached result' : '🔄 Fresh from eBay');
      if (d.refreshing) showToast('⏳ Fetching fresh results…');
      fetchSuggestions();
      fetchStats();
    } catch { setProducts([]); }
    setLoading(false);
  };

  const handleForceRefresh = (e) => {
    e.preventDefault();
    handleSearch(null, query, true);  // bypass cache
  };

  const handleRefresh = async () => {
    showToast('🔄 Background update started…');
    await fetch(`${API}/products/refresh`, { method: 'POST' });
    setTimeout(() => { fetchDeals(); fetchStats(); }, 3000);
  };

  // ── Init ──────────────────────────────────────────────
  useEffect(() => { fetchStats(); fetchSuggestions(); }, [fetchStats, fetchSuggestions]);
  useEffect(() => {
    if (tab === 'deals') fetchDeals();
    else if (tab === 'top') fetchTop();
  }, [tab, fetchDeals, fetchTop]);

  const shown = filter ? products.filter(p => p.verdict === filter) : products;

  return (
    <div className="app" onClick={() => setShowSug(false)}>

      {/* Header */}
      <header className="hdr">
        <div className="hdr-in">
          <div className="logo">
            <span className="logo-icon">📈</span>
            <div>
              <div className="logo-name">Smart Arbitrage</div>
              <div className="logo-sub">Dropshipping Intelligence</div>
            </div>
          </div>

          <div className="search-area" onClick={e => e.stopPropagation()}>
            <form className="s-wrap" onSubmit={handleSearch}>
              <input ref={searchRef} className="s-in"
                placeholder="Search products…"
                value={query}
                onChange={e => setQuery(e.target.value)}
                onFocus={() => setShowSug(true)}
              />
              <button className="s-go" type="submit">Search</button>
              {tab === 'search' && query && (
                <button type="button" className="s-refresh" onClick={handleForceRefresh}
                  title="Force refresh from eBay (uses 1 search credit)">↺</button>
              )}
            </form>
            {source && tab === 'search' && (
              <div className="source-tag">{source}</div>
            )}
            {showSug && (
              <SuggestionsDropdown
                suggestions={suggestions}
                history={userHistory}
                onSelect={q => { setQuery(q); setShowSug(false); handleSearch(null, q); }}
              />
              />
            )}
          </div>

          <button className="ref-btn" onClick={handleRefresh}>🔄 Refresh</button>
        </div>

        {limitInfo && (
          <div className="limit-bar">
            <span>🔍 {limitInfo}</span>
          </div>
        )}
      </header>

      {/* Stats */}
      <div className="stats">
        {[
          { v: stats.total_products || 0,  l: 'Products',    c: 'var(--txt)' },
          { v: stats.buy_signals    || 0,  l: 'BUY Signals', c: '#22c55e'   },
          { v: usd(stats.avg_profit),      l: 'Avg Profit',  c: '#f59e0b'   },
          { v: pct(stats.top_score),       l: 'Top Score',   c: '#3b82f6'   },
          { v: stats.cache?.fresh_entries || 0, l: 'Cached Queries', c: '#a78bfa' },
        ].map((s, i) => (
          <div key={i} className="stat">
            <div className="stat-v" style={{ color: s.c }}>{s.v}</div>
            <div className="stat-l">{s.l}</div>
          </div>
        ))}
      </div>

      {/* Toolbar */}
      <div className="toolbar">
        <div className="tabs">
          {[['deals','🔥 Top Deals'],['top','⭐ Today'],['search','🔍 Search']].map(([id, lbl]) => (
            <button key={id} className={`tab ${tab === id ? 'tab-on' : ''}`} onClick={() => setTab(id)}>
              {lbl}
            </button>
          ))}
        </div>
        <div className="filters">
          {['', 'BUY', 'RISKY', 'SKIP'].map(v => (
            <button key={v || 'all'} className={`flt ${filter === v ? 'flt-on' : ''}`}
              onClick={() => setFilter(v)}>
              {v || 'All'}
            </button>
          ))}
          <span className="cnt">{shown.length}</span>
        </div>
      </div>

      {/* Content */}
      <main className="main">
        {loading ? (
          <div className="s-loading"><div className="spin" /><p>Scanning…</p></div>
        ) : shown.length === 0 ? (
          <div className="s-empty">
            <p>No products found.</p>
            <p>Try searching or click Refresh to load data.</p>
            <button className="load-btn" onClick={handleRefresh}>Load Products</button>
            {suggestions.length > 0 && (
              <div className="empty-suggestions">
                <p>Try these popular searches:</p>
                <div className="sug-chips">
                  {suggestions.slice(0, 6).map((s, i) => (
                    <button key={i} className="sug-chip"
                      onClick={() => { setQuery(s.query); handleSearch(null, s.query); }}>
                      {s.query}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="grid">
            {shown.map(p => <ProductCard key={p.id} p={p} />)}
          </div>
        )}
      </main>

      {toast && <div className="toast">{toast}</div>}
    </div>
  );
}
