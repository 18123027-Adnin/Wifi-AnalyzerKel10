import os
import firebase_admin
from firebase_admin import credentials, firestore


def init_firebase():
    if firebase_admin._apps:
        return firestore.client()

    try:
        import streamlit as st
        if "firebase" in st.secrets:
            cred_dict = dict(st.secrets["firebase"])
            if "private_key" in cred_dict:
                cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")
            try:
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
                return firestore.client()
            except Exception as e:
                st.error(f"❌ Firebase init error: {e}")
                return None
        else:
            st.error("❌ Secrets tidak ditemukan — pastikan [firebase] sudah diisi di Streamlit Cloud")
            return None
    except Exception as e:
        pass

    key_candidates = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "serviceAccountKey.json"),
        os.path.join(os.getcwd(), "serviceAccountKey.json"),
    ]
    key_path = next((p for p in key_candidates if os.path.exists(p)), None)
    if key_path:
        try:
            cred = credentials.Certificate(key_path)
            firebase_admin.initialize_app(cred)
            return firestore.client()
        except Exception as e:
            return None

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
        return []
