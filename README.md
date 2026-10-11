# Health & Lifestyle Dashboard — Om Stan

Aplikasi monitoring kesehatan interaktif berbasis Streamlit dan PostgreSQL (Local / Neon Cloud).

## Fitur
- **Visualisasi Timeline Terpadu**: Korelasi kurva Gula Darah (mg/dL), Dosis Insulin Rapid (Unit), dan jam makan dalam 1 grafik dual-axis.
- **Zona Target GDS**: Zona Hijau (70-140 mg/dL), Kuning (140-200), Merah (>200).
- **Live Activity Stream**: Feed kronologis aktivitas medis dan nutrisi.
- **Database Support**: Terintegrasi PostgreSQL lokal dan Neon Cloud.

## Cara Menjalankan
1. Install dependensi:
   ```bash
   pip install -r requirements.txt
   ```
2. Jalankan dashboard:
   ```bash
   streamlit run app.py
   ```
3. Buka di browser: `http://localhost:8501`
