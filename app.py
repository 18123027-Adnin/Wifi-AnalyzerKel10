import time
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import streamlit as st

from analyzer import full_analysis
from firebase_config import init_firebase, get_history

st.set_page_config(
    page_title="WiFi Analyzer",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .recommend-box { background:#0D3B26; border-left:4px solid #00C851;
                     padding:12px; border-radius:6px; margin:8px 0; }
    .warn-box      { background:#3B1A0D; border-left:4px solid #FF4444;
                     padding:12px; border-radius:6px; margin:8px 0; }
</style>
""", unsafe_allow_html=True)

# ── Firebase ──────────────────────────────────────────────
@st.cache_resource
def get_db():
    return init_firebase()

db = get_db()

# ── Sidebar ───────────────────────────────────────────────
with st.sidebar:
    st.title("📡 WiFi Analyzer")
    st.markdown("**Kelompok 10 — ET3204 LTKA**")
    st.divider()

    st.subheader("⚙️ Pengaturan")
    auto_refresh     = st.checkbox("Auto Refresh", value=False)
    refresh_interval = st.slider("Interval (detik)", 10, 120, 30, disabled=not auto_refresh)

    st.divider()
    st.subheader("📋 Filter")
    band_filter    = st.multiselect("Band Frekuensi", ["2.4 GHz", "5 GHz"],
                                     default=["2.4 GHz", "5 GHz"])
    quality_filter = st.multiselect("Kualitas Sinyal",
                                     ["Excellent", "Good", "Fair", "Poor"],
                                     default=["Excellent", "Good", "Fair", "Poor"])
    st.divider()
    st.subheader("📥 Cara Pakai")
    st.markdown("""
1. Download **ScanWiFi.bat** & **wifiscan.py** dari repo GitHub
2. Letakkan **serviceAccountKey.json** di folder yang sama
3. Klik 2x **ScanWiFi.bat** sebagai Administrator
4. Dashboard ini otomatis terbuka dengan data nyata Anda ✅
""")

# ── Header ────────────────────────────────────────────────
st.title("📡 WiFi Analyzer Dashboard")
st.markdown("**Kelompok 10 | ET3204 Layanan Tersambung dan Komputasi Awan**")
st.divider()

# ── Ambil data dari Firebase ──────────────────────────────
col_btn, col_info = st.columns([1, 4])
with col_btn:
    st.button("🔄 Refresh Data", type="primary", use_container_width=True)
with col_info:
    st.caption("Data diambil dari Firebase — hasil scan WiFi nyata dari perangkat Anda")

# Cek koneksi Firebase
if db is None:
    st.error("""
    ❌ **Tidak dapat terhubung ke Firebase.**

    Untuk developer: pastikan `[firebase]` secrets sudah dikonfigurasi di Streamlit Cloud.
    Lihat README untuk panduan lengkap.
    """)
    st.stop()

with st.spinner("Mengambil data terbaru dari Firebase..."):
    history = get_history(db, limit=50)

if not history:
    st.warning("""
    ⚠️ **Belum ada data scan.**

    Jalankan **ScanWiFi.bat** di laptop Anda terlebih dahulu, lalu kembali ke halaman ini!
    Data akan otomatis muncul setelah scan selesai.
    """)
    st.stop()

# Ambil scan terbaru
latest    = history[0]
networks  = latest.get("networks", [])
last_time = latest.get("timestamp", "-")

# Filter
filtered = [
    n for n in networks
    if n.get("band") in band_filter
    and n.get("quality") in quality_filter
]

# Analisis
analysis = full_analysis(networks) if networks else {}
rec      = analysis.get("recommendation", {})

# ── Metrics ───────────────────────────────────────────────
st.success(f"✅ Data scan terbaru — {last_time} | {len(networks)} jaringan terdeteksi")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("🕐 Scan Terakhir", last_time[11:19] if len(last_time) > 10 else last_time)
with col2:
    st.metric("📶 Total Jaringan", analysis.get("total_networks", len(networks)))
with col3:
    st.metric("📻 Band 2.4 GHz", analysis.get("networks_24ghz", 0))
with col4:
    st.metric("🚀 Band 5 GHz", analysis.get("networks_5ghz", 0))

st.divider()

# ── Rekomendasi Channel ───────────────────────────────────
st.subheader("🎯 Rekomendasi Channel Optimal")
col_rec24, col_rec5 = st.columns(2)

with col_rec24:
    if "2.4GHz" in rec:
        r = rec["2.4GHz"]
        st.markdown(f"""
        <div class="recommend-box">
            <h3 style="color:#00C851;margin:0">✅ 2.4 GHz → Channel {r['channel']}</h3>
            <p style="margin:6px 0 0 0;color:#ccc">{r['reason']}</p>
            <small style="color:#aaa">Skor interferensi: {r['score']}</small>
        </div>""", unsafe_allow_html=True)

with col_rec5:
    if "5GHz" in rec:
        r = rec["5GHz"]
        st.markdown(f"""
        <div class="recommend-box">
            <h3 style="color:#00C851;margin:0">✅ 5 GHz → Channel {r['channel']}</h3>
            <p style="margin:6px 0 0 0;color:#ccc">{r['reason']}</p>
            <small style="color:#aaa">Skor interferensi: {r['score']}</small>
        </div>""", unsafe_allow_html=True)

congested = analysis.get("congested_channels", [])
overlaps  = analysis.get("overlapping_pairs", [])
if congested:
    st.markdown(f"""<div class="warn-box">
        ⚠️ <b>Channel Padat:</b> Channel {', '.join(map(str, congested))}
    </div>""", unsafe_allow_html=True)
if overlaps:
    st.markdown(f"""<div class="warn-box">
        ⚠️ <b>Overlap:</b> {', '.join([f'Ch{a}↔Ch{b}' for a, b in overlaps])}
    </div>""", unsafe_allow_html=True)

st.divider()

# ── Tabel jaringan ────────────────────────────────────────
st.subheader("📋 Jaringan WiFi Terdeteksi (Scan Terbaru)")
if filtered:
    df       = pd.DataFrame(filtered)
    cols_show = [c for c in ["ssid","bssid","rssi","channel","band","quality","timestamp"] if c in df.columns]
    df       = df[cols_show]
    df.columns = [c.upper() for c in cols_show]

    def color_q(val):
        return {
            "EXCELLENT": "color:#00C851;font-weight:bold",
            "GOOD"     : "color:#33B5E5;font-weight:bold",
            "FAIR"     : "color:#FFBB33;font-weight:bold",
            "POOR"     : "color:#FF4444;font-weight:bold",
        }.get(val.upper() if isinstance(val, str) else "", "")

    if "QUALITY" in df.columns:
        st.dataframe(df.style.map(color_q, subset=["QUALITY"]),
                     use_container_width=True, hide_index=True)
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("Tidak ada jaringan yang cocok dengan filter.")

st.divider()

# ── Bar Chart RSSI ────────────────────────────────────────
st.subheader("📊 Kekuatan Sinyal (RSSI) per Jaringan")
if filtered:
    df_plot   = pd.DataFrame(filtered).sort_values("rssi", ascending=True)
    color_map = {"Excellent":"#00C851","Good":"#33B5E5","Fair":"#FFBB33","Poor":"#FF4444"}
    fig = px.bar(df_plot, x="rssi", y="ssid", orientation="h",
                 color="quality", color_discrete_map=color_map,
                 labels={"rssi":"RSSI (dBm)","ssid":"SSID","quality":"Kualitas"},
                 title="Bar Chart RSSI — Semakin kanan semakin kuat",
                 text="rssi")
    fig.update_layout(plot_bgcolor="#0E1117", paper_bgcolor="#0E1117",
                      font_color="#FAFAFA",
                      xaxis=dict(range=[-100,-20], gridcolor="#333"),
                      yaxis=dict(gridcolor="#333"),
                      height=max(300, len(filtered)*40))
    fig.update_traces(texttemplate="%{text} dBm", textposition="outside")
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ── Channel Map ───────────────────────────────────────────
st.subheader("📻 Channel Map")
col_24, col_5 = st.columns(2)

with col_24:
    st.markdown("**Band 2.4 GHz**")
    nets_24 = [n for n in filtered if "2.4" in n.get("band","")]
    if nets_24:
        ch_counts = {ch: sum(1 for n in nets_24 if n["channel"] == ch) for ch in range(1,14)}
        fig2, ax  = plt.subplots(figsize=(8,3))
        fig2.patch.set_facecolor("#0E1117")
        ax.set_facecolor("#0E1117")
        bar_colors = ["#FF4444" if c >= 3 else "#33B5E5" if c >= 1 else "#2A2A3A"
                      for c in ch_counts.values()]
        ax.bar(list(ch_counts.keys()), list(ch_counts.values()),
               color=bar_colors, edgecolor="#444", width=0.7)
        rec_ch = rec.get("2.4GHz", {}).get("channel")
        if rec_ch:
            ax.axvline(x=rec_ch, color="#00C851", linestyle="--", linewidth=2,
                       label=f"Rekomendasi: Ch {rec_ch}")
            ax.legend(facecolor="#1E1E2E", labelcolor="white")
        ax.set_xlabel("Channel", color="white")
        ax.set_ylabel("Jumlah Jaringan", color="white")
        ax.set_xticks(range(1,14))
        ax.tick_params(colors="white")
        for s in ax.spines.values(): s.set_edgecolor("#333")
        st.pyplot(fig2)
    else:
        st.info("Tidak ada jaringan 2.4 GHz")

with col_5:
    st.markdown("**Band 5 GHz**")
    nets_5 = [n for n in filtered if "5" in n.get("band","")]
    if nets_5:
        ch_counts5 = {}
        for n in nets_5:
            ch_counts5[n["channel"]] = ch_counts5.get(n["channel"], 0) + 1
        fig3, ax3  = plt.subplots(figsize=(8,3))
        fig3.patch.set_facecolor("#0E1117")
        ax3.set_facecolor("#0E1117")
        chs        = sorted(ch_counts5.keys())
        bar_colors5 = ["#FF4444" if ch_counts5[c] >= 2 else "#33B5E5" for c in chs]
        ax3.bar(chs, [ch_counts5[c] for c in chs],
                color=bar_colors5, edgecolor="#444", width=3)
        rec_ch5 = rec.get("5GHz", {}).get("channel")
        if rec_ch5:
            ax3.axvline(x=rec_ch5, color="#00C851", linestyle="--", linewidth=2,
                        label=f"Rekomendasi: Ch {rec_ch5}")
            ax3.legend(facecolor="#1E1E2E", labelcolor="white")
        ax3.set_xlabel("Channel", color="white")
        ax3.set_ylabel("Jumlah Jaringan", color="white")
        ax3.tick_params(colors="white")
        for s in ax3.spines.values(): s.set_edgecolor("#333")
        st.pyplot(fig3)
    else:
        st.info("Tidak ada jaringan 5 GHz")

st.divider()

# ── Histori semua scan ────────────────────────────────────
st.subheader("☁️ Histori Semua Scan dari Firebase")
if len(history) > 1:
    for i, scan in enumerate(history[1:], start=2):
        ts    = scan.get("timestamp", "N/A")
        total = scan.get("total_networks", 0)
        with st.expander(f"📅 Scan #{i} — {ts} | {total} jaringan"):
            nets = scan.get("networks", [])
            if nets:
                df_h = pd.DataFrame(nets)
                cols = [c for c in ["ssid","rssi","channel","band","quality"] if c in df_h.columns]
                st.dataframe(df_h[cols], use_container_width=True, hide_index=True)
else:
    st.info("Baru ada 1 scan. Jalankan ScanWiFi.bat lagi dari lokasi lain untuk tambah data!")

# ── Auto refresh ──────────────────────────────────────────
if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()

st.divider()
st.markdown("""
<div style="text-align:center;color:#555;font-size:13px;padding-top:8px">
    WiFi Analyzer — Kelompok 10 | ET3204 Layanan Tersambung dan Komputasi Awan<br>
    Muthia Nabilla Azzahra · Belvaraina Tsuraya Sunu · Adnin Sakara
</div>
""", unsafe_allow_html=True)
