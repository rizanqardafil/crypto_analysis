import streamlit as st
import requests
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import pandas as pd

# ===== KONFIGURASI API =====
CMC_API_KEY = "9b77ca70-310b-4975-b4a6-ae1235330c7a"
FEAR_GREED_API = "https://api.alternative.me/fng/"

# ===== FUNGSI AMBIL DATA =====
@st.cache_data(ttl=300)  # Cache 5 menit
def get_cmc_data(coin_id):
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY}
    params = {"id": coin_id, "convert": "USD"}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()["data"][str(coin_id)]
            quote = data["quote"]["USD"]
            return {
                "name": data["name"],
                "symbol": data["symbol"],
                "harga": quote["price"],
                "perubahan_1h": quote.get("percent_change_1h", 0),
                "perubahan_24h": quote.get("percent_change_24h", 0),
                "perubahan_7d": quote.get("percent_change_7d", 0),
                "perubahan_30d": quote.get("percent_change_30d", 0),
                "volume": quote["volume_24h"],
                "volume_change": quote.get("volume_change_24h", 0),
                "market_cap": quote["market_cap"],
                "market_cap_dominance": quote.get("market_cap_dominance", 0),
                "fully_diluted_market_cap": quote.get("fully_diluted_market_cap", 0),
                "last_updated": quote["last_updated"],
                "circulating_supply": data.get("circulating_supply", 0),
                "total_supply": data.get("total_supply", 0),
                "max_supply": data.get("max_supply", 0),
                "cmc_rank": data.get("cmc_rank", 0)
            }
        else:
            st.error(f"Error API: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Kesalahan: {str(e)}")
        return None

@st.cache_data(ttl=3600)  # Cache 1 jam
def get_fear_greed_index():
    try:
        response = requests.get(FEAR_GREED_API)
        if response.status_code == 200:
            data = response.json()["data"][0]
            return {
                "value": int(data["value"]),
                "classification": data["value_classification"],
                "timestamp": data["timestamp"]
            }
    except:
        return None

@st.cache_data(ttl=3600)
def get_global_metrics():
    url = "https://pro-api.coinmarketcap.com/v1/global-metrics/quotes/latest"
    headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()["data"]["quote"]["USD"]
            return {
                "total_market_cap": data["total_market_cap"],
                "total_volume_24h": data["total_volume_24h"],
                "bitcoin_dominance": data["btc_dominance"],
                "eth_dominance": data["eth_dominance"],
                "defi_dominance": data.get("defi_dominance", 0),
                "defi_volume": data.get("defi_volume_24h", 0),
                "stablecoin_dominance": data.get("stablecoin_dominance", 0)
            }
    except:
        return None

# ===== FUNGSI PENCARIAN COIN =====
@st.cache_data(ttl=3600)
def search_coin(query):
    """Search coin by name or symbol"""
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/map"
    headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY}
    params = {"listing_status": "active", "limit": 100}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            coins = response.json()["data"]
            # Filter berdasarkan query
            filtered_coins = []
            query_lower = query.lower()
            
            for coin in coins:
                if (query_lower in coin["name"].lower() or 
                    query_lower in coin["symbol"].lower()):
                    filtered_coins.append({
                        "id": coin["id"],
                        "name": coin["name"],
                        "symbol": coin["symbol"],
                        "display": f"{coin['name']} ({coin['symbol']})"
                    })
            
            return filtered_coins[:20]  # Limit to 20 results
        else:
            return []
    except Exception as e:
        st.error(f"Error searching coins: {str(e)}")
        return []

# ===== DAFTAR COIN POPULER =====
popular_coins = {
    1: "Bitcoin (BTC)",
    1027: "Ethereum (ETH)", 
    14806: "MANTRA (OM)",
    1839: "BNB (BNB)",
    5426: "Solana (SOL)",
    74: "Dogecoin (DOGE)",
    825: "Tether (USDT)",
    3408: "USD Coin (USDC)",
    52: "XRP (XRP)",
    2010: "Cardano (ADA)",
    5805: "Avalanche (AVAX)",
    11840: "Polygon (MATIC)",
    1958: "TRON (TRX)",
    4943: "Dai (DAI)",
    7083: "Uniswap (UNI)"
}

