import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from google.cloud import bigquery
from google.oauth2 import service_account
import base64

# ======================================================
# CONFIG
# ======================================================
PROJECT_ID = "uasarw"
SOURCE_DATASET = "market_data2"
EVAL_DATASET = "model_evaluation"

# ======================================================
# BIGQUERY CLIENT (KHUSUS DEPLOY/GITHUB)
# ======================================================
@st.cache_resource
def get_client():
    # Mengambil credentials langsung dari Streamlit Secrets
    # Pastikan nama section di secrets Anda adalah [gcp_service_account]
    try:
        key_dict = st.secrets["gcp_service_account"]
        creds = service_account.Credentials.from_service_account_info(key_dict)
        return bigquery.Client(project=PROJECT_ID, credentials=creds)
    except Exception as e:
        st.error(f"Gagal mengakses Google Cloud Credentials: {e}")
        st.stop()

client = get_client()

st.set_page_config(
    page_title="Dashboard Saham BBCA",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ======================================================
# LOAD LOGO
# ======================================================
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except:
        return None

logo_base64 = get_base64_image("logo bca.png") 

# ======================================================
# CUSTOM CSS
# ======================================================
st.markdown("""
<style>
    /* Import Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    /* Global Styles */
    * {
        font-family: 'Inter', sans-serif;
        color: #334155;
    }
    
    .stApp {
        background: linear-gradient(180deg, #F0F4F9 0%, #FFFFFF 100%);
        background-attachment: fixed;
    }
    
    /* HEADER STYLING */
    .header-container {
        background: linear-gradient(135deg, #E3F2FD 0%, #FFFFFF 80%);
        padding: 1.5rem 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 20px rgba(0, 94, 184, 0.08);
        border: 1px solid #DCEBF7;
        display: flex;
        align-items: center; 
        gap: 2.5rem;
    }
    
    .logo-img {
        height: 120px; 
        width: auto;
        filter: drop-shadow(0 4px 6px rgba(0,0,0,0.1));
    }
    
    .header-text-col {
        display: flex;
        flex-direction: column;
        justify_content: center;
    }
    
    .header-title {
        color: #005EB8 !important;
        font-size: 2.8rem; 
        font-weight: 800;
        margin: 0;
        line-height: 1.1;
        letter-spacing: -0.5px;
    }
    
    .header-subtitle {
        color: #64748B !important;
        font-size: 1.1rem;
        margin: 0.5rem 0 0 0;
        font-weight: 500;
    }
    
    /* SECTION HEADERS (JUDUL UTAMA BAGIAN) */
    .section-container {
        margin-top: 2.5rem;
        margin-bottom: 1.5rem;
        border-bottom: 1px solid #E2E8F0; 
        padding-bottom: 0.5rem;
    }

    .section-title {
        margin: 0 !important;
        color: #1E293B !important;
        font-weight: 700 !important;
        font-size: 1.6rem !important; /* Ukuran Konsisten Utama */
    }
    
    .section-desc {
        color: #94A3B8 !important; 
        font-size: 0.95rem;
        font-weight: 400;
        margin-top: 0.3rem !important;
        margin-bottom: 0 !important;
    }

    /* SUBSECTION HEADERS (JUDUL KECIL - DATA TABLE) */
    /* Ini yang memperbaiki font "Data Aktual" agar pas */
    .subsection-title {
        color: #475569 !important;
        font-size: 1.2rem !important; /* Lebih kecil dari section-title */
        font-weight: 600 !important;
        margin-bottom: 1rem !important;
    }

    /* METRICS & CARDS */
    div[data-testid="stMetric"] {
        background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
        padding: 1.2rem;
        border-radius: 12px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.04);
        border: 1px solid #EEF2F6;
        text-align: center;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.9rem;
        font-weight: 600;
        color: #64748B !important;
        justify-content: center;
    }
    
    [data-testid="stMetricValue"] {
        font-size: 1.8rem;
        font-weight: 700;
        color: #005EB8 !important;
    }

    /* META CARD */
    .meta-card {
        background-color: #FFFFFF;
        border-radius: 50px;
        padding: 0.8rem 2.5rem;
        margin-top: 1.5rem;
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 2rem;
        border: 1px solid #E2E8F0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        width: fit-content;
        margin-left: auto;
        margin-right: auto;
    }

    .meta-item {
        font-size: 0.95rem;
        font-weight: 600;
        color: #64748B;
    }
    
    .meta-value {
        color: #005EB8;
        font-weight: 700;
        margin-left: 5px;
    }

    /* SIDEBAR */
    [data-testid="stSidebar"] {
        background-color: #F8FBFF; 
        border-right: 1px solid #E2E8F0;
    }
    [data-testid="stSidebar"] h3 {
        color: #005EB8 !important;
    }
</style>
""", unsafe_allow_html=True)


# ======================================================
# SIDEBAR
# ======================================================
st.sidebar.markdown("### Pengaturan Analisis")
st.sidebar.caption("Pilih parameter model dan waktu.")
st.sidebar.write("") 

model_choice = st.sidebar.radio("Pilih Model", ["ARIMA", "XGBoost"])

TIMEFRAME_MAP = {
    "1 Menit": {
        "source": "bbca_1menit",
        "ARIMA": "live_eval_arima_1m",
        "XGBoost": "live_eval_xgb_1m",
        "FORECAST": {
            "ARIMA": "live_forecast_arima_1m",
            "XGBoost": "live_forecast_xgb_1m",
        }
    },
    "15 Menit": {
        "source": "bbca_15menit",
        "ARIMA": "live_eval_arima_15m",
        "XGBoost": "live_eval_xgb_15m",
        "FORECAST": {
            "ARIMA": "live_forecast_arima_15m",
            "XGBoost": "live_forecast_xgb_15m",
        }
    },
    "1 Jam": {
        "source": "bbca_1jam",
        "ARIMA": "live_eval_arima_1h",
        "XGBoost": "live_eval_xgb_1h",
        "FORECAST": {
            "ARIMA": "live_forecast_arima_1h",
            "XGBoost": "live_forecast_xgb_1h",
        }
    },
    "1 Hari": {
        "source": "bbca_1hari",
        "ARIMA": "live_eval_arima_1d",
        "XGBoost": "live_eval_xgb_1d",
        "FORECAST": {
            "ARIMA": "live_forecast_arima_1d",
            "XGBoost": "live_forecast_xgb_1d",
        }
    },
    "1 Bulan": {
        "source": "bbca_1bulan",
        "ARIMA": "live_eval_arima_1mo",
        "XGBoost": "live_eval_xgb_1mo",
        "FORECAST": {
            "ARIMA": "live_forecast_arima_1mo",
            "XGBoost": "live_forecast_xgb_1mo",
        }
    },
}

timeframe = st.sidebar.selectbox("Timeframe Data", list(TIMEFRAME_MAP.keys()))

source_table = TIMEFRAME_MAP[timeframe]["source"]
eval_table = TIMEFRAME_MAP[timeframe][model_choice]
FORECAST_DATASET = "model_live_forecast"
forecast_table = TIMEFRAME_MAP[timeframe]["FORECAST"][model_choice]

# ======================================================
# LOAD DATA
# ======================================================
@st.cache_data(ttl=60)
def load_market_data(table):
    query = f"""
    SELECT timestamp, close
    FROM `{PROJECT_ID}.{SOURCE_DATASET}.{table}`
    ORDER BY timestamp DESC
    LIMIT 700
    """
    df = client.query(query).to_dataframe()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["close"] = df["close"].astype(float)
    df = df.sort_values("timestamp")
    return df

@st.cache_data(ttl=60)
def load_evaluation(table):
    query = f"""
    SELECT
        model_name, timeframe, evaluation_type,
        train_start_ts, train_end_ts, test_start_ts, test_end_ts,
        train_samples, test_samples, mae, rmse, mape,
        model_config, run_time
    FROM `{PROJECT_ID}.{EVAL_DATASET}.{table}`
    ORDER BY run_time DESC
    LIMIT 1
    """
    return client.query(query).to_dataframe()

@st.cache_data(ttl=60)
def load_forecast_data(table):
    query = f"""
    SELECT
        forecast_timestamp AS timestamp,
        forecast_close
    FROM `{PROJECT_ID}.{FORECAST_DATASET}.{table}`
    ORDER BY forecast_timestamp ASC
    """
    df = client.query(query).to_dataframe()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["forecast_close"] = df["forecast_close"].astype(float)
    return df

@st.cache_data(ttl=300)
def load_market_summary(table):
    query = f"""
    SELECT
        COUNT(*) AS total_rows,
        AVG(close) AS avg_price,
        (
            SELECT close
            FROM `{PROJECT_ID}.{SOURCE_DATASET}.{table}`
            ORDER BY timestamp DESC
            LIMIT 1
        ) AS last_price
    FROM `{PROJECT_ID}.{SOURCE_DATASET}.{table}`
    """
    return client.query(query).to_dataframe().iloc[0]

# ======================================================
# FETCH DATA
# ======================================================
df_market = load_market_data(source_table)
df_eval = load_evaluation(eval_table)
forecast_table = TIMEFRAME_MAP[timeframe]["FORECAST"][model_choice]
df_forecast = load_forecast_data(forecast_table)
df_summary = load_market_summary(source_table)

last_actual_ts = df_market["timestamp"].max()
df_forecast = df_forecast[df_forecast["timestamp"] > last_actual_ts]

# ======================================================
# HEADER
# ======================================================
if logo_base64:
    st.markdown(f"""
    <div class="header-container">
        <img src="data:image/png;base64,{logo_base64}" class="logo-img" alt="BCA Logo">
        <div class="header-text-col">
            <h1 class="header-title">Dashboard Saham BBCA</h1>
            <p class="header-subtitle">Analisis harga historis dan evaluasi performa model AI</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="header-container">
        <div class="header-text-col">
            <h1 class="header-title">Dashboard Saham BBCA</h1>
            <p class="header-subtitle">Analisis harga historis dan evaluasi performa model AI</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ======================================================
# RINGKASAN PASAR
# ======================================================
st.markdown("""
<div class="section-container">
    <h3 class="section-title">Ringkasan Pasar</h3>
    <p class="section-desc">Statistik data historis keseluruhan.</p>
</div>
""", unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
c1.metric("Jumlah Data", int(df_summary["total_rows"]))
c2.metric("Harga Terakhir", f"{df_summary['last_price']:.2f}")
c3.metric("Rata-rata Harga", f"{df_summary['avg_price']:.2f}")

# ======================================================
# EVALUASI MODEL
# ======================================================
st.markdown("""
<div class="section-container">
    <h3 class="section-title">Evaluasi Performa Model</h3>
    <p class="section-desc">Metrik berdasarkan data pengujian (Test Set).</p>
</div>
""", unsafe_allow_html=True)

if df_eval.empty:
    st.warning("Data evaluasi belum tersedia.")
else:
    mae = float(df_eval["mae"].iloc[0])
    rmse = float(df_eval["rmse"].iloc[0])
    mape = float(df_eval["mape"].iloc[0])
    
    e1, e2, e3 = st.columns(3)
    e1.metric("MAE", f"{mae:.2f}")
    e2.metric("RMSE", f"{rmse:.2f}")
    e3.metric("MAPE", f"{mape:.2f}%")
    
    train_count = int(df_eval['train_samples'].iloc[0])
    test_count = int(df_eval['test_samples'].iloc[0])
    
    st.markdown(f"""
    <div class="meta-card">
        <span class="meta-item">Train Samples: <span class="meta-value">{train_count}</span></span>
        <span style="color: #CBD5E1;">|</span>
        <span class="meta-item">Test Samples: <span class="meta-value">{test_count}</span></span>
    </div>
    """, unsafe_allow_html=True)

# ======================================================
# CHART AKTUAL
# ======================================================
st.markdown("""
<div class="section-container">
    <h3 class="section-title">Pergerakan Harga Saham</h3>
    <p class="section-desc">Visualisasi perbandingan harga aktual dan hasil prediksi.</p>
</div>
""", unsafe_allow_html=True)

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=df_market["timestamp"],
    y=df_market["close"],
    name="Harga Aktual",
    mode="lines",
    line=dict(color="#005EB8", width=2)
))

if not df_forecast.empty:
    fig.add_trace(go.Scatter(
        x=df_forecast["timestamp"],
        y=df_forecast["forecast_close"],
        name="Forecast",
        mode="lines+markers",
        line=dict(
            color="#EF4444", 
            width=2,
            dash="dash"
        ),
        marker=dict(size=5)
    ))

fig.update_layout(
    template="plotly_white",
    height=450,
    margin=dict(l=20, r=20, t=30, b=20),
    xaxis_title="Waktu",
    yaxis_title="Harga Saham",
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    ),
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
)

st.plotly_chart(fig, use_container_width=True)

# ======================================================
# DATA TABLE
# ======================================================
st.markdown("""
<div class="section-container">
    <h3 class="section-title">Data Detail</h3>
    <p class="section-desc">Tabel data harga historis dan hasil prediksi.</p>
</div>
""", unsafe_allow_html=True)

t1, t2 = st.columns(2)
with t1:
    # Mengganti st.subheader dengan Custom Markdown agar ukuran font sesuai
    st.markdown('<p class="subsection-title">Data Aktual </p>', unsafe_allow_html=True)
    st.dataframe(
        df_market.sort_values("timestamp", ascending=False).head(100), 
        use_container_width=True
    )
with t2:
    # Mengganti st.subheader dengan Custom Markdown agar ukuran font sesuai
    st.markdown('<p class="subsection-title">Data Forecast</p>', unsafe_allow_html=True)
    if not df_forecast.empty:
        st.dataframe(
            df_forecast.sort_values("timestamp", ascending=False), 
            use_container_width=True
        )
    else:
        st.info("Tidak ada data forecast.")