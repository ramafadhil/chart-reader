import asyncio
import sys
sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
from playwright.async_api import async_playwright
from browser_use import Agent
from browser_use.llm.google.chat import ChatGoogle

load_dotenv()

def parse_percent(val_str):
    if not val_str:
        return 0.0
    cleaned = val_str.replace('%', '').replace('$', '').replace(',', '').strip()
    for char in ['▲', '▼', ' ', '\n', '\t']:
        cleaned = cleaned.replace(char, '')
    try:
        return float(cleaned)
    except Exception:
        return 0.0

def parse_amount(val_str):
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

async def scrape_cmc_page(page, url):
    print(f"🌐 Menelusuri list CoinMarketCap: {url}...")
    await page.goto(url, timeout=60000)
    await page.wait_for_timeout(3000)
    
    # Scroll down slowly to trigger lazy loading of rows
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

async def run_pre_screening():
    print("📊 Menjalankan pre-screening matematis di CoinMarketCap...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Scrape page 1 (ranks 1-100)
        data1 = await scrape_cmc_page(page, "https://coinmarketcap.com/")
        # Scrape page 2 (ranks 101-200)
        data2 = await scrape_cmc_page(page, "https://coinmarketcap.com/?page=2")
        
        all_data = data1 + data2
        await browser.close()
        
        stablecoins_keywords = ['USD', 'EUR', 'GBP', 'USDT', 'USDC', 'TUSD', 'FDUSD', 'EURC', 'DAI', 'BUSD', 'UST', 'STABLE', 'STABLES']
        
        shortlist = []
        for coin in all_data:
            try:
                rank = int(coin['rankText'])
            except ValueError:
                continue
                
            # Filter rank 50-200
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
                    'compression_ratio': compression_ratio,
                    'vmc_ratio': vmc_ratio,
                    'price': coin['priceText']
                })
        
        # Sort shortlist by compression ratio (lowest first)
        shortlist.sort(key=lambda x: x['compression_ratio'])
        return shortlist

async def get_working_models():
    models_priority = [
        "gemini-3.1-pro-preview",
        "gemini-2.5-pro",
        "gemini-3.5-flash",
        "gemini-2.0-flash",
        "gemini-3.1-flash-lite"
    ]
    
    working_models = []
    print("🔍 Memeriksa ketersediaan kuota model Gemini...")
    from browser_use.llm.messages import UserMessage
    
    for model_name in models_priority:
        try:
            # Uji model dengan request minimal
            llm = ChatGoogle(model=model_name, temperature=0.0, max_output_tokens=8192)
            messages = [UserMessage(content="hi")]
            await llm.ainvoke(messages)
            print(f"✅ Model '{model_name}' aktif dan memiliki kuota!")
            working_models.append(llm)
            if len(working_models) == 2:
                break
        except Exception as e:
            # Jika ada validation error, berarti model merespon dengan benar dan kuota aktif
            err_name = type(e).__name__
            if "validation" in err_name.lower() or "validation" in str(e).lower():
                print(f"✅ Model '{model_name}' aktif dan memiliki kuota (validation check passed)!")
                working_models.append(ChatGoogle(model=model_name, temperature=0.0, max_output_tokens=8192))
                if len(working_models) == 2:
                    break
            else:
                print(f"❌ Model '{model_name}' terlewati: {err_name}")
            
    if not working_models:
        raise RuntimeError("Semua model Gemini dalam daftar prioritas tidak memiliki kuota aktif atau tidak dapat diakses.")

    primary_llm = working_models[0]
    fallback_llm = working_models[1] if len(working_models) > 1 else None
    return primary_llm, fallback_llm

