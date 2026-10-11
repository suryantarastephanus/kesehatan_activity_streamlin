import os
import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, date

st.set_page_config(page_title="Dashboard Kesehatan Om Stan", layout="wide", page_icon="🩺")

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
        <div style="text-align: center; padding: 25px 20px; border-radius: 12px; background: #1E293B; border: 1px solid #334155; box-shadow: 0 4px 20px rgba(0,0,0,0.3);">
            <div style="font-size: 3.5rem; margin-bottom: 5px;">🔒</div>
            <h2 style="margin: 0; color: #F8FAFC; font-size: 1.5rem;">Dashboard Terproteksi</h2>
            <p style="color: #94A3B8; font-size: 0.9rem; margin-top: 6px;">Masukkan PIN untuk membuka Dashboard Kesehatan Om Stan</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        with st.form("pin_login_form"):
            entered_pin = st.text_input("PIN Akses", type="password", max_chars=6, placeholder="••••", label_visibility="collapsed")
            submit_btn = st.form_submit_button("Masuk ke Dashboard 🚀", width="stretch")
            
            if submit_btn:
                if entered_pin.strip() == str(valid_pin).strip():
                    st.session_state["authenticated"] = True
                    st.success("✅ PIN Benar. Membuka dashboard...")
                    st.rerun()
                else:
                    st.error("❌ PIN salah! Silakan coba lagi.")

    return False

if not check_pin_auth():
    st.stop()

# Sidebar: Akun & Keamanan
with st.sidebar:
    st.markdown("### 🩺 Om Stan")
    st.caption("Status: **Terverifikasi** 🟢")
    st.caption("Database: **Neon Cloud PostgreSQL** ☁️")
    st.divider()
    if st.button("🔒 Kunci / Logout", width="stretch"):
        st.session_state["authenticated"] = False
        st.rerun()

# DB Connection (Prioritaskan Neon Cloud / DATABASE_URL)
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

st.title("🩺 Health & Lifestyle Dashboard — Om Stan")
st.caption("Monitoring Gula Darah, Insulin, Makanan, & Obat Terintegrasi PostgreSQL")

# Load data
df_gds = load_data("gula_darah")
df_meds = load_data("obat_insulin")
df_food = load_data("makanan")
df_sport = load_data("olahraga")

today = date.today()

# Metric summary
col1, col2, col3, col4 = st.columns(4)

with col1:
    if not df_gds.empty:
        latest_gds = df_gds.iloc[0]["nilai_mg_dl"]
        st.metric("Gula Darah Terakhir", f"{latest_gds} mg/dL", delta=f"{df_gds.iloc[0]['tipe']}")
    else:
        st.metric("Gula Darah Terakhir", "-")

with col2:
    if not df_meds.empty:
        today_meds = df_meds[df_meds["kategori"] == "Insulin"]
        total_insulin = today_meds["dosis_jumlah"].sum() if not today_meds.empty else 0
        st.metric("Total Insulin Hari Ini", f"{total_insulin} Unit", delta="Rapid")
    else:
        st.metric("Total Insulin Hari Ini", "0 Unit")

with col3:
    total_makan_hari_ini = len(df_food) if not df_food.empty else 0
    st.metric("Sesi Makan Terdata", f"{total_makan_hari_ini} Kali")

with col4:
    st.metric("Target Berat Badan", "< 90 kg", delta="Fokus Turun")

st.divider()

# Layout: Grafik & Form Input
c_left, c_right = st.columns([7, 3])

