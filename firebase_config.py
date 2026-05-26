import os
import firebase_admin
from firebase_admin import credentials, firestore


def init_firebase():
    if firebase_admin._apps:
        return firestore.client()

    try:
        try:
            import streamlit as st
            if "firebase" in st.secrets:
                cred_dict = dict(st.secrets["firebase"])
                if "private_key" in cred_dict:
                    cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
                return firestore.client()
        except Exception:
            pass

        key_candidates = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "serviceAccountKey.json"),
            os.path.join(os.getcwd(), "serviceAccountKey.json"),
        ]
        key_path = next((p for p in key_candidates if os.path.exists(p)), None)

        if key_path:
            cred = credentials.Certificate(key_path)
            firebase_admin.initialize_app(cred)
            return firestore.client()

        return None

    except Exception as e:
        print(f"[ERROR] Firebase gagal terhubung: {e}")
        return None


def get_history(db, limit=10):
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
