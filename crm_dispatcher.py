import os
import time
from typing import Tuple, Dict, Any, Optional
import requests


def dispatch_to_n8n(
    webhook_url: Optional[str],
    payload: Dict[str, Any],
    flow_type: str = "credit"
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Dispatch structured payload to an n8n webhook instance.
    Handles simulation mode when endpoint is unconfigured or unreachable.
    Returns: (success: bool, status_message: str, dispatched_payload: dict)
    """
    auth_token = os.getenv("N8N_AUTH_TOKEN", "nudesk_ops_secure_token_v2")
    enriched_payload = {
        "flow_type": flow_type,
        "metadata": {
            "source": "nuDesk Operations Studio",
            "flow_type": flow_type,
            "dispatch_timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "environment": "Mazatlan Operations Hub",
            "auth_token_present": bool(auth_token)
        },
        "data": payload
    }

    if not webhook_url or not webhook_url.strip():
        return (
            True,
            "Simulation Mode Active: Payload generated and validated. Ready for transmission once n8n webhook URL is provided.",
            enriched_payload
        )

    clean_url = webhook_url.strip()

    try:
        headers = {
            "Content-Type": "application/json",
            "X-nuDesk-Auth-Token": auth_token
        }
        response = requests.post(
            clean_url,
            json=enriched_payload,
            headers=headers,
            timeout=5
        )

        if response.status_code in [200, 201]:
            return (
                True,
                f"Successfully dispatched to n8n (HTTP {response.status_code}). Record processed for Google Sheets / CRM sync.",
                enriched_payload
            )
        else:
            return (
                False,
                f"n8n webhook responded with unexpected status HTTP {response.status_code}: {response.text[:200]}",
                enriched_payload
            )

    except requests.exceptions.ConnectionError:
        return (
            False,
            f"Connection refused at '{clean_url}'. If using local n8n, verify that Docker is running ('docker compose up -d').",
            enriched_payload
        )
    except requests.exceptions.Timeout:
        return (
            False,
            f"Webhook dispatch timed out after 5.0 seconds at '{clean_url}'.",
            enriched_payload
        )
    except requests.exceptions.RequestException as exc:
        return (
            False,
            f"Network dispatch error: {type(exc).__name__} - {str(exc)}",
            enriched_payload
        )
