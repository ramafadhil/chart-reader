import asyncio
import re
from typing import Any, AsyncGenerator, Dict, List, Optional
from playwright.async_api import async_playwright

from browser_use import Agent
from browser_use.browser.profile import BrowserProfile
from llm_factory import create_llm

def parse_percent(val_str: Optional[str]) -> float:
    if not val_str:
        return 0.0
    cleaned = val_str.replace('%', '').replace('$', '').replace(',', '').strip()
    for char in ['▲', '▼', ' ', '\n', '\t']:
        cleaned = cleaned.replace(char, '')
    try:
        return float(cleaned)
    except Exception:
        return 0.0

def parse_amount(val_str: Optional[str]) -> float:
    if not val_str:
        return 0.0
    cleaned = val_str.replace('$', '').replace(',', '').replace(' ', '').strip()
    multiplier = 1.0
    if cleaned.upper().endswith('M'):
        multiplier = 1_000_000.0
        cleaned = cleaned[:-1]
    elif cleaned.upper().endswith('B'):
        multiplier = 1_000_000_000.0
        cleaned = cleaned[:-1]
    elif cleaned.upper().endswith('K'):
        multiplier = 1_000.0
        cleaned = cleaned[:-1]
    try:
        return float(cleaned) * multiplier
    except Exception:
        return 0.0

async def scrape_cmc_page(page, url: str) -> List[Dict[str, str]]:
    await page.goto(url, timeout=60000)
    await page.wait_for_timeout(3000)
    
    # Scroll down to trigger lazy loading of rows
    for _ in range(8):
        await page.evaluate("window.scrollBy(0, 1000)")
        await page.wait_for_timeout(500)
        
    data = await page.evaluate("""() => {
        const rows = Array.from(document.querySelectorAll('table tbody tr'));
        const parsed = [];
        for (const tr of rows) {
            const tds = tr.querySelectorAll('td');
            if (tds.length < 9) continue;
            
            const rankText = tds[1] ? tds[1].innerText.trim() : '';
            const nameText = tds[2] ? tds[2].innerText.trim() : '';
            const priceText = tds[3] ? tds[3].innerText.trim() : '';
            const ch1hText = tds[4] ? tds[4].innerText.trim() : '';
            const ch24hText = tds[5] ? tds[5].innerText.trim() : '';
            const ch7dText = tds[6] ? tds[6].innerText.trim() : '';
            const marketCapText = tds[7] ? tds[7].innerText.trim() : '';
            const volumeText = tds[8] ? tds[8].innerText.trim() : '';
            
            parsed.push({
                rankText,
                nameText,
                priceText,
                ch1hText,
                ch24hText,
                ch7dText,
                marketCapText,
                volumeText
            });
        }
        return parsed;
    }""")
    return data

