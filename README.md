# 📈 Smart Arbitrage Finder

Find profitable dropshipping products automatically using AI + eBay data.

---

## 🚀 Quick Start (Windows)

### 1. Install Prerequisites
- [Python 3.10+](https://www.python.org/downloads/)
- [Node.js 18+](https://nodejs.org/)

### 2. Setup (run once)
```
setup.bat
```

### 3. Add API Keys
Edit `backend/.env`:
```
GROQ_API_KEY=your_key_here   # Free from console.groq.com
```

### 4. Start App
```
start.bat
```
Then open: **http://localhost:3000**

---

## 🔑 API Keys Setup

### Groq AI (Free - Required for AI classification)
1. Go to [console.groq.com](https://console.groq.com)
2. Sign up (free)
3. Create API key
4. Add to `backend/.env`

### eBay API (For real product data)
1. Go to [developer.ebay.com](https://developer.ebay.com)
2. Create developer account
3. Create application → get App ID + Cert ID
4. Add to `backend/.env`

> Without eBay API: Uses mock data for development

### Telegram Bot (Optional - for alerts)
1. Message @BotFather on Telegram
2. Create new bot → get token
3. Add token + your chat ID to `.env`

---

## 📁 Project Structure

```
smart-arbitrage/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── core/
│   │   ├── config.py        # Settings
│   │   ├── database.py      # SQLite DB
│   │   └── scheduler.py     # Background jobs
│   ├── services/
│   │   ├── ebay_service.py  # eBay API
│   │   ├── ai_service.py    # Groq AI classifier
│   │   ├── scoring_service.py # Profit + scoring
│   │   ├── pipeline.py      # Main pipeline
│   │   └── telegram_service.py # Alerts
│   ├── models/
│   │   └── product_repo.py  # DB operations
│   └── routers/
│       ├── search.py        # GET /search
│       ├── deals.py         # GET /deals
│       └── products.py      # GET /products
├── frontend/
│   └── src/
│       ├── App.js           # Main React app
│       └── App.css          # Dark theme styles
├── setup.bat                # One-click setup
└── start.bat                # Start both servers
```

---

## 🔌 API Endpoints

| Endpoint | Description |
|---|---|
| `GET /api/search?q=earbuds` | Search products |
| `GET /api/deals` | Top BUY deals |
| `GET /api/top-today` | Today's best |
| `GET /api/stats` | Overview stats |
| `POST /api/products/refresh` | Trigger update |
| `GET /docs` | Swagger API docs |

---

## 💡 Scoring Formula

```
Final Score = (Profit×0.4) + (Demand×0.3) + (Trend×0.2) - (Competition×0.1)
```

- **BUY** = score ≥ 0.65
- **RISKY** = score 0.40–0.64  
- **SKIP** = score < 0.40

---

## 🚀 Deploy to Server (Later)

Switch `backend/.env`:
```
DB_PATH=postgresql://...   # Change to PostgreSQL
```

And deploy with Docker or any VPS.
