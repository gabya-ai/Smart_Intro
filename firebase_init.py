import os, base64, json
import firebase_admin
from firebase_admin import credentials

def ensure_firebase_initialized():
    if not firebase_admin._apps:
        encoded = os.getenv("FIREBASE_CREDENTIALS")
        if encoded:
            creds_dict = json.loads(base64.b64decode(encoded).decode("utf-8"))
            cred = credentials.Certificate(creds_dict)
        else:
            cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(cred)
    return firebase_admin.get_app()

firebase_app = ensure_firebase_initialized()
