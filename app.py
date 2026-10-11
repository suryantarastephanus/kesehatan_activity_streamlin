import os
from datetime import datetime, date, timedelta
import pandas as pd
import psycopg2
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

# ==============================================================================
# 🩺 DASHBOARD KESEHATAN OM STAN — DESKTOP REMAKE
# Dioptimalkan dengan prinsip:
# - Visual Hierarchy, Law of Common Region, Data-ink ratio, Dark Mode Design
# - UI/UX Pro Max Design Intelligence
# ==============================================================================

st.set_page_config(
    page_title="Dashboard Kesehatan Om Stan — Executive Protocol",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load environment (.env.local / .env)
def load_local_env():
    for fname in [".env.local", ".env"]:
        env_path = os.path.join(os.path.dirname(__file__), fname)
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        if k not in os.environ:
                            os.environ[k] = v

load_local_env()

# ==============================================================================
# 🎨 DESKTOP DESIGN SYSTEM & STYLING
# ==============================================================================
DESKTOP_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

/* Typography & Root Variables */
:root {
    --bg-dark: #090D16;
    --surface-1: #0F172A;
    --surface-2: #1E293B;
    --border-subtle: rgba(255, 255, 255, 0.08);
    --border-highlight: rgba(56, 189, 248, 0.25);
    --accent-cyan: #06B6D4;
    --accent-emerald: #10B981;
    --accent-amber: #F59E0B;
    --accent-rose: #F43F5E;
    --accent-blue: #38BDF8;
}

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
    color: #F8FAFC;
}

/* Maximize Desktop Layout */
.main .block-container {
    padding-top: 1.2rem;
    padding-bottom: 2rem;
    padding-left: 2rem;
    padding-right: 2rem;
    max-width: 1600px;
}

/* Custom Scrollbar */
::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}
::-webkit-scrollbar-track {
    background: rgba(15, 23, 42, 0.6);
}
::-webkit-scrollbar-thumb {
    background: rgba(148, 163, 184, 0.25);
    border-radius: 9999px;
}
::-webkit-scrollbar-thumb:hover {
    background: rgba(148, 163, 184, 0.45);
}

/* Desktop Header Bar */
.desktop-header {
    background: linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 41, 59, 0.8) 100%);
    border: 1px solid var(--border-subtle);
    border-radius: 16px;
    padding: 16px 24px;
    margin-bottom: 18px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
    backdrop-filter: blur(12px);
}

.profile-badge {
    display: flex;
    align-items: center;
    gap: 14px;
}

.avatar-circle {
    width: 48px;
    height: 48px;
    border-radius: 14px;
    background: linear-gradient(135deg, #0284C7 0%, #0369A1 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.6rem;
    box-shadow: 0 0 15px rgba(2, 132, 199, 0.35);
}

/* Primary Metric Cards */
.metric-card {
    background: linear-gradient(145deg, rgba(30, 41, 59, 0.75) 0%, rgba(15, 23, 42, 0.9) 100%);
    border: 1px solid var(--border-subtle);
    border-radius: 16px;
    padding: 20px;
    box-shadow: 0 4px 18px rgba(0, 0, 0, 0.22);
    backdrop-filter: blur(8px);
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    position: relative;
    overflow: hidden;
}
.metric-card:hover {
    transform: translateY(-2px);
    border-color: var(--border-highlight);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
}
.metric-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 3px;
    background: linear-gradient(90deg, transparent, rgba(56, 189, 248, 0.4), transparent);
}

.metric-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}

.metric-label {
    color: #94A3B8;
    font-size: 0.8rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}

.metric-number {
    font-size: 2.25rem;
    font-weight: 800;
    line-height: 1;
    color: #F8FAFC;
    letter-spacing: -0.03em;
    font-feature-settings: "tnum";
}

.metric-unit {
    font-size: 1rem;
    font-weight: 600;
    color: #64748B;
    margin-left: 6px;
}

.metric-footer {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 12px;
}

