# Raport LKMM TD FST Unair 2026

Website cek raport berbasis Flask (Python), dengan HTML (Jinja2 template) dan CSS terpisah.

## Struktur File
```
raport-lkmm-td/
├── app.py
├── data.py
├── db.py                
├── requirements.txt     
├── .env                 
├── .gitignore           
├── sql/schema.sql       
├── static/
    ├── style.css
    └── image/logo-bem.png    
└── templates/
    ├── _flash.html         
    ├── index.html
    ├── raport.html
    ├── admin_login.html    
    ├── admin_dashboard.html 
    ├── admin_form.html     
    └── error.html          
```

## Cara Menjalankan (Lokal)
```bash
pip install flask
python app.py
```
Buka `http://127.0.0.1:5000` di browser. Coba NRP contoh: `5025261149` (belum final) atau `5025261103` (sudah final).

## Struktur Nilai (sesuai permintaan)
1. **Box "Belum Difinalisasi"** — selalu tampil, isinya otomatis berubah jadi "Sudah Difinalisasi ✓" (hijau) begitu status `finalized` diubah jadi `True`. Bisa diubah lewat Panel Admin di halaman raport (tambahkan `?admin=1` di URL, contoh: `/raport/5025261149?admin=1`), password default: `psdm2026` (ganti di `app.py`).
2. **Box "Nilai Praktik Materi"** — rata-rata tertimbang dari 9 materi (daftar & bobot ada di `data.py` → `PRAKTIK_MATERI_TEMPLATE`).
3. **Box "Nilai Penugasan"** (1 Kelompok + 3 Individu) dan **Box "Nilai Karakter"** (3 aspek) — daftar & bobot ada di `data.py` → `PENUGASAN_TEMPLATE` dan `KARAKTER_TEMPLATE`.
4. **Box "Nilai Total"** (gabungan 3 kategori di atas dengan bobot 40/35/25%) dan **Box "Status Kelulusan"** (Lulus ≥70, Lulus Bersyarat 60–69.9, Tidak Lulus <70) — logikanya ada di `data.py` → `hitung_status_kelulusan()` dan `BOBOT_TOTAL`.

## Mengubah Data Mahasiswa
Saat ini data mahasiswa disimpan langsung di `data.py` (variabel `STUDENTS`) sebagai contoh/demo. Untuk pemakaian sungguhan dengan banyak mahasiswa, ganti bagian ini dengan query ke database (Google Sheets API, Supabase/PostgreSQL, MySQL, dll.) — cukup ubah isi fungsi `get_raport()` dan `set_finalisasi()` di `data.py`, tidak perlu mengubah `app.py` atau template.

## Deployment Gratis (opsi)
- **Render.com** (Free Web Service) — hubungkan repo GitHub, set start command: `gunicorn app:app`, tambahkan `gunicorn` ke `requirements.txt`.
- **PythonAnywhere** (free tier) — upload file lewat dashboard, jalankan sebagai WSGI app.
- **Railway.app / Fly.io** — free tier tersedia, deploy langsung dari GitHub.

Untuk semua opsi di atas, buat file `requirements.txt` berisi:
```
flask
gunicorn
```