async def run_pre_screening_stream(emit_callback) -> List[Dict[str, Any]]:
    """
    Executes Stage 1 mathematical pre-screening and streams progress events.
    """
    await emit_callback({
        "type": "status",
        "stage": "prescreening",
        "message": "Starting headless browser to scrape CoinMarketCap..."
    })
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        await emit_callback({
            "type": "status",
            "stage": "prescreening",
            "message": "Scraping CoinMarketCap Page 1 (Ranks 1-100)..."
        })
        data1 = await scrape_cmc_page(page, "https://coinmarketcap.com/")
        
        await emit_callback({
            "type": "status",
            "stage": "prescreening",
            "message": "Scraping CoinMarketCap Page 2 (Ranks 101-200)..."
        })
        data2 = await scrape_cmc_page(page, "https://coinmarketcap.com/?page=2")
        
        all_data = data1 + data2
        await browser.close()
        
    await emit_callback({
        "type": "status",
        "stage": "prescreening",
        "message": f"Scraped {len(all_data)} coins. Applying mathematical filters..."
    })
    
    stablecoins_keywords = [
        'USD', 'EUR', 'GBP', 'USDT', 'USDC', 'TUSD', 'FDUSD', 'EURC', 'DAI',
        'BUSD', 'UST', 'STABLE', 'STABLES', 'USDD', 'PYUSD', 'FRAX'
    ]
    
    shortlist = []
    for coin in all_data:
        try:
            rank = int(coin['rankText'])
        except ValueError:
            continue
            
        # Target Rank 50-200
        if rank < 50 or rank > 200:
            continue
            
        name_text = coin['nameText']
        name_lines = [line.strip() for line in name_text.split('\n') if line.strip()]
        if len(name_lines) >= 2:
            name = name_lines[0]
            symbol = name_lines[1]
        else:
            parts = name_text.split()
            if len(parts) >= 2:
                symbol = parts[-1]
                name = " ".join(parts[:-1])
            else:
                name = name_text
                symbol = name_text
        
        # Filter out stablecoins
        is_stable = False
        for kw in stablecoins_keywords:
            if kw in symbol.upper() or kw in name.upper():
                is_stable = True
                break
        if is_stable:
            continue
            
        ch24h = parse_percent(coin['ch24hText'])
        ch7d = parse_percent(coin['ch7dText'])
        market_cap = parse_amount(coin['marketCapText'])
        volume_24h = parse_amount(coin['volumeText'])
        
        # Volatility Compression Ratio: abs(24h_change) / abs(7d_change)
        if abs(ch7d) > 0.0:
            compression_ratio = abs(ch24h) / abs(ch7d)
        else:
            compression_ratio = 999.0
            
        # Volume to Market Cap Ratio (VMC)
        if market_cap > 0.0:
            vmc_ratio = volume_24h / market_cap
        else:
            vmc_ratio = 0.0
            
        is_compression_pass = compression_ratio < 0.15
        is_vmc_pass = 0.03 <= vmc_ratio <= 0.15
        is_change_pass = -10.0 <= ch24h <= 10.0
        
        if is_compression_pass and is_vmc_pass and is_change_pass:
            shortlist.append({
                'rank': rank,
                'name': name,
                'symbol': symbol,
                'ch24h': ch24h,
                'ch7d': ch7d,
                'compression_ratio': round(compression_ratio, 4),
                'vmc_ratio': round(vmc_ratio, 4),
                'price': coin['priceText']
            })
            
    # Sort shortlist by compression ratio (lowest first = tightest compression)
    shortlist.sort(key=lambda x: x['compression_ratio'])
    
    await emit_callback({
        "type": "shortlist",
        "stage": "prescreening",
        "data": shortlist,
        "message": f"Pre-screening complete. Found {len(shortlist)} coins passing compression criteria."
    })
    
    return shortlist

def sanitize_token_identifier(text: str) -> str:
    """
    Sanitizes coin name and symbol scraped from external websites to prevent
    indirect prompt injection attacks against the browser-use LLM agent.
    Strips newlines, quotes, and non-alphanumeric punctuation.
    """
    cleaned = re.sub(r'[^A-Za-z0-9 .\-]', '', text)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned[:30]

