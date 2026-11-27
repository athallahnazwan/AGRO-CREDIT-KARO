import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px
from sync import sinkronkan_semua_data

st.set_page_config(
    page_title="SIM-PETANI KARO | Green Fintech",
    layout="wide",
    page_icon="🌱",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp { background-color: #F4F7F5; }
    .hero-banner {
        background: linear-gradient(135deg, #1B4332 0%, #2D6A4F 50%, #40916C 100%);
        padding: 25px 30px;
        border-radius: 15px;
        color: white;
        margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(27, 67, 50, 0.2);
    }
    .hero-banner h1 { color: white !important; margin: 0; font-size: 2.1rem; font-weight: 700; }
    .hero-banner p { color: #D8F3DC; margin-top: 8px; font-size: 1.05rem; }
    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        border-left: 6px solid #2D6A4F;
        padding: 15px 20px;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
    .stButton>button {
        background-color: #2D6A4F;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 20px;
        font-weight: 600;
    }
    .stButton>button:hover { background-color: #1B4332; color: #D8F3DC; }
</style>
""", unsafe_allow_html=True)

DB_URLS = st.secrets["DB_URLS"]

with st.sidebar:
    st.markdown("## 🌱 **SIM-PETANI KARO**")
    st.caption("Distributed Agro-Credit & Carbon Scoring")
    st.divider()
    menu = st.radio(
        "Pilih Halaman:",
        ["📊 Dashboard Pusat Karo", "➕ Input Simulasi Petani", "🌐 Arsitektur & Status DB"]
    )
    st.divider()
    st.info("💡 **Arsitektur Cloud:** Terhubung ke 6 Node PostgreSQL Neon & GitHub Actions.")

st.markdown("""
<div class="hero-banner">
    <h1>🌱 Agro-Credit & Green Scoring System</h1>
    <p>Platform Penilaian Kelayakan Kredit Mikro & Rekam Jejak Karbon Petani Kabupaten Karo</p>
</div>
""", unsafe_allow_html=True)

if menu == "📊 Dashboard Pusat Karo":
    col_btn, col_info = st.columns(2)
    with col_btn:
        if st.button("🔄 Sinkronkan 5 Kecamatan Sekarang"):
            with st.spinner("Menarik data dari seluruh kecamatan..."):
                jml = sinkronkan_semua_data()
                st.toast(f"Berhasil menyinkronkan {jml} data petani!", icon="✅")
    with col_info:
        st.caption("Data juga disinkronkan secara otomatis oleh GitHub Actions, atau klik tombol di samping untuk pembaruan instan.")

    conn = psycopg2.connect(DB_URLS["PUSAT"])
    df = pd.read_sql("SELECT * FROM hasil_skoring_kredit_karo", conn)
    conn.close()

    if df.empty:
        st.warning("⚠️ Data di database pusat masih kosong. Klik tombol **Sinkronkan 5 Kecamatan Sekarang** di atas.")
    else:
        df['skor_kredit_finansial'] = pd.to_numeric(df['skor_kredit_finansial'])
        df['skor_ramah_lingkungan'] = pd.to_numeric(df['skor_ramah_lingkungan'])
        df['plafon_kredit_maksimal'] = pd.to_numeric(df['plafon_kredit_maksimal'])
        df['margin_keuntungan'] = pd.to_numeric(df['margin_keuntungan'])

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("👨‍🌾 Total Petani Terdata", f"{len(df)} Petani", "5 Kecamatan")
        k2.metric("💳 Rata-rata Credit Score", f"{df['skor_kredit_finansial'].mean():.1f} / 100", "Kelayakan Finansial")
        k3.metric("🌿 Rata-rata Green Score", f"{df['skor_ramah_lingkungan'].mean():.1f} / 100", "Indeks Ramah Lingkungan")
        k4.metric("💰 Total Plafon Disetujui", f"Rp {df['plafon_kredit_maksimal'].sum():,.0f}", "Kredit Mikro Siap Salur")

        st.markdown("<br>", unsafe_allow_html=True)
        tab1, tab2, tab3 = st.tabs(["📈 Grafik Skor Petani", "🗺️ Analisis per Kecamatan", "📋 Tabel Keputusan Kredit"])

        with tab1:
            c1, c2 = st.columns(2)
            with c1:
                fig_bar = px.bar(
                    df, x="nama_petani", y=["skor_kredit_finansial", "skor_ramah_lingkungan"],
                    barmode="group", title="Perbandingan Skor Kredit Finansial vs Skor Karbon",
                    color_discrete_map={"skor_kredit_finansial": "#1B4332", "skor_ramah_lingkungan": "#52B788"},
                    labels={"value": "Nilai Skor", "nama_petani": "Nama Petani", "variable": "Jenis Skor"}
                )
                fig_bar.update_layout(plot_bgcolor="white", paper_bgcolor="white", legend_title_text="")
                st.plotly_chart(fig_bar, use_container_width=True)

            with c2:
                fig_pie = px.pie(
                    df, names="kategori_penerima", title="Distribusi Kategori Kredit",
                    hole=0.45, color_discrete_sequence=["#1B4332", "#40916C", "#95D5B2", "#E76F51"]
                )
                fig_pie.update_layout(paper_bgcolor="white")
                st.plotly_chart(fig_pie, use_container_width=True)

        with tab2:
            df_kec = df.groupby("kecamatan_asal", as_index=False).agg({
                "plafon_kredit_maksimal": "sum",
                "skor_ramah_lingkungan": "mean",
                "skor_kredit_finansial": "mean"
            })
            fig_kec = px.bar(
                df_kec, x="kecamatan_asal", y="plafon_kredit_maksimal", color="skor_ramah_lingkungan",
                title="Total Plafon Kredit Disetujui & Rata-rata Green Score per Kecamatan",
                color_continuous_scale="Greens",
                labels={"kecamatan_asal": "Kecamatan", "plafon_kredit_maksimal": "Total Plafon (Rp)", "skor_ramah_lingkungan": "Avg Green Score"}
            )
            fig_kec.update_layout(plot_bgcolor="white", paper_bgcolor="white")
            st.plotly_chart(fig_kec, use_container_width=True)

        with tab3:
            pilih_kec = st.multiselect(
                "Filter Berdasarkan Kecamatan:",
                options=df["kecamatan_asal"].unique(),
                default=df["kecamatan_asal"].unique()
            )
            df_tampil = df[df["kecamatan_asal"].isin(pilih_kec)].copy()
            df_tampil["margin_keuntungan"] = df_tampil["margin_keuntungan"].apply(lambda x: f"Rp {x:,.0f}")
            df_tampil["plafon_kredit_maksimal"] = df_tampil["plafon_kredit_maksimal"].apply(lambda x: f"Rp {x:,.0f}")
            st.dataframe(
                df_tampil[[
                    "id_registrasi", "nama_petani", "kecamatan_asal", "komoditas_utama",
                    "skor_kredit_finansial", "skor_ramah_lingkungan", "kategori_penerima", "plafon_kredit_maksimal"
                ]],
                use_container_width=True, hide_index=True
            )

elif menu == "➕ Input Simulasi Petani":
    st.subheader("📝 Simulasi Pengajuan Kredit & Jejak Karbon Petani")
    with st.form("form_petani", clear_on_submit=True):
        col_a, col_b = st.columns(2)
        with col_a:
            kecamatan = st.selectbox("Pilih Kecamatan Tujuan DB", ["Berastagi", "Tigapanah", "Merek", "Kabanjahe", "Payung"])
            id_reg = st.text_input("ID Registrasi (Contoh: BRS-09)")
            nama = st.text_input("Nama Lengkap Petani")
            poktan = st.text_input("Nama Kelompok Tani (Poktan)")
            komoditas = st.text_input("Komoditas Utama (Contoh: Jeruk Karo, Kopi, Kentang)")
        with col_b:
            pupuk = st.selectbox("Metode Pemupukan", ["100% Organik", "Organik-Kimia (50:50)", "Kimia Sintetis"])
            limbah = st.selectbox("Pengelolaan Limbah Panen", ["Diolah Jadi Kompos", "Pakan Ternak", "Dibakar"])
            irigasi = st.selectbox("Sistem Irigasi Lahan", ["Irigasi Tetes (Hemat Air)", "Sprinkler", "Tadah Hujan"])
            omzet = st.number_input("Omzet Panen Terakhir (Rp)", min_value=0, step=1000000, value=30000000)
            biaya = st.number_input("Biaya Operasional (Rp)", min_value=0, step=1000000, value=12000000)
            kredit = st.selectbox("Riwayat Kredit Sebelumnya", ["Lancar", "Belum Pernah Pinjam", "Menunggak"])

        submit = st.form_submit_button("💾 Simpan ke DB Kecamatan & Proses Skor Pusat")
        if submit:
            if not id_reg or not nama:
                st.error("ID Registrasi dan Nama Petani wajib diisi!")
            else:
                try:
                    conn_kec = psycopg2.connect(DB_URLS[kecamatan])
                    cur_kec = conn_kec.cursor()
                    cur_kec.execute("""
                        INSERT INTO log_agribisnis_petani (
                            id_registrasi, nama_petani, kelompok_tani, komoditas_utama,
                            metode_pemupukan, pengelolaan_limbah_panen, sistem_irigasi,
                            omzet_panen_terakhir, biaya_operasional, status_kredit_lalu, updated_at
                        )
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
                        ON CONFLICT (id_registrasi) DO UPDATE SET
                            nama_petani = EXCLUDED.nama_petani,
                            kelompok_tani = EXCLUDED.kelompok_tani,
                            komoditas_utama = EXCLUDED.komoditas_utama,
                            metode_pemupukan = EXCLUDED.metode_pemupukan,
                            pengelolaan_limbah_panen = EXCLUDED.pengelolaan_limbah_panen,
                            sistem_irigasi = EXCLUDED.sistem_irigasi,
                            omzet_panen_terakhir = EXCLUDED.omzet_panen_terakhir,
                            biaya_operasional = EXCLUDED.biaya_operasional,
                            status_kredit_lalu = EXCLUDED.status_kredit_lalu,
                            updated_at = NOW();
                    """, (id_reg, nama, poktan, komoditas, pupuk, limbah, irigasi, omzet, biaya, kredit))
                    conn_kec.commit()
                    cur_kec.close()
                    conn_kec.close()

                    sinkronkan_semua_data()
                    st.success(f"🎉 Data {nama} berhasil disimpan ke DB {kecamatan} dan diperbarui di DB Pusat!")
                    st.balloons()
                except Exception as e:
                    st.error(f"Gagal menyimpan data: {e}")

elif menu == "🌐 Arsitektur & Status DB":
    st.subheader("🔌 Monitoring Koneksi 6 Node Database Terdistribusi (Neon Cloud)")
    cols = st.columns(3)
    for idx, (nama_db, url) in enumerate(DB_URLS.items()):
        with cols[idx % 3]:
            try:
                conn = psycopg2.connect(url)
                conn.close()
                st.success(f"✅ Node {nama_db}\n\nStatus: Terhubung Aktif")
            except Exception as e:
                st.error(f"❌ Node {nama_db}\n\nGagal: {e}")