with c_left:
    st.subheader("📈 Timeline Interaktif (Korelasi GDS, Insulin & Makanan)")
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Range warna latar belakang (Zona Target GDS)
    fig.add_hrect(y0=70, y1=140, fillcolor="#10B981", opacity=0.08, line_width=0, annotation_text="Zona Ideal (70-140 mg/dL)", annotation_position="top left", secondary_y=False)
    fig.add_hrect(y0=140, y1=200, fillcolor="#F59E0B", opacity=0.08, line_width=0, annotation_text="Zona Perhatian (140-200)", annotation_position="top left", secondary_y=False)
    fig.add_hrect(y0=200, y1=350, fillcolor="#EF4444", opacity=0.08, line_width=0, annotation_text="Zona Waspada (>200)", annotation_position="top left", secondary_y=False)

    # 1. Curve Gula Darah (Sumbu Y Kiri)
    if not df_gds.empty:
        df_gds_chart = df_gds.copy().sort_values(by=["tanggal", "waktu"])
        df_gds_chart["ts"] = df_gds_chart["tanggal"].astype(str) + " " + df_gds_chart["waktu"].astype(str)
        fig.add_trace(
            go.Scatter(
                x=df_gds_chart["ts"],
                y=df_gds_chart["nilai_mg_dl"],
                mode="lines+markers+text",
                name="Gula Darah (mg/dL)",
                text=[f"<b>{v}</b>" for v in df_gds_chart["nilai_mg_dl"]],
                textposition="top center",
                line=dict(color="#EF4444", width=3, shape="spline"),
                marker=dict(size=12, symbol="diamond", color="#EF4444", line=dict(width=2, color="white")),
                hovertemplate="<b>Waktu:</b> %{x}<br><b>GDS:</b> %{y} mg/dL<extra></extra>"
            ),
            secondary_y=False
        )

    # 2. Bar Insulin Rapid (Sumbu Y Kanan)
    if not df_meds.empty:
        df_ins = df_meds[df_meds["kategori"] == "Insulin"].copy().sort_values(by=["tanggal", "waktu"])
        if not df_ins.empty:
            df_ins["ts"] = df_ins["tanggal"].astype(str) + " " + df_ins["waktu"].astype(str)
            fig.add_trace(
                go.Bar(
                    x=df_ins["ts"],
                    y=df_ins["dosis_jumlah"],
                    name="Suntik Insulin Rapid (Unit)",
                    text=[f"{int(d)} U" for d in df_ins["dosis_jumlah"]],
                    textposition="outside",
                    marker_color="#3B82F6",
                    opacity=0.7,
                    width=0.2,
                    hovertemplate="<b>Waktu:</b> %{x}<br><b>Insulin:</b> %{y} Unit<extra></extra>"
                ),
                secondary_y=True
            )

    # 3. Pin Marker Makanan
    if not df_food.empty:
        df_food_chart = df_food.copy().sort_values(by=["tanggal", "waktu"])
        df_food_chart["ts"] = df_food_chart["tanggal"].astype(str) + " " + df_food_chart["waktu"].astype(str)
        fig.add_trace(
            go.Scatter(
                x=df_food_chart["ts"],
                y=[100] * len(df_food_chart),
                mode="markers+text",
                name="Sesi Makan",
                text=[f"🍽️ {m} ({p})" for m, p in zip(df_food_chart["menu"], df_food_chart["porsi"])],
                textposition="bottom center",
                marker=dict(size=16, color="#10B981", symbol="circle", line=dict(width=2, color="white")),
                hovertemplate="<b>Waktu:</b> %{x}<br><b>Menu:</b> %{text}<extra></extra>"
            ),
            secondary_y=False
        )

    # Layout styling
    fig.update_layout(
        xaxis_title="Waktu (Tanggal & Jam)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=30, b=20),
        height=520,
        hovermode="x unified"
    )
    fig.update_yaxes(title_text="Gula Darah (mg/dL)", range=[40, 320], secondary_y=False)
    fig.update_yaxes(title_text="Dosis Insulin (Unit)", range=[0, 45], secondary_y=True)

    st.plotly_chart(fig, width="stretch")

with c_right:
    st.subheader("⚡ Live Activity Stream")
    st.caption("Auto-sync dari Telegram & Database")

    events = []
    for _, r in df_gds.iterrows():
        events.append({
            "ts": f"{r['tanggal']} {r['waktu']}",
            "type": "gds",
            "desc": f"🩸 GDS: <b>{r['nilai_mg_dl']} mg/dL</b> ({r['tipe']})",
            "note": r["catatan"]
        })
    for _, r in df_meds.iterrows():
        if r["kategori"] == "Insulin":
            events.append({
                "ts": f"{r['tanggal']} {r['waktu']}",
                "type": "insulin",
                "desc": f"💉 Suntik: <b>{int(r['dosis_jumlah'])} Unit</b> {r['nama']}",
                "note": r["catatan"]
            })
        else:
            events.append({
                "ts": f"{r['tanggal']} {r['waktu']}",
                "type": "med",
                "desc": f"💊 {r['kategori']}: <b>{r['nama']}</b> ({int(r['dosis_jumlah'])} {r['satuan']})",
                "note": r["catatan"]
            })
    for _, r in df_food.iterrows():
        events.append({
            "ts": f"{r['tanggal']} {r['waktu']}",
            "type": "food",
            "desc": f"🍽️ Makan: <b>{r['menu']}</b> ({r['porsi']})",
            "note": f"Est. {r['estimasi_kalori_kkal']} kkal"
        })

    events_sorted = sorted(events, key=lambda x: x["ts"], reverse=True)

    for ev in events_sorted[:12]:
        waktu_str = str(ev["ts"])
        st.markdown(f"""
        <div style="padding: 10px 14px; border-radius: 8px; margin-bottom: 8px; background: #1E293B; border-left: 4px solid #3B82F6; font-size: 0.95rem;">
            <span style="color: #94A3B8; font-size: 0.8rem;">🕒 {waktu_str}</span><br>
            <span>{ev['desc']}</span><br>
            <small style="color: #64748B;">{ev['note']}</small>
        </div>
        """, unsafe_allow_html=True)

st.divider()

