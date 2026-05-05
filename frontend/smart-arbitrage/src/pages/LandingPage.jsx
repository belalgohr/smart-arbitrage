import { useNavigate } from 'react-router-dom'
import styles from './LandingPage.module.css'

const FEATURES = [
  {
    icon: '⚡',
    title: 'AI-Powered Analysis',
    desc: 'Each product scored by Groq AI with clear BUY / RISKY / SKIP verdicts.',
  },
  {
    icon: '💰',
    title: 'Profit Calculator',
    desc: 'Instant profit & margin estimates so you know what's worth selling.',
  },
  {
    icon: '📡',
    title: 'Real-Time eBay Data',
    desc: 'Live market prices pulled directly from eBay search results.',
  },
  {
    icon: '🧠',
    title: 'Smart Recommendations',
    desc: 'Ranked product lists based on demand, margin, and competition.',
  },
  {
    icon: '🕐',
    title: 'Price History',
    desc: 'Track how prices change over time. (Pro — coming soon)',
  },
  {
    icon: '📤',
    title: 'Export Data',
    desc: 'Download your search results as CSV for deeper analysis. (Pro)',
  },
]

const COMPARE = [
  { feature: 'Price History', us: true, zik: false, autods: false },
  { feature: 'Transparent pricing', us: true, zik: false, autods: false },
  { feature: 'AI analysis', us: true, zik: true, autods: true },
  { feature: 'Simple interface', us: true, zik: false, autods: false },
  { feature: 'Free tier', us: true, zik: false, autods: false },
  { feature: 'Arabic market focus', us: true, zik: false, autods: false },
]

