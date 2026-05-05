import { useState, useEffect, useCallback, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import styles from './AppPage.module.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const RESTRICTED_KEYWORDS = [
  'underwear', 'panties', 'bra', 'bras', 'lingerie',
  'women clothing', "women's clothing", 'female clothing', 'ladies clothing',
  'vape', 'vaping', 'cigarette', 'cigarettes', 'tobacco', 'nicotine', 'e-cigarette',
  'alcohol', 'beer', 'wine', 'whiskey', 'vodka', 'liquor',
]

const RESTRICTED_MESSAGES = {
  underwear: 'Not available — high return rate due to sizing inconsistency.',
  "women's clothing": 'Not available — sizing inconsistency issues make returns too high.',
  vape: 'Not available — customs restrictions apply to vaping products.',
  cigarettes: 'Not available — customs restrictions apply to tobacco products.',
  alcohol: 'Not available — platform restrictions apply to alcohol.',
}

function getRestrictionMessage(query) {
  const q = query.toLowerCase()
  if (['underwear','panties','bra','bras','lingerie'].some(k => q.includes(k))) {
    return RESTRICTED_MESSAGES.underwear
  }
  if (['women clothing',"women's clothing",'female clothing','ladies clothing'].some(k => q.includes(k))) {
    return RESTRICTED_MESSAGES["women's clothing"]
  }
  if (['vape','vaping','e-cigarette'].some(k => q.includes(k))) {
    return RESTRICTED_MESSAGES.vape
  }
  if (['cigarette','cigarettes','tobacco','nicotine'].some(k => q.includes(k))) {
    return RESTRICTED_MESSAGES.cigarettes
  }
  if (['alcohol','beer','wine','whiskey','vodka','liquor'].some(k => q.includes(k))) {
    return RESTRICTED_MESSAGES.alcohol
  }
  return null
}

function isRestricted(query) {
  const q = query.toLowerCase()
  return RESTRICTED_KEYWORDS.some(k => q.includes(k))
}

const VERDICT_COLORS = {
  BUY:   { bg: 'var(--c-buy-bg)',   border: 'var(--c-buy-border)',   text: 'var(--c-buy)' },
  RISKY: { bg: 'var(--c-risky-bg)', border: 'var(--c-risky-border)', text: 'var(--c-risky)' },
  SKIP:  { bg: 'var(--c-skip-bg)',  border: 'var(--c-skip-border)',  text: 'var(--c-skip)' },
}

// Debounce hook
function useDebounce(value, delay) {
  const [debouncedValue, setDebouncedValue] = useState(value)
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay)
    return () => clearTimeout(timer)
  }, [value, delay])
  return debouncedValue
}

