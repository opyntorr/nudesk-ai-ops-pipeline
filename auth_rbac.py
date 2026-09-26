"""
Role-Based Access Control (RBAC) & Google Workspace Identity Management
Simulates Google Workspace Single Sign-On (SSO) and enforces role-specific
navigation, data access restrictions, and administrative isolation.
"""
from typing import Dict, Any, List
from dataclasses import dataclass


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
            "direct_webhook_dispatch": False,  # Dispatch happens automatically on approve
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


def get_persona_by_id(persona_id: str) -> UserPersona:
    for persona in PRESET_WORKSPACE_PERSONAS:
        if persona.id == persona_id:
            return persona
    return PRESET_WORKSPACE_PERSONAS[0]


def get_persona_by_role(role_key: str) -> UserPersona:
    for persona in PRESET_WORKSPACE_PERSONAS:
        if persona.role_key == role_key:
            return persona
    return PRESET_WORKSPACE_PERSONAS[0]