# ===== FUNGSI ANALISIS =====
def analyze_trend(data):
    """Analisis trend sederhana berdasarkan perubahan harga"""
    if data["perubahan_24h"] > 5:
        return "🚀 BULLISH KUAT", "success"
    elif data["perubahan_24h"] > 1:
        return "📈 Bullish", "success"  
    elif data["perubahan_24h"] > -1:
        return "➡️ Sideways", "info"
    elif data["perubahan_24h"] > -5:
        return "📉 Bearish", "warning"
    else:
        return "💥 BEARISH KUAT", "error"

def calculate_pivot_points(high, low, close):
    """
    Hitung Pivot Points menggunakan rumus matematika standar
    Berdasarkan High, Low, Close dari periode sebelumnya
    """
    # Pivot Point utama
    pivot_point = (high + low + close) / 3
    
    # Resistance levels
    r1 = (2 * pivot_point) - low
    r2 = pivot_point + (high - low)
    r3 = high + 2 * (pivot_point - low)
    
    # Support levels
    s1 = (2 * pivot_point) - high
    s2 = pivot_point - (high - low)
    s3 = low - 2 * (high - pivot_point)
    
    return {
        "pivot_point": pivot_point,
        "resistance": {"R1": r1, "R2": r2, "R3": r3},
        "support": {"S1": s1, "S2": s2, "S3": s3}
    }

def estimate_hlc_from_current_price(current_price, change_24h, volume_change):
    """
    Estimasi High, Low, Close dari data yang tersedia
    Untuk crypto, kita estimasi berdasarkan volatilitas 24h
    """
    # Estimasi volatility range
    volatility = abs(change_24h) / 100
    if volatility < 0.02:  # Low volatility
        range_multiplier = 0.015
    elif volatility < 0.05:  # Medium volatility  
        range_multiplier = 0.025
    else:  # High volatility
        range_multiplier = 0.04
    
    # Estimasi high dan low berdasarkan current price dan volatility
    estimated_high = current_price * (1 + range_multiplier)
    estimated_low = current_price * (1 - range_multiplier)
    
    # Close price estimation (current price adjusted by 24h change)
    estimated_close = current_price / (1 + (change_24h / 100))
    
    return estimated_high, estimated_low, estimated_close

