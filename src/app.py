# =========================================================
# app.py
# Flask app - Website Raport LKMM TD FST Unair 2026
# Fitur admin: finalisasi, edit nilai, tambah peserta
#
# Menjalankan:  pip install -r requirements.txt  ->  python app.py
# =========================================================
import os
import re
import hmac
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, flash, session

import data
import db

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(32)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")

EVENT_TITLE = "Raport LKMM TD"
EVENT_SUBTITLE = "LKMM-TD FST 2026 — Asisten Pemandu FST 26"
NIM_RE = re.compile(r"^[A-Za-z0-9]{3,30}$")
PER_PAGE = 15  # jumlah peserta per halaman di dashboard admin
SORT_OPTIONS = [("nim", "NIM"), ("nama", "Nama"), ("kelompok", "Kelompok"),
                ("prodi", "Prodi"), ("nilai_total", "Nilai"), ("finalized", "Status")]


# ---------------- helper ----------------
def is_admin():
    return bool(session.get("is_admin"))


def admin_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not is_admin():
            flash("Silakan masuk sebagai admin terlebih dahulu.", "error")
            return redirect(url_for("admin_login"))
        return view(*args, **kwargs)
    return wrapper


@app.context_processor
def inject_globals():
    return {"is_admin": is_admin()}


@app.errorhandler(db.DBError)
def handle_db_error(e):
    app.logger.error("Supabase error: %s", e)
    msg = str(e) if is_admin() else "Data belum bisa dimuat. Coba lagi beberapa saat lagi."
    return render_template("error.html", title=EVENT_TITLE, message=msg), 500


def _raw_vals(form):
    return {k: form.get(f"nilai_{k}", "") for k in data.semua_kode()}


def _render_form(mode, peserta, nilai_vals):
    return render_template("admin_form.html", title=EVENT_TITLE, mode=mode,
                           p=peserta, nilai_vals=nilai_vals, sections=data.SECTIONS)


# ---------------- halaman publik ----------------
@app.route("/")
def index():
    return render_template("index.html", title=EVENT_TITLE, subtitle=EVENT_SUBTITLE)


@app.route("/cek-raport", methods=["POST"])
def cek_raport():
    nim = request.form.get("nim", "").strip()
    if not nim:
        flash("NIM tidak boleh kosong.", "error")
        return redirect(url_for("index"))
    return redirect(url_for("raport", nim=nim))


@app.route("/raport/<nim>")
def raport(nim):
    hasil = data.get_raport(nim)
    if not hasil:
        return render_template("raport.html", title=EVENT_TITLE, not_found=True, nim=nim)
    return render_template("raport.html", title=EVENT_TITLE, r=hasil, not_found=False)


# ---------------- login admin ----------------
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if is_admin():
        return redirect(url_for("admin_dashboard"))
    if request.method == "POST":
        pw = request.form.get("password", "")
        if ADMIN_PASSWORD and hmac.compare_digest(pw.encode(), ADMIN_PASSWORD.encode()):
            session["is_admin"] = True
            return redirect(url_for("admin_dashboard"))
        flash("Password admin salah.", "error")
    return render_template("admin_login.html", title=EVENT_TITLE)


@app.route("/admin/logout", methods=["POST"])
def admin_logout():
    session.clear()
    return redirect(url_for("index"))


