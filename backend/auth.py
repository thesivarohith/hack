import os
import json
import requests
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth

FIREBASE_API_KEY = os.environ.get("FIREBASE_API_KEY", "")
FIREBASE_AUTH_REST = (
    "https://identitytoolkit.googleapis.com/v1/accounts"
)

# ── Firebase Admin Init ──────────────────────────────────────
def init_firebase():
    if firebase_admin._apps:
        return
    sa_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")
    if not sa_json:
        print("⚠️ No Firebase service account - auth disabled")
        return
    try:
        cred = credentials.Certificate(json.loads(sa_json))
        firebase_admin.initialize_app(cred)
        print("✅ Firebase Admin initialized")
    except Exception as e:
        print(f"⚠️ Firebase init error: {e}")

init_firebase()

# ── Email / Password ─────────────────────────────────────────
def email_signup(name: str, email: str, password: str) -> dict:
    r = requests.post(
        f"{FIREBASE_AUTH_REST}:signUp?key={FIREBASE_API_KEY}",
        json={
            "email": email,
            "password": password,
            "returnSecureToken": True
        },
        timeout=10
    )
    data = r.json()
    if "idToken" not in data:
        msg = data.get("error", {}).get("message", "Signup failed")
        raise ValueError(msg)
    # Set display name
    requests.post(
        f"{FIREBASE_AUTH_REST}:update?key={FIREBASE_API_KEY}",
        json={
            "idToken": data["idToken"],
            "displayName": name
        },
        timeout=10
    )
    return {
        "uid": data["localId"],
        "email": email,
        "name": name,
        "avatar": "",
        "token": data["idToken"]
    }

def email_login(email: str, password: str) -> dict:
    r = requests.post(
        f"{FIREBASE_AUTH_REST}:signInWithPassword"
        f"?key={FIREBASE_API_KEY}",
        json={
            "email": email,
            "password": password,
            "returnSecureToken": True
        },
        timeout=10
    )
    data = r.json()
    if "idToken" not in data:
        msg = data.get("error", {}).get("message", "Login failed")
        raise ValueError(msg)
    return {
        "uid": data["localId"],
        "email": email,
        "name": data.get("displayName", email.split("@")[0]),
        "avatar": data.get("photoUrl", ""),
        "token": data["idToken"]
    }

def forgot_password(email: str):
    r = requests.post(
        f"{FIREBASE_AUTH_REST}:sendOobCode"
        f"?key={FIREBASE_API_KEY}",
        json={"requestType": "PASSWORD_RESET", "email": email},
        timeout=10
    )
    data = r.json()
    if "email" not in data:
        raise ValueError("Could not send reset email")

# ── Google OAuth ─────────────────────────────────────────────
def get_google_oauth_url(app_url: str) -> str:
    client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
    return (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={client_id}"
        f"&redirect_uri={app_url}"
        "&response_type=code"
        "&scope=openid%20email%20profile"
        "&state=google"
        "&prompt=select_account"
    )

def google_callback(code: str, app_url: str) -> dict:
    client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET", "")
    # Exchange code for tokens
    token_r = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": app_url,
            "grant_type": "authorization_code"
        },
        timeout=10
    )
    tokens = token_r.json()
    google_id_token = tokens.get("id_token")
    if not google_id_token:
        raise ValueError("Google token exchange failed")
    # Sign in to Firebase with Google token
    fb_r = requests.post(
        f"https://identitytoolkit.googleapis.com/v1/accounts"
        f":signInWithIdp?key={FIREBASE_API_KEY}",
        json={
            "postBody": (
                f"id_token={google_id_token}"
                "&providerId=google.com"
            ),
            "requestUri": app_url,
            "returnIdpCredential": True,
            "returnSecureToken": True
        },
        timeout=10
    )
    fb_data = fb_r.json()
    if "idToken" not in fb_data:
        err_msg = fb_data.get("error", {}).get("message", "Unknown Firebase error")
        raise ValueError(f"Firebase Google sign-in failed: {err_msg}")
    return {
        "uid": fb_data["localId"],
        "email": fb_data.get("email", ""),
        "name": fb_data.get("displayName", "Student"),
        "avatar": fb_data.get("photoUrl", ""),
        "token": fb_data["idToken"]
    }

# ── GitHub OAuth ─────────────────────────────────────────────
def get_github_oauth_url(app_url: str) -> str:
    client_id = os.environ.get("GITHUB_CLIENT_ID", "")
    return (
        "https://github.com/login/oauth/authorize"
        f"?client_id={client_id}"
        f"&redirect_uri={app_url}"
        "&scope=user:email"
        "&state=github"
    )

def github_callback(code: str, app_url: str) -> dict:
    client_id = os.environ.get("GITHUB_CLIENT_ID", "")
    client_secret = os.environ.get("GITHUB_CLIENT_SECRET", "")
    # Exchange code for access token
    token_r = requests.post(
        "https://github.com/login/oauth/access_token",
        headers={"Accept": "application/json"},
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "redirect_uri": app_url
        },
        timeout=10
    )
    token_data = token_r.json()
    access_token = token_data.get("access_token")
    if not access_token:
        raise ValueError("GitHub token exchange failed")
    # Sign in to Firebase with GitHub token
    fb_r = requests.post(
        f"https://identitytoolkit.googleapis.com/v1/accounts"
        f":signInWithIdp?key={FIREBASE_API_KEY}",
        json={
            "postBody": (
                f"access_token={access_token}"
                "&providerId=github.com"
            ),
            "requestUri": app_url,
            "returnIdpCredential": True,
            "returnSecureToken": True
        },
        timeout=10
    )
    fb_data = fb_r.json()
    if "idToken" not in fb_data:
        raise ValueError("Firebase GitHub sign-in failed")
    return {
        "uid": fb_data["localId"],
        "email": fb_data.get("email", ""),
        "name": fb_data.get("displayName", "Student"),
        "avatar": fb_data.get("photoUrl", ""),
        "token": fb_data["idToken"]
    }
