# =========================================================
# db.py
# Koneksi ke Supabase (PostgREST) memakai library `requests`.
# Kunci rahasia HANYA dibaca dari environment variable (file .env).
# =========================================================
import os
import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_SECRET_KEY", "")


class DBError(Exception):
    def __init__(self, message, status=None):
        super().__init__(message)
        self.status = status


def _headers(prefer=None):
    h = {"apikey": SUPABASE_KEY, "Content-Type": "application/json"}
    # Kunci lama (service_role) berupa JWT -> boleh dikirim juga sebagai Bearer.
    # Kunci baru (sb_secret_...) BUKAN JWT -> cukup lewat header apikey.
    if SUPABASE_KEY.startswith("eyJ"):
        h["Authorization"] = f"Bearer {SUPABASE_KEY}"
    if prefer:
        h["Prefer"] = prefer
    return h


def _request(method, table, params=None, body=None, prefer=None):
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise DBError("SUPABASE_URL / SUPABASE_SECRET_KEY belum diatur di file .env")
    try:
        r = requests.request(
            method, f"{SUPABASE_URL}/rest/v1/{table}",
            headers=_headers(prefer), params=params, json=body, timeout=15,
        )
    except requests.RequestException as e:
        raise DBError(f"Tidak bisa terhubung ke Supabase: {e}")
    if r.status_code >= 400:
        try:
            msg = r.json().get("message", r.text)
        except ValueError:
            msg = r.text
        raise DBError(f"Supabase error {r.status_code}: {msg}", status=r.status_code)
    return r.json() if r.text else None


# ---------------- PESERTA ----------------
def get_peserta(nim):
    rows = _request("GET", "peserta", params={"nim": f"eq.{nim}", "select": "*"})
    return rows[0] if rows else None


def list_peserta():
    return _request("GET", "peserta", params={"select": "*", "order": "nama.asc", "limit": 1000}) or []


def insert_peserta(fields):
    _request("POST", "peserta", body=fields, prefer="return=minimal")


def update_peserta(nim, fields):
    _request("PATCH", "peserta", params={"nim": f"eq.{nim}"}, body=fields, prefer="return=minimal")


# ---------------- NILAI ----------------
def get_nilai(nim):
    rows = _request("GET", "nilai", params={"nim": f"eq.{nim}", "select": "kode,nilai"}) or []
    return {r["kode"]: r["nilai"] for r in rows}


def upsert_nilai(nim, nilai_map):
    if not nilai_map:
        return
    body = [{"nim": nim, "kode": k, "nilai": v} for k, v in nilai_map.items()]
    _request("POST", "nilai", params={"on_conflict": "nim,kode"}, body=body,
             prefer="resolution=merge-duplicates,return=minimal")


def delete_nilai(nim, kode_list):
    if not kode_list:
        return
    _request("DELETE", "nilai",
             params={"nim": f"eq.{nim}", "kode": f"in.({','.join(kode_list)})"},
             prefer="return=minimal")