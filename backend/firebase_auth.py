"""
Firebase Auth module for FocusFlow.
Handles Firebase Admin SDK initialization and ID token verification.
In local mode (no credentials), authentication is skipped entirely.
"""
import json
import logging

from fastapi import HTTPException

logger = logging.getLogger(__name__)

# ---------- Firebase Admin SDK Initialization ----------

_firebase_app = None

def _init_firebase():
    """Initialize Firebase Admin SDK from environment variable (called once)."""
    global _firebase_app
    from backend.config import FIREBASE_SERVICE_ACCOUNT_JSON

    if not FIREBASE_SERVICE_ACCOUNT_JSON:
        logger.warning(
            "FIREBASE_SERVICE_ACCOUNT_JSON not set — Firebase auth disabled (local mode)."
        )
        return

    try:
        import firebase_admin
        from firebase_admin import credentials

        cred_dict = json.loads(FIREBASE_SERVICE_ACCOUNT_JSON)
        cred = credentials.Certificate(cred_dict)
        _firebase_app = firebase_admin.initialize_app(cred)
        logger.info("✅ Firebase Admin SDK initialized successfully.")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Firebase Admin SDK: {e}")
        # Don't raise — allow app to start without Firebase auth

# Run initialization at module load time
_init_firebase()


# ---------- Token Verification ----------

def verify_firebase_token(id_token: str) -> dict:
    """
    Verify a Firebase ID token and return decoded claims.
    Returns dict with at least: uid, email, name (if available).
    Raises HTTPException 401 on any failure.
    """
    try:
        from firebase_admin import auth
        decoded = auth.verify_id_token(id_token)
        return {
            "uid": decoded["uid"],
            "email": decoded.get("email", ""),
            "name": decoded.get("name", ""),
        }
    except Exception as e:
        logger.warning(f"Firebase token verification failed: {e}")
        raise HTTPException(
            status_code=401,
            detail=f"Invalid or expired authentication token: {e}",
        )
