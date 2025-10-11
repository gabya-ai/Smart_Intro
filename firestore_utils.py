from typing import Dict, Any
from google.cloud import firestore

# Firestore uses Application Default Credentials (ADC).
# Locally: your GOOGLE_APPLICATION_CREDENTIALS key.
# On Cloud Run: the service account you deployed with.
_db = None

def _client() -> firestore.Client:
    global _db
    if _db is None:
        _db = firestore.Client()  # auto-detects project from ADC
    return _db

def save_log(event_type: str, payload: Dict[str, Any]) -> str:
    """Write a single event to Firestore. Returns the document id."""
    doc = {
        "event": event_type,
        **payload,
        "server_time": firestore.SERVER_TIMESTAMP,
    }
    doc_ref = _client().collection("cover_letter_logs").document()  # auto-ID
    doc_ref.set(doc)  # write
    return doc_ref.id