# ---------------- dashboard admin ----------------
@app.route("/admin")
@admin_required
def admin_dashboard():
    q = request.args.get("q", "").strip()
    sort = request.args.get("sort", "nama")
    if sort not in dict(SORT_OPTIONS):
        sort = "nama"
    order = request.args.get("order", "asc")
    if order not in ("asc", "desc"):
        order = "asc"
    page = request.args.get("page", 1, type=int)

    daftar = db.list_peserta()
    totals = db.get_total_nilai_semua()
    for p in daftar:
        p["nilai_total"] = data.fmt(totals.get(p["nim"], 0))
    if q:
        ql = q.lower()
        daftar = [p for p in daftar if ql in p["nim"].lower() or ql in p["nama"].lower()]

    # --- pengurutan (naik / turun) ---
    reverse = (order == "desc")
    if sort == "nilai_total":
        daftar.sort(key=lambda p: p["nilai_total"], reverse=reverse)
    elif sort == "finalized":
        daftar.sort(key=lambda p: bool(p["finalized"]), reverse=reverse)
    else:
        terisi = [p for p in daftar if (p.get(sort) or "").strip()]
        kosong = [p for p in daftar if not (p.get(sort) or "").strip()]  # selalu di paling bawah
        terisi.sort(key=lambda p: p[sort].strip().lower(), reverse=reverse)
        daftar = terisi + kosong

    # --- pagination ---
    total = len(daftar)
    total_pages = max(1, -(-total // PER_PAGE))
    page = min(max(page or 1, 1), total_pages)
    start = (page - 1) * PER_PAGE
    tampil = daftar[start:start + PER_PAGE]
    page_numbers = list(range(max(1, page - 2), min(total_pages, page + 2) + 1))

    return render_template(
        "admin_dashboard.html", title=EVENT_TITLE, peserta=tampil, q=q,
        sort=sort, order=order, sort_options=SORT_OPTIONS,
        total=total, page=page, total_pages=total_pages, page_numbers=page_numbers,
        start=start,
    )

# ---------------- 1. FINALISASI ----------------
@app.route("/admin/finalisasi/<nim>", methods=["POST"])
@admin_required
def admin_finalisasi(nim):
    if not db.get_peserta(nim):
        flash("Peserta tidak ditemukan.", "error")
        return redirect(url_for("admin_dashboard"))
    finalize = request.form.get("action") == "finalisasi"
    db.update_peserta(nim, {"finalized": finalize})
    flash("Raport berhasil difinalisasi." if finalize else "Finalisasi dibatalkan, raport dibuka kembali.", "ok")
    if request.form.get("next") == "raport":
        return redirect(url_for("raport", nim=nim))
    return redirect(url_for(
        "admin_dashboard",
        q=request.form.get("q") or None, sort=request.form.get("sort") or None,
        order=request.form.get("order") or None, page=request.form.get("page") or None,
    ))


# ---------------- 2. EDIT NILAI ----------------
@app.route("/admin/edit/<nim>", methods=["GET", "POST"])
@admin_required
def admin_edit(nim):
    peserta = db.get_peserta(nim)
    if not peserta:
        flash("Peserta tidak ditemukan.", "error")
        return redirect(url_for("admin_dashboard"))

    if request.method == "GET":
        vals = {k: data.fmt(v) for k, v in db.get_nilai(nim).items()}
        return _render_form("edit", peserta, vals)

    p = {"nim": nim,
         "nama": request.form.get("nama", "").strip(),
         "kelompok": request.form.get("kelompok", "").strip(),
         "prodi": request.form.get("prodi", "").strip()}
    simpan, hapus, errors = data.parse_nilai(request.form)
    if not p["nama"]:
        errors.append("Nama wajib diisi.")
    if errors:
        for e in errors:
            flash(e, "error")
        return _render_form("edit", p, _raw_vals(request.form))

    db.update_peserta(nim, {"nama": p["nama"], "kelompok": p["kelompok"], "prodi": p["prodi"]})
    db.upsert_nilai(nim, simpan)
    db.delete_nilai(nim, hapus)
    flash("Data & nilai berhasil disimpan.", "ok")
    return redirect(url_for("admin_edit", nim=nim))


# ---------------- 3. TAMBAH PESERTA ----------------
@app.route("/admin/tambah", methods=["GET", "POST"])
@admin_required
def admin_tambah():
    if request.method == "GET":
        return _render_form("tambah", {"nim": "", "nama": "", "kelompok": "", "prodi": ""}, {})

    p = {k: request.form.get(k, "").strip() for k in ("nim", "nama", "kelompok", "prodi")}
    simpan, _hapus, errors = data.parse_nilai(request.form)
    if not NIM_RE.match(p["nim"]):
        errors.append("NIM harus 3–30 karakter, hanya huruf/angka, tanpa spasi.")
    if not p["nama"]:
        errors.append("Nama wajib diisi.")
    if not errors and db.get_peserta(p["nim"]):
        errors.append("NIM sudah terdaftar.")
    if errors:
        for e in errors:
            flash(e, "error")
        return _render_form("tambah", p, _raw_vals(request.form))

    try:
        db.insert_peserta(p)
    except db.DBError as e:
        if e.status == 409:
            flash("NIM sudah terdaftar.", "error")
            return _render_form("tambah", p, _raw_vals(request.form))
        raise
    db.upsert_nilai(p["nim"], simpan)
    flash(f"Peserta {p['nama']} berhasil ditambahkan.", "ok")
    return redirect(url_for("admin_edit", nim=p["nim"]))


if __name__ == "__main__":
    app.run(debug=True)