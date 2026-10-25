# 🚀 Crypto Volatility Screener & AI Technical Analyst

An automated crypto screener that combines **mathematical pre-screening** on CoinMarketCap data with an **autonomous AI Agent (powered by `browser-use` and Google Gemini)** to inspect interactive TradingView candlestick charts and Perpetual Futures availability.

---

## 📌 Features

1. **Mathematical Pre-Screening:**
   - Scrapes ranks 50–200 on CoinMarketCap using headless Playwright.
   - Filters out stablecoins.
   - Calculates **Volatility Compression Ratio** (`abs(24h_change) / abs(7d_change) < 0.15`) and **Volume-to-Market-Cap Ratio (VMC)** (`3% - 15%`).
   - Limits 24h price swing between `-10%` and `+10%` to spot sideways consolidation.
2. **AI Chart Verification:**
   - Automatically navigates to shortlisted coins on CoinMarketCap.
   - Switches to the **TradingView** interactive chart (1h / 4h timeframe).
   - Validates horizontal sideways compression, support & resistance levels.
   - Verifies perpetual futures availability (Binance / Bitget).
   - Reports the top 3 best setups with estimated target zones (+5% TP, -5% SL).

---

## 📋 Prerequisites

- **Python**: Version `3.10` or higher
- **Google Gemini API Key**: [Get an API key from Google AI Studio](https://aistudio.google.com/)

---

## 🛠️ Installation & Setup

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd crypto-agent
```

### 2. Create and Activate a Virtual Environment

- **Windows (PowerShell):**
  ```powershell
  python -m venv .venv
  .venv\Scripts\Activate.ps1
  ```
- **Windows (Command Prompt):**
  ```cmd
  python -m venv .venv
  .venv\Scripts\activate.bat
  ```
- **macOS / Linux:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Install Playwright Browsers
Playwright requires browser binaries to scrape and run the AI agent:
```bash
playwright install chromium
```

### 5. Configure Environment Variables
Copy the `.env.example` file to `.env`:
```bash
# Windows PowerShell / CMD
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Open `.env` and insert your Google Gemini API key:
```env
GOOGLE_API_KEY="your_actual_gemini_api_key_here"
```

---

## 🚦 Usage

Run the screener script:
```bash
python screener.py
```

### How It Works:
1. Performs mathematical filtering on CoinMarketCap (ranks 50–200).
2. Prints a sorted `MATHEMATICAL SHORTLIST` to the console.
3. Automatically tests priority Gemini models (`gemini-3.1-pro-preview`, `gemini-2.5-pro`, `gemini-3.5-flash`, etc.) for active quota.
4. Launches the browser agent to analyze charts and outputs the top 3 setups.

---

## 🛡️ Privacy & Security

- Do **not** commit your `.env` file or API keys.
- Ensure `.gitignore` is present before making Git commits.
