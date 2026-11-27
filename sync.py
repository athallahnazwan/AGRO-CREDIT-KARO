import os
import psycopg2

def get_db_urls():
    # Mengambil URL dari Environment Variable (GitHub Actions) atau Streamlit Secrets
    try:
        import streamlit as st
        return st.secrets["DB_URLS"]
    except Exception:
        return {
            "PUSAT": os.environ["DB_PUSAT"],
            "Berastagi": os.environ["DB_BERASTAGI"],
            "Tigapanah": os.environ["DB_TIGAPANAH"],
            "Merek": os.environ["DB_MEREK"],
            "Kabanjahe": os.environ["DB_KABANJAHE"],
            "Payung": os.environ["DB_PAYUNG"],
        }

def sinkronkan_semua_data():
    urls = get_db_urls()
    total_data = 0
    conn_pusat = psycopg2.connect(urls["PUSAT"])
    cur_pusat = conn_pusat.cursor()

    for kec in ["Berastagi", "Tigapanah", "Merek", "Kabanjahe", "Payung"]:
        conn_kec = psycopg2.connect(urls[kec])
        cur_kec = conn_kec.cursor()
        cur_kec.execute("SELECT * FROM log_agribisnis_petani")
        rows = cur_kec.fetchall()
        cur_kec.close()
        conn_kec.close()

        for row in rows:
            id_reg, nama, poktan, komoditas, pupuk, limbah, irigasi, omzet, biaya, kredit_lalu, _ = row
            omzet, biaya = float(omzet), float(biaya)
            margin = omzet - biaya

            # Hitung Green Score (0-100)
            green_score = 10 + (50 if pupuk == '100% Organik' else 30 if pupuk == 'Organik-Kimia (50:50)' else 0)
            green_score += (40 if limbah == 'Diolah Jadi Kompos' else 25 if limbah == 'Pakan Ternak' else 0)

            # Hitung Credit Score (0-100)
            credit_score = 15 + (40 if margin >= biaya else 20 if margin > 0 else 0)
            credit_score += (20 if irigasi == 'Irigasi Tetes (Hemat Air)' else 10 if irigasi == 'Sprinkler' else 0)
            credit_score += (25 if kredit_lalu == 'Lancar' else 15 if kredit_lalu == 'Belum Pernah Pinjam' else 0)

            skor_akhir = (credit_score + green_score) / 2
            if skor_akhir >= 80 and credit_score >= 70:
                kategori, plafon = "Prioritas Kredit Hijau (Bunga 3%)", biaya * 2.5
            elif skor_akhir >= 55 and kredit_lalu != 'Menunggak':
                kategori, plafon = "Kredit Reguler (Bunga 6%)", biaya * 1.5
            else:
                kategori, plafon = "Pendampingan Teknis (Belum Layak)", 0

            cur_pusat.execute("""
                INSERT INTO hasil_skoring_kredit_karo 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (id_registrasi) DO UPDATE SET
                    margin_keuntungan = EXCLUDED.margin_keuntungan,
                    skor_kredit_finansial = EXCLUDED.skor_kredit_finansial,
                    skor_ramah_lingkungan = EXCLUDED.skor_ramah_lingkungan,
                    kategori_penerima = EXCLUDED.kategori_penerima,
                    plafon_kredit_maksimal = EXCLUDED.plafon_kredit_maksimal,
                    tanggal_sinkronisasi = NOW();
            """, (id_reg, nama, kec, poktan, komoditas, margin, credit_score, green_score, kategori, plafon))
            total_data += 1

    conn_pusat.commit()
    cur_pusat.close()
    conn_pusat.close()
    print(f"Sinkronisasi selesai: {total_data} data petani diproses.")
    return total_data

if __name__ == "__main__":
    sinkronkan_semua_data()
