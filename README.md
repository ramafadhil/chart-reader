# 🚀 Crypto Volatility Screener & AI Technical Analyst

An automated crypto screener and AI technical analyst combining **mathematical pre-screening** on CoinMarketCap data with an **autonomous AI Agent (powered by `browser-use`)** to inspect interactive TradingView candlestick charts and Perpetual Futures availability.

Features a **flagship Next.js (App Router) + Framer Motion + Tailwind CSS** frontend styled with an elite **Hitam & Emas / Gelap (Dark Luxury Fintech)** aesthetic, **Multi-Provider 2026 LLM support** (Google Gemini, Anthropic Claude, OpenAI, Groq, DeepSeek), live **Server-Sent Events (SSE)** streaming, and an interactive **Watch Agent Browser (Headed)** toggle.

---

## 📌 Architecture & Features

### 🌟 Frontend (`/frontend` — Next.js 16 + React 19 + Framer Motion)
- **Fluid Micro-Interactions & Spring Physics (`framer-motion`)**:
  - **Sliding Tab Indicator (`layoutId="active-provider-pill"`)**: Smooth spring animation when switching between Google, Claude, OpenAI, Groq, and DeepSeek.
  - **Cascade Stagger Entrances**: Shortlisted coins glide into the list with spring easing as soon as Stage 1 math completes.
  - **Live Terminal Telemetry**: Streaming real-time steps with auto-scrolling log feed.
  - **Risk/Reward Target Zone Gauges**: Visual bar breakdown for speculative entry, Take-Profit (+5%), and Stop-Loss (-5%).
  - **Morphing Copy Action**: "📋 Copy Raw Analysis for Claude" button morphs into a checkmark with celebratory spring feedback.
- **In-Browser Credential Security**: API keys are masked and cached strictly inside browser `localStorage` per provider. Zero `.env` requirements for frontend users.
- **Hitam & Emas (Dark Luxury)**: Deep obsidian surfaces (`#060608`), crisp white-gold typography, and brushed gold borders (`#d4af37`).

### ⚙️ Backend (`app.py`, `screener_engine.py`, `llm_factory.py` — FastAPI + Python 3.10+)
- **Stage 1 (Mathematical Pre-screening)**:
  - Scrapes CoinMarketCap ranks 50–200 via headless Playwright.
  - Filters stablecoins and calculates **Volatility Compression Ratio (VCR)** (`abs(24h)/abs(7d) < 0.15`) and **Volume-to-Market-Cap Ratio (VMC)** (`3% - 15%`).
- **Stage 2 (Autonomous AI Visual Verification)**:
  - `browser-use` Agent with Google Gemini, Anthropic Claude, OpenAI, Groq, or DeepSeek.
  - Navigates to CoinMarketCap, toggles TradingView interactive candlestick charts (1h/4h), checks horizontal consolidation, and verifies Binance/Bitget Perpetual Futures.
  - Emits real-time SSE stream events to the Next.js client.
- **Execution Mode**:
  - **Watch Agent Browser (Headed)**: Chromium window opens on screen so viewers/recruiters can watch the AI browse live.
  - **Headless Mode**: Runs silently in the background.

---

## 🚀 Quick Start

### 1. Install Backend Dependencies
```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install chromium
```

### 2. Run Both Backend & Frontend (One Command)
Gunakan launcher otomatis:
```powershell
.\run.ps1
```
*(atau klik ganda file **`run.bat`** di Windows Explorer)*

Ini akan otomatis:
1. Menjalankan **FastAPI Backend** di `http://127.0.0.1:8000`
2. Menjalankan **Next.js Frontend** di `http://localhost:3000`

Buka browser di:
👉 **`http://localhost:3000`**

---

### Manual Launch (Dua Terminal)

**Terminal 1 (Backend FastAPI):**
```powershell
.\.venv\Scripts\python.exe app.py
```

**Terminal 2 (Frontend Next.js):**
```powershell
cd frontend
npm run dev
```

---

## 🛡️ Privacy & Security
- **Thread-Safe & Zero Leaks**: API keys are passed directly to LLM constructors in memory without polluting process-global environment variables (`os.environ`).
- **In-Browser Isolation**: API keys entered in the UI are stored strictly in client-side `localStorage` per provider. A **"Clear Key"** button is provided to wipe keys immediately at any time.
- **Strict Local CORS**: API endpoints are locked to explicit loopback origins (`http://localhost:3000`, `http://127.0.0.1:3000`).
- **Anti-DoS Concurrency Lock**: Backend enforces single-task execution to protect system memory and Chromium process limits.
- **Prompt Injection Defense**: External CoinMarketCap tickers and symbols undergo strict regex sanitization before LLM prompt injection, with enforced domain restrictions (`coinmarketcap.com` and `tradingview.com`).
