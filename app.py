import os
from datetime import datetime, date, timedelta
import pandas as pd
import psycopg2
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

# ==========================================
# ⚙️ STREAMLIT CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Dashboard Kesehatan Om Stan",
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

# ==========================================
# 🎨 CUSTOM STYLING (UI/UX PRO MAX DESIGN)
# ==========================================
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Base theme tweaks */
.main .block-container {
    padding-top: 1.8rem;
    padding-bottom: 2.5rem;
    max-width: 1440px;
}

/* Glassmorphism Card Style */
.metric-card {
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.85) 100%);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px;
    padding: 18px 20px;
    box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.25);
    backdrop-filter: blur(8px);
    transition: transform 0.2s ease, border-color 0.2s ease;
    height: 100%;
}
.metric-card:hover {
    transform: translateY(-2px);
    border-color: rgba(56, 189, 248, 0.3);
}

.metric-title {
    color: #94A3B8;
    font-size: 0.82rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    display: flex;
    align-items: center;
    gap: 6px;
    margin-bottom: 8px;
}

.metric-value {
    color: #F8FAFC;
    font-size: 1.9rem;
    font-weight: 800;
    line-height: 1.1;
    letter-spacing: -0.02em;
}

.metric-unit {
    font-size: 0.95rem;
    font-weight: 500;
    color: #64748B;
    margin-left: 4px;
}

