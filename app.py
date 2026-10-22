import os
from datetime import datetime, date, timedelta, timezone
from zoneinfo import ZoneInfo
import pandas as pd
import psycopg2
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

# Page config — wide layout for data-dense dashboard
st.set_page_config(
    page_title="Kesehatan Om Stan",
    page_icon=":material/monitor_heart:",
    layout="wide",
    initial_sidebar_state="expanded",
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
# PIN protection
# ==============================================================================
def check_pin_auth():
    if st.session_state.get("authenticated", False):
        return True

    valid_pin = os.environ.get("DASHBOARD_PIN", "1123")
    if hasattr(st, "secrets") and "DASHBOARD_PIN" in st.secrets:
        valid_pin = str(st.secrets["DASHBOARD_PIN"])

    _, center_col, _ = st.columns([1, 1.2, 1])
    with center_col:
        st.space("large")
        st.header("Kesehatan Om Stan", icon=":material/monitor_heart:")
        st.caption("Masukkan PIN 4 digit untuk membuka dasbor.")

        with st.form("pin_login_form"):
            entered_pin = st.text_input(
                "PIN akses",
                type="password",
                max_chars=8,
                placeholder="Masukkan PIN...",
                label_visibility="collapsed",
            )
            submit_btn = st.form_submit_button("Buka dasbor", icon=":material/lock_open:", width="stretch")

            if submit_btn:
                if entered_pin.strip() == str(valid_pin).strip():
                    st.session_state["authenticated"] = True
                    st.toast("PIN benar. Memuat data...", icon=":material/check_circle:")
                    st.rerun()
                else:
                    st.error("PIN salah.", icon=":material/error:")

    return False


if not check_pin_auth():
    st.stop()

# ==============================================================================
# Database connection & data loading
# ==============================================================================
def get_connection():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url and hasattr(st, "secrets") and "DATABASE_URL" in st.secrets:
        db_url = st.secrets["DATABASE_URL"]

    conn = psycopg2.connect(db_url)
    conn.cursor().execute("SET timezone = 'Asia/Jakarta'")
    conn.commit()
    return conn


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
# Sidebar controls
# ==============================================================================
with st.sidebar:
    st.header("Om Stan", icon=":material/person:")
    st.caption("Protokol glukosa & nutrisi")

    st.badge("Terverifikasi", icon=":material/check:", color="green")
    st.badge("Neon PostgreSQL", icon=":material/cloud:", color="blue")

    st.subheader("Rentang waktu", icon=":material/date_range:")
    filter_range = st.segmented_control(
        "Periode analisis",
        ["Semua", "7 Hari", "30 Hari", "Hari Ini"],
        default="Semua",
        label_visibility="collapsed",
    )

    st.space("medium")
    with st.container(horizontal=True):
        if st.button("Refresh", icon=":material/refresh:", width="stretch"):
            st.cache_data.clear()
            st.rerun()

        if st.button("Logout", icon=":material/lock:", width="stretch"):
            st.session_state["authenticated"] = False
            st.rerun()

# ==============================================================================
# Load datasets
# ==============================================================================
df_gds = load_data("gula_darah")
df_meds = load_data("obat_insulin")
df_food = load_data("makanan")
df_sport = load_data("olahraga")

WIB = ZoneInfo("Asia/Jakarta")  # Indonesia Barat (UTC+7) - sumber kebenaran tanggal


def now_wib():
    """Waktu sekarang dalam zona WIB, timezone-aware."""
    return datetime.now(WIB)


def today_wib():
    """Tanggal hari ini dalam zona WIB."""
    return now_wib().date()


today = today_wib()


def filter_dataframe_by_date(df, date_col="tanggal"):
    if df.empty or date_col not in df.columns:
        return df
    try:
        temp = df.copy()
        temp[date_col] = pd.to_datetime(temp[date_col]).dt.date
        if filter_range == "Hari Ini":
            return temp[temp[date_col] == today]
        elif filter_range == "7 Hari":
            return temp[temp[date_col] >= (today - timedelta(days=7))]
        elif filter_range == "30 Hari":
            return temp[temp[date_col] >= (today - timedelta(days=30))]
        return df
    except Exception:
        return df


df_gds_filtered = filter_dataframe_by_date(df_gds)
df_meds_filtered = filter_dataframe_by_date(df_meds)
df_food_filtered = filter_dataframe_by_date(df_food)
df_sport_filtered = filter_dataframe_by_date(df_sport)

# ==============================================================================
# Header
# ==============================================================================
title_col, date_col = st.columns([4, 1])
with title_col:
    st.title("Kesehatan Om Stan", icon=":material/monitor_heart:")
    st.caption("Glukosa darah, insulin, asupan nutrisi, dan kebugaran")
with date_col:
    st.metric("Hari ini", today.strftime("%d %b %Y"), border=True)

# ==============================================================================
# KPI row — native st.metric with sparklines
# ==============================================================================

# Compute GDS values
if not df_gds.empty:
    latest_gds = int(df_gds.iloc[0]["nilai_mg_dl"])
    latest_tipe = str(df_gds.iloc[0]["tipe"])
    latest_time = str(df_gds.iloc[0]["waktu"])[:5]
    avg_gds = round(float(df_gds["nilai_mg_dl"].mean()), 1)
    est_a1c = round((avg_gds + 46.7) / 28.7, 1)
    tir_count = len(df_gds[(df_gds["nilai_mg_dl"] >= 70) & (df_gds["nilai_mg_dl"] <= 140)])
    tir_percentage = round((tir_count / len(df_gds)) * 100, 1)
    min_gds = int(df_gds["nilai_mg_dl"].min())
    max_gds = int(df_gds["nilai_mg_dl"].max())

    # Sparkline data: last 14 readings
    gds_spark = df_gds["nilai_mg_dl"].head(14).tolist()[::-1]
else:
    latest_gds = 0
    latest_tipe = "-"
    latest_time = "-"
    avg_gds, est_a1c, tir_percentage = 0, 0, 0
    min_gds, max_gds = 0, 0
    gds_spark = []

# Compute insulin values
if not df_meds.empty:
    today_ins = df_meds[df_meds["kategori"] == "Insulin"]
    total_insulin = int(today_ins["dosis_jumlah"].sum()) if not today_ins.empty else 0
    freq_insulin = len(today_ins) if not today_ins.empty else 0
    ins_spark = today_ins["dosis_jumlah"].head(14).tolist()[::-1] if not today_ins.empty else []
else:
    total_insulin, freq_insulin = 0, 0
    ins_spark = []

total_meals = len(df_food) if not df_food.empty else 0
total_sport_minutes = int(df_sport["durasi_menit"].sum()) if not df_sport.empty and "durasi_menit" in df_sport.columns else 0

# GDS status
if latest_gds <= 140:
    gds_delta_desc = f"{latest_tipe} — zona ideal"
elif latest_gds <= 200:
    gds_delta_desc = f"{latest_tipe} — perlu perhatian"
else:
    gds_delta_desc = f"{latest_tipe} — zona waspada"

with st.container(horizontal=True):
    st.metric(
        "Gula darah terakhir",
        f"{latest_gds} mg/dL",
        delta_description=f"Pukul {latest_time} · {gds_delta_desc}",
        border=True,
        chart_data=gds_spark if gds_spark else None,
        chart_type="line",
        icon=":material/bloodtype:",
    )
    st.metric(
        "Total insulin rapid",
        f"{total_insulin} unit",
        delta_description=f"{freq_insulin}x injeksi tercatat",
        border=True,
        chart_data=ins_spark if ins_spark else None,
        chart_type="bar",
        icon=":material/vaccines:",
    )
    st.metric(
        "Sesi makan",
        f"{total_meals} sesi",
        delta_description="Target: serat & protein utama",
        border=True,
        icon=":material/restaurant:",
    )
    st.metric(
        "Target berat badan",
        "< 90 kg",
        delta_description=f"Olahraga: {total_sport_minutes} menit total",
        border=True,
        icon=":material/fitness_center:",
    )

# ==============================================================================
# Clinical benchmarks row
# ==============================================================================
with st.container(horizontal=True):
    st.metric("Rata-rata GDS", f"{avg_gds} mg/dL", border=True, icon=":material/analytics:")
    st.metric("Estimasi HbA1c", f"{est_a1c}%", border=True, icon=":material/labs:")
    st.metric("Time in range (70–140)", f"{tir_percentage}%", border=True, icon=":material/target:")
    st.metric("Fluktuasi GDS", f"{min_gds} — {max_gds} mg/dL", border=True, icon=":material/swap_vert:")

# ==============================================================================
# Main workspace: chart (left) + activity feed (right)
# ==============================================================================
left_panel, right_panel = st.columns([7, 3])

with left_panel:
    with st.container(border=True):
        st.subheader("Korelasi glukosa, insulin & makanan", icon=":material/show_chart:")
        st.caption("Kurva fluktuasi glukosa darah terhadap asupan nutrisi dan injeksi insulin.")

        fig = make_subplots(specs=[[{"secondary_y": True}]])

        # Target zone bands
        fig.add_hrect(
            y0=70, y1=140,
            fillcolor="#34D399", opacity=0.10, line_width=0,
            annotation_text="Zona ideal (70–140 mg/dL)", annotation_position="top left",
            annotation_font=dict(color="#34D399", size=10, family="Inter"),
            secondary_y=False,
        )
        fig.add_hrect(
            y0=140, y1=200,
            fillcolor="#FBBF24", opacity=0.08, line_width=0,
            annotation_text="Perhatian (140–200)", annotation_position="top left",
            annotation_font=dict(color="#FBBF24", size=10, family="Inter"),
            secondary_y=False,
        )
        fig.add_hrect(
            y0=200, y1=380,
            fillcolor="#F87171", opacity=0.06, line_width=0,
            annotation_text="Waspada (>200)", annotation_position="top left",
            annotation_font=dict(color="#F87171", size=10, family="Inter"),
            secondary_y=False,
        )

        # GDS line
        if not df_gds_filtered.empty:
            df_gds_sorted = df_gds_filtered.copy().sort_values(by=["tanggal", "waktu"])
            df_gds_sorted["timestamp"] = df_gds_sorted["tanggal"].astype(str) + " " + df_gds_sorted["waktu"].astype(str)
            fig.add_trace(
                go.Scatter(
                    x=df_gds_sorted["timestamp"],
                    y=df_gds_sorted["nilai_mg_dl"],
                    mode="lines+markers+text",
                    name="Gula darah (mg/dL)",
                    text=[f"{int(v)}" for v in df_gds_sorted["nilai_mg_dl"]],
                    textposition="top center",
                    textfont=dict(color="#F87171", size=11, family="JetBrains Mono"),
                    line=dict(color="#F87171", width=2.5, shape="spline"),
                    marker=dict(size=10, symbol="diamond", color="#F87171", line=dict(width=1.5, color="#0F172A")),
                    hovertemplate="<b>Waktu:</b> %{x}<br><b>GDS:</b> %{y} mg/dL<extra></extra>",
                ),
                secondary_y=False,
            )

        # Insulin bars
        if not df_meds_filtered.empty:
            df_ins = df_meds_filtered[df_meds_filtered["kategori"] == "Insulin"].copy().sort_values(by=["tanggal", "waktu"])
            if not df_ins.empty:
                df_ins["timestamp"] = df_ins["tanggal"].astype(str) + " " + df_ins["waktu"].astype(str)
                fig.add_trace(
                    go.Bar(
                        x=df_ins["timestamp"],
                        y=df_ins["dosis_jumlah"],
                        name="Insulin rapid (unit)",
                        text=[f"{int(d)} U" for d in df_ins["dosis_jumlah"]],
                        textposition="outside",
                        textfont=dict(color="#60A5FA", size=10, family="JetBrains Mono"),
                        marker_color="#60A5FA",
                        opacity=0.8,
                        width=0.22,
                        hovertemplate="<b>Waktu:</b> %{x}<br><b>Dosis:</b> %{y} unit<extra></extra>",
                    ),
                    secondary_y=True,
                )

        # Meal markers
        if not df_food_filtered.empty:
            df_food_sorted = df_food_filtered.copy().sort_values(by=["tanggal", "waktu"])
            df_food_sorted["timestamp"] = df_food_sorted["tanggal"].astype(str) + " " + df_food_sorted["waktu"].astype(str)
            meal_texts = []
            for m, p in zip(df_food_sorted["menu"], df_food_sorted["porsi"]):
                p_str = str(p or "").strip()
                if p_str:
                    items = [it.strip() for it in p_str.split(",") if it.strip()]
                    formatted_p = ",<br>".join(items)
                    meal_texts.append(f"<b>{m}</b><br>{formatted_p}")
                else:
                    meal_texts.append(f"<b>{m}</b>")

            fig.add_trace(
                go.Scatter(
                    x=df_food_sorted["timestamp"],
                    y=[115] * len(df_food_sorted),
                    mode="markers+text",
                    name="Sesi makan",
                    text=meal_texts,
                    textposition="bottom center",
                    textfont=dict(color="#34D399", size=9, family="Inter"),
                    marker=dict(size=12, color="#34D399", symbol="circle", line=dict(width=1.5, color="#0F172A")),
                    hovertemplate="<b>Waktu:</b> %{x}<br><b>Menu:</b> %{text}<extra></extra>",
                ),
                secondary_y=False,
            )

        # Chart layout — dark canvas matching the theme
        fig.update_layout(
            plot_bgcolor="#0F172A",
            paper_bgcolor="#0F172A",
            xaxis_title="Linimasa kronologis",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                bgcolor="rgba(15, 23, 42, 0.9)",
                bordercolor="#334155",
                borderwidth=1,
                font=dict(color="#F1F5F9", size=11, family="Inter"),
            ),
            margin=dict(l=20, r=20, t=35, b=25),
            height=480,
            hovermode="x unified",
            hoverlabel=dict(bgcolor="#1E293B", font_color="#F1F5F9", font_size=12, bordercolor="#334155"),
        )
        fig.update_xaxes(
            showgrid=True,
            gridcolor="#1E293B",
            color="#94A3B8",
            tickfont=dict(color="#94A3B8", family="JetBrains Mono", size=10),
            title_font=dict(color="#94A3B8", size=12),
        )
        fig.update_yaxes(
            title_text="Gula darah (mg/dL)",
            range=[40, 320],
            showgrid=True,
            gridcolor="#1E293B",
            color="#F87171",
            tickfont=dict(color="#F87171", family="JetBrains Mono", size=10),
            title_font=dict(color="#F87171", size=12),
            secondary_y=False,
        )
        fig.update_yaxes(
            title_text="Insulin rapid (unit)",
            range=[0, 45],
            showgrid=False,
            color="#60A5FA",
            tickfont=dict(color="#60A5FA", family="JetBrains Mono", size=10),
            title_font=dict(color="#60A5FA", size=12),
            secondary_y=True,
        )

        st.plotly_chart(fig, width="stretch")

    # Data tables
    st.space("small")
    with st.container(border=True):
        st.subheader("Log riwayat data", icon=":material/table_chart:")
        t_gds, t_meds, t_food, t_sport = st.tabs([
            f"Gula darah ({len(df_gds)})",
            f"Obat & insulin ({len(df_meds)})",
            f"Nutrisi ({len(df_food)})",
            f"Olahraga ({len(df_sport)})",
        ])

        with t_gds:
            cols_gds = [c for c in ["tanggal", "waktu", "tipe", "nilai_mg_dl", "catatan"] if c in df_gds.columns]
            st.dataframe(
                df_gds[cols_gds] if cols_gds else df_gds,
                column_config={
                    "tanggal": st.column_config.DateColumn("Tanggal"),
                    "waktu": st.column_config.TimeColumn("Waktu"),
                    "tipe": st.column_config.TextColumn("Tipe"),
                    "nilai_mg_dl": st.column_config.NumberColumn("GDS (mg/dL)"),
                    "catatan": st.column_config.TextColumn("Catatan", width="medium"),
                },
                width="stretch",
                hide_index=True,
                alt="Riwayat gula darah",
            )

        with t_meds:
            cols_meds = [c for c in ["tanggal", "waktu", "kategori", "nama", "dosis_jumlah", "satuan", "catatan"] if c in df_meds.columns]
            st.dataframe(
                df_meds[cols_meds] if cols_meds else df_meds,
                column_config={
                    "tanggal": st.column_config.DateColumn("Tanggal"),
                    "waktu": st.column_config.TimeColumn("Waktu"),
                    "kategori": st.column_config.TextColumn("Kategori"),
                    "nama": st.column_config.TextColumn("Nama"),
                    "dosis_jumlah": st.column_config.NumberColumn("Dosis"),
                    "satuan": st.column_config.TextColumn("Satuan"),
                    "catatan": st.column_config.TextColumn("Catatan", width="medium"),
                },
                width="stretch",
                hide_index=True,
                alt="Riwayat obat dan insulin",
            )

        with t_food:
            df_food_display = df_food.copy()
            if not df_food_display.empty and "porsi" in df_food_display.columns:
                df_food_display["porsi"] = df_food_display["porsi"].apply(
                    lambda x: ",\n".join([i.strip() for i in str(x).split(",") if i.strip()]) if pd.notna(x) else ""
                )
            cols_food = [c for c in ["tanggal", "waktu", "menu", "porsi", "estimasi_kalori_kkal", "catatan"] if c in df_food_display.columns]
            st.dataframe(
                df_food_display[cols_food] if cols_food else df_food_display,
                column_config={
                    "tanggal": st.column_config.DateColumn("Tanggal"),
                    "waktu": st.column_config.TimeColumn("Waktu"),
                    "menu": st.column_config.TextColumn("Menu", width="medium"),
                    "porsi": st.column_config.TextColumn("Rincian / Porsi", width="large"),
                    "estimasi_kalori_kkal": st.column_config.TextColumn("Kalori (kkal)", width="small"),
                    "catatan": st.column_config.TextColumn("Catatan", width="medium"),
                },
                width="stretch",
                hide_index=True,
                alt="Riwayat asupan makanan",
            )

        with t_sport:
            cols_sport = [c for c in ["tanggal", "waktu", "jenis", "durasi_menit", "jarak_km", "catatan"] if c in df_sport.columns]
            st.dataframe(
                df_sport[cols_sport] if cols_sport else df_sport,
                column_config={
                    "tanggal": st.column_config.DateColumn("Tanggal"),
                    "waktu": st.column_config.TimeColumn("Waktu"),
                    "jenis": st.column_config.TextColumn("Jenis"),
                    "durasi_menit": st.column_config.NumberColumn("Durasi (mnt)"),
                    "jarak_km": st.column_config.NumberColumn("Jarak (km)"),
                    "catatan": st.column_config.TextColumn("Catatan", width="medium"),
                },
                width="stretch",
                hide_index=True,
                alt="Riwayat olahraga",
            )