async def main():
    # 1. Jalankan pre-screening matematis di python
    shortlist = await run_pre_screening()
    
    if not shortlist:
        print("❌ Tidak ada koin yang memenuhi kriteria pre-screening.")
        return
        
    print("\n=== MATHEMATICAL SHORTLIST ===")
    shortlist_lines = []
    for item in shortlist:
        line = f"Rank {item['rank']}: {item['name']} ({item['symbol']}) - CR: {item['compression_ratio']:.3f}, VMC: {item['vmc_ratio']:.3f}, Price: {item['price']}"
        print(line)
        shortlist_lines.append(line)
    print("==============================\n")
    
    shortlist_text = "\n".join(shortlist_lines)
    
    # 2. Setup prompt untuk Agent dengan shortlist yang sudah didapatkan
    prompt_tugas = (
        "Act as a professional Crypto Technical Analyst and Volatility Screener.\n"
        "Buka browser dan verifikasi koin-koin yang ada pada shortlist berikut di CoinMarketCap (https://coinmarketcap.com/):\n\n"
        
        f"=== SHORTLIST KOIN UNTUK DIVERIFIKASI ===\n"
        f"{shortlist_text}\n"
        f"=========================================\n\n"
        
        "CRITICAL RULE FOR REASONING LENGTH (PREVENT TRUNCATION ERROR):\n"
        "- Tulis 'Eval' dan 'Memory' Anda dengan sangat singkat (maksimal 1 kalimat pendek, kurang dari 15 kata).\n"
        "- JANGAN mendeskripsikan elemen DOM secara detail. Langsung lakukan tindakan agar respon Anda tetap pendek dan tidak terpotong (truncated) oleh batasan 8096 token!\n\n"
        
        "PETUNJUK ALUR KERJA (WAJIB DIIKUTI UNTUK SETIAP KOIN TANPA KECUALI):\n"
        "1. VERIFIKASI DARI SHORTLIST SECARA BERURUTAN:\n"
        "   - Lakukan verifikasi satu-per-satu untuk koin di dalam shortlist (urut dari koin pertama ke bawah).\n"
        "2. CARI DAN BUKA HALAMAN DETAIL KOIN:\n"
        "   - Gunakan fitur Search di CoinMarketCap untuk menemukan koin tersebut (cari berdasarkan symbol/ticker seperti 'JTO' atau 'ATOM').\n"
        "   - Klik koin tersebut dari hasil pencarian untuk membuka halaman detailnya.\n"
        "3. UBAH KE CHART TRADINGVIEW & TAMPILAN TIME-FRAME (WAJIB SISTEMATIS):\n"
        "   - Setelah masuk ke halaman detail koin, Anda WAJIB mengklik tombol bertuliskan 'TradingView' (terletak di bagian atas grafik di samping tab 'Price'/'Mkt Cap') untuk mengubah tampilan grafik menjadi grafik candlestick interaktif.\n"
        "   - Setelah beralih ke mode TradingView, klik tombol rentang waktu '1h' atau '4h' yang ada di kanan atas grafik untuk memantau grafik candlestick 1-Hour atau 4-Hour secara tepat.\n"
        "   - Anda WAJIB menggunakan aksi 'wait' selama 8 detik (seconds: 8) setelah memilih timeframe agar lilin candlestick termuat penuh.\n"
        "   - JANGAN menganalisis chart jika Anda belum mengklik 'TradingView', belum mengklik '1h'/'4h', dan belum melakukan wait 8 detik!\n"
        "   - Periksa visual chart candlestick untuk memastikan harga bergerak sideways mendatar dalam rentang sempit (flat range/consolidation) dan volume perdagangan cenderung menurun.\n"
        "   - JANGAN menyebutkan indikator Bollinger Bands atau indikator teknikal lain yang tidak Anda aktifkan secara manual pada grafik! Cukup jelaskan bentuk konsolidasi mendatar lilin candlestick 1H/4H serta range support dan resistance secara objektif.\n"
        "4. VERIFIKASI FUTURES DI TAB 'MARKETS':\n"
        "   - Buka tab 'Markets' (Pasar) di halaman detail koin tersebut.\n"
        "   - Pastikan koin tersebut aktif terdaftar di Perpetual Futures Binance (USD-M Perpetual) atau Bitget Futures.\n"
        "5. SELEKSI & BATAS MAKSIMAL:\n"
        "   - Jika koin memiliki konsolidasi sideways mendatar DAN terdaftar aktif di futures Binance/Bitget, simpan koin tersebut.\n"
        "   - BEGITU Anda sudah menemukan 3 koin yang memenuhi syarat, segera STOP (gunakan action 'done') dan laporkan hasilnya. Jangan menelusuri sisa shortlist lainnya demi menghemat waktu dan kuota!\n"
        "   - Jika dari seluruh list Anda hanya menemukan kurang dari 3 koin yang ideal, laporkan koin-koin terbaik yang paling mendekati syarat (pilih 3 koin yang paling sideways mendatar).\n\n"
        
        "Format output analisismu menjadi 3 koin terbaik dengan struktur data bersih ini:\n"
        "- Coin Name: [Ticker]\n"
        "- Target Direction: [Long / Short]\n"
        "- Available Platform: [Binance Futures / Bitget Futures / Both]\n"
        "- The Setup Structure: [Deskripsikan pola sideways, batas support, dan resistance saat ini]\n"
        "- Current Technical Reason: [Jelaskan ringkas bentuk kompresi harganya]\n"
        "- Estimated Target Zone (5%): [Sebutkan estimasi kisaran harga masuk spekulatif beserta +5% target TP dan -5% target SL]"
    )
    
    # 3. Inisialisasi Google Gemini dengan mencari model utama & fallback yang memiliki kuota
    primary_llm, fallback_llm = await get_working_models()
    if fallback_llm:
        print(f"ℹ️ Menggunakan fallback model: '{fallback_llm.model}' jika model utama kehabisan kuota.")
    
    # 4. Jalankan Agent
    agent = Agent(
        task=prompt_tugas,
        llm=primary_llm,
        fallback_llm=fallback_llm
    )
    
    print("🤖 Gemini AI Agent sedang membuka browser dan melakukan verifikasi grafik...")
    result = await agent.run()
    
    print("\n📊 DATA RAW UNTUK REKONFIRMASI CLAUDE:")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())