with st.expander("🛠️ Input Manual Cadangan (Bila tidak via Telegram)"):
    tab_f1, tab_f2, tab_f3, tab_f4 = st.tabs(["Gula Darah", "Insulin/Obat", "Makanan", "Olahraga"])

    with tab_f1:
        with st.form("form_gds", clear_on_submit=True):
            f_tgl = st.date_input("Tanggal", today, key="gds_tgl")
            f_wkt = st.time_input("Waktu", datetime.now().time(), key="gds_wkt")
            f_tipe = st.selectbox("Tipe", ["GDS (Sewaktu)", "GDP (Puasa)", "2 Jam Setelah Makan", "Sebelum Tidur"])
            f_nilai = st.number_input("Nilai Gula Darah (mg/dL)", min_value=20, max_value=800, value=120)
            f_catatan = st.text_input("Catatan Tambahan")
            if st.form_submit_button("Simpan Gula Darah"):
                conn = get_connection()
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO gula_darah (tanggal, waktu, tipe, nilai_mg_dl, catatan) VALUES (%s, %s, %s, %s, %s)",
                    (f_tgl, f_wkt.strftime("%H:%M"), f_tipe, f_nilai, f_catatan)
                )
                conn.commit()
                conn.close()
                st.success("Data GDS berhasil disimpan!")
                st.rerun()

    with tab_f2:
        with st.form("form_meds", clear_on_submit=True):
            f_tgl = st.date_input("Tanggal", today, key="meds_tgl")
            f_wkt = st.time_input("Waktu", datetime.now().time(), key="meds_wkt")
            f_kat = st.selectbox("Kategori", ["Insulin", "Obat", "Vitamin"])
            f_nama = st.text_input("Nama Obat / Insulin", value="Insulin Rapid")
            f_dosis = st.number_input("Dosis / Jumlah", min_value=0.5, max_value=200.0, value=26.0, step=1.0)
            f_satuan = st.selectbox("Satuan", ["unit", "tablet", "kapsul"])
            f_cat = st.text_input("Catatan")
            if st.form_submit_button("Simpan Obat/Insulin"):
                conn = get_connection()
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO obat_insulin (tanggal, waktu, kategori, nama, dosis_jumlah, satuan, catatan) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (f_tgl, f_wkt.strftime("%H:%M"), f_kat, f_nama, f_dosis, f_satuan, f_cat)
                )
                conn.commit()
                conn.close()
                st.success("Data Obat/Insulin berhasil disimpan!")
                st.rerun()

    with tab_f3:
        with st.form("form_food", clear_on_submit=True):
            f_tgl = st.date_input("Tanggal", today, key="food_tgl")
            f_wkt = st.time_input("Waktu", datetime.now().time(), key="food_wkt")
            f_menu = st.text_input("Menu Makanan")
            f_porsi = st.text_input("Porsi", value="1 porsi")
            f_kal = st.text_input("Estimasi Kalori (kkal)", value="300")
            f_cat = st.text_input("Catatan")
            if st.form_submit_button("Simpan Makanan"):
                conn = get_connection()
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO makanan (tanggal, waktu, menu, porsi, estimasi_kalori_kkal, catatan) VALUES (%s, %s, %s, %s, %s, %s)",
                    (f_tgl, f_wkt.strftime("%H:%M"), f_menu, f_porsi, f_kal, f_cat)
                )
                conn.commit()
                conn.close()
                st.success("Data Makanan berhasil disimpan!")
                st.rerun()

    with tab_f4:
        with st.form("form_sport", clear_on_submit=True):
            f_tgl = st.date_input("Tanggal", today, key="sport_tgl")
            f_wkt = st.time_input("Waktu", datetime.now().time(), key="sport_wkt")
            f_jenis = st.text_input("Jenis Olahraga", value="Jalan Pagi")
            f_durasi = st.number_input("Durasi (Menit)", min_value=1, max_value=300, value=30)
            f_jarak = st.number_input("Jarak (km)", min_value=0.0, max_value=50.0, value=2.0, step=0.1)
            f_cat = st.text_input("Catatan")
            if st.form_submit_button("Simpan Olahraga"):
                conn = get_connection()
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO olahraga (tanggal, waktu, jenis, durasi_menit, jarak_km, catatan) VALUES (%s, %s, %s, %s, %s, %s)",
                    (f_tgl, f_wkt.strftime("%H:%M"), f_jenis, f_durasi, f_jarak, f_cat)
                )
                conn.commit()
                conn.close()
                st.success("Data Olahraga berhasil disimpan!")
                st.rerun()

st.divider()

# Riwayat Lengkap
st.subheader("📋 Data Riwayat (PostgreSQL)")
t_gds, t_meds, t_food, t_sport = st.tabs(["Log Gula Darah", "Log Obat & Insulin", "Log Makanan", "Log Olahraga"])

with t_gds:
    st.dataframe(df_gds, width="stretch")

with t_meds:
    st.dataframe(df_meds, width="stretch")

with t_food:
    st.dataframe(df_food, width="stretch")

with t_sport:
    st.dataframe(df_sport, width="stretch")
