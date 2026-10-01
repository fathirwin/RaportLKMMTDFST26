# =========================================================
# data.py
# Konfigurasi komponen penilaian + logika perhitungan raport.
# Data peserta & nilai diambil dari Supabase (lihat db.py).
# =========================================================
import math
import db

PRAKTIK_MATERI_TEMPLATE = [
    {"kode": "M1", "nama": "Perumusan Gagasan Awal",                      "maks": 15},
    {"kode": "M2", "nama": "Merancang Ukuran dan Jadwal Kerja",           "maks": 15},
    {"kode": "M3", "nama": "Membangun Struktur Organisasi & Kepanitiaan", "maks": 15},
    {"kode": "M4", "nama": "Koordinasi & Penjabaran Gagasan ke Aksi",     "maks": 15},
    {"kode": "M5", "nama": "Administrasi",                                "maks": 15},
    {"kode": "M6", "nama": "Motivasi dan Keputusan",                      "maks": 15},
    {"kode": "M7", "nama": "Pengendalian Konflik",                        "maks": 15},
    {"kode": "M8", "nama": "Pengembangan Program Kerja",                  "maks": 15},
    {"kode": "M9", "nama": "Simulasi Total",                              "maks": 15},
]

PENUGASAN_TEMPLATE = [
    {"kode": "T1", "nama": "Pembuatan Proposal (Kelompok)",          "maks": 15},
    {"kode": "T2", "nama": "Studi Kasus Alur Komunikasi",            "maks": 15},
    {"kode": "T3", "nama": "Alur Birokrasi",                         "maks": 15},
    {"kode": "T4", "nama": "Perencanaan Program",                    "maks": 15},
]

KARAKTER_TEMPLATE = [
    {"kode": "K1", "nama": "Aktif",          "maks": 15},
    {"kode": "K2", "nama": "Disiplin",       "maks": 15},
    {"kode": "K3", "nama": "Tanggung Jawab", "maks": 10},
]

# Dipakai oleh form admin (edit nilai / tambah peserta)
SECTIONS = [
    {"judul": "Nilai Praktik Materi", "items": PRAKTIK_MATERI_TEMPLATE},
    {"judul": "Nilai Penugasan",      "items": PENUGASAN_TEMPLATE},
    {"judul": "Nilai Karakter",       "items": KARAKTER_TEMPLATE},
]

# KKM: nilai total >= KKM_LULUS = Lulus, selain itu Tidak Lulus
KKM_LULUS = 140

# link feedback
LINK_FEEDBACK = "https://forms.gle/eACa3kbGYW4Cw7er7"

# Link tugas syarat lulus (tampil hanya untuk peserta yang Tidak Lulus).
# Kosongkan ("") jika linknya belum ada.
LINK_TUGAS_SYARAT_LULUS = "https://forms.gle/1hMvVEskxumxgf7W9"


def fmt(x):
    """14.0 -> 14, 13.5 -> 13.5"""
    x = round(float(x), 2)
    return int(x) if x == int(x) else x


def _sum_score(nilai_map, template):
    total, maks_total, detail = 0.0, 0.0, []
    for item in template:
        skor = nilai_map.get(item["kode"])
        if skor is not None:
            total += float(skor)
        maks_total += item["maks"]
        detail.append({
            "kode": item["kode"],
            "nama": item["nama"],
            "maks": item["maks"],
            "nilai": fmt(skor) if skor is not None else None,  # None = belum dinilai
        })
    return fmt(total), fmt(maks_total), detail


def hitung_status_kelulusan(nilai_total):
    if nilai_total == 0:
        return "MULIH AE CAK!", "red"
    if nilai_total >= KKM_LULUS:
        return "Lulus", "green"
    return "Lulus Bersyarat", "red"



def get_raport(nim):
    mhs = db.get_peserta(nim)
    if not mhs:
        return None
    nilai = db.get_nilai(nim)

    p_tot, p_maks, p_det = _sum_score(nilai, PRAKTIK_MATERI_TEMPLATE)
    t_tot, t_maks, t_det = _sum_score(nilai, PENUGASAN_TEMPLATE)
    k_tot, k_maks, k_det = _sum_score(nilai, KARAKTER_TEMPLATE)

    nilai_total = fmt(p_tot + t_tot + k_tot)
    status, status_color = hitung_status_kelulusan(nilai_total)

    return {
        "nama": mhs["nama"],
        "nim": mhs["nim"],
        "kelompok": mhs.get("kelompok") or "",
        "prodi": mhs.get("prodi") or "",
        "finalized": mhs["finalized"],
        "praktik_materi": {"total": p_tot, "maks": p_maks, "detail": p_det},
        "penugasan": {"total": t_tot, "maks": t_maks, "detail": t_det},
        "karakter": {"total": k_tot, "maks": k_maks, "detail": k_det},
        "nilai_total": nilai_total,
        "maks_total": fmt(p_maks + t_maks + k_maks),
        "kkm_lulus": KKM_LULUS,
        "link_feedback": LINK_FEEDBACK, 
        "link_tugas": LINK_TUGAS_SYARAT_LULUS,
        "status": status,
        "status_color": status_color,
    }


def semua_kode():
    return [i["kode"] for s in SECTIONS for i in s["items"]]


def parse_nilai(form):
    """Baca input nilai dari form admin.
    Return: (dict kode->nilai yg disimpan, list kode yg dikosongkan, list error)"""
    simpan, hapus, errors = {}, [], []
    for sec in SECTIONS:
        for item in sec["items"]:
            raw = (form.get(f"nilai_{item['kode']}") or "").strip().replace(",", ".")
            if raw == "":
                hapus.append(item["kode"])
                continue
            try:
                v = float(raw)
            except ValueError:
                errors.append(f"{item['nama']}: nilai harus berupa angka.")
                continue
            if not math.isfinite(v) or v < 0 or v > item["maks"]:
                errors.append(f"{item['nama']}: nilai harus antara 0 dan {item['maks']}.")
                continue
            simpan[item["kode"]] = round(v, 2)
    return simpan, hapus, errors