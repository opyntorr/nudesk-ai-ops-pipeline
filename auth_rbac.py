"""
Role-Based Access Control (RBAC) & Google Workspace Identity Management
Supports Google Cloud Console OAuth 2.0 Single Sign-On (SSO) alongside
preset corporate personas for Mazatlán Talent Hub operational testing.
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import urllib.parse
import requests


@dataclass
class UserPersona:
    id: str
    name: str
    email: str
    role_key: str
    role_title: str
    department: str
    default_tab: str
    avatar_initials: str
    permissions: Dict[str, bool]
    picture_url: str = ""
    is_live_google_session: bool = False


PRESET_WORKSPACE_PERSONAS: List[UserPersona] = [
    UserPersona(
        id="usr_underwriter_1",
        name="Robert Martinez",
        email="robert.martinez@nudesk.ai",
        role_key="underwriter",
        role_title="Senior Underwriter",
        department="Credit Operations (Mazatlán)",
        default_tab="Credit DeskMate",
        avatar_initials="RM",
        permissions={
            "view_credit": True,
            "view_sales": True,
            "view_hr": False,
            "view_audit_log": True,
            "it_admin_settings": False,
            "view_raw_json": False,
            "direct_webhook_dispatch": False,
        }
    ),
    UserPersona(
        id="usr_bdr_1",
        name="Sarah Jenkins",
        email="sarah.jenkins@nudesk.ai",
        role_key="bdr",
        role_title="Commercial BDR",
        department="Sales Operations",
        default_tab="Sales DeskMate",
        avatar_initials="SJ",
        permissions={
            "view_credit": False,
            "view_sales": True,
            "view_hr": False,
            "view_audit_log": False,
            "it_admin_settings": False,
            "view_raw_json": False,
            "direct_webhook_dispatch": False,
        }
    ),
    UserPersona(
        id="usr_hr_1",
        name="Elena Ramos",
        email="elena.ramos@nudesk.ai",
        role_key="hr_recruiter",
        role_title="Talent Specialist",
        department="HR Solutions & Recruiting",
        default_tab="HR DeskMate",
        avatar_initials="ER",
        permissions={
            "view_credit": False,
            "view_sales": False,
            "view_hr": True,
            "view_audit_log": True,
            "it_admin_settings": False,
            "view_raw_json": False,
            "direct_webhook_dispatch": False,
        }
    ),
    UserPersona(
        id="usr_manager_1",
        name="Carlos Méndez",
        email="carlos.mendez@nudesk.ai",
        role_key="manager",
        role_title="Operations VP",
        department="Executive Leadership",
        default_tab="Executive KPI Dashboard",
        avatar_initials="CM",
        permissions={
            "view_credit": True,
            "view_sales": True,
            "view_hr": True,
            "view_audit_log": True,
            "it_admin_settings": False,
            "view_raw_json": False,
            "direct_webhook_dispatch": True,
        }
    ),
    UserPersona(
        id="usr_it_admin_1",
        name="Omar Payán",
        email="omar.payan@nudesk.ai",
        role_key="it_admin",
        role_title="Lead AI Ops Engineer",
        department="IT & Systems Architecture",
        default_tab="System Architecture & IT",
        avatar_initials="OP",
        permissions={
            "view_credit": True,
            "view_sales": True,
            "view_hr": True,
            "view_audit_log": True,
            "it_admin_settings": True,
            "view_raw_json": True,
            "direct_webhook_dispatch": True,
        }
    ),
]


def get_persona_by_id(persona_id: str, custom_persona: Optional[UserPersona] = None) -> UserPersona:
    """Retrieve persona by ID, supporting dynamically authenticated live Google sessions."""
    if custom_persona and custom_persona.id == persona_id:
        return custom_persona
    for persona in PRESET_WORKSPACE_PERSONAS:
        if persona.id == persona_id:
            return persona
    return PRESET_WORKSPACE_PERSONAS[0]


def get_persona_by_role(role_key: str) -> UserPersona:
    """Retrieve default persona by role key."""
    for persona in PRESET_WORKSPACE_PERSONAS:
        if persona.role_key == role_key:
            return persona
    return PRESET_WORKSPACE_PERSONAS[0]


def get_google_auth_url(client_id: str, redirect_uri: str) -> str:
    """Build the official Google OAuth 2.0 authorization URL."""
    base_url = "https://accounts.google.com/o/oauth2/v2/auth"
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account",
    }
    return f"{base_url}?{urllib.parse.urlencode(params)}"


def exchange_code_for_user(code: str, client_id: str, client_secret: str, redirect_uri: str) -> Dict[str, Any]:
    """Exchange authorization code for tokens and fetch user profile from Google API."""
    token_url = "https://oauth2.googleapis.com/token"
    token_payload = {
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }
    response = requests.post(token_url, data=token_payload, timeout=10)
    if response.status_code != 200:
        raise RuntimeError(f"Google Token Exchange Failed: {response.text}")
    tokens = response.json()
    access_token = tokens.get("access_token")
    if not access_token:
        raise RuntimeError("No access_token returned by Google OAuth server.")

    userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
    headers = {"Authorization": f"Bearer {access_token}"}
    userinfo_resp = requests.get(userinfo_url, headers=headers, timeout=10)
    if userinfo_resp.status_code != 200:
        raise RuntimeError(f"Failed to fetch Google User Info: {userinfo_resp.text}")
    return userinfo_resp.json()


def create_persona_from_google_user(user_info: Dict[str, Any]) -> UserPersona:
    """Construct an active UserPersona from real Google Workspace OAuth profile."""
    name = user_info.get("name") or user_info.get("email", "Google User")
    email = user_info.get("email", "")
    picture = user_info.get("picture", "")

    # Calculate initials
    name_parts = [p for p in name.strip().split() if p]
    if len(name_parts) >= 2:
        initials = (name_parts[0][0] + name_parts[1][0]).upper()
    elif len(name_parts) == 1:
        initials = name_parts[0][:2].upper()
    else:
        initials = "GW"

    # Lead Engineer / Admin check
    normalized_email = email.lower()
    is_admin = ("omar" in normalized_email) or ("payan" in normalized_email) or ("admin" in normalized_email)

    if is_admin:
        role_key = "it_admin"
        role_title = "Lead AI Ops Engineer (Workspace Admin)"
        department = "IT & Systems Architecture (Mazatlán Hub)"
        default_tab = "System Architecture & IT"
        permissions = {
            "view_credit": True,
            "view_sales": True,
            "view_hr": True,
            "view_audit_log": True,
            "it_admin_settings": True,
            "view_raw_json": True,
            "direct_webhook_dispatch": True,
        }
    else:
        role_key = "underwriter"
        role_title = "Operations Specialist"
        department = "Credit Operations (Mazatlán)"
        default_tab = "Credit DeskMate"
        permissions = {
            "view_credit": True,
            "view_sales": True,
            "view_hr": False,
            "view_audit_log": True,
            "it_admin_settings": False,
            "view_raw_json": False,
            "direct_webhook_dispatch": False,
        }

    return UserPersona(
        id="usr_live_google",
        name=name,
        email=email,
        role_key=role_key,
        role_title=role_title,
        department=department,
        default_tab=default_tab,
        avatar_initials=initials,
        permissions=permissions,
        picture_url=picture,
        is_live_google_session=True,
    )