.metric-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 3px 10px;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    margin-top: 8px;
}
.badge-green { background: rgba(16, 185, 129, 0.15); color: #34D399; border: 1px solid rgba(16, 185, 129, 0.3); }
.badge-amber { background: rgba(245, 158, 11, 0.15); color: #FBBF24; border: 1px solid rgba(245, 158, 11, 0.3); }
.badge-red { background: rgba(239, 68, 68, 0.15); color: #F87171; border: 1px solid rgba(239, 68, 68, 0.3); }
.badge-blue { background: rgba(59, 130, 246, 0.15); color: #60A5FA; border: 1px solid rgba(59, 130, 246, 0.3); }
.badge-purple { background: rgba(168, 85, 247, 0.15); color: #C084FC; border: 1px solid rgba(168, 85, 247, 0.3); }

/* Activity Feed Stream Item */
.stream-item {
    padding: 12px 14px;
    border-radius: 10px;
    margin-bottom: 10px;
    background: rgba(30, 41, 59, 0.6);
    border-left: 4px solid #3B82F6;
    border-top: 1px solid rgba(255, 255, 255, 0.04);
    border-right: 1px solid rgba(255, 255, 255, 0.04);
    border-bottom: 1px solid rgba(255, 255, 255, 0.04);
    transition: background 0.15s ease;
}
.stream-item:hover {
    background: rgba(30, 41, 59, 0.85);
}
.stream-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 4px;
}
.stream-time {
    color: #94A3B8;
    font-size: 0.78rem;
    font-family: 'JetBrains Mono', monospace;
}
.stream-body {
    color: #E2E8F0;
    font-size: 0.92rem;
    font-weight: 500;
}
.stream-note {
    color: #64748B;
    font-size: 0.8rem;
    margin-top: 2px;
}

/* Subtle header banner */
.hero-container {
    background: linear-gradient(135deg, rgba(8, 145, 178, 0.15) 0%, rgba(30, 41, 59, 0.6) 100%);
    border: 1px solid rgba(56, 189, 248, 0.2);
    border-radius: 16px;
    padding: 22px 26px;
    margin-bottom: 22px;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ==========================================
# 🔒 PIN PROTECTION GATE
# ==========================================
def check_pin_auth():
    if st.session_state.get("authenticated", False):
        return True

    valid_pin = os.environ.get("DASHBOARD_PIN", "1123")
    if hasattr(st, "secrets") and "DASHBOARD_PIN" in st.secrets:
        valid_pin = str(st.secrets["DASHBOARD_PIN"])

    _, center_col, _ = st.columns([1, 1.2, 1])
    with center_col:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="text-align: center; padding: 32px 24px; border-radius: 18px; background: linear-gradient(145deg, #1E293B, #0F172A); border: 1px solid rgba(56, 189, 248, 0.25); box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
            <div style="font-size: 3.2rem; margin-bottom: 10px;">🩺</div>
            <h2 style="margin: 0; color: #F8FAFC; font-size: 1.55rem; font-weight: 700;">Dashboard Om Stan</h2>
            <p style="color: #94A3B8; font-size: 0.9rem; margin-top: 6px; margin-bottom: 20px;">
                Proteksi Medis &amp; Lifestyle — Masukkan PIN untuk membuka
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        with st.form("pin_login_form"):
            entered_pin = st.text_input("PIN Akses", type="password", max_chars=8, placeholder="Masukkan 4 digit PIN...", label_visibility="collapsed")
            submit_btn = st.form_submit_button("Buka Dashboard 🚀", width="stretch")
            
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

# ==========================================
# 🗄️ DATABASE CONNECTION & DATA ACCESS
# ==========================================
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

# ==========================================
# 📋 SIDEBAR & PROFILE CONTROL
# ==========================================
with st.sidebar:
    st.markdown("""
    <div style="padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.08); margin-bottom: 12px;">
        <h3 style="margin: 0; color: #F8FAFC; display: flex; align-items: center; gap: 8px;">
            <span>🩺</span> Om Stan Profile
        </h3>
        <p style="color: #94A3B8; font-size: 0.8rem; margin: 4px 0 0 0;">Protokol Diabetes &amp; Nutrisi</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.caption("🟢 **Status:** Sesi Terverifikasi")
    st.caption("☁️ **Database:** Neon PostgreSQL Cloud")
    
    st.markdown("---")
    st.markdown("#### 🎯 Filter Linimasa")
    filter_range = st.selectbox(
        "Rentang Waktu Tampilan",
        ["Semua Riwayat", "7 Hari Terakhir", "30 Hari Terakhir", "Hari Ini"],
        index=0
    )

    st.markdown("---")
    if st.button("🔄 Segarkan Data (Refresh)", width="stretch"):
        st.cache_data.clear()
        st.rerun()

    if st.button("🔒 Kunci / Logout", width="stretch"):
        st.session_state["authenticated"] = False
        st.rerun()

# ==========================================
# 📊 LOAD & PREPARE DATASETS
# ==========================================
df_gds = load_data("gula_darah")
df_meds = load_data("obat_insulin")
df_food = load_data("makanan")
df_sport = load_data("olahraga")

today = date.today()

# Filter by selected time range
def apply_time_filter(df, date_col="tanggal"):
    if df.empty or date_col not in df.columns:
        return df
    try:
        temp_df = df.copy()
        temp_df[date_col] = pd.to_datetime(temp_df[date_col]).dt.date
        if filter_range == "Hari Ini":
            return temp_df[temp_df[date_col] == today]
        elif filter_range == "7 Hari Terakhir":
            return temp_df[temp_df[date_col] >= (today - timedelta(days=7))]
        elif filter_range == "30 Hari Terakhir":
            return temp_df[temp_df[date_col] >= (today - timedelta(days=30))]
        return df
    except Exception:
        return df

df_gds_filtered = apply_time_filter(df_gds)
df_meds_filtered = apply_time_filter(df_meds)
df_food_filtered = apply_time_filter(df_food)
df_sport_filtered = apply_time_filter(df_sport)

# ==========================================
# 🌟 HERO HEADER
# ==========================================
st.markdown(f"""
<div class="hero-container">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
        <div>
            <h1 style="color: #F8FAFC; margin: 0; font-size: 1.85rem; font-weight: 800; letter-spacing: -0.02em;">
                Health &amp; Lifestyle Protocol
            </h1>
            <p style="color: #94A3B8; margin: 4px 0 0 0; font-size: 0.95rem;">
                Monitoring Terpadu: Gula Darah, Insulin Rapid, Nutrisi, &amp; Olahraga
            </p>
        </div>
        <div style="text-align: right;">
            <span style="background: rgba(8, 145, 178, 0.2); color: #38BDF8; border: 1px solid rgba(56, 189, 248, 0.4); padding: 5px 12px; border-radius: 20px; font-size: 0.82rem; font-weight: 600;">
                📅 {today.strftime("%A, %d %B %Y")}
            </span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 📈 KEY PERFORMANCE METRIC CARDS
# ==========================================
m1, m2, m3, m4 = st.columns(4)

# 1. GDS Card
with m1:
    if not df_gds.empty:
        latest_gds = int(df_gds.iloc[0]["nilai_mg_dl"])
        latest_tipe = str(df_gds.iloc[0]["tipe"])
        if latest_gds <= 140:
            badge_class = "badge-green"
            status_text = "✅ Ideal (70-140)"
        elif latest_gds <= 200:
            badge_class = "badge-amber"
            status_text = "⚠️ Perhatian (140-200)"
        else:
            badge_class = "badge-red"
            status_text = "🚨 Waspada (>200)"
            
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">🩸 Gula Darah Terakhir</div>
            <div class="metric-value">{latest_gds}<span class="metric-unit">mg/dL</span></div>
            <div>
                <span class="metric-badge {badge_class}">{status_text}</span>
                <span style="color: #94A3B8; font-size: 0.75rem; margin-left: 6px;">({latest_tipe})</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-title">🩸 Gula Darah Terakhir</div>
            <div class="metric-value">-<span class="metric-unit">mg/dL</span></div>
            <span class="metric-badge badge-blue">Belum ada data</span>
        </div>
        """, unsafe_allow_html=True)

# 2. Insulin Card
with m2:
    if not df_meds.empty:
        today_meds = df_meds[(df_meds["kategori"] == "Insulin")]
        total_insulin = int(today_meds["dosis_jumlah"].sum()) if not today_meds.empty else 0
        insulin_counts = len(today_meds) if not today_meds.empty else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">💉 Insulin Rapid Hari Ini</div>
            <div class="metric-value">{total_insulin}<span class="metric-unit">Unit</span></div>
            <div>
                <span class="metric-badge badge-blue">{insulin_counts}x Injeksi Terdata</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-title">💉 Insulin Rapid Hari Ini</div>
            <div class="metric-value">0<span class="metric-unit">Unit</span></div>
            <span class="metric-badge badge-blue">Belum ada dosis</span>
        </div>
        """, unsafe_allow_html=True)

# 3. Makanan Card
with m3:
    total_makan = len(df_food) if not df_food.empty else 0
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">🍽️ Sesi Makan Terdata</div>
        <div class="metric-value">{total_makan}<span class="metric-unit">Sesi</span></div>
        <div>
            <span class="metric-badge badge-green">Protokol Rendah Gula</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 4. Target Berat Badan
with m4:
    st.markdown("""
    <div class="metric-card">
        <div class="metric-title">🎯 Target Berat Badan</div>
        <div class="metric-value">&lt; 90<span class="metric-unit">kg</span></div>
        <div>
            <span class="metric-badge badge-purple">Defisit &amp; Jalan Pagi</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# 📊 INTERACTIVE DUAL-AXIS TIMELINE & STREAM
# ==========================================
col_chart, col_stream = st.columns([7, 3])

with col_chart:
    st.markdown("### 📈 Timeline Korelasi (GDS, Insulin & Makanan)")
    st.caption("Visualisasi sinkron interaksi kurva glukosa dengan waktu makan dan suntik insulin rapid.")

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Target zones
    fig.add_hrect(
        y0=70, y1=140,
        fillcolor="#10B981", opacity=0.08, line_width=0,
        annotation_text="🟢 Zona Ideal (70-140)", annotation_position="top left",
        annotation_font=dict(color="#10B981", size=10),
        secondary_y=False
    )
    fig.add_hrect(
        y0=140, y1=200,
        fillcolor="#F59E0B", opacity=0.08, line_width=0,
        annotation_text="🟡 Zona Perhatian (140-200)", annotation_position="top left",
        annotation_font=dict(color="#F59E0B", size=10),
        secondary_y=False
    )
    fig.add_hrect(
        y0=200, y1=380,
        fillcolor="#EF4444", opacity=0.08, line_width=0,
        annotation_text="🔴 Zona Waspada (>200)", annotation_position="top left",
        annotation_font=dict(color="#EF4444", size=10),
        secondary_y=False
    )

    # 1. GDS Curve (Left Axis)
    if not df_gds_filtered.empty:
        df_gds_sorted = df_gds_filtered.copy().sort_values(by=["tanggal", "waktu"])
        df_gds_sorted["timestamp"] = df_gds_sorted["tanggal"].astype(str) + " " + df_gds_sorted["waktu"].astype(str)
        fig.add_trace(
            go.Scatter(
                x=df_gds_sorted["timestamp"],
                y=df_gds_sorted["nilai_mg_dl"],
                mode="lines+markers+text",
                name="Gula Darah (mg/dL)",
                text=[f"<b>{v}</b>" for v in df_gds_sorted["nilai_mg_dl"]],
                textposition="top center",
                line=dict(color="#EF4444", width=3, shape="spline"),
                marker=dict(size=11, symbol="diamond", color="#EF4444", line=dict(width=2, color="#FFFFFF")),
                hovertemplate="<b>Waktu:</b> %{x}<br><b>GDS:</b> %{y} mg/dL<extra></extra>"
            ),
            secondary_y=False
        )

    # 2. Insulin Bar (Right Axis)
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
                    width=0.25,
                    hovertemplate="<b>Waktu:</b> %{x}<br><b>Dosis:</b> %{y} Unit<extra></extra>"
                ),
                secondary_y=True
            )

    # 3. Pin Marker Makanan
    if not df_food_filtered.empty:
        df_food_sorted = df_food_filtered.copy().sort_values(by=["tanggal", "waktu"])
        df_food_sorted["timestamp"] = df_food_sorted["tanggal"].astype(str) + " " + df_food_sorted["waktu"].astype(str)
        fig.add_trace(
            go.Scatter(
                x=df_food_sorted["timestamp"],
                y=[110] * len(df_food_sorted),
                mode="markers+text",
                name="Sesi Makan",
                text=[f"🍽️ {m} ({p})" for m, p in zip(df_food_sorted["menu"], df_food_sorted["porsi"])],
                textposition="bottom center",
                marker=dict(size=14, color="#10B981", symbol="circle", line=dict(width=2, color="#FFFFFF")),
                hovertemplate="<b>Waktu:</b> %{x}<br><b>Menu:</b> %{text}<extra></extra>"
            ),
            secondary_y=False
        )

    # Layout styling with Dark Slate Palette
    fig.update_layout(
        plot_bgcolor="rgba(15, 23, 42, 0.4)",
        paper_bgcolor="rgba(0, 0, 0, 0)",
        xaxis_title="Linimasa Waktu",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color="#94A3B8", size=11)
        ),
        margin=dict(l=20, r=20, t=35, b=30),
        height=510,
        hovermode="x unified"
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(255, 255, 255, 0.05)", color="#94A3B8")
    fig.update_yaxes(
        title_text="Gula Darah (mg/dL)",
        range=[40, 320],
        showgrid=True,
        gridcolor="rgba(255, 255, 255, 0.05)",
        color="#EF4444",
        secondary_y=False
    )
    fig.update_yaxes(
        title_text="Dosis Insulin (Unit)",
        range=[0, 45],
        showgrid=False,
        color="#38BDF8",
        secondary_y=True
    )

    st.plotly_chart(fig, width="stretch")

with col_stream:
    st.markdown("### ⚡ Live Activity Stream")
    st.caption("Aktivitas klinis & nutrisi terdata terkini.")

    events = []
    for _, r in df_gds.iterrows():
        events.append({
            "ts": f"{r['tanggal']} {r['waktu']}",
            "color": "#EF4444",
            "icon": "🩸",
            "title": f"GDS: <b>{r['nilai_mg_dl']} mg/dL</b>",
            "badge": r['tipe'],
            "note": r['catatan'] or "Pengukuran gula darah"
        })
    for _, r in df_meds.iterrows():
        is_ins = r["kategori"] == "Insulin"
        events.append({
            "ts": f"{r['tanggal']} {r['waktu']}",
            "color": "#38BDF8" if is_ins else "#C084FC",
            "icon": "💉" if is_ins else "💊",
            "title": f"{r['kategori']}: <b>{r['nama']}</b> ({int(r['dosis_jumlah'])} {r['satuan']})",
            "badge": "Insulin Rapid" if is_ins else r["kategori"],
            "note": r['catatan'] or ("Injeksi dosis" if is_ins else "Konsumsi obat/vitamin")
        })
    for _, r in df_food.iterrows():
        events.append({
            "ts": f"{r['tanggal']} {r['waktu']}",
            "color": "#10B981",
            "icon": "🍽️",
            "title": f"Makan: <b>{r['menu']}</b>",
            "badge": f"{r['porsi']}",
            "note": f"Est. {r['estimasi_kalori_kkal']} kkal • {r['catatan']}"
        })
    for _, r in df_sport.iterrows():
        events.append({
            "ts": f"{r['tanggal']} {r['waktu']}",
            "color": "#F59E0B",
            "icon": "🏃",
            "title": f"Olahraga: <b>{r['jenis']}</b>",
            "badge": f"{r['durasi_menit']} mnt",
            "note": f"{r['jarak_km']} km • {r['catatan']}"
        })

    events_sorted = sorted(events, key=lambda x: str(x["ts"]), reverse=True)

    stream_container = st.container(height=490)
    with stream_container:
        if events_sorted:
            for ev in events_sorted[:15]:
                st.markdown(f"""
                <div class="stream-item" style="border-left-color: {ev['color']};">
                    <div class="stream-header">
                        <span class="stream-time">🕒 {ev['ts']}</span>
                        <span style="font-size: 0.75rem; color: {ev['color']}; font-weight: 600;">{ev['badge']}</span>
                    </div>
                    <div class="stream-body">{ev['icon']} {ev['title']}</div>
                    <div class="stream-note">{ev['note']}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Belum ada linimasa aktivitas.")

# ==========================================
# 🛠️ INPUT MANUAL CADANGAN
# ==========================================
st.markdown("---")
with st.expander("📝 Formulir Entri Data Cepat (Neon PostgreSQL)", expanded=False):
    st.caption("Input langsung ke database cloud jika tidak melalui bot Telegram.")
    tab_gds, tab_meds, tab_food, tab_sport = st.tabs(["🩸 Gula Darah", "💊 Obat / Insulin", "🍽️ Makanan", "🏃 Olahraga"])

    # 1. GDS Form
    with tab_gds:
        with st.form("form_add_gds", clear_on_submit=True):
            cg1, cg2, cg3 = st.columns(3)
            with cg1:
                f_tgl = st.date_input("Tanggal", today, key="in_gds_tgl")
            with cg2:
                f_wkt = st.time_input("Waktu", datetime.now().time(), key="in_gds_wkt")
            with cg3:
                f_tipe = st.selectbox("Tipe Pengukuran", ["GDP (Puasa)", "GDS (Sewaktu)", "2 Jam Setelah Makan", "Sebelum Tidur"])
            
            cg4, cg5 = st.columns([1, 2])
            with cg4:
                f_nilai = st.number_input("Nilai GDS (mg/dL)", min_value=20, max_value=800, value=120)
            with cg5:
                f_cat = st.text_input("Catatan", placeholder="Kondisi fisik, keluhan, dll.")

            if st.form_submit_button("Simpan Data Gula Darah 💾", width="stretch"):
                try:
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute(
                        "INSERT INTO gula_darah (tanggal, waktu, tipe, nilai_mg_dl, catatan) VALUES (%s, %s, %s, %s, %s)",
                        (f_tgl, f_wkt.strftime("%H:%M"), f_tipe, f_nilai, f_cat)
                    )
                    conn.commit()
                    conn.close()
                    st.cache_data.clear()
                    st.success("✅ Data GDS berhasil disimpan ke Neon Cloud!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Gagal menyimpan: {e}")

    # 2. Meds Form
    with tab_meds:
        with st.form("form_add_meds", clear_on_submit=True):
            cm1, cm2, cm3 = st.columns(3)
            with cm1:
                fm_tgl = st.date_input("Tanggal", today, key="in_meds_tgl")
            with cm2:
                fm_wkt = st.time_input("Waktu", datetime.now().time(), key="in_meds_wkt")
            with cm3:
                fm_kat = st.selectbox("Kategori", ["Insulin", "Obat", "Vitamin"])
            
            cm4, cm5, cm6 = st.columns(3)
            with cm4:
                fm_nama = st.text_input("Nama Obat / Insulin", value="Insulin Rapid")
            with cm5:
                fm_dosis = st.number_input("Dosis", min_value=0.5, max_value=250.0, value=26.0, step=1.0)
            with cm6:
                fm_satuan = st.selectbox("Satuan", ["unit", "tablet", "kapsul"])
            
            fm_cat = st.text_input("Catatan Obat", placeholder="Sebelum makan / sesudah makan")

            if st.form_submit_button("Simpan Data Obat / Insulin 💾", width="stretch"):
                try:
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute(
                        "INSERT INTO obat_insulin (tanggal, waktu, kategori, nama, dosis_jumlah, satuan, catatan) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                        (fm_tgl, fm_wkt.strftime("%H:%M"), fm_kat, fm_nama, fm_dosis, fm_satuan, fm_cat)
                    )
                    conn.commit()
                    conn.close()
                    st.cache_data.clear()
                    st.success("✅ Data Obat/Insulin tersimpan!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Gagal menyimpan: {e}")

    # 3. Food Form
    with tab_food:
        with st.form("form_add_food", clear_on_submit=True):
            cf1, cf2 = st.columns(2)
            with cf1:
                ff_tgl = st.date_input("Tanggal", today, key="in_food_tgl")
                ff_menu = st.text_input("Menu Makanan", placeholder="Contoh: Dada Ayam Panggang, Nasi Merah")
            with cf2:
                ff_wkt = st.time_input("Waktu", datetime.now().time(), key="in_food_wkt")
                ff_porsi = st.text_input("Porsi", value="1 porsi")
            
            cf3, cf4 = st.columns(2)
            with cf3:
                ff_kal = st.text_input("Estimasi Kalori (kkal)", value="350")
            with cf4:
                ff_cat = st.text_input("Catatan Makanan", placeholder="Rendah garam, tanpa gula")

            if st.form_submit_button("Simpan Data Makanan 💾", width="stretch"):
                try:
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute(
                        "INSERT INTO makanan (tanggal, waktu, menu, porsi, estimasi_kalori_kkal, catatan) VALUES (%s, %s, %s, %s, %s, %s)",
                        (ff_tgl, ff_wkt.strftime("%H:%M"), ff_menu, ff_porsi, ff_kal, ff_cat)
                    )
                    conn.commit()
                    conn.close()
                    st.cache_data.clear()
                    st.success("✅ Data Nutrisi tersimpan!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Gagal menyimpan: {e}")

    # 4. Sport Form
    with tab_sport:
        with st.form("form_add_sport", clear_on_submit=True):
            cs1, cs2 = st.columns(2)
            with cs1:
                fs_tgl = st.date_input("Tanggal", today, key="in_sport_tgl")
                fs_jenis = st.text_input("Jenis Latihan", value="Jalan Santai Pagi")
            with cs2:
                fs_wkt = st.time_input("Waktu", datetime.now().time(), key="in_sport_wkt")
                fs_durasi = st.number_input("Durasi (Menit)", min_value=1, max_value=360, value=30)

            cs3, cs4 = st.columns(2)
            with cs3:
                fs_jarak = st.number_input("Jarak Tempuh (km)", min_value=0.0, max_value=50.0, value=2.0, step=0.1)
            with cs4:
                fs_cat = st.text_input("Catatan Latihan", placeholder="Kondisi detak jantung, rute")

            if st.form_submit_button("Simpan Data Olahraga 💾", width="stretch"):
                try:
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute(
                        "INSERT INTO olahraga (tanggal, waktu, jenis, durasi_menit, jarak_km, catatan) VALUES (%s, %s, %s, %s, %s, %s)",
                        (fs_tgl, fs_wkt.strftime("%H:%M"), fs_jenis, fs_durasi, fs_jarak, fs_cat)
                    )
                    conn.commit()
                    conn.close()
                    st.cache_data.clear()
                    st.success("✅ Data Olahraga tersimpan!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Gagal menyimpan: {e}")

# ==========================================
# 📋 HISTORICAL DATA TABLES
# ==========================================
st.markdown("---")
st.markdown("### 📋 Log Riwayat Lengkap (Neon PostgreSQL Cloud)")
tab_dt_gds, tab_dt_meds, tab_dt_food, tab_dt_sport = st.tabs([
    f"Log Gula Darah ({len(df_gds)})",
    f"Log Obat & Insulin ({len(df_meds)})",
    f"Log Makanan ({len(df_food)})",
    f"Log Olahraga ({len(df_sport)})"
])

with tab_dt_gds:
    st.dataframe(df_gds, width="stretch")

with tab_dt_meds:
    st.dataframe(df_meds, width="stretch")

with tab_dt_food:
    st.dataframe(df_food, width="stretch")

with tab_dt_sport:
    st.dataframe(df_sport, width="stretch")
