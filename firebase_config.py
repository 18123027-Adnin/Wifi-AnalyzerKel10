"""
firebase_config.py
Koneksi Firebase — support Streamlit Cloud secrets & lokal (serviceAccountKey.json).
Tidak ada dummy data fallback: jika Firebase gagal, return None dan biarkan
app.py tampilkan pesan error yang jelas kepada pengguna.
"""

import os
import firebase_admin
from firebase_admin import credentials, firestore


def init_firebase():
    """Inisialisasi Firebase. Return Firestore client atau None jika gagal."""
    if firebase_admin._apps:
        return firestore.client()

    try:
        # ── Opsi 1: Streamlit Cloud Secrets ──────────────────────────────
        # Import streamlit hanya jika tersedia (tidak wajib di wifiscan.py)
        try:
            import streamlit as st
            if "firebase" in st.secrets:
                cred_dict = dict(st.secrets["firebase"])
                if "private_key" in cred_dict:
                    cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")
                cred = credentials.Certificate(cred_dict)
                print("[OK] Firebase terhubung via Streamlit Secrets")
                firebase_admin.initialize_app(cred)
                return firestore.client()
        except Exception:
            pass  # Streamlit tidak tersedia atau secrets tidak ada — lanjut ke opsi 2

        # ── Opsi 2: serviceAccountKey.json lokal ─────────────────────────
        key_candidates = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "serviceAccountKey.json"),
            os.path.join(os.getcwd(), "serviceAccountKey.json"),
        ]
        key_path = next((p for p in key_candidates if os.path.exists(p)), None)

        if key_path:
            cred = credentials.Certificate(key_path)
            print(f"[OK] Firebase terhubung via {key_path}")
            firebase_admin.initialize_app(cred)
            return firestore.client()

        # ── Tidak ada kredensial ──────────────────────────────────────────
        print("[WARN] Tidak ada kredensial Firebase ditemukan.")
        return None

    except Exception as e:
        print(f"[ERROR] Firebase gagal terhubung: {e}")
        return None


def upload_scan(db, scan_results: dict):
    """Upload hasil scan ke Firestore. Return doc_ref atau None jika gagal."""
    if db is None:
        print("[WARN] Firebase tidak tersedia, data tidak disimpan.")
        return None
    try:
        doc_ref = db.collection("wifi_scans").add(scan_results)
        print(f"[OK] {len(scan_results.get('networks', []))} jaringan tersimpan ke Firestore.")
        return doc_ref
    except Exception as e:
        print(f"[ERROR] Gagal upload ke Firestore: {e}")
        return None


def get_history(db, limit: int = 10) -> list:
    """Ambil histori scan dari Firestore, urut terbaru duluan."""
    if db is None:
        return []
    try:
        docs = (
            db.collection("wifi_scans")
            .order_by("timestamp", direction=firestore.Query.DESCENDING)
            .limit(limit)
            .stream()
        )
        return [doc.to_dict() for doc in docs]
    except Exception as e:
        print(f"[ERROR] Gagal ambil histori: {e}")
        return []