export default function LandingPage() {
  const navigate = useNavigate()

  return (
    <div className={styles.page}>
      {/* NAV */}
      <nav className={styles.nav}>
        <div className={styles.navInner}>
          <span className={styles.logo}>
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M10 2L18 6V14L10 18L2 14V6L10 2Z" stroke="#7c6af7" strokeWidth="1.5" fill="rgba(124,106,247,0.15)"/>
              <path d="M10 6L14 8V12L10 14L6 12V8L10 6Z" fill="#7c6af7"/>
            </svg>
            SmartArbitrage
          </span>
          <div className={styles.navLinks}>
            <a href="#features">Features</a>
            <a href="#pricing">Pricing</a>
            <button className={styles.ctaNavBtn} onClick={() => navigate('/app')}>
              Launch App
            </button>
          </div>
        </div>
      </nav>

      {/* HERO */}
      <section className={styles.hero}>
        <div className={styles.heroGlow} />
        <div className={styles.heroContent}>
          <div className={styles.heroBadge}>
            <span className={styles.heroBadgeDot} />
            Live eBay data · AI analysis
          </div>
          <h1 className={styles.heroTitle}>
            Find Profitable<br />
            <span className={styles.heroAccent}>Dropshipping Products</span><br />
            in Seconds
          </h1>
          <p className={styles.heroSubtitle}>
            AI-powered product research using real market data from eBay.
            Know what to sell — before your competitors do.
          </p>
          <div className={styles.heroCtas}>
            <button className={styles.primaryBtn} onClick={() => navigate('/app')}>
              Start Free — No card needed
            </button>
            <a href="#features" className={styles.ghostBtn}>
              See how it works
            </a>
          </div>
          <div className={styles.heroStats}>
            <div className={styles.stat}>
              <span className={styles.statNum}>10</span>
              <span className={styles.statLabel}>Free searches/day</span>
            </div>
            <div className={styles.statDivider} />
            <div className={styles.stat}>
              <span className={styles.statNum}>5s</span>
              <span className={styles.statLabel}>Average result time</span>
            </div>
            <div className={styles.statDivider} />
            <div className={styles.stat}>
              <span className={styles.statNum}>AI</span>
              <span className={styles.statLabel}>Verdict on every product</span>
            </div>
          </div>
        </div>

        {/* Hero mock product cards */}
        <div className={styles.heroCards}>
          <MockCard
            title="Wireless Earbuds Pro X5"
            profit="$18.40"
            margin="62%"
            verdict="BUY"
            delay="0s"
          />
          <MockCard
            title="Phone Stand Adjustable"
            profit="$7.20"
            margin="44%"
            verdict="RISKY"
            delay="0.1s"
          />
          <MockCard
            title="USB Hub 7-Port Slim"
            profit="$11.80"
            margin="51%"
            verdict="BUY"
            delay="0.2s"
          />
        </div>
      </section>

      {/* FEATURES */}
      <section id="features" className={styles.features}>
        <div className={styles.sectionInner}>
          <div className={styles.sectionLabel}>What you get</div>
          <h2 className={styles.sectionTitle}>Everything you need to research smarter</h2>
          <div className={styles.featuresGrid}>
            {FEATURES.map((f) => (
              <div key={f.title} className={styles.featureCard}>
                <span className={styles.featureIcon}>{f.icon}</span>
                <h3 className={styles.featureTitle}>{f.title}</h3>
                <p className={styles.featureDesc}>{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section className={styles.howItWorks}>
        <div className={styles.sectionInner}>
          <div className={styles.sectionLabel}>Process</div>
          <h2 className={styles.sectionTitle}>Three steps to your next winning product</h2>
          <div className={styles.steps}>
            <div className={styles.step}>
              <div className={styles.stepNum}>01</div>
              <h3>Type a product keyword</h3>
              <p>Enter any product you're curious about — "wireless charger", "LED lamp", anything.</p>
            </div>
            <div className={styles.stepArrow}>→</div>
            <div className={styles.step}>
              <div className={styles.stepNum}>02</div>
              <h3>We fetch & score it</h3>
              <p>Live eBay data is pulled, AI calculates profit margins, demand, and competition risk.</p>
            </div>
            <div className={styles.stepArrow}>→</div>
            <div className={styles.step}>
              <div className={styles.stepNum}>03</div>
              <h3>Get your verdict</h3>
              <p>Each product gets a clear BUY / RISKY / SKIP verdict with profit numbers you can act on.</p>
            </div>
          </div>
        </div>
      </section>

      {/* COMPARE */}
      <section className={styles.compare}>
        <div className={styles.sectionInner}>
          <div className={styles.sectionLabel}>vs. the competition</div>
          <h2 className={styles.sectionTitle}>Built different</h2>
          <div className={styles.compareTable}>
            <div className={styles.compareHeader}>
              <div className={styles.compareFeatureCol}>Feature</div>
              <div className={styles.compareUsCol}>SmartArbitrage</div>
              <div className={styles.compareOtherCol}>ZIK Analytics</div>
              <div className={styles.compareOtherCol}>AutoDS</div>
            </div>
            {COMPARE.map((row) => (
              <div key={row.feature} className={styles.compareRow}>
                <div className={styles.compareFeatureCol}>{row.feature}</div>
                <div className={styles.compareUsCol}>
                  <CheckIcon val={row.us} accent />
                </div>
                <div className={styles.compareOtherCol}>
                  <CheckIcon val={row.zik} />
                </div>
                <div className={styles.compareOtherCol}>
                  <CheckIcon val={row.autods} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* PRICING */}
      <section id="pricing" className={styles.pricing}>
        <div className={styles.sectionInner}>
          <div className={styles.sectionLabel}>Pricing</div>
          <h2 className={styles.sectionTitle}>Simple, transparent pricing</h2>
          <div className={styles.pricingGrid}>
            <div className={styles.pricingCard}>
              <div className={styles.planName}>Free</div>
              <div className={styles.planPrice}>
                $0 <span>/month</span>
              </div>
              <ul className={styles.planFeatures}>
                <li><CheckSmall /> 10 searches / day</li>
                <li><CheckSmall /> eBay data</li>
                <li><CheckSmall /> AI verdict (BUY / RISKY / SKIP)</li>
                <li><CheckSmall /> Profit calculator</li>
                <li className={styles.disabled}><XSmall /> Price history</li>
                <li className={styles.disabled}><XSmall /> Export CSV</li>
                <li className={styles.disabled}><XSmall /> Alerts</li>
              </ul>
              <button className={styles.planBtn} onClick={() => navigate('/app')}>
                Get started free
              </button>
            </div>

            <div className={`${styles.pricingCard} ${styles.pricingCardPro}`}>
              <div className={styles.proLabel}>Most Popular</div>
              <div className={styles.planName}>Pro</div>
              <div className={styles.planPrice}>
                $29 <span>/month</span>
              </div>
              <ul className={styles.planFeatures}>
                <li><CheckSmall accent /> 100 searches / day</li>
                <li><CheckSmall accent /> eBay + Amazon (coming soon)</li>
                <li><CheckSmall accent /> AI verdict (BUY / RISKY / SKIP)</li>
                <li><CheckSmall accent /> Profit calculator</li>
                <li><CheckSmall accent /> Price history</li>
                <li><CheckSmall accent /> Export CSV</li>
                <li><CheckSmall accent /> Alerts</li>
              </ul>
              <button className={styles.planBtnAccent} onClick={() => navigate('/app')}>
                Start Pro trial
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* FINAL CTA */}
      <section className={styles.finalCta}>
        <div className={styles.finalCtaGlow} />
        <h2>Ready to find your next winning product?</h2>
        <p>Join smart dropshippers who research with data, not guesses.</p>
        <button className={styles.primaryBtn} onClick={() => navigate('/app')}>
          Start Free — No card needed
        </button>
      </section>

      {/* FOOTER */}
      <footer className={styles.footer}>
        <div className={styles.footerInner}>
          <span className={styles.logo}>
            <svg width="16" height="16" viewBox="0 0 20 20" fill="none">
              <path d="M10 2L18 6V14L10 18L2 14V6L10 2Z" stroke="#7c6af7" strokeWidth="1.5" fill="rgba(124,106,247,0.15)"/>
              <path d="M10 6L14 8V12L10 14L6 12V8L10 6Z" fill="#7c6af7"/>
            </svg>
            SmartArbitrage
          </span>
          <span className={styles.footerText}>© 2025 Smart Arbitrage. Built for dropshippers.</span>
        </div>
      </footer>
    </div>
  )
}

function MockCard({ title, profit, margin, verdict, delay }) {
  const colorMap = {
    BUY: { bg: 'rgba(34,197,94,0.1)', border: 'rgba(34,197,94,0.25)', text: '#22c55e' },
    RISKY: { bg: 'rgba(245,158,11,0.1)', border: 'rgba(245,158,11,0.25)', text: '#f59e0b' },
    SKIP: { bg: 'rgba(239,68,68,0.1)', border: 'rgba(239,68,68,0.25)', text: '#ef4444' },
  }
  const c = colorMap[verdict]
  return (
    <div style={{
      background: '#111118',
      border: '1px solid rgba(255,255,255,0.07)',
      borderRadius: '12px',
      padding: '14px',
      animationDelay: delay,
    }} className="fade-in">
      <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
        <div style={{
          width: '48px', height: '48px',
          background: 'rgba(124,106,247,0.1)',
          borderRadius: '8px', flexShrink: 0,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: '22px'
        }}>📦</div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <p style={{ fontSize: '13px', fontWeight: 500, color: '#f0f0f8', marginBottom: '6px', lineHeight: 1.3 }}>{title}</p>
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '12px', color: '#9898b0' }}>Profit: <strong style={{ color: '#f0f0f8' }}>{profit}</strong></span>
            <span style={{ fontSize: '12px', color: '#9898b0' }}>Margin: <strong style={{ color: '#f0f0f8' }}>{margin}</strong></span>
          </div>
        </div>
        <span style={{
          fontSize: '11px', fontWeight: 600,
          padding: '3px 8px',
          borderRadius: '6px',
          background: c.bg,
          color: c.text,
          border: `1px solid ${c.border}`,
          flexShrink: 0,
        }}>{verdict}</span>
      </div>
    </div>
  )
}

function CheckIcon({ val, accent }) {
  if (val) return <span style={{ color: accent ? '#7c6af7' : '#22c55e', fontWeight: 700 }}>✓</span>
  return <span style={{ color: '#3a3a4a' }}>—</span>
}

function CheckSmall({ accent }) {
  return <span style={{ color: accent ? '#7c6af7' : '#22c55e', marginRight: '6px', fontSize: '13px' }}>✓</span>
}

function XSmall() {
  return <span style={{ color: '#3a3a4a', marginRight: '6px', fontSize: '13px' }}>✕</span>
}
