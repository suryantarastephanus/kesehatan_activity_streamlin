"""
health_query.py - Helper query data kesehatan (Neon PostgreSQL).

TANGGAL DIHITUNG DARI JAM NYATA (WIB), BUKAN DARI KONTEKS CHAT.
Aturan: kata relatif ("kemarin", "hari ini", "2 hari lalu") SELALU di-resolve
dari datetime.now(WIB) pada saat perintah dijalankan.

Contoh:
  python health_query.py                 # ringkasan hari ini
  python health_query.py --kemarin       # ringkasan kemarin
  python health_query.py --date 2026-10-27
  python health_query.py --date 2026-10-20 --range 7
  python health_query.py --kemarin --full
"""

import os
import argparse
from datetime import datetime, timedelta, timezone

# Indonesia Barat = UTC+7, tanpa DST. Pakai offset tetap (Windows Python
# tidak punya tzdata, jadi ZoneInfo('Asia/Jakarta') bisa ModuleNotFoundError).
WIB = timezone(timedelta(hours=7))


def now_wib():
    return datetime.now(WIB)


def resolve_date(when, base=None):
    """'today' | 'yesterday' | 'kemarin' | 'Ndays_ago' | 'YYYY-MM-DD' -> (date_str, label)"""
    base = base or now_wib()
    w = (when or "today").strip().lower()
    if w in ("today", "hari ini", "now"):
        return base.strftime("%Y-%m-%d"), "hari ini"
    if w in ("yesterday", "kemarin"):
        return (base - timedelta(days=1)).strftime("%Y-%m-%d"), "kemarin"
    if w.endswith("_days_ago"):
        try:
            n = int(w.split("_")[0])
            return (base - timedelta(days=n)).strftime("%Y-%m-%d"), f"{n} hari lalu"
        except ValueError:
            pass
    if len(w) == 10 and w[4] == "-" and w[7] == "-":
        return w, w
    raise SystemExit(f"Tanggal tidak.dimengerti: {when!r} (pakai today|yesterday|YYYY-MM-DD)")


def load_env():
    # .env berada di root project, script ini di scripts/ -> cek script dir & parent
    here = os.path.dirname(os.path.abspath(__file__))
    roots = [here, os.path.dirname(here)]
    for root in roots:
        for fname in (".env.local", ".env"):
            p = os.path.join(root, fname)
            if os.path.exists(p):
                with open(p, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def get_conn():
    import psycopg2
    load_env()
    url = os.environ.get("DATABASE_URL_UNPOOLED") or os.environ.get("DATABASE_URL")
    return psycopg2.connect(url)


def show(cur, tgl, full=False):
    print("=" * 56)
    print("DATA KESEHATAN -", tgl)
    print("=" * 56)

    print("\n-- MAKAN --")
    cur.execute(
        "SELECT waktu,menu,porsi,estimasi_kalori_kkal FROM makanan "
        "WHERE tanggal=%s ORDER BY waktu", (tgl,))
    rows = cur.fetchall()
    total = 0
    for r in rows:
        print(f"  {r[0]} | {r[1]} | {r[2] or ''} | {r[3]} kkal")
        try:
            total += int(r[3])
        except (TypeError, ValueError):
            pass
    if not rows:
        print("  (tidak ada data)")
    else:
        print(f"  TOTAL ~{total} kkal")

    print("\n-- OBAT --")
    cur.execute(
        "SELECT waktu,kategori,nama,dosis_jumlah,satuan FROM obat_insulin "
        "WHERE tanggal=%s ORDER BY waktu", (tgl,))
    rows = cur.fetchall()
    for r in rows:
        print(f"  {r[0]} | {r[1]:<12} | {r[2]:<18} | {r[3]} {r[4]}")
    if not rows:
        print("  (tidak ada data)")
    else:
        rapid = sum(float(r[3]) for r in rows if r[2] == "Insulin Rapid")
        lev = sum(float(r[3]) for r in rows if r[2] == "Insulin Levemir")
        print(f"  TOTAL suntik: Rapid {rapid:g} unit, Levemir {lev:g} unit")

    print("\n-- GDS --")
    cur.execute(
        "SELECT waktu,tipe,nilai_mg_dl,catatan FROM gula_darah "
        "WHERE tanggal=%s ORDER BY waktu", (tgl,))
    rows = cur.fetchall()
    for r in rows:
        print(f"  {r[0]} | {r[1]} | {r[2]} mg/dL | {r[3] or ''}")
    if not rows:
        print("  (tidak ada data)")

    print("\n-- OLAHRAGA --")
    cur.execute(
        "SELECT waktu,jenis,durasi_menit,jarak_km FROM olahraga "
        "WHERE tanggal=%s ORDER BY waktu", (tgl,))
    rows = cur.fetchall()
    for r in rows:
        print(f"  {r[0]} | {r[1]} | {r[2]} menit | {r[3] or ''} km")
    if not rows:
        print("  (tidak ada data)")

    if full:
        print("\n-- 7 HARI TERAKHIR --")
        cur.execute(
            "SELECT tanggal, count(*), sum(CASE WHEN nama='Insulin Rapid' "
            "THEN dosis_jumlah ELSE 0 END) FROM obat_insulin "
            "WHERE tanggal >= %s::date - 6 GROUP BY tanggal ORDER BY tanggal",
            (tgl,))
        for r in cur.fetchall():
            print(f"  {r[0]} | {r[1]} entri obat | rapid {r[2]} unit")


def main():
    p = argparse.ArgumentParser(description="Query data kesehatan (tanggal dari jam nyata WIB)")
    p.add_argument("--date", help="YYYY-MM-DD | today | yesterday | N_days_ago")
    p.add_argument("--kemarin", action="store_true", help="shortcut untuk yesterday")
    p.add_argument("--today", action="store_true", help="shortcut untuk today")
    p.add_argument("--full", action="store_true", help="tambah ringkasan 7 hari")
    args = p.parse_args()

    when = "today"
    if args.kemarin:
        when = "yesterday"
    if args.today:
        when = "today"
    if args.date:
        when = args.date

    tgl, label = resolve_date(when)
    n = now_wib()
    print(f"NOW (WIB) : {n.strftime('%Y-%m-%d %H:%M:%S %A')}")
    print(f"RESOLVE   : '{when}' -> {tgl} ({label})")

    conn = get_conn()
    cur = conn.cursor()
    show(cur, tgl, full=args.full)
    conn.close()


if __name__ == "__main__":
    main()