/* Status Badges */
.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 4px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.02em;
}
.pill-emerald { background: rgba(16, 185, 129, 0.15); color: #34D399; border: 1px solid rgba(16, 185, 129, 0.35); }
.pill-amber { background: rgba(245, 158, 11, 0.15); color: #FBBF24; border: 1px solid rgba(245, 158, 11, 0.35); }
.pill-rose { background: rgba(244, 63, 94, 0.15); color: #FB7185; border: 1px solid rgba(244, 63, 94, 0.35); }
.pill-sky { background: rgba(56, 189, 248, 0.15); color: #38BDF8; border: 1px solid rgba(56, 189, 248, 0.35); }
.pill-purple { background: rgba(168, 85, 247, 0.15); color: #C084FC; border: 1px solid rgba(168, 85, 247, 0.35); }

/* Secondary Benchmark Strip */
.benchmark-strip {
    background: rgba(15, 23, 42, 0.6);
    border: 1px solid var(--border-subtle);
    border-radius: 12px;
    padding: 12px 18px;
    display: flex;
    justify-content: space-around;
    align-items: center;
    margin-top: 14px;
    margin-bottom: 20px;
    flex-wrap: wrap;
    gap: 12px;
}
.benchmark-item {
    text-align: center;
}
.benchmark-title {
    color: #64748B;
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 2px;
}
.benchmark-val {
    color: #E2E8F0;
    font-size: 1.05rem;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
}

/* Activity Feed Card */
.feed-box {
    background: linear-gradient(145deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.85) 100%);
    border: 1px solid var(--border-subtle);
    border-radius: 16px;
    padding: 16px;
}
.feed-item {
    background: rgba(15, 23, 42, 0.65);
    border-radius: 10px;
    padding: 11px 14px;
    margin-bottom: 8px;
    border-left: 4px solid #38BDF8;
    border-top: 1px solid rgba(255, 255, 255, 0.03);
    border-right: 1px solid rgba(255, 255, 255, 0.03);
    border-bottom: 1px solid rgba(255, 255, 255, 0.03);
    transition: background 0.15s ease;
}
.feed-item:hover {
    background: rgba(30, 41, 59, 0.85);
}

/* Chart Canvas Card */
.chart-card {
    background: linear-gradient(145deg, rgba(30, 41, 59, 0.65) 0%, rgba(15, 23, 42, 0.85) 100%);
    border: 1px solid var(--border-subtle);
    border-radius: 16px;
    padding: 18px;
    box-shadow: 0 4px 18px rgba(0, 0, 0, 0.22);
}
</style>
"""
st.markdown(DESKTOP_CSS, unsafe_allow_html=True)

# ==============================================================================
# 🔒 PIN PROTECTION GATE
# ==============================================================================
def check_pin_auth():
    if st.session_state.get("authenticated", False):
        return True

    valid_pin = os.environ.get("DASHBOARD_PIN", "1123")
    if hasattr(st, "secrets") and "DASHBOARD_PIN" in st.secrets:
        valid_pin = str(st.secrets["DASHBOARD_PIN"])

    _, center_col, _ = st.columns([1, 1.1, 1])
    with center_col:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="text-align: center; padding: 36px 28px; border-radius: 20px; background: linear-gradient(145deg, #1E293B, #0F172A); border: 1px solid rgba(56, 189, 248, 0.25); box-shadow: 0 16px 36px rgba(0,0,0,0.55);">
            <div style="width: 68px; height: 68px; margin: 0 auto 16px auto; border-radius: 18px; background: linear-gradient(135deg, #0284C7, #0369A1); display: flex; align-items: center; justify-content: center; font-size: 2.2rem; box-shadow: 0 0 25px rgba(2, 132, 199, 0.4);">
                🩺
            </div>
            <h2 style="margin: 0; color: #F8FAFC; font-size: 1.6rem; font-weight: 800; letter-spacing: -0.02em;">Om Stan Health Protocol</h2>
            <p style="color: #94A3B8; font-size: 0.92rem; margin-top: 8px; margin-bottom: 24px;">
                Proteksi Akses Terpadu — Silakan masukkan PIN 4 digit untuk membuka dasbor.
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        with st.form("pin_login_form"):
            entered_pin = st.text_input("PIN Akses", type="password", max_chars=8, placeholder="Masukkan 4 digit PIN...", label_visibility="collapsed")
            submit_btn = st.form_submit_button("Buka Dasbor 🚀", width="stretch")
            
            if submit_btn:
                if entered_pin.strip() == str(valid_pin).strip():
                    st.session_state["authenticated"] = True
                    st.success("✅ Verifikasi berhasil. Memuat data...")
                    st.rerun()
                else:
                    st.error("❌ PIN salah. Silakan coba lagi.")

    return False

if not check_pin_auth():
    st.stop()

# ==============================================================================
# 🗄️ DATABASE CONNECTION & DATA ACCESS
# ==============================================================================
def get_connection():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url and hasattr(st, "secrets") and "DATABASE_URL" in st.secrets:
        db_url = st.secrets["DATABASE_URL"]

    if db_url:
        return psycopg2.connect(db_url)

    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "127.0.0.1"),
        port=int(os.environ.get("DB_PORT", 5432)),
        user=os.environ.get("DB_USER", "postgres"),
        password=os.environ.get("DB_PASSWORD", "PGpass#2026"),
        dbname=os.environ.get("DB_NAME", "kesehatan_db")
    )

@st.cache_data(ttl=5)
def load_data(table_name):
    try:
        conn = get_connection()
        df = pd.read_sql_query(f"SELECT * FROM {table_name} ORDER BY tanggal DESC, waktu DESC;", conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Gagal memuat data `{table_name}`: {e}")
        return pd.DataFrame()

# ==============================================================================
# 📋 SIDEBAR CONTROLS
# ==============================================================================
with st.sidebar:
    st.markdown("""
    <div style="padding: 12px 0 16px 0; border-bottom: 1px solid rgba(255,255,255,0.08); margin-bottom: 14px;">
        <div style="display: flex; align-items: center; gap: 10px;">
            <div style="font-size: 1.8rem;">🩺</div>
            <div>
                <h3 style="margin: 0; color: #F8FAFC; font-size: 1.15rem; font-weight: 700;">Om Stan</h3>
                <span style="color: #38BDF8; font-size: 0.78rem; font-weight: 600;">Protokol Glukosa &amp; Nutrisi</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.caption("🟢 **Status Sesi:** Terverifikasi")
    st.caption("☁️ **Cloud Database:** Neon PostgreSQL")
    
    st.markdown("---")
    st.markdown("##### ⏱️ Rentang Linimasa")
    filter_range = st.selectbox(
        "Pilih Periode Analisis",
        ["Semua Riwayat", "7 Hari Terakhir", "30 Hari Terakhir", "Hari Ini"],
        index=0,
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.markdown("##### ⚙️ Aksi Cepat")
    if st.button("🔄 Refresh Data", width="stretch"):
        st.cache_data.clear()
        st.rerun()

    if st.button("🔒 Kunci / Logout", width="stretch"):
        st.session_state["authenticated"] = False
        st.rerun()

# ==============================================================================
# 📊 LOAD DATASETS
# ==============================================================================
df_gds = load_data("gula_darah")
df_meds = load_data("obat_insulin")
df_food = load_data("makanan")
df_sport = load_data("olahraga")

today = date.today()

# Filter Data according to user selection
def filter_dataframe_by_date(df, date_col="tanggal"):
    if df.empty or date_col not in df.columns:
        return df
    try:
        temp = df.copy()
        temp[date_col] = pd.to_datetime(temp[date_col]).dt.date
        if filter_range == "Hari Ini":
            return temp[temp[date_col] == today]
        elif filter_range == "7 Hari Terakhir":
            return temp[temp[date_col] >= (today - timedelta(days=7))]
        elif filter_range == "30 Hari Terakhir":
            return temp[temp[date_col] >= (today - timedelta(days=30))]
        return df
    except Exception:
        return df

df_gds_filtered = filter_dataframe_by_date(df_gds)
df_meds_filtered = filter_dataframe_by_date(df_meds)
df_food_filtered = filter_dataframe_by_date(df_food)
df_sport_filtered = filter_dataframe_by_date(df_sport)

# ==============================================================================
# 🌟 DESKTOP EXECUTIVE HEADER
# ==============================================================================
st.markdown(f"""
<div class="desktop-header">
    <div class="profile-badge">
        <div class="avatar-circle">🩺</div>
        <div>
            <div style="display: flex; align-items: center; gap: 8px;">
                <h1 style="margin: 0; font-size: 1.6rem; font-weight: 800; color: #F8FAFC; letter-spacing: -0.02em;">
                    Health &amp; Lifestyle Executive Protocol
                </h1>
                <span class="status-pill pill-sky">Cloud Sync Active</span>
            </div>
            <p style="margin: 4px 0 0 0; color: #94A3B8; font-size: 0.88rem;">
                Monitoring Terpadu: Kurva Glukosa Darah, Injeksi Rapid, Asupan Nutrisi &amp; Kebugaran
            </p>
        </div>
    </div>
    <div style="text-align: right;">
        <span style="background: rgba(15, 23, 42, 0.8); color: #E2E8F0; border: 1px solid rgba(255, 255, 255, 0.1); padding: 7px 14px; border-radius: 9999px; font-size: 0.82rem; font-weight: 600; font-family: 'JetBrains Mono', monospace;">
            📅 {today.strftime("%A, %d %B %Y")}
        </span>
    </div>
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# 🎯 PRIMARY METRIC TILES (4 DESKTOP COLUMNS)
# ==============================================================================
c1, c2, c3, c4 = st.columns(4)

# 1. GDS Primary Card
with c1:
    if not df_gds.empty:
        latest_gds = int(df_gds.iloc[0]["nilai_mg_dl"])
        latest_tipe = str(df_gds.iloc[0]["tipe"])
        latest_time = str(df_gds.iloc[0]["waktu"])[:5]
        
        if latest_gds <= 140:
            pill_class, status_label = "pill-emerald", "✅ Zona Ideal"
        elif latest_gds <= 200:
            pill_class, status_label = "pill-amber", "⚠️ Perhatian"
        else:
            pill_class, status_label = "pill-rose", "🚨 Zona Waspada"

        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-header">
                <span class="metric-label">🩸 Gula Darah Terakhir</span>
                <span style="color: #64748B; font-size: 0.75rem; font-family: 'JetBrains Mono', monospace;">🕒 {latest_time}</span>
            </div>
            <div class="metric-number">{latest_gds}<span class="metric-unit">mg/dL</span></div>
            <div class="metric-footer">
                <span class="status-pill {pill_class}">{status_label}</span>
                <span style="color: #94A3B8; font-size: 0.76rem; font-weight: 500;">{latest_tipe}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-header"><span class="metric-label">🩸 Gula Darah Terakhir</span></div>
            <div class="metric-number">-<span class="metric-unit">mg/dL</span></div>
            <div class="metric-footer"><span class="status-pill pill-sky">Belum Ada Data</span></div>
        </div>
        """, unsafe_allow_html=True)

# 2. Insulin Primary Card
with c2:
    if not df_meds.empty:
        today_ins = df_meds[df_meds["kategori"] == "Insulin"]
        total_insulin = int(today_ins["dosis_jumlah"].sum()) if not today_ins.empty else 0
        freq_insulin = len(today_ins) if not today_ins.empty else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-header">
                <span class="metric-label">💉 Total Insulin Rapid</span>
                <span style="color: #38BDF8; font-size: 0.75rem; font-weight: 600;">{freq_insulin}x Injeksi</span>
            </div>
            <div class="metric-number">{total_insulin}<span class="metric-unit">Unit</span></div>
            <div class="metric-footer">
                <span class="status-pill pill-sky">Rapid Protocol</span>
                <span style="color: #94A3B8; font-size: 0.76rem;">Suntik pre/post meal</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-header"><span class="metric-label">💉 Total Insulin Rapid</span></div>
            <div class="metric-number">0<span class="metric-unit">Unit</span></div>
            <div class="metric-footer"><span class="status-pill pill-sky">0 Injeksi Hari Ini</span></div>
        </div>
        """, unsafe_allow_html=True)

# 3. Nutrition Primary Card
with c3:
    total_meals = len(df_food) if not df_food.empty else 0
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-header">
            <span class="metric-label">🍽️ Sesi Makan Terdata</span>
            <span style="color: #34D399; font-size: 0.75rem; font-weight: 600;">Aktif</span>
        </div>
        <div class="metric-number">{total_meals}<span class="metric-unit">Sesi</span></div>
        <div class="metric-footer">
            <span class="status-pill pill-emerald">Low Carb Target</span>
            <span style="color: #94A3B8; font-size: 0.76rem;">Serat &amp; Protein diutamakan</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 4. Target Body Weight & Metabolic Goal
with c4:
    total_sport_minutes = int(df_sport["durasi_menit"].sum()) if not df_sport.empty and "durasi_menit" in df_sport.columns else 0
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-header">
            <span class="metric-label">🎯 Target Berat Badan</span>
            <span style="color: #C084FC; font-size: 0.75rem; font-weight: 600;">Defisit Kalori</span>
        </div>
        <div class="metric-number">&lt; 90<span class="metric-unit">kg</span></div>
        <div class="metric-footer">
            <span class="status-pill pill-purple">Jalan Pagi: {total_sport_minutes} mnt</span>
            <span style="color: #94A3B8; font-size: 0.76rem;">Fokus Turun</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ==============================================================================
# 🩺 CLINICAL BENCHMARKS STRIP (Calculated Insights)
# ==============================================================================
if not df_gds.empty:
    avg_gds = round(float(df_gds["nilai_mg_dl"].mean()), 1)
    # Formula Estimasi HbA1c: (Avg Glucose + 46.7) / 28.7
    est_a1c = round((avg_gds + 46.7) / 28.7, 1)
    
    # Time in Range (70-140 mg/dL)
    tir_count = len(df_gds[(df_gds["nilai_mg_dl"] >= 70) & (df_gds["nilai_mg_dl"] <= 140)])
    tir_percentage = round((tir_count / len(df_gds)) * 100, 1)
    
    min_gds = int(df_gds["nilai_mg_dl"].min())
    max_gds = int(df_gds["nilai_mg_dl"].max())
else:
    avg_gds, est_a1c, tir_percentage, min_gds, max_gds = 0, 0, 0, 0, 0

st.markdown(f"""
<div class="benchmark-strip">
    <div class="benchmark-item">
        <div class="benchmark-title">Rata-Rata GDS</div>
        <div class="benchmark-val" style="color: #38BDF8;">{avg_gds} <small style="font-size: 0.7rem;">mg/dL</small></div>
    </div>
    <div style="height: 28px; width: 1px; background: rgba(255,255,255,0.08);"></div>
    <div class="benchmark-item">
        <div class="benchmark-title">Estimasi HbA1c</div>
        <div class="benchmark-val" style="color: #FBBF24;">{est_a1c}%</div>
    </div>
    <div style="height: 28px; width: 1px; background: rgba(255,255,255,0.08);"></div>
    <div class="benchmark-item">
        <div class="benchmark-title">Time In Range (70–140)</div>
        <div class="benchmark-val" style="color: #34D399;">{tir_percentage}%</div>
    </div>
    <div style="height: 28px; width: 1px; background: rgba(255,255,255,0.08);"></div>
    <div class="benchmark-item">
        <div class="benchmark-title">Fluktuasi GDS Terendah / Tertinggi</div>
        <div class="benchmark-val" style="color: #E2E8F0;">{min_gds} <span style="color: #64748B;">—</span> {max_gds} <small style="font-size: 0.7rem;">mg/dL</small></div>
    </div>
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# 🖥️ DESKTOP DUAL WORKSPACE (70% CHART / 30% STREAM)
# ==============================================================================
left_panel, right_panel = st.columns([7, 3])

# --- LEFT PANEL: TIMELINE CHART & DATA INSPECTOR ---
with left_panel:
    st.markdown("### 📈 Visualisasi Korelasi Glukosa, Insulin & Makanan")
    st.caption("Analisis sinkron terhadap kurva fluktuasi glukosa darah pasca asupan nutrisi dan injeksi insulin rapid.")

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Target Band Shapes (Green / Amber / Red)
    fig.add_hrect(
        y0=70, y1=140,
        fillcolor="#10B981", opacity=0.07, line_width=0,
        annotation_text="🟢 Zona Ideal (70–140 mg/dL)", annotation_position="top left",
        annotation_font=dict(color="#10B981", size=10),
        secondary_y=False
    )
    fig.add_hrect(
        y0=140, y1=200,
        fillcolor="#F59E0B", opacity=0.07, line_width=0,
        annotation_text="🟡 Zona Perhatian (140–200)", annotation_position="top left",
        annotation_font=dict(color="#F59E0B", size=10),
        secondary_y=False
    )
    fig.add_hrect(
        y0=200, y1=380,
        fillcolor="#EF4444", opacity=0.07, line_width=0,
        annotation_text="🔴 Zona Waspada (>200)", annotation_position="top left",
        annotation_font=dict(color="#EF4444", size=10),
        secondary_y=False
    )

    # 1. GDS Line (Axis Kiri)
    if not df_gds_filtered.empty:
        df_gds_sorted = df_gds_filtered.copy().sort_values(by=["tanggal", "waktu"])
        df_gds_sorted["timestamp"] = df_gds_sorted["tanggal"].astype(str) + " " + df_gds_sorted["waktu"].astype(str)
        fig.add_trace(
            go.Scatter(
                x=df_gds_sorted["timestamp"],
                y=df_gds_sorted["nilai_mg_dl"],
                mode="lines+markers+text",
                name="Gula Darah (mg/dL)",
                text=[f"<b>{int(v)}</b>" for v in df_gds_sorted["nilai_mg_dl"]],
                textposition="top center",
                line=dict(color="#F43F5E", width=3, shape="spline"),
                marker=dict(size=12, symbol="diamond", color="#F43F5E", line=dict(width=2, color="#FFFFFF")),
                hovertemplate="<b>Waktu:</b> %{x}<br><b>GDS:</b> %{y} mg/dL<extra></extra>"
            ),
            secondary_y=False
        )

    # 2. Insulin Bars (Axis Kanan)
    if not df_meds_filtered.empty:
        df_ins = df_meds_filtered[df_meds_filtered["kategori"] == "Insulin"].copy().sort_values(by=["tanggal", "waktu"])
        if not df_ins.empty:
            df_ins["timestamp"] = df_ins["tanggal"].astype(str) + " " + df_ins["waktu"].astype(str)
            fig.add_trace(
                go.Bar(
                    x=df_ins["timestamp"],
                    y=df_ins["dosis_jumlah"],
                    name="Insulin Rapid (Unit)",
                    text=[f"{int(d)} U" for d in df_ins["dosis_jumlah"]],
                    textposition="outside",
                    marker_color="#38BDF8",
                    opacity=0.85,
                    width=0.22,
                    hovertemplate="<b>Waktu:</b> %{x}<br><b>Dosis:</b> %{y} Unit<extra></extra>"
                ),
                secondary_y=True
            )

    # 3. Sesi Makan Pin Markers
    if not df_food_filtered.empty:
        df_food_sorted = df_food_filtered.copy().sort_values(by=["tanggal", "waktu"])
        df_food_sorted["timestamp"] = df_food_sorted["tanggal"].astype(str) + " " + df_food_sorted["waktu"].astype(str)
        fig.add_trace(
            go.Scatter(
                x=df_food_sorted["timestamp"],
                y=[115] * len(df_food_sorted),
                mode="markers+text",
                name="Sesi Makan",
                text=[f"🍽️ {m} ({p})" for m, p in zip(df_food_sorted["menu"], df_food_sorted["porsi"])],
                textposition="bottom center",
                marker=dict(size=15, color="#10B981", symbol="circle", line=dict(width=2, color="#FFFFFF")),
                hovertemplate="<b>Waktu:</b> %{x}<br><b>Menu:</b> %{text}<extra></extra>"
            ),
            secondary_y=False
        )

    # Desktop Chart Styling
    fig.update_layout(
        plot_bgcolor="rgba(15, 23, 42, 0.45)",
        paper_bgcolor="rgba(0, 0, 0, 0)",
        xaxis_title="Linimasa Kronologis",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color="#94A3B8", size=11)
        ),
        margin=dict(l=20, r=20, t=35, b=25),
        height=520,
        hovermode="x unified"
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(255, 255, 255, 0.05)", color="#94A3B8")
    fig.update_yaxes(
        title_text="Gula Darah (mg/dL)",
        range=[40, 320],
        showgrid=True,
        gridcolor="rgba(255, 255, 255, 0.05)",
        color="#F43F5E",
        secondary_y=False
    )
    fig.update_yaxes(
        title_text="Dosis Insulin Rapid (Unit)",
        range=[0, 45],
        showgrid=False,
        color="#38BDF8",
        secondary_y=True
    )

    st.plotly_chart(fig, width="stretch")

    # --- TABEL RIWAYAT LENGKAP (POSTGRESQL CLOUD) ---
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📋 Log Riwayat Data Lengkap")
    t_gds, t_meds, t_food, t_sport = st.tabs([
        f"🩸 Gula Darah ({len(df_gds)})",
        f"💊 Obat & Insulin ({len(df_meds)})",
        f"🍽️ Nutrisi & Makanan ({len(df_food)})",
        f"🏃 Latihan Olahraga ({len(df_sport)})"
    ])

    with t_gds:
        st.dataframe(df_gds, width="stretch")

    with t_meds:
        st.dataframe(df_meds, width="stretch")

    with t_food:
        st.dataframe(df_food, width="stretch")

    with t_sport:
        st.dataframe(df_sport, width="stretch")


# --- RIGHT PANEL: LIVE ACTIVITY FEED & QUICK ENTRY ---
with right_panel:
    st.markdown("### ⚡ Live Activity Feed")
    st.caption("Aktivitas klinis dan nutrisi terdata secara berurutan.")

    # Feed filter tabs
    filter_feed = st.radio(
        "Kategori Feed",
        ["Semua", "🩸 GDS", "💉 Insulin", "🍽️ Makan"],
        horizontal=True,
        label_visibility="collapsed"
    )

    events = []
    if filter_feed in ["Semua", "🩸 GDS"]:
        for _, r in df_gds.iterrows():
            events.append({
                "ts": f"{r['tanggal']} {str(r['waktu'])[:5]}",
                "color": "#F43F5E",
                "icon": "🩸",
                "title": f"GDS: <b>{r['nilai_mg_dl']} mg/dL</b>",
                "badge": r['tipe'],
                "note": r['catatan'] or "Pengukuran gula darah rutin"
            })
    if filter_feed in ["Semua", "💉 Insulin"]:
        for _, r in df_meds.iterrows():
            is_ins = r["kategori"] == "Insulin"
            events.append({
                "ts": f"{r['tanggal']} {str(r['waktu'])[:5]}",
                "color": "#38BDF8" if is_ins else "#C084FC",
                "icon": "💉" if is_ins else "💊",
                "title": f"{r['kategori']}: <b>{r['nama']}</b> ({int(r['dosis_jumlah'])} {r['satuan']})",
                "badge": "Insulin Rapid" if is_ins else r["kategori"],
                "note": r['catatan'] or ("Suntik dosis insulin" if is_ins else "Konsumsi obat/vitamin")
            })
    if filter_feed in ["Semua", "🍽️ Makan"]:
        for _, r in df_food.iterrows():
            events.append({
                "ts": f"{r['tanggal']} {str(r['waktu'])[:5]}",
                "color": "#10B981",
                "icon": "🍽️",
                "title": f"Makan: <b>{r['menu']}</b>",
                "badge": f"{r['porsi']}",
                "note": f"Est. {r['estimasi_kalori_kkal']} kkal • {r['catatan']}"
            })
    if filter_feed == "Semua":
        for _, r in df_sport.iterrows():
            events.append({
                "ts": f"{r['tanggal']} {str(r['waktu'])[:5]}",
                "color": "#F59E0B",
                "icon": "🏃",
                "title": f"Olahraga: <b>{r['jenis']}</b>",
                "badge": f"{r['durasi_menit']} mnt",
                "note": f"{r['jarak_km']} km • {r['catatan']}"
            })

    events_sorted = sorted(events, key=lambda x: str(x["ts"]), reverse=True)

    stream_container = st.container(height=480)
    with stream_container:
        if events_sorted:
            for ev in events_sorted[:16]:
                st.markdown(f"""
                <div class="feed-item" style="border-left-color: {ev['color']};">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 3px;">
                        <span style="color: #94A3B8; font-size: 0.76rem; font-family: 'JetBrains Mono', monospace;">🕒 {ev['ts']}</span>
                        <span style="font-size: 0.72rem; color: {ev['color']}; font-weight: 700; text-transform: uppercase;">{ev['badge']}</span>
                    </div>
                    <div style="color: #F8FAFC; font-size: 0.9rem; font-weight: 600;">{ev['icon']} {ev['title']}</div>
                    <div style="color: #64748B; font-size: 0.78rem; margin-top: 2px;">{ev['note']}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Belum ada data untuk kategori ini.")

    # --- QUICK DESKTOP INPUT DRAWER ---
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("➕ Entri Data Cepat (Input Manual)", expanded=False):
        in_tab1, in_tab2, in_tab3 = st.tabs(["🩸 GDS", "💉 Insulin", "🍽️ Makan"])

        with in_tab1:
            with st.form("quick_gds", clear_on_submit=True):
                q_tgl = st.date_input("Tanggal", today, key="q_gds_tgl")
                q_wkt = st.time_input("Waktu", datetime.now().time(), key="q_gds_wkt")
                q_tipe = st.selectbox("Tipe", ["GDP (Puasa)", "GDS (Sewaktu)", "2 Jam Setelah Makan", "Sebelum Tidur"], key="q_gds_tipe")
                q_val = st.number_input("Nilai (mg/dL)", min_value=20, max_value=800, value=120, key="q_gds_val")
                q_cat = st.text_input("Catatan", key="q_gds_cat")
                if st.form_submit_button("Simpan GDS", width="stretch"):
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute(
                        "INSERT INTO gula_darah (tanggal, waktu, tipe, nilai_mg_dl, catatan) VALUES (%s, %s, %s, %s, %s)",
                        (q_tgl, q_wkt.strftime("%H:%M"), q_tipe, q_val, q_cat)
                    )
                    conn.commit()
                    conn.close()
                    st.cache_data.clear()
                    st.success("✅ GDS tersimpan!")
                    st.rerun()

        with in_tab2:
            with st.form("quick_ins", clear_on_submit=True):
                qi_tgl = st.date_input("Tanggal", today, key="qi_tgl")
                qi_wkt = st.time_input("Waktu", datetime.now().time(), key="qi_wkt")
                qi_nama = st.text_input("Nama", value="Insulin Rapid", key="qi_nama")
                qi_dose = st.number_input("Dosis (Unit)", min_value=1.0, max_value=100.0, value=26.0, step=1.0, key="qi_dose")
                qi_cat = st.text_input("Catatan", key="qi_cat")
                if st.form_submit_button("Simpan Insulin", width="stretch"):
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute(
                        "INSERT INTO obat_insulin (tanggal, waktu, kategori, nama, dosis_jumlah, satuan, catatan) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                        (qi_tgl, qi_wkt.strftime("%H:%M"), "Insulin", qi_nama, qi_dose, "unit", qi_cat)
                    )
                    conn.commit()
                    conn.close()
                    st.cache_data.clear()
                    st.success("✅ Insulin tersimpan!")
                    st.rerun()

        with in_tab3:
            with st.form("quick_food", clear_on_submit=True):
                qf_tgl = st.date_input("Tanggal", today, key="qf_tgl")
                qf_wkt = st.time_input("Waktu", datetime.now().time(), key="qf_wkt")
                qf_menu = st.text_input("Menu", placeholder="e.g. Ayam Rebus, Nasi Merah", key="qf_menu")
                qf_por = st.text_input("Porsi", value="1 porsi", key="qf_por")
                qf_kal = st.text_input("Estimasi Kalori (kkal)", value="350", key="qf_kal")
                if st.form_submit_button("Simpan Makan", width="stretch"):
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute(
                        "INSERT INTO makanan (tanggal, waktu, menu, porsi, estimasi_kalori_kkal, catatan) VALUES (%s, %s, %s, %s, %s, %s)",
                        (qf_tgl, qf_wkt.strftime("%H:%M"), qf_menu, qf_por, qf_kal, "")
                    )
                    conn.commit()
                    conn.close()
                    st.cache_data.clear()
                    st.success("✅ Makanan tersimpan!")
                    st.rerun()