def parse_trade_cards(raw_text: str) -> List[Dict[str, Any]]:
    """
    Parses structured trading setup cards from LLM output.
    """
    cards = []
    # Try chunking by 'Coin Name:' or similar separators
    blocks = re.split(r'(?:[-*#\s]*Coin Name:)', raw_text, flags=re.IGNORECASE)
    
    for block in blocks[1:]:  # skip first chunk before first 'Coin Name:'
        card: Dict[str, Any] = {}
        
        # Coin Name / Ticker
        m_coin = re.search(r'^\s*([^\n\r]+)', block)
        if m_coin:
            card["coin"] = m_coin.group(1).replace('[', '').replace(']', '').strip()
            
        # Target Direction
        m_dir = re.search(r'(?:Target Direction|Direction):\s*([^\n\r]+)', block, re.IGNORECASE)
        if m_dir:
            card["direction"] = m_dir.group(1).replace('[', '').replace(']', '').strip()
        else:
            card["direction"] = "LONG / SHORT"
            
        # Available Platform
        m_plat = re.search(r'(?:Available Platform|Platform):\s*([^\n\r]+)', block, re.IGNORECASE)
        if m_plat:
            card["platform"] = m_plat.group(1).replace('[', '').replace(']', '').strip()
        else:
            card["platform"] = "Binance / Bitget Futures"
            
        # Setup Structure
        m_setup = re.search(r'(?:The Setup Structure|Setup Structure|Setup):\s*([^\n\r]+(?:\n[^\n\r\-*]+)?)', block, re.IGNORECASE)
        if m_setup:
            card["setup_structure"] = m_setup.group(1).replace('[', '').replace(']', '').strip()
            
        # Current Technical Reason
        m_reason = re.search(r'(?:Current Technical Reason|Technical Reason|Reason):\s*([^\n\r]+(?:\n[^\n\r\-*]+)?)', block, re.IGNORECASE)
        if m_reason:
            card["technical_reason"] = m_reason.group(1).replace('[', '').replace(']', '').strip()
            
        # Estimated Target Zone
        m_target = re.search(r'(?:Estimated Target Zone|Target Zone|Target):\s*([^\n\r]+(?:\n[^\n\r\-*]+)?)', block, re.IGNORECASE)
        if m_target:
            card["target_zone"] = m_target.group(1).replace('[', '').replace(']', '').strip()
            
        if card.get("coin"):
            cards.append(card)
            
    return cards