export default function AppPage() {
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [restrictionMsg, setRestrictionMsg] = useState(null)
  const [filter, setFilter] = useState('ALL')
  const [source, setSource] = useState(null)
  const [hasSearched, setHasSearched] = useState(false)
  const [page, setPage] = useState(1)
  const [copiedId, setCopiedId] = useState(null)
  const inputRef = useRef(null)
  const PAGE_SIZE = 5

  // Load last search from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('sa_last_search')
    if (saved) setQuery(saved)
    inputRef.current?.focus()
  }, [])

  const search = useCallback(async (q, refresh = false) => {
    if (!q.trim()) return

    setHasSearched(true)
    setRestrictionMsg(null)
    setError(null)
    setPage(1)

    // Check restrictions
    if (isRestricted(q)) {
      setRestrictionMsg(getRestrictionMessage(q))
      setProducts([])
      setLoading(false)
      return
    }

    localStorage.setItem('sa_last_search', q)
    setLoading(true)

    try {
      const params = new URLSearchParams({ q: q.trim() })
      if (refresh) params.append('refresh', 'true')

      const res = await fetch(`${API_URL}/api/search?${params}`)
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.detail || `Error ${res.status}`)
      }
      const data = await res.json()
      setProducts(data.products || [])
      setSource(data.source || null)
    } catch (err) {
      setError(err.message || 'Failed to fetch results. Is the backend running?')
      setProducts([])
    } finally {
      setLoading(false)
    }
  }, [])

  const handleSubmit = (e) => {
    e?.preventDefault()
    if (query.trim()) search(query)
  }

  const handleRefresh = () => search(query, true)

  const handleCopyLink = async (product) => {
    const url = product.url || product.ebay_url || product.link || `https://www.ebay.com/sch/i.html?_nkw=${encodeURIComponent(product.title || '')}`
    try {
      await navigator.clipboard.writeText(url)
      setCopiedId(product.id || product.title)
      setTimeout(() => setCopiedId(null), 2000)
    } catch {
      // fallback
    }
  }

  // Filtered products
  const filtered = filter === 'ALL'
    ? products
    : products.filter(p => (p.verdict || '').toUpperCase() === filter)

  const totalPages = Math.ceil(filtered.length / PAGE_SIZE)
  const paged = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)

  // Dashboard stats
  const buyCount = products.filter(p => (p.verdict || '').toUpperCase() === 'BUY').length
  const bestProfit = products.length
    ? Math.max(...products.map(p => parseFloat(p.profit || p.profit_estimate || 0)))
    : 0

  return (
    <div className={styles.page}>
      {/* HEADER */}
      <header className={styles.header}>
        <div className={styles.headerInner}>
          <button className={styles.backBtn} onClick={() => navigate('/')}>
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M10 4L6 8L10 12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
            </svg>
            Back
          </button>
          <span className={styles.logo}>
            <svg width="18" height="18" viewBox="0 0 20 20" fill="none">
              <path d="M10 2L18 6V14L10 18L2 14V6L10 2Z" stroke="#7c6af7" strokeWidth="1.5" fill="rgba(124,106,247,0.15)"/>
              <path d="M10 6L14 8V12L10 14L6 12V8L10 6Z" fill="#7c6af7"/>
            </svg>
            SmartArbitrage
          </span>
          <div className={styles.headerRight}>
            {source && (
              <span className={`${styles.sourceTag} ${source === 'fresh' ? styles.sourceFresh : styles.sourceCache}`}>
                {source === 'fresh' ? '● Fresh data' : '◎ Cached'}
              </span>
            )}
          </div>
        </div>
      </header>

      <main className={styles.main}>
        {/* SEARCH SECTION */}
        <section className={styles.searchSection}>
          <h1 className={styles.searchTitle}>What product are you researching?</h1>
          <form className={styles.searchForm} onSubmit={handleSubmit}>
            <div className={styles.searchInputWrap}>
              <svg className={styles.searchIcon} width="18" height="18" viewBox="0 0 18 18" fill="none">
                <circle cx="8" cy="8" r="5.5" stroke="currentColor" strokeWidth="1.5"/>
                <path d="M12.5 12.5L16 16" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
              </svg>
              <input
                ref={inputRef}
                className={styles.searchInput}
                type="text"
                value={query}
                onChange={e => setQuery(e.target.value)}
                placeholder="e.g. wireless earbuds, LED lamp, phone stand..."
                disabled={loading}
                autoComplete="off"
                autoFocus
              />
              {query && (
                <button
                  type="button"
                  className={styles.clearBtn}
                  onClick={() => { setQuery(''); setProducts([]); setHasSearched(false); setRestrictionMsg(null); setError(null); }}
                >
                  ×
                </button>
              )}
            </div>
            <button
              type="submit"
              className={styles.searchBtn}
              disabled={loading || !query.trim()}
            >
              {loading ? <Spinner /> : 'Search'}
            </button>
          </form>
        </section>

        {/* RESULTS AREA */}
        {hasSearched && (
          <section className={styles.resultsSection}>

            {/* Restriction message */}
            {restrictionMsg && (
              <div className={styles.restrictionBanner}>
                <span className={styles.restrictionIcon}>⚠️</span>
                <div>
                  <strong>Category not available</strong>
                  <p>{restrictionMsg}</p>
                </div>
              </div>
            )}

            {/* Error message */}
            {error && (
              <div className={styles.errorBanner}>
                <span>⚡</span>
                <div>
                  <strong>Something went wrong</strong>
                  <p>{error}</p>
                </div>
                <button className={styles.retryBtn} onClick={() => search(query)}>Retry</button>
              </div>
            )}

            {/* Loading skeletons */}
            {loading && (
              <div className={styles.skeletons}>
                {[...Array(3)].map((_, i) => <SkeletonCard key={i} />)}
              </div>
            )}

            {/* Dashboard */}
            {!loading && !error && !restrictionMsg && products.length > 0 && (
              <>
                <div className={styles.dashboard}>
                  <div className={styles.dashCard}>
                    <span className={styles.dashLabel}>Total Products</span>
                    <span className={styles.dashValue}>{products.length}</span>
                  </div>
                  <div className={styles.dashCard}>
                    <span className={styles.dashLabel}>Best Profit</span>
                    <span className={`${styles.dashValue} ${styles.dashGreen}`}>
                      ${bestProfit.toFixed(2)}
                    </span>
                  </div>
                  <div className={styles.dashCard}>
                    <span className={styles.dashLabel}>BUY Signals</span>
                    <span className={`${styles.dashValue} ${styles.dashAccent}`}>{buyCount}</span>
                  </div>
                  <div className={styles.dashCard}>
                    <span className={styles.dashLabel}>Data Source</span>
                    <span className={styles.dashValue} style={{ fontSize: '14px', textTransform: 'capitalize' }}>
                      {source || '—'}
                    </span>
                  </div>
                </div>

                {/* Toolbar */}
                <div className={styles.toolbar}>
                  <div className={styles.filterBtns}>
                    {['ALL', 'BUY', 'RISKY', 'SKIP'].map(v => (
                      <button
                        key={v}
                        className={`${styles.filterBtn} ${filter === v ? styles.filterActive : ''} ${v !== 'ALL' ? styles[`filter${v}`] : ''}`}
                        onClick={() => { setFilter(v); setPage(1); }}
                      >
                        {v}
                      </button>
                    ))}
                  </div>
                  <button
                    className={styles.refreshBtn}
                    onClick={handleRefresh}
                    disabled={loading}
                    title="Force refresh — bypass cache"
                  >
                    <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                      <path d="M2 7a5 5 0 0 1 8.66-2.5M12 7a5 5 0 0 1-8.66 2.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
                      <path d="M10.5 2v3h-3M3.5 12V9h3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                    Refresh
                  </button>
                </div>

                {/* Product cards */}
                {paged.length === 0 ? (
                  <div className={styles.emptyFilter}>
                    No {filter} products found in these results.
                  </div>
                ) : (
                  <div className={styles.productGrid}>
                    {paged.map((product, i) => (
                      <ProductCard
                        key={product.id || product.title || i}
                        product={product}
                        copiedId={copiedId}
                        onCopy={handleCopyLink}
                        style={{ animationDelay: `${i * 0.06}s` }}
                      />
                    ))}
                  </div>
                )}

                {/* Pagination */}
                {totalPages > 1 && (
                  <div className={styles.pagination}>
                    <button
                      className={styles.pageBtn}
                      disabled={page === 1}
                      onClick={() => setPage(p => p - 1)}
                    >← Prev</button>
                    <span className={styles.pageInfo}>
                      {page} / {totalPages}
                    </span>
                    <button
                      className={styles.pageBtn}
                      disabled={page === totalPages}
                      onClick={() => setPage(p => p + 1)}
                    >Next →</button>
                  </div>
                )}
              </>
            )}

            {/* Empty results */}
            {!loading && !error && !restrictionMsg && products.length === 0 && hasSearched && (
              <div className={styles.emptyState}>
                <span className={styles.emptyIcon}>🔍</span>
                <h3>No products found</h3>
                <p>Try a different keyword or check if the backend is running.</p>
              </div>
            )}
          </section>
        )}

        {/* Initial state (not searched yet) */}
        {!hasSearched && (
          <div className={styles.initialState}>
            <div className={styles.initialHint}>
              <span>Try searching for:</span>
              {['wireless earbuds', 'LED desk lamp', 'phone holder', 'USB hub', 'portable charger'].map(s => (
                <button
                  key={s}
                  className={styles.suggestionBtn}
                  onClick={() => { setQuery(s); search(s); }}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

function ProductCard({ product, copiedId, onCopy, style }) {
  const verdict = (product.verdict || 'SKIP').toUpperCase()
  const colors = VERDICT_COLORS[verdict] || VERDICT_COLORS.SKIP

  const profit = parseFloat(product.profit || product.profit_estimate || 0)
  const margin = product.profit_margin || product.margin || null
  const rating = product.rating || product.score || null
  const reviews = product.reviews_count || product.reviews || null
  const image = product.image || product.image_url || null
  const title = product.title || 'Unknown Product'
  const price = product.price || product.buy_price || null
  const sellPrice = product.sell_price || null
  const isCopied = copiedId === (product.id || product.title)

  return (
    <div className={`${styles.productCard} fade-in`} style={style}>
      {/* Image */}
      <div className={styles.productImg}>
        {image ? (
          <img src={image} alt={title} loading="lazy" />
        ) : (
          <div className={styles.productImgPlaceholder}>📦</div>
        )}
      </div>

      {/* Content */}
      <div className={styles.productContent}>
        <div className={styles.productHeader}>
          <h3 className={styles.productTitle} title={title}>{title}</h3>
          <span
            className={styles.verdict}
            style={{ background: colors.bg, color: colors.text, border: `1px solid ${colors.border}` }}
          >
            {verdict}
          </span>
        </div>

        <div className={styles.productMeta}>
          {profit > 0 && (
            <div className={styles.metaItem}>
              <span className={styles.metaLabel}>Profit</span>
              <span className={styles.metaValue} style={{ color: 'var(--c-buy)' }}>
                ${profit.toFixed(2)}
              </span>
            </div>
          )}
          {margin && (
            <div className={styles.metaItem}>
              <span className={styles.metaLabel}>Margin</span>
              <span className={styles.metaValue}>{margin}</span>
            </div>
          )}
          {price && (
            <div className={styles.metaItem}>
              <span className={styles.metaLabel}>Buy</span>
              <span className={styles.metaValue}>${parseFloat(price).toFixed(2)}</span>
            </div>
          )}
          {sellPrice && (
            <div className={styles.metaItem}>
              <span className={styles.metaLabel}>Sell</span>
              <span className={styles.metaValue}>${parseFloat(sellPrice).toFixed(2)}</span>
            </div>
          )}
          {rating && (
            <div className={styles.metaItem}>
              <span className={styles.metaLabel}>Rating</span>
              <span className={styles.metaValue}>⭐ {parseFloat(rating).toFixed(1)}</span>
            </div>
          )}
          {reviews && (
            <div className={styles.metaItem}>
              <span className={styles.metaLabel}>Reviews</span>
              <span className={styles.metaValue}>{Number(reviews).toLocaleString()}</span>
            </div>
          )}
        </div>

        {product.reason && (
          <p className={styles.productReason}>{product.reason}</p>
        )}

        <div className={styles.productActions}>
          <button
            className={styles.copyBtn}
            onClick={() => onCopy(product)}
          >
            {isCopied ? '✓ Copied!' : '🔗 Copy Link'}
          </button>
          {(product.url || product.ebay_url || product.link) && (
            <a
              href={product.url || product.ebay_url || product.link}
              target="_blank"
              rel="noopener noreferrer"
              className={styles.viewBtn}
            >
              View on eBay →
            </a>
          )}
        </div>
      </div>
    </div>
  )
}

function SkeletonCard() {
  return (
    <div className={styles.productCard}>
      <div className={`${styles.productImg} skeleton`} style={{ height: '140px' }} />
      <div className={styles.productContent}>
        <div className={`skeleton`} style={{ height: '16px', width: '80%', marginBottom: '8px' }} />
        <div className={`skeleton`} style={{ height: '14px', width: '60%', marginBottom: '16px' }} />
        <div style={{ display: 'flex', gap: '12px' }}>
          {[...Array(3)].map((_, i) => (
            <div key={i} className={`skeleton`} style={{ height: '40px', flex: 1 }} />
          ))}
        </div>
      </div>
    </div>
  )
}

function Spinner() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none" style={{ animation: 'spin 0.8s linear infinite' }}>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      <circle cx="9" cy="9" r="7" stroke="rgba(255,255,255,0.3)" strokeWidth="2"/>
      <path d="M9 2a7 7 0 0 1 7 7" stroke="white" strokeWidth="2" strokeLinecap="round"/>
    </svg>
  )
}