# ===== APLIKASI STREAMLIT =====
st.set_page_config(
    page_title="Crypto Trading Dashboard",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Advanced Crypto Trading Dashboard")
st.markdown("Dashboard lengkap untuk analisis dan trading cryptocurrency")

# Sidebar
with st.sidebar:
    st.header("⚙️ Pengaturan")
    
    # Pilihan metode input
    input_method = st.radio(
        "Pilih Metode:",
        ["🔍 Search Coin", "⭐ Popular Coins", "🔢 Manual ID"],
        index=0
    )
    
    coin_id = None
    selected_coin_name = ""
    
    if input_method == "🔍 Search Coin":
        # Search input
        search_query = st.text_input(
            "🔍 Cari Coin (nama atau symbol):",
            placeholder="Contoh: bitcoin, BTC, ethereum"
        )
        
        if search_query and len(search_query) >= 2:
            with st.spinner("Mencari coin..."):
                search_results = search_coin(search_query)
            
            if search_results:
                # Tampilkan hasil pencarian
                coin_names = [coin["display"] for coin in search_results]
                selected_display = st.selectbox(
                    "Pilih dari hasil pencarian:",
                    coin_names
                )
                
                # Get coin ID
                for coin in search_results:
                    if coin["display"] == selected_display:
                        coin_id = coin["id"]
                        selected_coin_name = coin["display"]
                        break
            else:
                st.warning("Tidak ada hasil ditemukan. Coba kata kunci lain.")
        
        elif search_query:
            st.info("Ketik minimal 2 karakter untuk mulai pencarian")
    
    elif input_method == "⭐ Popular Coins":
        # Popular coins dropdown
        selected_name = st.selectbox(
            "Pilih Popular Coins:",
            options=list(popular_coins.values()),
            index=0
        )
        coin_id = [id for id, name in popular_coins.items() if name == selected_name][0]
        selected_coin_name = selected_name
    
    elif input_method == "🔢 Manual ID":
        # Manual ID input
        manual_id = st.number_input(
            "Masukkan Coin ID:",
            min_value=1,
            value=1,
            help="Dapatkan ID dari CoinMarketCap URL. Contoh: 1 untuk Bitcoin"
        )
        coin_id = int(manual_id)
        selected_coin_name = f"Coin ID: {coin_id}"
    
    st.markdown("---")
    
    # Info section
    with st.expander("ℹ️ Tips Pencarian"):
        st.markdown("""
        **🔍 Search Tips:**
        - Gunakan nama lengkap: "Bitcoin", "Ethereum"
        - Atau symbol: "BTC", "ETH", "ADA"
        - Pencarian tidak case sensitive
        - Minimal 2 karakter
        
        **🔢 Manual ID:**
        - Bitcoin: 1
        - Ethereum: 1027
        - BNB: 1839
        - Solana: 5426
        
        **📊 Cara dapat ID:**
        1. Buka coinmarketcap.com
        2. Cari coin yang diinginkan
        3. Lihat angka di URL
        """)
    
    if st.button("🔄 Refresh Data", type="primary"):
        st.cache_data.clear()
        st.rerun()

# Layout dengan tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📈 Analisis Teknis", "🌍 Market Global", "🎯 Trading Signals"])

# Ambil data
if coin_id:
    data = get_cmc_data(coin_id)
    global_data = get_global_metrics()
    fear_greed = get_fear_greed_index()
else:
    st.warning("⚠️ Silakan pilih atau cari coin terlebih dahulu!")
    st.stop()

if data:
    with tab1:
        # Header coin info
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.header(f"{data['name']} ({data['symbol']})")
            st.caption(f"Rank #{data['cmc_rank']} | Selected: {selected_coin_name}")
            st.caption(f"Last Update: {datetime.fromisoformat(data['last_updated'].replace('Z', '+00:00')).strftime('%H:%M:%S UTC')}")
        
        with col2:
            trend, trend_color = analyze_trend(data)
            if trend_color == "success":
                st.success(trend)
            elif trend_color == "warning":
                st.warning(trend)
            elif trend_color == "error":
                st.error(trend)
            else:
                st.info(trend)
        
        with col3:
            if fear_greed:
                st.metric("Fear & Greed Index", f"{fear_greed['value']}/100", fear_greed['classification'])

        # Price metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "💰 Harga Terkini", 
                f"${data['harga']:,.4f}",
                f"{data['perubahan_24h']:+.2f}%"
            )
        
        with col2:
            st.metric(
                "📊 Volume 24h",
                f"${data['volume']:,.0f}",
                f"{data['volume_change']:+.2f}%"
            )
        
        with col3:
            st.metric(
                "🏛️ Market Cap",
                f"${data['market_cap']:,.0f}",
                f"Dominance: {data['market_cap_dominance']:.2f}%"
            )
        
        with col4:
            st.metric(
                "🔄 Circulating Supply",
                f"{data['circulating_supply']:,.0f} {data['symbol']}",
                f"Max: {data['max_supply']:,.0f}" if data['max_supply'] else "No Max"
            )

        # Timeframe analysis
        st.subheader("⏱️ Analisis Multi-Timeframe")
        col1, col2, col3, col4 = st.columns(4)
        
        timeframes = [
            ("1H", data['perubahan_1h']),
            ("24H", data['perubahan_24h']),
            ("7D", data['perubahan_7d']),
            ("30D", data['perubahan_30d'])
        ]
        
        for i, (tf, change) in enumerate(timeframes):
            with [col1, col2, col3, col4][i]:
                delta_color = "normal" if change >= 0 else "inverse"
                st.metric(tf, f"{change:+.2f}%", delta_color=delta_color)

    with tab2:
        st.subheader("📈 Analisis Teknis & Pivot Points")
        
        # Hitung pivot points
        estimated_high, estimated_low, estimated_close = estimate_hlc_from_current_price(
            data['harga'], data['perubahan_24h'], data['volume_change']
        )
        
        pivot_data = calculate_pivot_points(estimated_high, estimated_low, estimated_close)
        current_price = data['harga']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🎯 Pivot Points Analysis")
            st.caption("📊 Berdasarkan estimasi High/Low/Close 24h")
            
            # Pivot Point utama
            st.info(f"**🎯 Pivot Point**: ${pivot_data['pivot_point']:,.4f}")
            
            # Resistance levels
            st.markdown("**🔴 Resistance Levels:**")
            for level, price in pivot_data['resistance'].items():
                distance = ((price - current_price) / current_price) * 100
                if price > current_price:
                    st.success(f"**{level}**: ${price:,.4f} (+{distance:.2f}%)")
                else:
                    st.error(f"**{level}**: ${price:,.4f} (Broken)")
            
            # Support levels  
            st.markdown("**🟢 Support Levels:**")
            for level, price in pivot_data['support'].items():
                distance = ((current_price - price) / current_price) * 100
                if price < current_price:
                    st.success(f"**{level}**: ${price:,.4f} (-{distance:.2f}%)")
                else:
                    st.error(f"**{level}**: ${price:,.4f} (Broken)")
            
            # Current position analysis
            st.markdown("### 📍 Current Position")
            if current_price > pivot_data['pivot_point']:
                st.success(f"💹 **Above Pivot** - Bullish Zone")
                next_resistance = min([r for r in pivot_data['resistance'].values() if r > current_price], default=None)
                if next_resistance:
                    st.info(f"🎯 Next Target: ${next_resistance:,.4f}")
            else:
                st.warning(f"📉 **Below Pivot** - Bearish Zone") 
                next_support = max([s for s in pivot_data['support'].values() if s < current_price], default=None)
                if next_support:
                    st.info(f"🛡️ Next Support: ${next_support:,.4f}")
        
        with col2:
            # Technical indicators
            st.markdown("### 📊 Technical Indicators")
            
            # RSI approximation
            rsi_approx = 50 + (data['perubahan_24h'] * 2)
            rsi_approx = max(0, min(100, rsi_approx))
            
            st.write(f"**RSI (Approx)**: {rsi_approx:.1f}")
            st.progress(rsi_approx/100)
            
            if rsi_approx > 70:
                st.error("⚠️ Overbought Territory")
            elif rsi_approx < 30:
                st.success("💎 Oversold Territory")
            else:
                st.info("✅ Normal Range")
            
            # Volatility assessment
            st.markdown("### ⚡ Volatility Assessment")
            volatility = abs(data['perubahan_24h'])
            
            if volatility > 10:
                volatility_status = "🔥 Extreme"
                volatility_color = "error"
            elif volatility > 5:
                volatility_status = "⚡ High"
                volatility_color = "warning"
            elif volatility > 2:
                volatility_status = "📊 Medium"
                volatility_color = "info"
            else:
                volatility_status = "😌 Low"
                volatility_color = "success"
            
            if volatility_color == "error":
                st.error(f"{volatility_status}: {volatility:.2f}%")
            elif volatility_color == "warning":
                st.warning(f"{volatility_status}: {volatility:.2f}%")
            elif volatility_color == "info":
                st.info(f"{volatility_status}: {volatility:.2f}%")
            else:
                st.success(f"{volatility_status}: {volatility:.2f}%")

        # Trading setup suggestions
        st.markdown("### 🎯 Trading Setup Suggestions")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**🟢 Long Setup:**")
            nearest_support = max([s for s in pivot_data['support'].values() if s < current_price], default=pivot_data['support']['S1'])
            st.success(f"Entry: ${nearest_support:,.4f}")
            st.info(f"Stop Loss: ${nearest_support * 0.98:,.4f}")
            
        with col2:
            st.markdown("**🔴 Short Setup:**")
            nearest_resistance = min([r for r in pivot_data['resistance'].values() if r > current_price], default=pivot_data['resistance']['R1'])
            st.error(f"Entry: ${nearest_resistance:,.4f}")
            st.info(f"Stop Loss: ${nearest_resistance * 1.02:,.4f}")
            
        with col3:
            st.markdown("**⚖️ Risk Management:**")
            st.warning("Max Risk: 2-3% per trade")
            st.info("R:R Ratio: 1:2 minimum")

        # Volume analysis
        st.markdown("### 📈 Volume Analysis")
        col1, col2 = st.columns(2)
        
        with col1:
            volume_trend = "📈 Increasing" if data['volume_change'] > 0 else "📉 Decreasing"
            st.metric("Volume Trend", volume_trend, f"{data['volume_change']:+.2f}%")
        
        with col2:
            # Volume/Market Cap ratio
            vol_mcap_ratio = (data['volume'] / data['market_cap']) * 100
            st.metric("Volume/MCap Ratio", f"{vol_mcap_ratio:.3f}%")

    with tab3:
        st.subheader("🌍 Global Market Metrics")
        
        if global_data:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "🌐 Total Market Cap",
                    f"${global_data['total_market_cap']:,.0f}"
                )
            
            with col2:
                st.metric(
                    "💧 Total Volume 24h", 
                    f"${global_data['total_volume_24h']:,.0f}"
                )
            
            with col3:
                st.metric(
                    "₿ Bitcoin Dominance",
                    f"{global_data['bitcoin_dominance']:.2f}%"
                )
            
            with col4:
                st.metric(
                    "Ξ Ethereum Dominance",
                    f"{global_data['eth_dominance']:.2f}%"
                )
            
            # Market dominance chart
            st.markdown("### 📊 Market Dominance")
            dominance_data = {
                'Asset': ['Bitcoin', 'Ethereum', 'Others'],
                'Dominance': [
                    global_data['bitcoin_dominance'],
                    global_data['eth_dominance'], 
                    100 - global_data['bitcoin_dominance'] - global_data['eth_dominance']
                ]
            }
            
            fig = px.pie(
                dominance_data, 
                values='Dominance', 
                names='Asset',
                title="Crypto Market Dominance"
            )
            st.plotly_chart(fig)

    with tab4:
        st.subheader("🎯 Trading Signals & Recommendations")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🚦 Trading Signals")
            
            # Enhanced signal generation with pivot points
            signals = []
            
            # Pivot-based signals
            if data['harga'] > pivot_data['pivot_point']:
                if data['perubahan_24h'] > 2:
                    signals.append(("🟢 STRONG BUY", "Above pivot + bullish momentum"))
                else:
                    signals.append(("🟡 BUY", "Above pivot point - bullish zone"))
            else:
                if data['perubahan_24h'] < -2:
                    signals.append(("🔴 STRONG SELL", "Below pivot + bearish momentum"))
                else:
                    signals.append(("🟡 SELL", "Below pivot point - bearish zone"))
            
            # Support/Resistance proximity signals
            nearest_support = max([s for s in pivot_data['support'].values() if s < data['harga']], default=None)
            nearest_resistance = min([r for r in pivot_data['resistance'].values() if r > data['harga']], default=None)
            
            if nearest_support:
                support_distance = ((data['harga'] - nearest_support) / data['harga']) * 100
                if support_distance < 2:
                    signals.append(("💎 NEAR SUPPORT", f"Only {support_distance:.1f}% above support"))
            
            if nearest_resistance:
                resistance_distance = ((nearest_resistance - data['harga']) / data['harga']) * 100
                if resistance_distance < 2:
                    signals.append(("⚠️ NEAR RESISTANCE", f"Only {resistance_distance:.1f}% below resistance"))
            
            # Volume confirmation
            if data['volume_change'] > 20:
                signals.append(("📈 Volume Spike", "High trading activity - trend confirmation"))
            elif data['volume_change'] < -20:
                signals.append(("📉 Low Volume", "Weak activity - trend may reverse"))
            
            # Fear & Greed context
            if fear_greed:
                if fear_greed['value'] < 25:
                    signals.append(("💎 EXTREME FEAR", "Market panic - potential opportunity"))
                elif fear_greed['value'] > 75:
                    signals.append(("⚠️ EXTREME GREED", "Market euphoria - exercise caution"))
            
            # Display signals with proper colors
            for signal, description in signals:
                if "STRONG BUY" in signal or "NEAR SUPPORT" in signal or "EXTREME FEAR" in signal:
                    st.success(f"**{signal}**: {description}")
                elif "STRONG SELL" in signal or "NEAR RESISTANCE" in signal or "EXTREME GREED" in signal:
                    st.error(f"**{signal}**: {description}")
                elif "BUY" in signal:
                    st.info(f"**{signal}**: {description}")
                elif "SELL" in signal:
                    st.warning(f"**{signal}**: {description}")
                else:
                    st.info(f"**{signal}**: {description}")
        
        with col2:
            st.markdown("### 💡 Pivot Points Trading Guide")
            
            st.markdown("**🎯 Timeframe Recommendations:**")
            timeframe_tips = [
                "📊 **Daily (24h)**: Best for swing trading",
                "⚡ **4-Hour**: Good for day trading", 
                "🚀 **1-Hour**: Scalping and quick trades",
                "📈 **Weekly**: Position trading",
            ]
            
            for tip in timeframe_tips:
                st.markdown(f"• {tip}")
            
            st.markdown("**📐 How Pivot Points Work:**")
            pivot_guide = [
                "🎯 **Pivot Point**: Main support/resistance level",
                "🟢 **Above Pivot**: Bullish bias, look for longs",
                "🔴 **Below Pivot**: Bearish bias, look for shorts",
                "📊 **R1, R2, R3**: Resistance levels for take profit",
                "🛡️ **S1, S2, S3**: Support levels for stop loss"
            ]
            
            for guide in pivot_guide:
                st.markdown(f"• {guide}")
            
            st.markdown("### ⚠️ Risk Management")
            risk_tips = [
                "🎯 **Entry**: Near support for longs, resistance for shorts",
                "🛑 **Stop Loss**: 1-2% beyond support/resistance",
                "💰 **Take Profit**: Next resistance/support level",
                "⚖️ **Position Size**: Max 2-3% account risk",
                "📊 **Confirmation**: Use volume + RSI for entry"
            ]
            
            for tip in risk_tips:
                st.markdown(f"• {tip}")
            
            st.warning("⚠️ **Disclaimer**: Pivot points are estimates based on 24h data. Real High/Low/Close from exchange data will be more accurate!")

else:
    st.error("❌ Tidak dapat mengambil data. Periksa koneksi internet dan API key.")

# Footer
st.markdown("---")
st.markdown("**⚠️ Disclaimer**: Dashboard ini hanya untuk edukasi. Bukan saran investasi!")
st.markdown("🔗 **Data Source**: [CoinMarketCap](https://coinmarketcap.com) | [Fear & Greed Index](https://alternative.me)")