async def run_screening_orchestrator(
    provider: str,
    model: str,
    api_key: Optional[str],
    headed: bool,
    emit_callback
):
    """
    Full pipeline orchestrator:
    Stage 1: Pre-screening via Playwright
    Stage 2: AI Chart Verification via browser-use Agent
    """
    try:
        # Stage 1: Mathematical Pre-screening
        shortlist = await run_pre_screening_stream(emit_callback)
        
        if not shortlist:
            await emit_callback({
                "type": "done",
                "message": "No coins passed the mathematical compression criteria today.",
                "cards": [],
                "raw_output": "No coins passed pre-screening."
            })
            return
            
        shortlist_lines = []
        for item in shortlist:
            safe_name = sanitize_token_identifier(str(item.get('name', '')))
            safe_symbol = sanitize_token_identifier(str(item.get('symbol', '')))
            shortlist_lines.append(
                f"Rank {item['rank']}: {safe_name} ({safe_symbol}) - CR: {item['compression_ratio']:.3f}, VMC: {item['vmc_ratio']:.3f}, Price: {item['price']}"
            )
        shortlist_text = "\n".join(shortlist_lines)
        
        # Stage 2: Initialize Universal LLM
        await emit_callback({
            "type": "status",
            "stage": "ai_verification",
            "message": f"Initializing AI Agent with {provider.upper()} ({model}). Mode: {'Headed (Visible Browser)' if headed else 'Headless (Silent)'}..."
        })
        
        llm = create_llm(provider=provider, model=model, api_key=api_key)
        
        # Construct Prompt for Browser-Use
        prompt_task = (
            "Act as a professional Crypto Technical Analyst and Volatility Screener.\n"
            "Open browser and verify the following candidate coins on CoinMarketCap (https://coinmarketcap.com/):\n\n"
            
            "SECURITY & DOMAIN CONSTRAINT:\n"
            "- You are strictly permitted to interact ONLY with coinmarketcap.com and embedded tradingview.com charts.\n"
            "- NEVER navigate to unverified external URLs, file paths, or private IPs.\n\n"
            
            f"=== SHORTLIST KOIN UNTUK DIVERIFIKASI ===\n"
            f"{shortlist_text}\n"
            f"=========================================\n\n"
            
            "CRITICAL RULE FOR REASONING LENGTH (PREVENT TRUNCATION ERROR):\n"
            "- Tulis 'Eval' dan 'Memory' Anda dengan sangat singkat (maksimal 1 kalimat pendek, kurang dari 15 kata).\n"
            "- JANGAN mendeskripsikan elemen DOM secara detail. Langsung lakukan tindakan agar respon Anda tetap pendek!\n\n"
            
            "PETUNJUK ALUR KERJA (WAJIB DIIKUTI UNTUK SETIAP KOIN):\n"
            "1. Lakukan verifikasi berurutan mulai dari koin pertama di shortlist.\n"
            "2. Buka halaman detail koin menggunakan fitur Search CoinMarketCap berdasarkan symbol.\n"
            "3. Setelah masuk ke detail koin, WAJIB klik tombol 'TradingView' di bagian grafik untuk beralih ke candlestick interaktif.\n"
            "4. Klik timeframe '1h' atau '4h' dan gunakan aksi wait 8 detik agar grafik termuat sempurna.\n"
            "5. Analisis visual grafik: pastikan harga berkonsolidasi sideways mendatar dalam range sempit.\n"
            "6. Buka tab 'Markets' (Pasar) di detail koin untuk memastikan koin aktif di Binance Perpetual Futures atau Bitget Futures.\n"
            "7. BEGITU Anda menemukan 3 koin yang memenuhi syarat (sideways mendatar + listing futures), SEGERA STOP (action 'done') dan laporkan hasilnya!\n\n"
            
            "Format output analisismu menjadi 3 koin terbaik dengan format berikut:\n"
            "- Coin Name: [Ticker]\n"
            "- Target Direction: [Long / Short]\n"
            "- Available Platform: [Binance Futures / Bitget Futures / Both]\n"
            "- The Setup Structure: [Deskripsikan pola sideways, batas support, dan resistance saat ini]\n"
            "- Current Technical Reason: [Jelaskan ringkas bentuk kompresi harganya]\n"
            "- Estimated Target Zone: [Sebutkan estimasi kisaran harga masuk spekulatif beserta +5% target TP dan -5% target SL]"
        )
        
        # Step callback to stream agent thoughts and actions in real time
        async def on_step_callback(browser_state, agent_output, step_num):
            try:
                next_action = ""
                if getattr(agent_output, 'action', None):
                    actions_list = agent_output.action
                    if isinstance(actions_list, list) and len(actions_list) > 0:
                        first_act = actions_list[0]
                        next_action = str(getattr(first_act, 'model_dump', lambda: str(first_act))())[:150]
                
                goal = getattr(agent_output, 'next_goal', '') or getattr(agent_output, 'current_plan_item', '')
                memory = getattr(agent_output, 'memory', '')
                
                await emit_callback({
                    "type": "agent_step",
                    "stage": "ai_verification",
                    "step": step_num,
                    "goal": goal,
                    "action": next_action,
                    "memory": memory,
                    "message": f"Step {step_num}: {goal or 'Executing action...'}"
                })
            except Exception as e:
                pass
                
        # Configure Browser Profile (Headed vs Headless)
        browser_profile = BrowserProfile(headless=not headed)
        
        agent = Agent(
            task=prompt_task,
            llm=llm,
            browser_profile=browser_profile,
            register_new_step_callback=on_step_callback
        )
        
        await emit_callback({
            "type": "status",
            "stage": "ai_verification",
            "message": "AI Agent is launching browser and beginning chart inspections..."
        })
        
        history = await agent.run()
        raw_result = history.final_result() or str(history)
        
        # Parse output into clean cards
        cards = parse_trade_cards(raw_result)
        
        await emit_callback({
            "type": "done",
            "stage": "complete",
            "message": "Screening completed successfully!",
            "cards": cards,
            "raw_output": raw_result
        })
        
    except Exception as exc:
        import traceback
        err_detail = traceback.format_exc()
        await emit_callback({
            "type": "error",
            "message": str(exc),
            "traceback": err_detail
        })