# Activity feed (right panel)
with right_panel:
    with st.container(border=True):
        st.subheader("Aktivitas terkini", icon=":material/timeline:")
        st.caption("Catatan klinis dan nutrisi terurut waktu.")

        filter_feed = st.pills(
            "Kategori",
            ["Semua", "GDS", "Insulin", "Makan"],
            default="Semua",
            label_visibility="collapsed",
        )

        events = []
        if filter_feed in ["Semua", "GDS"]:
            for _, r in df_gds.iterrows():
                events.append({
                    "ts": f"{r['tanggal']} {str(r['waktu'])[:5]}",
                    "icon": ":material/bloodtype:",
                    "title": f"GDS: **{r['nilai_mg_dl']} mg/dL**",
                    "badge_text": r["tipe"],
                    "badge_color": "red" if int(r["nilai_mg_dl"]) > 200 else ("orange" if int(r["nilai_mg_dl"]) > 140 else "green"),
                    "note": r["catatan"] or "Pengukuran rutin",
                })
        if filter_feed in ["Semua", "Insulin"]:
            for _, r in df_meds.iterrows():
                is_ins = r["kategori"] == "Insulin"
                events.append({
                    "ts": f"{r['tanggal']} {str(r['waktu'])[:5]}",
                    "icon": ":material/vaccines:" if is_ins else ":material/medication:",
                    "title": f"{r['kategori']}: **{r['nama']}** ({int(r['dosis_jumlah'])} {r['satuan']})",
                    "badge_text": "Insulin rapid" if is_ins else r["kategori"],
                    "badge_color": "blue" if is_ins else "violet",
                    "note": r["catatan"] or ("Injeksi insulin" if is_ins else "Konsumsi obat"),
                })
        if filter_feed in ["Semua", "Makan"]:
            for _, r in df_food.iterrows():
                p_items = [i.strip() for i in str(r["porsi"]).split(",") if i.strip()] if r["porsi"] else []
                events.append({
                    "ts": f"{r['tanggal']} {str(r['waktu'])[:5]}",
                    "icon": ":material/restaurant:",
                    "title": f"Makan: **{r['menu']}**",
                    "badge_text": f"{len(p_items)} item" if len(p_items) > 1 else (p_items[0] if p_items else "Nutrisi"),
                    "badge_color": "green",
                    "porsi_items": p_items,
                    "note": f"Est. {r['estimasi_kalori_kkal']} kkal — {r['catatan']}" if r["catatan"] else f"Est. {r['estimasi_kalori_kkal']} kkal",
                })
        if filter_feed == "Semua":
            for _, r in df_sport.iterrows():
                events.append({
                    "ts": f"{r['tanggal']} {str(r['waktu'])[:5]}",
                    "icon": ":material/directions_run:",
                    "title": f"Olahraga: **{r['jenis']}**",
                    "badge_text": f"{r['durasi_menit']} mnt",
                    "badge_color": "orange",
                    "porsi_items": [],
                    "note": f"{r['jarak_km']} km — {r['catatan']}",
                })

        events_sorted = sorted(events, key=lambda x: str(x["ts"]), reverse=True)

        feed_container = st.container(height=480)
        with feed_container:
            if events_sorted:
                for ev in events_sorted[:20]:
                    with st.container(border=True):
                        st.caption(f":material/schedule: {ev['ts']}")
                        st.markdown(f"{ev['title']}")
                        st.badge(ev["badge_text"], color=ev["badge_color"])
                        if ev.get("porsi_items"):
                            rincian_lines = ",\n".join(ev["porsi_items"])
                            st.caption(f"**Rincian:**\n{rincian_lines}")
                        st.caption(ev["note"])
            else:
                st.info("Belum ada data untuk kategori ini.", icon=":material/info:")

    # Quick data entry
    st.space("small")
    with st.expander("Entri data cepat", icon=":material/add_circle:"):
        in_tab1, in_tab2, in_tab3 = st.tabs(["GDS", "Insulin", "Makan"])

        with in_tab1:
            with st.form("quick_gds", clear_on_submit=True):
                q_tgl = st.date_input("Tanggal", today, key="q_gds_tgl")
                q_wkt = st.time_input("Waktu", now_wib().time(), key="q_gds_wkt")
                q_tipe = st.selectbox("Tipe", ["GDP (Puasa)", "GDS (Sewaktu)", "2 Jam Setelah Makan", "Sebelum Tidur"], key="q_gds_tipe")
                q_val = st.number_input("Nilai (mg/dL)", min_value=20, max_value=800, value=120, key="q_gds_val")
                q_cat = st.text_input("Catatan", key="q_gds_cat")
                if st.form_submit_button("Simpan GDS", icon=":material/save:", width="stretch"):
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute(
                        "INSERT INTO gula_darah (tanggal, waktu, tipe, nilai_mg_dl, catatan) VALUES (%s, %s, %s, %s, %s)",
                        (q_tgl, q_wkt.strftime("%H:%M"), q_tipe, q_val, q_cat),
                    )
                    conn.commit()
                    conn.close()
                    st.cache_data.clear()
                    st.toast("GDS tersimpan.", icon=":material/check_circle:")
                    st.rerun()

        with in_tab2:
            with st.form("quick_ins", clear_on_submit=True):
                qi_tgl = st.date_input("Tanggal", today, key="qi_tgl")
                qi_wkt = st.time_input("Waktu", now_wib().time(), key="qi_wkt")
                qi_nama = st.text_input("Nama", value="Insulin Rapid", key="qi_nama")
                qi_dose = st.number_input("Dosis (unit)", min_value=1.0, max_value=100.0, value=26.0, step=1.0, key="qi_dose")
                qi_cat = st.text_input("Catatan", key="qi_cat")
                if st.form_submit_button("Simpan insulin", icon=":material/save:", width="stretch"):
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute(
                        "INSERT INTO obat_insulin (tanggal, waktu, kategori, nama, dosis_jumlah, satuan, catatan) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                        (qi_tgl, qi_wkt.strftime("%H:%M"), "Insulin", qi_nama, qi_dose, "unit", qi_cat),
                    )
                    conn.commit()
                    conn.close()
                    st.cache_data.clear()
                    st.toast("Insulin tersimpan.", icon=":material/check_circle:")
                    st.rerun()

        with in_tab3:
            with st.form("quick_food", clear_on_submit=True):
                qf_tgl = st.date_input("Tanggal", today, key="qf_tgl")
                qf_wkt = st.time_input("Waktu", now_wib().time(), key="qf_wkt")
                qf_menu = st.text_input("Menu", placeholder="Ayam rebus, nasi merah", key="qf_menu")
                qf_por = st.text_input("Porsi", value="1 porsi", key="qf_por")
                qf_kal = st.text_input("Estimasi kalori (kkal)", value="350", key="qf_kal")
                if st.form_submit_button("Simpan makanan", icon=":material/save:", width="stretch"):
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute(
                        "INSERT INTO makanan (tanggal, waktu, menu, porsi, estimasi_kalori_kkal, catatan) VALUES (%s, %s, %s, %s, %s, %s)",
                        (qf_tgl, qf_wkt.strftime("%H:%M"), qf_menu, qf_por, qf_kal, ""),
                    )
                    conn.commit()
                    conn.close()
                    st.cache_data.clear()
                    st.toast("Makanan tersimpan.", icon=":material/check_circle:")
                    st.rerun()
