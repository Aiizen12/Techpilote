import hashlib
import os
import secrets
from datetime import datetime, timedelta

import reflex as rx
from jose import JWTError, jwt

from techpilot.db.database import load_db, save_db
from techpilot.db.activity import log_activity

JWT_SECRET = os.getenv("JWT_SECRET", "techpilot-jwt-secret-fallback")
JWT_ALGORITHM = "HS256"
DEFAULT_MANAGER_PASSWORD = os.getenv("DEFAULT_MANAGER_PASSWORD", "TechPilot2025")

DEFAULT_PERMS = {
    "planning_edit": False,
    "matrix_edit": False,
    "technicians_edit": False,
    "tickets_manage": True,
    "import_excel": False,
    "permissions_manage": False,
    "escalade_proc_edit": False,
    "doc_edit": False,
}


# ── Helpers crypto ────────────────────────────────────────────────────────────

def _hash(password: str, salt: str) -> str:
    dk = hashlib.pbkdf2_hmac("sha512", password.encode(), salt.encode(), 100000, dklen=64)
    return dk.hex()

def _verify(password: str, hash_: str, salt: str) -> bool:
    return _hash(password, salt) == hash_

def _make_token(user_id: str, role: str, nom: str) -> str:
    payload = {
        "userId": user_id,
        "role": role,
        "nom": nom,
        "exp": datetime.utcnow() + timedelta(hours=8),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def _decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        return None


# ── Auth State ────────────────────────────────────────────────────────────────

class AuthState(rx.State):
    token: str = rx.LocalStorage("")
    user_id: str = ""
    user_role: str = ""
    user_nom: str = ""
    login_error: str = ""
    require_password_change: bool = False

    # Form fields
    login_user_id: str = ""
    login_password: str = ""

    @rx.var
    def is_authenticated(self) -> bool:
        if not self.token:
            return False
        payload = _decode_token(self.token)
        return payload is not None

    @rx.var
    def is_manager(self) -> bool:
        return self.user_role == "manager"

    @rx.var
    def can_edit_procedure(self) -> bool:
        return self.permissions.get("escalade_proc_edit", False)

    @rx.var
    def can_edit_doc(self) -> bool:
        return self.permissions.get("doc_edit", False)

    @rx.var
    def permissions(self) -> dict:
        if self.user_role == "manager":
            return {k: True for k in DEFAULT_PERMS}
        db = load_db()
        tech = next((t for t in db["technicians"] if str(t.get("id")) == str(self.user_id)), None)
        return {**DEFAULT_PERMS, **(tech.get("permissions", {}) if tech else {})}

    def set_login_user_id(self, val: str):
        self.login_user_id = val

    def set_login_password(self, val: str):
        self.login_password = val

    def do_login(self):
        self.login_error = ""
        user_id = self.login_user_id.strip()
        password = self.login_password

        if not user_id or not password:
            self.login_error = "Identifiant et mot de passe requis"
            return

        db = load_db()

        if user_id == "manager":
            mgr = db.get("manager_auth") or {}
            require_change = not mgr.get("password_hash")
            if mgr.get("password_hash"):
                ok = _verify(password, mgr["password_hash"], mgr["salt"])
            else:
                ok = password == DEFAULT_MANAGER_PASSWORD
            if not ok:
                self.login_error = "Mot de passe incorrect"
                log_activity("manager", "LOGIN_FAIL", "auth", "Mot de passe incorrect")
                return
            self.token = _make_token("manager", "manager", "Responsable")
            self.user_id = "manager"
            self.user_role = "manager"
            self.user_nom = "Responsable"
            self.require_password_change = require_change
            self.login_password = ""
            log_activity("Responsable", "LOGIN", "auth", "Connexion manager")
            return rx.redirect("/dashboard")

        tech = next(
            (t for t in db["technicians"]
             if str(t.get("id")) == str(user_id)
             or (t.get("nom") or "").strip().lower() == user_id.lower()
             or str(t.get("matricule") or "") == user_id),
            None
        )
        if not tech:
            self.login_error = "Utilisateur non trouvé"
            log_activity(user_id, "LOGIN_FAIL", "auth", "Utilisateur non trouvé")
            return
        if not tech.get("active", True):
            self.login_error = "Compte désactivé. Contactez votre responsable."
            log_activity(tech.get("nom", user_id), "LOGIN_FAIL", "auth", "Compte désactivé")
            return
        if not tech.get("password_hash"):
            self.login_error = "Aucun mot de passe défini. Contactez votre responsable."
            return
        if not _verify(password, tech["password_hash"], tech["password_salt"]):
            self.login_error = "Mot de passe incorrect"
            log_activity(tech.get("nom", user_id), "LOGIN_FAIL", "auth", "Mot de passe incorrect")
            return

        self.token = _make_token(str(tech["id"]), "tech", tech.get("nom", ""))
        self.user_id = str(tech["id"])
        self.user_role = "tech"
        self.user_nom = tech.get("nom", "")
        self.login_password = ""
        log_activity(tech.get("nom", ""), "LOGIN", "auth", "Connexion technicien")
        return rx.redirect("/dashboard")

    def logout(self):
        log_activity(self.user_nom or "?", "LOGOUT", "auth", "Déconnexion")
        self.token = ""
        self.user_id = ""
        self.user_role = ""
        self.user_nom = ""
        return rx.redirect("/login")

    def check_auth(self):
        """Appelé au chargement de chaque page protégée."""
        if not self.token:
            return rx.redirect("/login")
        payload = _decode_token(self.token)
        if not payload:
            self.token = ""
            return rx.redirect("/login")
        self.user_id = str(payload.get("userId", ""))
        self.user_role = payload.get("role", "")
        self.user_nom = payload.get("nom", "")

    def admin_set_password(self, tech_id: str, new_password: str):
        if self.user_role != "manager":
            return
        db = load_db()
        salt = secrets.token_hex(16)
        h = _hash(new_password, salt)
        if tech_id == "manager":
            db["manager_auth"] = {"password_hash": h, "salt": salt}
        else:
            idx = next((i for i, t in enumerate(db["technicians"]) if str(t.get("id")) == tech_id), -1)
            if idx != -1:
                db["technicians"][idx]["password_hash"] = h
                db["technicians"][idx]["password_salt"] = salt
        save_db(db)
