# Smart Arbitrage — Frontend

Production-ready React (Vite) frontend for the Smart Arbitrage Finder FastAPI backend.

## Stack

- **React 18** + **Vite 5**
- **React Router v6** (SPA routing)
- **CSS Modules** (zero dependencies for styling)
- **Fonts:** Syne (display) + DM Sans (body)

---

## Project Structure

```
smart-arbitrage/
├── public/
│   └── index.html
├── src/
│   ├── pages/
│   │   ├── LandingPage.jsx        # Marketing / home page
│   │   ├── LandingPage.module.css
│   │   ├── AppPage.jsx            # Main search tool
│   │   └── AppPage.module.css
│   ├── App.jsx                    # Routes
│   ├── main.jsx                   # Entry point
│   └── index.css                  # Global styles / design tokens
├── .env                           # Local env (not committed)
├── .env.example                   # Template
├── vercel.json                    # Vercel SPA routing fix
├── vite.config.js
└── package.json
```

---

## Quick Start (Local)

```bash
# 1. Install dependencies
npm install

# 2. Set your backend URL
cp .env.example .env
# Edit .env → VITE_API_URL=http://localhost:8000

# 3. Run dev server
npm run dev
# → http://localhost:3000
```

Make sure the FastAPI backend is running on port 8000:
```bash
cd ../backend
uvicorn main:app --reload
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `VITE_API_URL` | `http://localhost:8000` | FastAPI backend URL |

---

## Build for Production

```bash
npm run build
# Output → dist/
```

---

## Deploy to Vercel (Frontend)

1. Push your project to GitHub
2. Go to [vercel.com](https://vercel.com) → New Project → Import repo
3. Set **Framework**: Vite
4. Set **Root Directory**: `smart-arbitrage` (this folder)
5. Add Environment Variable:
   - `VITE_API_URL` = `https://your-backend.onrender.com`
6. Deploy ✅

The `vercel.json` file handles SPA routing automatically.

---

## Deploy Backend to Render

1. Go to [render.com](https://render.com) → New Web Service
2. Connect your GitHub repo
3. **Root Directory**: `v4/backend`
4. **Build Command**: `pip install -r requirements.txt`
5. **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. Add Environment Variables from `.env.example`
7. Set `ALLOWED_ORIGINS=https://your-vercel-app.vercel.app`

---

## Pages

### `/` — Landing Page
- Hero with live-preview product cards
- Features grid (6 cards)
- How it works (3 steps)
- Comparison table vs ZIK Analytics / AutoDS
- Pricing (Free / Pro)
- Final CTA

### `/app` — Search Tool
- Search bar with debounce
- Dashboard: total products, best profit, BUY signals, data source
- Filter: ALL / BUY / RISKY / SKIP
- Product cards: image, title, profit, margin, rating, reviews, verdict
- Copy eBay link button
- Refresh button (force bypass cache)
- Pagination (5 per page)
- Skeleton loading states
- Error handling with retry
- Restricted keyword detection (underwear, vape, alcohol, etc.)
- Last search saved in `localStorage`

---

## Business Rules (Restricted Categories)

Searches containing these keywords show a message instead of results:

| Category | Message |
|---|---|
| underwear, bra, lingerie | Not available — high return rate due to sizing |
| women clothing | Not available — sizing inconsistency issues |
| vape, e-cigarette | Not available — customs restrictions apply |
| cigarettes, tobacco, nicotine | Not available — customs restrictions apply |
| alcohol, beer, wine, etc. | Not available — platform restrictions apply |
